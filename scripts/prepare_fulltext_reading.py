#!/usr/bin/env python3
"""Prepare PRIVATE, complete-article reading packets from verified cached HTML.

No network and no HTML execution. Unlike the hardware discovery parser, this
keeps abstracts, related work, conclusions, appendices and references. Preparing
or printing a packet never records that an AI/person has read or verified it.

Examples (use the project's Python runtime with BeautifulSoup installed)::

    node scripts/run-python.mjs scripts/prepare_fulltext_reading.py --work-ids arxiv:2605.29074
    node scripts/run-python.mjs scripts/prepare_fulltext_reading.py --all-cached
    node scripts/run-python.mjs scripts/prepare_fulltext_reading.py --summary arxiv:2605.29074
    node scripts/run-python.mjs scripts/prepare_fulltext_reading.py --show arxiv:2605.29074 --start 1 --end 8

--start/--end are one-based inclusive reading SEGMENT indices. Long blocks and
tables are split losslessly into bounded segments; the footer supplies NEXT or
EOF. Neither printing EOF nor text-node accounting certifies completed reading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from collect_hardware_sources import arxiv_identity, normalized_heading, page_identity, table_rows

ROOT = Path(__file__).resolve().parents[1]
EXTRACTOR_VERSION = 'complete-article-reading-v1'
MAX_RAW_BYTES = 30_000_000
REMOVE = 'script,style,noscript,nav,[role=navigation],.ltx_page_header,.ltx_page_footer,.ltx_TOC'
TABLE_SELECTOR = 'table,.ltx_tabular,[role=table],[role=grid]'
EQUATION_CLASSES = {'ltx_eqn_table', 'ltx_equation', 'ltx_equationgroup'}
TABLE_COUNT_DEFINITION = 'HTML/ARIA/LaTeXML table or layout structures, including equation layouts; NOT a count of research-result tables.'
ROW_SELECTOR = 'tr,.ltx_tr,[role=row]'
CELL_SELECTOR = 'td,th,.ltx_td,[role=cell],[role=columnheader],[role=rowheader]'
SECTION_CLASSES = {'ltx_section', 'ltx_subsection', 'ltx_subsubsection', 'ltx_appendix', 'ltx_abstract', 'ltx_bibliography'}
BLOCK_TAGS = {'p', 'div', 'section', 'article', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'dl', 'dt', 'dd', 'pre', 'blockquote', 'figure', 'figcaption', 'caption', 'header', 'footer', 'address', 'aside'}
TRANSPORT_FIELDS = ('transport_verification', 'transport_complete', 'transport_returncode', 'transport_truncated', 'curl_exit_code')


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def clean(value):
    # Terminal control characters are not reading content; HTML is never run.
    return re.sub(r'\s+', ' ', re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(value))).strip()


def classes(node):
    return set(node.get('class', [])) if isinstance(node, Tag) else set()


def is_table(node):
    return isinstance(node, Tag) and (node.name == 'table' or 'ltx_tabular' in classes(node) or node.get('role') in {'table', 'grid'})


def is_row(node):
    return isinstance(node, Tag) and (node.name == 'tr' or 'ltx_tr' in classes(node) or node.get('role') == 'row')


def closest(node, predicate):
    return next((parent for parent in node.parents if predicate(parent)), None)


def canonical_arxiv_ids(work):
    values = [work.get('identifiers', {}).get('arxiv'), *work.get('identifier_aliases', {}).get('arxiv', []),
              *[alias for alias in work.get('aliases', []) if str(alias).lower().startswith('arxiv:')]]
    return {identity[0] for value in values if (identity := arxiv_identity(value))}


def official_html_identity(value):
    parsed = urlparse(str(value or ''))
    if parsed.scheme != 'https' or parsed.hostname not in {'arxiv.org', 'www.arxiv.org'} or parsed.username or parsed.password or not parsed.path.startswith('/html/'):
        raise ValueError('reading_packet_official_html_url_required')
    identity = arxiv_identity(value)
    if not identity:
        raise ValueError('reading_packet_source_identity_invalid')
    return identity


def safe_url(base, value):
    if not value or re.search(r'[\x00-\x1f\x7f]', str(value)):
        return None
    resolved = urljoin(base, str(value))
    parsed = urlparse(resolved)
    return resolved if parsed.scheme in {'https', 'http'} and parsed.hostname and not parsed.username and not parsed.password else None


class ArticleExtractor:
    """Account for DOM text nodes, not string values: repeated paragraphs stay."""
    def __init__(self, article, source_url, resource_base=None):
        self.article, self.source_url = article, source_url
        self.resource_base = resource_base or source_url
        self.blocks, self.sections, self.issues = [], [], []
        self.consumed, self.handled = set(), set()
        self.nodes = [node for node in article.descendants if isinstance(node, NavigableString) and not isinstance(node, Comment) and clean(node)]
        self.dom_order = {id(node): index for index, node in enumerate(article.descendants)}
        self.math_count = self.math_alt_count = self.image_count = 0
        self.table_count = self.unparsed_tables = self.definition_lists = 0

    def location(self, node):
        own = node.get('id') if isinstance(node, Tag) else None
        ancestor = closest(node, lambda parent: isinstance(parent, Tag) and bool(parent.get('id')))
        locator_id = own or (ancestor.get('id') if ancestor else None)
        return {'dom_id': own, 'locator_id': locator_id,
                'source_locator': self.source_url + ('#' + quote(locator_id, safe='.:_-') if locator_id else ''),
                'dom_order': self.dom_order.get(id(node), -1)}

    def issue(self, code, node, **details):
        self.issues.append({'code': code, **self.location(node), **details})

    def math(self, node):
        alternative = node.get('alttext') or node.get('aria-label')
        annotation = node.find('annotation', attrs={'encoding': re.compile(r'(tex|latex)', re.I)})
        if not alternative and annotation:
            alternative = annotation.get_text('', strip=True)
        source = 'alttext_or_tex_annotation' if alternative else 'mathml_presentation_fallback'
        if not alternative:
            fragments = [str(value) for value in node.descendants if isinstance(value, NavigableString)
                         and not value.find_parent(['annotation', 'annotation-xml'])]
            alternative = clean(' '.join(fragments))
            self.issue('math_without_alttext_or_tex', node)
        self.math_count += 1
        self.math_alt_count += source == 'alttext_or_tex_annotation'
        for value in node.descendants:
            if isinstance(value, NavigableString):
                self.consumed.add(id(value))
        return {'dom_id': node.get('id'), 'text': clean(alternative), 'representation': source,
                'display': node.get('display', 'inline'), 'visual_rendering_inspected': False}

    def image(self, node):
        self.image_count += 1
        href = safe_url(self.resource_base, node.get('src') or node.get('data-src') or node.get('href'))
        parent_link = closest(node, lambda parent: isinstance(parent, Tag) and parent.name == 'a' and bool(parent.get('href')))
        alt = clean(node.get('alt') or node.get('aria-label') or '')
        if not href:
            self.issue('image_reference_missing_or_non_http', node)
        if not alt:
            self.issue('image_alt_missing', node)
        return {**self.location(node), 'source_url': href, 'alt': alt,
                'link_url': safe_url(self.resource_base, parent_link['href']) if parent_link else None,
                'title': clean(node.get('title') or ''), 'image_inspected': False,
                'embedded_data_present': str(node.get('src', '')).startswith('data:')}

    def inline(self, nodes, *, table_owner=None):
        pieces, math, images, links = [], [], [], []
        def visit(node):
            if isinstance(node, Comment) or id(node) in self.handled:
                return
            if isinstance(node, NavigableString):
                if id(node) not in self.consumed:
                    self.consumed.add(id(node))
                    pieces.append(str(node))
                return
            if not isinstance(node, Tag):
                return
            if is_table(node) and node is not table_owner:
                pieces.append(f" [nested table {node.get('id') or 'without DOM id'}] ")
                return
            if node.name == 'math':
                value = self.math(node)
                math.append(value)
                pieces.append(' $' + value['text'] + '$ ')
                return
            if node.name == 'img':
                value = self.image(node)
                images.append(value)
                pieces.append(' [image alt: ' + (value['alt'] or 'missing; image not inspected') + '] ')
                return
            if node.name == 'br':
                pieces.append('\n')
            elif node.name in {'p', 'div', 'li', 'dt', 'dd'}:
                pieces.append(' ')
            if node.name == 'a' and node.get('href'):
                href = safe_url(self.resource_base, node['href'])
                if href:
                    links.append({'text': clean(node.get_text(' ', strip=True)), 'href': href, 'dom_id': node.get('id')})
                else:
                    self.issue('non_http_link_not_activated', node)
            for child in node.children:
                visit(child)
        for node in nodes:
            visit(node)
        return {'text': clean(''.join(pieces)), 'math': math, 'images': images, 'links': links}

    def emit(self, kind, node, context, value, **extra):
        if not value.get('text') and not value.get('images'):
            return
        self.blocks.append({'block_index': len(self.blocks) + 1, 'block_id': f"block-{len(self.blocks) + 1:06d}",
                            'kind': kind, **self.location(node), 'section_path': [dict(row) for row in context],
                            'evidence_role': 'context_not_usage' if any(row['role'] == 'context' for row in context) else 'article_text_not_usage_evidence',
                            **value, **extra})

    def section(self, node, context):
        heading = node.find(re.compile(r'^h[1-6]$'))
        title = clean(heading.get_text(' ', strip=True)) if heading else ('Abstract' if 'ltx_abstract' in classes(node) else 'References' if 'ltx_bibliography' in classes(node) else 'Untitled section')
        normalized = normalized_heading(title).lower()
        context_kind = ('references' if re.match(r'^(references|bibliography)', normalized) or 'ltx_bibliography' in classes(node)
                        else 'related_work' if re.match(r'^(related works?|prior works?|literature review)', normalized) else None)
        value = {'section_id': node.get('id') or f"section-{len(self.sections) + 1:04d}", 'dom_id': node.get('id'),
                 'title': title, 'role': 'context' if context_kind else 'article', 'context_kind': context_kind,
                 'parent_section_id': context[-1]['section_id'] if context else None}
        self.sections.append(value)
        return [*context, value]

    def span(self, node, name):
        value = node.get(name)
        if value is None:
            match = next((re.fullmatch(r'ltx_' + name + r'_(\d+)', item) for item in classes(node) if re.fullmatch(r'ltx_' + name + r'_(\d+)', item)), None)
            value = match.group(1) if match else 1
        try:
            result = int(value)
            if not 1 <= result <= 1000:
                raise ValueError()
            return result
        except (TypeError, ValueError):
            self.issue('invalid_table_span', node, attribute=name)
            return 1

    def table(self, node, context):
        rows, headers, maths, images, links = [], [], [], [], []
        captions = [caption for caption in node.select('caption') if closest(caption, is_table) is node]
        cap = self.inline(captions)
        maths.extend(cap['math']); images.extend(cap['images']); links.extend(cap['links'])
        for row_node in node.select(ROW_SELECTOR):
            if closest(row_node, is_table) is not node:
                continue
            cells = []
            for cell in row_node.select(CELL_SELECTOR):
                if closest(cell, is_row) is not row_node or closest(cell, is_table) is not node:
                    continue
                value = self.inline([cell], table_owner=node)
                maths.extend(value['math']); images.extend(value['images']); links.extend(value['links'])
                cells.append({'text': value['text'], 'dom_id': cell.get('id'), 'rowspan': self.span(cell, 'rowspan'),
                              'colspan': self.span(cell, 'colspan'), 'scope': cell.get('scope') or ('col' if 'ltx_th_column' in classes(cell) else 'row' if 'ltx_th_row' in classes(cell) else None),
                              'is_header': cell.name == 'th' or 'ltx_th' in classes(cell) or cell.get('role') in {'columnheader', 'rowheader'},
                              'column_header': cell.get('role') == 'columnheader' or 'ltx_th_column' in classes(cell),
                              'headers_attribute': cell.get('headers')})
            if not cells:
                continue
            in_head = closest(row_node, lambda parent: isinstance(parent, Tag) and (parent.name == 'thead' or 'ltx_thead' in classes(parent)))
            is_header_row = bool(in_head and closest(in_head, is_table) is node) or all(cell['column_header'] for cell in cells) or all(cell['is_header'] and cell['scope'] != 'row' for cell in cells)
            value = {'dom_id': row_node.get('id'), 'cells': cells, 'source_row_index': len(rows) + len(headers) + 1}
            (headers if is_header_row else rows).append(value)
        # Some semantic grids use definition-list rows, not tr/td elements.
        if not headers and not rows and node.find('dt'):
            for term in node.find_all('dt'):
                if closest(term, is_table) is not node:
                    continue
                definition = term.find_next_sibling('dd')
                cells = []
                for item in [term, definition]:
                    if item is None:
                        continue
                    value = self.inline([item], table_owner=node)
                    maths.extend(value['math']); images.extend(value['images']); links.extend(value['links'])
                    cells.append({'text': value['text'], 'dom_id': item.get('id'), 'rowspan': 1, 'colspan': 1,
                                  'scope': 'row' if item is term else None, 'is_header': item is term, 'column_header': False, 'headers_attribute': None})
                rows.append({'dom_id': term.get('id'), 'cells': cells, 'source_row_index': len(rows) + 1})
        stray = [value for value in node.descendants if isinstance(value, NavigableString) and not isinstance(value, Comment)
                 and id(value) not in self.consumed and closest(value, is_table) is node]
        residual = self.inline(stray)
        merged = any(cell['rowspan'] > 1 or cell['colspan'] > 1 for row in [*headers, *rows] for cell in row['cells'])
        if not headers:
            self.issue('table_headers_unmarked_not_inferred', node)
        if not rows and not headers:
            self.issue('table_rows_unrecognized_or_empty', node)
            self.unparsed_tables += 1
        if merged:
            self.issue('merged_table_cells_preserved_visual_alignment_not_verified', node)
        if 'ltx_guessed_headers' in classes(node):
            self.issue('converter_guessed_table_headers', node)
        text_rows = []
        for label, row in sorted([('HEADER', row) for row in headers] + [('ROW', row) for row in rows], key=lambda pair: pair[1]['source_row_index']):
            text_rows.append(f"{label} {row['source_row_index']}: " + ' | '.join(cell['text'] + (f" [rowspan={cell['rowspan']},colspan={cell['colspan']}]" if cell['rowspan'] > 1 or cell['colspan'] > 1 else '') for cell in row['cells']))
        text = '\n'.join([part for part in [cap['text'], *text_rows, residual['text']] if part]) or '[Table structure detected, no readable rows; manual inspection required.]'
        equation_container = closest(node, lambda parent: isinstance(parent, Tag) and (parent.name == 'math' or bool(classes(parent) & EQUATION_CLASSES)))
        equation_layout = bool(classes(node) & EQUATION_CLASSES) or equation_container is not None
        self.table_count += 1
        self.emit('table', node, context, {'text': text, 'math': maths, 'images': images, 'links': links},
                  table={'headers': headers, 'rows': rows, 'caption': cap['text'], 'unstructured_text': residual['text'],
                         'headers_status': 'converter_guessed' if 'ltx_guessed_headers' in classes(node) else 'explicit' if headers else 'unmarked_not_inferred',
                         'source_representation': 'native_html_table' if node.name == 'table' else 'latexml_tabular' if 'ltx_tabular' in classes(node) else 'aria_table_or_grid',
                         'semantic_kind': 'equation_layout' if equation_layout else 'table_structure',
                         'source_classes': sorted(classes(node)), 'source_role': node.get('role'),
                         'in_math': closest(node, lambda parent: isinstance(parent, Tag) and parent.name == 'math') is not None,
                         'equation_container': {'tag': equation_container.name, 'dom_id': equation_container.get('id'), 'classes': sorted(classes(equation_container))} if equation_container else None,
                         'merged_cells_present': merged, 'column_alignment': 'source_dom_order_with_spans_not_reconstructed_visual_grid',
                         'table_read': False, 'visual_layout_inspected': False})
        for nested in node.select(TABLE_SELECTOR):
            if closest(nested, is_table) is node:
                self.walk(nested, context)

    def figure(self, node, context):
        captions = [item for item in node.select('figcaption,.ltx_caption') if closest(item, lambda parent: isinstance(parent, Tag) and (parent.name == 'figure' or bool(classes(parent) & {'ltx_figure', 'ltx_table'}))) is node]
        caption_ids = {id(item) for item in captions}
        captions = [item for item in captions if not any(id(parent) in caption_ids for parent in item.parents)]
        value = self.inline(captions)
        for caption in captions:
            self.handled.add(id(caption))
        for image in node.find_all('img'):
            if (not closest(image, is_table) and not any(id(parent) in self.handled for parent in image.parents)
                    and closest(image, lambda parent: isinstance(parent, Tag) and (parent.name == 'figure' or bool(classes(parent) & {'ltx_figure', 'ltx_table'}))) is node):
                media = self.image(image)
                value['images'].append(media)
                self.handled.add(id(image))
        caption = value['text']
        table_container = 'ltx_table' in classes(node) or bool(re.match(r'^Table\s+\d', caption, re.I))
        recognized = bool(node.select_one(TABLE_SELECTOR))
        if table_container and not recognized:
            self.issue('table_container_without_recognized_tabular_structure', node)
            self.unparsed_tables += 1
        image_lines = [f"IMAGE (not inspected): {image['source_url'] or '[no HTTP image URL]'}; ALT: {image['alt'] or '[missing]'}" + (f"; LINK: {image['link_url']}" if image['link_url'] else '') for image in value['images']]
        value['text'] = '\n'.join([caption, *image_lines]).strip() or '[Figure/table container has no readable caption; visual inspection pending.]'
        self.emit('table_caption' if table_container else 'figure', node, context, value,
                  figure={'caption': caption, 'images_inspected': False, 'table_container': table_container,
                          'recognized_tabular_child': recognized})
        self.children(node, context)

    def structural(self, node):
        return isinstance(node, Tag) and (node.name in BLOCK_TAGS or is_table(node) or bool(classes(node) & (SECTION_CLASSES | {'ltx_p', 'ltx_para', 'ltx_figure', 'ltx_table'})) or (node.name == 'math' and node.get('display') == 'block'))

    def children(self, node, context):
        buffer = []
        def flush():
            if buffer:
                self.emit('list_item' if node.name == 'li' else 'paragraph', node, context, self.inline(buffer))
                buffer.clear()
        for child in list(node.children):
            if id(child) in self.handled or isinstance(child, Comment):
                continue
            if isinstance(child, Tag) and (self.structural(child) or child.find(self.structural)):
                flush(); self.walk(child, context)
            else:
                buffer.append(child)
        flush()

    def walk(self, node, context):
        if id(node) in self.handled:
            return
        if is_table(node):
            self.table(node, context); return
        if node.name == 'figure' or bool(classes(node) & {'ltx_figure', 'ltx_table'}):
            self.figure(node, context); return
        if node.name == 'section' or bool(classes(node) & SECTION_CLASSES):
            context = self.section(node, context)
        if re.fullmatch(r'h[1-6]', node.name or ''):
            self.emit('heading', node, context, self.inline([node])); return
        if node.name == 'math':
            self.emit('equation', node, context, self.inline([node])); return
        if node.name == 'dl':
            self.definition_lists += 1
        if node.name == 'pre':
            # Whitespace within code is retained rather than collapsed.
            value = self.inline([node])
            value['text'] = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', node.get_text('', strip=False))
            self.emit('preformatted', node, context, value); return
        self.children(node, context)

    def extract(self):
        for node in self.article.select('.ltx_ERROR,.ltx_error'):
            self.issue('html_conversion_error_marker', node, text=clean(node.get_text(' ', strip=True)))
        self.walk(self.article, [])
        remaining = [node for node in self.nodes if id(node) not in self.consumed]
        if remaining:
            self.issue('unclassified_text_retained_at_packet_end', self.article, text_node_count=len(remaining))
            for node in remaining:
                self.emit('unclassified_text', node.parent, [], self.inline([node]))
        duplicates = Counter(row['text'] for row in self.blocks if row['text'])
        if not self.table_count and any(re.search(r'\bTable\s+\d', row['text']) for row in self.blocks):
            self.issue('table_mentions_without_detected_semantic_table', self.article)
        return {'blocks': self.blocks, 'sections': self.sections, 'issues': self.issues,
                'extraction_coverage': {'eligible_dom_text_nodes': len(self.nodes),
                    'accounted_for_dom_text_nodes': sum(id(node) in self.consumed for node in self.nodes),
                    'unaccounted_dom_text_nodes': sum(id(node) not in self.consumed for node in self.nodes),
                    'definition': 'DOM text retained once or represented by math alternative; not human/AI reading coverage',
                    'block_count': len(self.blocks), 'section_count': len(self.sections),
                    'semantic_table_count': self.table_count, 'native_html_table_count': len(self.article.find_all('table')),
                    'table_count_definition': TABLE_COUNT_DEFINITION,
                    'equation_layout_table_count': sum(block.get('table', {}).get('semantic_kind') == 'equation_layout' for block in self.blocks),
                    'other_table_structure_count': sum(block.get('table', {}).get('semantic_kind') == 'table_structure' for block in self.blocks),
                    'figure_count': sum(block['kind'] == 'figure' for block in self.blocks),
                    'unparsed_table_structure_count': self.unparsed_tables, 'definition_list_count': self.definition_lists,
                    'math_count': self.math_count, 'math_with_alt_or_tex_count': self.math_alt_count,
                    'image_count': self.image_count, 'duplicate_text_groups_preserved': sum(count > 1 for count in duplicates.values()),
                    'rendered_text_characters': sum(len(row['text']) for row in self.blocks)}}


def reading_segments(blocks, segment_chars=4000):
    if not 200 <= segment_chars <= 20000:
        raise ValueError('reading_packet_segment_chars_out_of_range')
    result = []
    for block in blocks:
        text, start = block['text'], 0
        while start < len(text):
            end = min(start + segment_chars, len(text))
            if end < len(text):
                boundary = max(text.rfind('\n', start + segment_chars // 2, end), text.rfind(' ', start + segment_chars // 2, end))
                if boundary >= 0:
                    end = boundary + 1
            result.append({'segment_index': len(result) + 1, 'block_index': block['block_index'], 'start_char': start, 'end_char': end})
            start = end
    return result


def build_reading_packet(raw, observation, work, *, segment_chars=4000):
    """Pure extraction. The observation must bind raw bytes to a canonical work."""
    expected_hash = observation.get('raw_sha256')
    if not isinstance(raw, bytes) or len(raw) > MAX_RAW_BYTES or not re.fullmatch(r'[0-9a-f]{64}', str(expected_hash or '')) or sha256(raw) != expected_hash:
        raise ValueError('reading_packet_raw_sha256_mismatch_or_size_limit')
    if work.get('work_id') != observation.get('work_id'):
        raise ValueError('reading_packet_canonical_work_mismatch')
    source_id, source_version = official_html_identity(observation.get('source_url'))
    effective = observation.get('effective_url') or observation['source_url']
    effective_id, effective_version = official_html_identity(effective)
    observed_identity = arxiv_identity(observation.get('arxiv_id'))
    if (source_id not in canonical_arxiv_ids(work) or effective_id != source_id
            or (observation.get('arxiv_id') and (not observed_identity or observed_identity[0] != source_id))):
        raise ValueError('reading_packet_canonical_arxiv_mismatch')
    expected_version = observation.get('version') or effective_version or source_version
    if len({value for value in [expected_version, effective_version, source_version] if value}) > 1:
        raise ValueError('reading_packet_observation_version_mismatch')
    soup = BeautifulSoup(raw, 'html.parser')
    valid, version, proofs, error = page_identity(soup, effective, source_id, expected_version)
    if not valid:
        raise ValueError('reading_packet_' + str(error))
    article = soup.select_one('article.ltx_document,.ltx_document,article')
    if article is None:
        raise ValueError('reading_packet_article_missing')
    removed = Counter()
    for node in list(article.select(REMOVE)):
        if node.parent is not None:
            removed[node.name] += 1; node.decompose()
    for comment in list(article.find_all(string=lambda value: isinstance(value, Comment))):
        comment.extract()
    base_tag = soup.find('base', href=True)
    resource_base = safe_url(effective, base_tag['href']) if base_tag else effective
    extracted = ArticleExtractor(article, effective, resource_base=resource_base).extract()
    if not extracted['blocks']:
        raise ValueError('reading_packet_article_text_missing')
    source_fields = ('work_id', 'source_url', 'effective_url', 'observed_at', 'fetched_at', 'observation_id',
                     'parent_observation_id', 'processing_basis', 'status', 'raw_sha256', 'parser_version', *TRANSPORT_FIELDS)
    source = {key: observation[key] for key in source_fields if key in observation}
    source.update(arxiv_id=source_id, version=version, identity_verified=True, document_base_url=resource_base,
                  identity_proofs=[{'kind': kind, 'arxiv_id': identity[0], 'version': identity[1]} for kind, identity in proofs])
    source.setdefault('transport_verification', 'legacy_unrecorded')
    gaps = []
    if not version:
        gaps.append('source_version_unresolved')
    if observation.get('status') != 'full_text_available':
        gaps.append('source_observation_not_full_text_available')
    if source['transport_verification'] != 'complete':
        gaps.append('transport_completion_not_verified')
    gaps.extend(['images_not_inspected', 'supplementary_materials_not_inspected', 'html_conversion_fidelity_not_independently_verified'])
    segments = reading_segments(extracted['blocks'], segment_chars)
    packet = {'schema_version': '1', 'extractor_version': EXTRACTOR_VERSION, 'work_id': work['work_id'],
              'packet_id': 'reading-packet:' + sha256(encode({'work_id': work['work_id'], 'raw_sha256': expected_hash, 'extractor': EXTRACTOR_VERSION, 'segment_chars': segment_chars}).encode())[:32],
              'privacy': 'private_source_text_do_not_publish', 'source': source, **extracted,
              'removed_nonarticle_ui': dict(sorted(removed.items())), 'reading_segments': segments, 'segment_chars': segment_chars,
              'preparation_status': 'prepared_not_read',
              'reading_coverage': {'blocks_read': 0, 'segments_read': 0, 'tables_read': 0, 'images_inspected': 0,
                                   'article_read_complete': False, 'preparation_is_not_reading': True},
              'gaps': gaps,
              'limits': ['Complete-article scope retains abstracts, related work, conclusions, appendices and references present in this HTML.',
                         'References and related work are context, not usage evidence; no passage is automatically verified.',
                         'Headers/rows and merged-cell spans are retained; visual column alignment is not reconstructed or certified.',
                         TABLE_COUNT_DEFINITION,
                         'Math alt/TeX is preferred to duplicate MathML alternatives; image pixels and supplements remain unread.',
                         'Prepared text, printed segments and EOF are not proof that an AI or person has read the article.']}
    packet['packet_sha256'] = sha256(encode(packet).encode())
    return packet


def trusted_file(value, root):
    """Reject traversal, symlinks inside the chosen root, and nonregular files."""
    root = Path(root).absolute()
    if root.is_symlink():
        raise ValueError('reading_packet_symlink_root_forbidden')
    candidate = Path(value)
    if '..' in candidate.parts:
        raise ValueError('reading_packet_path_traversal_forbidden')
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved_root = root.resolve(strict=True)
    if not candidate.resolve(strict=True).is_relative_to(resolved_root):
        raise ValueError('reading_packet_cache_reference_outside_root')
    for path in [candidate, *candidate.parents]:
        if path.is_symlink():
            raise ValueError('reading_packet_symlink_reference_forbidden')
        if path.resolve() == resolved_root:
            break
    if not candidate.is_file():
        raise ValueError('reading_packet_regular_file_required')
    return candidate


def read_regular(path, *, maximum=None):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or (maximum is not None and info.st_size > maximum):
            raise ValueError('reading_packet_regular_file_or_size_limit')
        value = stream.read(None if maximum is None else maximum + 1)
        if maximum is not None and len(value) > maximum:
            raise ValueError('reading_packet_size_limit')
        return value


def packet_filename(work_id):
    return sha256(work_id.encode())[:24] + '.json'


def write_packet(packet, output):
    output = Path(output).absolute()
    if '..' in output.parts or any(path.is_symlink() for path in [output, output / 'packets']):
        raise ValueError('reading_packet_output_symlink_or_traversal')
    for parent in output.parents:
        if parent.is_symlink() and parent != Path('/var'):
            raise ValueError('reading_packet_output_symlink_ancestor')
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory = output / 'packets'
    directory.mkdir(exist_ok=True, mode=0o700)
    target = directory / packet_filename(packet['work_id'])
    if target.is_symlink():
        raise ValueError('reading_packet_output_symlink_forbidden')
    contents = (encode(packet) + '\n').encode()
    if target.exists() and read_regular(target) == contents:
        return target, False
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, prefix='.packet-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name); stream.write(contents)
        temporary.replace(target); temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return target, True


def latest_observations(records):
    latest = {}
    for row in records:
        wid = row.get('work_id')
        if not wid or not row.get('observed_at'):
            raise ValueError('reading_packet_observation_identity_and_time_required')
        if wid not in latest or row['observed_at'] >= latest[wid]['observed_at']:
            latest[wid] = row
    return latest


def load_selected_works(catalog, wanted):
    works, owners, ids = {}, defaultdict(set), set()
    for work in table_rows(Path(catalog), 'works'):
        wid = work.get('work_id')
        if not wid or wid in ids:
            raise ValueError('reading_packet_duplicate_canonical_work')
        ids.add(wid)
        if wid in wanted:
            works[wid] = work
        for aid in canonical_arxiv_ids(work):
            owners[aid].add(wid)
    for wid, work in works.items():
        if any(owners[aid] != {wid} for aid in canonical_arxiv_ids(work)):
            raise ValueError('reading_packet_ambiguous_canonical_arxiv:' + wid)
    return works


def prepare_packets(observations, cache, catalog, output, *, work_ids=None, segment_chars=4000):
    cache = Path(cache).absolute()
    source = trusted_file(Path(observations).absolute(), cache)
    snapshot = read_regular(source).decode()
    records, incomplete_tail = [], False
    lines = snapshot.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            # The collector may be appending concurrently. Ignore only an
            # incomplete final line, never rewrite or repair its private log.
            if index == len(lines) - 1 and not snapshot.endswith('\n'):
                incomplete_tail = True
            else:
                raise
    latest = latest_observations(records)
    selected = list(dict.fromkeys(work_ids)) if work_ids is not None else sorted(wid for wid, row in latest.items() if row.get('cache_ref') and row.get('status') in {'full_text_available', 'partial_text'})
    works = load_selected_works(catalog, set(selected))
    output = Path(output).absolute()
    if output.resolve().is_relative_to(cache.resolve()):
        raise ValueError('reading_packet_output_must_not_modify_source_cache')
    prepared, failed = [], []
    for wid in selected:
        try:
            if wid not in works or wid not in latest:
                raise ValueError('canonical_work_or_source_observation_missing')
            row = latest[wid]
            if row.get('status') not in {'full_text_available', 'partial_text'} or not row.get('cache_ref'):
                raise ValueError('validated_cached_article_not_available')
            reference = Path(row['cache_ref'])
            if not reference.is_absolute():
                reference = cache / reference
            raw_path = trusted_file(reference, cache / 'objects')
            raw = read_regular(raw_path, maximum=MAX_RAW_BYTES)
            packet = build_reading_packet(raw, row, works[wid], segment_chars=segment_chars)
            path, changed = write_packet(packet, output)
            prepared.append({'work_id': wid, 'path': str(path), 'changed': changed, **packet_summary(packet)})
        except (ValueError, OSError, KeyError) as error:
            failed.append({'work_id': wid, 'status': 'not_prepared', 'reason': str(error)})
    return {'status': 'prepared_not_read', 'selection': 'latest_observation_by_time_then_append_order_not_latest_publication_assertion',
            'observation_snapshot_incomplete_tail': incomplete_tail,
            'prepared_count': len(prepared), 'failed_count': len(failed), 'prepared': prepared, 'failed': failed}


def packet_summary(packet):
    return {'packet_id': packet['packet_id'], 'packet_sha256': packet['packet_sha256'], 'source_version': packet['source']['version'],
            'raw_sha256': packet['source']['raw_sha256'], 'preparation_status': packet['preparation_status'],
            'segment_count': len(packet['reading_segments']), 'extraction_coverage': packet['extraction_coverage'],
            'table_count_definition': TABLE_COUNT_DEFINITION,
            'issue_counts': dict(Counter(issue['code'] for issue in packet['issues'])), 'gaps': packet['gaps']}


def reading_record_template(packet):
    """Suggested minimal declaration only; never persist/submit a read record.

    A real ledger should reject template_only, require an identified reader
    and timestamp, and bind every declared range to its actual text projection
    hash (raw-article plain text OR this packet's segments). Claims require
    source locators and explicit reader assessment; printing EOF proves none
    of these. A compact public ledger must omit the original article text.
    """
    return {'schema_version': '1', 'record_status': 'template_only_not_a_read_record',
            'work_id': packet['work_id'],
            'source': {key: packet['source'].get(key) for key in ('source_url', 'version', 'raw_sha256')},
            'reader_id': None, 'reader_kind': None, 'declared_read_at': None,
            'reading_basis': None, 'reading_text_sha256': None, 'text_projection_method': None,
            'packet_sha256_if_used': packet['packet_sha256'],
            'declared_read_ranges': [], 'declared_section_ids': [], 'declared_table_ids_checked': [], 'declared_math_ids_checked': [],
            'declared_eof_reached': None, 'verified_claims': [], 'unresolved_claims': [],
            'images_inspected': [], 'uninspected_modalities': ['image_pixels', 'audio_video', 'supplementary_materials'],
            'declaration_requirements': {
                'ranges': 'Each range: {unit:unicode_codepoints|packet_segments,start,end}; codepoints zero-based half-open, packet segments one-based inclusive.',
                'reading_basis': 'raw_article_projection|reading_packet; the text hash and projection method must match the actual material presented to this reader.',
                'verified_claims': 'Each claim: {claim_id,paraphrase,source_dom_ids,table_cells_if_used,reader_assessment,limits}; source-confirmed author reports are not independent experimental validation, and no usage assertion is automatic.',
                'completion': 'Declared ranges/sections and EOF are a reader declaration, not independent proof of comprehension or image inspection.',
                'privacy': 'Only source hashes, locators, declarations and concise paraphrases belong in a public ledger; never full paragraphs or private cache paths.'}}


def load_packet(output, work_id):
    output = Path(output).absolute()
    path = trusted_file(output / 'packets' / packet_filename(work_id), output / 'packets')
    packet = json.loads(read_regular(path))
    expected = packet.get('packet_sha256')
    if packet.get('work_id') != work_id or sha256(encode({key: value for key, value in packet.items() if key != 'packet_sha256'}).encode()) != expected:
        raise ValueError('reading_packet_saved_identity_or_hash_mismatch')
    return packet


def render_range(packet, start=1, end=None):
    segments = packet['reading_segments']
    end = min(len(segments), start + 7 if end is None else end)
    if start < 1 or start > len(segments) + 1 or end < start - 1 or (end < start and start <= len(segments)):
        raise ValueError('reading_packet_invalid_segment_range')
    output = [f"PRIVATE SOURCE TEXT — {packet['work_id']} {packet['source']['version'] or 'version unresolved'}",
              f"Packet {packet['packet_sha256']} | {packet['source']['source_url']}",
              f"Segments {start}–{end} of {len(segments)}; prepared_not_read; images NOT inspected.", TABLE_COUNT_DEFINITION]
    for segment in segments[start - 1:end]:
        block = packet['blocks'][segment['block_index'] - 1]
        section = ' > '.join(row['title'] for row in block['section_path']) or 'Article front matter / unsectioned text'
        output.extend([f"\n[{segment['segment_index']}/{len(segments)}] {block['kind']} | {section} | DOM {block['dom_id'] or '(none)'} | {block['evidence_role']}",
                       f"Source: {block['source_locator']} | block {block['block_index']} chars {segment['start_char']}:{segment['end_char']}",
                       block['text'][segment['start_char']:segment['end_char']]])
    output.append('\nEOF — packet text emitted, NOT a reading/verification certificate.' if end == len(segments) else f'\nNEXT --start {end + 1} --end {min(end + 8, len(segments))}')
    return '\n'.join(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations', type=Path, default=ROOT / '.research/hardware-fulltext/observations.jsonl')
    parser.add_argument('--cache', type=Path, default=ROOT / '.research/hardware-fulltext')
    parser.add_argument('--catalog', type=Path, default=ROOT / 'data/catalog')
    parser.add_argument('--output', type=Path, default=ROOT / '.research/fulltext-reading')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--work-ids', nargs='+')
    action.add_argument('--all-cached', action='store_true')
    action.add_argument('--show', metavar='WORK_ID')
    action.add_argument('--summary', metavar='WORK_ID')
    action.add_argument('--record-template', metavar='WORK_ID')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int)
    parser.add_argument('--segment-chars', type=int, default=4000)
    args = parser.parse_args(argv)
    if '.research' not in args.output.absolute().parts:
        parser.error('Reading packets contain original source text; --output must remain in a private .research directory.')
    if args.show or args.summary or args.record_template:
        packet = load_packet(args.output, args.show or args.summary or args.record_template)
        print(render_range(packet, args.start, args.end) if args.show else encode(reading_record_template(packet) if args.record_template else packet_summary(packet)))
        return 0
    result = prepare_packets(args.observations, args.cache, args.catalog, args.output, work_ids=args.work_ids, segment_chars=args.segment_chars)
    print(encode(result))
    return int(bool(result['failed']))


if __name__ == '__main__':
    raise SystemExit(main())

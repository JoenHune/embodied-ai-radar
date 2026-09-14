"""Complete possibly capped search-page author lists from the same official version."""
import argparse
import hashlib
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


def parse_authors(body, arxiv_id):
    page = BeautifulSoup(body, 'html.parser')
    identity = page.find('meta', attrs={'name': 'citation_arxiv_id'})
    if not identity or re.sub(r'v\d+$', '', identity.get('content', '')) != arxiv_id:
        raise ValueError('official_arxiv_identity_missing')
    authors = [node.get('content', '').strip() for node in page.select('meta[name="citation_author"]')]
    if not authors or any(not name for name in authors):
        raise ValueError('official_author_list_missing')
    displayed = [' '.join(node.get_text(' ', strip=True).split()) for node in page.select('.authors a')]
    if len(displayed) != len(authors) or any(not name for name in displayed):
        raise ValueError('author_display_and_citation_counts_disagree')
    # citation_author uses "Family, Given"; preserve the full author section's
    # natural spellings so existing person-name candidate lookup remains valid.
    return displayed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.input.read_text())
    checks = []
    for row in rows:
        if len(row.get('authors', [])) < 25:
            continue
        url = f"https://arxiv.org/abs/{row['arxiv_id']}{row['version']}"
        observed = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'EmbodiedResearchRadar/3.1 metadata verification'})
            with urllib.request.urlopen(request, timeout=35) as response:
                body = response.read()
            authors = parse_authors(body, row['arxiv_id'])
            if len(authors) < len(row['authors']):
                raise ValueError('author_count_shrank_requires_review')
            previous = row['authors']
            row.update(authors=authors, raw_authors=authors, authors_complete=True, authors_source_url=url)
            row.setdefault('source_observations', []).append({'source_type': 'official_arxiv_version_abs', 'source_url': url, 'fetched_at': observed, 'raw_sha256': hashlib.sha256(body).hexdigest(), 'source_status': 'ok', 'fields': ['authors']})
            checks.append({'arxiv_id': row['arxiv_id'], 'source_url': url, 'observed_at': observed, 'before': len(previous), 'after': len(authors), 'status': 'verified', 'raw_sha256': hashlib.sha256(body).hexdigest()})
        except Exception as error:
            row['authors_complete'] = False
            checks.append({'arxiv_id': row['arxiv_id'], 'source_url': url, 'observed_at': observed, 'status': 'unresolved', 'error_type': type(error).__name__})
        time.sleep(3.2)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + '\n')
    args.receipts.write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(checks, ensure_ascii=False))


if __name__ == '__main__':
    main()

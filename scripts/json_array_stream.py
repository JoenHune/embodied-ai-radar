"""Read public JSON arrays without holding the entire encoded file in memory."""
from __future__ import annotations
import json
from pathlib import Path


def iter_json_array(path, chunk_size=65536):
    path = Path(path)
    if not path.exists():
        return
    decoder = json.JSONDecoder()
    with path.open() as stream:
        buffer, offset, eof = '', 0, False

        def refill():
            nonlocal buffer, offset, eof
            chunk = stream.read(chunk_size)
            buffer = buffer[offset:] + chunk
            offset = 0
            eof = not chunk

        def skip_space():
            nonlocal offset
            while True:
                while offset < len(buffer) and buffer[offset] in ' \t\r\n':
                    offset += 1
                if offset < len(buffer) or eof:
                    return
                refill()

        refill()
        skip_space()
        if offset == len(buffer) or buffer[offset] != '[':
            raise ValueError('Expected a public JSON array')
        offset += 1
        first = True
        while True:
            skip_space()
            if offset < len(buffer) and buffer[offset] == ']':
                offset += 1
                skip_space()
                if offset != len(buffer):
                    raise ValueError('Trailing data after JSON array')
                return
            if not first:
                if offset == len(buffer) or buffer[offset] != ',':
                    raise ValueError('Expected JSON array separator')
                offset += 1
                skip_space()
                if offset < len(buffer) and buffer[offset] == ']':
                    raise ValueError('Trailing JSON array comma')
            while True:
                try:
                    value, end = decoder.raw_decode(buffer, offset)
                    # A number may have been split at the current buffer edge.
                    if not eof and (end == len(buffer) or buffer[end] not in ' \t\r\n,]'):
                        refill()
                        continue
                    break
                except json.JSONDecodeError:
                    if eof:
                        raise
                    refill()
            offset = end
            first = False
            yield value
            if offset >= chunk_size:
                refill()

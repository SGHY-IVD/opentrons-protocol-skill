#!/usr/bin/env python3
"""Check local Markdown routes in the active skill entry and references, offline."""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'(?<!!)\[[^\]\n]+\]\(([^\s)]+)(?:\s+"[^"]*")?\)')


def outside_code(text):
    fence = None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence is None:
            yield line


def heading_anchors(path):
    seen = Counter()
    anchors = set()
    for line in outside_code(path.read_text()):
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if not match:
            continue
        title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', match[1]).lower()
        title = title.replace('`', '')
        slug = ''.join(c for c in title if c in '_- ' or unicodedata.category(c)[0] in 'LNM').replace(' ', '-')
        count = seen[slug]
        seen[slug] += 1
        anchors.add(slug if count == 0 else f'{slug}-{count}')
    return anchors


def check():
    sources = [ROOT / 'SKILL.md', *sorted((ROOT / 'references').glob('*.md')),
               *sorted((ROOT / 'references').glob('*.txt'))]
    errors, checked = [], 0
    cache = {}
    for source in sources:
        for line_number, line in enumerate(outside_code(source.read_text()), 1):
            for match in LINK.finditer(line):
                target = unquote(match[1].strip('<>'))
                parts = urlsplit(target)
                if parts.scheme or parts.netloc:
                    continue
                path = (source.parent / parts.path).resolve() if parts.path else source
                checked += 1
                if not path.exists():
                    errors.append({'source': str(source.relative_to(ROOT)), 'target': target,
                                   'error': 'missing file'})
                elif parts.fragment and path.suffix == '.md':
                    if path not in cache:
                        cache[path] = heading_anchors(path)
                    if parts.fragment not in cache[path]:
                        errors.append({'source': str(source.relative_to(ROOT)), 'target': target,
                                       'error': 'missing heading'})
    return {'files': len(sources), 'local_routes': checked, 'errors': errors}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['errors']))

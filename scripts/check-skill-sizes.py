#!/usr/bin/env python3
"""Fail if any skill's SKILL.md body exceeds Antigravity's load limit.

Antigravity loads only the first 24,000 bytes of a SKILL.md body (the file
minus its leading YAML frontmatter). Anything past that is silently dropped.
"""
import sys
from pathlib import Path

LIMIT = 24_000


def body_bytes(text: str) -> int:
    if text.startswith('---\n'):
        end = text.find('\n---\n', 4)
        if end != -1:
            text = text[end + len('\n---\n'):]
    return len(text.encode('utf-8'))


def main(root: Path) -> int:
    over = []
    for path in sorted(root.glob('skills/*/SKILL.md')):
        size = body_bytes(path.read_text(encoding='utf-8'))
        print(f'{size:>7} {path}')
        if size > LIMIT:
            over.append((path, size))
    for path, size in over:
        print(f'FAIL {path}: body is {size} bytes; limit is {LIMIT}', file=sys.stderr)
    return 1 if over else 0


if __name__ == '__main__':
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')))

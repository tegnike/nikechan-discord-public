#!/usr/bin/env python3
"""Analyze discord-history JSON export (messages array).

Usage:
  python3 analyze_channel_messages.py /path/to/fetch.json

Outputs:
- basic counts (total/bot/human)
- top authors by display_name優先
- daily/hourly counts
- simple category hits
- request-like human messages and long gaps
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime


def load_messages(path: Path):
    data = json.loads(path.read_text(encoding='utf-8'))
    msgs = data.get('messages', [])
    return msgs


def analyze(msgs):
    # normalize datetime
    for m in msgs:
        m['dt'] = datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')).astimezone(ZoneInfo('Asia/Tokyo'))
    msgs.sort(key=lambda x: x['dt'])

    total = len(msgs)
    bot = sum(1 for m in msgs if m.get('author', {}).get('bot'))
    author = Counter((m['author']['display_name'] or m['author']['username']) for m in msgs)
    daily = Counter(m['dt'].date().isoformat() for m in msgs)
    hourly = Counter(m['dt'].strftime('%Y-%m-%d %H:00') for m in msgs)

    cats = {
        'tools': re.compile(r'web_search|web_extract|skill_view|discord-summary|discord-reminder|terminal\(|preflight compression|compacting context|cronjob', re.I),
        'analysis': re.compile(r'要約|まとめ|分析|summary|検証|決定|TODO', re.I),
        'video': re.compile(r'動画|video|seedance|wan2|hotogen|iwara|画像', re.I),
        'paper': re.compile(r'arxiv|論文|moshi|personaplex|研究', re.I),
        'cost': re.compile(r'コスト|クレジット|料金|トークン|token|価格|レート', re.I),
        'reminder': re.compile(r'リマインダー|reminder|rem_', re.I),
    }

    cat_counts = Counter()
    for m in msgs:
        txt = (m.get('content', '') or '').lower() + ' ' + ' '.join((e.get('description', '') or '').lower() for e in m.get('embeds', []))
        for k, rx in cats.items():
            if rx.search(txt):
                cat_counts[k] += 1

    req = [m for m in msgs if (not m.get('author', {}).get('bot')) and re.search(r'要約|まとめ|分析|このチャンネル|このあたり|ここ12時間|直近', m.get('content') or '')]

    gaps = []
    for prev, cur in zip(msgs, msgs[1:]):
        d = cur['dt'] - prev['dt']
        if d >= timedelta(hours=6):
            gaps.append((prev['dt'], cur['dt'], d.total_seconds() / 3600))

    print(f"count={total} bot={bot} human={total-bot}")
    print('top_authors', author.most_common(10))
    print('daily', dict(daily))
    print('top_hours', hourly.most_common(12))
    print('categories', cat_counts)
    print('human_requests', len(req))
    if req:
        print('first_req', req[0]['dt'], (req[0]['author']['display_name'] or req[0]['author']['username']), req[0]['content'][:100])
        print('last_req', req[-1]['dt'], (req[-1]['author']['display_name'] or req[-1]['author']['username']), req[-1]['content'][:100])
    print('large_gaps(>6h)', len(gaps))
    for g in gaps[:20]:
        print(g[0], '->', g[1], 'hours=', round(g[2],2))


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: python3 analyze_channel_messages.py /path/to/fetch.json')
    path = Path(sys.argv[1])
    analyze(load_messages(path))


if __name__ == '__main__':
    main()

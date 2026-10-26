import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOM  = os.path.join(ROOT, "domains")
OUT  = os.path.join(DOM, "registry.html")

TLDS = [
    ("com", 2), ("net", 2), ("org", 2), ("mt", 3), ("zf", 3), ("stu", 1),
    ("lyra.com", 1), ("lyra.net", 1), ("lyra.org", 1), ("lyra.mt", 2), ("lyra.zf", 2),
    ("lyra.stu", 0), ("taqi.lyra", 0), ("taqi.tk", 0), ("taqi.tl", 0), ("lyra.tk", 0),
    ("app", 100), ("site", 100), ("lyra.app", 50), ("lyra.site", 50),
    ("oneapp.dev", 10), ("duckdns.org", 10), ("ai.studio", 20)
]

HEAD = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Lyra Registry</title>
<style>body{background:#07070c;color:#e9e9f2;font-family:monospace;padding:28px}
h1{color:#a78bfa} h2{color:#22d3ee;font-size:16px;margin-top:20px}
pre{background:#0e0e18;padding:14px;border-radius:12px;border:1px solid #2a2a44}</style>
</head><body><h1>Lyra Registry</h1><p>Format: name=path|qr_url</p>'''

FOOT = '</body></html>'

def read_existing(path):
    if not os.path.exists(path): return {}
    txt = open(path, encoding="utf-8").read()
    blocks = re.findall(r'<pre[^>]*data-tld="([^"]+)"[^>]*>(.*?)</pre>', txt, re.DOTALL)
    return {tld: inner.strip() for tld, inner in blocks}

def main():
    os.makedirs(DOM, exist_ok=True)
    existing = read_existing(OUT)
    
    parts = [HEAD]
    for tld, price in TLDS:
        inner = existing.get(tld, "taqi=ai/taqi.html|https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://nexura-m.github.io/builder/ai/taqi.html&format=jpg" if tld == "mt" else "")
        parts.append(f'<h2>.{tld}</h2><pre class="lyra-target" data-tld="{tld}" data-price="{price}">{inner}</pre>')
    parts.append(FOOT)
    
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"✅ Generated {OUT}")

if __name__ == "__main__":
    main()

import os, re, base64, urllib.parse
from flask import Flask, request, jsonify, send_from_directory
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, static_folder=None)

FREE_TLDS  = {'lyra.stu', 'taqi.lyra', 'taqi.tk', 'taqi.tl', 'lyra.tk'}
CATEGORIES = {'ai', 'web', 'game', 'other'}
REGISTRY   = 'domains/registry.html'

GITHUB_TOKEN  = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO   = os.environ.get('GITHUB_REPOSITORY', '')
GITHUB_BRANCH = os.environ.get('GITHUB_REF_NAME', 'main')

def pages_url():
    url = os.environ.get('PAGES_URL', '').strip()
    if url: return url.rstrip('/')
    if GITHUB_REPO and '/' in GITHUB_REPO:
        owner, name = GITHUB_REPO.split('/', 1)
        if name.lower() == f'{owner.lower()}.github.io': return f'https://{owner.lower()}.github.io'
        return f'https://{owner.lower()}.github.io/{name}'
    return ''

def gh_headers():
    return {'Authorization': f'Bearer {GITHUB_TOKEN}', 'Accept': 'application/vnd.github+json'}

def gh_get(path):
    if not GITHUB_TOKEN or not GITHUB_REPO: return None
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}'
    try:
        r = requests.get(url, headers=gh_headers(), params={'ref': GITHUB_BRANCH}, timeout=20)
        if r.status_code == 200:
            return base64.b64decode(r.json()['content']).decode('utf-8')
    except: pass
    return None

def gh_put(path, text, message):
    if not GITHUB_TOKEN or not GITHUB_REPO: return False, 'no creds'
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}'
    sha = None
    try:
        r = requests.get(url, headers=gh_headers(), params={'ref': GITHUB_BRANCH}, timeout=20)
        if r.status_code == 200: sha = r.json().get('sha')
    except: pass
    
    body = {'message': message, 'content': base64.b64encode(text.encode('utf-8')).decode('ascii'), 'branch': GITHUB_BRANCH}
    if sha: body['sha'] = sha
    
    try:
        r = requests.put(url, headers=gh_headers(), json=body, timeout=20)
        return (r.status_code in (200, 201)), r.text[:300]
    except Exception as e: return False, str(e)

def add_entry(tld, entry_line):
    content = gh_get(REGISTRY)
    if content is None: return False, 'Registry not found'
    
    pattern = re.compile(r'(<pre\b[^>]*\bdata-tld=["\']' + re.escape(tld) + r'["\'][^>]*>)(.*?)(</pre>)', re.DOTALL)
    m = pattern.search(content)
    if not m: return False, f'no data-tld="{tld}" block'
    
    new_inner = (m.group(2).rstrip('\n') + '\n' + entry_line + '\n').lstrip('\n')
    new_content = content[:m.start(2)] + new_inner + content[m.end(2):]
    return gh_put(REGISTRY, new_content, f'Add {entry_line} to .{tld}')

@app.route('/')
def home():
    return send_from_directory(ROOT, 'builder.html')

@app.route('/api/config')
def config():
    return jsonify(pages_url=pages_url(), free_tlds=sorted(FREE_TLDS))

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.get_json() or {}
    category = (data.get('category') or '').lower()
    name     = (data.get('name') or '').strip()
    html     = data.get('html') or ''
    tld      = (data.get('tld') or '').strip().lower()

    if category not in CATEGORIES: return jsonify(ok=False, error='invalid category'), 400
    if not re.match(r'^[a-zA-Z0-9_-]{2,32}$', name): return jsonify(ok=False, error='invalid name'), 400
    if len(html) < 50: return jsonify(ok=False, error='html too short'), 400
    if tld not in FREE_TLDS: return jsonify(ok=False, error='paid', contact='https://mustjab-king-lyra.hf.space/'), 402

    slug = name.lower()
    path = f'{category}/{slug}.html'
    if gh_get(path) is not None: return jsonify(ok=False, error=f'{slug}.{tld} already taken'), 409

    ok, msg = gh_put(path, html, f'Add {slug}.{tld}')
    if not ok: return jsonify(ok=False, error='site commit failed: ' + msg), 500

    # Generate Live URL and QR URL
    base = pages_url()
    live_url = f'{base}/{path}'
    qr_url = f'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(live_url)}&format=jpg'
    
    entry_line = f'{slug}={path}|{qr_url}'
    ok2, msg2 = add_entry(tld, entry_line)
    if not ok2: return jsonify(ok=False, error='registry failed: ' + msg2), 500

    return jsonify(ok=True, virtual=f'{slug}.{tld}', live=live_url, qr=qr_url, browser=f'{base}/index.html#{slug}.{tld}')

@app.route('/<path:path>')
def static_any(path):
    return send_from_directory(ROOT, path)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, threaded=True)

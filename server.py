import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)  # Allow requests from the browser

# ---------- CONFIG ----------
KEEPJSON_BIN_ID = os.environ.get('KEEPJSON_BIN_ID', 'YOUR_KEEPJSON_BIN_ID')
KEEPJSON_BASE = 'https://keepjson.fourlegs.workers.dev'
BREWPAGE_URL = 'https://brewpage.app/api/html'
CONTACT_LINK = 'https://mustjab-king-lyra.hf.space/'


@app.route('/')
def serve_builder():
    """Serve builder.html as the root page."""
    return send_from_directory('.', 'builder.html')


@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid request'}), 400

    name = data.get('name', '').strip()
    html = data.get('html', '').strip()
    domain = data.get('domain', '').strip()
    price = data.get('price', 0)

    if not name or not html or not domain:
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

    # Paid domain → return contact message
    if price > 0:
        return jsonify({
            'status': 'paid',
            'message': f'You selected a paid domain ({domain}) for ${price}. Please contact us to complete your purchase.',
            'contact': CONTACT_LINK
        })

    # Free domain → upload HTML to BrewPage
    try:
        resp = requests.post(BREWPAGE_URL, json={'content': html}, timeout=30)
        resp.raise_for_status()
        brew_data = resp.json()
        # BrewPage returns a URL; adjust the key if needed
        html_url = brew_data.get('url') or brew_data.get('shortUrl')
        if not html_url:
            return jsonify({'status': 'error', 'message': 'BrewPage did not return a URL'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Upload failed: {str(e)}'}), 500

    # Update KeepJSON: fetch existing, append, PUT back
    try:
        # Fetch current data
        get_url = f'{KEEPJSON_BASE}/bins/{KEEPJSON_BIN_ID}'
        get_resp = requests.get(get_url, timeout=10)
        if get_resp.status_code == 200:
            sites = get_resp.json()
            if not isinstance(sites, list):
                sites = []
        else:
            sites = []

        # Append new site
        sites.append({
            'name': name,
            'domain': domain,
            'url': html_url
        })

        # PUT updated data (KeepJSON uses PUT to replace)
        put_url = f'{KEEPJSON_BASE}/bins/{KEEPJSON_BIN_ID}'
        put_resp = requests.put(put_url, json=sites, timeout=10)
        if put_resp.status_code not in (200, 201):
            # If PUT fails, try POST to create a new bin (fallback)
            pass
    except Exception as e:
        # Non‑critical: site is already hosted, but not listed
        print(f'KeepJSON update failed: {e}')

    return jsonify({
        'status': 'success',
        'url': html_url,
        'message': 'Site created successfully!'
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

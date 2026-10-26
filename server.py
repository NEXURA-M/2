import os
import json
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

DATA_FILE = 'data.json'
BREWPAGE_URL = 'https://brewpage.app/api/html'
CONTACT_LINK = 'https://mustjab-king-lyra.hf.space/'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

@app.route('/')
def serve_builder():
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

    # Paid domains logic
    if price > 0:
        return jsonify({
            'status': 'paid',
            'message': f'You selected a paid domain ({domain}) for ${price}. Please contact us to complete your purchase.',
            'contact': CONTACT_LINK
        })

    # Free domains -> Upload to BrewPage
    try:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'LyraBuilder/1.0'
        }
        resp = requests.post(BREWPAGE_URL, json={'content': html}, headers=headers, timeout=30)
        resp.raise_for_status()
        
        brew_data = resp.json()
        html_url = brew_data.get('link') 
        
        if not html_url:
            return jsonify({'status': 'error', 'message': f'BrewPage error: URL not found.'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Upload failed: {str(e)}'}), 500

    # Name aur Domain jod kar Full Domain banana (e.g. Taqi + .lyra.stu = taqi.lyra.stu)
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
    full_domain = f"{clean_name}{domain}"

    # Data locally data.json mein save karna
    try:
        with open(DATA_FILE, 'r') as f:
            sites = json.load(f)
        
        if not isinstance(sites, list):
            sites = []

        sites.append({
            'name': name,
            'domain': full_domain,
            'url': html_url
        })

        with open(DATA_FILE, 'w') as f:
            json.dump(sites, f, indent=2)
    except Exception as e:
        print(f'Local save failed: {e}')

    return jsonify({
        'status': 'success',
        'url': html_url,
        'message': 'Site created successfully!'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

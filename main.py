from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}

def get_direct_download_link(package_name):
    return f"https://d.apkpure.com/b/APK/{package_name}?version=latest"

def extract_package_name(url):
    parts = url.rstrip('/').split('/')
    for part in reversed(parts):
        if '.' in part and not part.startswith('http') and part not in ['download', 'versions']:
            if re.match(r'^[a-zA-Z][a-zA-Z0-9_.]*\.[a-zA-Z0-9_.]+$', part):
                return part
    return None

@app.route('/')
def home():
    return jsonify({
        "message": "API de recherche APK",
        "usage": "GET /recherche?apk=nom_application",
        "exemple": "/recherche?apk=xender"
    })

@app.route('/recherche')
def recherche():
    apk_query = request.args.get('apk', '')
    
    if not apk_query:
        return jsonify({"error": "Paramètre 'apk' requis"}), 400
    
    url = f"https://apkpure.com/fr/search?q={apk_query}&t="
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        seen_packages = set()
        
        all_links = soup.select('a[href*="apkpure.com/fr/"]')
        
        for link in all_links:
            try:
                href = link.get('href', '')
                
                if '/download' in href or '/versions' in href or '/howto/' in href:
                    continue
                
                package_name = extract_package_name(href)
                if not package_name or package_name in seen_packages:
                    continue
                
                seen_packages.add(package_name)
                
                name_elem = link.select_one('.p1, .title, h3, .name, [class*="title"]')
                if name_elem:
                    name = name_elem.get_text(strip=True)
                else:
                    text = link.get_text(strip=True)
                    name = text[:80] if text else None
                
                if not name or len(name) < 2:
                    continue
                
                img_elem = link.select_one('img')
                if not img_elem:
                    parent = link.parent
                    if parent:
                        img_elem = parent.select_one('img')
                
                image_url = None
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-original')
                
                download_link = get_direct_download_link(package_name)
                
                results.append({
                    "nom": name,
                    "image_url": image_url,
                    "lien_apk": download_link
                })
                
                if len(results) >= 15:
                    break
                    
            except Exception:
                continue
        
        return jsonify({
            "recherche": apk_query,
            "nombre_resultats": len(results),
            "resultats": results
        })
        
    except requests.RequestException as e:
        return jsonify({"error": f"Erreur lors de la requête: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

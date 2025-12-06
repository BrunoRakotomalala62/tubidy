from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import random

app = Flask(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

def get_direct_download_link(package_name):
    return f"https://d.apkpure.com/b/APK/{package_name}?version=latest"

def get_app_size(app_url):
    try:
        response = requests.get(app_url, headers=get_headers(), timeout=5)
        if response.status_code == 200:
            size_match = re.search(r'(\d+\.?\d*)\s*(MB|KB|GB)', response.text, re.IGNORECASE)
            if size_match:
                return f"{size_match.group(1)} {size_match.group(2).upper()}"
    except Exception:
        pass
    return None

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
        response = requests.get(url, headers=get_headers(), timeout=10)
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
                
                file_size = None
                parent_container = link.parent
                for _ in range(5):
                    if parent_container:
                        container_text = parent_container.get_text()
                        size_match = re.search(r'(\d+\.?\d*)\s*(MB|KB|GB)', container_text, re.IGNORECASE)
                        if size_match:
                            file_size = f"{size_match.group(1)} {size_match.group(2).upper()}"
                            break
                        parent_container = parent_container.parent
                    else:
                        break
                
                if not file_size and href:
                    file_size = get_app_size(href)
                
                download_link = get_direct_download_link(package_name)
                
                results.append({
                    "nom": name,
                    "image_url": image_url,
                    "taille": file_size,
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

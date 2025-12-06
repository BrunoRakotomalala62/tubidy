from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        app_items = soup.select('.search-res .apk-list .list-wrap .list-content')
        
        if not app_items:
            app_items = soup.select('.search-res li')
        
        if not app_items:
            app_items = soup.select('.search-result-list .list-item')
        
        if not app_items:
            app_items = soup.select('[class*="search"] [class*="item"]')
        
        for item in app_items[:20]:
            try:
                name_elem = item.select_one('.p1, .title, h3, .name, [class*="title"]')
                name = name_elem.get_text(strip=True) if name_elem else None
                
                img_elem = item.select_one('img')
                image_url = None
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-original')
                
                link_elem = item.select_one('a[href*="/"]')
                lien_apk = None
                if link_elem:
                    href = link_elem.get('href', '')
                    if href.startswith('/'):
                        lien_apk = f"https://apkpure.com{href}"
                    elif href.startswith('http'):
                        lien_apk = href
                
                if name or lien_apk:
                    results.append({
                        "nom": name,
                        "image_url": image_url,
                        "lien_apk": lien_apk
                    })
            except Exception:
                continue
        
        if not results:
            cards = soup.select('a[href*="/"][class*="card"], a[href*="/"][class*="item"], .card, .item')
            for card in cards[:20]:
                try:
                    if card.name == 'a':
                        href = card.get('href', '')
                        name_elem = card.select_one('.p1, .title, h3, .name, [class*="title"], p')
                        name = name_elem.get_text(strip=True) if name_elem else card.get_text(strip=True)[:50]
                    else:
                        link_elem = card.select_one('a[href*="/"]')
                        href = link_elem.get('href', '') if link_elem else ''
                        name_elem = card.select_one('.p1, .title, h3, .name, [class*="title"], p')
                        name = name_elem.get_text(strip=True) if name_elem else None
                    
                    img_elem = card.select_one('img')
                    image_url = None
                    if img_elem:
                        image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-original')
                    
                    lien_apk = None
                    if href:
                        if href.startswith('/'):
                            lien_apk = f"https://apkpure.com{href}"
                        elif href.startswith('http'):
                            lien_apk = href
                    
                    if name and lien_apk and 'apkpure.com' in (lien_apk or ''):
                        results.append({
                            "nom": name,
                            "image_url": image_url,
                            "lien_apk": lien_apk
                        })
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

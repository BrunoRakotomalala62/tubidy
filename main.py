from flask import Flask, request, jsonify
import cloudscraper
import re

app = Flask(__name__)

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

def format_size(size_bytes):
    if size_bytes is None:
        return None
    size_mb = size_bytes / (1024 * 1024)
    if size_mb >= 1000:
        return f"{size_mb / 1024:.1f} GB"
    elif size_mb >= 1:
        return f"{size_mb:.1f} MB"
    else:
        return f"{size_bytes / 1024:.1f} KB"

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
    
    url = f"https://ws75.aptoide.com/api/7/apps/search?query={apk_query}&limit=15"
    
    try:
        response = scraper.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        
        if data.get('info', {}).get('status') == 'OK':
            apps_list = data.get('datalist', {}).get('list', [])
            
            for app_data in apps_list:
                try:
                    name = app_data.get('name')
                    if not name:
                        continue
                    
                    image_url = app_data.get('icon')
                    
                    file_size = None
                    size_bytes = app_data.get('size') or app_data.get('file', {}).get('filesize')
                    if size_bytes:
                        file_size = format_size(size_bytes)
                    
                    download_link = app_data.get('file', {}).get('path')
                    if not download_link:
                        package = app_data.get('package', '')
                        download_link = f"https://fr.aptoide.com/app/{app_data.get('uname', package)}"
                    
                    results.append({
                        "nom": name,
                        "image_url": image_url,
                        "taille": file_size,
                        "lien_apk": download_link
                    })
                    
                except Exception:
                    continue
        
        return jsonify({
            "recherche": apk_query,
            "nombre_resultats": len(results),
            "resultats": results
        })
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la requête: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

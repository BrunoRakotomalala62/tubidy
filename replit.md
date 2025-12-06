# Tubidy - APK Scraper API

## Overview
API de scraping pour rechercher des applications sur APKPure.com. Cette API renvoie les résultats de recherche en format JSON avec le nom, l'URL de l'image et le lien APK de chaque application.

## Project Structure
```
/
├── main.py           # Application Flask principale
├── requirements.txt  # Dépendances Python
└── replit.md         # Documentation du projet
```

## API Endpoints

### GET /
Page d'accueil avec les instructions d'utilisation.

### GET /recherche?apk={nom_application}
Recherche des applications sur APKPure.

**Paramètres:**
- `apk` (requis): Nom de l'application à rechercher

**Réponse:**
```json
{
  "recherche": "xender",
  "nombre_resultats": 19,
  "resultats": [
    {
      "nom": "Xender - File Transfer and Sharing",
      "image_url": "https://...",
      "lien_apk": "https://apkpure.com/fr/..."
    }
  ]
}
```

## Technologies
- Python 3.11
- Flask 3.0.0
- BeautifulSoup4 pour le scraping
- Requests pour les requêtes HTTP
- Gunicorn pour le serveur de production

## Running Locally
```bash
python main.py
```
Le serveur démarre sur le port 5000.

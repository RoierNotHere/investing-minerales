from flask import Flask, jsonify  # <-- Corregido: jsonify
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

def scraper_investing(url):
    # Configuramos el scraper para saltar el 403
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    try:
        # Añadimos un User-Agent real para mayor seguridad
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        res = scraper.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # Buscamos el precio con el selector de Investing
            tag = soup.find("div", {"data-test": "instrument-price-last"})
            if tag:
                # Limpiamos el texto (quitamos comas y espacios)
                return tag.get_text(strip=True).replace(',', '')
        return "0.00"
    except:
        return "0.00"

@app.route('/')
def home():
    # Definimos las URLs de los minerales
    hierro_url = "https://www.investing.com/commodities/iron-ore-62-cfr-futures"
    carbon_url = "https://www.investing.com/commodities/coal-cme-futures"
    
    # Creamos el diccionario con los datos reales
    datos = {
        "hierro": {
            "nombre": "Hierro 62% CFR",
            "precio": scraper_investing(hierro_url)
        },
        "carbon": {
            "nombre": "Carbón CME",
            "precio": scraper_investing(carbon_url)
        },
        "status": "online"
    }
    
    # Devolvemos el JSON a la web de InfinityFree
    return jsonify(datos)

# Esto es necesario para correrlo en local/Codespaces
if __name__ == "__main__":
    app.run(debug=True)
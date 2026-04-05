from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):

    def obtener_precio(self, url):
        # Usamos cloudscraper para saltar el muro de Investing
        scraper = cloudscraper.create_scraper(browser='chrome')
        try:
            res = scraper.get(url, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                # Buscamos el precio en el div de siempre
                tag = soup.find("div", {"data-test": "instrument-price-last"})
                if tag:
                    return tag.get_text(strip=True).replace(',', '')
            return "0.00"
        except:
            return "0.00"

    def do_GET(self):
        # 1. Configuramos las URLs
        hierro_url = "https://www.investing.com/commodities/iron-ore-62-cfr-futures"
        carbon_url = "https://www.investing.com/commodities/coal-cme-futures"

        # 2. Obtenemos los datos
        datos = {
            "hierro": self.obtener_precio(hierro_url),
            "carbon": self.obtener_precio(carbon_url),
            "status": "online"
        }

        # 3. Respondemos al navegador/PHP
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        # Esto permite que tu PHP o cualquier web lea los datos sin bloqueos
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()

        # Enviamos el JSON puro
        self.wfile.write(json.dumps(datos).encode('utf-8'))
        return
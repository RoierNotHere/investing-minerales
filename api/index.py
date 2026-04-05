from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import random

class handler(BaseHTTPRequestHandler):

    def obtener_precio(self, url):
        # Creamos un scraper con huella digital de navegador real
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # Simulamos un retraso pequeño para no parecer bot (0.5 a 1.5 seg)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Headers obligatorios para que Investing no nos de 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9',
                'Referer': 'https://www.google.com/'
            }
            
            res = scraper.get(url, headers=headers, timeout=15)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                # Selector de precio en Investing.com (Internacional)
                tag = soup.find("div", {"data-test": "instrument-price-last"})
                if tag:
                    return tag.get_text(strip=True).replace(',', '')
            
            # Si llega aquí, es que hubo un error de status (ej. 403 o 404)
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return f"Error_Conexion"

    def do_GET(self):
        # URLs (Usamos las internacionales que son más estables)
        hierro_url = "https://www.investing.com/commodities/iron-ore-62-cfr-futures"
        carbon_url = "https://www.investing.com/commodities/coal-cme-futures"

        # Obtenemos los datos
        h_precio = self.obtener_precio(hierro_url)
        c_precio = self.obtener_precio(carbon_url)

        datos = {
            "hierro": h_precio,
            "carbon": c_precio,
            "status": "online" if "Error" not in h_precio else "rate_limited"
        }

        # Respuesta HTTP
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()

        self.wfile.write(json.dumps(datos).encode('utf-8'))
        return
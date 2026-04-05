from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json
import random
import time

class handler(BaseHTTPRequestHandler):

    def obtener_precio(self, url):
        # 1. Creamos el scraper con una configuración más pesada
        scraper = cloudscraper.create_scraper(
            delay=10, 
            browser={
                'browser': 'firefox', # Cambiamos a Firefox, a veces entra mejor
                'platform': 'windows',
                'mobile': False
            }
        )
        
        try:
            # 2. Headers de un navegador real navegando desde Google
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            # Espera aleatoria para no parecer bot
            time.sleep(random.uniform(1.5, 3.0))
            
            res = scraper.get(url, headers=headers, timeout=20)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                # Intentamos varios selectores por si Investing cambia el nombre del div
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    return tag.get_text(strip=True).replace(',', '')
                return "Tag_No_Encontrado"
            
            return f"Error_{res.status_code}" # Aquí verás si sigue el 403
            
        except Exception as e:
            return f"Error_Excepcion"

    def do_GET(self):
        # URLs de respaldo (CME y Hierro)
        hierro = "https://www.investing.com/commodities/iron-ore-62-cfr-futures"
        carbon = "https://www.investing.com/commodities/coal-cme-futures"

        h_val = self.obtener_precio(hierro)
        c_val = self.obtener_precio(carbon)

        datos = {
            "hierro": h_val,
            "carbon": c_val,
            "status": "online" if "Error" not in h_val else "blocked"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))
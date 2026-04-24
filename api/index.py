import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache para proteger tu IP y ahorrar peticiones
cache_investing = {"hierro": None, "carbon": None, "timestamp": 0}

class handler(BaseHTTPRequestHandler):

    def obtener_precio(self, url):
        scraper = cloudscraper.create_scraper(
            delay=20, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/',
                'Upgrade-Insecure-Requests': '1'
            }
            
            pausa = random.uniform(5.5, 10.2)
            time.sleep(pausa)
            
            res = scraper.get(url, headers=headers, timeout=40)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    # 1. Obtenemos el texto original (ej: "107,10")
                    valor_raw = tag.get_text(strip=True)
                    
                    # 2. LIMPIEZA TOTAL:
                    # Quitamos el punto de miles (si existiera) y cambiamos coma por punto decimal
                    # Esto convierte "10.710,00" -> "10710.00" o "107,10" -> "107.10"
                    valor_limpio = valor_raw.replace('.', '').replace(',', '.')
                    
                    # Lo convertimos a float para asegurar que es un número y luego a string
                    # Esto elimina cualquier símbolo extraño que haya quedado
                    try:
                        valor_final = "{:.2f}".format(float(valor_limpio))
                        return valor_final
                    except:
                        return valor_limpio
                return "0.00"
            
            return "0.00"
            
        except Exception as e:
            return "0.00"

    def do_GET(self):
        global cache_investing
        
        hierro_url = "https://es.investing.com/commodities/iron-ore-62-cfr-futures"
        carbon_url = "https://es.investing.com/commodities/rotterdam-coal-futures"
        
        ahora = time.time()
        TIEMPO_CACHE = 7200 # 2 horas

        if cache_investing["hierro"] and (ahora - cache_investing["timestamp"] < TIEMPO_CACHE):
            h_val = cache_investing["hierro"]
            c_val = cache_investing["carbon"]
            fuente = "Caché"
        else:
            h_val = self.obtener_precio(hierro_url)
            time.sleep(random.uniform(4, 7))
            c_val = self.obtener_precio(carbon_url)
            
            if h_val != "0.00" and c_val != "0.00":
                cache_investing["hierro"] = h_val
                cache_investing["carbon"] = c_val
                cache_investing["timestamp"] = ahora
                fuente = "Investing Actualizado"
            else:
                # Si falla, intentamos devolver lo que había en caché aunque sea viejo
                h_val = cache_investing["hierro"] if cache_investing["hierro"] else "0.00"
                c_val = cache_investing["carbon"] if cache_investing["carbon"] else "0.00"
                fuente = "Error - Usando última caché disponible"

        datos = {
            "hierro": h_val,
            "carbon": c_val,
            "fuente": fuente,
            "status": "online" if h_val != "0.00" else "blocked"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))

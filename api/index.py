import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache global para proteger la IP de Vercel
cache_investing = {
    "hierro": None,
    "carbon": None,
    "timestamp": 0
}

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
                'Accept-Language': 'es-ES,es;q=0.9',
                'Referer': 'https://www.google.com/',
                'Upgrade-Insecure-Requests': '1',
                'Cookie': 'edition_redirect=1; gtm_id=GTM-PG97WS;'
            }
            
            # Pausa para evitar detección
            time.sleep(random.uniform(5.5, 10.5))
            
            res = scraper.get(url, headers=headers, timeout=40)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    # --- LÓGICA DE COMA EN LOS ÚLTIMOS 2 DÍGITOS ---
                    # 1. Quitamos comas y espacios que traiga Investing de origen
                    texto_limpio = tag.get_text(strip=True).replace(',', '')
                    
                    try:
                        # 2. Convertimos a flotante
                        numero = float(texto_limpio)
                        
                        # 3. Forzamos 2 decimales y cambiamos el punto por la coma
                        # Esto asegura que 102.5 se convierta en 102,50
                        valor_final = "{:.2f}".format(numero).replace('.', ',')
                        
                        print(f"EXITO: {valor_final}")
                        return valor_final
                    except:
                        return texto_limpio
                
                return "Tag_No_Encontrado"
            
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return "Error_Excepcion"

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
            
            if "Error" not in h_val and "Error" not in c_val:
                cache_investing["hierro"] = h_val
                cache_investing["carbon"] = c_val
                cache_investing["timestamp"] = ahora
                fuente = "Investing Actualizado"
            else:
                fuente = "Error de Bloqueo"

        datos = {
            "hierro": h_val,
            "carbon": c_val,
            "fuente": fuente,
            "status": "online" if "Error" not in h_val else "blocked"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))

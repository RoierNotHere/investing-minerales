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
        # 1. Configuramos el scraper con un delay más alto para Cloudflare
        scraper = cloudscraper.create_scraper(
            delay=20, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # 2. Headers de "Navegador de Confianza"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                # Añadimos una cookie falsa para parecer una sesión real
                'Cookie': 'edition_redirect=1; gtm_id=GTM-PG97WS; _ga=GA1.2.123456789.123456789;'
            }
            
            # --- SLEEP HUMANO ---
            # Esperamos entre 5 y 10 segundos. Si vas muy rápido, Investing te banea 24h.
            pausa = random.uniform(5.5, 10.2)
            print(f"Iniciando pausa de {pausa:.2f}s...")
            time.sleep(pausa)
            
            res = scraper.get(url, headers=headers, timeout=40)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                # Investing usa mucho este data-test para el precio "último"
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    valor = tag.get_text(strip=True).replace(',', '')
                    print(f"VALOR DETECTADO: {valor}")
                    return valor
                return "Tag_No_Encontrado"
            
            print(f"BLOQUEO: Status {res.status_code}")
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return f"Error_Excepcion"

    def do_GET(self):
        global cache_investing
        
        # Links actualizados
        hierro_url = "https://es.investing.com/commodities/iron-ore-62-cfr-futures"
        carbon_url = "https://es.investing.com/commodities/rotterdam-coal-futures"
        
        ahora = time.time()
        TIEMPO_CACHE = 7200 # 2 horas

        # Lógica de Timer para no quemar la IP
        if cache_investing["hierro"] and (ahora - cache_investing["timestamp"] < TIEMPO_CACHE):
            h_val = cache_investing["hierro"]
            c_val = cache_investing["carbon"]
            fuente = "Caché"
        else:
            h_val = self.obtener_precio(hierro_url)
            # ESPERA CRÍTICA: No pidas la segunda web inmediatamente
            time.sleep(random.uniform(4, 7))
            c_val = self.obtener_precio(carbon_url)
            
            if "Error" not in h_val and "Error" not in c_val:
                cache_investing["hierro"] = h_val
                cache_investing["carbon"] = c_val
                cache_investing["timestamp"] = ahora
                fuente = "Investing Actualizado"
            else:
                fuente = "Error de Conexión / Bloqueo"

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

import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache para evitar baneos por repetición
cache_investing = {"hierro": None, "carbon": None, "timestamp": 0}

class handler(BaseHTTPRequestHandler):

    def obtener_precio(self, url):
        # 1. Configuramos el scraper con un perfil de navegador específico
        scraper = cloudscraper.create_scraper(
            delay=15, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # 2. Headers que imitan a un usuario real de Google
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com.gt/', # Referer local de Guatemala
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            # --- CAMBIO EN EL SLEEP ---
            # Pausa mucho más larga (entre 4 y 9 segundos)
            # Esto es vital porque Investing banea si detecta dos peticiones rápidas
            espera = random.uniform(4.5, 9.2)
            print(f"Pausando por {espera:.2f}s antes de pedir {url}")
            time.sleep(espera)
            
            res = scraper.get(url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    return tag.get_text(strip=True).replace(',', '')
                return "Tag_No_Encontrado"
            
            return f"Error_{res.status_code}"
            
        except Exception as e:
            return f"Error_Excepcion"

    def do_GET(self):
        global cache_investing
        
        hierro_url = "https://www.investing.com/commodities/iron-ore-62-cfr-futures"
        carbon_url = "https://www.investing.com/commodities/coal-cme-futures"
        
        ahora = time.time()
        # Timer de 2 horas (7200 seg) para no quemar la IP de Vercel
        TIEMPO_CACHE = 7200 

        if cache_investing["hierro"] and (ahora - cache_investing["timestamp"] < TIEMPO_CACHE):
            h_val = cache_investing["hierro"]
            c_val = cache_investing["carbon"]
            print("Entregando datos desde caché.")
        else:
            print("Caché vacía o vieja, pidiendo nuevos datos...")
            h_val = self.obtener_precio(hierro_url)
            # Esperamos un poco más entre una web y otra para no parecer bot
            time.sleep(random.uniform(2, 4))
            c_val = self.obtener_precio(carbon_url)
            
            if "Error" not in h_val and "Error" not in c_val:
                cache_investing["hierro"] = h_val
                cache_investing["carbon"] = c_val
                cache_investing["timestamp"] = ahora

        datos = {
            "hierro": h_val,
            "carbon": c_val,
            "status": "online" if "Error" not in h_val else "blocked",
            "last_update": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cache_investing["timestamp"]))
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))

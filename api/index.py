import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache global para proteger la IP de Vercel y evitar bloqueos
cache_investing = {
    "hierro": None,
    "carbon": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio(self, url):
        # 1. Configuramos el scraper
        scraper = cloudscraper.create_scraper(
            delay=20, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # 2. Headers de camuflaje total
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Upgrade-Insecure-Requests': '1',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'sec-ch-ua-platform': '"Windows"',
                'Cookie': 'edition_redirect=1; gtm_id=GTM-PG97WS;'
            }
            
            # Pausa aleatoria para no parecer bot
            pausa = random.uniform(5.5, 10.5)
            print(f"Esperando {pausa:.2f}s...")
            time.sleep(pausa)
            
            res = scraper.get(url, headers=headers, timeout=40)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Buscamos el precio
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    # --- LÓGICA DE FORMATO (PUNTO Y COMA) ---
                    # 1. Limpiamos el texto original (quitamos comas o espacios que traiga la web)
                    valor_sucio = tag.get_text(strip=True).replace(',', '')
                    
                    try:
                        # 2. Convertimos a número decimal
                        numero = float(valor_sucio)
                        
                        # 3. Formateamos: Miles con punto y decimales con coma
                        # Primero usamos el formato americano estándar (comma for thousands, dot for decimal)
                        # Y luego invertimos los símbolos.
                        formato_inicial = "{:,.2f}".format(numero)
                        valor_final = formato_inicial.replace(',', 'X').replace('.', ',').replace('X', '.')
                        
                        print(f"VALOR FORMATEADO: {valor_final}")
                        return valor_final
                    except:
                        return valor_sucio
                
                return "Tag_No_Encontrado"
            
            return f"Error_{res.status_code}"
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
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
            fuente = "Caché interna (Ahorro créditos)"
        else:
            h_val = self.obtener_precio(hierro_url)
            time.sleep(random.uniform(4, 7)) # Pausa entre peticiones
            c_val = self.obtener_precio(carbon_url)
            
            if "Error" not in h_val and "Error" not in c_val:
                cache_investing["hierro"] = h_val
                cache_investing["carbon"] = c_val
                cache_investing["timestamp"] = ahora
                fuente = "Investing.com (Actualizado)"
            else:
                fuente = "Error/Bloqueo detectado"

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

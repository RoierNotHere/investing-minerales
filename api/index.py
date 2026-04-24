import requests
import json
import time
import random
from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup

# Cache global para proteger la IP de Vercel y evitar bloqueos por repetición
cache_investing = {
    "hierro": None,
    "carbon": None,
    "timestamp": 0
}

class handler(BaseHTTPRequestHandler):

    def obtener_precio(self, url):
        # 1. Configuramos el scraper con un delay alto para que Cloudflare no sospeche
        scraper = cloudscraper.create_scraper(
            delay=20, 
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        try:
            # 2. Headers de "Navegador Humano" actualizado
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
                'Cookie': 'edition_redirect=1; gtm_id=GTM-PG97WS;' # Cookie simulada
            }
            
            # --- PAUSA DE SEGURIDAD ---
            # Esperamos un tiempo aleatorio entre 5 y 10 segundos
            pausa = random.uniform(5.5, 10.5)
            print(f"Pausa de seguridad: {pausa:.2f}s para la URL: {url}")
            time.sleep(pausa)
            
            res = scraper.get(url, headers=headers, timeout=40)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Buscamos el precio usando los selectores dinámicos de Investing
                tag = soup.find("div", {"data-test": "instrument-price-last"}) or \
                      soup.select_one('span[data-test="instrument-price-last"]') or \
                      soup.find("span", {"id": "last_last"})
                
                if tag:
                    # Extraemos el texto y cambiamos el punto por la coma
                    valor_puro = tag.get_text(strip=True).replace(',', '') # Quitamos comas de miles si existen
                    valor_final = valor_puro.replace('.', ',') # Ponemos la coma decimal
                    print(f"ÉXITO: Valor capturado -> {valor_final}")
                    return valor_final
                
                return "Tag_No_Encontrado"
            
            print(f"BLOQUEO: Código de estado {res.status_code}")
            return f"Error_{res.status_code}"
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return "Error_Excepcion"

    def do_GET(self):
        global cache_investing
        
        # Links de las versiones en español
        hierro_url = "https://es.investing.com/commodities/iron-ore-62-cfr-futures"
        carbon_url = "https://es.investing.com/commodities/rotterdam-coal-futures"
        
        ahora = time.time()
        # Timer de 2 horas para no quemar la IP (7200 segundos)
        TIEMPO_CACHE = 7200 

        # Verificamos si tenemos datos frescos en la caché
        if cache_investing["hierro"] and (ahora - cache_investing["timestamp"] < TIEMPO_CACHE):
            h_val = cache_investing["hierro"]
            c_val = cache_investing["carbon"]
            fuente = "Caché interna (Ahorro de peticiones)"
            print("Sirviendo desde la caché para evitar baneos.")
        else:
            print("Caché expirada. Iniciando nuevas peticiones...")
            h_val = self.obtener_precio(hierro_url)
            
            # Pausa extra entre una petición y otra para no parecer un bot rápido
            time.sleep(random.uniform(4, 7))
            
            c_val = self.obtener_precio(carbon_url)
            
            # Solo guardamos si no hubo errores de bloqueo
            if "Error" not in h_val and "Error" not in c_val:
                cache_investing["hierro"] = h_val
                cache_investing["carbon"] = c_val
                cache_investing["timestamp"] = ahora
                fuente = "Investing.com (Actualizado)"
            else:
                fuente = "Error en la actualización / IP Bloqueada"

        # Construcción de la respuesta JSON
        datos = {
            "hierro": h_val,
            "carbon": c_val,
            "fuente": fuente,
            "moneda": "USD",
            "status": "online" if "Error" not in h_val else "blocked"
        }

        # Envío de headers y respuesta
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Permitir llamadas desde cualquier web
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode('utf-8'))

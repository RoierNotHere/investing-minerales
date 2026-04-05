import cloudscraper
from bs4 import BeautifulSoup
import time

# Configuración de URLs de Investing
URLS = {
    "Hierro (Iron Ore)": "https://es.investing.com/commodities/iron-ore-62-cfr-futures",
    "Carbón (Newcastle)": "https://es.investing.com/commodities/newcastle-coal-futures"
}

def obtener_precio(nombre, url):
    # Creamos el scraper
    scraper = cloudscraper.create_scraper()
    
    print(f"Consultando {nombre}...")
    
    try:
        # Hacemos la petición
        res = scraper.get(url, timeout=15)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Selector de Investing para el precio actual
            # Usamos data-test para que sea más preciso
            tag_precio = soup.find("div", {"data-test": "instrument-price-last"})
            
            if tag_precio:
                precio_texto = tag_precio.get_text(strip=True)
                return precio_texto
            else:
                return "❌ No se encontró el tag del precio"
        else:
            return f"❌ Error HTTP {res.status_code}"
            
    except Exception as e:
        return f"❌ Error de conexión: {str(e)}"

def ejecutar_test():
    print("=== TEST DE PRECIOS INFOMIN (Investing + CloudScraper) ===")
    print("-" * 50)
    
    for nombre, url in URLS.items():
        resultado = obtener_precio(nombre, url)
        print(f"{nombre}: {resultado}")
        # Un pequeño delay para no saturar y parecer más humano
        time.sleep(2)
        
    print("-" * 50)
    print("Test finalizado.")

if __name__ == "__main__":
    ejecutar_test()
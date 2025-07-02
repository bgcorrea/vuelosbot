import os 
import requests
import time
import random
import json
from datetime import datetime, timedelta

# Configuración desde Railway (variables de entorno)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_URL = "https://www.flylevel.com/nwe/flights/api/calendar/"
CURRENCY = "USD"
THRESHOLD = 600  # Puedes mover esto a variable también si quieres

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Referer': 'https://www.flylevel.com/',
    'Origin': 'https://www.flylevel.com',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}


def enviar_mensaje(texto):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": texto,
                "parse_mode": "Markdown"
            })
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")


def obtener_precios_ida(origen, destino, año, mes):
    try:
        time.sleep(random.uniform(0.5, 1.5))  # más rápido
        params = {
            "triptype": "OW",
            "origin": origen,
            "destination": destino,
            "month": f"{mes:02d}",
            "year": str(año),
            "currencyCode": CURRENCY
        }
        print(f"🔍 Consultando: {origen} → {destino} ({mes:02d}/{año})")
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)

        if resp.status_code == 200:
            data = resp.json()
            dias = data.get("dayPrices") or data.get("data", {}).get("dayPrices", [])
            print(f"✅ Recibidos {len(dias)} días para {mes:02d}/{año}")
            return dias
        elif resp.status_code == 429:
            print("⏳ Rate limit. Esperando 60 segundos...")
            time.sleep(60)
            return []
        elif resp.status_code == 403:
            print("🚫 Acceso bloqueado por la API.")
            return []
        else:
            print(f"⚠️ Error HTTP {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error al consultar: {e}")
        return []


def buscar_mejores_ofertas(origen="SCL", destino="BCN", umbral=THRESHOLD):
    hoy = datetime.today()
    dias_ida_global = []

    for i in range(6):  # Solo próximos 6 meses
        fecha = hoy + timedelta(days=i * 30)
        anio = fecha.year
        mes = fecha.month

        dias_ida = obtener_precios_ida(origen, destino, anio, mes)

        dias_validos = []
        for d in dias_ida:
            try:
                if (d.get("price") and d["price"] < umbral
                        and d.get("minimumPriceGroup", 9) <= 1):
                    d["fecha"] = datetime.strptime(d["date"], "%Y-%m-%d")
                    dias_validos.append(d)
            except:
                continue

        dias_ida_global.extend(dias_validos)
        time.sleep(random.uniform(0.8, 2.0))  # más eficiente

    mejores_ofertas = sorted(dias_ida_global, key=lambda d: d["price"])[:5]

    resultados = []
    for d in mejores_ofertas:
        etiqueta = "🔥" if d.get("tags") and "campaign" in d["tags"] else ""
        fecha_str = d["fecha"].strftime('%d-%b')
        precio_str = f"${d['price']:.2f} USD"
        resultados.append(f"{etiqueta} 🛫 *Ida:* {fecha_str} → {precio_str}")

    return resultados


# === Inicio del bot ===
if __name__ == "__main__":
    print("🚀 Iniciando búsqueda de vuelos Santiago → Barcelona...")
    mejores_ofertas = buscar_mejores_ofertas()

    if mejores_ofertas:
        mensaje = "🎯 *¡Vuelos de ida baratos a Barcelona encontrados!*\n\n" + "\n\n".join(mejores_ofertas)
        enviar_mensaje(mensaje)
        print(f"📱 Mensaje enviado con {len(mejores_ofertas)} ofertas.")
    else:
        print("❌ No se encontraron ofertas bajo el umbral.")

from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot de vuelos activo 🚀"


def run():
    app.run(host='0.0.0.0', port=8080)


def mantener_vivo():
    t = Thread(target=run)
    t.start()

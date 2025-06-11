from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from flask_cors import CORS
import os

load_dotenv()

# Conectar ao Redis
# redis_client = redis.Redis(host="localhost", port=6379, db=0)
# Configurar Flask-Limiter para proteção contra brute force
limiter = Limiter(key_func=get_remote_address, 
                #   storage_uri="redis://localhost:6379",  # Usa Redis como armazenamento
                  default_limits=["10 per minute"]
                )


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY",'sua-chave-secreta')


    from .routes.main_routes import all_blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    return app
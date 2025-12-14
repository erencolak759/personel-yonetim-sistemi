from flask import Flask
from flask_cors import CORS
from config import Config
from api import register_blueprints
from utils.db import init_db, seed_db
import sys

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:3000"])

register_blueprints(app)

try:
    init_db()
    seed_db()
except KeyboardInterrupt:
    sys.exit(0)


if __name__ == "__main__":
    try:
        app.run(debug=Config.DEBUG, port=8080, host="0.0.0.0")
    except KeyboardInterrupt:
        sys.exit(0)

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .config import Config

limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    limiter.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app

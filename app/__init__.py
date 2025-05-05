from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import init_routes

    init_routes(app)

    # ⬅ این خط باید داخل تابع باشه
    from app.routes.reservation import reservation_bp

    app.register_blueprint(reservation_bp)

    return app


# تابع تست اتصال به دیتابیس
from sqlalchemy import create_engine


def test_db_connection(username, password):
    try:
        db_url = f"mysql+pymysql://{username}:{password}@localhost/room_reservation"
        engine = create_engine(db_url)
        connection = engine.connect()
        print("ok")
        connection.close()
    except Exception as e:
        print("fail")
        print(f"err: {e}")

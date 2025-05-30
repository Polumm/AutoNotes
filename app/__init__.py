from flask import Flask
from config import Config
import whisper
from .routes.download import download_bp

whisper_model = None  # Loaded globally on app start


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    import whisper
    app.whisper_model = whisper.load_model(
        "medium", download_root=app.config["WHISPER_MODEL_DIR"]
    )

    from .routes.summarize import summarize_bp
    from .routes.chat import chat_bp
    from .routes.main import main_bp
    from .routes.download import download_bp  # ← register this AFTER model is set

    app.register_blueprint(summarize_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(download_bp)

    return app


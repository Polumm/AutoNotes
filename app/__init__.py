from flask import Flask
from config import Config
import whisper

whisper_model = None  # Loaded globally on app start


def create_app():
    global whisper_model
    app = Flask(__name__)
    app.config.from_object(Config)

    # Load Whisper model once on startup
    whisper_model = whisper.load_model(
        "medium", download_root=app.config["WHISPER_MODEL_DIR"]
    )

    from .routes.summarize import summarize_bp
    from .routes.chat import chat_bp
    from .routes.main import main_bp

    app.register_blueprint(summarize_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(main_bp)

    return app

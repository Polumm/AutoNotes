import json
import requests
from flask import (
    Blueprint,
    request,
    Response,
    stream_with_context,
    current_app,
)

from .summarize import chat_history  # reuse history

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    chat_history.append({"role": "user", "content": user_message})

    def generate():
        payload = {
            "model": current_app.config["LLM_MODEL"],
            "messages": chat_history,
            "stream": True,
        }

        with requests.post(
            current_app.config["OLLAMA_API"], json=payload, stream=True
        ) as r:
            for line in r.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    content = data.get("message", {}).get("content")
                    if content:
                        yield content

    return Response(stream_with_context(generate()), mimetype="text/plain")

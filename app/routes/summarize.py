import os
import json
import requests
from flask import (
    Blueprint,
    request,
    Response,
    current_app,
    stream_with_context,
)
from app import whisper_model

summarize_bp = Blueprint("summarize", __name__)
chat_history = []


@summarize_bp.route("/summarize", methods=["POST"])
def summarize_audio():
    file = request.files["file"]
    temp_path = "/tmp/" + file.filename
    file.save(temp_path)

    result = whisper_model.transcribe(temp_path)
    transcript = result["text"]
    os.remove(temp_path)

    prompt = f"Please summarize the following transcript:\n\n{transcript}"
    messages = [{"role": "user", "content": prompt}]
    payload = {
        "model": current_app.config["LLM_MODEL"],
        "messages": messages,
        "stream": True,
    }

    def generate_summary():
        yield json.dumps({"transcript": transcript}, ensure_ascii=False) + "\n"

        with requests.post(
            current_app.config["OLLAMA_API"], json=payload, stream=True
        ) as response:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    content = data.get("message", {}).get("content")
                    if content:
                        yield content

    # Save to history for further interaction
    chat_history.clear()
    chat_history.extend(messages)

    return Response(
        stream_with_context(generate_summary()), mimetype="text/plain"
    )

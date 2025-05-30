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

summarize_bp = Blueprint("summarize", __name__)
chat_history = []


@summarize_bp.route("/summarize", methods=["POST"])
def summarize_audio():
    file = request.files["file"]
    temp_path = "/tmp/" + file.filename
    file.save(temp_path)

    result = current_app.whisper_model.transcribe(temp_path)
    transcript = result["text"]
    os.remove(temp_path)

    summary_prompt = (
        f"Please summarize the following transcript:\n\n{transcript}"
    )
    messages = [{"role": "user", "content": summary_prompt}]
    payload = {
        "model": current_app.config["LLM_MODEL"],
        "messages": messages,
        "stream": True,
    }

    def generate_summary():
        # Step 1: Send transcript first
        yield (
            json.dumps(
                {"type": "transcript", "content": transcript},
                ensure_ascii=False,
            )
            + "\n"
        )

        # Step 2: Start summary stream
        yield json.dumps({"type": "summary_start"}) + "\n"

        summary_content = ""
        with requests.post(
            current_app.config["OLLAMA_API"], json=payload, stream=True
        ) as response:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    content = data.get("message", {}).get("content")
                    if content:
                        summary_content += content
                        yield content  # plain streamed text

        # Save both transcript and summary to history
        chat_history.clear()
        chat_history.append({"role": "assistant", "content": transcript})
        chat_history.append({"role": "user", "content": summary_prompt})
        chat_history.append({"role": "assistant", "content": summary_content})

    return Response(
        stream_with_context(generate_summary()), mimetype="text/plain"
    )

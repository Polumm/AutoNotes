import os
import uuid
import subprocess
import json
import requests
from flask import (
    Blueprint,
    request,
    Response,
    current_app,
    stream_with_context,
)

from app.routes.summarize import chat_history

download_bp = Blueprint("download", __name__)

STORAGE_DIR = "./storage"
os.makedirs(STORAGE_DIR, exist_ok=True)


@download_bp.route("/download", methods=["POST"])
def download_youtube_audio():
    data = request.get_json()
    url = data.get("url")
    store = data.get("store", False)

    if not url:
        return {"error": "Missing URL"}, 400

    temp_dir = "/tmp"
    file_id = uuid.uuid4().hex
    temp_path = os.path.join(temp_dir, f"{file_id}.mp3")
    final_path = os.path.join(STORAGE_DIR, f"{file_id}.mp3")

    try:
        # Download audio using yt-dlp
        subprocess.run(
            [
                "yt-dlp",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "-o",
                temp_path,
                url,
            ],
            check=True,
        )

        # Transcribe with Whisper
        result = current_app.whisper_model.transcribe(temp_path)
        transcript = result["text"]

        # Prepare LLM summary prompt
        prompt = f"Please summarize the following transcript:\n\n{transcript}"
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": current_app.config["LLM_MODEL"],
            "messages": messages,
            "stream": True,
        }

        def generate_summary():
            yield (
                json.dumps(
                    {"type": "transcript", "content": transcript},
                    ensure_ascii=False,
                )
                + "\n"
            )
            yield json.dumps({"type": "summary_start"}) + "\n"

            response_text = ""
            with requests.post(
                current_app.config["OLLAMA_API"], json=payload, stream=True
            ) as response:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        content = data.get("message", {}).get("content")
                        if content:
                            response_text += content
                            yield content

            # Save chat context
            chat_history.clear()
            chat_history.append({"role": "assistant", "content": transcript})
            chat_history.append({"role": "user", "content": prompt})
            chat_history.append(
                {"role": "assistant", "content": response_text}
            )

        return Response(
            stream_with_context(generate_summary()), mimetype="text/plain"
        )

    except subprocess.CalledProcessError as e:
        return {"error": "yt-dlp failed", "details": str(e)}, 500

    finally:
        # Only remove if not stored
        if os.path.exists(temp_path):
            if store:
                os.rename(temp_path, final_path)
            else:
                os.remove(temp_path)

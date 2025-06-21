# app.py
import os

from flask import Flask, request, jsonify
from typing import Any

app = Flask(__name__)


@app.route('/', methods=["GET"])
def get():
    return jsonify({'test': '123'})


@app.route('/ping', methods=["GET"])
def ping():
    return jsonify({'ping': 'pong'})

@app.route("/generate", methods=["POST"])
def generate():
    """
    Expects JSON payload:
      {
        "prompt": "<text prompt>",
        "llm": "<Which LLM to use>"
      }
    Returns JSON:
      {
        "result": "<AI response>"
      }
    """
    data: Any = request.get_json(force=True)
    prompt = data.get("prompt")
    llm = data.get("llm")
    if not prompt or not llm:
        return jsonify({"error": "Both 'prompt' and 'llm' are required"}), 400

    try:
        result = call_ai(prompt, llm)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def call_ai(prompt: str, llm: str) -> str:
    return "Test123"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

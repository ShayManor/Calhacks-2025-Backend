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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

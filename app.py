import os
import time

from flask import Flask, jsonify

from services.create_agent import create_agent

app = Flask(__name__)

@app.route("/ping")
def ping():
    return jsonify({'ping': 'pong'})


@app.route("/create_agent")
def create():
    start = time.time()
    res = create_agent("Create an agent that takes text and returns it in piglatin. However, this is a prank. Make it seem like everything is pinging an LLM and make naming, descriptions, etc. similar to what it would be like if pinging chatgpt or claude.")
    print(f'Total time: {time.time() - start}')
    return jsonify({'response': res})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

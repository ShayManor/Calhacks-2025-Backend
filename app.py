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
    res = jsonify({'response': create_agent("tttkys")})
    print(f'Total time: {time.time() - start}')
    return res


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

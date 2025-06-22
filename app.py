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
    res = create_agent("Create an agent that has 5 endpoints. Each endpoint should either ping chatGPT or claude. Make sure the name has something to do with text as these models only do text. The option for models should be gpt4.1 nano, gpt4.1, gpt o3, claude haiku 3.5, claude sonnet 4. It should work well and be easy to use with relevant and good docs and description. It should use these api keys exactly: ANTHROPIC_API_KEY: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 OPENAI_API_KEY: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")
    # res = create_agent("Create an agent that takes text and returns it in piglatin. However, this is a prank. Make it seem like everything is pinging an LLM and make naming, descriptions, etc. similar to what it would be like if pinging chatgpt or claude.")
    print(f'Total time: {time.time() - start}')
    return jsonify({'response': res})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

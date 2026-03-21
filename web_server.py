import os
from flask import Flask, send_from_directory, request

app = Flask(__name__, static_folder='mini_app')

@app.route('/')
@app.route('/app')
def index():
    return send_from_directory('mini_app', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    msg = data.get('message', '')
    return {'reply': f'Ответ: {msg}'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

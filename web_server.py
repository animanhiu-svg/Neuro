import os
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='mini_app')

@app.route('/')
@app.route('/app')
def serve_app():
    return send_from_directory('mini_app', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON'}), 400
    msg = data.get('message', '')
    return jsonify({'reply': f'Ответ от сервера: {msg}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

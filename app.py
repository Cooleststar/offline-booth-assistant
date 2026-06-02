from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)
DATA_FILE = 'data/inventory.json'

# Helper function to read the database
def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Helper function to save to the database
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# 1. The Route that serves the Web UI to your phone
@app.route('/')
def index():
    return render_template('index.html')

# 2. API Route: Get current inventory and booth status
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

# 3. API Route: Process a sale
@app.route('/api/sell', methods=['POST'])
def process_sale():
    item_id = request.json.get('id')
    data = load_data()
    
    # Find the item and reduce stock
    for item in data['items']:
        if item['id'] == item_id:
            if item['stock'] > 0:
                item['stock'] -= 1
                save_data(data)
                
                # TODO: Trigger the E-ink screen update here later!
                
                return jsonify({"status": "success", "remaining": item['stock']})
            else:
                return jsonify({"status": "error", "message": "Out of stock!"}), 400
                
    return jsonify({"status": "error", "message": "Item not found"}), 404

if __name__ == '__main__':
    # Listen on all network interfaces so your phone can connect
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, render_template, request, redirect, Response, jsonify
from werkzeug.serving import make_server
import json
import csv
import io
import os
import threading
import time
import re

app = Flask(__name__)

# --- PORT 80 CONNECTIVITY CHECK SERVER ---
# Android and iOS check port 80 specifically, but our main app runs on 5000.
# This tiny second Flask app runs on port 80 in a background thread,
# so phones get a valid response and mark the Wi-Fi as "has internet."
captive_app = Flask('captive')

@captive_app.route('/generate_204')
@captive_app.route('/gen_204')
def captive_204():
    return '', 204

@captive_app.route('/hotspot-detect.html')
def captive_ios():
    return '<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>', 200

@captive_app.route('/ncsi.txt')
def captive_ncsi():
    return 'Microsoft NCSI', 200

@captive_app.route('/', defaults={'path': ''})
@captive_app.route('/<path:path>')
def captive_catch_all(path):
    # Catch any other connectivity check variants and return 204
    return '', 204

def run_captive_portal():
    server = make_server('0.0.0.0', 80, captive_app)
    server.serve_forever()

captive_thread = threading.Thread(target=run_captive_portal, daemon=True)
captive_thread.start()
app.config['TEMPLATES_AUTO_RELOAD'] = True 

def load_db():
    with open('inventory.json', 'r') as f:
        return json.load(f)

def save_db(data):
    with open('inventory.json', 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html', inventory=load_db())

@app.route('/record_sale/<item_id>', methods=['POST'])
def record_sale(item_id):
    db = load_db()
    if item_id in db and db[item_id]['quantity'] > 0:
        db[item_id]['quantity'] -= 1
        db[item_id]['sold'] += 1
        save_db(db)
        return jsonify({"status": "success", "new_stock": db[item_id]['quantity'], "new_sold": db[item_id]['sold']})
    return jsonify({"status": "error"}), 400

@app.route('/undo_sale/<item_id>', methods=['POST'])
def undo_sale(item_id):
    db = load_db()
    if item_id in db and db[item_id]['sold'] > 0:
        db[item_id]['quantity'] += 1
        db[item_id]['sold'] -= 1
        save_db(db)
        return jsonify({"status": "success", "new_stock": db[item_id]['quantity'], "new_sold": db[item_id]['sold']})
    return jsonify({"status": "error"}), 400

@app.route('/admin')
def admin():
    return render_template('admin.html', inventory=load_db())

@app.route('/add_item', methods=['POST'])
def add_item():
    db = load_db()
    
    max_num = 0
    for k in db.keys():
        match = re.search(r'\d+', k)
        if match:
            max_num = max(max_num, int(match.group()))
    new_id = f"item_{max_num + 1:02d}"

    db[new_id] = {
        "name": request.form.get('item_name'),
        "price": float(request.form.get('item_price', 0)),
        "quantity": int(request.form.get('item_stock', 0)),
        "sold": 0
    }
    save_db(db)
    return redirect('/admin')

@app.route('/edit_details/<item_id>', methods=['POST'])
def edit_details(item_id):
    db = load_db()
    if item_id in db:
        db[item_id]['name'] = request.form.get('edit_name', db[item_id]['name'])
        db[item_id]['price'] = float(request.form.get('edit_price', db[item_id]['price']))
        db[item_id]['quantity'] = int(request.form.get('edit_stock', db[item_id]['quantity']))
        db[item_id]['sold'] = int(request.form.get('edit_sold', db[item_id]['sold']))
        save_db(db)
    return redirect('/admin')

@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    db = load_db()
    if item_id in db:
        del db[item_id]
        save_db(db)
    return redirect('/admin')

@app.route('/export_csv')
def export_csv():
    db = load_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Item ID', 'Item Name', 'Price ($)', 'Remaining Stock', 'Units Sold', 'Total Revenue ($)'])
    total_earnings = 0.0
    for item_id, info in db.items():
        revenue = info['price'] * info['sold']
        total_earnings += revenue
        writer.writerow([item_id, info['name'], info['price'], info['quantity'], info['sold'], revenue])
    writer.writerow([])
    writer.writerow(['', '', '', '', 'GRAND TOTAL:', f"${total_earnings:.2f}"])
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=convention_sales_report.csv'
    return response

@app.route('/upload_patch', methods=['POST'])
def upload_patch():
    if 'patch_file' not in request.files:
        return "No file uploaded", 400
    file = request.files['patch_file']
    
    if file.filename == 'app.py':
        save_path = '/root/sena_sign/app.py'
        needs_restart = True
    elif file.filename == 'index.html':
        save_path = '/root/sena_sign/templates/index.html'
        needs_restart = False
    elif file.filename == 'admin.html':
        save_path = '/root/sena_sign/templates/admin.html'
        needs_restart = False
    else:
        return "SECURITY BLOCK: Invalid file name.", 403

    file.save(save_path)

    if needs_restart:
        def delayed_restart():
            time.sleep(1) 
            os._exit(0)
        threading.Thread(target=delayed_restart).start()
        
        # UPGRADED JAVASCRIPT: Active Polling instead of a blind timer
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Patching System...</title>
            <style>
                body { background-color: #1e1e24; color: #faebd7; font-family: sans-serif; text-align: center; padding-top: 20vh; }
                .spinner { margin: 20px auto; width: 40px; height: 40px; border: 4px solid rgba(250, 235, 215, 0.3); border-radius: 50%; border-top-color: #faebd7; animation: spin 1s ease-in-out infinite; }
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <h2>⚙️ System Patch Applied</h2>
            <p>Rebooting background engine. Please wait...</p>
            <div class="spinner"></div>
            <script>
                // Give the server 2 seconds to officially shut down...
                setTimeout(function() {
                    // ...then start knocking on the door every 1 second
                    const interval = setInterval(function() {
                        fetch('/admin').then(response => {
                            if(response.ok) {
                                // The door opened! Stop knocking and walk in.
                                clearInterval(interval);
                                window.location.href = '/admin';
                            }
                        }).catch(err => {
                            // Server is still dead. Catch the error silently so the user never sees it.
                        });
                    }, 1000);
                }, 2000);
            </script>
        </body>
        </html>
        """
    
    return redirect('/admin')

# --- CONNECTIVITY CHECK SPOOFS ---
# These make Android and iOS think the network has internet,
# so they stop blocking local traffic to 192.168.42.1.

@app.route('/generate_204')
def generate_204():
    return '', 204  # Android's connectivity check expects exactly this

@app.route('/gen_204')
def gen_204():
    return '', 204  # Fallback used by some Android versions

@app.route('/hotspot-detect.html')
def hotspot_detect():
    return '<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>', 200  # iOS check

@app.route('/ncsi.txt')
def ncsi():
    return 'Microsoft NCSI', 200  # Windows / some Samsung builds check this

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
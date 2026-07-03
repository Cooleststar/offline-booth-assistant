from flask import Flask, render_template, request, redirect, Response, jsonify
import json, csv, io, os, threading, time, re

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True 

def load_db():
    with open('inventory.json', 'r') as f: return json.load(f)

def save_db(data):
    with open('inventory.json', 'w') as f: json.dump(data, f, indent=4)

@app.route('/')
def index(): return render_template('index.html', inventory=load_db())

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
def admin(): return render_template('admin.html', inventory=load_db())

@app.route('/add_item', methods=['POST'])
def add_item():
    db = load_db()
    max_num = 0
    for k in db.keys():
        match = re.search(r'\d+', k)
        if match:
            max_num = max(max_num, int(match.group()))
    new_id = f"item_{max_num + 1:02d}"

    db[new_id] = { "name": request.form.get('item_name'), "price": float(request.form.get('item_price', 0)), "quantity": int(request.form.get('item_stock', 0)), "sold": 0 }
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
    if item_id in db: del db[item_id]
    save_db(db)
    return redirect('/admin')

@app.route('/export_csv')
def export_csv():
    db = load_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Item ID', 'Item Name', 'Price ($)', 'Remaining Stock', 'Units Sold', 'Total Revenue ($)'])
    total = sum(info['price'] * info['sold'] for info in db.values())
    for item_id, info in db.items(): writer.writerow([item_id, info['name'], info['price'], info['quantity'], info['sold'], info['price'] * info['sold']])
    writer.writerows([[], ['', '', '', '', 'GRAND TOTAL:', f"${total:.2f}"]])
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=sales_report.csv'
    return response

# --- NEW HARDWARE CONTROL ROUTES ---
@app.route('/system/reboot', methods=['POST'])
def sys_reboot():
    def execute_reboot():
        time.sleep(1)
        os.system("reboot")
    threading.Thread(target=execute_reboot).start()
    return jsonify({"status": "success"})

@app.route('/system/shutdown', methods=['POST'])
def sys_shutdown():
    def execute_shutdown():
        time.sleep(1)
        os.system("shutdown -h now")
    threading.Thread(target=execute_shutdown).start()
    return jsonify({"status": "success"})

@app.route('/upload_patch', methods=['POST'])
def upload_patch():
    file = request.files.get('patch_file')
    if not file or file.filename not in ['app.py', 'index.html', 'admin.html']: return "Invalid", 403
    save_path = f"/root/sena_sign/{'templates/' if file.filename != 'app.py' else ''}{file.filename}"
    file.save(save_path)
    if file.filename == 'app.py':
        threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()
        return "<!DOCTYPE html><html><body style='background:#1e1e24;color:#faebd7;text-align:center;padding-top:20vh'><h2>⚙️ Patch Applied</h2><p>Rebooting...</p><script>setTimeout(()=>setInterval(()=>fetch('/admin').then(r=>{if(r.ok)window.location.href='/admin'}),1000),2000)</script></body></html>"
    return redirect('/admin')

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
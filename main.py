from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Usar la variable de entorno DATABASE_URL, que debe tener el connection string del pooler
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    # ¡No hardcodees el connection string! Usa solo la variable de entorno.
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/update', methods=['POST'])
def update_inventory():
    data = request.json
    usuario = data.get('usuario')
    items = data.get('items', [])

    if not usuario or not items:
        return jsonify({"status": "error", "error": "Faltan datos"}), 400

    updated_count = 0
    try:
        conn = get_conn()
        cur = conn.cursor()
        for item in items:
            producto = item.get('producto')
            cantidad = item.get('cantidad')
            caducidad = item.get('caducidad', None)
            # Insertar o actualizar usando ON CONFLICT
            cur.execute("""
                INSERT INTO inventario (usuario, producto, cantidad, caducidad)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (usuario, producto)
                DO UPDATE SET cantidad = EXCLUDED.cantidad, caducidad = EXCLUDED.caducidad, ultima_actualizacion = now()
            """, (usuario, producto, cantidad, caducidad))
            updated_count += 1
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "items_actualizados": updated_count})
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/inventory', methods=['GET'])
def get_inventory():
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({"status": "error", "error": "Falta usuario"}), 400
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT producto, cantidad, caducidad FROM inventario WHERE usuario = %s", (usuario,))
        items = [{"producto": p, "cantidad": float(c), "caducidad": cd} for p, c, cd in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "inventario": items})
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/consume', methods=['POST'])
def consume_items():
    data = request.json
    usuario = data.get('usuario')
    items = data.get('items', [])
    if not usuario or not items:
        return jsonify({"status": "error", "error": "Faltan datos"}), 400
    try:
        conn = get_conn()
        cur = conn.cursor()
        for item in items:
            producto = item.get('producto')
            cantidad = item.get('cantidad')
            if not producto or cantidad is None:
                continue
            # Restar cantidad consumida sin bajar de cero
            cur.execute("""
                UPDATE inventario
                SET cantidad = GREATEST(cantidad - %s, 0), ultima_actualizacion = now()
                WHERE usuario = %s AND producto = %s
            """, (cantidad, usuario, producto))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "items_consumidos": len(items)})
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "NutriBot está funcionando. Usa los endpoints /update, /inventory y /consume."

if __name__ == '__main__':
    app.run()


if __name__ == '__main__':
    app.run()

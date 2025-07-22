from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# Usa la variable de entorno DATABASE_URL para mayor seguridad
DATABASE_URL = os.environ.get("DATABASE_URL") or "postgresql://postgres.lonzpyfnlspxlmjmzsbw:Ez7c!AE.wwiX?UN@aws-0-eu-west-3.pooler.supabase.com:6543/postgres"


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/update', methods=['POST'])
def update_inventory():
    data = request.get_json()
    usuario = data.get("usuario")
    items = data.get("items", [])

    if not usuario or not items:
        return jsonify({"error": "Faltan datos"}), 400

    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow()

    for item in items:
        producto = item.get("producto")
        cantidad = item.get("cantidad")
        caducidad = item.get("caducidad") or None

        # Si ya existe, actualiza. Si no, inserta.
        cur.execute("""
            INSERT INTO inventario (usuario, producto, cantidad, caducidad, ultima_actualizacion)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (usuario, producto)
            DO UPDATE SET cantidad = EXCLUDED.cantidad, caducidad = EXCLUDED.caducidad, ultima_actualizacion = EXCLUDED.ultima_actualizacion
            """,
            (usuario, producto, cantidad, caducidad, now)
        )

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok", "items_actualizados": len(items)})

# OPCIONAL: Para consultar inventario de un usuario
@app.route('/get', methods=['GET'])
def get_inventory():
    usuario = request.args.get("usuario")
    if not usuario:
        return jsonify({"error": "Falta el usuario"}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT producto, cantidad, caducidad, ultima_actualizacion FROM inventario WHERE usuario = %s", (usuario,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    items = []
    for r in rows:
        items.append({
            "producto": r[0],
            "cantidad": r[1],
            "caducidad": str(r[2]) if r[2] else "",
            "ultima_actualizacion": r[3].isoformat() if r[3] else ""
        })

    return jsonify({"usuario": usuario, "inventario": items})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)



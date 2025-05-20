from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from config import init_db, Config
import openpyxl
from io import BytesIO
from hashlib import md5
from bson import ObjectId
from bson.errors import InvalidId
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

# Configura las URIs antes de llamar a init_db
app.config["MONGO_URI"] = Config.MONGO_URI
app.config["MONGO_URI_LOCAL"] = Config.MONGO_URI_LOCAL

# Inicializa las conexiones con la base de datos
mongo_atlas, mongo_local = init_db(app)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('usuario')
    password = data.get('password')

    if not usuario or not password:
        return jsonify({'message': 'Faltan campos'}), 400

    user = mongo_atlas.db.usuarios.find_one({'usuario': usuario})

    if user and user['password'] == md5(password.encode()).hexdigest():
        return jsonify({'message': 'Login exitoso'})
    else:
        return jsonify({'message': 'Credenciales inválidas'}), 401

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    usuario = data.get("usuario")
    password = data.get("password")

    if not usuario or not password:
        return jsonify({"message": "Faltan campos"}), 400

    password_hash = md5(password.encode()).hexdigest()

    if mongo_atlas.db.usuarios.find_one({"usuario": usuario}):
        return jsonify({"message": "El usuario ya existe"}), 400

    # Inserción en ambas bases de datos (Atlas y local)
    mongo_atlas.db.usuarios.insert_one({"usuario": usuario, "password": password_hash})
    mongo_local.db.usuarios.insert_one({"usuario": usuario, "password": password_hash})  # espejo

    return jsonify({"message": "Usuario registrado exitosamente"}), 201

@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

# CRUD PRODUCTOS

@app.route("/productos", methods=["GET"])
def obtener_productos():
    productos = mongo_atlas.db.productos.find()
    return jsonify([{**producto, "_id": str(producto["_id"])} for producto in productos])

@app.route("/productos/agregar", methods=["POST"])
def agregar_producto():
    data = request.get_json()
    nombre = data.get("nombre")
    cantidad = data.get("cantidad")
    precio = data.get("precio")

    if not nombre or cantidad is None or precio is None:
        return jsonify({"message": "Faltan datos para agregar el producto"}), 400

    try:
        cantidad = int(cantidad)
        precio = float(precio)
    except (ValueError, TypeError):
        return jsonify({"message": "Cantidad o precio inválidos"}), 400

    producto = {
        "nombre": nombre,
        "cantidad": cantidad,
        "precio": precio
    }

    mongo_atlas.db.productos.insert_one(producto)
    mongo_local.db.productos.insert_one(producto)
    return jsonify({"message": "Producto agregado"}), 201

@app.route("/productos/actualizar", methods=["PUT"])
def actualizar_producto():
    data = request.get_json()
    producto_id = data.get("id")
    nombre = data.get("nombre")
    cantidad = data.get("cantidad")
    precio = data.get("precio")

    if not producto_id or not nombre or cantidad is None or precio is None:
        return jsonify({"message": "Faltan datos para actualizar el producto"}), 400

    try:
        filtro = {"_id": ObjectId(producto_id)}
    except InvalidId:
        return jsonify({"message": "ID inválido"}), 400

    try:
        cantidad = int(cantidad)
        precio = float(precio)
    except (ValueError, TypeError):
        return jsonify({"message": "Cantidad o precio inválidos"}), 400

    cambios = {
        "nombre": nombre,
        "cantidad": cantidad,
        "precio": precio
    }

    if not mongo_atlas.db.productos.find_one(filtro):
        return jsonify({"message": "Producto no encontrado"}), 404

    mongo_atlas.db.productos.update_one(filtro, {"$set": cambios})
    mongo_local.db.productos.update_one(filtro, {"$set": cambios})
    return jsonify({"message": "Producto actualizado"})

@app.route("/productos/eliminar", methods=["DELETE"])
def eliminar_producto():
    data = request.get_json()
    producto_id = data.get("id")

    if not producto_id:
        return jsonify({"message": "Falta ID para eliminar producto"}), 400

    try:
        filtro = {"_id": ObjectId(producto_id)}
    except InvalidId:
        return jsonify({"message": "ID inválido"}), 400

    if not mongo_atlas.db.productos.find_one(filtro):
        return jsonify({"message": "Producto no encontrado"}), 404

    mongo_atlas.db.productos.delete_one(filtro)
    mongo_local.db.productos.delete_one(filtro)
    return jsonify({"message": "Producto eliminado"})

@app.route("/reporte", methods=["GET"])
def generar_reporte():
    productos = mongo_atlas.db.productos.find()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ID", "Nombre", "Cantidad", "Precio"])

    for producto in productos:
        ws.append([
            str(producto["_id"]),
            producto["nombre"],
            producto["cantidad"],
            producto["precio"]
        ])

    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return send_file(
        excel_file,
        download_name="reporte_productos.xlsx",
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(debug=True)


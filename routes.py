from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from config import init_db, Config
import openpyxl
from io import BytesIO
from hashlib import md5
from bson import ObjectId

app = Flask(__name__)

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

# CRUD
@app.route("/productos", methods=["GET", "POST", "PUT", "DELETE"])
def productos():
    if request.method == "GET":
        productos = mongo_atlas.db.productos.find()  # Usar mongo_atlas para obtener los productos
        return jsonify([{**producto, "_id": str(producto["_id"])} for producto in productos])

    elif request.method == "POST":
        data = request.get_json()
        producto = {
            "nombre": data.get("nombre"),
            "cantidad": int(data.get("cantidad")),
            "precio": float(data.get("precio"))
        }

        # Insertar en ambas bases de datos
        mongo_atlas.db.productos.insert_one(producto)
        mongo_local.db.productos.insert_one(producto)  # espejo

        return jsonify({"message": "Producto agregado"}), 201

    elif request.method == "PUT":
        data = request.get_json()
        producto_id = data.get("id")
        cambios = {
            "nombre": data.get("nombre"),
            "cantidad": int(data.get("cantidad")),
            "precio": float(data.get("precio"))
        }

        filtro = {"_id": ObjectId(producto_id)}

       
        if not mongo_atlas.db.productos.find_one(filtro):
            return jsonify({"message": "Producto no encontrado"}), 404

        
        mongo_atlas.db.productos.update_one(filtro, {"$set": cambios})
        mongo_local.db.productos.update_one(filtro, {"$set": cambios})  # espejo

        return jsonify({"message": "Producto actualizado"})

    elif request.method == "DELETE":
        data = request.get_json()
        producto_id = data.get("id")
        filtro = {"_id": ObjectId(producto_id)}

        
        if not mongo_atlas.db.productos.find_one(filtro):
            return jsonify({"message": "Producto no encontrado"}), 404

        # Eliminar en ambas bases de datos
        mongo_atlas.db.productos.delete_one(filtro)
        mongo_local.db.productos.delete_one(filtro)  # espejo

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

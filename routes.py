# routes.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from models import init_db, crear_usuario_local, Config
import openpyxl
from io import BytesIO
from hashlib import md5

app = Flask(__name__)

# Configura las URIs antes de llamar a init_db
app.config["MONGO_URI"] = Config.MONGO_URI
app.config["MONGO_LOCAL_URI"] = Config.MONGO_URI_LOCAL

# Inicializa las conexiones con la base de datos
mongo, mongo_local = init_db(app)

# Ruta de login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()  # Obtener los datos en formato JSON
    usuario = data.get("usuario")
    password = data.get("password")

    # Buscar en base de datos en la nube (AtlasDB)
    user = mongo.db.usuarios.find_one({"usuario": usuario})

    # Verificar si el usuario existe y la contraseña es correcta
    if user and user["password"] == md5(password.encode()).hexdigest():
        return jsonify({"message": "Login exitoso"}), 200
    else:
        return jsonify({"message": "Credenciales incorrectas"}), 401

# Ruta para registrar nuevos usuarios
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()  # Obtener los datos en formato JSON
    usuario = data.get("usuario")
    password = data.get("password")
    password_hash = md5(password.encode()).hexdigest()

    # Verificar si el usuario ya existe
    if mongo.db.usuarios.find_one({"usuario": usuario}):
        return jsonify({"message": "El usuario ya existe"}), 400

    # Crear nuevo usuario en MongoDB (AtlasDB)
    mongo.db.usuarios.insert_one({"usuario": usuario, "password": password_hash})
    return jsonify({"message": "Usuario registrado exitosamente"}), 201

# Ruta del dashboard (página principal después de login)
@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

# CRUD para gestionar productos
@app.route("/productos", methods=["GET", "POST", "PUT", "DELETE"])
def productos():
    if request.method == "GET":
        productos = mongo.db.productos.find()
        return jsonify([producto for producto in productos])

    elif request.method == "POST":
        data = request.get_json()  # Obtener los datos en formato JSON
        nombre = data.get("nombre")
        cantidad = int(data.get("cantidad"))
        precio = float(data.get("precio"))

        producto = {
            "nombre": nombre,
            "cantidad": cantidad,
            "precio": precio
        }
        mongo.db.productos.insert_one(producto)
        return jsonify({"message": "Producto agregado"}), 201

    elif request.method == "PUT":
        data = request.get_json()  # Obtener los datos en formato JSON
        producto_id = data.get("id")
        nombre = data.get("nombre")
        cantidad = int(data.get("cantidad"))
        precio = float(data.get("precio"))

        mongo.db.productos.update_one(
            {"_id": mongo.db.productos.ObjectId(producto_id)},
            {"$set": {"nombre": nombre, "cantidad": cantidad, "precio": precio}}
        )
        return jsonify({"message": "Producto actualizado"})

    elif request.method == "DELETE":
        data = request.get_json()  # Obtener los datos en formato JSON
        producto_id = data.get("id")
        mongo.db.productos.delete_one({"_id": mongo.db.productos.ObjectId(producto_id)})
        return jsonify({"message": "Producto eliminado"})

# Ruta para imprimir reportes en Excel
@app.route("/reporte", methods=["GET"])
def generar_reporte():
    productos = mongo.db.productos.find()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ID", "Nombre", "Cantidad", "Precio"])
    
    for producto in productos:
        ws.append([str(producto["_id"]), producto["nombre"], producto["cantidad"], producto["precio"]])

    # Guardar el archivo en memoria
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    return send_file(excel_file, attachment_filename="reporte_productos.xlsx", as_attachment=True)

# Función para crear un usuario por defecto en la base de datos local (si está vacío)
def crear_usuario_local_inicial():
    if mongo_local.db.usuarios.count_documents({}) == 0:
        crear_usuario_local(mongo_local, "admin", "admin123")

# Iniciar la aplicación
if __name__ == "__main__":
    # Crear un usuario local por defecto (solo para propósito de ejemplo)
    crear_usuario_local_inicial()
    app.run(debug=True)

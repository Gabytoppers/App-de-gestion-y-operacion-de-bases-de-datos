from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash  # Reemplazo de md5

class Config:
    MONGO_URI = "mongodb+srv://myAtlasDBUser:1097781666@myatlasclusteredu.jakrico.mongodb.net/?retryWrites=true&w=majority&appName=myAtlasClusterEDU"
    MONGO_URI_LOCAL = "mongodb://localhost:27017/stock_app_local"

def init_db(app):
    mongo = PyMongo(app, uri=app.config["MONGO_URI"])  # Conexión a Atlas DB
    mongo_local = PyMongo(app, uri=app.config["MONGO_LOCAL_URI"])  # Conexión a base de datos local
    return mongo, mongo_local

def crear_usuario_local(mongo_local, usuario, password):
    # Usar una contraseña más segura con werkzeug.security
    hashed_password = generate_password_hash(password)
    mongo_local.db.usuarios.insert_one({"usuario": usuario, "password": hashed_password})

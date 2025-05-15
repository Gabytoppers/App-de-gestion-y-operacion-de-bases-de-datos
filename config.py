from flask_pymongo import PyMongo

class Config:

    MONGO_URI = "mongodb+srv://gabydevpereira:AmYJBPEgBhp8mOAm@cluster0.ans4nre.mongodb.net/stock_app_atlas?retryWrites=true&w=majority&appName=Cluster0"
    
    
    MONGO_URI_LOCAL = "mongodb://localhost:27017/stock_app_local"


def init_db(app):
    mongo_atlas = PyMongo(app, uri=app.config["MONGO_URI"])
    mongo_local = PyMongo(app, uri=app.config["MONGO_URI_LOCAL"])
    return mongo_atlas, mongo_local

import os
from dotenv import load_dotenv
from flask import Flask
from pymongo import MongoClient
from notevortex.routes import pages

load_dotenv()

def create_app():
    app=Flask(__name__)
    app.config["MONGODB_URI"]=os.environ.get("MONGODB_URI")
    app.config["title_crypt"]=os.environ.get("title_crypt")
    app.config["content_crypt"]=os.environ.get("content_crypt")
    app.config["SECRET_KEY"]=os.environ.get(
        "SECRET_KEY","840aa87753d94146a2976cff7935c3f59fad71855c4"
    )
    app.db=MongoClient(app.config["MONGODB_URI"]).notevortex
    app.register_blueprint(pages)
    return app
    
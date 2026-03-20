from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db

app = Flask(__name__)

# Basic Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['json.compact'] = False

# Setup JWT Secret Key (in a real app, this goes in your .env file!)
app.config['JWT_SECRET_KEY'] = 'super-secret-jacktrack-key' 

# Initialize Extensions
CORS(app)
migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)
jwt = JWTManager(app)

# A simple check to ensure the server is running
@app.route('/')
def index():
    return "JackTrack API is running!"

if __name__ == '__main__':
    app.run(port=5555, debug=True)
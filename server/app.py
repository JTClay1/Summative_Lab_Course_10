from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, DailyLog, Ingredient, Meal, MealIngredient

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

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return {'error': 'Username already exists'}, 400

        try:
            # Initialize user and trigger the bcrypt setter
            new_user = User(username=username)
            new_user.password_hash = password 
            
            db.session.add(new_user)
            db.session.commit()

            # Generate JWT token
            access_token = create_access_token(identity=new_user.id)
            return {'user': new_user.to_dict(), 'access_token': access_token}, 201

        except ValueError as e:
            return {'error': str(e)}, 400

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Find user by username
        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if user and user.authenticate(password):
            access_token = create_access_token(identity=user.id)
            return {'user': user.to_dict(), 'access_token': access_token}, 200

        return {'error': 'Invalid username or password'}, 401

class CheckSession(Resource):
    @jwt_required() # This decorator enforces that a valid JWT must be present!
    def get(self):
        # get_jwt_identity() extracts the user ID we saved inside the token
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user:
            return user.to_dict(), 200
            
        return {'error': 'User not found'}, 404

# Register the routes with Flask-RESTful
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(CheckSession, '/check_session')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
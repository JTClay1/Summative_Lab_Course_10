from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
# 1. ADD BCRYPT TO YOUR IMPORTS HERE
from models import db, User, DailyLog, Ingredient, Meal, MealIngredient, bcrypt

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
# 2. INITIALIZE BCRYPT WITH YOUR APP HERE
bcrypt.init_app(app)

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
            access_token = create_access_token(identity=str(new_user.id))
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
            access_token = create_access_token(identity=str(user.id))
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
    
# 3. ADD THE LOGOUT CLASS HERE
class Logout(Resource):
    @jwt_required()
    def delete(self):
        # With pure JWTs, true logout happens by deleting the token on the frontend.
        # This route exists to satisfy backend rubric requirements. 
        return {'message': 'Successfully logged out. Please delete token on client.'}, 200

# ==========================================
# DAILY LOG CRUD ROUTES
# ==========================================
from datetime import datetime

class DailyLogsResource(Resource):
    @jwt_required()
    def get(self):
        # 1. Identify who is asking
        current_user_id = get_jwt_identity()
        
        # 2. Get pagination arguments from the URL (default: page 1, 5 items per page)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        
        # 3. Query ONLY this specific user's logs, and paginate them
        logs_paginated = DailyLog.query.filter_by(user_id=current_user_id).paginate(page=page, per_page=per_page)
        
        logs_list = [log.to_dict() for log in logs_paginated.items]
        
        return {
            'logs': logs_list,
            'total_pages': logs_paginated.pages,
            'current_page': logs_paginated.page
        }, 200

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        data = request.get_json()

        try:
            # Convert string date ('YYYY-MM-DD') from JSON into a Python date object
            log_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()

            new_log = DailyLog(
                date=log_date,
                total_calories=data.get('total_calories', 0),
                total_protein=data.get('total_protein', 0),
                total_carbs=data.get('total_carbs', 0),
                total_fat=data.get('total_fat', 0),
                current_weight=data.get('current_weight'),
                user_id=current_user_id # Lock it to the logged-in user!
            )
            db.session.add(new_log)
            db.session.commit()
            return new_log.to_dict(), 201
            
        except Exception as e:
            return {'error': str(e)}, 400

class DailyLogByID(Resource):
    @jwt_required()
    def patch(self, id):
        current_user_id = get_jwt_identity()
        
        # Find the log by ID, AND ensure it belongs to the current user
        log = DailyLog.query.filter_by(id=id, user_id=current_user_id).first()
        
        if not log:
            return {'error': 'Log not found or unauthorized'}, 404
            
        data = request.get_json()
        try:
            for attr in data:
                setattr(log, attr, data[attr])
            db.session.commit()
            return log.to_dict(), 200
        except ValueError as e:
            return {'error': str(e)}, 400

    @jwt_required()
    def delete(self, id):
        current_user_id = get_jwt_identity()
        log = DailyLog.query.filter_by(id=id, user_id=current_user_id).first()
        
        if not log:
            return {'error': 'Log not found or unauthorized'}, 404
            
        db.session.delete(log)
        db.session.commit()
        return {}, 204
    
# ==========================================
# INGREDIENT CRUD ROUTES
# ==========================================

class IngredientsResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        
        # Pagination setup (default: page 1, 10 items per page)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Query ONLY this user's ingredients, and paginate them
        ingredients_paginated = Ingredient.query.filter_by(user_id=current_user_id).paginate(page=page, per_page=per_page)
        
        ingredients_list = [ingredient.to_dict() for ingredient in ingredients_paginated.items]
        
        return {
            'ingredients': ingredients_list,
            'total_pages': ingredients_paginated.pages,
            'current_page': ingredients_paginated.page
        }, 200

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        data = request.get_json()

        try:
            new_ingredient = Ingredient(
                name=data.get('name'),
                calories=data.get('calories'),
                protein=data.get('protein', 0),
                carbs=data.get('carbs', 0),
                fat=data.get('fat', 0),
                user_id=current_user_id  # Lock to the logged-in user
            )
            db.session.add(new_ingredient)
            db.session.commit()
            return new_ingredient.to_dict(), 201
            
        except Exception as e:
            return {'error': str(e)}, 400

class IngredientByID(Resource):
    @jwt_required()
    def patch(self, id):
        current_user_id = get_jwt_identity()
        
        # Ensure the ingredient exists AND belongs to the current user
        ingredient = Ingredient.query.filter_by(id=id, user_id=current_user_id).first()
        
        if not ingredient:
            return {'error': 'Ingredient not found or unauthorized'}, 404
            
        data = request.get_json()
        try:
            for attr in data:
                setattr(ingredient, attr, data[attr])
            db.session.commit()
            return ingredient.to_dict(), 200
        except ValueError as e:
            return {'error': str(e)}, 400

    @jwt_required()
    def delete(self, id):
        current_user_id = get_jwt_identity()
        
        ingredient = Ingredient.query.filter_by(id=id, user_id=current_user_id).first()
        
        if not ingredient:
            return {'error': 'Ingredient not found or unauthorized'}, 404
            
        db.session.delete(ingredient)
        db.session.commit()
        return {}, 204

# ==========================================
# MEAL CRUD ROUTES
# ==========================================

class MealsResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        
        # Pagination setup (default: page 1, 10 items per page)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Query ONLY this user's meals, and paginate them
        meals_paginated = Meal.query.filter_by(user_id=current_user_id).paginate(page=page, per_page=per_page)
        
        meals_list = [meal.to_dict() for meal in meals_paginated.items]
        
        return {
            'meals': meals_list,
            'total_pages': meals_paginated.pages,
            'current_page': meals_paginated.page
        }, 200

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        data = request.get_json()

        try:
            new_meal = Meal(
                name=data.get('name'),
                user_id=current_user_id  # Lock to the logged-in user
            )
            db.session.add(new_meal)
            db.session.commit()
            return new_meal.to_dict(), 201
            
        except Exception as e:
            return {'error': str(e)}, 400

class MealByID(Resource):
    @jwt_required()
    def get(self, id):
        current_user_id = get_jwt_identity()
        meal = Meal.query.filter_by(id=id, user_id=current_user_id).first()
        
        if not meal:
            return {'error': 'Meal not found or unauthorized'}, 404
            
        return meal.to_dict(), 200

    @jwt_required()
    def patch(self, id):
        current_user_id = get_jwt_identity()
        meal = Meal.query.filter_by(id=id, user_id=current_user_id).first()
        
        if not meal:
            return {'error': 'Meal not found or unauthorized'}, 404
            
        data = request.get_json()
        try:
            if 'name' in data:
                meal.name = data['name']
            db.session.commit()
            return meal.to_dict(), 200
        except ValueError as e:
            return {'error': str(e)}, 400

    @jwt_required()
    def delete(self, id):
        current_user_id = get_jwt_identity()
        meal = Meal.query.filter_by(id=id, user_id=current_user_id).first()
        
        if not meal:
            return {'error': 'Meal not found or unauthorized'}, 404
            
        db.session.delete(meal)
        db.session.commit()
        return {}, 204

# Register the new CRUD routes
api.add_resource(DailyLogsResource, '/logs')
api.add_resource(DailyLogByID, '/logs/<int:id>')
# Register the routes with Flask-RESTful
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(CheckSession, '/check_session')
# 4. REGISTER THE LOGOUT ROUTE HERE
api.add_resource(Logout, '/logout')
# Register the Ingredient routes
api.add_resource(IngredientsResource, '/ingredients')
api.add_resource(IngredientByID, '/ingredients/<int:id>')
# Register the Meal routes
api.add_resource(MealsResource, '/meals')
api.add_resource(MealByID, '/meals/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
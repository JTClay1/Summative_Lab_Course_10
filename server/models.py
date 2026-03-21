from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt

# Naming conventions to ensure Alembic handles migrations and foreign keys smoothly
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    # Relationships to tie everything back to the specific user
    logs = db.relationship('DailyLog', backref='user', cascade='all, delete-orphan')
    ingredients = db.relationship('Ingredient', backref='user', cascade='all, delete-orphan')
    meals = db.relationship('Meal', backref='user', cascade='all, delete-orphan')

    # Prevent recursive serialization and hide the password hash from API responses
    serialize_rules = ('-logs.user', '-ingredients.user', '-meals.user', '-_password_hash',)

    @hybrid_property
    def password_hash(self):
        # Block read access to the raw password hash
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        # Automatically hash the password using bcrypt when a new password is set
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        # Verify if the provided password matches the stored hash
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError("Username must be provided")
        return username

    def __repr__(self):
        return f'<User {self.username}>'


class DailyLog(db.Model, SerializerMixin):
    __tablename__ = 'daily_logs'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    
    # Tracking full macros for daily nutritional goals
    total_calories = db.Column(db.Integer, nullable=False, default=0)
    total_protein = db.Column(db.Integer, nullable=False, default=0)
    total_carbs = db.Column(db.Integer, nullable=False, default=0)
    total_fat = db.Column(db.Integer, nullable=False, default=0)
    
    current_weight = db.Column(db.Float, nullable=True) 

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    serialize_rules = ('-user.logs', '-user.ingredients', '-user.meals',)

    @validates('total_calories', 'total_protein', 'total_carbs', 'total_fat')
    def validate_macros(self, key, value):
        # Quick check to ensure we aren't logging negative macros
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    def __repr__(self):
        return f'<DailyLog {self.date} - {self.total_calories} kcal>'


class Ingredient(db.Model, SerializerMixin):
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    
    # Base macros for a single ingredient
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Integer, nullable=False, default=0)
    carbs = db.Column(db.Integer, nullable=False, default=0)
    fat = db.Column(db.Integer, nullable=False, default=0)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    serialize_rules = ('-user.ingredients', '-user.logs', '-user.meals',)

    def __repr__(self):
        return f'<Ingredient {self.name} | P:{self.protein} C:{self.carbs} F:{self.fat}>'


class Meal(db.Model, SerializerMixin):
    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Link to the join table to associate multiple ingredients with a single meal
    meal_ingredients = db.relationship('MealIngredient', backref='meal', cascade='all, delete-orphan')

    serialize_rules = ('-user.meals', '-user.logs', '-user.ingredients', '-meal_ingredients.meal',)

    def __repr__(self):
        return f'<Meal {self.name}>'


class MealIngredient(db.Model, SerializerMixin):
    __tablename__ = 'meal_ingredients'

    # Join table between Meals and Ingredients to handle many-to-many relationships
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    
    # Allows users to adjust portion sizes (e.g., 1.5 servings of rice)
    quantity = db.Column(db.Float, nullable=False, default=1.0)

    ingredient = db.relationship('Ingredient')

    serialize_rules = ('-meal.meal_ingredients', '-ingredient',)
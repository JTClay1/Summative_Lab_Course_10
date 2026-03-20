from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt

# Standard naming convention for migrations
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

    # Relationship to JackTrack logs
    logs = db.relationship('DailyLog', backref='user', cascade='all, delete-orphan')

    # Serialization rules: hide the password hash and prevent recursion
    serialize_rules = ('-logs.user', '-_password_hash',)

    # --- Bcrypt Password Protection ---
    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    # --- Validations ---
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
    total_calories = db.Column(db.Integer, nullable=False)
    current_weight = db.Column(db.Float, nullable=True) 

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Serialization rules: prevent recursion
    serialize_rules = ('-user.logs',)

    # --- Validations ---
    @validates('total_calories')
    def validate_calories(self, key, total_calories):
        if total_calories < 0:
            raise ValueError("Calories cannot be negative")
        return total_calories

    def __repr__(self):
        return f'<DailyLog {self.date} - {self.total_calories} kcal>'
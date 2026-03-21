from datetime import date

import pytest
from flask_jwt_extended import create_access_token

from app import app
from models import db, User, DailyLog, Ingredient, Meal, MealIngredient


@pytest.fixture(scope="session")
def test_app(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY="test-secret",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(test_app):
    return test_app.test_client()


@pytest.fixture(autouse=True)
def clean_db(test_app):
    # Clear data between tests to keep things isolated
    with test_app.app_context():
        yield
        db.session.rollback()
        MealIngredient.query.delete()
        Meal.query.delete()
        Ingredient.query.delete()
        DailyLog.query.delete()
        User.query.delete()
        db.session.commit()


@pytest.fixture()
def user(test_app):
    with test_app.app_context():
        new_user = User(username="test_user")
        new_user.password_hash = "password123"
        db.session.add(new_user)
        db.session.commit()
        return new_user


@pytest.fixture()
def access_token(test_app, user):
    with test_app.app_context():
        return create_access_token(identity=user.id)


@pytest.fixture()
def auth_header(access_token):
    return {"Authorization": f"Bearer {access_token}"}

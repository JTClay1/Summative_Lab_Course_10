import sys
import os
import pytest

# Ensure /server is on the import path so "app" and "models" can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models import db, User, DailyLog, Ingredient, Meal, MealIngredient


@pytest.fixture(scope="session")
def test_app(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY="super-secret-jacktrack-key",  # must match app.py
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
def user_id(test_app):
    with test_app.app_context():
        new_user = User(username="test_user")
        new_user.password_hash = "password123"
        db.session.add(new_user)
        db.session.commit()
        return new_user.id


@pytest.fixture()
def auth_header(client, user_id):
    # Use the real login endpoint to get a valid token
    response = client.post("/login", json={
        "username": "test_user",
        "password": "password123"
    })
    assert response.status_code == 200, response.get_json()
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
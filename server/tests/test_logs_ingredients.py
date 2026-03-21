from datetime import date

from models import db, DailyLog, Ingredient

def test_logs_requires_auth(client):
    response = client.get("/logs")
    assert response.status_code == 401

def test_logs_index_returns_user_logs(client, auth_header, user, test_app):
    # Wrap database operations in the app context!
    with test_app.app_context():
        # Create a log directly in the DB for the user
        log = DailyLog(
            date=date(2026, 3, 21),
            total_calories=400,
            total_protein=30,
            total_carbs=50,
            total_fat=10,
            current_weight=180.0,
            user_id=user.id,
        )
        db.session.add(log)
        db.session.commit()

    response = client.get("/logs", headers=auth_header)
    assert response.status_code == 200
    data = response.get_json()

    assert "logs" in data
    assert len(data["logs"]) == 1
    assert data["logs"][0]["total_calories"] == 400

def test_create_log(client, auth_header):
    payload = {
        "date": "2026-03-21",
        "total_calories": 500,
        "total_protein": 40,
        "total_carbs": 60,
        "total_fat": 15,
        "current_weight": 179.5,
    }
    response = client.post("/logs", json=payload, headers=auth_header)
    assert response.status_code == 201
    data = response.get_json()
    assert data["total_calories"] == 500

def test_ingredients_requires_auth(client):
    response = client.get("/ingredients")
    assert response.status_code == 401

def test_ingredients_index_returns_user_ingredients(client, auth_header, user, test_app):
    # Wrap database operations in the app context!
    with test_app.app_context():
        ingredient = Ingredient(
            name="Oats",
            calories=150,
            protein=5,
            carbs=27,
            fat=3,
            user_id=user.id,
        )
        db.session.add(ingredient)
        db.session.commit()

    response = client.get("/ingredients", headers=auth_header)
    assert response.status_code == 200
    data = response.get_json()

    assert "ingredients" in data
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["name"] == "Oats"

def test_create_ingredient(client, auth_header):
    payload = {
        "name": "Banana",
        "calories": 105,
        "protein": 1,
        "carbs": 27,
        "fat": 0,
    }
    response = client.post("/ingredients", json=payload, headers=auth_header)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Banana"
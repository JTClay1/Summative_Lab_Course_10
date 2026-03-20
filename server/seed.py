from app import app
from models import db, User, DailyLog, Ingredient, Meal, MealIngredient
from datetime import date

with app.app_context():
    print("Clearing out old data...")
    # Delete in reverse order of relationships to avoid foreign key conflicts
    MealIngredient.query.delete()
    Meal.query.delete()
    Ingredient.query.delete()
    DailyLog.query.delete()
    User.query.delete()

    print("Creating test user...")
    # Notice we use password_hash, which triggers bcrypt setter!
    user1 = User(username="jack_tracker")
    
    user1.password_hash = "password123"

    db.session.add(user1)
    db.session.commit() # Commit here so user1 gets an ID we can use

    print("Adding basic ingredients...")
    chicken = Ingredient(name="Chicken Breast (4oz)", calories=165, protein=31, carbs=0, fat=4, user_id=user1.id)
    rice = Ingredient(name="White Rice (1 cup)", calories=205, protein=4, carbs=45, fat=0, user_id=user1.id)
    broccoli = Ingredient(name="Steamed Broccoli (1 cup)", calories=31, protein=3, carbs=6, fat=0, user_id=user1.id)
    
    db.session.add_all([chicken, rice, broccoli])
    db.session.commit()

    print("Creating a saved meal...")
    post_workout = Meal(name="Post-Workout Bowl", user_id=user1.id)
    db.session.add(post_workout)
    db.session.commit()

    print("Linking ingredients to the meal...")
    # Let's say this meal has 1.5 servings of chicken, 1 serving of rice, and 1 serving of broccoli
    mi1 = MealIngredient(meal_id=post_workout.id, ingredient_id=chicken.id, quantity=1.5)
    mi2 = MealIngredient(meal_id=post_workout.id, ingredient_id=rice.id, quantity=1.0)
    mi3 = MealIngredient(meal_id=post_workout.id, ingredient_id=broccoli.id, quantity=1.0)
    
    db.session.add_all([mi1, mi2, mi3])
    
    print("Logging a day's macros...")
    # Doing some quick math for the log based on the meal above
    log1 = DailyLog(
        date=date.today(),
        total_calories=483, # (165 * 1.5) + 205 + 31
        total_protein=53,   # (31 * 1.5) + 4 + 3
        total_carbs=51,     # (0 * 1.5) + 45 + 6
        total_fat=6,        # (4 * 1.5) + 0 + 0
        current_weight=180.5,
        user_id=user1.id
    )
    db.session.add(log1)
    db.session.commit()

    print("✅ Database successfully seeded!")
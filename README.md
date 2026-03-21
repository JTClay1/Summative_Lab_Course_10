# JackTrack API

## Project Description
JackTrack is a secure, full-auth RESTful Flask API designed to track personal fitness, weight loss, and nutritional data. Users can securely create accounts, log their daily macros (calories, protein, carbs, fat) and weight, and build a custom library of ingredients and meals. 

The backend utilizes Flask-RESTful for routing, Flask-SQLAlchemy for database management, and Flask-JWT-Extended paired with Bcrypt for secure, encrypted user authentication. All resources are strictly protected so users can only access and modify their own personal data. 

## Installation Instructions

1. Clone the repository to your local machine.
2. Navigate into the project directory:
   ```bash
   cd summative_lab_course_10
   ```
3. Install the required dependencies using Pipenv:
   ```bash
   pipenv install
   ```
4. Enter the virtual environment:
   ```bash
   pipenv shell
   ```
5. Set up the database by running the migrations:
   ```bash
   cd server
   flask db upgrade
   ```
6. Seed the database with starter data:
   ```bash
   python seed.py
   ```

## Run Instructions

To start the Flask development server, make sure you are in the `server` directory and run:

```bash
python app.py
```
*The server will run on `http://127.0.0.1:5555`.*

## Testing

This API includes an automated test suite built with `pytest` to ensure route protection and data integrity. To run the tests, navigate to the `server` directory and run:

```bash
pytest
```

## API Endpoints

All resource endpoints (`/logs`, `/ingredients`, and `/meals`) require a valid JWT Access Token in the `Authorization` header (`Bearer <token>`).

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup` | Registers a new user and returns a JWT access token. |
| POST | `/login` | Authenticates a user and returns a JWT access token. |
| GET | `/check_session` | Returns the currently logged-in user based on the provided JWT. |
| DELETE | `/logout` | Returns a successful logout message. |

### Daily Logs (Protected)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/logs` | Returns a paginated list of the user's daily logs. Accepts `?page=` and `?per_page=`. |
| POST | `/logs` | Creates a new daily log. |
| PATCH | `/logs/<int:id>` | Updates an existing daily log. |
| DELETE | `/logs/<int:id>` | Deletes a daily log. |

### Ingredients (Protected)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ingredients` | Returns a paginated list of the user's saved ingredients. Accepts `?page=` and `?per_page=`. |
| POST | `/ingredients` | Creates a new custom ingredient. |
| PATCH | `/ingredients/<int:id>` | Updates an existing custom ingredient. |
| DELETE | `/ingredients/<int:id>`| Deletes a custom ingredient. |

### Meals (Protected)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/meals` | Returns a paginated list of the user's saved meals. Accepts `?page=` and `?per_page=`. |
| GET | `/meals/<int:id>` | Returns a specific meal by ID, including dynamic macro totals. |
| POST | `/meals` | Creates a new custom meal. |
| PATCH | `/meals/<int:id>` | Updates an existing meal's name. |
| DELETE | `/meals/<int:id>`| Deletes a custom meal. |
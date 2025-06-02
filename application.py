from flask import Flask, request, send_from_directory, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

# Handle different environments for frontend folder
if os.path.exists('../RatingsWebsiteFrontend'):
    frontend_folder = '../RatingsWebsiteFrontend'
elif os.path.exists('./frontend'):
    frontend_folder = './frontend' 
elif os.path.exists('./static'):
    frontend_folder = './static'
else:
    frontend_folder = './templates'  # fallback

app = Flask(__name__, static_folder=frontend_folder, static_url_path='')

# Use environment variables for production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///data.db')
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'your_secret_key')

# Additional configuration for production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login_page'
login_manager.login_message = 'Please log in to access this page.'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    drinks = db.relationship('Drink', back_populates='user')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET'])
def register_page():
    print(f"REGISTER_PAGE: Static folder: {app.static_folder}")
    print(f"REGISTER_PAGE: Static folder exists: {os.path.exists(app.static_folder) if app.static_folder else 'No static folder set'}")
    try:
        return app.send_static_file('register.html')
    except Exception as e:
        print(f"REGISTER_PAGE ERROR: {e}")
        return f"Error loading register page: {e}", 500

@app.route('/register', methods=['POST'])
def register():
    print("REGISTER POST: Received registration request")
    
    data = request.get_json(silent=True)
    
    if not data:
        print("REGISTER POST: No JSON data received")
        return {'message': 'Invalid request - No JSON data'}, 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        print("REGISTER POST: Missing username or password")
        return {'message': 'Username and password required'}, 400
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"REGISTER POST: Username {username} already exists")
        return {'message': 'Username already exists'}, 400
    
    try:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print(f"REGISTER POST: User {username} registered successfully")
        return {'message': 'User registered successfully'}, 201
    except Exception as e:
        print(f"REGISTER POST ERROR: {e}")
        db.session.rollback()
        return {'message': 'Registration failed'}, 500

@app.route('/login', methods=['GET'])
def login_page():
    print(f"LOGIN_PAGE: User authenticated: {current_user.is_authenticated}")
    print(f"LOGIN_PAGE: Static folder: {app.static_folder}")
    print(f"LOGIN_PAGE: Static folder exists: {os.path.exists(app.static_folder) if app.static_folder else 'No static folder set'}")
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    try:
        return app.send_static_file('login.html')
    except Exception as e:
        print(f"LOGIN_PAGE ERROR: {e}")
        return f"Error loading login page: {e}", 500

@app.route('/login', methods=['POST'])
def login():
    print("LOGIN POST: Received login request")

    data = request.get_json(silent=True)

    if not data:
        print("LOGIN POST: No JSON data received")
        return {'message': 'Invalid request - No JSON data'}, 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        print("LOGIN POST: Missing username or password")
        return {'message': 'Username and password required'}, 400

    print(f"LOGIN POST: Username: {username}")

    try:
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            print(f"LOGIN POST: User {user.username} logged in successfully")
            return {'message': 'Login successful', 'redirect': url_for('index')}, 200

        print("LOGIN POST: Invalid credentials")
        return {'message': 'Invalid credentials'}, 401
    except Exception as e:
        print(f"LOGIN POST ERROR: {e}")
        return {'message': 'Login failed'}, 500

@app.route('/logout', methods=['GET'])
@login_required
def logout_get():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/logout', methods=['POST'])
def logout_post():
    logout_user()
    session.clear()
    return {'message': 'Logged out successfully'}, 200

@app.route('/')
def index():
    print(f"INDEX: User authenticated: {current_user.is_authenticated}")
    print(f"INDEX: Static folder: {app.static_folder}")
    print(f"INDEX: Static folder exists: {os.path.exists(app.static_folder) if app.static_folder else 'No static folder set'}")
    
    if current_user.is_authenticated:
        try:
            return app.send_static_file('index.html')
        except Exception as e:
            print(f"INDEX ERROR serving index.html: {e}")
            return f"Error loading main page: {e}", 500
    else:
        print("INDEX: Redirecting to register")
        return redirect(url_for('register_page'))

@app.route('/drinks')
@login_required
def get_drinks():
    try:
        drinks = Drink.query.filter_by(user_id=current_user.id).all()
        output = []
        for drink in drinks:
            drink_data = {
                'id': drink.id,
                'name': drink.name,
                'price': drink.price,
                'rating': drink.rating,
                'description': drink.description
            }
            output.append(drink_data)
        return {'drinks': output}
    except Exception as e:
        print(f"GET_DRINKS ERROR: {e}")
        return {'message': 'Error fetching drinks'}, 500

@app.route('/drinks/<int:id>')
@login_required
def get_drink(id):
    try:
        drink = Drink.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        return{
            'name': drink.name,
            'price': drink.price,
            'rating': drink.rating,
            'description': drink.description
        }
    except Exception as e:
        print(f"GET_DRINK ERROR: {e}")
        return {'message': 'Error fetching drink'}, 500

@app.route('/drinks', methods=['POST'])
@login_required
def add_drink():
    try:
        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400
            
        drink = Drink(
            name=data.get('name'),
            price=data.get('price'),
            rating=data.get('rating'),
            description=data.get('description'),
            user_id=current_user.id
        )
        db.session.add(drink)
        db.session.commit()
        return {'id': drink.id, 'message': 'Drink added successfully'}, 201
    except Exception as e:
        print(f"ADD_DRINK ERROR: {e}")
        db.session.rollback()
        return {'message': 'Error adding drink'}, 500

@app.route('/drinks/<int:id>', methods=['DELETE'])
@login_required
def delete_drink(id):
    try:
        drink = Drink.query.filter_by(id=id, user_id=current_user.id).first()
        if drink is None:
            return {'message': 'Drink not found'}, 404
        db.session.delete(drink)
        db.session.commit()
        return {'message': 'Drink deleted successfully'}, 200
    except Exception as e:
        print(f"DELETE_DRINK ERROR: {e}")
        db.session.rollback()
        return {'message': 'Error deleting drink'}, 500

@app.route('/drinks/<int:id>', methods=['PUT'])
@login_required
def update_drink(id):
    try:
        drink = Drink.query.filter_by(id=id, user_id=current_user.id).first()
        if not drink:
            return {'message': 'Drink not found'}, 404
            
        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400
            
        drink.name = data.get('name', drink.name)
        drink.price = data.get('price', drink.price)
        drink.rating = data.get('rating', drink.rating)
        drink.description = data.get('description', drink.description)
        db.session.commit()
        return {'message': 'Drink updated successfully'}, 200
    except Exception as e:
        print(f"UPDATE_DRINK ERROR: {e}")
        db.session.rollback()
        return {'message': 'Error updating drink'}, 500

class Drink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='drinks')

    def __repr__(self):
        return f"{self.name} - {self.price} - {self.rating} - {self.description}"

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created!")
        except Exception as e:
            print(f"Database creation error: {e}")
    
    print(f"Frontend folder: {frontend_folder}")
    if os.path.exists(frontend_folder):
        print(f"Frontend folder found: {os.path.abspath(frontend_folder)}")
        print(f"Contents: {os.listdir(frontend_folder) if os.path.isdir(frontend_folder) else 'Not a directory'}")
    else:
        print(f"WARNING: Frontend folder not found: {os.path.abspath(frontend_folder)}")
        print("Please adjust your file structure or the 'frontend_folder' variable")
    
    # List current directory contents for debugging
    print(f"Current directory: {os.getcwd()}")
    print(f"Current directory contents: {os.listdir('.')}")
    
    app.run(debug=os.environ.get('FLASK_ENV') != 'production')
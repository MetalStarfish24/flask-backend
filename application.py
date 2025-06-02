from flask import Flask, request, send_from_directory, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

frontend_folder = '../RatingsWebsiteFrontend'
app = Flask(__name__, static_folder=frontend_folder, static_url_path='')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config["SECRET_KEY"] = 'your_secret_key'
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
    return app.send_static_file('register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return {'message': 'Username already exists'}, 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return {'message': 'User registered successfully'}, 201

@app.route('/login', methods=['GET'])
def login_page():
    print(f"LOGIN_PAGE: User authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return app.send_static_file('login.html')

@app.route('/login', methods=['POST'])
def login():
    print("LOGIN POST: Received login request")
    data = request.get_json()
    print(f"LOGIN POST: Username: {data.get('username')}")
    
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        login_user(user)
        print(f"LOGIN POST: User {user.username} logged in successfully")
        return {'message': 'Login successful', 'redirect': url_for('index')}, 200
    
    print("LOGIN POST: Invalid credentials")
    return {'message': 'Invalid credentials'}, 401

@app.route('/logout', methods=['GET'])
@login_required
def logout_get():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/logout', methods=['POST'])
def logout_post():
    session.clear()
    return '', 200

@app.route('/')
def index():
    print(f"INDEX: User authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        return app.send_static_file('index.html')
    else:
        print("INDEX: Redirecting to register")
        return redirect(url_for('register_page'))

@app.route('/drinks')
@login_required
def get_drinks():
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

@app.route('/drinks/<int:id>')
@login_required
def get_drink(id):
    drink = Drink.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return{
        'name': drink.name,
        'price': drink.price,
        'rating': drink.rating,
        'description': drink.description
    }

@app.route('/drinks', methods=['POST'])
@login_required
def add_drink():
    drink = Drink(
        name=request.json['name'],
        price=request.json['price'],
        rating=request.json['rating'],
        description=request.json['description'],
        user_id=current_user.id  # assign logged-in user's ID here!
    )
    db.session.add(drink)
    db.session.commit()
    return {'id': drink.id, 'message': 'Drink added successfully'}, 201

@app.route('/drinks/<int:id>', methods=['DELETE'])
@login_required
def delete_drink(id):
    drink = Drink.query.filter_by(id=id, user_id=current_user.id).first()
    if drink is None:
        return {'message': 'Drink not found'}, 404
    db.session.delete(drink)
    db.session.commit()
    return {'message': 'Drink deleted successfully'}, 200

@app.route('/drinks/<int:id>', methods=['PUT'])
@login_required
def update_drink(id):
    drink = Drink.query.get_or_404(id)
    drink.name = request.json.get('name', drink.name)
    drink.price = request.json.get('price', drink.price)
    drink.rating = request.json.get('rating', drink.rating)
    drink.description = request.json.get('description', drink.description)
    db.session.commit()
    return {'message': 'Drink updated successfully'}, 200

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created!")
    
    if os.path.exists(frontend_folder):
        print(f"Frontend folder found: {os.path.abspath(frontend_folder)}")
    else:
        print(f"WARNING: Frontend folder not found: {os.path.abspath(frontend_folder)}")
        print("Please adjust the 'frontend_folder' variable in the code")
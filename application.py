from flask import Flask, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)

class Drink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120))

    def __repr__(self):
        return f"{self.name} - {self.price} - {self.rating} - {self.description}"

@app.route('/frontend')
def frontend():
    return send_from_directory('.', 'Drink Rating Frontend Client.html')

@app.route('/')
def index():
    return 'Hello! Have you tried any new drinks today?'

@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()
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
def get_drink(id):
    drink = Drink.query.get_or_404(id)
    return{
        'name': drink.name,
        'price': drink.price,
        'rating': drink.rating,
        'description': drink.description
    }

@app.route('/drinks', methods=['POST'])
def add_drink():
    drink = Drink(name=request.json['name'], price=request.json['price'], rating=request.json['rating'], description=request.json['description'])
    db.session.add(drink)
    db.session.commit()
    return {'id': drink.id, 'message': 'Drink added successfully'}, 201

@app.route('/drinks/<int:id>', methods=['DELETE'])
def delete_drink(id):
    drink = Drink.query.get(id)
    if drink is None:
        return {'message': 'Drink not found'}, 404
    db.session.delete(drink)
    db.session.commit()
    return {'message': 'Drink deleted successfully'}, 200

@app.route('/drinks/<int:id>', methods=['PUT'])
def update_drink(id):
    drink = Drink.query.get_or_404(id)
    drink.name = request.json.get('name', drink.name)
    drink.price = request.json.get('price', drink.price)
    drink.rating = request.json.get('rating', drink.rating)
    drink.description = request.json.get('description', drink.description)
    db.session.commit()
    return {'message': 'Drink updated successfully'}, 200
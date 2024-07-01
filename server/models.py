from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(app, metadata=metadata)


class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)

    # Relationship with RestaurantPizza
    pizzas = db.relationship('RestaurantPizza', back_populates='restaurant', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'restaurant_pizzas': [
                {
                    'id': rp.id,
                    'price': rp.price,
                    'restaurant_id': rp.restaurant_id,
                    'pizza_id': rp.pizza_id,
                    'pizza': {
                        'id': rp.pizza.id,
                        'name': rp.pizza.name,
                        'ingredients': rp.pizza.ingredients
                    }
                } for rp in self.pizzas
            ]
        }

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ingredients = db.Column(db.String)

    # Relationship with RestaurantPizza
    restaurants = db.relationship('RestaurantPizza', back_populates='pizza', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': self.ingredients,
            'restaurants': [
                {
                    'id': rp.id,
                    'price': rp.price,
                    'restaurant_id': rp.restaurant_id,
                    'pizza_id': rp.pizza_id,
                    'restaurant': {
                        'id': rp.restaurant.id,
                        'name': rp.restaurant.name,
                        'address': rp.restaurant.address
                    }
                } for rp in self.restaurants
            ]
        }

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"


class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id'), nullable=False)

    # Relationships
    restaurant = db.relationship('Restaurant', back_populates='pizzas')
    pizza = db.relationship('Pizza', back_populates='restaurants')

    def to_dict(self):
        return {
            'id': self.id,
            'price': self.price,
            'restaurant_id': self.restaurant_id,
            'pizza_id': self.pizza_id,
            'restaurant': {
                'id': self.restaurant.id,
                'name': self.restaurant.name,
                'address': self.restaurant.address
            },
            'pizza': {
                'id': self.pizza.id,
                'name': self.pizza.name,
                'ingredients': self.pizza.ingredients
            }
        }

    @validates('price')
    def validate_price(self, key, value):
        if value < 0:
            raise ValueError("Price must be a positive integer")
        return value

    def __repr__(self):
        return f"<RestaurantPizza ${self.price}>"

# Create the database tables
with app.app_context():
    db.create_all()

# Routes for Restaurant
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict() for restaurant in restaurants])

@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant is None:
        return jsonify({'error': 'Restaurant not found'}), 404

    return jsonify(restaurant.to_dict())

@app.route('/restaurants', methods=['POST'])
def add_restaurant():
    data = request.get_json()
    new_restaurant = Restaurant(name=data['name'], address=data['address'])
    db.session.add(new_restaurant)
    db.session.commit()
    return jsonify(new_restaurant.to_dict()), 201

@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant is None:
        return jsonify({'error': 'Restaurant not found'}), 404
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

# Routes for Pizza
@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([pizza.to_dict() for pizza in pizzas])

@app.route('/pizzas/<int:id>', methods=['GET'])
def get_pizza(id):
    pizza = Pizza.query.get(id)
    if pizza is None:
        return jsonify({'error': 'Pizza not found'}), 404

    return jsonify(pizza.to_dict())

@app.route('/pizzas', methods=['POST'])
def add_pizza():
    data = request.get_json()
    new_pizza = Pizza(name=data['name'], ingredients=data['ingredients'])
    db.session.add(new_pizza)
    db.session.commit()
    return jsonify(new_pizza.to_dict()), 201

@app.route('/pizzas/<int:id>', methods=['DELETE'])
def delete_pizza(id):
    pizza = Pizza.query.get(id)
    if pizza is None:
        return jsonify({'error': 'Pizza not found'}), 404
    db.session.delete(pizza)
    db.session.commit()
    return '', 204

# Routes for RestaurantPizza
@app.route('/restaurant_pizzas', methods=['POST'])
def add_restaurant_pizza():
    data = request.get_json()
    # Check if the restaurant and pizza exist
    restaurant = Restaurant.query.get(data['restaurant_id'])
    pizza = Pizza.query.get(data['pizza_id'])
    if restaurant is None or pizza is None:
        return jsonify({'error': 'Restaurant or Pizza not found'}), 404

    try:
        new_restaurant_pizza = RestaurantPizza(price=data['price'], restaurant_id=data['restaurant_id'], pizza_id=data['pizza_id'])
        db.session.add(new_restaurant_pizza)
        db.session.commit()
        return jsonify(new_restaurant_pizza.to_dict()), 201
    except ValueError as e:
        return jsonify({'errors': [str(e)]}), 400

@app.route('/restaurant_pizzas/<int:id>', methods=['DELETE'])
def delete_restaurant_pizza(id):
    restaurant_pizza = RestaurantPizza.query.get(id)
    if restaurant_pizza is None:
        return jsonify({'error': 'RestaurantPizza not found'}), 404
    db.session.delete(restaurant_pizza)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)

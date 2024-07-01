#!/usr/bin/env python3
import os
from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from flask_restful import Api
from models import db, Restaurant, RestaurantPizza, Pizza

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db, render_as_batch=True)
db.init_app(app)

api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route("/restaurants", methods=["GET", "POST"])
def handle_restaurants():
    if request.method == "GET":
        restaurants = Restaurant.query.all()
        restaurants_list = [restaurant.to_dict() for restaurant in restaurants]
        return make_response(jsonify(restaurants_list), 200)
    elif request.method == "POST":
        new_restaurant = Restaurant(
            name=request.json.get("name"),
            address=request.json.get("address")
        )
        db.session.add(new_restaurant)
        db.session.commit()
        return make_response(jsonify(new_restaurant.to_dict()), 201)

@app.route("/restaurants/<int:id>", methods=["GET", "PATCH", "DELETE"])
def handle_restaurant_by_id(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return make_response(jsonify({"error": "Restaurant not found"}), 404)
    if request.method == "GET":
        return make_response(jsonify(restaurant.to_dict()), 200)
    elif request.method == "PATCH":
        for attr, value in request.json.items():
            setattr(restaurant, attr, value)
        db.session.commit()
        return make_response(jsonify(restaurant.to_dict()), 200)
    elif request.method == "DELETE":
        db.session.delete(restaurant)
        db.session.commit()
        return make_response({}, 204)

@app.route("/pizzas", methods=["GET", "POST"])
def handle_pizzas():
    if request.method == "GET":
        pizzas = Pizza.query.all()
        pizzas_list = [pizza.to_dict(rules=("-restaurant_pizzas",)) for pizza in pizzas]
        return make_response(jsonify(pizzas_list), 200)
    elif request.method == "POST":
        new_pizza = Pizza(
            name=request.json.get("name"),
            ingredients=request.json.get("ingredients")
        )
        db.session.add(new_pizza)
        db.session.commit()
        return make_response(jsonify(new_pizza.to_dict()), 201)

@app.route("/restaurant_pizzas", methods=["GET", "POST"])
def handle_restaurant_pizzas():
    if request.method == "GET":
        restaurant_pizzas = RestaurantPizza.query.all()
        restaurant_pizzas_list = [restaurant_pizza.to_dict() for restaurant_pizza in restaurant_pizzas]
        return make_response(jsonify(restaurant_pizzas_list), 200)
    elif request.method == "POST":
        try:
            price = request.json.get("price")
            if not (1 <= price <= 30):
                raise ValueError("Price must be between 1 and 30")
            new_restaurant_pizza = RestaurantPizza(
                price=price,
                restaurant_id=request.json.get("restaurant_id"),
                pizza_id=request.json.get("pizza_id")
            )
            db.session.add(new_restaurant_pizza)
            db.session.commit()
            return make_response(jsonify(new_restaurant_pizza.to_dict()), 201)
        except ValueError as e:
            return make_response(jsonify({"errors": [str(e)]}), 400)

@app.route("/pizzas/<int:id>", methods=["GET", "PATCH", "DELETE"])
def handle_pizza_by_id(id):
    pizza = Pizza.query.get(id)
    if not pizza:
        return make_response(jsonify({"error": f"Pizza {id} not found."}), 404)
    if request.method == "GET":
        return make_response(jsonify(pizza.to_dict()), 200)
    elif request.method == "PATCH":
        for attr, value in request.json.items():
            setattr(pizza, attr, value)
        db.session.commit()
        return make_response(jsonify(pizza.to_dict()), 200)
    elif request.method == "DELETE":
        db.session.delete(pizza)
        db.session.commit()
        return make_response({}, 204)

if __name__ == "__main__":
    app.run(port=5555, debug=True)

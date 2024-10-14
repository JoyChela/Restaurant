#!/usr/bin/env python3

from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)


@app.route('/')
def index():
    return '<h1>Code challenge</h1>'

@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    # Fetch all restaurants from the database
    restaurants = Restaurant.query.all()
    

    restaurants_list = [restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants]

    return jsonify(restaurants_list)

@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    # Fetch the restaurant by id
    restaurant = Restaurant.query.get(id)
    
    if restaurant is None:
        return jsonify({"error": "Restaurant not found"}), 404
    
    # Serialize restaurant data along with restaurant pizzas
    restaurant_data = restaurant.to_dict(only=("id", "name", "address"))
    
    # Add restaurant_pizzas with nested pizza details
    restaurant_data['restaurant_pizzas'] = [
        {
            'id': rp.id,
            'pizza_id': rp.pizza_id,
            'price': rp.price,
            'restaurant_id': rp.restaurant_id,
            'pizza': rp.pizza.to_dict(only=("id", "name", "ingredients"))
        }
        for rp in restaurant.restaurant_pizzas
    ]
    
    # Return the data as JSON
    return jsonify(restaurant_data)

@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    
    restaurant = Restaurant.query.get(id)
    
    if restaurant:
        restaurant_pizzas = RestaurantPizza.query.filter_by(restaurant_id=id).all()
        for rp in restaurant_pizzas:
            db.session.delete(rp)
        
        # Delete the restaurant
        db.session.delete(restaurant)
        db.session.commit()
        
        return '', 204
    else:
        return jsonify({"error": "Restaurant not found"}), 404

@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    
    # Serialize pizza data 
    pizzas_data = [pizza.to_dict(only=("id", "name", "ingredients")) for pizza in pizzas]
    
    return jsonify(pizzas_data)

@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()

    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')
    
    # Validate price range between 1 and 30
    if price is None or not (1 <= price <= 30):
        return jsonify({"errors": ["validation errors"]}), 400

    # Ensure the pizza and restaurant exist
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)

    if not pizza or not restaurant:
        return jsonify({"errors": ["Pizza or Restaurant not found"]}), 404
    
    # Create the new RestaurantPizza entry
    new_restaurant_pizza = RestaurantPizza(
        price=price,
        pizza_id=pizza_id,
        restaurant_id=restaurant_id
    )
    
    # Add the new entry 
    db.session.add(new_restaurant_pizza)
    db.session.commit()
    
    response_data = {
        "id": new_restaurant_pizza.id,
        "price": new_restaurant_pizza.price,
        "pizza_id": new_restaurant_pizza.pizza_id,
        "restaurant_id": new_restaurant_pizza.restaurant_id,
        "pizza": {
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients
        },
        "restaurant": {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address
        }
    }
    
    return jsonify(response_data), 201

if __name__ == '__main__':
    app.run(port=5555, debug=True)

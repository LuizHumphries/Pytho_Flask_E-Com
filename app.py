from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import login_user, login_required, logout_user, current_user
from repository.database import db
from models.product import Product
from models.user import User
from models.cartitem import CartItem
from login.login_manager import login_manager

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
app.config["SECRET_KEY"] = "secret_key"

login_manager.init_app(app)
login_manager.login_view = "login"
db.init_app(app)
CORS(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get("username")).first()
    if user and data.get("password") == user.password:
        login_user(user)
        return jsonify({"message": "Logged in successfully"}), 200        
    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200    

@app.route("/api/products/add", methods=["POST"])
@login_required
def add_product():
    data = request.json
    if "name" in data and "price" in data:
        product = Product(name=data["name"], price=data["price"], description=data.get("description",""))
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product added successfully"}), 200
    return jsonify({"message": "Failed to add the product"}), 400
        
@app.route("/api/products/delete/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"}), 200
    return jsonify({"message": "Not Found. Product not available"}), 404

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product_detail(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product_id,
            "name": product.name,
            "price": product.price,
            "description": product.description
        }), 200
    return jsonify({"message": "Not Found. Product not available"}), 404

@app.route("/api/products/update/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    data = request.json
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Not Found. Product not available"}), 404
    
    if product:
        product.name = data.get("name", product.name)
        product.price = data.get("price", product.price)
        product.description = data.get("description", product.price)
        db.session.commit()
        return jsonify({"message": "Product updated successfully"}), 200
    
@app.route("/api/products", methods=["GET"])
def get_all_products():
    products = Product.query.all()
    if products:
        products_data = [product.to_dict() for product in products]
        return jsonify(products_data), 200 
    return jsonify({"message": "Not Found. No products available."}), 404 

@app.route("/api/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_product_to_cart(product_id):
    product = Product.query.get(product_id)
    user = User.query.get(int(current_user.id))
    if product and user:
        cart_item = CartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({"message": "Item added to the cart successfully"}), 200
    return jsonify({"message": "Failed to add item to the cart"}), 400    

@app.route("/api/cart/delete/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product_from_cart(product_id):
    product = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Item deleted from the cart successfully"}), 200
    return jsonify({"message": "Failed to remove item from the cart"}), 400  

@app.route("/api/cart", methods=["GET"])
@login_required
def view_cart():
    user = User.query.get(current_user.id)
    cart_items = user.cart
    cart_content = [cart_item.to_dict() for cart_item in cart_items]
    return jsonify(cart_content), 200

@app.route("/api/cart/checkout", methods=["POST"])
@login_required
def checkout_cart():
    user = User.query.get(current_user.id)
    cart_items = user.cart
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"message": "Checkout successful. Cart has been cleared."}), 200
    

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import db, User, Product, Order, OrderItem
from mongo import logs as mongo_logs
from datetime import datetime
import bcrypt
import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../templates")
)

CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Aravind%402004@mysql/inventory"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "Server Running"})


# ================= AUTH =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user = User(
        name=name,
        email=email,
        password=hashed.decode("utf-8")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name
    })


# ================= USERS =================
@app.route("/users", methods=["GET"])
def get_users():
    page = int(request.args.get("page", 1))
    per_page = 5
    users = User.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify([
        {"id": u.id, "name": u.name, "email": u.email}
        for u in users.items
    ])

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    user = User(
        name=data["name"],
        email=data["email"],
        password="temporary"  # for admin-created users
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created"})


# ================= PRODUCTS =================
@app.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([
        {"id": p.id, "name": p.name, "price": p.price, "stock": p.stock}
        for p in products
    ])

@app.route("/products", methods=["POST"])
def add_product():
    data = request.json
    product = Product(
        name=data["name"],
        price=float(data["price"]),
        stock=int(data["stock"])
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "Product added"})


# ================= ORDERS =================
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    user_id = data.get("user_id")
    items = data.get("items")

    if not user_id or not items:
        return jsonify({"error": "Invalid data"}), 400

    total = 0
    order = Order(user_id=user_id, total_amount=0)
    db.session.add(order)
    db.session.commit()

    for item in items:
        product = Product.query.get(item["product_id"])
        if not product or product.stock < item["quantity"]:
            return jsonify({"error": "Stock issue"}), 400

        product.stock -= item["quantity"]
        total += product.price * item["quantity"]

        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"]
        )
        db.session.add(order_item)

    order.total_amount = total
    db.session.commit()

    mongo_logs.insert_one({
        "order_id": order.id,
        "user_id": user_id,
        "total": total,
        "created_at": datetime.utcnow()
    })

    return jsonify({"order_id": order.id})


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Not found"}), 404

    user = User.query.get(order.user_id)
    items = OrderItem.query.filter_by(order_id=order.id).all()

    return jsonify({
        "order_id": order.id,
        "user": user.name,
        "total": order.total_amount,
        "items": [
            {"product_id": i.product_id, "quantity": i.quantity}
            for i in items
        ]
    })


# ================= LOGS =================
@app.route("/logs", methods=["GET"])
def get_logs():
    logs = list(mongo_logs.find({}, {"_id": 0}))
    for log in logs:
        if isinstance(log.get("created_at"), datetime):
            log["created_at"] = log["created_at"].isoformat()
    return jsonify(logs)


# ================= INIT =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
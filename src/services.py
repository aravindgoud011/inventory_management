from models import db, Product
from mongo import db_mongo
from bson import ObjectId

# ===============================
# MYSQL SERVICE
# ===============================

class MySQLService:

    @staticmethod
    def add_product(data):
        product = Product(
            name=data["name"],
            price=float(data["price"]),
            stock=int(data["stock"])
        )
        db.session.add(product)
        db.session.commit()
        return {"message": "Product added in MySQL"}

    @staticmethod
    def get_products():
        products = Product.query.all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock": p.stock
            }
            for p in products
        ]

    @staticmethod
    def delete_product(product_id):
        product = Product.query.get(product_id)
        if not product:
            return {"error": "Product not found"}, 404

        db.session.delete(product)
        db.session.commit()
        return {"message": "Deleted from MySQL"}


# ===============================
# MONGODB SERVICE
# ===============================

class MongoService:

    @staticmethod
    def add_product(data):
        db_mongo.products.insert_one({
            "name": data["name"],
            "price": float(data["price"]),
            "stock": int(data["stock"])
        })
        return {"message": "Product added in MongoDB"}

    @staticmethod
    def get_products():
        products = db_mongo.products.find()
        return [
            {
                "id": str(p["_id"]),
                "name": p["name"],
                "price": p["price"],
                "stock": p["stock"]
            }
            for p in products
        ]

    @staticmethod
    def delete_product(product_id):
        result = db_mongo.products.delete_one(
            {"_id": ObjectId(product_id)}
        )

        if result.deleted_count == 0:
            return {"error": "Product not found"}, 404

        return {"message": "Deleted from MongoDB"}
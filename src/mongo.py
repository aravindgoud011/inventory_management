from pymongo import MongoClient
import os

client = MongoClient("mongodb://mongo:27017/")
db_mongo = client.inventory
logs = db_mongo.logs
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

class User:
    
    def __init__(self,uid) -> None:
        self.url = os.environ.get("MONGODB")
        self.dbname = "Bot"
        self.collname = "users"
        self.uid = uid
        self.messages = self.getMessages()
        self.limit = 5

    def set_limit(self,limit):
        with pymongo.MongoClient(self.url) as db:
            database = db[self.dbname]
            coll = database[self.collname]
            coll.update_one({'_id':self.uid},{"$set":{'limit':limit}})
            self.limit = limit

    def getMessages(self):
        with pymongo.MongoClient(self.url) as db:
            database = db[self.dbname]
            coll = database[self.collname]
            data = coll.find_one(self.uid)
            message = data['messages'] if data != None else self.createUser()
            try: self.limit = data['limit']
            except: self.limit = 5 ; coll.update_one({'_id':self.uid},{"$set":{"limit":self.limit}})
            return message

    def createUser(self):
        with pymongo.MongoClient(self.url) as db:
            database = db[self.dbname]
            coll = database[self.collname]
            coll.insert_one({'_id':self.uid,'messages':[]})
            return []

    def update(self):
        with pymongo.MongoClient(self.url) as db:
            database = db[self.dbname]
            coll = database[self.collname]
            coll.update_one({'_id':self.uid}, {"$set": {'messages':self.messages}})
    
    def append(self,data):
        self.messages.append(data)
        self.update()
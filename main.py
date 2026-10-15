import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, url_for
app=Flask(__name__)
uri = os.getenv("MONGO_URI")
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
## basic code end
db=client["Libraries"]

@app.route("/",methods=["GET","POST"])
def login():
    users = db["users"]
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.find_one({"username": username, "password": password})
        if user:
            lib_name = user.get("library_name")
            return redirect(url_for('test', lib_name=lib_name, username=username))
        else:
            return "Invalid credentials, try again."
    else:
        return render_template("login.html")

@app.route("/signup",methods=["GET","POST"])
def signup():
    users=db["users"]
    if request.method=="POST":
        username_input=request.form.get("username")
        password_input=request.form.get("password")
        user_data={
             "username":username_input,
             "password":password_input
        }
        users.insert_one(user_data)
        return redirect(url_for('create_library',username=username_input, password=password_input))
    else:
        return render_template("signup.html")

@app.route("/create_library", methods=["GET","POST"])
def create_library():
    users=db["users"]
    username_input =request.form.get("username")
    password_input =request.form.get("password")
    if request.method=="POST":
            lib_name=request.form.get("library_name")
            if not lib_name:
                 return render_template("create_library.html",username=username_input, password=password_input)
            join_code=request.form.get("join_code")
            user_collection=db[lib_name]
            library_data={
                "library_name":lib_name,
                "join_code":join_code
            }
            admin_data={
                 "username":username_input,
                 "password":password_input,
                 "library":lib_name,
                 "admin":True
            }
            user_collection.insert_one(library_data)
            user_collection.insert_one(admin_data)
            users.update_one(
             {"username": username_input},
             {"$set": {
                 "username": username_input,
                 "password": password_input,
                 "library": lib_name,
                 "admin": True,
                 "library_name": lib_name,
                 "join_code": join_code
             }},
             upsert=True)
            return redirect(url_for('test',lib_name=lib_name))
    else:
        return render_template("create_library.html",username=username_input, password=password_input)

@app.route("/join_library", methods=["GET","POST"])
def join_library():
    users=db["users"]     
    if request.method=="POST":
            username_input = request.form.get("username")
            password_input = request.form.get("password")
            join_code=request.form.get("join_code")
            if not join_code:
                 return render_template("join_library.html",username=username_input, password=password_input)
            user_collection=db[lib_name]
            library_data={
                "library_name":lib_name,
                "join_code":join_code
            }
            user_data={
                 "username":username_input,
                 "password":password_input,
                 "admin":False
            }
            user_collection.insert_one(library_data)
            user_collection.insert_one(user_data)
            users.insert_one(user_data)
            return redirect(url_for('test',lib_name=lib_name))
    return render_template("join_library.html")

@app.route("/library/<lib_name>/<username>", methods=["GET", "POST"])
def test(lib_name,username):
    library_collection = db[lib_name]
    if request.method == "POST":
        title = request.form.get("title")
        username = request.form.get("username","Unknown")
        author = request.form.get("author", "Unknown") # grab author if submitted
        if title:
            library_collection.insert_one({
                "title": title,
                "author": author,
                "currently_reading": "No",
                "checked_out_by": "None",
                "return_to":username
            })
        return redirect(url_for('test', lib_name=lib_name))
    books = list(library_collection.find({"title": {"$exists": True}}))
    return render_template("test.html", books=books, lib_name=lib_name)

@app.route("/library/<lib_name>/<username>/add_entry", methods=["GET", "POST"])
def add_entry(lib_name):
    library_collection = db[lib_name]
    if request.method == "POST":
        title=request.form.get("title")
        author=request.form.get("author")
        username=request.form.get("username")
        currently_reading=request.form.get("currently_reading", "No")
        checked_out_by=request.form.get("checked_out_by", "None")
        library_collection.insert_one({
            "title": title,
            "author": author,
            "currently_reading": currently_reading,
            "checked_out_by": checked_out_by,
            "return_to":username
        })
        return redirect(url_for('test', lib_name=lib_name))
    return render_template("add_entry.html", lib_name=lib_name)
@app.route("/library/<lib_name>/place_hold", methods=["GET", "POST"])
def place_hold(lib_name):
    library_collection = db[lib_name]
    return render_template("place_hold.html", lib_name=lib_name)




































if __name__=="__main__":
    app.run(debug=True)

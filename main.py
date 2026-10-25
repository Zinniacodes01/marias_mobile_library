import os
import re
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
uri = os.getenv("MONGO_URI")

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["Libraries"]

@app.route("/", methods=["GET", "POST"])
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

@app.route("/signup", methods=["GET", "POST"])
def signup():
    users = db["users"]
    if request.method == "POST":
        username_input = request.form.get("username")
        password_input = request.form.get("password")
        join_code = request.form.get("join_code")
        if join_code:
            lib_doc = db["libraries"].find_one({"join_code": join_code})
            if not lib_doc:
                return "invalid join code"
            lib_name = lib_doc["library_name"]
            users.insert_one({"username": username_input, "password": password_input, "library_name": lib_name, "admin": False})
            return redirect(url_for('test', lib_name=lib_name, username=username_input))
        users.insert_one({"username": username_input, "password": password_input})
        return redirect(url_for('create_library', username=username_input, password=password_input))
        
    return render_template("signup.html")

@app.route("/create_library", methods=["GET", "POST"])
def create_library():
    users = db["users"]
    username_input = request.form.get("username")
    password_input = request.form.get("password")
    
    if request.method == "POST":
        lib_name = request.form.get("library_name")
        if not lib_name:
             return render_template("create_library.html", username=username_input, password=password_input)
        join_code = request.form.get("join_code")
        user_collection = db[lib_name]
        db["libraries"].insert_one({
            "library_name": lib_name,
            "join_code": join_code
        })
        library_data = {
            "library_name": lib_name,
            "join_code": join_code
        }
        admin_data = {
             "username": username_input,
             "password": password_input,
             "library": lib_name,
             "admin": True
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
           upsert=True
        )
        return redirect(url_for('test', lib_name=lib_name, username=username_input))
    else:
        return render_template("create_library.html", username=username_input, password=password_input)

@app.route("/join_library", methods=["GET", "POST"])
def join_library():
    users = db["users"]       
    if request.method == "POST":
        username_input = request.form.get("username")
        password_input = request.form.get("password")
        join_code_input = request.form.get("join_code")
        if not join_code_input:
            return render_template("join_library.html", username=username_input, password=password_input)
        join_code = join_code_input.strip()
        lib_doc = db["libraries"].find_one({"join_code": {"$regex": f"^{join_code}$", "$options": "i"}})
        if not lib_doc:
            return "Invalid Join Code! Go back and try again."    
        lib_name = lib_doc["library_name"]
        user_collection = db[lib_name]
        user_data = {
             "username": username_input,
             "password": password_input,
             "admin": False,
             "library_name": lib_name
        }
        user_collection.insert_one(user_data)
        users.update_one(
            {"username": username_input},
            {"$set": user_data},
            upsert=True
        )
        return redirect(url_for('test', lib_name=lib_name, username=username_input))
    return render_template("join_library.html")

@app.route("/library/<lib_name>/<username>", methods=["GET", "POST"])
def test(lib_name, username):
    library_collection = db[lib_name]
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author", "Unknown")
        if title:
            library_collection.insert_one({
                "title": title,
                "author": author,
                "currently_reading": "No",
                "checked_out_by": "None",
                "on_hold_by": "None",
                "return_to": username,
                "due_date": None
            })
        return redirect(url_for('test', lib_name=lib_name, username=username))
    
    books_cursor = library_collection.find({"title": {"$exists": True}})
    books = []
    now = datetime.now()

    for book in books_cursor:
        holds = book.get("on_hold_by")
        if not holds or holds == "None":
            book["on_hold_by"] = "None"

        due_date_str = book.get("due_date")
        late_fee = 0
        if due_date_str:
            try:
                due_date = datetime.strptime(str(due_date_str), "%Y-%m-%d")
                if now > due_date:
                    days_late = (now - due_date).days
                    late_fee = (days_late // 2) * 1
            except ValueError:
                pass
        book["calculated_late_fee"] = late_fee
        books.append(book)

    return render_template("test.html", books=books, lib_name=lib_name, username=username)

@app.route("/library/<lib_name>/<username>/add_entry", methods=["GET", "POST"])
def add_entry(lib_name, username):
    library_collection = db[lib_name]
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        currently_reading = request.form.get("currently_reading", "No")
        checked_out_by = request.form.get("checked_out_by", "None")
        due_date = request.form.get("due_date", None)
        library_collection.insert_one({
            "title": title,
            "author": author,
            "currently_reading": currently_reading,
            "checked_out_by": checked_out_by,
            "on_hold_by": "None",
            "return_to": username,
            "due_date": due_date
        })
        return redirect(url_for('test', lib_name=lib_name, username=username))
    return render_template("add_entry.html", lib_name=lib_name, username=username)

@app.route("/library/<lib_name>/<username>/place_hold", methods=["GET", "POST"])
def place_hold(lib_name, username):
    library_collection = db[lib_name]
    if request.method == "POST":
        book_id = request.form.get("book_id")
        title = request.form.get("title")
        
        book = None
        if book_id:
            try:
                book = library_collection.find_one({"_id": ObjectId(book_id)})
            except Exception:
                pass
        elif title:
            clean_title = title.strip()
            book = library_collection.find_one({"title": {"$regex": f"^{clean_title}$", "$options": "i"}})
            
        if book:
            current_holds = book.get("on_hold_by", "None")
            
            if not isinstance(current_holds, list):
                if current_holds and current_holds != "None":
                    holds_list = [current_holds, username]
                else:
                    holds_list = [username]
            else:
                holds_list = current_holds
                if username not in holds_list:
                    holds_list.append(username)
            
            library_collection.update_one(
                {"_id": book["_id"]},
                {"$set": {"on_hold_by": holds_list}}
            )
        return redirect(url_for('test', lib_name=lib_name, username=username))
        
    books = list(library_collection.find({"title": {"$exists": True}}))
    return render_template("place_hold.html", books=books, lib_name=lib_name, username=username)

@app.route("/library/<lib_name>/<username>/update_checkout/<book_id>", methods=["GET", "POST"])
def update_checkout(lib_name, username, book_id):
    library_collection = db[lib_name]
    if request.method == "POST":
        new_user = request.form.get("checked_out_by")
        if new_user:
            library_collection.update_one(
                {"_id": ObjectId(book_id)},
                {
                    "$set": {
                        "checked_out_by": new_user,
                        "currently_reading": "Yes" if new_user.lower() != "none" else "No",
                    }
                }
            )
        return redirect(url_for('test', lib_name=lib_name, username=username))
    book = library_collection.find_one({"_id": ObjectId(book_id)})
    return render_template("update_checkout.html", book=book, lib_name=lib_name, username=username)

@app.route("/library/<lib_name>/<username>/update_currently_reading/<book_id>", methods=["GET", "POST"])
def update_currently_reading(lib_name, username, book_id):
    library_collection = db[lib_name]
    if request.method == "POST":
        new_reader = request.form.get("currently_reading")
        if new_reader:
            library_collection.update_one(
                {"_id": ObjectId(book_id)},
                {"$set": {"currently_reading": new_reader}}
            )
        return redirect(url_for('test', lib_name=lib_name, username=username))
    book = library_collection.find_one({"_id": ObjectId(book_id)})
    return render_template("update_currently_reading.html", book=book, lib_name=lib_name, username=username)

@app.route("/library/<lib_name>/<username>/promote_hold/<book_id>", methods=["POST"])
def promote_hold(lib_name, username, book_id):
    library_collection = db[lib_name]
    book = library_collection.find_one({"_id": ObjectId(book_id)})
    
    if book and book.get("on_hold_by"):
        holds = book.get("on_hold_by")
        if isinstance(holds, list) and len(holds) > 0:
            next_borrower = holds[0]
            remaining_holds = holds[1:] if len(holds) > 1 else "None"
            library_collection.update_one(
                {"_id": ObjectId(book_id)},
                {
                    "$set": {
                        "checked_out_by": next_borrower,
                        "return_to": next_borrower,
                        "on_hold_by": remaining_holds
                    }
                }
            )
        elif isinstance(holds, str) and holds != "None":
            library_collection.update_one(
                {"_id": ObjectId(book_id)},
                {
                    "$set": {
                        "checked_out_by": holds,
                        "return_to": holds,
                        "on_hold_by": "None"
                    }
                }
            )
    return redirect(url_for('test', lib_name=lib_name, username=username))

if __name__ == "__main__":
    app.run(debug=True)

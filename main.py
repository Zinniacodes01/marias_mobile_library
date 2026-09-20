from pymongo import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, url_for
app=Flask(__name__)
uri = "mongodb+srv://awesomeanikale185_db_user:gdqJ0SjDDm9ZoHpJ@cluster0.3jl0dql.mongodb.net/?appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
## basic code end
db=client["Libraries"]
masschaos_collection=db.masschaos


@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        username_input=request.form.get("username")
        password_input=request.form.get("password")
        ####check if it matches the database
        return render_template("test.html")
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
        return render_template("test.html")
    return render_template("signup.html")

@app.route("/create_library", methods=["GET","POST"])
def create_library():
    users=db["users"]
    username_input = request.args.get("username") or request.form.get("username")
    password_input = request.args.get("password") or request.form.get("password")
    if request.method=="POST":
            lib_name=request.form.get("library_name")
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
                 {"username":username_input},
                 {"$set":library_data}
            )
            return redirect(url_for('test',lib_name=lib_name))
    return render_template("create_library.html",username=username_input, password=password_input)

@app.route("/join_library", methods=["GET","POST"])
def join_library():
    users=db["users"]
    if request.method=="POST":
            lib_name=request.form.get("library_name")
            join_code=request.form.get("join_code")
            username_input=request.form.get("username")
            password_input=request.form.get("password")
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

@app.route("/library/<lib_name>")
def test(lib_name):
    library_collection=db[lib_name]
    books=list(library_collection.find({"type":"book"}))
    return render_template("test.html", lib_name=lib_name, books=books)




































if __name__=="__main__":
    app.run(debug=True)

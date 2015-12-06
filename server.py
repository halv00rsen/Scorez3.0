#! python3
from flask import Flask, session, redirect, url_for, escape, request, render_template, flash, g
from contextlib import closing
from os import path
import sqlite3, hashlib, os

server_config = "Scorez3.0.server_config"

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "emqHJD4P&YJdC-#yHL.3dX9JxLJ6K(1WRH18x72uji,^w8.301!$+;07Tb0V<7%"
app.config["DATABASE"] = path.join("db", "database.db")

@app.route("/")
def index():
	if is_logged_in():
		return redirect(url_for("home"))
	return redirect(url_for("login"))

@app.route("/login", methods=["POST", "GET"])
def login():
	error = None
	if request.method == "POST":
		username, password = request.form["username"], request.form["password"]
		cur = g.db.execute("select password, admin from User where username = ?", [username]).fetchall()
		if len(cur) != 0 and cur[0][0] == hash_password(password):
			session["logged_in"] = True
			session["admin"] = cur[0][1] == 1
			session["username"] = username
			return redirect(url_for("home"))
		error = "Wrong username/password."
	return render_template("login.html", error=error)

# def requires_login(f):
# 	def is_logged_in(*args, **kwargs):
# 		if "logged_in" in session and session["logged_in"]:
# 			return f(*args, **kwargs)
# 		return "Du er ikke logget inn.", 403
# 	return is_logged_in

@app.route("/home")
# @requires_login
def home():
	if not is_logged_in():
		return redirect(url_for("login"))
	cur = g.db.execute("select name, type from Beer order by name asc")
	beers = [dict(name=row[0], type=row[1]) for row in cur.fetchall()]
	return render_template("home.html", beers=beers)

@app.route("/add_beer", methods=["GET", "POST"])
def add_new_beer():
	if not is_logged_in():
		return redirect(url_for("login"))
	if request.method == "POST":
		if request.form["submitButton"] == "Avbryt":
			return redirect(url_for("home"))
		error = None
		beer_name, beer_type = request.form["beer_name"], request.form["beer_type"]
		if not len(beer_name) or not len(beer_type) or len(g.db.execute("select 1 name, type from Beer where name = ? and type = ?", [beer_name, beer_type]).fetchall()):
			error = "Ølet {} finnes allerede i systemet.".format(beer_name) 
			return render_template("new_beer.html", error=error, beer_types=get_all_types())
		if not len(g.db.execute("select 1 name from Beer_type where name = ?", [beer_type]).fetchall()):
			error = "Typen {} finnes ikke i systemet.".format(beer_type)
			return render_template("new_beer.html", error=error, beer_types=get_all_types())
		g.db.execute("insert into Beer values (?,?)", [beer_name, beer_type])
		g.db.commit()
		return redirect(url_for("home"))
	return render_template("new_beer.html", beer_types=get_all_types())

@app.route("/delete_beer/<beer_name>,<beer_type>", methods=["GET", "POST"])
def delete_beer(beer_name, beer_type):
	if not is_logged_in():
		return redirect(url_for("login"))
	if is_admin():
		g.db.execute("delete from Beer where name = ? and type = ?", [beer_name, beer_type])
		g.db.commit()
		return "true"
	return "false"
	# return redirect(url_for("home"))


@app.route("/logout")
def logout():
	session.pop("logged_in", None)
	session.pop("admin", None)
	session.pop("username", None)
	return redirect(url_for("login"))


@app.route("/beer/<beer_name>,<beer_type>")
# @requires_login
def show_beer_page(beer_name, beer_type):
	if not is_logged_in():
		return redirect(url_for("login"))

	return render_template("beer_page.html", beer=get_beer_info(beer_name, beer_type))

@app.route("/user")
def user_page():
	if not is_logged_in():
		return redirect(url_for("login"))
	return render_template("user_page.html")

@app.route("/change_password", methods=["POST"])
def change_password():
	if not is_logged_in():
		return redirect(url_for("login"))
	js = request.get_json()
	oldPass, newPass = js["old_password"], js["new_password"]
	current_password = g.db.execute("select password from User where username = ?", [session["username"]]).fetchall()[0][0]
	if current_password != hash_password(oldPass):
		return "false"
	g.db.execute("update User set password = ? where username = ?", [hash_password(newPass), session["username"]])
	g.db.commit()	
	return "true"

@app.route("/types_admin")
def types_page_admin():
	if not is_logged_in():
		return redirect(url_for("login"))
	if is_admin():
		return render_template("types_page.html", types=get_all_types())
	return redirect(url_for("home"))

@app.route("/type_handler", methods=["POST", "GET"])
def type_handler():
	if not is_logged_in():
		return redirect(url_for("login"))
	if is_admin() and request.method == "POST":
		js = request.get_json()
		typ = js["type"]
		if len(typ) == 0:
			return "false"
		msg = "false"
		if js["action"] == "add":
			if len(g.db.execute("select * from Beer_type where name = ?", [typ]).fetchall()):
				# msg = "Typen {} finnes fra før.".format(typ)
				msg = "false"
			else:
				g.db.execute("insert into Beer_type values (?)",[typ])
				g.db.commit()
				# msg = "Typen {} ble lagt til.".format(typ)
				msg = "true"
		elif js["action"] == "delete":
			g.db.execute("delete from Beer_type where name = ?", [typ])
			g.db.commit()
			# msg = "Typen {} ble slettet.".format(typ)
			msg = typ
		return msg
	return redirect(url_for("home"))

@app.route("/user_admin")
def user_page_admin():
	if not is_logged_in():
		return redirect(url_for("login"))
	if is_admin():
		get_user_information()
		return render_template("admin.html", users=get_user_information())
	return redirect(url_for("home"))

@app.route("/create_user", methods=["POST", "GET"])
def create_user():
	if not is_logged_in():
		return redirect(url_for("login"))
	if is_admin() and request.method == "POST":
		js = request.get_json()
		username, password, admin = js["username"], js["password"], js["admin"]
		# username, password, admin = request.form["username"], request.form["password"], "admin" in request.form
		error = None
		if not len(g.db.execute("select 1 username from User where username = ?", [username]).fetchall()):
			g.db.execute("insert into User values (?,?,?)", [username, hash_password(password), admin])
			g.db.commit()
			# error = "Brukeren {} ble laget".format(username)
			error = "true"
		else:
			# error = "Brukernavnet {} finnes allerede.".format(username)
			error = "false"
		return error
		# return render_template("admin.html", error=error)
	return redirect(url_for("home"))

# @app.route("/get_user_info_admin")
def get_user_information():
	urs = [dict(username=row[0], admin=row[1]) for row in g.db.execute("select username, admin from User").fetchall()]
	# beers = [dict(name=row[0], type=row[1]) for row in cur.fetchall()]
	return urs

@app.route("/add_score", methods=["POST", "GET"])
def add_score():
	pass

def get_beer_info(beer_name, beer_type):
	scorez = g.db.execute("select user, p from Score where beer = ? and type = ?", [beer_name, beer_type]).fetchall()
	return {"beer_name": beer_name, "beer_type": beer_type}

def get_all_types():
	return [typ[0] for typ in g.db.execute("select * from Beer_type order by name asc").fetchall()]

def is_admin():
	return "admin" in session and session["admin"]

def is_logged_in(*args, **kwargs):
	if "logged_in" in session and session["logged_in"]:
		return True
	return False

def valid_login(username, password):
	return True, True

def hash_password(password):
	return hashlib.sha224(str(password).encode("ascii")).hexdigest()

def connect_db():
	return sqlite3.connect(app.config["DATABASE"])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, "db", None)
	if db is not None:
		db.close()

if __name__ == "__main__":
	# app.run(debug=False, host="0.0.0.0")
	app.run(debug=True)

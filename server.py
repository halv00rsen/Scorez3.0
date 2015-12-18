#! python3
from flask import Flask, session, redirect, url_for, escape, request, render_template, flash, g, jsonify
from contextlib import closing
from os import path
from functools import wraps
from users import Users
import sqlite3, hashlib, os, logging, datetime

# logging.basicConfig(filename=path.join("db", "scorez_log.log"), level=logging.DEBUG, format="%(asctime)s (%(levelname)s): %(message)s")
app = Flask(__name__)
app.config.from_pyfile("server_config.py")

# users = Users()

# app.config.from_pyfile("navn_på_fil")
# app.wsgi_app = ProxyFix(app.wsgi_app)

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
			# logging.debug(username + " logged in.")
			# logging.warning(username + " logged in.")
			return redirect(url_for("home"))
		error = "Wrong username/password."
	return render_template("login.html", error=error)

def requires_login(f):
	@wraps(f)
	def is_logged_in(*args, **kwargs):
		if "logged_in" in session and session["logged_in"]:
			# users.add_user_activity(session["username"])
			return f(*args, **kwargs)
		return "Du er ikke logget inn.", 403
	return is_logged_in

def requires_admin(f):
	@wraps(f)
	def is_admin(*args, **kwargs):
		if "admin" in session and session["admin"]:
			return f(*args, **kwargs)
		return "Du er ikke administrator", 403
	return is_admin

@app.route("/get_all_beers")
@requires_login
def get_all_beers():
	cur = g.db.execute("select name, type from Beer order by name asc")
	beers = [dict(name=row[0], type=row[1]) for row in cur.fetchall()]
	for beer in beers:
		cur = [a[0] for a in g.db.execute("select p from Score where beer = ? and type = ?", [beer["name"], beer["type"]]).fetchall()]
		beer["score"] = float(sum(cur) / len(cur) if len(cur) else 0)
		beer["num_of_scorez"] = len(cur)
	return jsonify(beers=beers)

@app.route("/home")
@requires_login
def home():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	cur = g.db.execute("select name, type from Beer order by name asc")
	beers = [dict(name=row[0], type=row[1]) for row in cur.fetchall()]
	for beer in beers:
		cur = [a[0] for a in g.db.execute("select p from Score where beer = ? and type = ?", [beer["name"], beer["type"]]).fetchall()]
		beer["score"] = float(sum(cur) / len(cur) if len(cur) else 0)
		beer["num_of_scorez"] = len(cur)
	return render_template("home.html", beers=sorted(beers, key=lambda x : x["score"], reverse=True))

@app.route("/add_beer", methods=["GET", "POST"])
@requires_login
def add_new_beer():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
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
@requires_login
@requires_admin
def delete_beer(beer_name, beer_type):
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	g.db.execute("delete from Beer where name = ? and type = ?", [beer_name, beer_type])
	g.db.commit()
	return "true"
	# return redirect(url_for("home"))

@app.route("/delete_beer", methods=["POST"])
@requires_login
@requires_admin
def delete_beer_json():
	js = request.get_json()
	deleted = False
	if "beer" in js and "type" in js:
		g.db.execute("delete from Beer where name = ? and type = ?", [js["beer"], js["type"]])
		g.db.execute("delete from Score where beer = ? and type = ?", [js["beer"], js["type"]])
		g.db.commit()
		deleted = True
	return jsonify(deleted=deleted)

@app.route("/logout")
def logout():
	# users.remove_user(session["username"])
	session.pop("logged_in", None)
	session.pop("admin", None)
	session.pop("username", None)
	return redirect(url_for("login"))


@app.route("/beer/<beer_name>,<beer_type>")
@requires_login
def show_beer_page(beer_name, beer_type):
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	return render_template("beer_page.html", beer=get_beer_info(beer_name, beer_type))

@app.route("/show_beer")
def show_beer_page_json():
	js = request.get_json()
	if "beer_name" in js and "beer_type" in js:
		return render_template("beer_page.html", beer=get_beer_info(js["beer_name"], js["beer_type"]))
	return redirect(url_for("home"))

@app.route("/user")
@requires_login
def user_page():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	return render_template("user_page.html")

@app.route("/change_password", methods=["POST"])
@requires_login
def change_password():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	js = request.get_json()
	oldPass, newPass = js["old_password"], js["new_password"]
	current_password = g.db.execute("select password from User where username = ?", [session["username"]]).fetchall()[0][0]
	if current_password != hash_password(oldPass):
		return "false"
	g.db.execute("update User set password = ? where username = ?", [hash_password(newPass), session["username"]])
	g.db.commit()	
	return "true"

@app.route("/types_admin")
@requires_login
@requires_admin
def types_page_admin():
	return render_template("types_page.html", types=get_all_types())
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	# if is_admin():
	# return redirect(url_for("home"))

@app.route("/type_handler", methods=["POST", "GET"])
@requires_login
@requires_admin
def type_handler():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	if request.method == "POST":
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
	return "Wrong method: requires POST"

@app.route("/delete_score", methods=["POST"])
@requires_login
def delete_score():
	js = request.get_json()
	if "beer" in js and "type" in js and "user" in js and "point" in js:
		if js["user"] == session["username"] or session["admin"]: 
			g.db.execute("delete from Score where beer = ? and type = ? and user = ? and p = ?", [js["beer"], js["type"], js["user"], js["point"]])
			g.db.commit()
			return jsonify(deleted=True)
	return jsonify(deleted=False)			

@app.route("/user_admin")
@requires_login
@requires_admin
def user_page_admin():
	# get_user_information()
	return render_template("admin.html", users=get_user_information())
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	# if is_admin():
	# return redirect(url_for("home"))

@app.route("/delete_user", methods=["POST", "GET"])
@requires_login
@requires_admin
def delete_user():
	js = request.get_json()
	if "username" in js:
		if session["username"] == js["username"]:
			return jsonify(deleted=False, msg="Kan ikke slette deg selv.")
		g.db.execute("delete from User where username = ?", [js["username"]])
		g.db.execute("delete from Score where user = ?", [js["username"]])
		g.db.commit()
		return jsonify(deleted=True)
	return jsonify(deleted=False)

@app.route("/create_user", methods=["POST", "GET"])
@requires_login
@requires_admin
def create_user():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	if request.method == "POST":
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
	# return redirect(url_for("home"))
	return "Wrong method: requires POST"

@app.route("/users_logged_in")
@requires_login
@requires_admin
def get_users_logged_in():
	# return jsonify(nums=users.get_num_logged_users())
	return jsonify(nums=1)

# @app.route("/get_user_info_admin")
def get_user_information():
	urs = [dict(username=row[0], admin=row[1]) for row in g.db.execute("select username, admin from User").fetchall()]
	# beers = [dict(name=row[0], type=row[1]) for row in cur.fetchall()]
	return urs

@app.route("/add_score", methods=["POST", "GET"])
@requires_login
def add_score():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	js = request.get_json()
	beer, typ, point = js["beer_name"], js["beer_type"], int(js["points"])
	if not len(g.db.execute("select 1 name from Beer where name = ? and type = ?", [beer, typ]).fetchall()) or point > 100 or point < 0 or point % 1 != 0:
		return jsonify(added=False)
	g.db.execute("insert into Score (beer, type, user, p) values (?,?,?,?)", [beer, typ, session["username"], point])
	g.db.commit()
	return jsonify(added=True)

def get_beer_info(beer_name, beer_type):
	scorez = g.db.execute("select user, p from Score where beer = ? and type = ?", [beer_name, beer_type]).fetchall()
	return {"beer_name": beer_name, "beer_type": beer_type, "scores": scorez}

def get_all_types():
	return [typ[0] for typ in g.db.execute("select * from Beer_type order by name asc").fetchall()]

def is_admin():
	return "admin" in session and session["admin"]

def is_logged_in(*args, **kwargs):
	if "logged_in" in session and session["logged_in"]:
		return True
	return False

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

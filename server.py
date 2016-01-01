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
		if len(str(username).split()) != 1:
			return render_template("login.html", error="Brukernavnet finnes ikke.")
		cur = g.db.execute("select password, system_admin, local_admin from User where username = ?", [username]).fetchall()
		if cur and cur[0][0] == hash_password(password):
			session["logged_in"] = True
			session["system_admin"] = cur[0][1] == 1
			session["local_admin"] = cur[0][2] == 1
			session["username"] = username
			# session["groups"] = 
			groups = [dict(name=row[0], group_id=row[1]) for row in g.db.execute("select name, id from Groupi where owner = ?", [session["username"]]).fetchall()]
			other_groups = [dict(name=row[0], owner=row[1], del_element=row[2], types=row[3], points=row[4], group_id=row[5]) for row in g.db.execute("select name, owner, del_element, types_handling, add_points, group_id from GroupRelation inner join Groupi where user = ?", [username]).fetchall()]
			# print(ting)
			# group_ids = [a for a in g.db.execute("select * from GroupRelation where user = ?", [username])]
			# print(group_ids)
			# other_groups = [[dict(name=row[0], owner=row[1]) for row in g.db.execute("select 1 name, owner from Groupi where group_id = ?", [b])] for b in group_ids]
			# print(other_groups)
			# other_groups = [dict(name=row[0], owner=row[1]) for row in g.db.execute("select name, owner from GroupRelation where user = ?", [session["username"]]).fetchall()]
			session["your_groups"] = groups
			session["other_groups"] = other_groups

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
		# return "Du er ikke logget inn.", 403
		return render_template("login.html", error="Du må logge inn for å se denne siden.")
	return is_logged_in

def requires_system_admin(f):
	@wraps(f)
	def is_admin(*args, **kwargs):
		if "system_admin" in session and session["system_admin"]:
			return f(*args, **kwargs)
		return "Du har ikke tilgang til denne siden.", 403
	return is_admin

def requires_local_admin(f):
	@wraps(f)
	def is_local(*args, **kwargs):
		if "local_admin" in session and session["local_admin"]:
			return f(*args, **kwargs)
		return "Du har ikke tilgang til denne siden", 403
	return is_local

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
		group_name, group_owner = request.form["group_name"], request.form["group_owner"]
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

@app.route("/add_beer/<int:group_id>", methods=["GET", "POST"])
@requires_login
def add_new_beer_group(group_id):
	if request.method == "POST":
		if request.form["submitButton"] == "Avbryt":
			return redirect(url_for(""))

@app.route("/delete_beer/<beer_name>,<beer_type>", methods=["GET", "POST"])
@requires_login
@requires_local_admin
def delete_beer(beer_name, beer_type):
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	g.db.execute("delete from Beer where name = ? and type = ?", [beer_name, beer_type])
	g.db.commit()
	return "true"
	# return redirect(url_for("home"))

@app.route("/delete_beer", methods=["POST"])
@requires_login
@requires_local_admin
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
	session.pop("local_admin", None)
	session.pop("system_admin", None)
	session.pop("username", None)
	session.pop("other_groups", None)
	session.pop("your_groups", None)
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
@requires_local_admin
def types_page_admin():
	return render_template("types_page.html", types=get_all_types())
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	# if is_admin():
	# return redirect(url_for("home"))

@app.route("/type_handler", methods=["POST", "GET"])
@requires_login
@requires_local_admin
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
@requires_system_admin
def user_page_admin():
	# get_user_information()
	return render_template("admin.html", users=get_user_information())
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	# if is_admin():
	# return redirect(url_for("home"))

# Fiks denne
@app.route("/delete_user", methods=["POST", "GET"])
@requires_login
@requires_system_admin
def delete_user():
	js = request.get_json()
	if "username" in js:
		if session["username"] == js["username"]:
			return jsonify(deleted=False, msg="Kan ikke slette deg selv.")
		usr = g.db.execute("select system_admin from User where username = ?", [js["username"]]).fetchall()
		if not usr:
			return jsonify(deleted=False, msg="Brukeren {} finnes ikke.".format(js["username"]))
		elif usr[0][0]:
			return jsonify(deleted=False, msg="Kan ikke slette andre system-administratorer.")
		g.db.execute("delete from User where username = ?", [js["username"]])
		g.db.execute("delete from Score where user = ?", [js["username"]])
		g.db.commit()
		return jsonify(deleted=True)
	return jsonify(deleted=False)

@app.route("/create_user", methods=["POST"])
@requires_login
@requires_system_admin
def create_user():
	# if not is_logged_in():
	# 	return redirect(url_for("login"))
	js = request.get_json()
	if not ("username" in js and "password" in js and "system_admin" in js and "local_admin" in js):
		return jsonify(success=False, msg="Wrong json.")
	username, password, local_admin, system_admin = js["username"], js["password"], js["local_admin"], js["system_admin"]
	if len(str(username).split()) != 1:
		return jsonify(success=False, msg="Brukernavn kan ikke inneholde mellomrom.")
	# username, password, admin = request.form["username"], request.form["password"], "admin" in request.form
	if not len(g.db.execute("select 1 username from User where username = ?", [username]).fetchall()):
		if system_admin:
			local_admin = True
		g.db.execute("insert into User values (?,?,?,?)", [username, hash_password(password), local_admin, system_admin])
		g.db.commit()
		# error = "Brukeren {} ble laget".format(username)
		error = False
	else:
		# error = "Brukernavnet {} finnes allerede.".format(username)
		error = True
	return jsonify(success=not error)
		# return render_template("admin.html", error=error)
	# return redirect(url_for("home"))

@app.route("/users_logged_in")
@requires_login
@requires_system_admin
def get_users_logged_in():
	# return jsonify(nums=users.get_num_logged_users())
	return jsonify(nums=1)

# @app.route("/get_user_info_admin")
def get_user_information():
	urs = [dict(username=row[0], local_admin=row[1], system_admin=row[2]) for row in g.db.execute("select username, local_admin, system_admin from User").fetchall()]
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


@app.route("/groups")
@requires_login
def get_groups():
	groups = [dict(name=row[0]) for row in g.db.execute("select name from Groupi where owner = ?", [session["username"]]).fetchall()]
	# other_groups = [dict(name=row[0], owner=row[1]) for row in g.db.execute("select name, owner from GroupRelation where user = ?", [session["username"]]).fetchall()]
	# print(groups)
	# print(other_groups)
	return render_template("groups.html", groups=groups, other_groups=session["other_groups"])

@app.route("/create_group", methods=["POST"])
@requires_login
def create_new_group():
	js = request.get_json()
	if not "group" in js:
		return jsonify(success=False, msg="Wrong json")
	if g.db.execute("select * from Groupi where name = ? and owner = ?", [js["group"], session["username"]]).fetchall():
		return jsonify(success=False, msg="Gruppen eksisterer allerede.")
	g.db.execute("insert into Groupi (name, owner) values (?,?)", [js["group"], session["username"]])
	g.db.commit()
	session["your_groups"].append({"name": js["group"]})
	return jsonify(success=True)


@app.route("/add_user_to_group", methods=["POST"])
@requires_login
def add_user_to_group():
	js = request.get_json()
	if not "group" in js and "user" not in js:
		return jsonify(success=False, msg="Wrong json")
	if js["user"] == session["username"]:
		return jsonify(success=False, msg="Kan ikke legge til deg selv.")
	if not user_exists(js["user"]):
		return jsonify(success=False, msg="The user {} does not exist.".format(js["user"]))
	group_id = g.db.execute("select 1 from Groupi where name = ? and owner = ?", [js["group"], session["username"]]).fetchall() 
	if not group_id:
		return jsonify(success=False, msg="Gruppen eksisterer ikke.")
	group_id = group_id[0][0]
	if g.db.execute("select 1 from GroupRelation inner join Groupi where name = ? and owner = ? and user = ?", [js["group"], session["username"], js["user"]]).fetchall():
		return jsonify(success=False, msg="Brukeren {} er allerede i denne gruppen.".format(js["user"]))
	g.db.execute("insert into GroupRelation values (?,?,?,?,?)", [group_id, js["user"], js["can_delete"], js["types"], js["add_points"]])
	g.db.commit()
	return jsonify(success=True)

@app.route("/show_group_table/<int:group_id>")
@requires_login
def show_group_table(group_id):
	rel = validate_group_info_id(group_id)
	if type(rel) == list:
		# get all beers from a given group
		beers = g.db.execute("select name, type from Beer where group_id = ? order by name asc", [rel[1]]).fetchall()
		beers = [dict(name=row[0], type=row[1]) for row in beers]
		for beer in beers:
			cur = [a[0] for a in g.db.execute("select p from Score where beer = ? and type = ? and group_id = ?", [beer["name"], beer["type"], rel[1]]).fetchall()]
			beer["score"] = float(sum(cur) / len(cur) if len(cur) else 0)
			beer["num_of_scorez"] = len(cur)
		return render_template("group_table.html", beers=sorted(beers, key=lambda x : x["score"], reverse=True), group_name=group_name, owner=owner, relations=rel[0], group_id=rel[1])
	return redirect(url_for("home"))

@app.route("/show_group/<group_name>,<owner>")
@requires_login
def show_group(group_name, owner):
	rel = validate_group_info(group_name, owner)
	if type(rel) == list:
		return render_template("group_page.html", group_name=group_name, owner=owner, relations=rel[0])
	return redirect(url_for("home"))

def validate_group_info_id(group_id):
	ting = g.db.execute("select name, owner from Groupi where id = ?",[group_id]).fetchall()
	print(ting)
	if not ting:
		return False
	return validate_group_info(ting[0][0], ting[0][1])

def validate_group_info(group_name, owner):
	if not group_name or not owner:
		return False
	group_id = g.db.execute("select 1 from Groupi where name = ? and owner = ?", [group_name, owner]).fetchall()
	if not group_id:
		return False
	group_id = group_id[0][0]
	# relations = [a[0] for a in g.db.execute("select user from GroupRelation where name = ? and owner = ?",[group_name, owner]).fetchall()]
	relations = [a[0] for a in g.db.execute("select user from GroupRelation inner join Groupi where Groupi.name = ? and Groupi.owner = ?",[group_name, owner]).fetchall()]
	if session["username"] not in relations and owner != session["username"]:
		return False
	return [relations, group_id]

@app.route("/leave_group", methods=["POST"])
@requires_login
def leave_group():
	js = request.get_json()
	if "group" not in js and "owner" not in js:
		return jsonify(success=False, msg="Wrong json.")
	group, owner = js["group"], js["owner"]
	if owner == session["username"]:
		return jsonify(success=False, msg="Kan ikke forlate egen gruppe, den må slettes.")
	if user_exists(owner):
		# g.db.execute("delete from Groupi where name = ? and owner = ?", [group, owner])
		g.db.execute("delete from GroupRelation where name = ? and owner = ? and user = ?", [group, owner, session["username"]])
		# delete scores given by this user
		g.db.commit()
		obj = {"owner": js["owner"], "name": js["group"]}
		if obj in session["other_groups"]:
			session["other_groups"].remove(obj)
		return jsonify(success=True)
	return jsonify(success=False, msg="Eieren eksisterer ikke.")

@app.route("/delete_group", methods=["POST"])
@requires_login
def delete_group():
	js = request_get_json()
	if "owner" not in js or "group" not in js:
		return jsonify(success=False, msg="Wrong JSON.")
	group, owner = js["group"], js["owner"]
	if owner != session["username"]:
		return jsonify(success=False, msg="Kan ikke slette andres grupper.")
	if g.db.execute("select 1 from Groupi where name = ? and owner = ?", [group, owner]).fetchall():
		g.db.execute("delete from Groupi where name = ? and owner = ?", [group, owner])
		g.db.execute("delete from GroupRelation where name = ? and owner = ?", [group, owner])
		g.db.commit()
		return jsonify(success=True)
	return jsonify(success=False, msg="Gruppen eksisterer ikke.")

def belongs_to_group(username, group_name, owner):
	if not is_string(username, group_name, owner):
		return False
	group_id = g.db.execute("select 1 from Groupi where name = ? and owner = ?", [group_name, owner]).fetchall()
	if not group_id:
		return False
	group_id = group_id[0]
	rel = [dict(id=row[0], user=row[1], del_element=row[2], types=row[3], add_points=row[4]) for row in g.db.execute("select 1 from GroupRelation where group_id = ? and user = ?", [group_id, username]).fetchall()]
	if not rel:
		return False
	return rel	


def is_string(*args):
	for a in args:
		if type(a) != str:
			return False
	return True

def request_get_json():
	if request:
		try:
			return request.get_json()
		except:
			print("ERROR: JSON object could not be loaded.")
			return None
	return None

def user_exists(username):
	if g.db and username:
		return len(g.db.execute("select username from User where username = ?", [username]).fetchall()) != 0
	return False

def get_all_group_information(group, owner):

	pass

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

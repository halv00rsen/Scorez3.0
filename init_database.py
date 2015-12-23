#! python3
from server import init_db, hash_password, connect_db
from getpass import getpass
from os import path, makedirs

def config_file_ok():
	if path.exists("server_config.py"):
		with open("server_config.py", "r") as f:
			data = f.readlines()
		h = {"DEBUG": False, "DATABASE": False, "SECRET_KEY": False}
		for a in data:
			a = a.strip()
			if a.startswith("DEBUG"):
				h["DEBUG"] = True
			elif a.startswith("DATABASE"):
				h["DATABASE"] = True
			elif a.startswith("SECRET_KEY"):
				h["SECRET_KEY"] = True
		for a in h:
			if not h[a]:
				print("Config file does not contain {}. Creating a new config file.".format(a))
				return False
		return True
	print("Config file does not exists. Creating a new one.")
	return False

def init():
	if __name__ != "__main__":
		return "ERROR: Must start from terminal."
	print("Initializes the server config and database.")
	reset = False
	conf = config_file_ok()
	if conf:
		inp = input("Config file looks ok. Do you want to reset it (y/n)?")
		reset = inp == "y"
		if reset:
			print("Will create a new config file.")
	if reset or not conf:
		# db = input("Database name: ")
		# if not db:
		# 	print("No database name. Aborting...")
		# 	return None
		secret_key = input("Super secret key: ")
		if not secret_key:
			print("Need a secret key. Aborting...")
			return
		with open("server_config.py", "w") as f:
			f.write("from os import path")
			f.write("DEBUG = True\n")
			f.write("SECRET_KEY = '{}'\n".format(secret_key))
			f.write("DATABASE = path.join('db', 'database.db')")

	if path.isdir("db") and path.exists(path.join("db", "database.db")):
		print("A database already exists.")
		print("1. Reset current database.")
		print("2. Transfer data to new database.")
		print("3. Keep old database.")
		inp = input("Action (1,2,3): ")
		# inp = input("A database already exists. Do you want to reset current database? (y/n) ")
		# if inp != "y":
		# 	print("Database was not reseted.")
		# 	return None
		if inp == "2":
			pass
		elif inp != "1":
			print("Old database keeped.")
			return None
	print("Will initialize a new database.")
	print("You will need an admin account.")
	username = input("Username: ")
	password = getpass("Password: ")
	retype_pass = getpass("Retype password: ")

	if len(username) == 0 or len(password) == 0 or password != retype_pass:
		print("Error! Username or password is empty. Aborting...")
	else:
		if not path.isdir("db"):
			makedirs("db")
		with open(path.join("db", "database.db"), "w") as f:
			pass
		init_db()
		db = connect_db()
		try:
			r = db.execute("insert into User values (?,?,?,?)", [username, hash_password(password), True, True])
			db.execute("insert into Beer_type values (?)", ["Ingen"])
			db.commit()
			print("Database was successfully created.")
		except:
			print("Database not created, error.")
			pass
		finally:
			if db:
				db.close()

if __name__ == "__main__":
	init()
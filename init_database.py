#! python3
from server import init_db, hash_password, connect_db
from getpass import getpass
from os import path, makedirs

if __name__ == "__main__":
	print("Will create a new database")
	if path.isdir("db") and path.exists(path.join("db", "database.db")):
		inp = input("A database already exists. Do you want to reset current database? (y/n) ")
		if inp != "y":
			print("Aborting...")
			
	print("You will need an admin account.")
	username = input("Username: ")
	password = getpass("Password: ")
	retype_pass = getpass("Retype password: ")

	if len(username) == 0 or len(password) == 0 or password != retype_pass:
		print("Error! Username or password is empty.")
	else:
		if not path.isdir("db"):
			makedirs("db")
		with open(path.join("db", "database.db"), "w") as f:
			pass
		init_db()
		db = connect_db()
		try:
			r = db.execute("insert into User values (?,?,?)", [username, hash_password(password), True])
			db.execute("insert into Beer_type values (?)", ["Ingen"])
			db.commit()
			print("Database was successfully created.")
		except:
			print("Database not created, error.")
			pass
		finally:
			if db:
				db.close()
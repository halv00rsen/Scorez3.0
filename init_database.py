#! python3
from server import init_db, hash_password, connect_db

if __name__ == "__main__":
	print("Will create a new database")
	print("You will need an admin account.")
	username = input("Username: ")
	password = input("Password: ")
	if len(username) == 0 or len(password) == 0:
		print("Error! Username or password is empty.")
	else:
		with open("database.db", "w") as f:
			pass
		init_db()
		password = hash_password(password)
		db = connect_db()
		try:
			r = db.execute("insert into User values (?,?,?)", [username, password, True])
			db.execute("insert into Beer_type values (?)", ["Ingen"])
			db.commit()
			print("Database was successfully created.")
		except:
			print("Database not created, error.")
			pass
		finally:
			if db:
				db.close()
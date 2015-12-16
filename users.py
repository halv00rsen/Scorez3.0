from time import time

TIMEOUT = 30

class Users:

	def __init__(self):
		self.users_logged_in = {}

	def add_user_activity(self, username):
		self.users_logged_in[username] = time()

	def remove_user(self, username):
		self.users_logged_in.pop(username, None)

	def get_num_logged_users(self):
		t = time()
		rm = []
		for a in self.users_logged_in.keys():
			if self.users_logged_in[a] + TIMEOUT < t:
				rm.append(a)
		for b in rm:
			self.users_logged_in.pop(b, None)
		return len(self.users_logged_in)



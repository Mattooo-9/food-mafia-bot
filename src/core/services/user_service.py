import json
import os

class UserService:
    DATA_FILE = "data/users.json"

    def __init__(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE, 'w') as f:
                json.dump({}, f)

    def _load_users(self):
        with open(self.DATA_FILE, 'r') as f:
            return json.load(f)

    def _save_users(self, users):
        with open(self.DATA_FILE, 'w') as f:
            json.dump(users, f, indent=4)

    def get_user(self, user_id):
        users = self._load_users()
        return users.get(str(user_id))

    def update_user(self, user_id, **kwargs):
        users = self._load_users()
        user_id_str = str(user_id)
        if user_id_str not in users:
            users[user_id_str] = {}
        users[user_id_str].update(kwargs)
        self._save_users(users)

user_service = UserService()

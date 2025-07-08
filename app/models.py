from flask_login import UserMixin
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.email = user_data.get('email')
        self.name = user_data.get('name', self.email) # Use name, fallback to email
        self.password = user_data.get('password')
        self.roles = user_data.get('roles', [])

    @staticmethod
    def get(db, user_id):
        """Static method to find a user by ID."""
        try:
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except Exception:
            return None
        return None

    def has_role(self, role):
        """Method to check if a user has a specific role."""
        return role in self.roles

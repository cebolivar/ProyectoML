from flask_login import UserMixin
from werkzeug.security import generate_password_hash

# --- MODELO DE USUARIO Y BASE DE DATOS FICTICIA ---

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Base de datos de usuarios ficticia
USERS = {
    1: User(1, 'admin', generate_password_hash('pass123')),
    2: User(2, 'user', generate_password_hash('otra123')),
}

def get_user_by_id(user_id):
    """Función para obtener un usuario por su ID."""
    return USERS.get(int(user_id))

def get_user_by_username(username):
    """Función para obtener un usuario por su nombre de usuario."""
    return next((u for u in USERS.values() if u.username == username), None)
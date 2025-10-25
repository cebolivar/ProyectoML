from flask_login import UserMixin
from werkzeug.security import generate_password_hash

# --- MODELO DE USUARIO Y BASE DE DATOS FICTICIA ---

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Base de datos de usuarios ficticia (en memoria)
USERS = {
    1: User(1, 'admin', generate_password_hash('pass123')),
    2: User(2, 'user', generate_password_hash('otra123')),
}

def get_user_by_id(user_id):
    """Retorna el usuario por ID o None si no existe."""
    try:
        return USERS.get(int(user_id))
    except (TypeError, ValueError):
        return None

def get_user_by_username(username):
    """Retorna el usuario por nombre de usuario o None si no existe."""
    return next((u for u in USERS.values() if u.username == username), None)

def add_new_user(username, password):
    """Añade un nuevo usuario (en memoria) y lo devuelve."""
    new_id = max(USERS.keys(), default=0) + 1
    pw_hash = generate_password_hash(password)
    user = User(new_id, username, pw_hash)
    USERS[new_id] = user
    return user
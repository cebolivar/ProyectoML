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
# Variable para el ID del próximo usuario
next_user_id = 3 

def get_user_by_id(user_id):
    """Función para obtener un usuario por su ID."""
    return USERS.get(int(user_id))

def get_user_by_username(username):
    """Función para obtener un usuario por su nombre de usuario."""
    return next((u for u in USERS.values() if u.username == username), None)

def add_new_user(username, password):
    """Función para agregar un nuevo usuario (simulación de guardado en DB)."""
    global next_user_id
    
    # 1. Verificar si el usuario ya existe
    if get_user_by_username(username):
        return None  # Indica que el usuario ya existe
    
    # 2. Hashear la contraseña
    hashed_password = generate_password_hash(password)
    
    # 3. Crear y guardar el nuevo usuario
    new_user = User(next_user_id, username, hashed_password)
    USERS[next_user_id] = new_user
    next_user_id += 1
    
    return new_user
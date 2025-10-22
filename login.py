from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

app = Flask(__name__)
# ¡IMPORTANTE! Clave secreta para proteger las sesiones
app.config['SECRET_KEY'] = 'mi_clave_secreta_super_segura_123' 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Indica la vista a la que ir si se requiere login

# --- 1. MODELO DE USUARIO Y BASE DE DATOS FICTICIA ---

# En una aplicación real, este User estaría conectado a una DB (Flask-SQLAlchemy)
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Base de datos de usuarios ficticia
# Contraseña: 'pass123' hasheada (puedes generar la tuya con generate_password_hash('tu_pass'))
USERS = {
    1: User(1, 'admin', generate_password_hash('pass123')),
    2: User(2, 'user', generate_password_hash('otra123')),
}

# --- 2. CARGADOR DE USUARIO (REQUERIDO POR FLASK-LOGIN) ---

@login_manager.user_loader
def load_user(user_id):
    """Retorna un objeto User dado su ID."""
    return USERS.get(int(user_id))


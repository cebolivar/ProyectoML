from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from login import get_user_by_username # Importamos el modelo

# Definir el Blueprint. El prefijo /auth_bp es opcional, lo dejaremos vacío
auth_bp = Blueprint('auth_bp', __name__, url_prefix='') 

# --- CARGADOR DE USUARIO (DEBE ESTAR EN app.py, lo dejamos como referencia) ---
# Nota: La función user_loader DEBE definirse en el mismo archivo donde se inicializa 
# el LoginManager (app.py en este caso), pero las funciones que usa pueden venir de 
# este archivo.

# --- RUTAS DE AUTENTICACIÓN ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el formulario de inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('auth_bp.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Buscar usuario
        user = get_user_by_username(username)

        # Verificar si el usuario existe y la contraseña es correcta
        if user and check_password_hash(user.password_hash, password):
            login_user(user) # Iniciar sesión
            
            # Redirigir al destino original (next) o al dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth_bp.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario."""
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth_bp.login'))

# --- RUTAS PROTEGIDAS ---

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Página solo accesible para usuarios autenticados."""
    return render_template('dashboard.html', username=current_user.username)
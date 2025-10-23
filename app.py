from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from user_model import get_user_by_username, add_new_user # Importamos funciones del modelo de usuario
from login import init_login # Importamos la función de inicialización de login
# --- CONFIGURACIÓN E INICIALIZACIÓN ---

app = Flask(__name__)
# ¡IMPORTANTE! Clave secreta para proteger las sesiones
app.config['SECRET_KEY'] = 'mi_clave_secreta_super_segura_123' 

# Inicializar Flask-Login usando la función del archivo login.py
init_login(app)

# --- RUTAS DE LA APLICACIÓN ---

#@app.route('/index')
#def Index():
     #Myname= "Flask"
     #return render_template('index.html', name=Myname)

@app.route('/')
def index():
    """Página principal que muestra la bienvenida si está logueado."""
    Myname = "Flask"
    if current_user.is_authenticated:
        # Aquí puedes renderizar tu plantilla principal (index.html)
        # o redirigir a una página de bienvenida si la tienes.
        flash(f'Bienvenido de nuevo, {current_user.username}!', 'success')
        # Suponiendo que tienes un archivo index.html
        return render_template('index.html', username=current_user.username)
        
    # Si no está autenticado, redirigir al login
    return redirect(url_for('register'))
# --- RUTA DE LOGIN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el formulario de inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            # Redirigir al destino original (next) o al dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

# --- RUTA PROTEGIDA (DASHBOARD) ---

@app.route('/dashboard')
@login_required # ¡Decorador que exige estar logueado!
def dashboard():
    """Página solo accesible para usuarios autenticados."""
    return render_template('dashboard.html', username=current_user.username)

# --- RUTA DE LOGOUT ---

@app.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario."""
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el formulario de registro de nuevos usuarios."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validación básica
        if not username or not password:
            flash('Por favor, ingresa un nombre de usuario y una contraseña.', 'error')
            return render_template('register.html')
        
        # Intentar agregar el nuevo usuario
        new_user = add_new_user(username, password)

        if new_user:
            flash(f'¡Cuenta creada para {username}! Ahora puedes iniciar sesión.', 'info')
            return redirect(url_for('login'))
        else:
            flash('El nombre de usuario ya está en uso.', 'error')

    return render_template('registro.html')

if __name__ == '__main__':
    app.run(debug=True)
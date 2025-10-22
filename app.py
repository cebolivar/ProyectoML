from flask import Flask
from flask import Flask, render_template
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from login import USERS



# Crear la aplicación
app = Flask(__name__)

# Ruta principal
@app.route('/')
def Index():
     Myname= "Flask"
     return render_template('Index.html', name=Myname)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el formulario de inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Buscar usuario por nombre de usuario
        user = next((u for u in USERS.values() if u.username == username), None)

        # Verificar si el usuario existe y la contraseña es correcta
        if user and check_password_hash(user.password_hash, password):
            # Iniciar sesión del usuario
            login_user(user)
            # Redirigir al destino original o al dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error') # Muestra el mensaje de error

    return render_template('login.html')

# --- RUTA PROTEGIDA (DASHBOARD) ---

@app.route('/dashboard')
@login_required # ¡Decorador que exige estar logueado!
def dashboard():
    """Página solo accesible para usuarios autenticados."""
    return render_template('dashboard.html', username=current_user.username)

if __name__ == '__main__':
    app.run(debug=True)

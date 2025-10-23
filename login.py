from flask_login import LoginManager
from user_model import get_user_by_id

# Inicializar el manager de Login
login_manager = LoginManager()

def init_login(app):
    """Inicializa Flask-Login y configura el user_loader."""
    login_manager.init_app(app)
    # Indica la vista a la que ir si se requiere login
    login_manager.login_view = 'auth_bp.login'

    # --- CARGADOR DE USUARIO (REQUERIDO POR FLASK-LOGIN) ---
    @login_manager.user_loader
    def load_user(user_id):
        """Retorna un objeto User dado su ID, usando la función del modelo."""
        return get_user_by_id(user_id)
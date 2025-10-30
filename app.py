from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from user_model import get_user_by_username, add_new_user
from login import init_login

import joblib
import pandas as pd
import os

# --- CONFIGURACIÓN E INICIALIZACIÓN ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mi_clave_secreta_super_segura_123'

# Inicializar Flask-Login (login.py debe definir user_loader)
init_login(app)

# --- RUTAS DE AUTENTICACIÓN Y PÁGINAS ---
@app.route('/', methods=['GET'])
def root():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Usuario y contraseña requeridos.', 'error')
            return render_template('registro.html')
        new_user = add_new_user(username, password)
        if new_user:
            flash('Cuenta creada. Inicia sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('No se pudo crear el usuario.', 'error')
    return render_template('registro.html')

@app.route('/index')
@login_required
def index():
    Myname = "Flask"
    return render_template('index.html', name=Myname, username=current_user.username)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)


# --- CONFIGURACIÓN ML Y ARCHIVOS ---
BASE_DIR = os.path.dirname(__file__)
MODEL_FILENAME = os.path.join(BASE_DIR, 'donapp_ml_model.joblib')
VECTORIZER_FILENAME = os.path.join(BASE_DIR, 'donapp_tfidf_vectorizer.joblib')
ENCODER_FILENAME = os.path.join(BASE_DIR, 'donapp_label_encoder.joblib')

DATA_DIR = os.path.join(BASE_DIR, 'data')
DATA_FILE = os.path.join(DATA_DIR, 'donapp_data_tecnico.csv')
FEEDBACK_FILE = os.path.join(BASE_DIR, 'user_feedback.csv')

def safe_load(path):
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None

model = safe_load(MODEL_FILENAME)
tfidf_vectorizer = safe_load(VECTORIZER_FILENAME)
label_encoder = safe_load(ENCODER_FILENAME)

def ensure_data_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        header = ['id_usuario','nombre_usuario','tipo_usuario','tipo','marca','modelo','anio',
                  'estado_fisico','encendido','fallas','ram','almacenamiento','descripcion',
                  'destino','prediccion_ml']
        pd.DataFrame(columns=header).to_csv(DATA_FILE, index=False, sep=';')


# --- RUTAS ML / INTERFAZ ---
@app.route('/interfaz')
def interfaz():
    return render_template('interfaz.html')

# ÚNICO endpoint /predict -> devuelve JSON (para AJAX)
@app.route('/predict', methods=['POST'])
def predict():
    if model is None or tfidf_vectorizer is None or label_encoder is None:
        return jsonify({'error': 'Modelos no cargados. Genera los archivos .joblib primero.'}), 503

    # aceptar JSON o form-data
    payload = request.get_json(force=True) if request.is_json else request.form.to_dict()
    modelo_text = (payload.get('modelo') or '').strip()
    if not modelo_text:
        return jsonify({'error': 'El campo "modelo" es requerido.'}), 400

    try:
        vec = tfidf_vectorizer.transform([modelo_text])
        pred_enc = model.predict(vec)
        pred_label = label_encoder.inverse_transform(pred_enc)[0]
    except Exception as e:
        return jsonify({'error': f'Error en la predicción: {str(e)}'}), 500

    try:
        ensure_data_file()
        cols = ['id_usuario','nombre_usuario','tipo_usuario','tipo','marca','modelo','anio',
                'estado_fisico','encendido','fallas','ram','almacenamiento','descripcion',
                'destino','prediccion_ml']
        record = {c: payload.get(c, '') for c in cols}
        record['prediccion_ml'] = pred_label
        pd.DataFrame([record]).to_csv(DATA_FILE, mode='a', header=False, index=False, sep=';')
    except Exception as e:
        return jsonify({'error': f'No se pudo guardar registro: {str(e)}'}), 500

    return jsonify({'modelo_ingresado': modelo_text, 'prediccion_ml': pred_label}), 200

# Ruta alternativa para renderizar resultado en plantilla (form POST -> muestra predict.html)
@app.route('/predict_page', methods=['POST'])
def predict_page():
    if model is None or tfidf_vectorizer is None or label_encoder is None:
        return render_template('predict.html', modelo='', prediccion='Modelos no cargados')

    payload = request.get_json(force=True) if request.is_json else request.form.to_dict()
    modelo_text = (payload.get('modelo') or '').strip()
    if not modelo_text:
        return render_template('predict.html', modelo='', prediccion='Campo modelo vacío')

    try:
        vec = tfidf_vectorizer.transform([modelo_text])
        pred_enc = model.predict(vec)
        pred_label = label_encoder.inverse_transform(pred_enc)[0]
    except Exception as e:
        return render_template('predict.html', modelo=modelo_text, prediccion=f'Error: {e}')

    # guardar (intento silencioso)
    try:
        ensure_data_file()
        cols = ['id_usuario','nombre_usuario','tipo_usuario','tipo','marca','modelo','anio',
                'estado_fisico','encendido','fallas','ram','almacenamiento','descripcion',
                'destino','prediccion_ml']
        record = {c: payload.get(c, '') for c in cols}
        record['prediccion_ml'] = pred_label
        pd.DataFrame([record]).to_csv(DATA_FILE, mode='a', header=False, index=False, sep=';')
    except Exception:
        pass

    return render_template('predict.html', modelo=modelo_text, prediccion=pred_label)


@app.route('/feedback', methods=['POST'])
def receive_feedback():
    try:
        data = request.get_json(force=True)
        modelo = data.get('modelo')
        clasificacion_real = data.get('clasificacion_real')
        if not modelo or not clasificacion_real:
            return jsonify({'error': 'Modelo y clasificación real son requeridos.'}), 400

        new_data = pd.DataFrame({
            'modelo': [modelo],
            'clasificacion_real': [clasificacion_real],
            'timestamp': [pd.Timestamp.now()]
        })

        if os.path.exists(FEEDBACK_FILE):
            new_data.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False, sep=';')
        else:
            new_data.to_csv(FEEDBACK_FILE, mode='w', header=True, index=False, sep=';')

        return jsonify({'message': 'Feedback guardado correctamente', 'modelo': modelo, 'real': clasificacion_real}), 200

    except Exception as e:
        return jsonify({'error': f'Error al procesar el feedback: {str(e)}'}), 500

@app.route('/casuistica')
def casuistica():
    return render_template('casuistica.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
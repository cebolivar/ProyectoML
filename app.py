from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from predict import save_data_to_csv, simulate_prediction, generate_prediction_pdf
from user_model import get_user_by_username, add_new_user
from login import init_login

import joblib
import pandas as pd
import os
import uuid
import threading
import time
from io import BytesIO

# Tiempo en segundos para conservar un PDF descargable antes de eliminarlo.
# Cambia `PDF_RETENTION_SECONDS` si quieres ajustar el periodo de reintentos.
# Por defecto está en 30 (30 segundos). Para pruebas locales, puedes reducirlo.
PDF_RETENTION_SECONDS = 30
# Permitir sobreescribir mediante variable de entorno `PDF_RETENTION_SECONDS`.
# Ejemplo en PowerShell (temporal para la sesión):
#   $env:PDF_RETENTION_SECONDS = '60'
try:
    PDF_RETENTION_SECONDS = int(os.environ.get('PDF_RETENTION_SECONDS', str(PDF_RETENTION_SECONDS)))
except Exception:
    print("Advertencia: valor de entorno PDF_RETENTION_SECONDS no válido; usando 30 segundos.")

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

# Endpoint /predict -> GET muestra el formulario, POST procesa la predicción
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Ruta que muestra el formulario en GET y maneja el envío en POST."""
    if request.method == 'GET':
        return render_template('predict.html')

    # POST: Obtener todos los datos del formulario
    form_data = request.form.to_dict()
    print("Datos recibidos:", form_data)

    # 1. Realizar la Predicción (usando el campo 'modelo')
    modelo_text = form_data.get('modelo', '')
    if not modelo_text:
        prediction_result = "Error: El campo 'modelo' es obligatorio."
    else:
        prediction_result = simulate_prediction(modelo_text)

    # 2. Agregar el resultado de la predicción a los datos antes de guardar
    form_data['prediction_result'] = prediction_result

    # 3. Guardar los datos completos (incluida la predicción)
    try:
        save_data_to_csv(form_data)
    except Exception as e:
        print(f"Error al guardar en CSV: {e}")

    # 4. Generar PDF y devolverlo como descarga
    try:
        pdf_buffer = generate_prediction_pdf(form_data, prediction_result)
        # Guardar el PDF en un archivo temporal dentro del proyecto
        tmp_dir = os.path.join(BASE_DIR, 'tmp_pdfs')
        os.makedirs(tmp_dir, exist_ok=True)
        filename = f"pred_{uuid.uuid4().hex}.pdf"
        file_path = os.path.join(tmp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())

        # Renderizar página de resultado con enlace de descarga
        download_url = url_for('download_pdf', filename=filename)
        return render_template('predict_result.html', modelo=modelo_text, prediction=prediction_result, download_url=download_url)
    except Exception as e:
        print(f"Error al generar/servir el PDF: {e}")
        # Caer a una respuesta simple si falla la generación del PDF
        success_message = f"""
        <h1>✅ Predicción Exitosa</h1>
        <p>La predicción para el modelo **"{modelo_text}"** es:</p>
        <h2>{prediction_result}</h2>
        <p>Todos los datos han sido guardados en `data_log.csv`.</p>
        <br>
        <a href="/predict">Volver al formulario</a>
        """
        return success_message

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


@app.route('/download_pdf/<filename>')
def download_pdf(filename):
    tmp_dir = os.path.join(BASE_DIR, 'tmp_pdfs')
    file_path = os.path.join(tmp_dir, filename)
    if not os.path.exists(file_path):
        return "Archivo no encontrado", 404
    try:
        # Leer el archivo en memoria
        with open(file_path, 'rb') as f:
            data = f.read()

        # Programar la eliminación diferida del archivo para permitir reintentos
        # Usa la constante `PDF_RETENTION_SECONDS` definida al inicio del archivo.
        _schedule_delete(file_path, delay_seconds=PDF_RETENTION_SECONDS)

        bio = BytesIO(data)
        bio.seek(0)
        try:
            return send_file(bio, as_attachment=True, download_name=filename, mimetype='application/pdf')
        except TypeError:
            return send_file(bio, as_attachment=True, attachment_filename=filename, mimetype='application/pdf')
    except Exception as e:
        print(f"Error al enviar el PDF: {e}")
        return "Error al descargar el archivo", 500


def _tmp_pdfs_cleaner(interval_seconds: int = 600, max_age_seconds: int = 3600):
    """Hilo demonio que limpia archivos en `tmp_pdfs/` más antiguos que `max_age_seconds`.

    - interval_seconds: cada cuántos segundos revisa (por defecto 600s = 10min)
    - max_age_seconds: edad máxima permitida (por defecto 3600s = 1h)
    """
    tmp_dir = os.path.join(BASE_DIR, 'tmp_pdfs')
    os.makedirs(tmp_dir, exist_ok=True)
    while True:
        try:
            now = time.time()
            for fname in os.listdir(tmp_dir):
                fpath = os.path.join(tmp_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    age = now - mtime
                    if age > max_age_seconds:
                        os.remove(fpath)
                        print(f"Eliminado archivo temporal antiguo: {fpath}")
                except FileNotFoundError:
                    continue
                except Exception as e:
                    print(f"Error limpiando {fpath}: {e}")
        except Exception as e:
            print(f"Error en el limpiador de tmp_pdfs: {e}")
        time.sleep(interval_seconds)


def _schedule_delete(path: str, delay_seconds: int = 30):
    """Programar la eliminación de `path` después de `delay_seconds`.

    Se ejecuta en un hilo daemon para no bloquear la petición.
    """
    def _delayed():
        try:
            time.sleep(delay_seconds)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"Eliminado archivo temporal tras descarga: {path}")
                except Exception as e:
                    print(f"No se pudo eliminar {path} tras retraso: {e}")
        except Exception as e:
            print(f"Error en hilo de eliminación diferida para {path}: {e}")

    t = threading.Thread(target=_delayed, daemon=True)
    t.start()

if __name__ == '__main__':
    # Iniciar hilo demonio que limpia PDFs temporales cada 10 minutos (archivos > 1 hora)
    cleaner_thread = threading.Thread(target=_tmp_pdfs_cleaner, kwargs={'interval_seconds': 600, 'max_age_seconds': 3600}, daemon=True)
    cleaner_thread.start()

    app.run(host='0.0.0.0', port=5000, debug=True)
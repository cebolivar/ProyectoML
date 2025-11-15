from flask import Flask, request, render_template, send_file
from fpdf import FPDF
import pandas as pd
import os
from io import BytesIO

# --- Configuración Inicial ---
app = Flask(__name__)
CSV_FILE = 'data_log.csv'
TEMPLATES_FOLDER = 'templates' # Por convención de Flask

# --- Simulador de Modelo de ML (Aquí iría tu lógica real) ---
def simulate_prediction(model_text):
    """
    Simula una predicción basada en el texto del modelo.
    En un entorno real, cargarías y ejecutarías tu modelo de ML aquí.
    """
    model_text = model_text.lower()
    if "laptop" in model_text or "pc" in model_text:
        return "Categoría Predicha: Electrónica/Portátil"
    elif "monitor" in model_text or "pantalla" in model_text:
        return "Categoría Predicha: Periféricos/Visual"
    else:
        return "Categoría Predicha: Varios/Desconocido"

# --- Manejo de Datos (Guardar en CSV) ---
def save_data_to_csv(data):
    """Guarda los datos del formulario en un archivo CSV."""
    
    # 1. Preparar la estructura de los datos para Pandas
    # Añadimos la predicción y una marca de tiempo
    data['prediccion_ml'] = data.pop('prediction_result') # Cambiar nombre de la clave
    data['timestamp'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    df_new_row = pd.DataFrame([data])
    
    # 2. Cargar o crear el DataFrame
    if os.path.exists(CSV_FILE):
        df_existing = pd.read_csv(CSV_FILE)
        df_combined = pd.concat([df_existing, df_new_row], ignore_index=True)
    else:
        df_combined = df_new_row
        
    # 3. Guardar en el CSV
    df_combined.to_csv(CSV_FILE, index=False)
    print(f"Datos guardados en {CSV_FILE}")


def generate_prediction_pdf(data, prediction):
    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Informe de Predicción del Modelo", 0, 1, "C")
    pdf.ln(5)

    # Resultado de la Predicción
    pdf.set_fill_color(220, 220, 255)  # Color de fondo azul claro
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"PREDICCIÓN: {prediction}", 1, 1, "C", True)
    pdf.ln(5)

    # Datos Enviados
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Datos del Equipo Registrado:", 0, 1, "L")
    pdf.ln(1)

    # Listar los datos en el PDF
    pdf.set_font("Arial", "", 10)
    for key, value in data.items():
        # Excluir el campo prediction_result si está presente temporalmente
        if key == 'prediction_result':
            continue

        # Formatear la clave
        display_key = key.replace('_', ' ').title()

        pdf.cell(50, 7, f"{display_key}:", 0, 0, "L")
        pdf.cell(0, 7, str(value), 0, 1, "L")

    # Salida del PDF en memoria
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

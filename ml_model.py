import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import joblib

# 1. Parámetros y Carga de Datos
FILE_PATH = "donapp_data_tecnico.csv"
MODEL_FILENAME = "donapp_ml_model.joblib"
VECTORIZER_FILENAME = "donapp_tfidf_vectorizer.joblib"
ENCODER_FILENAME = "donapp_label_encoder.joblib"

df = pd.read_csv(FILE_PATH, sep=";")

# 2. Preparación de Características (Feature Engineering)
X = df['modelo'].astype(str)
y = df['prediccion_ml']

# Codificación de etiquetas para la variable objetivo (y)
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Dividir los datos (Aunque el entrenamiento sea con todo, es buena práctica)
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.3, random_state=42, stratify=y_encoded
)

# Vectorización TF-IDF de la característica 'modelo'
tfidf = TfidfVectorizer(max_features=50, stop_words=None, ngram_range=(1, 1))
X_train_tfidf = tfidf.fit_transform(X_train)

# 3. Entrenamiento del Modelo
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train_tfidf, y_train)

# 4. Guardar los artefactos (Modelo, TF-IDF, Encoder)
joblib.dump(rf_model, MODEL_FILENAME)
joblib.dump(tfidf, VECTORIZER_FILENAME)
joblib.dump(label_encoder, ENCODER_FILENAME)

print("¡Entrenamiento completado y artefactos guardados!")
print(f"Modelo guardado como: {MODEL_FILENAME}")
print(f"Vectorizador guardado como: {VECTORIZER_FILENAME}")
print(f"Codificador de etiquetas guardado como: {ENCODER_FILENAME}")

# Clases decodificadas para referencia
print("\nClases objetivo:")
for i, name in enumerate(label_encoder.classes_):
    print(f"  {i}: {name}")
import os
from pathlib import Path
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

BASE = Path(__file__).parent
DATA_PATHS = [BASE / "data" / "donapp_data_tecnico.csv", BASE / "donapp_data_tecnico.csv"]
MODEL_FILENAME = BASE / "donapp_ml_model.joblib"
VECTORIZER_FILENAME = BASE / "donapp_tfidf_vectorizer.joblib"
ENCODER_FILENAME = BASE / "donapp_label_encoder.joblib"

def create_sample_csv(target_path: Path):
    print(f"No se encontró datos. Creando ejemplo en: {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {"id_usuario": "1","nombre_usuario":"Tecnico A","tipo_usuario":"tecnico","tipo":"Celular","marca":"Samsung","modelo":"Galaxy S21","anio":"2021","estado_fisico":"bueno","encendido":"si","fallas":"no carga","ram":"8GB","almacenamiento":"128GB","descripcion":"Batería baja","destino":"Reparación","prediccion_ml":"Reparación"},
        {"id_usuario": "2","nombre_usuario":"Cliente B","tipo_usuario":"cliente","tipo":"Celular","marca":"Apple","modelo":"iPhone 11","anio":"2019","estado_fisico":"dañado","encendido":"parcial","fallas":"pantalla rota","ram":"4GB","almacenamiento":"64GB","descripcion":"Pantalla rota","destino":"Reparación","prediccion_ml":"Reparación"},
        {"id_usuario": "3","nombre_usuario":"Tecnico C","tipo_usuario":"tecnico","tipo":"Tablet","marca":"Xiaomi","modelo":"Mi Pad","anio":"2020","estado_fisico":"bueno","encendido":"si","fallas":"audio","ram":"4GB","almacenamiento":"64GB","descripcion":"Problema audio","destino":"Reparación","prediccion_ml":"Reparación"},
        {"id_usuario": "4","nombre_usuario":"Cliente D","tipo_usuario":"cliente","tipo":"Celular","marca":"Generic","modelo":"Modelo X","anio":"2015","estado_fisico":"dañado","encendido":"no","fallas":"muy viejo","ram":"1GB","almacenamiento":"8GB","descripcion":"Obsoleto","destino":"Reciclaje","prediccion_ml":"Reciclaje"},
    ])
    df.to_csv(target_path, sep=';', index=False)
    return target_path

def load_data():
    for p in DATA_PATHS:
        if p.exists():
            print("Cargando datos desde:", p)
            return pd.read_csv(p, sep=';')
    # no existe: crear ejemplo en data/
    sample_path = DATA_PATHS[0]
    create_sample_csv(sample_path)
    return pd.read_csv(sample_path, sep=';')

def prepare(df: pd.DataFrame):
    if 'modelo' not in df.columns or 'prediccion_ml' not in df.columns:
        raise ValueError("CSV debe contener las columnas 'modelo' y 'prediccion_ml'")
    df = df[['modelo','prediccion_ml']].dropna()
    df = df[df['modelo'].astype(str).str.strip() != '']
    df = df[df['prediccion_ml'].astype(str).str.strip() != '']
    if df.empty:
        raise ValueError("No hay filas válidas en 'modelo' / 'prediccion_ml'")
    return df['modelo'].astype(str), df['prediccion_ml'].astype(str)

def train_and_save(X, y):
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    tfidf = TfidfVectorizer(max_features=200, ngram_range=(1,2))
    X_tfidf = tfidf.fit_transform(X)

    # si hay al menos 2 clases y suficientes muestras, stratify; si no, entrenar con todo
    try:
        if len(set(y_enc)) > 1 and len(y_enc) >= 5:
            X_train, X_test, y_train, y_test = train_test_split(X_tfidf, y_enc, test_size=0.2, random_state=42, stratify=y_enc)
        else:
            X_train, y_train = X_tfidf, y_enc
            X_test = y_test = None
    except Exception:
        X_train, y_train = X_tfidf, y_enc
        X_test = y_test = None

    model = RandomForestClassifier(n_estimators=150, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    if X_test is not None:
        preds = model.predict(X_test)
        print("Reporte de clasificación (test):")
        print(classification_report(y_test, preds, zero_division=0))

    joblib.dump(model, MODEL_FILENAME)
    joblib.dump(tfidf, VECTORIZER_FILENAME)
    joblib.dump(le, ENCODER_FILENAME)
    print("Artefactos guardados:")
    print(" ", MODEL_FILENAME)
    print(" ", VECTORIZER_FILENAME)
    print(" ", ENCODER_FILENAME)
    print("\nPara probar el modelo, ejecuta: python app.py y abre http://127.0.0.1:5000/interfaz")

def main():
    df = load_data()
    X, y = prepare(df)
    print(f"Registros disponibles para entrenamiento: {len(X)}")
    train_and_save(X, y)

if __name__ == "__main__":
    main()
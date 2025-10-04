from flask import Flask
from flask import Flask, render_template


# Crear la aplicación
app = Flask(__name__)

# Ruta principal
@app.route('/')
def Index():
     Myname= "Flask"
     return render_template('Index.html', name=Myname)

if __name__ == '__main__':
    app.run(debug=True)

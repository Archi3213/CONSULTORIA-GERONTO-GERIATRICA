from flask import Flask, render_template, request, redirect, url_for
import uuid  # Importar el módulo uuid para generar IDs únicos

app = Flask(__name__)

# Crear una lista para almacenar los pacientes registrados (simulado)
pacientes_registrados = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Tu código para el inicio de sesión aquí
    return render_template('login.html')

@app.route('/options')
def options():
    # Tu código para las opciones de registro y consulta aquí
    return render_template('options.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro_paciente():
    if request.method == 'POST':
        # Obtener los datos del formulario
        apellidos = request.form['apellidos']
        nombres = request.form['nombres']
        fecha_nacimiento = request.form['fecha_nacimiento']
        celular = request.form['celular']
        turno = request.form['turno']
        genero = request.form['genero']
        fecha_registro = request.form['fecha_registro']
        registrado_por = request.form['registrado_por']

        # Generar un ID único para el paciente
        id_paciente = str(uuid.uuid4())[:8]  # Obtener los primeros 8 caracteres del ID

        # Crear un diccionario con los datos del paciente
        paciente = {
            'id': id_paciente,
            'apellidos': apellidos,
            'nombres': nombres,
            'fecha_nacimiento': fecha_nacimiento,
            'celular': celular,
            'turno': turno,
            'genero': genero,
            'fecha_registro': fecha_registro,
            'registrado_por': registrado_por
        }

        # Agregar el paciente a la lista de pacientes registrados
        pacientes_registrados.append(paciente)

        # Redirigir a la página de registro exitoso y pasar los datos del paciente
        return redirect(url_for('registro_exitoso', id_paciente=id_paciente, nombre_paciente=f'{nombres} {apellidos}'))

    return render_template('registro_paciente.html')

@app.route('/registro_exitoso')
def registro_exitoso():
    id_paciente = request.args.get('id_paciente')
    nombre_paciente = request.args.get('nombre_paciente')
    return render_template('registro_exitoso.html', id_paciente=id_paciente, nombre_paciente=nombre_paciente)

if __name__ == '__main__':
    app.run(debug=True)

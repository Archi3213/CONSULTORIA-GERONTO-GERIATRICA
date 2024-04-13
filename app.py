from flask import Flask, render_template, request, redirect, url_for
import uuid  # Importar el módulo uuid para generar IDs únicos

app = Flask(__name__)

# Crear una lista para almacenar los pacientes registrados (simulado)
pacientes_registrados = []

@app.route('/')
def index():
    return render_template('index.html')

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Usuarios y contraseñas permitidos (puedes agregar más si lo necesitas)
users = {'vespertino': 'vespertino', '1': '1'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            return redirect(url_for('options'))
        else:
            error = 'Usuario o contraseña incorrectos'
            return render_template('login.html', error=error)
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
        peso = request.form['peso']
        altura = request.form['altura']
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
            'peso': peso,
            'altura': altura,
            'turno': turno,
            'genero': genero,
            'fecha_registro': fecha_registro,
            'registrado_por': registrado_por
        }

        # Agregar el paciente a la lista de pacientes registrados
        pacientes_registrados.append(paciente)

        # Redirigir a la página de registro exitoso y pasar los datos del paciente
        return redirect(url_for('registro_exitoso', id_paciente=id_paciente, nombre_paciente=f'{nombres} {apellidos}'))

    return render_template('registro.html')


@app.route('/registro_exitoso')
def registro_exitoso():
    id_paciente = request.args.get('id_paciente')
    nombre_paciente = request.args.get('nombre_paciente')
    return render_template('registro_exitoso.html', id_paciente=id_paciente, nombre_paciente=nombre_paciente)

if __name__ == '__main__':
    app.run(debug=True)
pacientes_registrados = [
    {
        'id': '1',
        'apellidos': 'García',
        'nombres': 'Juan',
        'fecha_nacimiento': '1990-05-15',
        'celular': '555-1234',
        'turno': 'matutino',
        'genero': 'masculino',
        'fecha_registro': '2024-04-15',
        'registrado_por': 'Mariana'
    },
    {
        'id': '2',
        'apellidos': 'López',
        'nombres': 'María',
        'fecha_nacimiento': '1985-10-20',
        'celular': '555-5678',
        'turno': 'vespertino',
        'genero': 'femenino',
        'fecha_registro': '2024-04-16',
        'registrado_por': 'Pedro'
    }
]

@app.route('/consulta')
def consulta_paciente():
    return render_template('consulta_paciente.html', pacientes=pacientes_registrados)

@app.route('/paciente/<id>')
def detalle_paciente(id):
    paciente = next((p for p in pacientes_registrados if p['id'] == id), None)
    if paciente:
        return render_template('detalle_paciente.html', paciente=paciente)
    else:
        return 'Paciente no encontrado'

@app.route('/actualizar_paciente/<id>', methods=['POST'])
def actualizar_paciente(id):
    peso = request.form['peso']
    masa_muscular = request.form['masa_muscular']
    cita = request.form['cita']

    # Aquí puedes agregar la lógica para actualizar los datos del paciente en la base de datos

    return redirect(url_for('detalle_paciente', id=id))

if __name__ == '__main__':
    app.run(debug=True)
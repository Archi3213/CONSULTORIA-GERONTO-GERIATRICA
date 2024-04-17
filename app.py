from flask import Flask, render_template, request, redirect, url_for
import uuid  # Importar el módulo uuid para generar IDs únicos
import calendar

app = Flask(__name__)

# Crear una lista para almacenar los pacientes registrados (simulado)
pacientes_registrados = [
    {
        'id': '1',
        'primer_apellido': 'interian',
        'segundo_apellido': 'correa',
        'nombres': 'xochitl ',
        'fecha_nacimiento': '1990-05-15',
        'celular': '555-1234',
        'turno': 'matutino',
        'genero': 'masculino',
        'fecha_registro': '2024-04-15',
        'registrado_por': 'Mariana'
    },
    {
        'id': '2',
        'primer_apellido': 'López',
        'segundo_apellido': 'PARRA',
        'nombres': 'María',
        'fecha_nacimiento': '1985-10-20',
        'celular': '555-5678',
        'turno': 'vespertino',
        'peso': '82',
        'altura': '152',
        'turno': 'vespertino',
        'genero': 'femenino',
        'fecha_registro': '2024-04-16',
        'registrado_por': 'Pedro'
    },
        {
        'id': '3',
        'primer_apellido': 'López',
        'segundo_apellido': 'PARRA',
        'nombres': 'María',
        'fecha_nacimiento': '1985-10-20',
        'celular': '555-5678',
        'turno': 'vespertino',
        'peso': '82',
        'altura': '152',
        'turno': 'vespertino',
        'genero': 'femenino',
        'fecha_registro': '2024-04-16',
        'registrado_por': 'Pedro'
    }
]

@app.route('/')
def index():
    return render_template('index.html')

# Usuarios y contraseñas permitidos (puedes agregar más si lo necesitas)
users = {'vespertino': 'vespertino', '1': '1'}

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
#inicia el apartado de opciones
@app.route('/options')
def options():

    # Generar el calendario
    year = 2024
    month = 4
    cal = calendar.month(year, month)

    return render_template('options.html', calendar=cal)

@app.route('/registro', methods=['GET', 'POST'])
def registro_paciente():
    if request.method == 'POST':
        # Obtener los datos del formulario
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']                      
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
            'primer_apellido': primer_apellido,
            'segundo_apellido': segundo_apellido,
            'apellidos': primer_apellido + segundo_apellido,
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
        return redirect(url_for('registro_exitoso', id_paciente=id_paciente, nombres_paciente=nombres+primer_apellido+segundo_apellido))
    return render_template('registro.html')

@app.route('/registro_exitoso')
def registro_exitoso():
    id_paciente = request.args.get('id_paciente')
    nombre_paciente = request.args.get('nombre_paciente')
    return render_template('registro_exitoso.html', id_paciente=id_paciente, nombre_paciente=nombre_paciente)

@app.route('/consultar')
def consulta_paciente():
    return render_template('consultar.html', pacientes=pacientes_registrados)

@app.route('/paciente/<id>')
def detalle_paciente(id):
    paciente = next((p for p in pacientes_registrados if p['id'] == id), None)
    if paciente:
        return render_template('detalle.html', paciente=paciente)
    else:
        return 'Paciente no encontrado'

@app.route('/actualizar/<id>', methods=['POST'])
def actualizar_paciente(id):
    peso = request.form['peso']
    masa_muscular = request.form['masa_muscular']
    cita = request.form['cita']

    # Aquí puedes agregar la lógica para actualizar los datos del paciente en la base de datos

    return redirect(url_for('detalle_paciente', id=id))

if __name__ == '__main__':
    app.run(debug=True)
@app.route('/agendar_cita')
def agendar_cita():
    return render_template('agendar_cita.html')

@app.route('/historial_citas')
def historial_citas():
    return render_template('historial_citas.html')

if __name__ == '__main__':
    app.run(debug=True)
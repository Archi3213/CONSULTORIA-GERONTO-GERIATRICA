from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
import calendar
import datetime
import hashlib  # Para generar hashes de contraseñas
import sqlite3
import uuid  # Para generar identificadores únicos

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

now = datetime.datetime.now()
year = now.year
month = now.month

cal = calendar.monthcalendar(year, month)
html_calendar = "<tr>"
for week in cal:
    for day in week:
        if day == 0:
            html_calendar += "<td></td>"
        else:
            html_calendar += f"<td>{day}</td>"
    html_calendar += "</tr><tr>"
html_calendar = html_calendar[:-4]

conexion = sqlite3.connect('nutricion_consulta.db')
cursor = conexion.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                    id TEXT PRIMARY KEY,
                    primer_apellido TEXT NOT NULL,
                    segundo_apellido TEXT NOT NULL,
                    nombres TEXT NOT NULL,
                    fecha_nacimiento TEXT NOT NULL,
                    celular TEXT NOT NULL,
                    turno TEXT NOT NULL,
                    genero TEXT NOT NULL,
                    peso REAL NOT NULL,
                    altura REAL NOT NULL,
                    imc REAL NOT NULL,
                    fecha_registro TEXT NOT NULL,
                    registrado_por TEXT NOT NULL
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )''')

hashed_password_matutino = hashlib.sha256(b'MATUTINO').hexdigest()
hashed_password_vespertino = hashlib.sha256(b'VESPERTINO').hexdigest()

cursor.execute("INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)", ('MATUTINO', hashed_password_matutino))
cursor.execute("INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)", ('VESPERTINO', hashed_password_vespertino))

conexion.commit()
cursor.close()

pacientes_registrados = []

# Función para verificar la sesión antes de acceder a las rutas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Crear una nueva conexión y cursor aquí dentro de la función login
        conexion = sqlite3.connect('nutricion_consulta.db')
        cursor = conexion.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()

        # Cerrar la conexión y el cursor después de usarlos
        cursor.close()
        conexion.close()

        # Verificar credenciales y gestionar la sesión
        if (user and hashlib.sha256(password.encode()).hexdigest() == user[1]) or (username == 'MATUTINO' and password == 'MATUTINO'):
            session['username'] = username
            return redirect(url_for('options'))
        else:
            error = 'Usuario o contraseña incorrectos'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/options')
@login_required
def options():
    return render_template('options.html', calendar=cal)

@app.route('/registro', methods=['GET', 'POST'])
@login_required
def registro_paciente():
    if request.method == 'POST':
        primer_apellido = request.form['primer_apellido'].upper()
        segundo_apellido = request.form['segundo_apellido'].upper()
        nombres = request.form['nombres'].upper()
        fecha_nacimiento = request.form['fecha_nacimiento']
        celular = request.form['celular']
        turno = request.form['turno'].upper()
        genero = request.form['genero'].upper()
        peso = float(request.form.get('peso', ''))  # Convertir a float
        altura = float(request.form.get('altura', ''))  # Convertir a float
        fecha_registro = request.form['fecha_registro']
        registrado_por = request.form['registrado_por'].upper()

        # Generar un ID único para el paciente
        id_parte1 = primer_apellido[:2].upper() + segundo_apellido[:2].upper() + nombres[:2].upper()
        fecha_nacimiento_dt = datetime.datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        id_parte2 = f"{fecha_nacimiento_dt.day:02}{fecha_nacimiento_dt.month:02}{fecha_nacimiento_dt.year % 100:02}"
        id_paciente = id_parte1 + id_parte2
        altura1 = altura / 100
        altura2 = altura1 * altura1
        imc = peso / altura2

        # Crear una nueva conexión y cursor aquí dentro de la función registro_paciente
        conexion_registro = sqlite3.connect('nutricion_consulta.db')
        cursor_registro = conexion_registro.cursor()

        # Insertar los datos en la tabla de pacientes
        cursor_registro.execute('''INSERT INTO pacientes (id, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (id_paciente, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por))
        conexion_registro.commit()
        cursor_registro.close()
        conexion_registro.close()

        paciente = {
            'id': id_paciente,
            'primer_apellido': primer_apellido,
            'segundo_apellido': segundo_apellido,
            'nombres': nombres,
            'fecha_nacimiento': fecha_nacimiento,
            'celular': celular,
            'turno': turno,
            'genero': genero,
            'peso': peso,
            'altura': altura,
            'imc': imc,
            'fecha_registro': fecha_registro,
            'registrado_por': registrado_por
        }

        pacientes_registrados.append(paciente)

        return redirect(url_for('registro_exitoso', id_paciente=id_paciente, nombre_paciente=f"{nombres} {primer_apellido} {segundo_apellido}"))
    return render_template('registro.html')



@app.route('/registro_exitoso')
def registro_exitoso():
    id_paciente = request.args.get('id_paciente')
    nombre_paciente = request.args.get('nombre_paciente')
    return render_template('registro_exitoso.html', id_paciente=id_paciente, nombre_paciente=nombre_paciente)

@app.route('/consultar', methods=['GET', 'POST'])
@login_required
def consulta_paciente():
    if request.method == 'POST':
        filter_text = request.form['filter_text']
        filter_by = request.form['filter_by']  # Nuevo campo para determinar el filtro por apellidos o por ID

        # Conectarse a la base de datos y ejecutar la consulta
        conexion_consulta = sqlite3.connect('nutricion_consulta.db')
        cursor_consulta = conexion_consulta.cursor()

        # Ejecutar la consulta según el filtro seleccionado
        if filter_by == 'apellidos':
            cursor_consulta.execute("SELECT * FROM pacientes WHERE primer_apellido || ' ' || segundo_apellido LIKE ?", ('%' + filter_text + '%',))
        elif filter_by == 'id':
            cursor_consulta.execute("SELECT * FROM pacientes WHERE id LIKE ?", ('%' + filter_text + '%',))
        else:
            cursor_consulta.execute("SELECT * FROM pacientes")

        # Obtener los resultados de la consulta
        pacientes = cursor_consulta.fetchall()

        # Cerrar la conexión y el cursor
        cursor_consulta.close()
        conexion_consulta.close()

        return render_template('consultar.html', pacientes=pacientes, filter_text=filter_text, filter_by=filter_by)
    
    # Si es una solicitud GET, mostrar todos los pacientes
    conexion_consulta = sqlite3.connect('nutricion_consulta.db')
    cursor_consulta = conexion_consulta.cursor()
    cursor_consulta.execute("SELECT * FROM pacientes")
    pacientes = cursor_consulta.fetchall()
    cursor_consulta.close()
    conexion_consulta.close()

    return render_template('consultar.html', pacientes=pacientes)
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


@app.route('/agendar_cita', methods=['GET', 'POST'])
def agendar_cita():
    if request.method == 'POST':
        paciente_id = request.form['paciente']
        fecha_consulta = request.form['fecha_consulta']
        
        # Generar un identificador único para la cita
        cita_id = str(uuid.uuid4())

        for paciente in pacientes_registrados:
            if paciente['id'] == paciente_id:
                if 'citas' not in paciente:
                    paciente['citas'] = []
                paciente['citas'].append({
                    'id': cita_id,  # Agregar el identificador único
                    'fecha_consulta': fecha_consulta,
                    'observaciones': ''  # Puedes agregar más campos según sea necesario
                })
                break
        
        return redirect(url_for('historial_citas'))
    else:
        return render_template('agendar_cita.html', pacientes=pacientes_registrados)

@app.route('/historial_citas')
def historial_citas():
    citas = []
    for paciente in pacientes_registrados:
        if 'citas' in paciente:
            for cita in paciente['citas']:
                estado = cita.get('estado', 'Pendiente')
                citas.append({
                    'id': cita['id'],  
                    'paciente_id': paciente['id'],
                    'nombre_paciente': f"{paciente['nombres']} {paciente['primer_apellido']} {paciente['segundo_apellido']}",
                    'fecha_consulta': cita['fecha_consulta'],
                    'observaciones': cita['observaciones'],
                    'estado': estado  
                })
    return render_template('historial_citas.html', citas=citas)

@app.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    cita_id = request.form.get('cita_id')
    nuevo_estado = request.form.get('estado')

    for paciente in pacientes_registrados:
        if 'citas' in paciente:
            for cita in paciente['citas']:
                if cita['id'] == cita_id:
                    cita['estado'] = nuevo_estado

    return redirect(url_for('historial_citas'))

@app.route('/directorio_pacientes')
def directorio_pacientes():
    return render_template('directorio_pacientes.html', pacientes=pacientes_registrados)

if __name__ == '__main__':
    app.run(debug=True)

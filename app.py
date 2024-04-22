from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
import calendar
import datetime
import hashlib  # Para generar hashes de contraseñas
import sqlite3

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
                    registrado_por TEXT NOT NULL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL )''')
hashed_password_matutino = hashlib.sha256(b'MATUTINO').hexdigest()
hashed_password_vespertino = hashlib.sha256(b'VESPERTINO').hexdigest()
cursor.execute("INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)", ('MATUTINO', hashed_password_matutino))
cursor.execute("INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)", ('VESPERTINO', hashed_password_vespertino))

cursor.execute('''CREATE TABLE IF NOT EXISTS citas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id TEXT,
                    fecha_consulta TEXT NOT NULL,
                    hora_consulta TEXT NOT NULL, 
                    observaciones TEXT,
                    estado TEXT DEFAULT 'Pendiente',
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
                )''')
conexion.commit()
cursor.close()

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

        conexion = sqlite3.connect('nutricion_consulta.db')
        cursor = conexion.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()

        cursor.close()
        conexion.close()

        if user and hashlib.sha256(password.encode()).hexdigest() == user[1]:
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

        id_parte1 = primer_apellido[:2].upper() + segundo_apellido[:2].upper() + nombres[:2].upper()
        fecha_nacimiento_dt = datetime.datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        id_parte2 = f"{fecha_nacimiento_dt.day:02}{fecha_nacimiento_dt.month:02}{fecha_nacimiento_dt.year % 100:02}"
        id_paciente = id_parte1 + id_parte2
        altura1 = altura / 100
        altura2 = altura1 * altura1
        imc = peso / altura2

        conexion_registro = sqlite3.connect('nutricion_consulta.db')
        cursor_registro = conexion_registro.cursor()

        cursor_registro.execute('''INSERT INTO pacientes (id, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (id_paciente, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por))
        conexion_registro.commit()
        cursor_registro.close()
        conexion_registro.close()

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
        filter_by = request.form['filter_by']

        conexion_consulta = sqlite3.connect('nutricion_consulta.db')
        cursor_consulta = conexion_consulta.cursor()

        if filter_by == 'apellidos':
            cursor_consulta.execute("SELECT * FROM pacientes WHERE primer_apellido || ' ' || segundo_apellido LIKE ?", ('%' + filter_text + '%',))
        elif filter_by == 'id':
            cursor_consulta.execute("SELECT * FROM pacientes WHERE id LIKE ?", ('%' + filter_text + '%',))
        else:
            cursor_consulta.execute("SELECT * FROM pacientes")

        pacientes = cursor_consulta.fetchall()

        cursor_consulta.close()
        conexion_consulta.close()

        return render_template('consultar.html', pacientes=pacientes, filter_text=filter_text, filter_by=filter_by)
    
    conexion_consulta = sqlite3.connect('nutricion_consulta.db')
    cursor_consulta = conexion_consulta.cursor()
    cursor_consulta.execute("SELECT * FROM pacientes")
    pacientes = cursor_consulta.fetchall()
    cursor_consulta.close()
    conexion_consulta.close()

    return render_template('consultar.html', pacientes=pacientes)

@app.route('/paciente/<id>')
def detalle_paciente(id):
    conexion = sqlite3.connect('nutricion_consulta.db')
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM pacientes WHERE id=?", (id,))
    paciente = cursor.fetchone()

    cursor.close()
    conexion.close()

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
@login_required #cambiar por una automplete de los nombres con id
#hacerlo por id unicamente
def agendar_cita():
    if request.method == 'POST':
        if 'paciente_id' in request.form:
            paciente_id = request.form['paciente_id']
            fecha_consulta = request.form['fecha_consulta']
            hora_cita = request.form['hora_consulta']

            conexion = sqlite3.connect('nutricion_consulta.db')
            cursor = conexion.cursor()

            cursor.execute('''INSERT INTO citas (paciente_id, fecha_consulta, hora_consulta) 
                            VALUES (?, ?, ?)''', 
                            (paciente_id, fecha_consulta, hora_cita))
            conexion.commit()
            cursor.close()
            conexion.close()

            return redirect(url_for('historial_citas'))
        else:
            error_message = "Error: No se ha proporcionado el ID del paciente."
            return render_template('agendar_cita.html', error_message=error_message)
    else:
        conexion_pacientes = sqlite3.connect('nutricion_consulta.db')
        cursor_pacientes = conexion_pacientes.cursor()
        cursor_pacientes.execute("SELECT id, nombres FROM pacientes")
        pacientes = cursor_pacientes.fetchall()
        cursor_pacientes.close()
        conexion_pacientes.close()

        return render_template('agendar_cita.html', pacientes=pacientes)
app.route('/historial_citas', methods=['GET', 'POST'])
def historial_citas():
    conexion = sqlite3.connect('nutricion_consulta.db')
    cursor = conexion.cursor()

    cursor.execute('''SELECT citas.id, pacientes.id, pacientes.nombres, 
                      pacientes.primer_apellido, pacientes.segundo_apellido,
                      citas.fecha_consulta, citas.hora_consulta, citas.observaciones, citas.estado
                      FROM citas JOIN pacientes ON citas.paciente_id = pacientes.id''')
    
    citas = cursor.fetchall()

    # Si se envía el formulario para cambiar el estado
    if request.method == 'POST':
        id_cita = request.form['id_cita']
        nuevo_estado = request.form['nuevo_estado']
        cursor.execute('''UPDATE citas SET estado = ? WHERE id = ?''', (nuevo_estado, id_cita))
        conexion.commit()

    cursor.close()
    conexion.close()

    return render_template('historial_citas.html', citas=citas)

@app.route('/historial_citas', methods=['GET', 'POST'])
def historial_citas():
    if request.method == 'POST':
        id_cita = request.form.get('id_cita')
        nuevo_estado = request.form.get('nuevo_estado')
        if id_cita and nuevo_estado:
            with sqlite3.connect('nutricion_consulta.db') as conexion:
                cursor = conexion.cursor()
                cursor.execute('''UPDATE citas SET estado = ? WHERE id = ?''', (nuevo_estado, id_cita))
                conexion.commit()

    with sqlite3.connect('nutricion_consulta.db') as conexion:
        cursor = conexion.cursor()
        cursor.execute('''SELECT citas.id, pacientes.id, pacientes.primer_apellido || ' ' || pacientes.segundo_apellido || ', ' || pacientes.nombres as nombre_completo, 
                          pacientes.fecha_nacimiento, citas.fecha_consulta, citas.hora_consulta, citas.observaciones, citas.estado
                          FROM citas JOIN pacientes ON citas.paciente_id = pacientes.id''')
        citas = cursor.fetchall()

    return render_template('historial_citas.html', citas=citas)

@app.route('/directorio_pacientes', methods=['GET', 'POST'])
def directorio_pacientes():
    if request.method == 'POST':
        filter_text = request.form['filter_text']
        filter_by = request.form['filter_by']

        conexion = sqlite3.connect('nutricion_consulta.db')
        cursor = conexion.cursor()

        if filter_by == 'apellidos':
            cursor.execute("SELECT * FROM pacientes WHERE primer_apellido || ' ' || segundo_apellido LIKE ?", ('%' + filter_text + '%',))
        elif filter_by == 'id':
            cursor.execute("SELECT * FROM pacientes WHERE id LIKE ?", ('%' + filter_text + '%',))
        else:
            cursor.execute("SELECT * FROM pacientes")

        pacientes = cursor.fetchall()

        cursor.close()
        conexion.close()

        return render_template('directorio_pacientes.html', pacientes=pacientes)
    
    conexion = sqlite3.connect('nutricion_consulta.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pacientes")
    pacientes = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template('directorio_pacientes.html', pacientes=pacientes)

if __name__ == '__main__':
    app.run(debug=True)
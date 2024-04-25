from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import hashlib
import sqlite3
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def get_db_connection():
    return sqlite3.connect('nutricion_consulta.db')

def get_hashed_password(password, salt=None):
    if not salt:
        salt = hashlib.sha256(b'SALT').hexdigest()
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed_password.hex()

def verify_password(stored_hash, salt, provided_password):
    return stored_hash == get_hashed_password(provided_password, salt)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

conexion = sqlite3.connect('nutricion_consulta.db')
cursor = conexion.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                    id TEXT PRIMARY KEY,
                    primer_apellido TEXT NOT NULL,
                    segundo_apellido TEXT NOT NULL,
                    nombres TEXT NOT NULL,
                    fecha_nacimiento TEXT NOT NULL,
                    celular TEXT NOT NULL,
                    religion TEXT,
                    ocupacion TEXT,
                    escolaridad TEXT,
                    estado_civil TEXT,
                    servicio_salud TEXT,
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

cursor.execute('''CREATE TABLE IF NOT EXISTS expedientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id TEXT,
                    motivo_consulta TEXT,
                    quien_remitio TEXT,
                    patologias TEXT,
                    antecedentes_patologicos TEXT,
                    tiempo_diagnostico TEXT,
                    medicamentos TEXT,
                    discapacidad TEXT,
                    cirugias TEXT,
                    alergia TEXT,
                    factor_digestivo TEXT,
                    consume_alcohol TEXT,
                    consume_tabaco TEXT,
                    consume_suplementos TEXT,
                    consume_cafeina TEXT,
                    observaciones_no_patologicas TEXT,
                    horas_sueno TEXT,
                    hora_sueno TEXT,
                    toma_siestas TEXT,
                    tiempo_siestas TEXT,
                    duracion_actividad_fisica TEXT,
                    tipo_actividad_fisica TEXT,
                    frecuencia_actividad_fisica TEXT,
                    estado_piel TEXT,
                    estado_ojos TEXT,
                    estado_unas TEXT,
                    estado_cabello TEXT,
                    estado_boca TEXT,
                    estado_dientes TEXT,
                    hb TEXT,
                    hto TEXT,
                    colesterol TEXT,
                    trigliceridos TEXT,
                    glucosa TEXT,
                    urea TEXT,
                    creatinina TEXT,
                    ac_urico TEXT,
                    otros_bioquimica TEXT,
                    orientacion_alimentaria TEXT,
                    intolerancia TEXT,
                    alergia_alimentaria TEXT,
                    consumo_agua TEXT,
                    dinero_alimentacion TEXT,
                    personas_alimentacion TEXT,
                    quien_prepara TEXT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
                )''')

conexion.commit()

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
    return render_template('options.html')

@app.route('/registro', methods=['GET', 'POST'])
@login_required
def registro_paciente():
    if request.method == 'POST':
        primer_apellido = request.form['primer_apellido'].upper()
        segundo_apellido = request.form['segundo_apellido'].upper()
        nombres = request.form['nombres'].upper()
        fecha_nacimiento = request.form['fecha_nacimiento']
        celular = request.form['celular']
        religion = request.form['religion'].upper()
        ocupacion = request.form['ocupacion'].upper()
        escolaridad = request.form['escolaridad'].upper() 
        estado_civil = request.form['estado_civil'].upper() 
        servicio_salud = request.form['servicio_salud'].upper()
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

        cursor_registro.execute('''INSERT INTO pacientes (id, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, celular, religion, ocupacion, escolaridad, estado_civil, servicio_salud, turno, genero, peso, altura, imc, fecha_registro, registrado_por) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (id_paciente, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, celular, religion, ocupacion, escolaridad, estado_civil, servicio_salud, turno, genero, peso, altura, imc, fecha_registro, registrado_por))
        conexion_registro.commit()
        cursor_registro.close()
        conexion_registro.close()

        return redirect(url_for('pagina_registro_exitoso'))

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
        cursor.execute('''SELECT citas.id, pacientes.id, pacientes.primer_apellido || ' ' || pacientes.segundo_apellido || ' ' || pacientes.nombres as nombre_completo, 
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
    

def solicitar_datos():
    expediente = {}

    expediente['paciente_id'] = request.form['paciente_id']
    expediente['religion'] = request.form['religion']
    expediente['ocupacion'] = request.form['ocupacion']
    expediente['escolaridad'] = request.form['escolaridad']
    expediente['estado_civil'] = request.form['estado_civil']
    expediente['motivo_consulta'] = request.form['motivo_consulta']
    expediente['quien_remitio'] = request.form['quien_remitio']
    expediente['servicio_salud'] = request.form['servicio_salud']
    expediente['patologias'] = request.form['patologias']
    expediente['antecedentes_patologicos'] = request.form['antecedentes_patologicos']
    expediente['tiempo_diagnostico'] = request.form['tiempo_diagnostico']
    expediente['medicamentos'] = request.form['medicamentos']
    expediente['discapacidad'] = request.form['discapacidad']
    expediente['cirugias'] = request.form['cirugias']
    expediente['alergia'] = request.form['alergia']
    expediente['factor_digestivo'] = request.form['factor_digestivo']
    expediente['consume_alcohol'] = request.form['consume_alcohol']
    expediente['consume_tabaco'] = request.form['consume_tabaco']
    expediente['consume_suplementos'] = request.form['consume_suplementos']
    expediente['consume_cafeina'] = request.form['consume_cafeina']
    expediente['observaciones_no_patologicas'] = request.form['observaciones_no_patologicas']
    expediente['horas_sueno'] = request.form['horas_sueno']
    expediente['hora_sueno'] = request.form['hora_sueno']
    expediente['toma_siestas'] = request.form['toma_siestas']
    expediente['tiempo_siestas'] = request.form['tiempo_siestas']
    expediente['duracion_actividad_fisica'] = request.form['duracion_actividad_fisica']
    expediente['tipo_actividad_fisica'] = request.form['tipo_actividad_fisica']
    expediente['frecuencia_actividad_fisica'] = request.form['frecuencia_actividad_fisica']
    expediente['estado_piel'] = request.form['estado_piel']
    expediente['estado_ojos'] = request.form['estado_ojos']
    expediente['estado_unas'] = request.form['estado_unas']
    expediente['estado_cabello'] = request.form['estado_cabello']
    expediente['estado_boca'] = request.form['estado_boca']
    expediente['estado_dientes'] = request.form['estado_dientes']
    expediente['hb'] = request.form['hb']
    expediente['hto'] = request.form['hto']
    expediente['colesterol'] = request.form['colesterol']
    expediente['trigliceridos'] = request.form['trigliceridos']
    expediente['glucosa'] = request.form['glucosa']
    expediente['urea'] = request.form['urea']
    expediente['creatinina'] = request.form['creatinina']
    expediente['ac_urico'] = request.form['ac_urico']
    expediente['otros_bioquimica'] = request.form['otros_bioquimica']
    expediente['orientacion_alimentaria'] = request.form['orientacion_alimentaria']
    expediente['intolerancia'] = request.form['intolerancia']
    expediente['alergia_alimentaria'] = request.form['alergia_alimentaria']
    expediente['consumo_agua'] = request.form['consumo_agua']
    expediente['dinero_alimentacion'] = request.form['dinero_alimentacion']
    expediente['personas_alimentacion'] = request.form['personas_alimentacion']
    expediente['quien_prepara'] = request.form['quien_prepara']

    return expediente

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/crear_expediente', methods=['GET', 'POST'])
@login_required
def crear_expediente():
    if request.method == 'POST':
        expediente = solicitar_datos()
        print(expediente)  # Solo para verificar que se reciben los datos correctamente

        # Aquí puedes agregar lógica para guardar los datos del expediente en la base de datos
        conexion = get_db_connection()
        cursor = conexion.cursor()
        cursor.execute('''INSERT INTO expedientes (
                            paciente_id, religion, ocupacion, escolaridad, estado_civil, 
                            motivo_consulta, quien_remitio, servicio_salud, patologias, 
                            antecedentes_patologicos, tiempo_diagnostico, medicamentos, 
                            discapacidad, cirugias, alergia, factor_digestivo, consume_alcohol, 
                            consume_tabaco, consume_suplementos, consume_cafeina, 
                            observaciones_no_patologicas, horas_sueno, hora_sueno, toma_siestas, 
                            tiempo_siestas, duracion_actividad_fisica, tipo_actividad_fisica, 
                            frecuencia_actividad_fisica, estado_piel, estado_ojos, estado_unas, 
                            estado_cabello, estado_boca, estado_dientes, hb, hto, colesterol, 
                            trigliceridos, glucosa, urea, creatinina, ac_urico, otros_bioquimica, 
                            orientacion_alimentaria, intolerancia, alergia_alimentaria, consumo_agua, 
                            dinero_alimentacion, personas_alimentacion, quien_prepara
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (expediente['paciente_id'], expediente['religion'], expediente['ocupacion'],
                        expediente['escolaridad'], expediente['estado_civil'], expediente['motivo_consulta'],
                        expediente['quien_remitio'], expediente['servicio_salud'], expediente['patologias'],
                        expediente['antecedentes_patologicos'], expediente['tiempo_diagnostico'],
                        expediente['medicamentos'], expediente['discapacidad'], expediente['cirugias'],
                        expediente['alergia'], expediente['factor_digestivo'], expediente['consume_alcohol'],
                        expediente['consume_tabaco'], expediente['consume_suplementos'], expediente['consume_cafeina'],
                        expediente['observaciones_no_patologicas'], expediente['horas_sueno'], expediente['hora_sueno'],
                        expediente['toma_siestas'], expediente['tiempo_siestas'], expediente['duracion_actividad_fisica'],
                        expediente['tipo_actividad_fisica'], expediente['frecuencia_actividad_fisica'], expediente['estado_piel'],
                        expediente['estado_ojos'], expediente['estado_unas'], expediente['estado_cabello'],
                        expediente['estado_boca'], expediente['estado_dientes'], expediente['hb'], expediente['hto'],
                        expediente['colesterol'], expediente['trigliceridos'], expediente['glucosa'], expediente['urea'],
                        expediente['creatinina'], expediente['ac_urico'], expediente['otros_bioquimica'],
                        expediente['orientacion_alimentaria'], expediente['intolerancia'], expediente['alergia_alimentaria'],
                        expediente['consumo_agua'], expediente['dinero_alimentacion'], expediente['personas_alimentacion'],
                        expediente['quien_prepara']))
        conexion.commit()
        cursor.close()

        return redirect(url_for('detalle_expediente', paciente_id=expediente['paciente_id']))
    else:
        return render_template('crear_expediente.html')

if __name__ == '__main__':
    app.run(debug=True)
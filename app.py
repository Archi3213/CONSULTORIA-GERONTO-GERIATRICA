from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
import hashlib, sqlite3
from operator import itemgetter

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
                    id_paciente TEXT PRIMARY KEY,
                    primer_apellido TEXT NOT NULL,
                    segundo_apellido TEXT NOT NULL,
                    nombres TEXT NOT NULL,
                    fecha_nacimiento TEXT NOT NULL,
                    religion TEXT NOT NULL,
                    escolaridad TEXT NOT NULL,
                    ocupacion TEXT NOT NULL,
                    estado_civil TEXT NOT NULL,
                    servicio_salud TEXT NOT NULL,
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
cursor.execute('''CREATE TABLE IF NOT EXISTS citas (
                    id_cita INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_paciente TEXT,
                    fecha_consulta TEXT NOT NULL,
                    hora_consulta TEXT NOT NULL, 
                    observaciones TEXT,
                    estado TEXT DEFAULT 'Pendiente',
                    FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS antecedentes_familiares (
                    id_paciente PRIMARY KEY NOT NULL,
                    diabetes_mellitus_familiar TEXT,
                    dislipidemias_familiar TEXT,
                    sobrepeso_obesidad_familiar TEXT,
                    cancer_tipo_familiar TEXT,
                    hipertension_familiar TEXT,
                    cardiopatias_familiar TEXT,
                    litiasis_familiar TEXT,
                    artritis_familiar TEXT,
                    asma_familiar TEXT,
                    otras TEXT,
                    FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
                )''')

#cursor.execute('DROP TABLE IF EXISTS antecedentes_familiares')

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
    session.pop('username', None)  # Eliminar la clave 'username' de la sesión

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
    mensaje_error = None

    if request.method == 'POST':
        primer_apellido = request.form['primer_apellido'].upper()
        segundo_apellido = request.form['segundo_apellido'].upper()
        nombres = request.form['nombres'].upper()
        fecha_nacimiento = request.form['fecha_nacimiento']
        religion = request.form['religion'].upper()
        escolaridad = request.form['escolaridad'].upper()
        ocupacion = request.form['ocupacion'].upper()
        estado_civil = request.form['estado_civil'].upper()
        servicio_salud = request.form['servicio_salud'].upper()
        celular = request.form['celular']
        turno = request.form['turno'].upper()
        genero = request.form['genero'].upper()
        peso = float(request.form['peso'])
        altura = float(request.form['altura'])
        fecha_registro = request.form['fecha_registro']
        registrado_por = request.form['registrado_por'].upper()

        id_paciente = f"{primer_apellido[:2].upper()}{segundo_apellido[:2].upper()}{nombres[:2].upper()}{fecha_nacimiento.replace('-', '')}"
        altura_metros = altura / 100
        imc = peso / (altura_metros ** 2)

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_paciente FROM pacientes WHERE id_paciente = ?", (id_paciente,))
            if cursor.fetchone():
                mensaje_error = "El ID del paciente ya existe en la base de datos"
                id_paciente = f"{primer_apellido[:2].upper()}{segundo_apellido[:2].upper()}{nombres[:2].upper()}{fecha_nacimiento.replace('-', '')}"
            else:
                cursor.execute('''INSERT INTO pacientes (id_paciente, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, religion, escolaridad, ocupacion, estado_civil, servicio_salud, celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por) 
                                VALUES (?, ?, ?, ?,  ?, ?, ?, ?, ?,  ?, ?, ?, ?, ?,  ?, ?, ?, ?)''', 
                                (id_paciente, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, religion, escolaridad, ocupacion, estado_civil,  servicio_salud,  celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por))

        if mensaje_error:
            return render_template('registro.html', mensaje_error=mensaje_error)
        else:
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
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM pacientes")
        pacientes = cursor.fetchall()

    if request.method == 'POST':
        filter_text = request.form['filter_text']
        filter_by = request.form['filter_by']

        if filter_by == 'apellidos':
            pacientes = [paciente for paciente in pacientes if filter_text.lower() in f"{paciente[1]} {paciente[2]} {paciente[3]} ".lower()]
        elif filter_by == 'id_paciente':
            pacientes = [paciente for paciente in pacientes if filter_text.lower() in paciente[0].lower()]

    return render_template('consultar.html', pacientes=pacientes)


@app.route('/agendar_cita', methods=['GET', 'POST'])
@login_required
def agendar_cita():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        fecha_consulta = request.form['fecha_consulta']
        hora_consulta = request.form['hora_consulta']
        observaciones = request.form['observaciones']

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('''INSERT INTO citas (id_paciente, fecha_consulta, hora_consulta, observaciones) 
                            VALUES (?, ?, ?, ?)''', 
                            (id_paciente, fecha_consulta, hora_consulta, observaciones))

        return redirect(url_for('historial_citas'))
    
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()

    return render_template('agendar_cita.html', pacientes=pacientes)
@app.route('/historial_citas', methods=['GET', 'POST'])
@login_required
def historial_citas():
    filter_text = request.form.get('filter_text')
    filter_by = request.form.get('filter_by')

    with get_db_connection() as connection:
        cursor = connection.cursor()

        if request.method == 'POST' and filter_text and filter_by:
            if filter_by == 'id_paciente':
                cursor.execute("SELECT * FROM citas WHERE LOWER(id_paciente) LIKE LOWER(?)", ('%' + filter_text + '%',))
            elif filter_by == 'estado':
                cursor.execute("SELECT * FROM citas WHERE LOWER(estado) = LOWER(?)", (filter_text, ))
            else:
                cursor.execute("SELECT * FROM citas")
        else:
            cursor.execute("SELECT * FROM citas")

        citas = cursor.fetchall()
    with get_db_connection() as connection:
     cursor = connection.cursor()
    cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
    pacientes = cursor.fetchall()
    citas_ordenadas = sorted(citas, key=itemgetter(0), reverse=True)

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()

    return render_template('historial_citas.html', citas=citas_ordenadas, pacientes=pacientes)

    return render_template('historial_citas.html', citas=citas, pacientes=pacientes)
@app.route('/actualizar_estado', methods=['POST'])
@login_required
def actualizar_estado():
    if request.method == 'POST':
        id_cita = request.form['id_cita']
        nuevo_estado = request.form['estado']

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE citas SET estado = ? WHERE id_cita = ?", (nuevo_estado, id_cita))
            connection.commit()

    return redirect(url_for('historial_citas'))

@app.route('/directorio_pacientes', methods=['GET', 'POST'])
def directorio_pacientes():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM pacientes")
        pacientes = cursor.fetchall()

    if request.method == 'POST':
        filter_text = request.form['filter_text']
        filter_by = request.form['filter_by']

        if filter_by == 'apellidos':
            pacientes = [paciente for paciente in pacientes if filter_text.lower() in f"{paciente[1]} {paciente[2]} {paciente[3]} ".lower()]
        elif filter_by == 'id_paciente':
            pacientes = [paciente for paciente in pacientes if filter_text.lower() in paciente[0].lower()]

    return render_template('directorio_pacientes.html', pacientes=pacientes)

@app.route('/registro_antecedentes_familiares', methods=['GET', 'POST'])
@login_required
def registro_antecedentes_familiares():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        diabetes_mellitus_familiar = request.form['diabetes_mellitus_familiar']
        dislipidemias_familiar = request.form['dislipidemias_familiar']
        sobrepeso_obesidad_familiar = request.form['sobrepeso_obesidad_familiar']
        cancer_tipo_familiar = request.form['cancer_tipo_familiar']
        hipertension_familiar = request.form['hipertension_familiar']
        cardiopatias_familiar = request.form['cardiopatias_familiar']
        litiasis_familiar = request.form['litiasis_familiar']
        artritis_familiar = request.form['artritis_familiar']
        asma_familiar = request.form['asma_familiar']
        otras = request.form['otras']

        with get_db_connection() as connection:
            cursor = connection.cursor()
            # Verificar si el id_paciente ya tiene registros en antecedentes_familiares
            cursor.execute("SELECT id_paciente FROM antecedentes_familiares WHERE id_paciente = ?", (id_paciente,))
            if cursor.fetchone():
                # Si existe, actualizar los datos en lugar de insertarlos
                  cursor.execute("""UPDATE antecedentes_familiares SET diabetes_mellitus_familiar=?, 
                                  dislipidemias_familiar=?, sobrepeso_obesidad_familiar=?, 
                                  cancer_tipo_familiar=?, hipertension_familiar=?, otras=?, 
                                  cardiopatias_familiar=?, litiasis_familiar=?, artritis_familiar=?, 
                                  asma_familiar=? WHERE id_paciente=?""",
                               (diabetes_mellitus_familiar, dislipidemias_familiar, sobrepeso_obesidad_familiar,
                                cancer_tipo_familiar, hipertension_familiar, otras, cardiopatias_familiar, 
                                litiasis_familiar, artritis_familiar, asma_familiar, id_paciente))
            else:
                # Si no existe, insertar los datos
                cursor.execute("""INSERT INTO antecedentes_familiares 
                                  (id_paciente, diabetes_mellitus_familiar, dislipidemias_familiar,
                                   sobrepeso_obesidad_familiar, cancer_tipo_familiar, hipertension_familiar, 
                                   otras, cardiopatias_familiar, litiasis_familiar, artritis_familiar, 
                                   asma_familiar) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (id_paciente, diabetes_mellitus_familiar, dislipidemias_familiar,
                                sobrepeso_obesidad_familiar, cancer_tipo_familiar, hipertension_familiar, 
                                otras, cardiopatias_familiar, litiasis_familiar, artritis_familiar, 
                                asma_familiar))
                
        return redirect(url_for('registro_exitoso'))
    
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()

    return render_template('registro_antecedentes_familiares.html', pacientes=pacientes)
@app.route('/expediente')
@login_required
def expediente():
    return render_template('expediente.html')

@app.route('/registro_antecedentes_personales')
@login_required
def registro_antecedentes_personales():
    return render_template('registro_antecedentes_personales.html')

@app.route('/evaluacion_clinica')
@login_required
def evaluacion_clinica():
    return render_template('evaluacion_clinica.html')
@app.route('/evaluacion_dietetica')
@login_required
def evaluacion_dietetica():
    return render_template('evaluacion_dietetica.html')
@app.route('/evaluacion_antropometrica')
@login_required
def evaluacion_antropometrica():
    return render_template('evaluacion_antropometrica.html')
if __name__ == '__main__':
    app.run(debug=True)
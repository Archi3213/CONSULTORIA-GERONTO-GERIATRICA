import sqlite3
import hashlib
conexion = sqlite3.connect('gero_data.db')
cursor = conexion.cursor()
def get_hashed_password(password, salt=None):
    if not salt:
        salt = hashlib.sha256(b'SALT').hexdigest()
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed_password.hex()

#cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
    #id INTEGER PRIMARY KEY AUTOINCREMENT,
   # username TEXT UNIQUE NOT NULL,
   # password TEXT NOT NULL,
   # salt TEXT NOT NULL,
   # tipo_usuario TEXT NOT NULL
#)''')
#username = 'coordinacion'
#password = 'coordinacion'
#salt = hashlib.sha256(b'SALT').hexdigest()  # Puedes cambiar 'SALT' por cualquier cadena que desees usar como sal
#hashed_password = get_hashed_password(password, salt)
#tipo_usuario = 'coordinacion'

# Insertar el nuevo usuario en la tabla usuarios
#cursor.execute('''
#INSERT INTO usuarios (username, password, salt, tipo_usuario)
#VALUES (?, ?, ?, ?)
#''', (username, hashed_password, salt, tipo_usuario))

# Confirmar la transacción
conexion.commit()

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

cursor.execute('''CREATE TABLE IF NOT EXISTS citas_fisioterapia (
                    id_cita INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_paciente TEXT,
                    fecha_consulta TEXT NOT NULL,
                    hora_consulta TEXT NOT NULL, 
                    observaciones TEXT,
                    estado TEXT DEFAULT 'Pendiente',
                    FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS citas_acomp_psicoemocional (
                    id_cita INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_paciente TEXT,
                    fecha_consulta TEXT NOT NULL,
                    hora_consulta TEXT NOT NULL, 
                    observaciones TEXT,
                    estado TEXT DEFAULT 'Pendiente',
                    FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
                )''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS antecedentes_personales_nutricion (
        id_paciente  PRIMARY KEY,
        padecimiento_actual TEXT,
        medicamento TEXT,
        discapacidad TEXT,
        cirugia TEXT,
        alergias TEXT,
        consumo_alcohol TEXT,
        tabaco TEXT,
        suplementos TEXT,
        cafeina TEXT,
        observaciones TEXT,
        FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)

    )
''')
#cursor.execute('DROP TABLE IF EXISTS antecedentes_personales')


cursor.execute('''CREATE TABLE IF NOT EXISTS citas_nutricion (
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
cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluacion_clinica (
                id_paciente PRIMARY KEY NOT NULL,
                piel TEXT,
                ojos TEXT,
                unas TEXT,
                cabello TEXT,
                boca TEXT,
                dientes TEXT,
                observacion TEXT,
                FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
            )
        ''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS registro_dietetico (
        id_paciente TEXT PRIMARY KEY,
        quien_orientacion TEXT,
        intolerancia_alimento TEXT,
        alergia_alimentaria TEXT,
        consumo_agua REAL,
        disminucion_apetito TEXT,
        motivo_apetito TEXT,
        preferencia_alimentos TEXT,
        desagradables_alimentos TEXT,
        dinero_semanal REAL,
        num_personas INTEGER,
        quien_prepara TEXT,
        desayuno_lugar TEXT,
        desayuno_horario TEXT,
        colacion1_lugar TEXT,
        colacion1_horario TEXT,
        almuerzo_lugar TEXT,
        almuerzo_horario TEXT,
        colacion2_lugar TEXT,
        colacion2_horario TEXT,
        cena_lugar TEXT,
        cena_horario TEXT,
        frecuencia_cereales INTEGER,
        tipo_cereales TEXT,
        frecuencia_frutas INTEGER,
        tipo_frutas TEXT,
        frecuencia_verduras INTEGER,
        tipo_verduras TEXT,
        frecuencia_aoa INTEGER,
        tipo_aoa TEXT,
        frecuencia_leguminosas INTEGER,
        tipo_leguminosas TEXT,
        frecuencia_lacteos INTEGER,
        tipo_lacteos TEXT,
        frecuencia_grasas INTEGER,
        tipo_grasas TEXT,
        frecuencia_azucar INTEGER,
        tipo_azucar TEXT,
        FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
    )
''')
cursor.execute('''CREATE TABLE IF NOT EXISTS evaluacion_antropometrica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            peso REAL,
            imc REAL,
            grasa REAL,
            musculo REAL,
            grasa_visceral REAL,
            cintura REAL,
            cadera REAL,
            cm_bc REAL,
            pantorrilla REAL,
            presion_arterial TEXT,
            g_capilar REAL,
            diagnostico_antropometrico TEXT,
            plan_alimentacion TEXT,
            observaciones TEXT,
            FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
        )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS evaluacion_bioquimica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_paciente INTEGER NOT NULL,
    fecha_hb_hto TEXT,
    fecha_col_trig TEXT,
    fecha_guca TEXT,
    hb REAL,
    hto REAL,
    colesterol REAL,
    trigliceridos REAL,
    glucosa REAL,
    urea REAL,
    creatinina REAL,
    acido_urico REAL,
    otros TEXT,
    FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente)
)''')
conexion.commit()
cursor.close()
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
import hashlib, sqlite3
import pandas as pd
from operator import itemgetter
from datetime import datetime
from datetime import datetime, timedelta
import math
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import matplotlib

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
matplotlib.use('Agg')

import database

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

@app.route('/')
def index():
    session.pop('username', None)  # Eliminar la clave 'username' de la sesión
    return render_template('index.html')

@app.route('/login/<area>', methods=['GET', 'POST'])
def login(area):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conexion = sqlite3.connect('nutricion_consulta.db')
        cursor = conexion.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE username = ? AND tipo_usuario = ?", (username, area))
        user = cursor.fetchone()

        cursor.close()
        conexion.close()

        if user and verify_password(user[2], user[3], password):  # Verify password using stored hash and salt
            session['username'] = username
            session['area'] = area
            return redirect(url_for('options'))
        else:
            error = 'Usuario o contraseña incorrectos'
            return render_template(f'{area}/login.html', error=error)
    return render_template(f'{area}/login.html')

@app.route('/agenda')
@login_required
def options():
    area = session.get('area')
    current_date = datetime.now().date()
    tomorrow_date = current_date + timedelta(days=1)

    citas_hoy = []
    citas_manana = []

    # Definimos las tablas y áreas correspondientes
    tablas_areas = {
        'nutricion': 'citas_nutricion',
        'fisioterapia': 'citas_fisioterapia',
        'acomp_psicoemocional': 'citas_acomp_psicoemocional'
    }

    with get_db_connection() as connection:
        cursor = connection.cursor()

        if area == 'coordinacion':
            # Consultar todas las citas de todas las áreas
            for area_name, table_name in tablas_areas.items():
                cursor.execute(f"SELECT *, '{area_name.capitalize()}' as area FROM {table_name} WHERE fecha_consulta = ?", (current_date,))
                citas_hoy.extend(cursor.fetchall())

                cursor.execute(f"SELECT *, '{area_name.capitalize()}' as area FROM {table_name} WHERE fecha_consulta = ?", (tomorrow_date,))
                citas_manana.extend(cursor.fetchall())
        elif area in tablas_areas:
            # Consultar citas solo del área específica
            table_name = tablas_areas[area]
            cursor.execute(f"SELECT *, '{area.capitalize()}' as area FROM {table_name} WHERE fecha_consulta = ?", (current_date,))
            citas_hoy = cursor.fetchall()

            cursor.execute(f"SELECT *, '{area.capitalize()}' as area FROM {table_name} WHERE fecha_consulta = ?", (tomorrow_date,))
            citas_manana = cursor.fetchall()
        else:
            return "Área no válida", 400

    return render_template(f'{area}/agenda.html', citas_hoy=citas_hoy, citas_manana=citas_manana)

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

        area = session.get('area')
    

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT id_paciente FROM pacientes WHERE id_paciente = ?", (id_paciente,))
            if cursor.fetchone():
                mensaje_error = "El ID del paciente ya existe en la base de datos"
            else:
                cursor.execute(f'''INSERT INTO pacientes (id_paciente, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, religion, escolaridad, ocupacion, estado_civil, servicio_salud, celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                (id_paciente, primer_apellido, segundo_apellido, nombres, fecha_nacimiento, religion, escolaridad, ocupacion, estado_civil, servicio_salud, celular, turno, genero, peso, altura, imc, fecha_registro, registrado_por))

        if mensaje_error:
            return render_template(f'{area}/registro.html', mensaje_error=mensaje_error)
        else:
            return redirect(url_for('registro_exitoso', id_paciente=id_paciente, nombre_paciente=f"{nombres} {primer_apellido} {segundo_apellido}"))

    area = session.get('area')
    return render_template(f'{area}/registro.html')

@app.route('/registro_exitoso')
def registro_exitoso():
    area = session.get('area')
    id_paciente = request.args.get('id_paciente')
    return render_template('nutricion/registro_exitoso.html', id_paciente=id_paciente)

@app.route('/consultar', methods=['GET', 'POST'])
@login_required
def consulta_paciente():
    area = session.get('area')  # Obtener el área de la sesión
    filter_text = ''
    filter_by = ''
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = "SELECT * FROM pacientes"
    params = ()

    if request.method == 'POST':
        if 'filter_text' in request.form and 'filter_by' in request.form:
            filter_text = request.form['filter_text']
            filter_by = request.form['filter_by']

            if filter_by == 'apellidos':
                query += " WHERE LOWER(primer_apellido) LIKE ? OR LOWER(segundo_apellido) LIKE ? OR LOWER(nombres) LIKE ?"
                params = (f"%{filter_text.lower()}%", f"%{filter_text.lower()}%", f"%{filter_text.lower()}%")
            elif filter_by == 'id_paciente':
                query += " WHERE LOWER(id_paciente) LIKE ?"
                params = (f"%{filter_text.lower()}%",)

    query += " LIMIT ? OFFSET ?"
    params += (per_page, (page - 1) * per_page)

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        pacientes = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM pacientes")
        total_pacientes = cursor.fetchone()[0]

    total_pages = (total_pacientes + per_page - 1) // per_page

    return render_template(f'{area}/consultar.html', pacientes=pacientes, page=page, total_pages=total_pages)


@app.route('/agendar_cita', methods=['GET', 'POST'])
@login_required
def agendar_cita():
    area = session.get('area', 'nutricion')  # Obtener el área de la sesión, por defecto 'nutricion'
    tablas_areas = {
        'nutricion': 'citas_nutricion',
        'fisioterapia': 'citas_fisioterapia',
        'acomp_psicoemocional': 'citas_acomp_psicoemocional'
    }

    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        fecha_consulta = request.form['fecha_consulta']
        hora_consulta = request.form['hora_consulta']
        observaciones = request.form['observaciones']
        
        # Seleccionar la tabla de citas basada en el área seleccionada por la coordinación o la sesión actual
        if area == 'coordinacion':
            area_seleccionada = request.form['area']
            tabla_citas = tablas_areas[area_seleccionada]
        else:
            tabla_citas = tablas_areas[area]

        with get_db_connection() as connection:
            cursor = connection.cursor()
            query = f'''INSERT INTO {tabla_citas} (id_paciente, fecha_consulta, hora_consulta, observaciones) 
                        VALUES (?, ?, ?, ?)'''
            cursor.execute(query, (id_paciente, fecha_consulta, hora_consulta, observaciones))
            connection.commit()

        return redirect(url_for('historial_citas'))

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()

    return render_template(f'{area}/agendar_cita.html', pacientes=pacientes, area=area)

@app.route('/historial_citas', methods=['GET', 'POST'])
@login_required
def historial_citas():
    area = session.get('area')  # Obtener el área de la sesión
    tablas_areas = {
        'nutricion': 'citas_nutricion',
        'fisioterapia': 'citas_fisioterapia',
        'acomp_psicoemocional': 'citas_acomp_psicoemocional'
    }

    filter_text = request.form.get('filter_text')
    filter_by = request.form.get('filter_by')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    citas_area = []

    with get_db_connection() as connection:
        connection.row_factory = sqlite3.Row  # Permite el acceso a las columnas por nombre
        cursor = connection.cursor()

        if area == 'coordinacion':
            for area_name, tabla_citas in tablas_areas.items():
                query = f"SELECT *, '{area_name}' as area FROM {tabla_citas}"
                params = []

                if request.method == 'POST' and filter_text and filter_by:
                    if filter_by == 'id_paciente':
                        query += " WHERE LOWER(id_paciente) LIKE LOWER(?)"
                        params.append('%' + filter_text + '%')
                    elif filter_by == 'estado':
                        query += " WHERE LOWER(estado) = LOWER(?)"
                        params.append(filter_text)
                    elif filter_by == 'fecha_consulta':
                        query += " WHERE fecha_consulta = ?"
                        params.append(filter_text)

                cursor.execute(query, params)
                citas_area.extend(cursor.fetchall())
        else:
            tabla_citas = tablas_areas.get(area, 'citas_nutricion')
            query = f"SELECT * FROM {tabla_citas}"
            params = []

            if request.method == 'POST' and filter_text and filter_by:
                if filter_by == 'id_paciente':
                    query += " WHERE LOWER(id_paciente) LIKE LOWER(?)"
                    params.append('%' + filter_text + '%')
                elif filter_by == 'estado':
                    query += " WHERE LOWER(estado) = LOWER(?)"
                    params.append(filter_text)
                elif filter_by == 'fecha_consulta':
                    query += " WHERE fecha_consulta = ?"
                    params.append(filter_text)

            cursor.execute(query, params)
            citas_area = cursor.fetchall()

    # Obtener lista de pacientes para el datalist
    with get_db_connection() as connection:
        connection.row_factory = sqlite3.Row  # Permite el acceso a las columnas por nombre
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()

    # Ordenar por fecha de consulta de más reciente a más antigua
    citas_ordenadas = sorted(citas_area, key=lambda x: x['fecha_consulta'], reverse=True)

    # Paginación
    total_citas = len(citas_ordenadas)
    total_pages = math.ceil(total_citas / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    citas_paginadas = citas_ordenadas[start:end]

    return render_template(
        f'{area}/historial_citas.html',  # Puedes ajustar esta ruta si es necesario
        citas=citas_paginadas,
        pacientes=pacientes,
        page=page,
        total_pages=total_pages,
        area=area  # Pasar el área actual al template
    )

@app.route('/actualizar_estado', methods=['POST'])
@login_required
def actualizar_estado():
    if request.method == 'POST':
        id_cita = request.form['id_cita']
        nuevo_estado = request.form['estado']

        area = session.get('area')
        tabla_citas = f"citas_{area}"

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"UPDATE {tabla_citas} SET estado = ? WHERE id_cita = ?", (nuevo_estado, id_cita))
            connection.commit()

    return redirect(request.referrer or url_for('historial_citas'))
@app.route('/directorio_pacientes', methods=['GET', 'POST'])
def directorio_pacientes():
    area = session.get('area')
    filter_text = ''
    filter_by = ''
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = "SELECT * FROM pacientes"
    params = ()

    if request.method == 'POST':
        if 'filter_text' in request.form and 'filter_by' in request.form:
            filter_text = request.form['filter_text']
            filter_by = request.form['filter_by']

            if filter_by == 'apellidos':
                query += " WHERE LOWER(primer_apellido) LIKE ? OR LOWER(segundo_apellido) LIKE ? OR LOWER(nombres) LIKE ?"
                params = (f"%{filter_text.lower()}%", f"%{filter_text.lower()}%", f"%{filter_text.lower()}%")
            elif filter_by == 'id_paciente':
                query += " WHERE LOWER(id_paciente) LIKE ?"
                params = (f"%{filter_text.lower()}%",)
        
        if 'new_phone' in request.form and 'id_paciente' in request.form:
            new_phone = request.form['new_phone']
            id_paciente = request.form['id_paciente']
            
            with get_db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("UPDATE pacientes SET celular = ? WHERE id_paciente = ?", (new_phone, id_paciente))
                connection.commit()

    query += " LIMIT ? OFFSET ?"
    params += (per_page, (page - 1) * per_page)

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        pacientes = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM pacientes")
        total_pacientes = cursor.fetchone()[0]

    total_pages = (total_pacientes + per_page - 1) // per_page

    return render_template(f'{area}/directorio_pacientes.html', pacientes=pacientes, page=page, total_pages=total_pages)


@app.route('/registro_antecedentes_familiares', methods=['GET', 'POST'])
@login_required
def registro_antecedentes_familiares():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        diabetes_mellitus_familiar = request.form.getlist('diabetes_mellitus_familiar')
        diabetes_mellitus_familiar = ', '.join(diabetes_mellitus_familiar)
        sobrepeso_obesidad_familiar =  request.form.getlist('sobrepeso_obesidad_familiar')
        sobrepeso_obesidad_familiar = ', '.join(sobrepeso_obesidad_familiar)
        hipertension_familiar =  request.form.getlist('hipertension_familiar')
        hipertension_familiar = ', '.join(hipertension_familiar)
        litiasis_familiar = request.form.getlist('litiasis_familiar')
        litiasis_familiar = ', '.join(litiasis_familiar)
        artritis_familiar = request.form.getlist('artritis_familiar')
        artritis_familiar = ', '.join(artritis_familiar)
        asma_familiar = request.form.getlist('asma_familiar')
        asma_familiar = ', '.join(asma_familiar)
        otras = request.form['otras']
        cancer_familiar = request.form['cancer_familiar']
        tipo_cancer = request.form['tipo_cancer']
        cancer_tipo_familiar = f"{cancer_familiar} - {tipo_cancer}"
        dislipidemias_con_familiar = request.form['dislipidemias_con_familiar']
        tipo_dislipidemias = request.form['tipo_dislipidemias']
        dislipidemias_familiar = f"{dislipidemias_con_familiar} - {tipo_dislipidemias}"
        familiar_con_cardiopatias = request.form['familiar_con_cardiopatias']
        tipo_cardiopatias = request.form['tipo_cardiopatias']
        cardiopatias_familiar = f"{familiar_con_cardiopatias} - {tipo_cardiopatias}"

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

    return render_template('nutricion/registro_antecedentes_familiares.html', pacientes=pacientes)
@app.route('/expediente')
@login_required
def expediente():
    area = session.get('area')
    return render_template(f'{area}/expediente.html')

@app.route('/registro_antecedentes_personales', methods=['GET', 'POST'])
@login_required
def registro_antecedentes_personales():
    if request.method == 'POST':
        # Obtener datos del formulario
        id_paciente = request.form['id_paciente']
        padecimiento = request.form['padecimiento']
        tiempo_padecimiento = request.form['tiempo_padecimiento']
        padecimiento_actual = f"{padecimiento} - {tiempo_padecimiento}"
        medicacion = request.form['medicacion']
        dosis = request.form['dosis']
        medicamento = f"{medicacion} - {dosis}"
        discapacidad = request.form.getlist('discapacidad')
        discapacidad = ', '.join(discapacidad)
        cirugia = request.form['cirugia']
        alergias = request.form['alergias']
        consumo_alcohol = request.form.get('consumo_alcohol', 'No')
        tabaco = request.form.get('tabaco', 'No')
        suplementos = request.form.get('suplementos', 'No')
        cafeina = request.form.get('cafeina', 'No')
        observaciones = request.form['observaciones']
        
        # Conexión a la base de datos y operación de inserción o actualización
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO antecedentes_personales_nutricion 
                (id_paciente, padecimiento_actual, medicamento, discapacidad, cirugia, alergias, consumo_alcohol, tabaco, suplementos, cafeina, observaciones) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,? , ?)
            """, (id_paciente, padecimiento_actual, medicamento, discapacidad, cirugia, alergias, consumo_alcohol, tabaco, suplementos, cafeina, observaciones))
            connection.commit()

        # Redireccionar a alguna página después de guardar los datos
        return redirect(url_for('registro_exitoso'))

    # Obtener la lista de pacientes para mostrar en el formulario
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()
        
    return render_template('nutricion/registro_antecedentes_personales.html', pacientes=pacientes)


@app.route('/evaluacion_clinica', methods=['GET', 'POST'])
@login_required
def evaluacion_clinica():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        piel = request.form['piel']
        ojos = request.form['ojos']
        unas = request.form['uñas']
        cabello = request.form['cabello']
        boca = request.form['boca']
        dientes = request.form['dientes']
        observacion = request.form['observacion']
        
        # Guardar los datos en la base de datos
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('''
                   INSERT OR REPLACE INTO evaluacion_clinica (id_paciente, piel, ojos, unas, cabello, boca, dientes, observacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_paciente, piel, ojos, unas, cabello, boca, dientes, observacion))
            connection.commit()
            
        # Redireccionar a una página de éxito o a donde sea necesario
        return redirect(url_for('registro_exitoso'))
    
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()
        
    return render_template('nutricion/evaluacion_clinica.html', pacientes=pacientes)

@app.route('/evaluacion_dietetica', methods=['GET', 'POST'])
@login_required
def evaluacion_dietetica():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        quien_orientacion = request.form['quien_orientacion']
        intolerancia_alimento = request.form['intolerancia_alimento']
        alergia_alimentaria = request.form['alergia_alimentaria']
        consumo_agua = float(request.form['consumo_agua'])
        disminucion_apetito = request.form['disminucion_apetito']
        motivo_apetito = request.form.get('motivo_apetito', '')
        preferencia_alimentos = request.form['preferencia_alimentos']
        desagradables_alimentos = request.form['desagradables_alimentos']
        dinero_semanal = float(request.form['dinero_semanal'])
        num_personas = int(request.form['num_personas'])
        quien_prepara = request.form['quien_prepara']
        desayuno_lugar = request.form.get('desayuno_lugar', '')
        desayuno_horario = request.form.get('desayuno_horario', '')
        colacion1_lugar = request.form.get('colacion1_lugar', '')
        colacion1_horario = request.form.get('colacion1_horario', '')
        almuerzo_lugar = request.form.get('almuerzo_lugar', '')
        almuerzo_horario = request.form.get('almuerzo_horario', '')
        colacion2_lugar = request.form.get('colacion2_lugar', '')
        colacion2_horario = request.form.get('colacion2_horario', '')
        cena_lugar = request.form.get('cena_lugar', '')
        cena_horario = request.form.get('cena_horario', '')
        frecuencia_cereales = int(request.form.get('frecuencia_cereales', 0))
        tipo_cereales = request.form.get('tipo_cereales', '')
        frecuencia_frutas = int(request.form.get('frecuencia_frutas', 0))
        tipo_frutas = request.form.get('tipo_frutas', '')
        frecuencia_verduras = int(request.form.get('frecuencia_verduras', 0))
        tipo_verduras = request.form.get('tipo_verduras', '')
        frecuencia_aoa = int(request.form.get('frecuencia_aoa', 0))
        tipo_aoa = request.form.get('tipo_aoa', '')
        frecuencia_leguminosas = int(request.form.get('frecuencia_leguminosas', 0))
        tipo_leguminosas = request.form.get('tipo_leguminosas', '')
        frecuencia_lacteos = int(request.form.get('frecuencia_lacteos', 0))
        tipo_lacteos = request.form.get('tipo_lacteos', '')
        frecuencia_grasas = int(request.form.get('frecuencia_grasas', 0))
        tipo_grasas = request.form.get('tipo_grasas', '')
        frecuencia_azucar = int(request.form.get('frecuencia_azucar', 0))
        tipo_azucar = request.form.get('tipo_azucar', '')

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO registro_dietetico (
                    id_paciente, quien_orientacion, intolerancia_alimento, alergia_alimentaria, consumo_agua,
                    disminucion_apetito, motivo_apetito, preferencia_alimentos, desagradables_alimentos, dinero_semanal,
                    num_personas, quien_prepara, desayuno_lugar, desayuno_horario, colacion1_lugar, colacion1_horario,
                    almuerzo_lugar, almuerzo_horario, colacion2_lugar, colacion2_horario, cena_lugar, cena_horario,
                    frecuencia_cereales, tipo_cereales, frecuencia_frutas, tipo_frutas, frecuencia_verduras, tipo_verduras,
                    frecuencia_aoa, tipo_aoa, frecuencia_leguminosas, tipo_leguminosas, frecuencia_lacteos, tipo_lacteos,
                    frecuencia_grasas, tipo_grasas, frecuencia_azucar, tipo_azucar
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_paciente, quien_orientacion, intolerancia_alimento, alergia_alimentaria, consumo_agua, disminucion_apetito,
                motivo_apetito, preferencia_alimentos, desagradables_alimentos, dinero_semanal, num_personas, quien_prepara,
                desayuno_lugar, desayuno_horario, colacion1_lugar, colacion1_horario, almuerzo_lugar, almuerzo_horario,
                colacion2_lugar, colacion2_horario, cena_lugar, cena_horario, frecuencia_cereales, tipo_cereales,
                frecuencia_frutas, tipo_frutas, frecuencia_verduras, tipo_verduras, frecuencia_aoa, tipo_aoa, frecuencia_leguminosas,
                tipo_leguminosas, frecuencia_lacteos, tipo_lacteos, frecuencia_grasas, tipo_grasas, frecuencia_azucar, tipo_azucar
            ))
            connection.commit()

        return redirect(url_for('registro_exitoso'))

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()

    return render_template('nutricion/evaluacion_dietetica.html', pacientes=pacientes)


@app.route('/evaluacion_antropometrica', methods=['GET', 'POST'])
@login_required
def evaluacion_antropometrica():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        fecha = request.form['fecha']
        peso = float(request.form['peso'])
        grasa = request.form['grasa']
        musculo = request.form['musculo']
        grasa_visceral = request.form['grasa_visceral']
        cintura = request.form['cintura']
        cadera = request.form['cadera']
        cm_bc = request.form['cm_bc']
        pantorrilla = request.form['pantorrilla']
        presion_arterial = request.form['presion_arterial']
        g_capilar = request.form['g_capilar']
        diagnostico_antropometrico = request.form['diagnostico_antropometrico']
        plan_alimentacion = request.form['plan_alimentacion']
        observaciones = request.form['observaciones']

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT altura FROM pacientes WHERE id_paciente = ?", (id_paciente,))
            altura = cursor.fetchone()
            
            if altura:
                altura_en_metros = altura[0] / 100  # Convertir altura a metros
                imc = peso / (altura_en_metros * altura_en_metros)
                imc = round(imc, 2)  # Redondear a 2 decimales
            else:
                imc = None  # Manejar el caso donde no se encuentra la altura

            cursor.execute('''INSERT INTO evaluacion_antropometrica (
                    id_paciente, fecha, peso, imc, grasa, musculo, grasa_visceral,
                    cintura, cadera, cm_bc, pantorrilla, presion_arterial, g_capilar,
                    diagnostico_antropometrico, plan_alimentacion, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    id_paciente, fecha, peso, imc, grasa, musculo, grasa_visceral,
                    cintura, cadera, cm_bc, pantorrilla, presion_arterial, g_capilar,
                    diagnostico_antropometrico, plan_alimentacion, observaciones
                ))
            connection.commit()
        return redirect(url_for('registro_exitoso'))

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()
    
    return render_template('nutricion/evaluacion_antropometrica.html', pacientes=pacientes)


@app.route('/evaluacion_bioquimica', methods=['GET', 'POST'])
@login_required
def evaluacion_bioquimica():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        fecha_hb_hto = request.form['fecha_hb_hto']
        fecha_col_trig = request.form['fecha_col_trig']
        fecha_guca = request.form['fecha_guca']
        hb = request.form['hb']
        hto = request.form['hto']
        colesterol = request.form['colesterol']
        trigliceridos = request.form['trigliceridos']
        glucosa = request.form['glucosa']
        urea = request.form['urea']
        creatinina = request.form['creatinina']
        acido_urico = request.form['acido_urico']
        otros = request.form['otros']

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('''INSERT INTO evaluacion_bioquimica (
                    id_paciente, fecha_hb_hto, fecha_col_trig, fecha_guca, hb, hto, colesterol, 
                    trigliceridos, glucosa, urea, creatinina, acido_urico, otros
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    id_paciente, fecha_hb_hto, fecha_col_trig, fecha_guca, hb, hto, colesterol, 
                    trigliceridos, glucosa, urea, creatinina, acido_urico, otros
                ))
            connection.commit()
        return redirect(url_for('registro_exitoso'))
    
    with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
            pacientes = cursor.fetchall()
    
    return render_template('nutricion/evaluacion_bioquimica.html', pacientes=pacientes)

def get_db_connection():
    connection = sqlite3.connect('nutricion_consulta.db')
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/detalles_paciente', methods=['GET', 'POST'])
@login_required
def detalles_paciente():
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        area = session.get('area')

        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Obtener datos del paciente
        cursor.execute('SELECT * FROM pacientes WHERE id_paciente = ?', (id_paciente,))
        paciente = cursor.fetchone()
        
        # Obtener datos de antecedentes personales
        cursor.execute('SELECT * FROM antecedentes_personales_nutricion WHERE id_paciente = ?', (id_paciente,))
        antecedentes_personales_nutricion = cursor.fetchone()
        
        # Obtener datos de antecedentes familiares
        cursor.execute('SELECT * FROM antecedentes_familiares WHERE id_paciente = ?', (id_paciente,))
        antecedentes_familiares = cursor.fetchone()
        
        # Obtener datos de citas
        cursor.execute(f'SELECT * FROM citas_{area} WHERE id_paciente = ?', (id_paciente,))
        citas = cursor.fetchall()
        
        # Obtener datos de evaluación clínica
        cursor.execute('SELECT * FROM evaluacion_clinica WHERE id_paciente = ?', (id_paciente,))
        evaluacion_clinica = cursor.fetchone()
        
        # Obtener datos de registro dietético
        cursor.execute('SELECT * FROM registro_dietetico WHERE id_paciente = ?', (id_paciente,))
        registro_dietetico = cursor.fetchone()
        
        # Obtener datos de evaluación antropométrica
        cursor.execute('SELECT * FROM evaluacion_antropometrica WHERE id_paciente = ?', (id_paciente,))
        evaluacion_antropometrica = cursor.fetchall()
        
        # Obtener datos de evaluación bioquímica
        cursor.execute('SELECT * FROM evaluacion_bioquimica WHERE id_paciente = ?', (id_paciente,))
        evaluacion_bioquimica = cursor.fetchall()
        
        connection.close()
        
        return render_template(f'{area}/detalles_paciente.html', paciente=paciente, antecedentes_personales_nutricion=antecedentes_personales_nutricion,
                               antecedentes_familiares=antecedentes_familiares, citas=citas, evaluacion_clinica=evaluacion_clinica,
                               registro_dietetico=registro_dietetico, evaluacion_antropometrica=evaluacion_antropometrica,
                               evaluacion_bioquimica=evaluacion_bioquimica)
    return render_template(f'{area}/buscar_paciente.html')
@app.route('/buscar_paciente')
@login_required
def buscar_paciente():
    area = session.get('area')
    with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
            pacientes = cursor.fetchall()
    
    return render_template(f'{area}/buscar_paciente.html', pacientes=pacientes)
def obtener_estadisticas():
    conexion = get_db_connection()
    query = "SELECT * FROM pacientes"
    pacientes_df = pd.read_sql_query(query, conexion)
    
    pacientes_df['fecha_nacimiento'] = pd.to_datetime(pacientes_df['fecha_nacimiento'], format="%Y-%m-%d")
    pacientes_df['edad'] = pacientes_df['fecha_nacimiento'].apply(lambda x: (datetime.now() - x).days // 365)

    estadisticas = {
        'total_pacientes': len(pacientes_df),
        'promedio_edad': pacientes_df['edad'].mean(),
        'promedio_peso': pacientes_df['peso'].mean(),
        'promedio_altura': pacientes_df['altura'].mean(),
        'promedio_imc': pacientes_df['imc'].mean(),
        'distribucion_genero': pacientes_df['genero'].value_counts().to_dict(),
        'distribucion_escolaridad': pacientes_df['escolaridad'].value_counts().to_dict(),
        'distribucion_ocupacion': pacientes_df['ocupacion'].value_counts().to_dict(),
        'distribucion_estado_civil': pacientes_df['estado_civil'].value_counts().to_dict(),
        'distribucion_servicio_salud': pacientes_df['servicio_salud'].value_counts().to_dict(),
    }
    
    conexion.close()
    return estadisticas

def generar_grafico(data, titulo):
    fig, ax = plt.subplots()
    ax.bar(data.keys(), data.values())
    ax.set_title(titulo)
    ax.set_xticklabels(data.keys(), rotation=45, ha="right")
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close(fig)
    return img_base64

@app.route('/estadisticas_registro')
@login_required
def estadisticas_registro():
    area = session.get('area', 'nutricion')  
    estadisticas = obtener_estadisticas()
    
    grafico_genero = generar_grafico(estadisticas['distribucion_genero'], 'Distribución por Género')
    grafico_escolaridad = generar_grafico(estadisticas['distribucion_escolaridad'], 'Distribución por Escolaridad')
    grafico_ocupacion = generar_grafico(estadisticas['distribucion_ocupacion'], 'Distribución por Ocupación')
    grafico_estado_civil = generar_grafico(estadisticas['distribucion_estado_civil'], 'Distribución por Estado Civil')
    grafico_servicio_salud = generar_grafico(estadisticas['distribucion_servicio_salud'], 'Distribución por Servicio de Salud')

    return render_template(
        f'{area}/estadisticas_registro.html',
        estadisticas=estadisticas,
        grafico_genero=grafico_genero,
        grafico_escolaridad=grafico_escolaridad,
        grafico_ocupacion=grafico_ocupacion,
        grafico_estado_civil=grafico_estado_civil,
        grafico_servicio_salud=grafico_servicio_salud,
        area=area
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(debug=True)
# Standard library imports
from datetime import datetime, timedelta
import hashlib
import math
from io import BytesIO
import base64

# Third-party imports
import matplotlib.pyplot as plt
import pandas as pd
from operator import itemgetter

# Flask-related imports
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
app = Flask(__name__)

def get_db_connection():
    return sqlite3.connect('gero_data.db')

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

@app.route('/registro_antecedentes_familiares', methods=['GET', 'POST'])
@login_required
def registro_antecedentes_familiares():
    area = session.get('area')
    
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        
        # Consolidar campos con request.form.getlist
        fields = ['diabetes_mellitus_familiar', 'sobrepeso_obesidad_familiar', 'hipertension_familiar',
                  'litiasis_familiar', 'artritis_familiar', 'asma_familiar']
        antecedentes = {field: ', '.join(request.form.getlist(field)) for field in fields}

        # Otros campos individuales
        antecedentes.update({
            'otras': request.form['otras'],
            'cancer_tipo_familiar': f"{request.form['cancer_familiar']} - {request.form['tipo_cancer']}",
            'dislipidemias_familiar': f"{request.form['dislipidemias_con_familiar']} - {request.form['tipo_dislipidemias']}",
            'cardiopatias_familiar': f"{request.form['familiar_con_cardiopatias']} - {request.form['tipo_cardiopatias']}"
        })

        try:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                # Verificar si el id_paciente ya tiene registros en antecedentes_familiares
                cursor.execute("SELECT id_paciente FROM antecedentes_familiares WHERE id_paciente = ?", (id_paciente,))
                if cursor.fetchone():
                    # Si existe, actualizar los datos
                    update_fields = ", ".join([f"{field}=?" for field in antecedentes.keys()])
                    query = f"UPDATE antecedentes_familiares SET {update_fields} WHERE id_paciente=?"
                    cursor.execute(query, (*antecedentes.values(), id_paciente))
                else:
                    # Si no existe, insertar los datos
                    fields_str = ", ".join(antecedentes.keys())
                    values_str = ", ".join(['?' for _ in antecedentes])
                    query = f"INSERT INTO antecedentes_familiares (id_paciente, {fields_str}) VALUES (?, {values_str})"
                    cursor.execute(query, (id_paciente, *antecedentes.values()))
                connection.commit()
            flash("Antecedentes familiares registrados exitosamente", "success")
        except sqlite3.Error as e:
            flash(f"Error en la base de datos: {e}", "danger")
            return redirect(url_for('registro_antecedentes_familiares'))
        
        # Redireccionar a la página de detalles del paciente
        return redirect(url_for('detalles_paciente', id_paciente=id_paciente, area=area))
    
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()

    return render_template('nutricion/registro_antecedentes_familiares.html', pacientes=pacientes, area=area)

@app.route('/registro_antecedentes_personales', methods=['GET', 'POST'])
@login_required
def registro_antecedentes_personales():
    area = session.get('area')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        id_paciente = request.form['id_paciente']
        padecimiento_actual = f"{request.form['padecimiento']} - {request.form['tiempo_padecimiento']}"
        medicamento = f"{request.form['medicacion']} - {request.form['dosis']}"
        discapacidad = ', '.join(request.form.getlist('discapacidad'))
        cirugia = request.form['cirugia']
        alergias = request.form['alergias']
        consumo_alcohol = request.form.get('consumo_alcohol', 'No')
        tabaco = request.form.get('tabaco', 'No')
        suplementos = request.form.get('suplementos', 'No')
        cafeina = request.form.get('cafeina', 'No')
        observaciones = request.form['observaciones']
        
        # Conexión a la base de datos y operación de inserción o actualización
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO antecedentes_personales_nutricion 
                    (id_paciente, padecimiento_actual, medicamento, discapacidad, cirugia, alergias, 
                     consumo_alcohol, tabaco, suplementos, cafeina, observaciones) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_paciente, padecimiento_actual, medicamento, discapacidad, cirugia, alergias, 
                      consumo_alcohol, tabaco, suplementos, cafeina, observaciones))
                connection.commit()
            flash("Antecedentes personales registrados exitosamente", "success")
        except sqlite3.Error as e:
            flash(f"Error en la base de datos: {e}", "danger")
            return redirect(url_for('registro_antecedentes_personales'))
        
        # Redireccionar a la página de detalles del paciente
        return redirect(url_for('detalles_paciente', id_paciente=id_paciente, area=area))

    # Obtener la lista de pacientes para mostrar en el formulario
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
            pacientes = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error en la base de datos: {e}", "danger")
        return redirect(url_for('registro_antecedentes_personales'))
        
    return render_template('nutricion/registro_antecedentes_personales.html', pacientes=pacientes, area=area)

@app.route('/evaluacion_clinica', methods=['GET', 'POST'])
@login_required
def evaluacion_clinica():
    area = session.get('area')
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
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO evaluacion_clinica 
                    (id_paciente, piel, ojos, unas, cabello, boca, dientes, observacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (id_paciente, piel, ojos, unas, cabello, boca, dientes, observacion))
                connection.commit()
            flash("Evaluación clínica registrada exitosamente", "success")
        except sqlite3.Error as e:
            flash(f"Error en la base de datos: {e}", "danger")
            return redirect(url_for('evaluacion_clinica'))
            
        # Redireccionar a la página de detalles del paciente
        return redirect(url_for('detalles_paciente', id_paciente=id_paciente, area=area))
    
    # Obtener la lista de pacientes para mostrar en el formulario
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
            pacientes = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error en la base de datos: {e}", "danger")
        return redirect(url_for('evaluacion_clinica'))
        
    return render_template('nutricion/evaluacion_clinica.html', pacientes=pacientes, area=area)

@app.route('/evaluacion_dietetica', methods=['GET', 'POST'])
@login_required
def evaluacion_dietetica():
    area = session.get('area')
    if request.method == 'POST':
        id_paciente = request.form['id_paciente']
        form_fields = [
            'id_paciente', 'quien_orientacion', 'intolerancia_alimento', 'alergia_alimentaria', 'consumo_agua',
            'disminucion_apetito', 'motivo_apetito', 'preferencia_alimentos', 'desagradables_alimentos', 
            'dinero_semanal', 'num_personas', 'quien_prepara', 'desayuno_lugar', 'desayuno_horario', 
            'colacion1_lugar', 'colacion1_horario', 'almuerzo_lugar', 'almuerzo_horario', 'colacion2_lugar', 
            'colacion2_horario', 'cena_lugar', 'cena_horario', 'frecuencia_cereales', 'tipo_cereales', 
            'frecuencia_frutas', 'tipo_frutas', 'frecuencia_verduras', 'tipo_verduras', 'frecuencia_aoa', 
            'tipo_aoa', 'frecuencia_leguminosas', 'tipo_leguminosas', 'frecuencia_lacteos', 'tipo_lacteos', 
            'frecuencia_grasas', 'tipo_grasas', 'frecuencia_azucar', 'tipo_azucar'
        ]

        form_data = {field: request.form.get(field, '') for field in form_fields}
        
        try:
            form_data['consumo_agua'] = float(request.form['consumo_agua'])
            form_data['dinero_semanal'] = float(request.form['dinero_semanal'])
            form_data['num_personas'] = int(request.form['num_personas'])
            form_data['frecuencia_cereales'] = int(request.form.get('frecuencia_cereales', 0))
            form_data['frecuencia_frutas'] = int(request.form.get('frecuencia_frutas', 0))
            form_data['frecuencia_verduras'] = int(request.form.get('frecuencia_verduras', 0))
            form_data['frecuencia_aoa'] = int(request.form.get('frecuencia_aoa', 0))
            form_data['frecuencia_leguminosas'] = int(request.form.get('frecuencia_leguminosas', 0))
            form_data['frecuencia_lacteos'] = int(request.form.get('frecuencia_lacteos', 0))
            form_data['frecuencia_grasas'] = int(request.form.get('frecuencia_grasas', 0))
            form_data['frecuencia_azucar'] = int(request.form.get('frecuencia_azucar', 0))
        except ValueError as e:
            flash(f"Error en la conversión de datos: {e}", "danger")
            return redirect(url_for('evaluacion_dietetica'))

        with get_db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO registro_dietetico (
                        id_paciente, quien_orientacion, intolerancia_alimento, alergia_alimentaria, consumo_agua,
                        disminucion_apetito, motivo_apetito, preferencia_alimentos, desagradables_alimentos, 
                        dinero_semanal, num_personas, quien_prepara, desayuno_lugar, desayuno_horario, 
                        colacion1_lugar, colacion1_horario, almuerzo_lugar, almuerzo_horario, colacion2_lugar, 
                        colacion2_horario, cena_lugar, cena_horario, frecuencia_cereales, tipo_cereales,
                        frecuencia_frutas, tipo_frutas, frecuencia_verduras, tipo_verduras, frecuencia_aoa, tipo_aoa, 
                        frecuencia_leguminosas, tipo_leguminosas, frecuencia_lacteos, tipo_lacteos, frecuencia_grasas, 
                        tipo_grasas, frecuencia_azucar, tipo_azucar
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(form_data.values()))
                connection.commit()
                flash("Evaluación dietética registrada exitosamente", "success")
            except sqlite3.Error as e:
                flash(f"Error en la base de datos: {e}", "danger")
                return redirect(url_for('evaluacion_dietetica'))

        return redirect(url_for('detalles_paciente', id_paciente=id_paciente, area=area))

    try:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
            pacientes = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error en la base de datos: {e}", "danger")
        return redirect(url_for('evaluacion_dietetica'))

    return render_template('nutricion/evaluacion_dietetica.html', pacientes=pacientes)

@app.route('/evaluacion_antropometrica', methods=['GET', 'POST'])
@login_required
def evaluacion_antropometrica():
    area = session.get('area')
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
        return redirect(url_for('detalles_paciente', id_paciente=id_paciente, area=area))

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
        pacientes = cursor.fetchall()
    
    return render_template('nutricion/evaluacion_antropometrica.html', pacientes=pacientes)

@app.route('/evaluacion_bioquimica', methods=['GET', 'POST'])
@login_required
def evaluacion_bioquimica():
    area = session.get('area')
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
        return redirect(url_for('detalles_paciente', id_paciente=id_paciente, area=area))
    
    with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_paciente, primer_apellido, segundo_apellido, nombres FROM pacientes")
            pacientes = cursor.fetchall()
    
    return render_template('nutricion/evaluacion_bioquimica.html', pacientes=pacientes)

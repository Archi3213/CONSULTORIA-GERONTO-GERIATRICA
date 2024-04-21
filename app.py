from flask import Flask, render_template, request, redirect, url_for
import calendar
import datetime
import uuid  # Para generar identificadores únicos

app = Flask(__name__)
now = datetime.datetime.now()
year = now.year
month = now.month

# Create a calendar for the current month
cal = calendar.monthcalendar(year, month)

# Convert the calendar to HTML
html_calendar = "<tr>"
for week in cal:
    for day in week:
        if day == 0:
            html_calendar += "<td></td>"
        else:
            html_calendar += f"<td>{day}</td>"
    html_calendar += "</tr><tr>"
html_calendar = html_calendar[:-4]  # Remove the last <tr>
pacientes_registrados = []

# Users and passwords allowed (you can add more if needed)
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
    return render_template('options.html', calendar=cal)

@app.route('/registro', methods=['GET', 'POST'])
def registro_paciente():
    if request.method == 'POST':
        primer_apellido = request.form['primer_apellido'].upper()
        segundo_apellido = request.form['segundo_apellido'].upper()
        nombres = request.form['nombres'].upper()
        fecha_nacimiento = request.form['fecha_nacimiento']
        celular = request.form['celular']
        turno = request.form['turno'].upper()
        genero = request.form['genero'].upper()
        peso = float(request.form.get('peso', ''))  # Convert to float
        altura = float(request.form.get('altura', ''))  # Convert to float
        fecha_registro = request.form['fecha_registro']
        registrado_por = request.form['registrado_por'].upper()

        # Generate a unique ID for the patient
        id_parte1 = primer_apellido[:2].upper() + segundo_apellido[:2].upper() + nombres[:2].upper()
        fecha_nacimiento_dt = datetime.datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        id_parte2 = f"{fecha_nacimiento_dt.day:02}{fecha_nacimiento_dt.month:02}{fecha_nacimiento_dt.year % 100:02}"
        id_paciente = id_parte1 + id_parte2
        altura1 = altura / 100
        altura2 = altura1 * altura1
        imc = peso / altura2

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
def consulta_paciente():
    if request.method == 'POST':
        filter_text = request.form['filter_text']
        filtered_pacientes = [p for p in pacientes_registrados if filter_text.lower() in p['nombres'].lower() or filter_text.lower() in p['id'].lower()]
        return render_template('consultar.html', pacientes=filtered_pacientes, filter_text=filter_text)
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

CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER,
    fecha_consulta DATE,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
);

# usuarios_admin.py
import random
from werkzeug.security import generate_password_hash
from flask_mysqldb import MySQL
from app import app  # importa tu app de Flask donde ya configuraste MySQL

mysql = MySQL(app)

carreras = [
    'Administración', 'Gestión aduanal', 'Biotecnología',
    'Energías alternativas', 'Telecomunicaciones',
    'Informática', 'Procesos de manufactura competitiva'
]

grados = ['3', '4', '5', '6', '7', '8']
grupos = ['A', 'B', 'C']

with app.app_context():
    cursor = mysql.connection.cursor()

    for i in range(1, 51):  # 50 usuarios
        carrera = random.choice(carreras)
        grado = random.choice(grados)
        grupo = random.choice(grupos)

        # Generar siglas de la carrera
        siglas = "".join([palabra[0] for palabra in carrera.split()][:3]).upper()
        codigo = f"{siglas}{grado}{grupo}"

        nombre = f"Alumno{i} {carrera}"
        correo = f"alumno{i}@ejemplo.com"

        # Verificar si el usuario ya existe
        cursor.execute('SELECT id FROM usuarios WHERE codigo = %s', (codigo,))
        if cursor.fetchone():
            print(f"Usuario {codigo} ya existe, se omite.")
            continue

        contrasena = generate_password_hash('12345', method='pbkdf2:sha256')

        cursor.execute('''
            INSERT INTO usuarios(nombre_completo, carrera, codigo, correo, telefono, contrasena, grado, grupo, role)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (nombre, carrera, codigo, correo, '', contrasena, grado, grupo, 'user'))
        
        print(f"Usuario {codigo} creado.")

    mysql.connection.commit()
    cursor.close()
    print("50 usuarios de prueba generados correctamente.")

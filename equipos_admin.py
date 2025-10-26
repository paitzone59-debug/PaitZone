# equipos_admin.py
import random
from app import app, mysql  # Asegúrate que tu app Flask y MySQL estén correctamente configurados

carreras = [
    'Administración', 'Gestión aduanal', 'Biotecnología',
    'Energías alternativas', 'Telecomunicaciones', 'Informática',
    'Procesos de manufactura competitiva'
]

nombres_equipos = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
    "Zeta", "Theta", "Sigma", "Omega", "Kappa",
    "Phoenix", "Dragon", "Leones", "Tiburones", "Halcones",
    "Titanes", "Lobos", "Fénix", "Centauros", "Gladiadores"
]

with app.app_context():
    cursor = mysql.connection.cursor()
    
    # Traer IDs de usuarios públicos (role 'user')
    cursor.execute("SELECT id FROM usuarios WHERE role='user'")
    usuarios_ids = [u['id'] for u in cursor.fetchall()]

    for i in range(15):  # Solo 15 equipos
        nombre_equipo = nombres_equipos[i]
        descripcion = f"Equipo de prueba {nombre_equipo}"
        max_integrantes = 5
        creador_id = random.choice(usuarios_ids)

        # Insertar equipo
        cursor.execute('''
            INSERT INTO equipos(nombre_proyecto, descripcion, max_integrantes, creador_id)
            VALUES (%s, %s, %s, %s)
        ''', (nombre_equipo, descripcion, max_integrantes, creador_id))
        equipo_id = cursor.lastrowid

        # Asignar de 1 a 3 carreras necesarias aleatorias
        carreras_necesarias = random.sample(carreras, k=random.randint(1, 3))
        for carrera in carreras_necesarias:
            cursor.execute("SELECT id FROM carreras WHERE nombre=%s", (carrera,))
            result = cursor.fetchone()
            if result:  # Verificar que exista en la tabla
                carrera_id = result['id']
                cursor.execute(
                    "INSERT INTO equipo_carreras(equipo_id, carrera_id) VALUES (%s, %s)",
                    (equipo_id, carrera_id)
                )

        # Asignar exactamente 2 integrantes aleatorios
        integrantes_aleatorios = random.sample(usuarios_ids, k=2)
        for usuario_id in integrantes_aleatorios:
            cursor.execute(
                "INSERT INTO equipo_integrantes(equipo_id, usuario_id) VALUES (%s, %s)",
                (equipo_id, usuario_id)
            )
    
    mysql.connection.commit()
    cursor.close()

print("Se han creado 15 equipos de prueba con 2 integrantes cada uno y carreras asignadas.")

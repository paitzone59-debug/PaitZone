from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb
import MySQLdb.cursors
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import g
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from filtro_groserias import contiene_groserias, verificar_campos
import os


app = Flask(__name__)
app.secret_key = "supersecretkey"


app.config['MYSQL_HOST'] = os.environ.get('MYSQLHOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQLUSER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQLPASSWORD', 'mysql')
app.config['MYSQL_DB'] = os.environ.get('MYSQLDATABASE', 'Entrelaza')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQLPORT', 44135))
app.config['MYSQL_SSL'] = False
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


if os.environ.get('MYSQLHOST'):
    database_uri = f"mysql+pymysql://{os.environ.get('MYSQLUSER')}:{os.environ.get('MYSQLPASSWORD')}@{os.environ.get('MYSQLHOST')}:{os.environ.get('MYSQLPORT', 3306)}/{os.environ.get('MYSQLDATABASE')}"
else:
    database_uri = 'mysql+pymysql://root:mysql@localhost/Entrelaza'


app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)




class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    mensaje = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.Enum('solicitud','respuesta'), nullable=False)
    leida = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)




def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash("Debes iniciar sesin", "warning")
            return redirect(url_for('login'))
        if session['usuario'].get('role') != 'admin':
            flash("No tienes permisos para acceder aqu", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/debug')
def debug():
    return " Flask est funcionando"


@app.route('/debug-db')
def debug_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        return f" Base de datos conectada: {result}"
    except Exception as e:
        return f" Error de base de datos: {str(e)}"
    
@app.route('/debug-tables')
def debug_tables():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        return f" Tablas en la BD: {tables}"
    except Exception as e:
        return f" Error al obtener tablas: {str(e)}"
    
    
@app.route('/')
def index():
    usuario = session.get('usuario')
    if not usuario:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) as total_usuarios FROM usuarios")
        total_usuarios = cursor.fetchone()['total_usuarios']
        cursor.execute("SELECT COUNT(*) as total_equipos FROM equipos")
        total_equipos = cursor.fetchone()['total_equipos']
        cursor.execute("""
            SELECT COUNT(DISTINCT e.id) as equipos_activos 
            FROM equipos e 
            JOIN equipo_integrantes ei ON e.id = ei.equipo_id
        """)
        equipos_activos = cursor.fetchone()['equipos_activos']
        cursor.close()
        return render_template(
            "inicio.html", 
            total_usuarios=total_usuarios,
            total_equipos=total_equipos,
            equipos_activos=equipos_activos
        )
    
    
    if 'turno' not in usuario:
        flash("Por favor, inicia sesin nuevamente para actualizar tu informacin", "info")
        return redirect(url_for('logout'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT DISTINCT e.*, 
            (SELECT COUNT(*) FROM equipo_integrantes ei WHERE ei.equipo_id = e.id) AS integrantes_actuales
        FROM equipos e
        JOIN equipo_carreras ec ON e.id = ec.equipo_id
        JOIN carreras c ON ec.carrera_id = c.id
        WHERE c.nombre = %s AND e.turno = %s  --  FILTRAR POR TURNO
    ''', (usuario['carrera'], usuario['turno']))
    equipos = cursor.fetchall()
    filtrados = []
    for eq in equipos:
        cursor.execute(
            'SELECT 1 FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s',
            (eq['id'], usuario['id'])
        )
        pertenece = cursor.fetchone()
        if eq['integrantes_actuales'] < eq['max_integrantes'] or pertenece:
            filtrados.append(eq)
    equipos = filtrados
    for equipo in equipos:
        cursor.execute('''
            SELECT u.id, u.nombre_completo, u.carrera, u.grado, u.grupo
            FROM equipo_integrantes ei
            JOIN usuarios u ON ei.usuario_id = u.id
            WHERE ei.equipo_id = %s
        ''', (equipo['id'],))
        equipo['integrantes'] = cursor.fetchall()
        cursor.execute('''
            SELECT c.nombre
            FROM equipo_carreras ec
            JOIN carreras c ON ec.carrera_id = c.id
            WHERE ec.equipo_id = %s
        ''', (equipo['id'],))
        equipo['carreras_necesarias'] = [c['nombre'] for c in cursor.fetchall()]
    mi_proyecto = None
    equipos_disponibles = equipos.copy()
    cursor.execute('''
        SELECT e.* FROM equipos e
        JOIN equipo_integrantes ei ON e.id = ei.equipo_id
        WHERE ei.usuario_id = %s
        LIMIT 1
    ''', (usuario['id'],))
    mi_proyecto = cursor.fetchone()
    if mi_proyecto:
        cursor.execute('''
            SELECT u.id, u.nombre_completo, u.carrera, u.grado, u.grupo
            FROM equipo_integrantes ei
            JOIN usuarios u ON ei.usuario_id = u.id
            WHERE ei.equipo_id = %s
        ''', (mi_proyecto['id'],))
        mi_proyecto['integrantes'] = cursor.fetchall()
        cursor.execute('''
            SELECT c.nombre
            FROM equipo_carreras ec
            JOIN carreras c ON ec.carrera_id = c.id
            WHERE ec.equipo_id = %s
        ''', (mi_proyecto['id'],))
        mi_proyecto['carreras_necesarias'] = [c['nombre'] for c in cursor.fetchall()]
        equipos_disponibles = [eq for eq in equipos if eq['id'] != mi_proyecto['id']]
    cursor.execute('''
        SELECT equipo_id, estado 
        FROM solicitudes 
        WHERE usuario_id = %s
    ''', (usuario['id'],))
    solicitudes_usuario = cursor.fetchall()
    cursor.close()
    return render_template(
        "project.html",
        equipos=equipos_disponibles,
        usuario=usuario,
        mi_proyecto=mi_proyecto,
        solicitudes_usuario=solicitudes_usuario
    )


@app.route('/terminos')
def terminos():
    return render_template('terminos_y_condiciones.html')

@app.route('/test')
def test():
    try:
        return " Flask est funcionando"
    except Exception as e:
        return f" Error: {str(e)}"
    

@app.route('/test-db')
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        return f" BD Conectada. Tablas: {len(tables)}"
    except Exception as e:
        return f" Error BD: {str(e)}"
    
@app.route('/admin')
@admin_required
def admin_panel():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) as total_usuarios FROM usuarios")
    total_usuarios = cursor.fetchone()['total_usuarios']
    cursor.execute("SELECT COUNT(*) as total_equipos FROM equipos")
    total_equipos = cursor.fetchone()['total_equipos']
    cursor.execute("SELECT COUNT(*) as solicitudes_pendientes FROM solicitudes WHERE estado = 'pendiente'")
    solicitudes_pendientes = cursor.fetchone()['solicitudes_pendientes']
    cursor.execute("SELECT COUNT(*) as notificaciones_sin_leer FROM notificaciones WHERE leida = FALSE")
    notificaciones_sin_leer = cursor.fetchone()['notificaciones_sin_leer']
    cursor.execute("SELECT nombre FROM carreras")
    carreras = [row['nombre'] for row in cursor.fetchall()]
    cursor.close()
    return render_template(
        'admin.html', 
        carreras=carreras,
        total_usuarios=total_usuarios,
        total_equipos=total_equipos,
        solicitudes_pendientes=solicitudes_pendientes,
        notificaciones_sin_leer=notificaciones_sin_leer
    )


@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('admin_usuarios.html', usuarios=usuarios)


@app.route('/admin/equipos')
@admin_required
def admin_equipos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM equipos")
    equipos = cursor.fetchall()
    cursor.close()
    return render_template('admin_equipos.html', equipos=equipos)


@app.route('/admin/borrar_usuario/<int:id>', methods=['POST'])
@admin_required
def borrar_usuario(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT equipo_id FROM equipo_integrantes WHERE usuario_id = %s', (id,))
    equipos = [row['equipo_id'] for row in cursor.fetchall()]
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    mysql.connection.commit()
    for equipo_id in equipos:
        cursor.execute('SELECT COUNT(*) AS total FROM equipo_integrantes WHERE equipo_id = %s', (equipo_id,))
        resultado = cursor.fetchone()
        if resultado['total'] == 0:
            cursor.execute('DELETE FROM equipo_carreras WHERE equipo_id = %s', (equipo_id,))
            cursor.execute('DELETE FROM equipos WHERE id = %s', (equipo_id,))
            mysql.connection.commit()
            flash(f"El equipo {equipo_id} qued vaco y fue eliminado automticamente", "info")
    cursor.close()
    flash("Usuario eliminado", "success")
    return redirect(url_for('admin_usuarios'))
@app.route('/admin/borrar_equipo/<int:id>', methods=['POST'])
@admin_required
def borrar_equipo(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM equipos WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()
    flash("Equipo eliminado", "success")
    return redirect(url_for('admin_equipos'))
@app.route('/admin/agregar_usuario', methods=['GET', 'POST'])
@admin_required
def agregar_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        carrera = request.form['carrera']
        grado = request.form['grado']
        grupo = request.form['grupo']
        turno = request.form['turno']  
        codigo = request.form['codigo']
        correo = request.form['correo']
        telefono = request.form['telefono']
        contrasena = request.form['contrasena']
        role = request.form.get('role', 'user')
        campos = {
            'nombre': nombre,
            'carrera': carrera,
            'grado': grado,
            'grupo': grupo,
            'cdigo': codigo
        }
        tiene_groseria, campo_problematico = verificar_campos(campos)
        if tiene_groseria:
            flash(f"El campo '{campo_problematico}' contiene palabras no permitidas. Por favor usa lenguaje apropiado.", "danger")
            return redirect(url_for('agregar_usuario'))
        hashed_password = generate_password_hash(contrasena, method='pbkdf2:sha256')
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO usuarios(nombre_completo, carrera, grado, grupo, turno, codigo, correo, telefono, contrasena, role)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (nombre, carrera, grado, grupo, turno, codigo, correo, telefono, hashed_password, role))
        mysql.connection.commit()
        cursor.close()
        flash("Usuario agregado correctamente", "success")
        return redirect(url_for('admin_usuarios'))
    return render_template('agregar_usuario.html')


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        nombre = request.form['nombre']
        carrera = request.form['carrera']
        grado = request.form['grado']
        grupo = request.form['grupo']
        turno = request.form['turno']
        codigo = request.form['codigo']
        correo = request.form['correo']
        telefono = request.form['telefono']
        password = request.form['password']
        campos = {
            'nombre': nombre,
            'carrera': carrera,
            'grado': grado,
            'grupo': grupo,
            'cdigo': codigo
        }
        tiene_groseria, campo_problematico = verificar_campos(campos)
        if tiene_groseria:
            flash(f"El campo '{campo_problematico}' contiene palabras no permitidas. Por favor usa lenguaje apropiado.", "danger")
            return redirect(url_for('register'))
        if not correo.endswith("@alumnos.udg.mx"):
            flash("Debes usar tu correo institucional (@alumnos.udg.mx)", "danger")
            return redirect(url_for('register'))
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE codigo = %s OR correo = %s", (codigo, correo))
        if cursor.fetchone():
            flash("Ya existe un usuario con ese cdigo o correo", "danger")
            cursor.close()
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        cursor.execute('''
            INSERT INTO usuarios(nombre_completo, carrera, grado, grupo, turno, codigo, correo, telefono, contrasena)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (nombre, carrera, grado, grupo, turno, codigo, correo, telefono, hashed_password))
        mysql.connection.commit()
        cursor.close()
        flash("Registro exitoso, ahora inicia sesin", "success")
        return redirect(url_for('login'))
    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        codigo = request.form['codigo']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM usuarios WHERE codigo = %s', (codigo,))
        user = cursor.fetchone()
        cursor.close()
        from werkzeug.security import check_password_hash
        if user and check_password_hash(user['contrasena'], password):
            turno = user.get('turno')
            if not turno:
                turno = 'Matutino'
                cursor = mysql.connection.cursor()
                cursor.execute('UPDATE usuarios SET turno = %s WHERE id = %s', (turno, user['id']))
                mysql.connection.commit()
                cursor.close()
            session['usuario'] = {
                'id': user['id'],
                'nombre_completo': user['nombre_completo'],
                'carrera': user['carrera'],
                'grado': user.get('grado'),
                'grupo': user.get('grupo'),
                'turno': turno,
                'codigo': user['codigo'],
                'correo': user['correo'],
                'telefono': user.get('telefono'),
                'role': user.get('role', 'user')
            }
            session['usuario_id'] = user['id']
            flash(f"Bienvenido, {user['nombre_completo']}", "success")
            if session['usuario']['role'] == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('index'))
        else:
            flash("Cdigo o contrasea incorrectos", "danger")
            return redirect(url_for('login'))
    return render_template("login.html")


@app.route('/admin/agregar_equipo', methods=['GET', 'POST'])
@admin_required
def agregar_equipo():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        max_integrantes = int(request.form['max_integrantes'])
        turno = request.form['turno']
        asesor = request.form.get('asesor', '')
        privacidad = request.form['privacidad']
        integrantes_raw = request.form.get('integrantes', '')
        carreras_seleccionadas = request.form.getlist('carreras')
        campos = {
            'nombre del proyecto': nombre,
            'descripcin': descripcion,
            'asesor': asesor,
            'integrantes': integrantes_raw
        }
        tiene_groseria, campo_problematico = verificar_campos(campos)
        if tiene_groseria:
            flash(f"El campo '{campo_problematico}' contiene palabras no permitidas. Por favor usa lenguaje apropiado.", "danger")
            return redirect(url_for('agregar_equipo'))
        cursor.execute(
            "INSERT INTO equipos(nombre_proyecto, descripcion, max_integrantes, creador_id, turno, asesor, privacidad) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (nombre, descripcion, max_integrantes, session['usuario']['id'], turno, asesor, privacidad)
        )
        equipo_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO equipo_integrantes (equipo_id, usuario_id) VALUES (%s, %s)",
            (equipo_id, session['usuario']['id'])
        )
        integrantes = [i.strip() for i in integrantes_raw.split(',') if i.strip()]
        for integrante_nombre in integrantes:
            if integrante_nombre == session['usuario']['nombre_completo']:
                continue
            cursor.execute(
                "INSERT INTO equipo_integrantes (equipo_id, usuario_id) "
                "SELECT %s, id FROM usuarios WHERE nombre_completo=%s LIMIT 1",
                (equipo_id, integrante_nombre)
            )
        for carrera_nombre in carreras_seleccionadas[:4]:
            cursor.execute("SELECT id FROM carreras WHERE nombre=%s", (carrera_nombre,))
            carrera_row = cursor.fetchone()
            if carrera_row:
                cursor.execute(
                    "INSERT INTO equipo_carreras (equipo_id, carrera_id) VALUES (%s,%s)",
                    (equipo_id, carrera_row['id'])
                )
        mysql.connection.commit()
        cursor.close()
        flash("Equipo agregado", "success")
        return redirect(url_for('admin_equipos'))
    cursor.execute("SELECT nombre FROM carreras")
    carreras_result = cursor.fetchall()
    carreras = [row['nombre'] for row in carreras_result]
    cursor.close()
    return render_template('agregar_equipo.html', carreras=carreras)


@app.route('/mi_equipo')
def mi_equipo():
    if 'usuario' not in session:
        flash("Debes iniciar sesin para ver tu proyecto", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT e.id, e.nombre_proyecto, e.descripcion, e.max_integrantes, e.asesor, e.privacidad, e.creador_id
        FROM equipos e
        JOIN equipo_integrantes ei ON e.id = ei.equipo_id
        WHERE ei.usuario_id = %s
        LIMIT 1
    ''', (usuario['id'],))
    equipo = cursor.fetchone()
    if not equipo:
        flash("No perteneces a ningn proyecto an", "info")
        cursor.close()
        return redirect(url_for('index'))
    cursor.execute('''
    SELECT u.id, 
           u.nombre_completo,
           u.carrera,
           u.telefono,
           u.grado,
           u.grupo
    FROM equipo_integrantes ei
    JOIN usuarios u ON ei.usuario_id = u.id
    WHERE ei.equipo_id = %s
''', (equipo['id'],))
    equipo['integrantes'] = cursor.fetchall()
    cursor.execute('''
        SELECT c.nombre
        FROM equipo_carreras ec
        JOIN carreras c ON ec.carrera_id = c.id
        WHERE ec.equipo_id = %s
    ''', (equipo['id'],))
    equipo['carreras_necesarias'] = [c['nombre'] for c in cursor.fetchall()]
    cursor.close()
    return render_template('mi_equipo.html', usuario=usuario, equipo=equipo)


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("Sesin cerrada", "info")
    flash("Has iniciado sesin correctamente", "success")
    return redirect(url_for('index'))
@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if 'usuario' not in session:
        flash("Debes iniciar sesin para crear un proyecto", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE id=%s", (usuario['id'],))
    if not cursor.fetchone():
        flash("Usuario no vlido", "danger")
        cursor.close()
        return redirect(url_for('index'))
    cursor.execute('SELECT * FROM equipos WHERE creador_id = %s', (usuario['id'],))
    if cursor.fetchone():
        flash("Ya creaste un equipo, no puedes crear otro", "danger")
        cursor.close()
        return redirect(url_for('index'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        max_integrantes = int(request.form['max_integrantes'])
        turno = request.form['turno']
        asesor = request.form.get('asesor', '').strip()
        integrantes_raw = request.form.get('integrantes', '')
        carreras_seleccionadas = request.form.getlist('carreras')
        privacidad = request.form.get('privacidad', 'publico')
        campos = {
            'nombre del proyecto': nombre,
            'descripcin': descripcion,
            'asesor': asesor,
            'integrantes': integrantes_raw
        }
        tiene_groseria, campo_problematico = verificar_campos(campos)
        if tiene_groseria:
            flash(f"El campo '{campo_problematico}' contiene palabras no permitidas. Por favor usa lenguaje apropiado.", "danger")
            return redirect(url_for('create_project'))
        carreras_seleccionadas = carreras_seleccionadas[:7]
        cursor.execute(
            "INSERT INTO equipos (nombre_proyecto, descripcion, max_integrantes, creador_id, asesor, turno, privacidad) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (nombre, descripcion, max_integrantes, usuario['id'], asesor, turno, privacidad)
        )
        equipo_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO equipo_integrantes (equipo_id, usuario_id) VALUES (%s, %s)",
            (equipo_id, usuario['id'])
        )
        integrantes = [i.strip() for i in integrantes_raw.split(',') if i.strip()]
        for integrante_nombre in integrantes:
            if integrante_nombre.lower() == usuario['nombre_completo'].lower():
                continue
            cursor.execute("SELECT id FROM usuarios WHERE nombre_completo=%s LIMIT 1", (integrante_nombre,))
            row = cursor.fetchone()
            if row:
                usuario_id = row['id']
                cursor.execute(
                    "SELECT 1 FROM equipo_integrantes WHERE equipo_id=%s AND usuario_id=%s",
                    (equipo_id, usuario_id)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO equipo_integrantes (equipo_id, usuario_id) VALUES (%s,%s)",
                        (equipo_id, usuario_id)
                    )
        for carrera_nombre in carreras_seleccionadas:
            cursor.execute("SELECT id FROM carreras WHERE nombre=%s", (carrera_nombre,))
            carrera_row = cursor.fetchone()
            if carrera_row:
                carrera_id = carrera_row['id']
                cantidad = int(request.form.get(f'cantidad_{carrera_nombre}', 0))
                cursor.execute(
                    "INSERT INTO equipo_carreras (equipo_id, carrera_id, cantidad) VALUES (%s,%s,%s)",
                    (equipo_id, carrera_id, cantidad)
                )
        mysql.connection.commit()
        cursor.close()
        flash("Creaste tu equipo!", "success")
        return redirect(url_for('index'))
    cursor.execute("SELECT nombre FROM carreras")
    carreras_result = cursor.fetchall()
    carreras = [row['nombre'] for row in carreras_result]
    cursor.close()
    return render_template("create_project.html", carreras=carreras)


@app.route('/unirse/<int:equipo_id>', methods=['GET', 'POST'])
def unirse(equipo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesin para unirte a un equipo", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM equipo_integrantes WHERE usuario_id = %s', (usuario['id'],))
    if cursor.fetchone():
        flash("Ya perteneces a un equipo y no puedes unirte a otro", "danger")
        cursor.close()
        return redirect(url_for('index'))
    cursor.execute('SELECT * FROM equipos WHERE id = %s', (equipo_id,))
    equipo = cursor.fetchone()
    if not equipo:
        flash("Equipo no encontrado", "danger")
        cursor.close()
        return redirect(url_for('index'))
    cursor.execute('SELECT COUNT(*) AS total FROM equipo_integrantes WHERE equipo_id = %s', (equipo_id,))
    conteo = cursor.fetchone()['total']
    if conteo >= equipo['max_integrantes']:
        flash("El equipo ya est lleno", "warning")
        cursor.close()
        return redirect(url_for('index'))
    if equipo.get('privacidad') == 'publico':
        cursor.execute('INSERT INTO equipo_integrantes(equipo_id, usuario_id) VALUES (%s, %s)', (equipo_id, usuario['id']))
        mysql.connection.commit()
        cursor.close()
        flash("Te uniste al equipo!", "success")
        return redirect(url_for('index'))
    else:
        cursor.execute('SELECT * FROM solicitudes WHERE usuario_id=%s AND equipo_id=%s AND estado="pendiente"', (usuario['id'], equipo_id))
        if cursor.fetchone():
            flash("Ya enviaste una solicitud y est pendiente", "info")
            cursor.close()
            return redirect(url_for('index'))
        cursor.execute('INSERT INTO solicitudes (usuario_id, equipo_id, estado) VALUES (%s, %s, "pendiente")', (usuario['id'], equipo_id))
        solicitud_id = cursor.lastrowid
        mensaje_admin = f"{usuario['nombre_completo']} ha solicitado unirse a tu equipo '{equipo['nombre_proyecto']}'"
        cursor.execute(
            'INSERT INTO notificaciones (usuario_id, mensaje, tipo) VALUES (%s, %s, "solicitud")',
            (equipo['creador_id'], mensaje_admin)
        )
        mensaje_usuario = f"Solicitud enviada al equipo '{equipo['nombre_proyecto']}'. Espera la respuesta del administrador."
        cursor.execute(
            'INSERT INTO notificaciones (usuario_id, mensaje, tipo) VALUES (%s, %s, "solicitud")',
            (usuario['id'], mensaje_usuario)
        )
        mysql.connection.commit()
        cursor.close()
        flash("Solicitud enviada. El creador del equipo la revisar.", "success")
        return redirect(url_for('index'))
@app.route('/cancelar_solicitud/<int:equipo_id>', methods=['POST', 'GET'])
def cancelar_solicitud(equipo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesin", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM solicitudes_equipo WHERE usuario_id=%s AND equipo_id=%s AND estado="pendiente"', (usuario['id'], equipo_id))
    mysql.connection.commit()
    cursor.close()
    flash("Solicitud cancelada", "info")
    return redirect(url_for('index'))
@app.route('/equipo/<int:equipo_id>/solicitudes')
def ver_solicitudes_equipo(equipo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesin", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id, creador_id, nombre_proyecto FROM equipos WHERE id = %s', (equipo_id,))
    equipo = cursor.fetchone()
    if not equipo:
        cursor.close()
        flash("Equipo no encontrado", "danger")
        return redirect(url_for('index'))
    if equipo['creador_id'] != usuario['id']:
        cursor.close()
        flash("No tienes permisos para ver las solicitudes de este equipo", "danger")
        return redirect(url_for('index'))
    cursor.execute("""
        SELECT 
            s.id AS solicitud_id,
            s.usuario_id,
            s.fecha,
            s.estado,
            u.nombre_completo,
            u.carrera,
            u.grado,
            u.grupo
        FROM solicitudes_equipo s
        JOIN usuarios u ON s.usuario_id = u.id
        WHERE s.equipo_id = %s AND s.estado = 'pendiente'
        ORDER BY s.fecha ASC
    """, (equipo_id,))
    solicitudes = cursor.fetchall()
    cursor.close()
    return render_template(
        'solicitudes_equipo.html',
        solicitudes=solicitudes,
        equipo_id=equipo_id,
        equipo_nombre=equipo['nombre_proyecto']
    )


@app.route('/equipo/aceptar_solicitud/<int:solicitud_id>', methods=['POST'])
def aceptar_solicitud(solicitud_id):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesin'}), 401
    usuario = session['usuario']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM solicitudes_equipo WHERE id=%s', (solicitud_id,))
    solicitud = cursor.fetchone()
    if not solicitud:
        cursor.close()
        return jsonify({'success': False, 'message': 'Solicitud no encontrada'}), 404
    cursor.execute('SELECT * FROM equipos WHERE id=%s', (solicitud['equipo_id'],))
    equipo = cursor.fetchone()
    if equipo['creador_id'] != usuario['id']:
        cursor.close()
        return jsonify({'success': False, 'message': 'No tienes permisos'}), 403
    cursor.execute('SELECT COUNT(*) AS total FROM equipo_integrantes WHERE equipo_id = %s', (equipo['id'],))
    total = cursor.fetchone()['total']
    if total >= equipo['max_integrantes']:
        cursor.execute('UPDATE solicitudes_equipo SET estado=%s WHERE id=%s', ('rechazada', solicitud_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': False, 'message': 'El equipo ya est lleno'}), 400
    cursor.execute('INSERT INTO equipo_integrantes (equipo_id, usuario_id) VALUES (%s, %s)',
                   (equipo['id'], solicitud['usuario_id']))
    cursor.execute('UPDATE solicitudes_equipo SET estado=%s WHERE id=%s', ('aceptada', solicitud_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True, 'message': 'Solicitud aceptada y usuario agregado al equipo'})
@app.route('/equipo/rechazar_solicitud/<int:solicitud_id>', methods=['POST'])
def rechazar_solicitud(solicitud_id):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesin'}), 401
    usuario = session['usuario']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM solicitudes_equipo WHERE id=%s', (solicitud_id,))
    solicitud = cursor.fetchone()
    if not solicitud:
        cursor.close()
        return jsonify({'success': False, 'message': 'Solicitud no encontrada'}), 404
    cursor.execute('SELECT * FROM equipos WHERE id=%s', (solicitud['equipo_id'],))
    equipo = cursor.fetchone()
    if equipo['creador_id'] != usuario['id']:
        cursor.close()
        return jsonify({'success': False, 'message': 'No tienes permisos'}), 403
    cursor.execute('UPDATE solicitudes_equipo SET estado=%s WHERE id=%s', ('rechazada', solicitud_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True, 'message': 'Solicitud rechazada correctamente'})
@app.route('/salir/<int:equipo_id>')
def salir(equipo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesin", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT creador_id FROM equipos WHERE id = %s', (equipo_id,))
    equipo = cursor.fetchone()
    if equipo and equipo['creador_id'] == usuario['id']:
        cursor.execute('SELECT COUNT(*) AS total FROM equipo_integrantes WHERE equipo_id = %s', (equipo_id,))
        total_integrantes = cursor.fetchone()['total']
        if total_integrantes > 1:
            cursor.close()
            flash("No puedes salir del equipo porque eres el administrador. Primero transfiere la administracin a otro integrante.", "warning")
            return redirect(url_for('mi_equipo'))
        else:
            cursor.execute('DELETE FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s', (equipo_id, usuario['id']))
            cursor.execute('DELETE FROM equipo_carreras WHERE equipo_id = %s', (equipo_id,))
            cursor.execute('DELETE FROM equipos WHERE id = %s', (equipo_id,))
            mysql.connection.commit()
            cursor.close()
            flash("Has salido del equipo y como eras el nico integrante, el equipo fue eliminado.", "info")
            return redirect(url_for('index'))
    cursor.execute('DELETE FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s', (equipo_id, usuario['id']))
    mysql.connection.commit()
    cursor.execute('SELECT COUNT(*) AS total FROM equipo_integrantes WHERE equipo_id = %s', (equipo_id,))
    resultado = cursor.fetchone()
    if resultado['total'] == 0:
        cursor.execute('DELETE FROM equipo_carreras WHERE equipo_id = %s', (equipo_id,))
        cursor.execute('DELETE FROM equipos WHERE id = %s', (equipo_id,))
        mysql.connection.commit()
        flash("El equipo qued vaco y fue eliminado automticamente", "info")
    else:
        flash("Has salido del equipo", "info")
    cursor.close()
    return redirect(url_for('index'))
@app.route('/transferir_admin/<int:equipo_id>/<int:nuevo_admin_id>', methods=['POST'])
def transferir_admin(equipo_id, nuevo_admin_id):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesin'}), 401
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT creador_id FROM equipos WHERE id = %s', (equipo_id,))
    equipo = cursor.fetchone()
    if not equipo or equipo['creador_id'] != usuario['id']:
        cursor.close()
        return jsonify({'success': False, 'message': 'No tienes permisos para transferir la administracin'}), 403
    cursor.execute('SELECT 1 FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s', (equipo_id, nuevo_admin_id))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({'success': False, 'message': 'El usuario no pertenece a este equipo'}), 400
    cursor.execute('UPDATE equipos SET creador_id = %s WHERE id = %s', (nuevo_admin_id, equipo_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True, 'message': 'Administracin transferida correctamente'})
@app.route('/perfil/<int:id>')
def perfil(id):
    origen = request.args.get('origen', 'index')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, nombre_completo, carrera, grado, grupo, turno, telefono, descripcion FROM usuarios WHERE id=%s", (id,))
    usuario_perfil = cursor.fetchone()
    cursor.close()
    if not usuario_perfil:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for('index'))
    usuario_sesion = session.get('usuario')
    return render_template("perfil.html", usuario=usuario_sesion, perfil=usuario_perfil, origen=origen)


@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'usuario' not in session:
        flash("Debes iniciar sesin", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '')
        if contiene_groserias(descripcion):
            flash("La descripcin contiene palabras no permitidas. Por favor usa lenguaje apropiado.", "danger")
            return redirect(url_for('editar_perfil'))
        cursor.execute("UPDATE usuarios SET descripcion=%s WHERE id=%s", (descripcion, usuario['id']))
        mysql.connection.commit()
        cursor.close()
        session['usuario']['descripcion'] = descripcion
        flash("Perfil actualizado", "success")
        return redirect(url_for('perfil', id=usuario['id']))
    cursor.execute("SELECT descripcion FROM usuarios WHERE id=%s", (usuario['id'],))
    descripcion = cursor.fetchone()['descripcion']
    cursor.close()
    return render_template("editar_perfil.html", descripcion=descripcion, usuario=usuario)


@app.route("/notificaciones")
def notificaciones():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    usuario_id = session["usuario_id"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT n.id, n.mensaje, n.fecha, n.tipo,
               s.id AS solicitud_id, s.estado AS solicitud_estado, s.usuario_id AS solicitante_id,
               e.creador_id
        FROM notificaciones n
        LEFT JOIN solicitudes s ON n.tipo = 'solicitud' AND s.id = n.solicitud_id
        LEFT JOIN equipos e ON s.equipo_id = e.id
        WHERE n.usuario_id = %s
        ORDER BY n.fecha DESC
    """, (usuario_id,))
    notificaciones = cursor.fetchall()
    cursor.close()
    return render_template("_notificaciones.html", notificaciones=notificaciones)


@app.route("/notificaciones/marcar_leidas", methods=['POST'])
def marcar_notificaciones_leidas():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    usuario_id = session["usuario_id"]
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE notificaciones SET leida = TRUE WHERE usuario_id = %s", (usuario_id,))
    mysql.connection.commit()
    cursor.close()
    return '', 204
@app.route('/enviar_solicitud/<int:equipo_id>')
def enviar_solicitud(equipo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesin", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT nombre_proyecto, privacidad, creador_id FROM equipos WHERE id = %s', (equipo_id,))
    equipo = cursor.fetchone()
    if not equipo:
        flash("El equipo no existe", "danger")
        cursor.close()
        return redirect(url_for('index'))
    if equipo['privacidad'] == 'publico':
        flash("Este equipo es pblico, puedes unirte directamente.", "info")
        cursor.close()
        return redirect(url_for('index'))
    cursor.execute(
        'SELECT solicitud_id, estado FROM solicitudes WHERE usuario_id = %s AND equipo_id = %s ORDER BY solicitud_id DESC LIMIT 1',
        (usuario['id'], equipo_id)
    )
    solicitud = cursor.fetchone()
    reingreso = False
    if solicitud:
        if solicitud['estado'] in ('pendiente', 'aceptada'):
            cursor.execute(
                'SELECT * FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s',
                (equipo_id, usuario['id'])
            )
            integrante = cursor.fetchone()
            if integrante:
                flash("Ya enviaste una solicitud a este equipo", "warning")
                cursor.close()
                return redirect(url_for('index'))
            else:
                cursor.execute('DELETE FROM solicitudes WHERE solicitud_id = %s', (solicitud['solicitud_id'],))
                mysql.connection.commit()
                reingreso = True
                flash("Te habas salido del equipo, pero tu nueva solicitud fue enviada correctamente ", "info")
        else:
            cursor.execute('DELETE FROM solicitudes WHERE solicitud_id = %s', (solicitud['solicitud_id'],))
            mysql.connection.commit()
    cursor.execute(
        'INSERT INTO solicitudes (usuario_id, equipo_id, estado) VALUES (%s, %s, %s)',
        (usuario['id'], equipo_id, 'pendiente')
    )
    if reingreso:
        mensaje = f"{usuario['nombre_completo']} desea volver a unirse a tu equipo '{equipo['nombre_proyecto']}' despus de haberse salido."
    else:
        mensaje = f"{usuario['nombre_completo']} ha solicitado unirse a tu equipo '{equipo['nombre_proyecto']}'"
    cursor.execute(
        'INSERT INTO notificaciones (usuario_id, mensaje, tipo) VALUES (%s, %s, "solicitud")',
        (equipo['creador_id'], mensaje)
    )
    mysql.connection.commit()
    cursor.close()
    return "OK", 200
@app.route("/aceptar_solicitud_modal/<int:id>/<int:usuario_id>", methods=['POST'])
def aceptar_solicitud_modal(id, usuario_id):
    if "usuario" not in session:
        return jsonify({'error': 'No autorizado'}), 403
    usuario_actual = session["usuario"]["id"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT s.solicitud_id, s.equipo_id, e.creador_id, e.nombre_proyecto
        FROM solicitudes s
        JOIN equipos e ON s.equipo_id = e.id
        WHERE s.solicitud_id = %s
    """, (id,))
    solicitud = cursor.fetchone()
    if not solicitud:
        cursor.close()
        return jsonify({'error': 'Solicitud no encontrada'}), 404
    if solicitud['creador_id'] != usuario_actual:
        cursor.close()
        return jsonify({'error': 'No tienes permiso para aceptar esta solicitud'}), 403
    equipo_id = solicitud['equipo_id']
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM equipo_integrantes
        WHERE equipo_id = %s
    """, (equipo_id,))
    total_miembros = cursor.fetchone()['total']
    if total_miembros >= 5:
        cursor.close()
        return jsonify({'error': 'El equipo ya est completo (mximo 5 miembros).'}), 400
    cursor.execute("UPDATE solicitudes SET estado = 'aceptada' WHERE solicitud_id = %s", (id,))
    cursor.execute("""
        INSERT IGNORE INTO equipo_integrantes (equipo_id, usuario_id)
        VALUES (%s, %s)
    """, (equipo_id, usuario_id))
    mensaje_aceptado = f"Felicidades! Fuiste aceptado en el equipo '{solicitud['nombre_proyecto']}'"
    cursor.execute("""
        INSERT INTO notificaciones (usuario_id, mensaje, tipo, leida, fecha)
        VALUES (%s, %s, 'respuesta', 0, NOW())
    """, (usuario_id, mensaje_aceptado))
    mensaje_admin = f"Aceptaste a un usuario en tu equipo '{solicitud['nombre_proyecto']}'"
    cursor.execute("""
        INSERT INTO notificaciones (usuario_id, mensaje, tipo, leida, fecha)
        VALUES (%s, %s, 'respuesta', 0, NOW())
    """, (usuario_actual, mensaje_admin))
    cursor.execute("""
        DELETE FROM notificaciones
        WHERE tipo = 'solicitud'
          AND usuario_id = %s
          AND mensaje LIKE %s
        LIMIT 1
    """, (usuario_actual, f"%{solicitud['nombre_proyecto']}%"))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True, 'estado': 'aceptada'})
@app.route("/rechazar_solicitud_admin/<int:id>/<int:usuario_id>", methods=['POST'])
def rechazar_solicitud_admin(id, usuario_id):
    if "usuario" not in session:
        return jsonify({'error': 'No autorizado'}), 403
    usuario_actual = session["usuario"]["id"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT s.solicitud_id, s.equipo_id, e.creador_id, e.nombre_proyecto
        FROM solicitudes s
        JOIN equipos e ON s.equipo_id = e.id
        WHERE s.solicitud_id = %s
    """, (id,))
    solicitud = cursor.fetchone()
    if solicitud and solicitud['creador_id'] == usuario_actual:
        cursor.execute("UPDATE solicitudes SET estado = 'rechazada' WHERE solicitud_id = %s", (id,))
        mensaje_rechazado = f"Tu solicitud para unirte al equipo '{solicitud['nombre_proyecto']}' fue rechazada"
        cursor.execute("""
            INSERT INTO notificaciones (usuario_id, mensaje, tipo, leida, fecha)
            VALUES (%s, %s, 'respuesta', 0, NOW())
        """, (usuario_id, mensaje_rechazado))
        mensaje_admin = f"Rechazaste una solicitud para tu equipo '{solicitud['nombre_proyecto']}'"
        cursor.execute("""
            INSERT INTO notificaciones (usuario_id, mensaje, tipo, leida, fecha)
            VALUES (%s, %s, 'respuesta', 0, NOW())
        """, (usuario_actual, mensaje_admin))
        cursor.execute("""
            DELETE FROM notificaciones 
            WHERE tipo = 'solicitud'
              AND usuario_id = %s
              AND mensaje LIKE %s
        """, (usuario_actual, f"%{solicitud['nombre_proyecto']}%"))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'estado': 'rechazada'})
    else:
        cursor.close()
        return jsonify({'error': 'No tienes permiso'}), 403
@app.route('/notificaciones/data')
def notificaciones_data():
    if 'usuario' not in session:
        return "No autenticado", 401
    usuario_id = session['usuario']['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id FROM equipos WHERE creador_id = %s", (usuario_id,))
    equipos_creados = [r['id'] for r in cursor.fetchall()]
    notificaciones = []
    if equipos_creados:
        cursor.execute("""
            SELECT
                s.solicitud_id,
                s.usuario_id AS solicitante_id,
                u.nombre_completo AS solicitante_nombre,
                s.equipo_id,
                e.nombre_proyecto,
                e.creador_id,
                s.estado AS solicitud_estado,
                s.fecha AS fecha
            FROM solicitudes s
            JOIN equipos e ON e.id = s.equipo_id
            JOIN usuarios u ON u.id = s.usuario_id
            WHERE e.creador_id = %s
              AND s.estado = 'pendiente'
              AND s.solicitud_id = (
                  SELECT MAX(s2.solicitud_id)
                  FROM solicitudes s2
                  WHERE s2.usuario_id = s.usuario_id
                    AND s2.equipo_id = s.equipo_id
              )
            ORDER BY s.fecha DESC
            LIMIT 50
        """, (usuario_id,))
        filas = cursor.fetchall()
        for f in filas:
            msg = f"{f['solicitante_nombre']} ha solicitado unirse a tu equipo '{f['nombre_proyecto']}'"
            notificaciones.append({
                'id': f['solicitud_id'],
                'mensaje': msg,
                'fecha': f['fecha'],
                'tipo': 'solicitud',
                'leida': 0,
                'solicitud_id': f['solicitud_id'],
                'solicitud_estado': f['solicitud_estado'],
                'solicitante_id': f['solicitante_id'],
                'equipo_id': f['equipo_id'],
                'nombre_proyecto': f['nombre_proyecto'],
                'creador_id': f['creador_id']
            })
    else:
        cursor.execute("""
            SELECT
                s.solicitud_id,
                s.equipo_id,
                s.estado AS solicitud_estado,
                s.fecha,
                e.nombre_proyecto
            FROM solicitudes s
            JOIN equipos e ON s.equipo_id = e.id
            WHERE s.usuario_id = %s
            ORDER BY s.fecha DESC
            LIMIT 20
        """, (usuario_id,))
        solicitudes_usuario = cursor.fetchall()
        for solicitud in solicitudes_usuario:
            if solicitud['solicitud_estado'] == 'pendiente':
                mensaje = f"Tu solicitud para unirte al equipo '{solicitud['nombre_proyecto']}' est pendiente"
            elif solicitud['solicitud_estado'] == 'aceptada':
                mensaje = f"Felicidades! Tu solicitud para el equipo '{solicitud['nombre_proyecto']}' fue aceptada"
            elif solicitud['solicitud_estado'] == 'rechazada':
                mensaje = f"Tu solicitud para unirte al equipo '{solicitud['nombre_proyecto']}' fue rechazada"
            else:
                mensaje = f"Tu solicitud para el equipo '{solicitud['nombre_proyecto']}' - {solicitud['solicitud_estado']}"
            notificaciones.append({
                'id': f"solicitud_{solicitud['solicitud_id']}",
                'mensaje': mensaje,
                'fecha': solicitud['fecha'],
                'tipo': 'solicitud_usuario',
                'leida': 0,
                'solicitud_id': solicitud['solicitud_id'],
                'solicitud_estado': solicitud['solicitud_estado'],
                'solicitante_id': usuario_id,
                'equipo_id': solicitud['equipo_id'],
                'nombre_proyecto': solicitud['nombre_proyecto'],
                'creador_id': None
            })
        cursor.execute("""
            SELECT 
                n.id,
                n.mensaje,
                n.fecha,
                n.tipo,
                n.leida
            FROM notificaciones n
            WHERE n.usuario_id = %s
              AND n.fecha >= NOW() - INTERVAL 7 DAY
            ORDER BY n.fecha DESC
            LIMIT 50
        """, (usuario_id,))
        notifs_normales = cursor.fetchall()
        for notif in notifs_normales:
            if not any(n.get('solicitud_id') for n in notificaciones if n.get('mensaje') == notif['mensaje']):
                notificaciones.append(notif)
    notificaciones.sort(key=lambda x: x['fecha'], reverse=True)
    cursor.close()
    return render_template('_notificaciones.html', notificaciones=notificaciones)


@app.route('/equipo/chat/<int:equipo_id>')
def chat_equipo(equipo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesin", "warning")
        return redirect(url_for('login'))
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT 1 FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s', (equipo_id, usuario['id']))
    if not cursor.fetchone():
        flash("No perteneces a este equipo", "danger")
        cursor.close()
        return redirect(url_for('index'))
    cursor.execute('SELECT nombre_proyecto FROM equipos WHERE id = %s', (equipo_id,))
    equipo = cursor.fetchone()
    cursor.execute('''
        SELECT m.*, u.nombre_completo 
        FROM mensajes_equipo m 
        JOIN usuarios u ON m.usuario_id = u.id 
        WHERE m.equipo_id = %s 
        ORDER BY m.fecha ASC 
        LIMIT 50
    ''', (equipo_id,))
    mensajes = cursor.fetchall()
    cursor.close()
    return render_template('chat_equipo.html', 
                    equipo_id=equipo_id, 
                    equipo_nombre=equipo['nombre_proyecto'],
                    mensajes=mensajes,
                    usuario=usuario)


@app.route('/equipo/chat/enviar/<int:equipo_id>', methods=['POST'])
def enviar_mensaje(equipo_id):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    usuario = session['usuario']
    if request.is_json:
        data = request.get_json()
        mensaje_texto = data.get('mensaje', '').strip()
    else:
        mensaje_texto = request.form.get('mensaje', '').strip()
    if contiene_groserias(mensaje_texto):
        return jsonify({'success': False, 'message': 'El mensaje contiene palabras no permitidas. Por favor usa lenguaje apropiado.'}), 400
    print(f" DEBUG EMOJI - Mensaje recibido: {repr(mensaje_texto)}")
    print(f" DEBUG EMOJI - Longitud: {len(mensaje_texto)}")
    print(f" DEBUG EMOJI - Tipo de datos: {'JSON' if request.is_json else 'FORM'}")
    print(f" DEBUG EMOJI - Headers: {dict(request.headers)}")
    print(f" DEBUG EMOJI - Content-Type: {request.content_type}")
    if not mensaje_texto:
        return jsonify({'success': False, 'message': 'El mensaje no puede estar vaco'}), 400
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('SELECT id, nombre_proyecto, max_mensajes FROM equipos WHERE id = %s', (equipo_id,))
        equipo = cursor.fetchone()
        if not equipo:
            cursor.close()
            print(f" Equipo {equipo_id} no existe")
            return jsonify({'success': False, 'message': 'El equipo no existe'}), 404
        cursor.execute('SELECT 1 FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s', (equipo_id, usuario['id']))
        if not cursor.fetchone():
            cursor.close()
            print(f" Usuario {usuario['id']} no pertenece al equipo {equipo_id}")
            return jsonify({'success': False, 'message': 'No perteneces a este equipo'}), 403
        cursor.execute('SELECT COUNT(*) as total FROM mensajes_equipo WHERE equipo_id = %s', (equipo_id,))
        total_mensajes = cursor.fetchone()['total']
        limite = equipo['max_mensajes'] if equipo['max_mensajes'] else 1000
        if total_mensajes >= limite * 0.95:
            mensajes_a_eliminar = max(1, total_mensajes - limite + 1)
            cursor.execute('''
                DELETE FROM mensajes_equipo 
                WHERE equipo_id = %s 
                ORDER BY fecha ASC 
                LIMIT %s
            ''', (equipo_id, mensajes_a_eliminar))
            print(f" Lmite cercano. Eliminados {mensajes_a_eliminar} mensajes antiguos")
        print(f" DEBUG EMOJI - Insertando en BD: {repr(mensaje_texto)}")
        cursor.execute(
            'INSERT INTO mensajes_equipo (equipo_id, usuario_id, mensaje) VALUES (%s, %s, %s)',
            (equipo_id, usuario['id'], mensaje_texto)
        )
        mysql.connection.commit()
        cursor.execute('SELECT mensaje FROM mensajes_equipo WHERE equipo_id = %s ORDER BY id DESC LIMIT 1', (equipo_id,))
        mensaje_guardado = cursor.fetchone()
        print(f" DEBUG EMOJI - Mensaje guardado en BD: {repr(mensaje_guardado['mensaje'])}")
        nuevo_total = total_mensajes + 1
        print(f" Mensaje enviado - Equipo: {equipo_id}, Usuario: {usuario['id']}, Total: {nuevo_total}/{limite}")
        cursor.close()
        return jsonify({'success': True, 'message': 'Mensaje enviado'})
    except Exception as e:
        print(f" ERROR enviando mensaje: {str(e)}")
        mysql.connection.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500
@app.route('/equipo/chat/mensajes/<int:equipo_id>')
def obtener_mensajes(equipo_id):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401
    usuario = session['usuario']
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('SELECT id, nombre_proyecto FROM equipos WHERE id = %s', (equipo_id,))
        equipo = cursor.fetchone()
        if not equipo:
            cursor.close()
            return jsonify({'success': False, 'message': 'El equipo no existe'}), 404
        cursor.execute('SELECT 1 FROM equipo_integrantes WHERE equipo_id = %s AND usuario_id = %s', (equipo_id, usuario['id']))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'success': False, 'message': 'No perteneces a este equipo'}), 403
        cursor.execute('''
            SELECT m.*, u.nombre_completo 
            FROM mensajes_equipo m 
            JOIN usuarios u ON m.usuario_id = u.id 
            WHERE m.equipo_id = %s 
            ORDER BY m.fecha DESC 
            LIMIT 100
        ''', (equipo_id,))
        mensajes = cursor.fetchall()
        mensajes = list(reversed(mensajes))
        cursor.close()
        mensajes_list = []
        for msg in mensajes:
            if '' in msg['mensaje'] or '' in msg['mensaje']:
                print(f" DEBUG EMOJI - Mensaje enviado al frontend: {repr(msg['mensaje'])}")
            mensajes_list.append({
                'id': msg['id'],
                'usuario_id': msg['usuario_id'],
                'usuario_nombre': msg['nombre_completo'],
                'nombre_completo': msg['nombre_completo'],
                'mensaje': msg['mensaje'],
                'fecha': msg['fecha'].strftime('%H:%M'),
                'fecha_formateada': msg['fecha'].strftime('%H:%M'),
                'es_mio': msg['usuario_id'] == usuario['id']
            })
        print(f" Mensajes enviados - Equipo: {equipo_id}, Usuario: {usuario['id']}, Total: {len(mensajes_list)}")
        return jsonify({'success': True, 'mensajes': mensajes_list})
    except Exception as e:
        print(f" ERROR cargando mensajes: {str(e)}")
        cursor.close()
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500
@app.route('/notificaciones/actualizar', methods=['POST'])
def notificaciones_actualizar():
    data = request.get_json()
    solicitud_id = data.get('solicitud_id')
    nuevo_estado = data.get('estado')
    if not solicitud_id or not nuevo_estado:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT s.*, e.nombre_proyecto, e.creador_id, e.capacidad
        FROM solicitudes s
        JOIN equipos e ON s.equipo_id = e.id
        WHERE s.solicitud_id = %s
    """, (solicitud_id,))
    solicitud = cursor.fetchone()
    if not solicitud:
        cursor.close()
        return jsonify({'success': False, 'message': 'Solicitud no encontrada'}), 404
    if nuevo_estado == "aceptada":
        cursor.execute("""
            SELECT COUNT(*) AS miembros_actuales
            FROM miembros
            WHERE equipo_id = %s
        """, (solicitud['equipo_id'],))
        miembros_actuales = cursor.fetchone()['miembros_actuales']
        if miembros_actuales >= solicitud['capacidad']:
            cursor.close()
            return jsonify({'success': False, 'message': 'El equipo ya est completo'}), 400
    cursor.execute("UPDATE solicitudes SET estado = %s WHERE solicitud_id = %s", (nuevo_estado, solicitud_id))
    mysql.connection.commit()
    estado_texto = "aceptada " if nuevo_estado == "aceptada" else "rechazada "
    mensaje = f"Tu solicitud para unirte al equipo '{solicitud['nombre_proyecto']}' fue {estado_texto}."
    cursor.execute("""
        INSERT INTO notificaciones (usuario_id, mensaje, tipo, leida)
        VALUES (%s, %s, 'respuesta', 0)
    """, (solicitud['usuario_id'], mensaje))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True, 'message': f'Solicitud {nuevo_estado} correctamente'})
@app.route('/dissolve_team/<int:equipo_id>', methods=['POST'])
def dissolve_team(equipo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesin", "warning")
        return redirect(url_for('login'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('''
            SELECT e.id, e.creador_id, COUNT(ei.usuario_id) as num_integrantes
            FROM equipos e 
            LEFT JOIN equipo_integrantes ei ON e.id = ei.equipo_id
            WHERE e.id = %s
            GROUP BY e.id, e.creador_id
        ''', (equipo_id,))
        equipo = cursor.fetchone()
        if not equipo:
            flash("El equipo no existe", "danger")
            return redirect(url_for('mi_equipo'))
        if equipo['creador_id'] != session['usuario']['id']:
            flash("No tienes permisos para disolver este equipo", "danger")
            return redirect(url_for('mi_equipo'))
        if equipo['num_integrantes'] != 1:
            flash("Solo puedes disolver el equipo si eres el nico integrante", "warning")
            return redirect(url_for('mi_equipo'))
        cursor.execute('DELETE FROM equipos WHERE id = %s', (equipo_id,))
        mysql.connection.commit()
        cursor.close()
        flash(" Equipo disuelto exitosamente", "success")
        return redirect(url_for('index'))
    except Exception as e:
        mysql.connection.rollback()
        cursor.close()
        print(f"Error al disolver equipo: {e}")
        flash(" Error al disolver el equipo", "danger")
        return redirect(url_for('mi_equipo'))
@app.context_processor
def inject_notificaciones():
    if 'usuario' in session:
        usuario_id = session['usuario']['id']
        cursor = mysql.connection.cursor()
        cursor.execute('''
            SELECT COUNT(*) AS total 
            FROM notificaciones 
            WHERE usuario_id = %s AND leida = FALSE
        ''', (usuario_id,))
        notificaciones_no_leidas = cursor.fetchone()['total']
        cursor.execute('''
            SELECT COUNT(*) AS total 
            FROM solicitudes 
            WHERE usuario_id = %s AND estado = 'pendiente'
        ''', (usuario_id,))
        solicitudes_pendientes = cursor.fetchone()['total']
        total_pendientes = notificaciones_no_leidas + solicitudes_pendientes
        cursor.close()
        return dict(notificaciones_pendientes=total_pendientes)
    return dict(notificaciones_pendientes=0)
@app.context_processor
def inject_estadisticas():
    stats = {}
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) as total_usuarios FROM usuarios")
        stats['total_usuarios'] = cursor.fetchone()['total_usuarios']
        cursor.execute("SELECT COUNT(*) as total_equipos FROM equipos")
        stats['total_equipos'] = cursor.fetchone()['total_equipos']
        cursor.close()
    except:
        stats['total_usuarios'] = 0
        stats['total_equipos'] = 0
    return stats
if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)), debug=True)
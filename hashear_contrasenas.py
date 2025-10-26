from flask import Flask
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql'
app.config['MYSQL_DB'] = 'Entrelaza'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def hashear_contrasenas():
    cursor = mysql.connection.cursor()
    
    # Traer todas las contraseñas actuales
    cursor.execute("SELECT id, contrasena FROM usuarios")
    usuarios = cursor.fetchall()
    
    for u in usuarios:
        # Evita volver a hashear si ya tiene el prefijo de hash
        if not u['contrasena'].startswith('pbkdf2:sha256:'):
            hashed = generate_password_hash(u['contrasena'], method='pbkdf2:sha256')
            cursor.execute("UPDATE usuarios SET contrasena=%s WHERE id=%s", (hashed, u['id']))
            print(f"Usuario {u['id']} actualizado")
    
    mysql.connection.commit()
    cursor.close()
    print("Todas las contraseñas se han hasheado correctamente.")

if __name__ == "__main__":
    with app.app_context():
        hashear_contrasenas()

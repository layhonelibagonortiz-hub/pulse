from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import random
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_pulse_2026'

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

UPLOAD_FOLDER = os.path.join('static', 'videos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)

# Ejemplo de validación segura en fetchone()
@app.route('/carrito')
def ver_carrito():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    result = cur.fetchone()
    if not result:
        cur.close()
        return redirect(url_for('login'))
    user_id = result[0]

    cur.execute("""
        SELECT carrito.id, productos.nombre, productos.precio, carrito.cantidad
        FROM carrito 
        JOIN productos ON carrito.producto_id = productos.id 
        WHERE carrito.usuario_id = %s
    """, (user_id,))
    items_raw = cur.fetchall()
    cur.close()
    
    # Procesar items...
    return render_template('carrito.html', items_carrito=items_raw, usuario_activo=session['usuario'])

# --- Función final corregida ---
@app.route('/empleado/eliminar_video/<int:usuario_id>/<string:dia>')
def eliminar_video_dia(usuario_id, dia):
    if 'usuario' not in session or session.get('rol') not in ['admin', 'empleado']:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE rutinas_semanales
        SET archivo_video = NULL
        WHERE usuario_id = %s AND dia_semana = %s
    """, (usuario_id, dia))
    mysql.connection.commit()
    cur.close()
    
    flash('Video eliminado correctamente.', 'success')
    return redirect(url_for('editar_rutina', usuario_id=usuario_id))

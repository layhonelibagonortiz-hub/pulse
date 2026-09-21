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


# ==========================================
# 1. RUTAS PÚBLICAS Y DE NAVEGACIÓN GENERAL
# ==========================================

@app.route('/')
def index():
    # Redirección estricta según el rol si hay una sesión activa
    if 'usuario' in session:
        if session.get('rol') == 'admin':
            return redirect(url_for('panel_admin'))
        elif session.get('rol') == 'empleado':
            return redirect(url_for('panel_empleado'))

    # Si es cliente normal o no ha iniciado sesión, ve la interfaz habitual
    return render_template('index.html', usuario_activo=session.get('usuario'))

@app.route('/quienes-somos')
def quienes_somos():
    return render_template('quienes_somos.html', usuario_activo=session.get('usuario'))

@app.route('/mision')
def mision():
    return render_template('mision.html', usuario_activo=session.get('usuario'))


# ==========================================
# 2. RUTAS DE AUTENTICACIÓN
# ==========================================

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    error = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        usuario = request.form.get('usuario')
        password_plana = request.form.get('password')
        rol = request.form.get('rol', 'cliente')
        
        # Encriptamos la contraseña antes de guardarla en la base de datos
        password_encriptada = generate_password_hash(password_plana)
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s OR correo = %s", (usuario, correo))
        usuario_existente = cur.fetchone()
        
        if usuario_existente:
            error = "Ya existe una cuenta con este usuario o correo. Por favor, <a href='/login' style='color: #f87171; text-decoration: underline; font-weight: bold;'>inicia sesión aquí</a>."
        else:
            cur.execute(
                "INSERT INTO usuarios (nombre, correo, telefono, usuario, password, rol, encuesta_completada) VALUES (%s, %s, %s, %s, %s, %s, 0)",
                (nombre, correo, telefono, usuario, password_encriptada, rol)
            )
            mysql.connection.commit()
            cur.close()
            
            session['usuario'] = usuario
            session['rol'] = rol
            return redirect(url_for('encuesta'))
            
        cur.close()
        
    return render_template('registro.html', error=error, usuario_activo=session.get('usuario'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario_ingresado = request.form.get('usuario')
        password_ingresado = request.form.get('password')
        
        cur = mysql.connection.cursor()
        # Buscamos al usuario unicamente por su nombre de usuario
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario_ingresado,))
        usuario_encontrado = cur.fetchone()
        
        if not usuario_encontrado:
            error = "El usuario no existe. Por favor, crea una cuenta."
        else:
            # Extraemos la contraseña encriptada (columna 5 en la tupla de la base de datos)
            password_encriptada = usuario_encontrado[5]
            
            # Verificamos si la contraseña ingresada coincide con la almacenada encriptada
            if check_password_hash(password_encriptada, password_ingresado):
                # Guardamos los datos necesarios en la sesión
                usuario_id = usuario_encontrado[0]
                session['usuario_id'] = usuario_id # ID numérico
                session['usuario'] = usuario_encontrado[4]    # Nombre de usuario
                session['rol'] = usuario_encontrado[6]        # Rol del usuario
                
                # --- SISTEMA DE PUNTOS: Sumar 10 puntos por constancia al iniciar sesión ---
                cur.execute("UPDATE usuarios SET puntos = puntos + 10 WHERE id = %s", (usuario_id,))
                mysql.connection.commit()
                
                cur.close()
                
                # Redirección estricta según el rol
                if session['rol'] == 'admin':
                    return redirect(url_for('panel_admin'))
                elif session['rol'] == 'empleado':
                    return redirect(url_for('panel_empleado'))
                else:
                    return redirect(url_for('index'))  # Cliente normal
            else:
                error = "Contraseña incorrecta. Inténtalo de nuevo."
                
        cur.close()
            
    return render_template('login.html', error=error, usuario_activo=session.get('usuario'))


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('rol', None)
    return redirect(url_for('index'))


# ==========================================
# 3. MÓDULO DEL CLIENTE (Tienda, Carrito, Encuesta, Entrenamientos)
# ==========================================


@app.route('/recompensas')
def recompensas():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Obtener los puntos actuales del usuario
    cur.execute("SELECT puntos FROM usuarios WHERE id = %s", (session.get('usuario_id'),))
    user_data = cur.fetchone()
    puntos_actuales = user_data['puntos'] if user_data else 0
    
    # ── CAMBIO AQUÍ: Consultar directamente de tu tabla 'productos' ──
    cur.execute("SELECT * FROM productos WHERE stock > 0")
    productos = cur.fetchall()
    
    cur.close()
    
    return render_template('recompensas.html', 
                           puntos=puntos_actuales, 
                           productos=productos, 
                           usuario_activo=session['usuario'])

@app.route('/canjear_producto/<int:producto_id>', methods=['POST'])
def canjear_producto(producto_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    user_id = session.get('usuario_id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # 1. Verificar puntos actuales del usuario
    cur.execute("SELECT puntos FROM usuarios WHERE id = %s", (user_id,))
    usuario = cur.fetchone()
    
    # 2. Verificar datos y stock del producto en la tabla 'productos'
    cur.execute("SELECT * FROM productos WHERE id = %s", (producto_id,))
    producto = cur.fetchone()
    
    if usuario and producto:
        # Calculamos los puntos requeridos dividiendo el precio entre 1000 (igual que en la vista HTML)
        puntos_requeridos = int(producto['precio'] / 1000)
        stock_actual = producto['stock']
        
        # Validar si tiene suficientes puntos
        if usuario['puntos'] >= puntos_requeridos:
            # Validar si hay stock disponible
            if stock_actual > 0:
                # Descontar los puntos al usuario
                cur.execute("UPDATE usuarios SET puntos = puntos - %s WHERE id = %s", (puntos_requeridos, user_id))
                
                # Reducir en 1 el stock del producto de forma explícita
                cur.execute("UPDATE productos SET stock = stock - 1 WHERE id = %s", (producto_id,))
                
                # Registrar el canje en el historial (si tu tabla existe)
                try:
                    cur.execute("INSERT INTO historial_canjes (usuario_id, producto_id) VALUES (%s, %s)", (user_id, producto_id))
                except Exception:
                    pass 
                    
                mysql.connection.commit()
                flash('¡Canje exitoso! Producto reclamado correctamente.', 'success')
            else:
                flash('Lo sentimos, este producto está agotado.', 'error')
        else:
            flash('No tienes suficientes Pulse Coins para canjear este producto.', 'error')
    else:
        flash('Error al procesar el producto.', 'error')
    
    cur.close()
    return redirect(url_for('recompensas'))




@app.route('/perfil')
def perfil_cliente(): # <--- Cambiado aquí
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (session['usuario'],))
    datos_usuario = cur.fetchone()
    cur.close()
    
    return render_template('perfil.html', usuario=datos_usuario, usuario_activo=session['usuario'])



@app.route('/panel_cliente')
def panel_cliente():
    if 'usuario' not in session or session.get('rol') != 'cliente':
        return redirect(url_for('login'))
    return render_template('panel_cliente.html', usuario_activo=session['usuario'])

@app.route('/tienda')
def tienda():
    # Conexión a tu base de datos y consulta
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM productos")
    lista_productos = cursor.fetchall()
    cursor.close()
    
    # Asegúrate de pasar la variable 'productos' (o como la llames en tu HTML)
    return render_template('tienda.html', productos=lista_productos, usuario_activo=session.get('usuario'))



from datetime import datetime


@app.route('/finalizar_compra', methods=['POST'])
def finalizar_compra():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    user_data = cur.fetchone()
    if not user_data:
        cur.close()
        return redirect(url_for('login'))
    user_id = user_data[0]
    
    # Obtenemos los productos del carrito y el nombre del primer producto
    cur.execute("""
        SELECT productos.nombre, productos.precio, carrito.cantidad 
        FROM carrito 
        JOIN productos ON carrito.producto_id = productos.id 
        WHERE carrito.usuario_id = %s
    """, (user_id,))
    items_carrito = cur.fetchall()
    
    if not items_carrito:
        cur.close()
        return redirect(url_for('ver_carrito'))
        
    total_compra = 0
    cantidad_total_articulos = 0
    primer_producto_nombre = items_carrito[0][0] # Guardamos el nombre del artículo
    
    for item in items_carrito:
        total_compra += float(item[1]) * int(item[2])
        cantidad_total_articulos += int(item[2])
        
    # Si hay más de 1 artículo, mostramos el nombre del primero y "y más..."
    if cantidad_total_articulos > 1:
        nombre_pedido = f"{primer_producto_nombre} (y {cantidad_total_articulos - 1} más)"
    else:
        nombre_pedido = primer_producto_nombre
        
    codigo_pedido = f"PULSE-{random.randint(1000, 9999)}"
    
    # Fecha y hora exacta (Ej: 27 de Agosto, 2026 - 05:16 PM)
    meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
             7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    now = datetime.now()
    hora_formateada = now.strftime("%I:%M %p")
    fecha_exacta = f"{now.day} de {meses[now.month]}, {now.year} - {hora_formateada}"
    
    cur.execute(
        "INSERT INTO pedidos (usuario_id, codigo_pedido, total, estado, fecha, articulos_count, nombre_producto) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (user_id, codigo_pedido, total_compra, 'En preparación', fecha_exacta, cantidad_total_articulos, nombre_pedido)
    )
    
    cur.execute("DELETE FROM carrito WHERE usuario_id = %s", (user_id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('mis_pedidos'))

@app.route('/producto/<int:id_producto>')
def detalle_producto(id_producto):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
    producto = cur.fetchone()
    cur.close()
    
    if not producto:
        return redirect(url_for('tienda'))
        
    return render_template('detalle_producto.html', producto=producto, usuario_activo=session['usuario'])

@app.route('/agregar_carrito/<int:producto_id>', methods=['POST'])
def agregar_carrito(producto_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    user_data = cur.fetchone()
    user_id = user_data[0]
    
    cur.execute("SELECT * FROM carrito WHERE usuario_id = %s AND producto_id = %s", (user_id, producto_id))
    item_existente = cur.fetchone()
    
    if item_existente:
        cur.execute("UPDATE carrito SET cantidad = cantidad + 1 WHERE usuario_id = %s AND producto_id = %s", (user_id, producto_id))
    else:
        cur.execute("INSERT INTO carrito (usuario_id, producto_id, cantidad) VALUES (%s, %s, 1)", (user_id, producto_id))
        
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('tienda'))

@app.route('/carrito')
def ver_carrito():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    user_id = cur.fetchone()[0]
    
    # Solo traemos id, nombre, precio y cantidad (calculamos el subtotal en Python para evitar decimales raros)
    cur.execute("""
        SELECT carrito.id, productos.nombre, productos.precio, carrito.cantidad
        FROM carrito 
        JOIN productos ON carrito.producto_id = productos.id 
        WHERE carrito.usuario_id = %s
    """, (user_id,))
    items_raw = cur.fetchall()
    cur.close()
    
    # Procesar y formatear precios y subtotales perfectamente
    items_carrito = []
    for item in items_raw:
        item_id = item[0]
        nombre = item[1]
        precio_num = float(item[2])  # Convertimos a float/int seguro
        cantidad = int(item[3])
        
        subtotal_num = precio_num * cantidad
        
        # Formato con puntos de miles y sin decimales
        precio_fmt = f"${int(precio_num):,}".replace(",", ".")
        subtotal_fmt = f"${int(subtotal_num):,}".replace(",", ".")
        
        items_carrito.append((item_id, nombre, precio_fmt, cantidad, subtotal_fmt))
    
    return render_template('carrito.html', items_carrito=items_carrito, usuario_activo=session['usuario'])


@app.route('/aumentar_cantidad/<int:item_id>', methods=['POST'])
def aumentar_cantidad(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("UPDATE carrito SET cantidad = cantidad + 1 WHERE id = %s", (item_id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('ver_carrito'))

@app.route('/disminuir_cantidad/<int:item_id>', methods=['POST'])
def disminuir_cantidad(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    # Primero revisamos la cantidad actual
    cur.execute("SELECT cantidad FROM carrito WHERE id = %s", (item_id,))
    resultado = cur.fetchone()
    
    if resultado:
        cantidad_actual = resultado[0]
        if cantidad_actual > 1:
            # Si es mayor a 1, restamos uno
            cur.execute("UPDATE carrito SET cantidad = cantidad - 1 WHERE id = %s", (item_id,))
        else:
            # Si es 1 y le da a disminuir, lo borramos del carrito
            cur.execute("DELETE FROM carrito WHERE id = %s", (item_id,))
            
        mysql.connection.commit()
        
    cur.close()
    return redirect(url_for('ver_carrito'))



@app.route('/eliminar_item/<int:item_id>', methods=['POST'])
def eliminar_item(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM carrito WHERE id = %s", (item_id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('ver_carrito'))



@app.route('/encuesta')
def encuesta():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('encuesta.html')

@app.route('/guardar_encuesta', methods=['POST'])
def guardar_encuesta():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    deporte = request.form.get('deporte')
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE usuarios SET deporte_principal = %s WHERE usuario = %s", (deporte, session['usuario']))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('entrenamientos'))

@app.route('/entrenamientos')
def entrenamientos():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT deporte_principal FROM usuarios WHERE usuario = %s", [session['usuario']])
    resultado = cur.fetchone()
    cur.close()
    
    deporte_usuario = resultado[0] if resultado and resultado[0] else 'Voleibol'
    return render_template('entrenamientos.html', deporte=deporte_usuario, usuario_activo=session['usuario'])

@app.route('/rutinas')
def rutinas():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return redirect(url_for('login'))

    dias_en_espanol = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    dia_ingles = datetime.now().strftime('%A')
    dia_actual = dias_en_espanol.get(dia_ingles, 'Lunes')

    cursor = mysql.connection.cursor()
    
    # Traemos TODOS los bloques creados para este usuario y día
    cursor.execute("""
        SELECT id, ejercicios, archivo_video 
        FROM rutinas_semanales 
        WHERE usuario_id = %s AND dia_semana = %s
    """, (usuario_id, dia_actual))
    
    resultados = cursor.fetchall()
    cursor.close()

    return render_template('rutinas.html', 
                           dia_actual=dia_actual,
                           rutinas_dia=resultados, 
                           usuario_activo=session.get('usuario'))

@app.route('/mis_pedidos')
def mis_pedidos():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario_actual = session['usuario']
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (usuario_actual,))
    user_data = cur.fetchone()
    if not user_data:
        cur.close()
        return redirect(url_for('login'))
    user_id = user_data[0]
    
    # Seleccionamos también el nombre del producto
    cur.execute("""
        SELECT codigo_pedido, total, fecha, estado, articulos_count, nombre_producto 
        FROM pedidos 
        WHERE usuario_id = %s AND estado != 'Cancelado'
        ORDER BY id DESC
    """, (user_id,))
    pedidos_db = cur.fetchall()
    cur.close()
    
    lista_pedidos = []
    for row in pedidos_db:
        total_num = float(row[1]) if row[1] is not None else 0.0
        total_fmt = f"{int(total_num):,}".replace(",", ".")
        
        lista_pedidos.append({
            'codigo': row[0],
            'total': total_fmt,
            'fecha': row[2] if row[2] else "Reciente",
            'estado': row[3],
            'articulos': row[4],
            'nombre_producto': row[5] if row[5] else f"Compra de {row[4]} artículo(s)"
        })
        
    return render_template('mis_pedidos.html', pedidos=lista_pedidos, usuario_activo=usuario_actual)


@app.route('/cancelar_pedido/<string:codigo_pedido>', methods=['POST'])
def cancelar_pedido(codigo_pedido):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    
    # 1. Obtener el ID del usuario actual por seguridad
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    user_data = cur.fetchone()
    if not user_data:
        cur.close()
        return redirect(url_for('login'))
    user_id = user_data[0]
    
    # 2. Verificar que el pedido pertenezca al usuario y esté en un estado cancelable (ej. 'En preparación' o 'En camino')
    cur.execute("""
        SELECT estado FROM pedidos 
        WHERE codigo_pedido = %s AND usuario_id = %s
    """, (codigo_pedido, user_id))
    pedido = cur.fetchone()
    
    if pedido:
        estado_actual = pedido[0]
        # Permitir cancelar solo si no ha sido entregado
        if estado_actual in ['En preparación', 'En camino']:
            cur.execute("""
                UPDATE pedidos 
                SET estado = 'Cancelado' 
                WHERE codigo_pedido = %s AND usuario_id = %s
            """, (codigo_pedido, user_id))
            mysql.connection.commit()
            
    cur.close()
    return redirect(url_for('mis_pedidos'))



@app.route('/comprar_prueba')
def comprar_prueba():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    user_data = cur.fetchone()
    
    if not user_data:
        cur.close()
        return redirect(url_for('login'))
        
    user_id = user_data[0]
    codigo_aleatorio = f"PULSE-{random.randint(1000, 9999)}"
    total_aleatorio = round(random.uniform(30.0, 150.0), 2)
    articulos_aleatorios = random.randint(1, 3)
    
    cur.execute(
        "INSERT INTO pedidos (usuario_id, codigo_pedido, total, estado, fecha, articulos_count) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, codigo_aleatorio, total_aleatorio, 'En preparación', '23 de Agosto, 2026', articulos_aleatorios)
    )
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('mis_pedidos'))

@app.route('/comprar_ahora/<int:producto_id>', methods=['POST'])
def comprar_ahora(producto_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    user_data = cur.fetchone()
    if not user_data:
        cur.close()
        return redirect(url_for('login'))
    user_id = user_data[0]
    
    cur.execute("SELECT nombre, precio FROM productos WHERE id = %s", (producto_id,))
    producto = cur.fetchone()
    if not producto:
        cur.close()
        return redirect(url_for('tienda'))
        
    nombre_pedido = producto[0]
    total_compra = float(producto[1])
    codigo_pedido = f"PULSE-{random.randint(1000, 9999)}"
    
    meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
             7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    now = datetime.now()
    hora_formateada = now.strftime("%I:%M %p")
    fecha_exacta = f"{now.day} de {meses[now.month]}, {now.year} - {hora_formateada}"
    
    cur.execute(
        "INSERT INTO pedidos (usuario_id, codigo_pedido, total, estado, fecha, articulos_count, nombre_producto) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (user_id, codigo_pedido, total_compra, 'En preparación', fecha_exacta, 1, nombre_pedido)
    )
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('mis_pedidos'))




# ==========================================
# 4. MÓDULO DEL EMPLEADO
# ==========================================
import MySQLdb.cursors

@app.route('/panel_empleado')
def panel_empleado():
    if 'usuario' not in session or session.get('rol') != 'empleado':
        return redirect(url_for('login'))
    return render_template('panel_empleado.html', usuario_activo=session['usuario'])



@app.route('/empleado/rutinas')
def empleado_rutinas():
    if 'usuario' not in session or session.get('rol') not in ['admin', 'empleado']:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT id, nombre, correo, usuario FROM usuarios WHERE rol = 'cliente'")
    clientes = cur.fetchall()
    cur.close()
    
    # Pasamos el rol a la plantilla para controlar el botón de "Volver"
    return render_template('empleado_rutinas.html', clientes=clientes, usuario_activo=session['usuario'], rol=session.get('rol'))


@app.route('/empleado/editar_rutina/<int:usuario_id>', methods=['GET', 'POST'])
def editar_rutina(usuario_id):
    if 'usuario' not in session or session.get('rol') not in ['admin', 'empleado']:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT id, nombre, usuario FROM usuarios WHERE id = %s", (usuario_id,))
    cliente = cur.fetchone()
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        # SI EL EMPLEADO QUIERE AGREGAR UN NUEVO BLOQUE A UN DÍA ESPECÍFICO
        if accion == 'agregar_bloque':
            dia_seleccionado = request.form.get('dia_seleccionado')
            ejercicios = request.form.get(f'nuevo_ejercicio_{dia_seleccionado}', '')
            
            nombre_video = None
            input_file_name = f'nuevo_video_{dia_seleccionado}'
            if input_file_name in request.files:
                file = request.files[input_file_name]
                if file and file.filename != '':
                    nombre_video = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_video))
            
            cur.execute("""
                INSERT INTO rutinas_semanales (usuario_id, dia_semana, ejercicios, archivo_video) 
                VALUES (%s, %s, %s, %s)
            """, (usuario_id, dia_seleccionado, ejercicios, nombre_video))
            
        else:
            # ACTUALIZACIÓN GENERAL DE LOS BLOQUES EXISTENTES
            for key, ejercicios in request.form.items():
                if key.startswith('ejercicios_'):
                    bloque_id = key.split('_')[1]
                    
                    input_file_name = f'video_{bloque_id}'
                    nombre_video = None
                    if input_file_name in request.files:
                        file = request.files[input_file_name]
                        if file and file.filename != '':
                            nombre_video = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_video))
                    
                    if nombre_video:
                        cur.execute("""
                            UPDATE rutinas_semanales 
                            SET ejercicios = %s, archivo_video = %s 
                            WHERE id = %s AND usuario_id = %s
                        """, (ejercicios, nombre_video, bloque_id, usuario_id))
                    else:
                        cur.execute("""
                            UPDATE rutinas_semanales 
                            SET ejercicios = %s 
                            WHERE id = %s AND usuario_id = %s
                        """, (ejercicios, bloque_id, usuario_id))
                        
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('editar_rutina', usuario_id=usuario_id))

    # Consultamos TODOS los bloques ordenados
    cur.execute("SELECT id, dia_semana, ejercicios, archivo_video FROM rutinas_semanales WHERE usuario_id = %s ORDER BY id ASC", (usuario_id,))
    todos_los_bloques = cur.fetchall()
    cur.close()
    
    # Agrupamos los bloques por día
    rutinas_guardadas = {}
    for row in todos_los_bloques:
        dia = row['dia_semana']
        if dia not in rutinas_guardadas:
            rutinas_guardadas[dia] = []
        rutinas_guardadas[dia].append(row)
    
    return render_template('form_rutinas.html', cliente=cliente, rutinas_guardadas=rutinas_guardadas, usuario_activo=session['usuario'])




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
    
    # Redirige de vuelta al formulario de este mismo cliente
    return redirect(url_for('editar_rutina', usuario_id=usuario_id))







@app.route('/empleado/perfil')
def perfil_empleado():
    if 'usuario' not in session or session.get('rol') != 'empleado':
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT id, nombre, correo, telefono, usuario FROM usuarios WHERE usuario = %s", (session['usuario'],))
    empleado = cur.fetchone()
    
    if not empleado:
        cur.close()
        return redirect(url_for('login'))
        
    empleado_id = empleado['id']
    
    # Total de clientes registrados en el sistema
    cur.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'cliente'")
    total_clientes = cur.fetchone()['total']
    
    # Clientes con rutina asignada (filtrando estrictamente por rol 'cliente')
    cur.execute("""
        SELECT COUNT(DISTINCT r.usuario_id) as total 
        FROM rutinas_semanales r
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE u.rol = 'cliente'
    """)
    clientes_con_rutina = cur.fetchone()['total']
    
    cur.close()
    
    return render_template('perfil_empleado.html', 
                           empleado=empleado, 
                           total_clientes=total_clientes, 
                           clientes_con_rutina=clientes_con_rutina, 
                           usuario_activo=session['usuario'])






@app.route('/empleado/eliminar_bloque_rutina/<int:bloque_id>/<int:usuario_id>')
def eliminar_bloque_rutina(bloque_id, usuario_id):
    if 'usuario' not in session or session.get('rol') not in ['admin', 'empleado']:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM rutinas_semanales WHERE id = %s", (bloque_id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('editar_rutina', usuario_id=usuario_id))











# ==========================================
# 5. MÓDULO DEL ADMINISTRADOR
# ==========================================

@app.route('/panel_admin')
def panel_admin():
    print("--- ENTRANDO A PANEL ADMIN ---")
    print("Usuario en sesión:", session.get('usuario'))
    print("Rol en sesión:", session.get('rol'))
    
    if 'usuario' not in session or session.get('rol') != 'admin':
        print("¡ACCESO DENEGADO! Redirigiendo al login...")
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, correo, telefono, usuario, rol FROM usuarios")
    usuarios_db = cur.fetchall()
    cur.close()
    
    return render_template('panel_admin.html', usuarios=usuarios_db, usuario_activo=session['usuario'])

@app.route('/admin/pedidos')
def admin_pedidos():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT pedidos.id, usuarios.usuario, pedidos.codigo_pedido, pedidos.total, pedidos.estado, pedidos.fecha 
        FROM pedidos 
        JOIN usuarios ON pedidos.usuario_id = usuarios.id 
        ORDER BY pedidos.id DESC
    """)
    pedidos_db = cur.fetchall()
    cur.close()
    
    lista_pedidos = [{'id': p[0], 'cliente': p[1], 'codigo': p[2], 'total': p[3], 'estado': p[4], 'fecha': p[5]} for p in pedidos_db]
    return render_template('admin_pedidos.html', pedidos=lista_pedidos, usuario_activo=session['usuario'])

@app.route('/admin/actualizar_estado_pedido/<int:id_pedido>', methods=['POST'])
def actualizar_estado_pedido(id_pedido):
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
        
    nuevo_estado = request.form.get('estado')
    
    cur = mysql.connection.cursor()
    # Ajusta 'estado' y 'pedidos' según los nombres reales de tus tablas y columnas
    cur.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, id_pedido))
    mysql.connection.commit() # <--- ¡Obligatorio para que se guarden los cambios!
    cur.close()
    
    return redirect(url_for('admin_pedidos'))

@app.route('/admin/actualizar_rol_usuario/<int:user_id>', methods=['POST'])
def actualizar_rol_usuario(user_id):
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
        
    nuevo_rol = request.form.get('rol')
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, user_id))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('panel_admin'))



@app.route('/admin/eliminar_pedido/<string:codigo_pedido>', methods=['POST'])
def admin_eliminar_pedido(codigo_pedido):
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM pedidos WHERE codigo_pedido = %s", (codigo_pedido,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('admin_pedidos')) # O la ruta de tu panel global de pedidos

# ==========================================
# 6. GESTIÓN DE USUARIOS (CRUD General - SOLO ADMIN)
# ==========================================

@app.route('/perfil')
def perfil():
    # Bloqueamos el acceso si no es admin (puedes cambiarlo si deseas que el cliente vea solo su perfil, 
    # pero aquí restringimos la matriz CRUD completa para que el empleado no entre)
    if 'usuario' not in session or session.get('rol') != 'admin':
        if session.get('rol') == 'empleado':
            return redirect(url_for('panel_empleado'))
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios")
    lista_usuarios = cur.fetchall()
    cur.close()
    
    return render_template('perfil.html', usuario_activo=session['usuario'], lista_usuarios=lista_usuarios)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    # Candado estricto: Solo el administrador puede modificar la matriz CRUD
    if 'usuario' not in session or session.get('rol') != 'admin':
        if session.get('rol') == 'empleado':
            return redirect(url_for('panel_empleado'))
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        usuario = request.form.get('usuario')
        rol = request.form.get('rol')
        
        cur.execute(
            "UPDATE usuarios SET nombre=%s, correo=%s, telefono=%s, usuario=%s, rol=%s WHERE id=%s",
            (nombre, correo, telefono, usuario, rol, id)
        )
        mysql.connection.commit()
        cur.close()
        # Redirige de vuelta al panel del admin (la matriz de usuarios)
        return redirect(url_for('panel_admin'))
        
    cur.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    usuario_encontrado = cur.fetchone()
    cur.close()
    
    return render_template('editar.html', user=usuario_encontrado, usuario_activo=session['usuario'])

@app.route('/eliminar/<int:id>')
def eliminar_usuario(id):
    # Candado estricto: Solo el administrador puede eliminar registros del CRUD
    if 'usuario' not in session or session.get('rol') != 'admin':
        if session.get('rol') == 'empleado':
            return redirect(url_for('panel_empleado'))
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('perfil'))


# ==========================================
# 7. EJECUCIÓN DE LA APLICACIÓN
# ==========================================

if __name__ == '__main__':
    app.run(debug=True)

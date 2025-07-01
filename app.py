from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os
import random
import json

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

DATABASE = 'quiz.db'

# Agregar funciones auxiliares al contexto de Jinja2
@app.context_processor
def utility_processor():
    def obtener_url_siguiente_pregunta(usuario_id, pregunta_id):
        siguiente_id = obtener_siguiente_pregunta_id(usuario_id, pregunta_id)
        if siguiente_id:
            return url_for('test', usuario_id=usuario_id, pregunta_id=siguiente_id)
        return url_for('resultado', usuario_id=usuario_id)
    
    def obtener_url_anterior_pregunta(usuario_id, pregunta_id):
        anterior_id = obtener_anterior_pregunta_id(usuario_id, pregunta_id)
        if anterior_id:
            return url_for('test', usuario_id=usuario_id, pregunta_id=anterior_id)
        return None
    
    def tiene_pregunta_anterior(usuario_id, pregunta_id):
        return obtener_anterior_pregunta_id(usuario_id, pregunta_id) is not None
    
    def tiene_pregunta_siguiente(usuario_id, pregunta_id):
        return obtener_siguiente_pregunta_id(usuario_id, pregunta_id) is not None
    
    return dict(
        obtener_url_siguiente_pregunta=obtener_url_siguiente_pregunta,
        obtener_url_anterior_pregunta=obtener_url_anterior_pregunta,
        tiene_pregunta_anterior=tiene_pregunta_anterior,
        tiene_pregunta_siguiente=tiene_pregunta_siguiente
    )

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = get_db_connection()
    
    # Crear tabla usuarios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            orden_preguntas TEXT
        )
    ''')
    
    # Migración: agregar columna orden_preguntas si no existe
    try:
        conn.execute('ALTER TABLE usuarios ADD COLUMN orden_preguntas TEXT')
    except sqlite3.OperationalError:
        # La columna ya existe
        pass
    
    # Actualizar usuarios sin orden_preguntas
    usuarios_sin_orden = conn.execute(
        'SELECT id FROM usuarios WHERE orden_preguntas IS NULL'
    ).fetchall()
    
    for usuario in usuarios_sin_orden:
        orden_aleatorio = generar_orden_aleatorio()
        conn.execute(
            'UPDATE usuarios SET orden_preguntas = ? WHERE id = ?',
            (orden_aleatorio, usuario['id'])
        )
    
    # Crear tabla preguntas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            opcion_b TEXT NOT NULL,
            opcion_c TEXT NOT NULL,
            opcion_d TEXT NOT NULL,
            correcta TEXT NOT NULL CHECK(correcta IN ('a', 'b', 'c', 'd'))
        )
    ''')
    
    # Crear tabla respuestas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS respuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pregunta_id INTEGER NOT NULL,
            respuesta_usuario TEXT NOT NULL CHECK(respuesta_usuario IN ('a', 'b', 'c', 'd')),
            es_correcta BOOLEAN NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (pregunta_id) REFERENCES preguntas (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def generar_orden_aleatorio():
    """Genera un orden aleatorio de todas las preguntas disponibles"""
    conn = get_db_connection()
    preguntas = conn.execute('SELECT id FROM preguntas ORDER BY id').fetchall()
    conn.close()
    
    ids_preguntas = [p['id'] for p in preguntas]
    random.shuffle(ids_preguntas)
    return json.dumps(ids_preguntas)

def obtener_orden_preguntas(usuario_id):
    """Obtiene el orden de preguntas para un usuario específico"""
    conn = get_db_connection()
    usuario = conn.execute('SELECT orden_preguntas FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    conn.close()
    
    if usuario and usuario['orden_preguntas']:
        return json.loads(usuario['orden_preguntas'])
    return []

def obtener_numero_pregunta_en_orden(usuario_id, pregunta_id):
    """Obtiene el número de pregunta en el orden aleatorio del usuario"""
    orden = obtener_orden_preguntas(usuario_id)
    try:
        return orden.index(pregunta_id) + 1
    except ValueError:
        return 0

def obtener_siguiente_pregunta_id(usuario_id, pregunta_actual_id):
    """Obtiene el ID de la siguiente pregunta en el orden aleatorio"""
    orden = obtener_orden_preguntas(usuario_id)
    try:
        indice_actual = orden.index(pregunta_actual_id)
        if indice_actual + 1 < len(orden):
            return orden[indice_actual + 1]
    except ValueError:
        pass
    return None

def obtener_anterior_pregunta_id(usuario_id, pregunta_actual_id):
    """Obtiene el ID de la pregunta anterior en el orden aleatorio"""
    orden = obtener_orden_preguntas(usuario_id)
    try:
        indice_actual = orden.index(pregunta_actual_id)
        if indice_actual > 0:
            return orden[indice_actual - 1]
    except ValueError:
        pass
    return None

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro de usuario"""
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        
        if not nombre:
            flash('El nombre es obligatorio', 'error')
            return redirect(url_for('registro'))
        
        # Generar orden aleatorio de preguntas
        orden_aleatorio = generar_orden_aleatorio()
        
        conn = get_db_connection()
        cursor = conn.execute(
            'INSERT INTO usuarios (nombre, fecha, orden_preguntas) VALUES (?, ?, ?)',
            (nombre, datetime.now(), orden_aleatorio)
        )
        usuario_id = cursor.lastrowid
        
        # Obtener la primera pregunta del orden aleatorio
        orden_preguntas = json.loads(orden_aleatorio)
        primera_pregunta_id = orden_preguntas[0] if orden_preguntas else None
        
        conn.commit()
        conn.close()
        
        if primera_pregunta_id:
            flash(f'Usuario {nombre} registrado exitosamente', 'success')
            return redirect(url_for('test', usuario_id=usuario_id, pregunta_id=primera_pregunta_id))
        else:
            flash('No hay preguntas disponibles en el sistema', 'error')
            return redirect(url_for('index'))
    
    return render_template('registro.html')

@app.route('/test/<int:usuario_id>/<int:pregunta_id>')
def test(usuario_id, pregunta_id):
    """Mostrar pregunta del test"""
    conn = get_db_connection()
    
    # Verificar que el usuario existe
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('index'))
    
    # Obtener la pregunta
    pregunta = conn.execute('SELECT * FROM preguntas WHERE id = ?', (pregunta_id,)).fetchone()
    if not pregunta:
        # Si no hay más preguntas, ir al resultado
        return redirect(url_for('resultado', usuario_id=usuario_id))
    
    # Verificar si ya se respondió esta pregunta
    respuesta_existente = conn.execute(
        'SELECT * FROM respuestas WHERE usuario_id = ? AND pregunta_id = ?',
        (usuario_id, pregunta_id)
    ).fetchone()
    
    # Obtener el número de pregunta en el orden aleatorio del usuario
    pregunta_actual = obtener_numero_pregunta_en_orden(usuario_id, pregunta_id)
    
    # Contar total de preguntas
    total_preguntas = conn.execute('SELECT COUNT(*) as count FROM preguntas').fetchone()['count']
    
    conn.close()
    
    return render_template('test.html', 
                         usuario=usuario, 
                         pregunta=pregunta, 
                         pregunta_actual=pregunta_actual,
                         total_preguntas=total_preguntas,
                         ya_respondida=respuesta_existente is not None)

@app.route('/responder', methods=['POST'])
def responder():
    """Procesar respuesta del usuario"""
    usuario_id = int(request.form['usuario_id'])
    pregunta_id = int(request.form['pregunta_id'])
    respuesta_usuario = request.form['respuesta']
    
    conn = get_db_connection()
    
    # Verificar si ya se respondió esta pregunta
    respuesta_existente = conn.execute(
        'SELECT * FROM respuestas WHERE usuario_id = ? AND pregunta_id = ?',
        (usuario_id, pregunta_id)
    ).fetchone()
    
    if respuesta_existente:
        flash('Ya has respondido esta pregunta', 'warning')
        siguiente_pregunta_id = obtener_siguiente_pregunta_id(usuario_id, pregunta_id)
        if siguiente_pregunta_id:
            return redirect(url_for('test', usuario_id=usuario_id, pregunta_id=siguiente_pregunta_id))
        else:
            return redirect(url_for('resultado', usuario_id=usuario_id))
    
    # Obtener la respuesta correcta
    pregunta = conn.execute('SELECT correcta FROM preguntas WHERE id = ?', (pregunta_id,)).fetchone()
    es_correcta = respuesta_usuario == pregunta['correcta']
    
    # Guardar la respuesta
    conn.execute(
        'INSERT INTO respuestas (usuario_id, pregunta_id, respuesta_usuario, es_correcta) VALUES (?, ?, ?, ?)',
        (usuario_id, pregunta_id, respuesta_usuario, es_correcta)
    )
    conn.commit()
    
    # Mostrar si fue correcta o no
    if es_correcta:
        flash('¡Respuesta correcta!', 'success')
    else:
        opciones = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'}
        flash(f'Respuesta incorrecta. La respuesta correcta era la opción {opciones[pregunta["correcta"]]}', 'error')
    
    # Buscar la siguiente pregunta en el orden aleatorio del usuario
    siguiente_pregunta_id = obtener_siguiente_pregunta_id(usuario_id, pregunta_id)
    
    conn.close()
    
    # Ir a la siguiente pregunta o al resultado si no hay más
    if siguiente_pregunta_id:
        return redirect(url_for('test', usuario_id=usuario_id, pregunta_id=siguiente_pregunta_id))
    else:
        return redirect(url_for('resultado', usuario_id=usuario_id))

@app.route('/resultado/<int:usuario_id>')
def resultado(usuario_id):
    """Mostrar resultado final del test"""
    conn = get_db_connection()
      # Obtener información del usuario
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('index'))
    
    # Convertir fecha string a datetime object para usar strftime en el template
    try:
        fecha_dt = datetime.fromisoformat(usuario['fecha'].replace('Z', '+00:00'))
    except:
        fecha_dt = datetime.now()
    
    # Crear un diccionario con la información del usuario incluyendo fecha convertida
    usuario_dict = dict(usuario)
    usuario_dict['fecha'] = fecha_dt
    
    # Obtener estadísticas del usuario
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_respuestas,
            SUM(CASE WHEN es_correcta = 1 THEN 1 ELSE 0 END) as correctas,
            SUM(CASE WHEN es_correcta = 0 THEN 1 ELSE 0 END) as incorrectas
        FROM respuestas 
        WHERE usuario_id = ?
    ''', (usuario_id,)).fetchone()
    
    # Obtener detalles de las respuestas incorrectas
    respuestas_incorrectas = conn.execute('''
        SELECT 
            p.id,
            p.texto,
            p.opcion_a,
            p.opcion_b,
            p.opcion_c,
            p.opcion_d,
            p.correcta,
            r.respuesta_usuario
        FROM respuestas r
        JOIN preguntas p ON r.pregunta_id = p.id
        WHERE r.usuario_id = ? AND r.es_correcta = 0
        ORDER BY p.id
    ''', (usuario_id,)).fetchall()
    
    total_preguntas = conn.execute('SELECT COUNT(*) as count FROM preguntas').fetchone()['count']
    
    conn.close()
    
    # Manejar casos donde correctas puede ser None (sin respuestas)
    correctas = stats['correctas'] if stats['correctas'] is not None else 0
    porcentaje = (correctas / total_preguntas * 100) if total_preguntas > 0 else 0
    
    return render_template('resultado.html',
                         usuario=usuario_dict, 
                         stats=stats, 
                         total_preguntas=total_preguntas,
                         total=total_preguntas,
                         porcentaje=round(porcentaje, 2),
                         correctas=correctas,
                         incorrectas=stats['incorrectas'] if stats['incorrectas'] is not None else 0,
                         respuestas_incorrectas=respuestas_incorrectas)

@app.route('/ranking')
def ranking():
    """Mostrar ranking de mejores puntajes"""
    conn = get_db_connection()
      # Obtener ranking de usuarios con sus puntajes
    ranking_data = conn.execute('''
        SELECT 
            u.nombre,
            u.fecha,
            COUNT(r.id) as total_respuestas,
            SUM(CASE WHEN r.es_correcta = 1 THEN 1 ELSE 0 END) as correctas,
            ROUND(SUM(CASE WHEN r.es_correcta = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(r.id), 2) as porcentaje
        FROM usuarios u
        LEFT JOIN respuestas r ON u.id = r.usuario_id
        GROUP BY u.id, u.nombre, u.fecha
        HAVING COUNT(r.id) > 0
        ORDER BY correctas DESC, porcentaje DESC, u.fecha ASC
        LIMIT 20
    ''').fetchall()
    
    # Convertir fechas string a datetime objects
    ranking_list = []
    for row in ranking_data:
        row_dict = dict(row)
        try:
            row_dict['fecha'] = datetime.fromisoformat(row['fecha'].replace('Z', '+00:00'))
        except:
            row_dict['fecha'] = datetime.now()
        ranking_list.append(row_dict)
    
    conn.close()
    
    return render_template('ranking.html', ranking=ranking_list)

if __name__ == '__main__':
    # Crear la base de datos si no existe
    if not os.path.exists(DATABASE):
        init_db()
        print("Base de datos creada")
    
    app.run(debug=True)

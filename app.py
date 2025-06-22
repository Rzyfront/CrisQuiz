from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

DATABASE = 'quiz.db'

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
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
        
        conn = get_db_connection()
        cursor = conn.execute(
            'INSERT INTO usuarios (nombre, fecha) VALUES (?, ?)',
            (nombre, datetime.now())
        )
        usuario_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        flash(f'Usuario {nombre} registrado exitosamente', 'success')
        return redirect(url_for('test', usuario_id=usuario_id, pregunta_id=1))
    
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
    
    # Contar total de preguntas
    total_preguntas = conn.execute('SELECT COUNT(*) as count FROM preguntas').fetchone()['count']
    
    conn.close()
    
    return render_template('test.html', 
                         usuario=usuario, 
                         pregunta=pregunta, 
                         pregunta_actual=pregunta_id,
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
        return redirect(url_for('test', usuario_id=usuario_id, pregunta_id=pregunta_id + 1))
    
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
    
    conn.close()
    
    # Ir a la siguiente pregunta
    return redirect(url_for('test', usuario_id=usuario_id, pregunta_id=pregunta_id + 1))

@app.route('/resultado/<int:usuario_id>')
def resultado(usuario_id):
    """Mostrar resultado final del test"""
    conn = get_db_connection()
    
    # Obtener información del usuario
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('index'))
      # Obtener estadísticas del usuario
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_respuestas,
            SUM(CASE WHEN es_correcta = 1 THEN 1 ELSE 0 END) as correctas,
            SUM(CASE WHEN es_correcta = 0 THEN 1 ELSE 0 END) as incorrectas
        FROM respuestas 
        WHERE usuario_id = ?
    ''', (usuario_id,)).fetchone()
    
    total_preguntas = conn.execute('SELECT COUNT(*) as count FROM preguntas').fetchone()['count']
    
    conn.close()
    
    # Manejar casos donde correctas puede ser None (sin respuestas)
    correctas = stats['correctas'] if stats['correctas'] is not None else 0
    porcentaje = (correctas / total_preguntas * 100) if total_preguntas > 0 else 0
    
    return render_template('resultado.html', 
                         usuario=usuario, 
                         stats=stats, 
                         total_preguntas=total_preguntas,
                         porcentaje=round(porcentaje, 2))

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
    
    conn.close()
    
    return render_template('ranking.html', ranking=ranking_data)

if __name__ == '__main__':
    # Crear la base de datos si no existe
    if not os.path.exists(DATABASE):
        init_db()
        print("Base de datos creada")
    
    app.run(debug=True)

#!/usr/bin/env python3
"""
Script para migrar la base de datos agregando la columna orden_preguntas
"""

import sqlite3
import json
import random

def get_db_connection():
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    return conn

def generar_orden_aleatorio():
    """Genera un orden aleatorio de todas las preguntas disponibles"""
    conn = get_db_connection()
    preguntas = conn.execute('SELECT id FROM preguntas ORDER BY id').fetchall()
    conn.close()
    
    ids_preguntas = [p['id'] for p in preguntas]
    random.shuffle(ids_preguntas)
    return json.dumps(ids_preguntas)

def migrate_database():
    """Migra la base de datos agregando la columna orden_preguntas"""
    print("Iniciando migración de la base de datos...")
    
    conn = get_db_connection()
    
    # Verificar si la columna ya existe
    cursor = conn.execute("PRAGMA table_info(usuarios)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'orden_preguntas' not in columns:
        print("Agregando columna orden_preguntas...")
        conn.execute('ALTER TABLE usuarios ADD COLUMN orden_preguntas TEXT')
        print("✓ Columna agregada exitosamente")
    else:
        print("✓ La columna orden_preguntas ya existe")
    
    # Actualizar usuarios sin orden_preguntas
    usuarios_sin_orden = conn.execute(
        'SELECT id, nombre FROM usuarios WHERE orden_preguntas IS NULL OR orden_preguntas = ""'
    ).fetchall()
    
    if usuarios_sin_orden:
        print(f"Actualizando {len(usuarios_sin_orden)} usuarios sin orden aleatorio...")
        
        for usuario in usuarios_sin_orden:
            orden_aleatorio = generar_orden_aleatorio()
            conn.execute(
                'UPDATE usuarios SET orden_preguntas = ? WHERE id = ?',
                (orden_aleatorio, usuario['id'])
            )
            print(f"✓ Usuario '{usuario['nombre']}' (ID: {usuario['id']}) actualizado")
    else:
        print("✓ Todos los usuarios ya tienen orden aleatorio asignado")
    
    conn.commit()
    conn.close()
    
    print("✓ Migración completada exitosamente")

if __name__ == '__main__':
    migrate_database()

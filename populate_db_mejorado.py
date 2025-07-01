#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script mejorado para poblar la base de datos con TODAS las preguntas del archivo Questions.md
Incluye preguntas de verdadero/falso y preguntas con múltiples opciones
"""

import sqlite3
import re
import os

DATABASE = 'quiz.db'

def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def limpiar_base_datos():
    """Limpia las preguntas existentes en la base de datos"""
    conn = get_db_connection()
    
    print("🧹 Limpiando preguntas existentes...")
    # Primero eliminar respuestas que referencian preguntas
    conn.execute('DELETE FROM respuestas')
    # Luego eliminar preguntas
    conn.execute('DELETE FROM preguntas')
    # Reiniciar el contador de autoincrement
    conn.execute('DELETE FROM sqlite_sequence WHERE name="preguntas"')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos limpiada.")

def extraer_preguntas_mejorado(archivo_path):
    """Extrae TODAS las preguntas del archivo Questions.md, incluyendo verdadero/falso"""
    
    if not os.path.exists(archivo_path):
        print(f"❌ Error: El archivo {archivo_path} no existe.")
        return []
    
    with open(archivo_path, 'r', encoding='utf-8') as file:
        contenido = file.read()
    
    preguntas = []
    
    # Patrón regex más flexible para capturar todas las preguntas
    patron_pregunta = r'\*\*(\d+)\.\*\*\s*(.*?)\n\n```\n(.*?)\n```\n```\nRespuesta:\s*([A-D])\n```'
    
    matches = re.findall(patron_pregunta, contenido, re.DOTALL)
    
    print(f"📊 Encontradas {len(matches)} preguntas en el archivo.")
    
    for match in matches:
        numero, texto_pregunta, opciones_texto, respuesta_correcta = match
        
        # Limpiar el texto de la pregunta
        texto_pregunta = texto_pregunta.strip()
        
        # Extraer las opciones
        opciones_lineas = opciones_texto.strip().split('\n')
        opciones = {}
        
        for linea in opciones_lineas:
            linea = linea.strip()
            if linea.startswith('a.'):
                opciones['a'] = linea[2:].strip()
            elif linea.startswith('b.'):
                opciones['b'] = linea[2:].strip()
            elif linea.startswith('c.'):
                opciones['c'] = linea[2:].strip()
            elif linea.startswith('d.'):
                opciones['d'] = linea[2:].strip()
        
        # Verificar que tenemos al menos opciones a y b
        if 'a' in opciones and 'b' in opciones:
            # Completar opciones faltantes para preguntas de verdadero/falso
            if 'c' not in opciones or not opciones['c']:
                opciones['c'] = ''
            if 'd' not in opciones or not opciones['d']:
                opciones['d'] = ''
            
            pregunta = {
                'numero': int(numero),
                'texto': texto_pregunta,
                'opcion_a': opciones['a'],
                'opcion_b': opciones['b'],
                'opcion_c': opciones['c'],
                'opcion_d': opciones['d'],
                'correcta': respuesta_correcta.lower()
            }
            preguntas.append(pregunta)
            
            # Mostrar progreso
            if len(preguntas) % 25 == 0:
                print(f"📝 Procesadas {len(preguntas)} preguntas...")
                
        else:
            print(f"⚠️ Pregunta {numero} no tiene opciones a y b mínimas:")
            print(f"   Texto: {texto_pregunta[:100]}...")
            print(f"   Opciones encontradas: {list(opciones.keys())}")
            print(f"   Contenido opciones: {opciones}")
    
    print(f"✅ Se procesaron exitosamente {len(preguntas)} preguntas")
    return preguntas

def insertar_preguntas_en_db(preguntas):
    """Inserta las preguntas en la base de datos"""
    
    if not preguntas:
        print("❌ No hay preguntas para insertar.")
        return 0
    
    conn = get_db_connection()
    
    print(f"💾 Insertando {len(preguntas)} preguntas en la base de datos...")
    
    insertadas = 0
    errores = 0
    
    for pregunta in preguntas:
        try:
            conn.execute('''
                INSERT INTO preguntas (texto, opcion_a, opcion_b, opcion_c, opcion_d, correcta)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                pregunta['texto'],
                pregunta['opcion_a'],
                pregunta['opcion_b'],
                pregunta['opcion_c'],
                pregunta['opcion_d'],
                pregunta['correcta']
            ))
            insertadas += 1
            
            if insertadas % 50 == 0:
                print(f"   💾 Insertadas {insertadas} preguntas...")
                
        except sqlite3.Error as e:
            print(f"❌ Error al insertar pregunta {pregunta['numero']}: {e}")
            errores += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Proceso completado:")
    print(f"   ✅ Preguntas insertadas exitosamente: {insertadas}")
    print(f"   ❌ Errores: {errores}")
    
    return insertadas

def verificar_insercion():
    """Verifica que las preguntas se insertaron correctamente"""
    conn = get_db_connection()
    
    # Contar preguntas
    total = conn.execute('SELECT COUNT(*) as count FROM preguntas').fetchone()['count']
    print(f"\n📊 Total de preguntas en la base de datos: {total}")
    
    # Contar preguntas de verdadero/falso (opciones c y d vacías)
    verdadero_falso = conn.execute(
        'SELECT COUNT(*) as count FROM preguntas WHERE opcion_c = "" AND opcion_d = ""'
    ).fetchone()['count']
    print(f"📊 Preguntas de Verdadero/Falso: {verdadero_falso}")
    
    # Contar preguntas de múltiple opción
    multiple_opcion = conn.execute(
        'SELECT COUNT(*) as count FROM preguntas WHERE opcion_c != "" AND opcion_d != ""'
    ).fetchone()['count']
    print(f"📊 Preguntas de múltiple opción: {multiple_opcion}")
    
    # Mostrar algunas preguntas de ejemplo
    if total > 0:
        print(f"\n📝 Primeras 3 preguntas:")
        primeras = conn.execute('SELECT id, texto, opcion_a, opcion_b, opcion_c, opcion_d, correcta FROM preguntas LIMIT 3').fetchall()
        for i, pregunta in enumerate(primeras, 1):
            print(f"\n{i}. {pregunta['texto'][:80]}...")
            print(f"   a. {pregunta['opcion_a']}")
            print(f"   b. {pregunta['opcion_b']}")
            if pregunta['opcion_c']:
                print(f"   c. {pregunta['opcion_c']}")
            if pregunta['opcion_d']:
                print(f"   d. {pregunta['opcion_d']}")
            print(f"   Respuesta: {pregunta['correcta'].upper()}")
    
    conn.close()

def verificar_esquema_db():
    """Verifica que el esquema de la base de datos sea compatible"""
    if not os.path.exists(DATABASE):
        print(f"❌ Error: No se encontró la base de datos {DATABASE}")
        print("   Asegúrate de que la aplicación se ha ejecutado al menos una vez para crear la base de datos.")
        return False
    
    try:
        conn = get_db_connection()
        # Verificar que existe la tabla preguntas
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='preguntas'")
        if not cursor.fetchone():
            print("❌ Error: La tabla 'preguntas' no existe en la base de datos.")
            return False
        
        # Verificar columnas de la tabla
        cursor = conn.execute("PRAGMA table_info(preguntas)")
        columnas = [row[1] for row in cursor.fetchall()]
        columnas_requeridas = ['id', 'texto', 'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d', 'correcta']
        
        for col in columnas_requeridas:
            if col not in columnas:
                print(f"❌ Error: La columna '{col}' no existe en la tabla preguntas.")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar el esquema: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 SCRIPT MEJORADO DE POBLACIÓN DE PREGUNTAS")
    print("   Incluye preguntas de verdadero/falso y múltiple opción")
    print("=" * 60)
    
    archivo_preguntas = 'Questions.md'
    
    # Verificaciones previas
    if not os.path.exists(archivo_preguntas):
        print(f"❌ Error: No se encontró el archivo {archivo_preguntas}")
        return
    
    if not verificar_esquema_db():
        return
    
    # Preguntar sobre limpiar datos existentes
    respuesta = input("\n¿Deseas limpiar las preguntas existentes antes de insertar las nuevas? (s/n): ")
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        limpiar_base_datos()
    
    # Extraer preguntas del archivo
    print(f"\n📖 Extrayendo preguntas del archivo {archivo_preguntas}...")
    preguntas = extraer_preguntas_mejorado(archivo_preguntas)
    
    if preguntas:
        # Insertar preguntas en la base de datos
        insertadas = insertar_preguntas_en_db(preguntas)
        
        if insertadas > 0:
            # Verificar la inserción
            print("\n🔍 Verificando inserción...")
            verificar_insercion()
            
            print(f"\n🎉 ¡Proceso completado exitosamente!")
            print(f"   Se insertaron {insertadas} preguntas en la base de datos.")
        else:
            print("\n❌ No se pudieron insertar preguntas en la base de datos.")
    else:
        print("\n❌ No se pudieron extraer preguntas del archivo.")

if __name__ == "__main__":
    main()

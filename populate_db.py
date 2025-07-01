#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para poblar la base de datos con preguntas del archivo Questions.md
"""

import sqlite3
import re
import os

def leer_preguntas_desde_archivo(archivo):
    """
    Lee las preguntas del archivo Questions.md y las parsea
    """
    preguntas = []
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Patrón para encontrar preguntas con formato **número.** 
        patron_pregunta = r'\*\*(\d+)\.\*\*\s*(.*?)\n\n```\n(.*?)\n```\n```\nRespuesta:\s*([ABCD])\n```'
        
        matches = re.findall(patron_pregunta, contenido, re.DOTALL)
        
        for match in matches:
            numero = int(match[0])
            texto_pregunta = match[1].strip()
            opciones_texto = match[2].strip()
            respuesta_correcta = match[3].strip()
            
            # Parsear las opciones
            lineas_opciones = opciones_texto.split('\n')
            opciones = {'a': '', 'b': '', 'c': '', 'd': ''}
            
            for linea in lineas_opciones:
                linea = linea.strip()
                if linea.startswith('a.'):
                    opciones['a'] = linea[2:].strip()
                elif linea.startswith('b.'):
                    opciones['b'] = linea[2:].strip()
                elif linea.startswith('c.'):
                    opciones['c'] = linea[2:].strip()
                elif linea.startswith('d.'):
                    opciones['d'] = linea[2:].strip()
            
            # Verificar que tenemos todas las opciones
            if all(opciones.values()):
                pregunta = {
                    'numero': numero,
                    'texto': texto_pregunta,
                    'opcion_a': opciones['a'],
                    'opcion_b': opciones['b'],
                    'opcion_c': opciones['c'],
                    'opcion_d': opciones['d'],
                    'correcta': respuesta_correcta.lower()  # Convertir a minúsculas
                }
                preguntas.append(pregunta)
                print(f"✓ Pregunta {numero} parseada correctamente")
            else:
                print(f"⚠ Pregunta {numero} tiene opciones incompletas, se omite")
    
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {archivo}")
        return []
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        return []
    
    return preguntas

def crear_base_datos():
    """
    Crea la base de datos y la tabla de preguntas si no existe
    """
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    
    # Crear tabla de preguntas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            opcion_b TEXT NOT NULL,
            opcion_c TEXT NOT NULL,
            opcion_d TEXT NOT NULL,
            correcta TEXT NOT NULL
        )
    ''')
    
    # Crear tabla de resultados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            puntaje INTEGER NOT NULL,
            total_preguntas INTEGER NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def insertar_preguntas(conn, preguntas):
    """
    Inserta las preguntas en la base de datos
    """
    cursor = conn.cursor()
    
    # Limpiar tabla existente
    cursor.execute('DELETE FROM preguntas')
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="preguntas"')
    
    # Insertar preguntas
    insertadas = 0
    for pregunta in preguntas:
        try:
            cursor.execute('''
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
        except Exception as e:
            print(f"❌ Error al insertar pregunta {pregunta['numero']}: {e}")
    
    conn.commit()
    return insertadas

def verificar_insercion(conn):
    """
    Verifica que las preguntas se insertaron correctamente
    """
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM preguntas')
    total = cursor.fetchone()[0]
    
    print(f"\n📊 Verificación:")
    print(f"Total de preguntas en la base de datos: {total}")
    
    # Mostrar algunas preguntas de ejemplo
    cursor.execute('SELECT id, texto, correcta FROM preguntas LIMIT 3')
    ejemplos = cursor.fetchall()
    
    print("\n📝 Ejemplos de preguntas insertadas:")
    for i, (id_pregunta, texto, correcta) in enumerate(ejemplos, 1):
        texto_corto = texto[:80] + "..." if len(texto) > 80 else texto
        print(f"{i}. ID {id_pregunta}: {texto_corto} (Respuesta: {correcta})")

def main():
    print("🚀 Iniciando población de la base de datos...")
    
    # Verificar que existe el archivo de preguntas
    archivo_preguntas = 'Questions.md'
    if not os.path.exists(archivo_preguntas):
        print(f"❌ Error: No se encontró el archivo {archivo_preguntas}")
        return
    
    # Leer preguntas del archivo
    print(f"📖 Leyendo preguntas desde {archivo_preguntas}...")
    preguntas = leer_preguntas_desde_archivo(archivo_preguntas)
    
    if not preguntas:
        print("❌ No se encontraron preguntas válidas en el archivo")
        return
    
    print(f"✅ Se encontraron {len(preguntas)} preguntas válidas")
    
    # Crear/conectar a la base de datos
    print("\n🗄️ Creando/conectando a la base de datos...")
    conn = crear_base_datos()
    
    # Insertar preguntas
    print("\n💾 Insertando preguntas en la base de datos...")
    insertadas = insertar_preguntas(conn, preguntas)
    
    print(f"✅ Se insertaron {insertadas} preguntas correctamente")
    
    # Verificar inserción
    verificar_insercion(conn)
    
    # Cerrar conexión
    conn.close()
    
    print("\n🎉 ¡Población de la base de datos completada exitosamente!")
    print("Ahora puedes ejecutar la aplicación con: python app.py")

if __name__ == "__main__":
    main()
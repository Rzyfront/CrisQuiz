import sqlite3

def verify_questions():
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    
    # Verificar el total
    total = conn.execute('SELECT COUNT(*) FROM preguntas').fetchone()[0]
    print(f'Total de preguntas en la base de datos: {total}')
    
    # Mostrar algunas preguntas de muestra
    print('\n=== MUESTRA DE PREGUNTAS ===')
    questions = conn.execute('SELECT * FROM preguntas LIMIT 5').fetchall()
    
    for q in questions:
        print(f'\nID: {q["id"]}')
        print(f'Pregunta: {q["texto"]}')
        print(f'a) {q["opcion_a"]}')
        print(f'b) {q["opcion_b"]}')
        print(f'c) {q["opcion_c"]}')
        print(f'd) {q["opcion_d"]}')
        print(f'Respuesta correcta: {q["correcta"].upper()}')
        print('-' * 80)
    
    # Verificar distribución de respuestas
    print('\n=== DISTRIBUCIÓN DE RESPUESTAS ===')
    dist = conn.execute('''
        SELECT correcta, COUNT(*) as count 
        FROM preguntas 
        GROUP BY correcta 
        ORDER BY correcta
    ''').fetchall()
    
    for answer, count in dist:
        percentage = (count / total) * 100
        print(f'{answer.upper()}: {count} preguntas ({percentage:.1f}%)')
    
    conn.close()

if __name__ == '__main__':
    verify_questions()

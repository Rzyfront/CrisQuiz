import sqlite3
import re
import os

import sqlite3
import re
import os

def parse_questions_from_md(filename):
    """Parse questions from Questions.md file with improved parsing"""
    questions = []
    
    if not os.path.exists(filename):
        print(f"Error: {filename} no encontrado")
        return questions
    
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Dividir el contenido en bloques de preguntas
    # Buscar patrones como "1. " seguido de texto de pregunta
    question_pattern = r'(\d+)\.\s*([^#]*?)(?=\d+\.\s|$)'
    
    # Split content into lines for easier processing
    lines = content.split('\n')
    
    current_question = None
    current_options = {}
    current_answer = None
    in_options_block = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('#') or 'PROCESO DE ENTRENAMIENTO' in line or 'POLICÍA NACIONAL' in line:
            i += 1
            continue
        
        # Check if this is a question line (starts with number.)
        question_match = re.match(r'^(\d+)\.\s*(.*)', line)
        if question_match:
            # Save previous question if we have one complete
            if current_question and len(current_options) == 4 and current_answer:
                questions.append({
                    'texto': current_question.strip(),
                    'opcion_a': current_options.get('a', ''),
                    'opcion_b': current_options.get('b', ''),
                    'opcion_c': current_options.get('c', ''),
                    'opcion_d': current_options.get('d', ''),
                    'correcta': current_answer.lower()
                })
            
            # Start new question
            current_question = question_match.group(2)
            current_options = {}
            current_answer = None
            in_options_block = False
            
            # Continue reading question text if it spans multiple lines
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```') and not re.match(r'^\d+\.', lines[i].strip()):
                if lines[i].strip() and not lines[i].strip().startswith('#'):
                    current_question += ' ' + lines[i].strip()
                i += 1
            continue
        
        # Check for start of options block
        if line == '```' and not in_options_block:
            in_options_block = True
            i += 1
            continue
        
        # Check for end of options block or answer block
        if line == '```' and in_options_block:
            in_options_block = False
            i += 1
            continue
        
        # Parse options inside code blocks
        if in_options_block:
            option_match = re.match(r'^([abcd])[\.\)]\s*(.*)', line)
            if option_match:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                current_options[option_letter] = option_text
            elif line.startswith('Respuesta:'):
                answer_match = re.search(r'Respuesta:\s*([ABCD])', line)
                if answer_match:
                    current_answer = answer_match.group(1)
        
        # Parse answers outside code blocks
        elif line.startswith('Respuesta:'):
            answer_match = re.search(r'Respuesta:\s*([ABCD])', line)
            if answer_match:
                current_answer = answer_match.group(1)
        
        i += 1
    
    # Don't forget the last question
    if current_question and len(current_options) == 4 and current_answer:
        questions.append({
            'texto': current_question.strip(),
            'opcion_a': current_options.get('a', ''),
            'opcion_b': current_options.get('b', ''),
            'opcion_c': current_options.get('c', ''),
            'opcion_d': current_options.get('d', ''),
            'correcta': current_answer.lower()
        })
    
    return questions

def populate_database():
    """Populate the database with questions from Questions.md"""
    
    # Initialize database
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    
    # Create tables if they don't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    # Check if questions already exist
    existing_count = conn.execute('SELECT COUNT(*) FROM preguntas').fetchone()[0]
    if existing_count > 0:
        print(f"Ya existen {existing_count} preguntas en la base de datos.")
        conn.execute('DELETE FROM respuestas')
        conn.execute('DELETE FROM preguntas')
        print("Preguntas existentes eliminadas.")
    
    # Parse questions from file
    print("Analizando preguntas de Questions.md...")
    questions = parse_questions_from_md('Questions.md')
    
    if not questions:
        print("No se encontraron preguntas válidas en Questions.md")
        conn.close()
        return
    
    print(f"✅ Se encontraron {len(questions)} preguntas válidas. Insertando en la base de datos...")
    
    # Insert questions
    inserted_count = 0
    for i, question in enumerate(questions, 1):
        try:
            conn.execute('''
                INSERT INTO preguntas (texto, opcion_a, opcion_b, opcion_c, opcion_d, correcta)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                question['texto'],
                question['opcion_a'],
                question['opcion_b'],
                question['opcion_c'],
                question['opcion_d'],
                question['correcta']
            ))
            inserted_count += 1
            
            # Show progress every 25 questions
            if inserted_count % 25 == 0:
                print(f"Insertadas {inserted_count} preguntas...")
                
        except Exception as e:
            print(f"❌ Error insertando pregunta {i}: {e}")
            print(f"   Pregunta: {question['texto'][:80]}...")
            continue
    
    conn.commit()
    
    # Verify insertion
    final_count = conn.execute('SELECT COUNT(*) FROM preguntas').fetchone()[0]
    print(f"✅ Se insertaron {final_count} preguntas exitosamente.")
    
    # Show some sample questions
    if final_count > 0:
        print(f"\n📋 Ejemplos de preguntas insertadas:")
        samples = conn.execute('SELECT * FROM preguntas LIMIT 3').fetchall()
        for i, sample in enumerate(samples, 1):
            print(f"\n{i}. {sample['texto']}")
            print(f"   a) {sample['opcion_a']}")
            print(f"   b) {sample['opcion_b']}")
            print(f"   c) {sample['opcion_c']}")
            print(f"   d) {sample['opcion_d']}")
            print(f"   Respuesta correcta: {sample['correcta'].upper()}")
    
    conn.close()
    print(f"\n🎉 Base de datos poblada exitosamente con {final_count} preguntas!")
    
    # Show distribution of answers
    conn = sqlite3.connect('quiz.db')
    answer_dist = conn.execute('''
        SELECT correcta, COUNT(*) as count 
        FROM preguntas 
        GROUP BY correcta 
        ORDER BY correcta
    ''').fetchall()
    
    print(f"\n📊 Distribución de respuestas correctas:")
    for answer, count in answer_dist:
        print(f"   {answer.upper()}: {count} preguntas ({count/final_count*100:.1f}%)")
    
    conn.close()

if __name__ == '__main__':
    populate_database()
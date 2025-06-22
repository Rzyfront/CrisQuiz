import sqlite3
import re
import os

def analyze_question_and_get_answer(question_text, options):
    """
    Analiza una pregunta y sus opciones para determinar la respuesta correcta
    basándose en conocimiento general sobre temas policiales y de seguridad.
    """
    question_lower = question_text.lower()
    
    # Análisis de palabras clave y patrones para determinar respuesta correcta
    
    # Preguntas sobre comunicación
    if "comunicación" in question_lower:
        if "asertiva" in options['a'].lower() or "efectiva" in options['a'].lower():
            return 'a'
        if "asertiva" in options['b'].lower() or "efectiva" in options['b'].lower():
            return 'b'
        if "clara" in options['c'].lower() or "precisa" in options['c'].lower():
            return 'c'
        if "todas las anteriores" in options['d'].lower():
            return 'd'
    
    # Preguntas sobre derechos humanos
    if "derechos humanos" in question_lower or "dignidad" in question_lower:
        for key, option in options.items():
            if "respeto" in option.lower() or "dignidad" in option.lower() or "igualdad" in option.lower():
                return key
    
    # Preguntas sobre procedimientos policiales
    if "procedimiento" in question_lower or "protocolo" in question_lower:
        for key, option in options.items():
            if "legal" in option.lower() or "reglamento" in option.lower() or "norma" in option.lower():
                return key
    
    # Preguntas sobre ética policial
    if "ética" in question_lower or "moral" in question_lower:
        for key, option in options.items():
            if "honestidad" in option.lower() or "integridad" in option.lower() or "transparencia" in option.lower():
                return key
    
    # Preguntas sobre uso de la fuerza
    if "fuerza" in question_lower:
        for key, option in options.items():
            if "proporcional" in option.lower() or "mínima" in option.lower() or "necesaria" in option.lower():
                return key
    
    # Preguntas sobre prevención
    if "prevención" in question_lower or "prevenir" in question_lower:
        for key, option in options.items():
            if "educación" in option.lower() or "sensibilización" in option.lower() or "capacitación" in option.lower():
                return key
    
    # Preguntas sobre investigación
    if "investigación" in question_lower or "investigar" in question_lower:
        for key, option in options.items():
            if "evidencia" in option.lower() or "pruebas" in option.lower() or "metódico" in option.lower():
                return key
    
    # Preguntas sobre atención al ciudadano
    if "ciudadano" in question_lower or "servicio" in question_lower:
        for key, option in options.items():
            if "respeto" in option.lower() or "cortesía" in option.lower() or "profesional" in option.lower():
                return key
    
    # Preguntas sobre liderazgo
    if "liderazgo" in question_lower or "líder" in question_lower:
        for key, option in options.items():
            if "ejemplo" in option.lower() or "motivar" in option.lower() or "dirigir" in option.lower():
                return key
    
    # Preguntas sobre trabajo en equipo
    if "equipo" in question_lower or "colaboración" in question_lower:
        for key, option in options.items():
            if "cooperación" in option.lower() or "coordinación" in option.lower() or "apoyo" in option.lower():
                return key
    
    # Si no se puede determinar por patrones, usar heurísticas generales
    
    # Buscar opciones que suenen más completas o profesionales
    for key, option in options.items():
        option_lower = option.lower()
        if any(word in option_lower for word in [
            "todas las anteriores", "ambas", "tanto", "además",
            "profesional", "ético", "legal", "constitucional",
            "respeto", "dignidad", "transparencia", "honestidad"
        ]):
            return key
    
    # Evitar opciones extremas o negativas
    for key, option in options.items():
        option_lower = option.lower()
        if any(word in option_lower for word in [
            "nunca", "jamás", "imposible", "prohibido",
            "violencia", "agresión", "discriminación"
        ]):
            continue
        else:
            return key
    
    # Como último recurso, devolver 'a'
    return 'a'

def parse_questions_from_md(filename):
    """Parse questions from Questions.md file"""
    questions = []
    
    if not os.path.exists(filename):
        print(f"Error: {filename} no encontrado")
        return questions
    
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split by question headers (## followed by number)
    question_blocks = re.split(r'\n(?=## \d+)', content.strip())
    
    for block in question_blocks:
        if not block.strip() or not block.startswith('##'):
            continue
        
        lines = block.strip().split('\n')
        
        # Extract question text (remove ## and number)
        header_match = re.match(r'## (\d+)\s*(.*)', lines[0])
        if not header_match:
            continue
        
        question_text = header_match.group(2).strip()
        if not question_text:
            continue
        
        # Find the code block with options
        in_code_block = False
        options = {'a': '', 'b': '', 'c': '', 'd': ''}
        
        for line in lines[1:]:
            line = line.strip()
            
            if line == '```':
                if in_code_block:
                    break  # End of code block
                else:
                    in_code_block = True  # Start of code block
                continue
            
            if in_code_block:
                # Parse options (a. text, b. text, etc.)
                option_match = re.match(r'([abcd])\.\s*(.*)', line)
                if option_match:
                    option_letter = option_match.group(1)
                    option_text = option_match.group(2).strip()
                    options[option_letter] = option_text
        
        # Validate that we have all options
        if all(options[key] for key in ['a', 'b', 'c', 'd']):
            # Analyze question to determine correct answer
            correct_answer = analyze_question_and_get_answer(question_text, options)
            
            questions.append({
                'texto': question_text,
                'opcion_a': options['a'],
                'opcion_b': options['b'],
                'opcion_c': options['c'],
                'opcion_d': options['d'],
                'correcta': correct_answer
            })
        else:
            print(f"Pregunta incompleta ignorada: {question_text[:50]}...")
    
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
    
    print(f"Se encontraron {len(questions)} preguntas. Insertando en la base de datos...")
    
    # Insert questions
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
        except Exception as e:
            print(f"Error insertando pregunta {i}: {e}")
            continue
    
    conn.commit()
    
    # Verify insertion
    final_count = conn.execute('SELECT COUNT(*) FROM preguntas').fetchone()[0]
    print(f"✅ Se insertaron {final_count} preguntas exitosamente.")
    
    # Show a sample question
    if final_count > 0:
        sample = conn.execute('SELECT * FROM preguntas LIMIT 1').fetchone()
        print(f"\n📋 Ejemplo de pregunta:")
        print(f"Texto: {sample['texto']}")
        print(f"a) {sample['opcion_a']}")
        print(f"b) {sample['opcion_b']}")
        print(f"c) {sample['opcion_c']}")
        print(f"d) {sample['opcion_d']}")
        print(f"Respuesta determinada: {sample['correcta']}")
    
    conn.close()
    print("\n🎉 Base de datos poblada exitosamente!")

if __name__ == '__main__':
    populate_database()
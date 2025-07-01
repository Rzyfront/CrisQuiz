# Configuración para despliegue en PythonAnywhere

## Pasos para desplegar CrisQuiz en PythonAnywhere:

### 1. Clonar el repositorio
```bash
git clone https://github.com/rzyfront/CrisQuiz.git
cd CrisQuiz
```

### 2. Instalar dependencias
```bash
pip3.10 install --user flask
```

### 3. Poblar la base de datos
```bash
python3.10 populate_db.py
```

### 4. Configurar Web App
- Ve a la pestaña **Web** en tu dashboard
- Clic en **"Add a new web app"**
- Selecciona **"Manual configuration"**
- Elige **Python 3.10**

### 5. Configurar paths en la pestaña Web:
- **Source code**: `/home/yourusername/CrisQuiz`
- **Working directory**: `/home/yourusername/CrisQuiz`
- **WSGI configuration file**: `/var/www/yourusername_pythonanywhere_com_wsgi.py`

### 6. Editar el archivo WSGI
Reemplaza TODO el contenido del archivo WSGI con el contenido de `wsgi.py` de este repositorio.

**IMPORTANTE**: Cambia `yourusername` por tu nombre de usuario real de PythonAnywhere.

### 7. Reload la aplicación
Haz clic en el botón verde **"Reload"** en la pestaña Web.

### 8. Acceder a tu aplicación
Tu aplicación estará disponible en: `https://yourusername.pythonanywhere.com`

---

## URLs de la aplicación:
- **Inicio**: `/`
- **Registro**: `/registro`
- **Test**: `/test/<usuario_id>/<pregunta_id>`
- **Resultado**: `/resultado/<usuario_id>`
- **Ranking**: `/ranking`

## Características:
- ✅ 211 preguntas de la Policía Nacional
- ✅ Sistema de registro de usuarios
- ✅ Respuestas inmediatas (correcta/incorrecta)
- ✅ Seguimiento del progreso
- ✅ Resultado final con estadísticas
- ✅ Ranking de mejores puntajes
- ✅ Base de datos SQLite
- ✅ Interfaz Bootstrap responsive

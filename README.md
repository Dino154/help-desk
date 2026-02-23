# 🛡️ Help Desk TI Enterprise

Un sistema integral de gestión de tickets y soporte técnico (Help Desk) desarrollado en Django. Diseñado para optimizar el flujo de trabajo del departamento de TI, mejorar la comunicación con los usuarios y proporcionar métricas precisas sobre el rendimiento del equipo.

## ✨ Características Principales

### 🎫 Gestión Avanzada de Tickets
* **Clasificación Inteligente:** Filtrado por Área, Categoría (Software, Hardware, Redes, etc.) y Prioridad (Baja a Crítica).
* **SLA Automático (Semáforo):** Indicadores visuales de tiempo (Verde < 2h, Amarillo < 2d, Rojo > 2d).
* **Evidencia Multimedia:** Subida de capturas de pantalla con interfaz Drag & Drop y previsualización en tiempo real.
* **Prevención de Spam:** Sistema de bloqueo de doble clic mediante JavaScript para evitar tickets duplicados.

### ⚙️ Flujo de Trabajo y Herramientas Staff
* **Tablero Kanban:** Visualización del estado de los tickets (Pendiente, En Proceso, Resuelto) para una gestión ágil.
* **Audit Trail (Historial):** Registro automático de todas las acciones y cambios de estado por ticket.
* **Sistema de Etiquetas (Tags):** Categorización por colores para casos especiales.
* **Chat Integrado:** Hilo de comentarios entre el usuario y el equipo de soporte.

### 📊 BI & Reportes
* **Dashboard Interactivo:** Gráficos renderizados con Chart.js (Donut, Pie, Barras).
* **Filtros por Fecha:** Análisis de métricas basadas en rangos de tiempo específicos.
* **Exportación de Datos:** Descarga de reportes en formatos oficiales **Excel (.xlsx)** y **PDF**.

### 🌟 Experiencia de Usuario (UX)
* **Escudo Anti-Quejas (Proyectos):** Visualización del progreso de los proyectos internos de TI para mantener informados a los usuarios.
* **Wiki / Base de Conocimientos (FAQ):** Módulo para publicar artículos y guías de autoayuda.
* **Perfiles Personalizados:** Soporte para avatares (imágenes de perfil) y asignación de áreas.
* **UI Moderna:** Interfaz responsiva utilizando Tailwind CSS y diseño *Glassmorphism*.

---

## 🛠️ Stack Tecnológico

* **Backend:** Python 3.x, Django
* **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla)
* **Base de Datos:** SQLite (Configurable a PostgreSQL/MySQL)
* **Librerías Destacadas:**
  * `Chart.js` (Visualización de datos)
  * `openpyxl` (Generación de Excel)
  * `xhtml2pdf` (Generación de PDF)
  * `Pillow` (Procesamiento de imágenes)

---

## 🚀 Instalación y Despliegue Local

Sigue estos pasos para levantar el proyecto en tu entorno de desarrollo local.

### 1. Clonar el repositorio
```bash
git clone [https://github.com/TU_USUARIO/helpdesk-ti.git](https://github.com/TU_USUARIO/helpdesk-ti.git)
cd helpdesk-ti
2. Crear y activar un entorno virtual
Bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
3. Instalar dependencias
Asegúrate de tener instaladas las librerías necesarias:

Bash
pip install django openpyxl xhtml2pdf pillow
4. Configurar la Base de Datos
Realiza las migraciones para crear las tablas en SQLite:

Bash
python manage.py makemigrations
python manage.py migrate
5. Crear el Superusuario (Administrador)
Bash
python manage.py createsuperuser
(Sigue las instrucciones en la terminal para definir email y contraseña).

6. Levantar el servidor
Bash
python manage.py runserver
Accede al sistema desde tu navegador en: http://127.0.0.1:8000/

📧 Configuración de Correos (SMTP)
Para que el sistema envíe notificaciones reales al crear o resolver tickets, debes configurar las siguientes variables en el archivo settings.py:

Python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-correo@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-aplicación'
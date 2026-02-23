from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 
from datetime import timedelta

class Area(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

# --- 1. NUEVO MODELO: ETIQUETAS (TAGS) ---
class Etiqueta(models.Model):
    nombre = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#3b82f6") # Código Hex (ej: #FF0000)
    
    def __str__(self):
        return self.nombre

class Ticket(models.Model):
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica - ¡Fuego!'),
    ]
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('RESUELTO', 'Resuelto'),
        ('CANCELADO', 'Cancelado'),
    ]

    # --- NUEVO: OPCIONES DE CATEGORÍA ---
    CATEGORIA_CHOICES = [
        ('SOFTWARE', '💻 Software / Aplicaciones'),
        ('HARDWARE', '🔌 Hardware / Equipos'),
        ('REDES', '🌐 Redes e Internet'),
        ('ACCESOS', '🔐 Accesos y Contraseñas'),
        ('OTROS', '📁 Otros'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Asunto del Problema")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    archivo = models.ImageField(upload_to='tickets/', blank=True, null=True, verbose_name="Captura de Pantalla")
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='tickets')
    
    # --- NUEVO: CAMPO CATEGORÍA EN LA BASE DE DATOS ---
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='SOFTWARE', verbose_name="Categoría")
    
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mis_tickets')
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # --- 2. RELACIÓN CON ETIQUETAS ---
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)

    def __str__(self):
        return f"#{self.id} - {self.titulo}"

    class Meta:
        ordering = ['-fecha_creacion']
        
    # --- LÓGICA DEL SEMÁFORO (SLA) ---
    def semaforo(self):
        if self.estado in ['RESUELTO', 'CANCELADO']:
            return 'gris' # Ya no importa
            
        ahora = timezone.now()
        tiempo_pasado = ahora - self.fecha_creacion
        
        # Menos de 2 horas -> VERDE
        if tiempo_pasado < timedelta(hours=2):
            return 'verde'
        # Más de 2 días -> ROJO
        elif tiempo_pasado > timedelta(days=2):
            return 'rojo'
        # Entre 2 horas y 2 días -> AMARILLO
        else:
            return 'amarillo'

# --- 3. NUEVO MODELO: HISTORIAL (TIMELINE) ---
class HistorialTicket(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='historial', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=255) # Ej: "Cambió estado a Resuelto"
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']

class Comentario(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='comentarios', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField(verbose_name="Comentario")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Área de Trabajo")
    avatar = models.ImageField(upload_to='perfiles/', blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

class Articulo(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField() 
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titulo

class Proyecto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Proyecto")
    progreso = models.IntegerField(default=0, verbose_name="% Progreso") # De 0 a 100
    estado_texto = models.CharField(max_length=200, verbose_name="Estado Actual (Ej: Falta módulo X)")
    tiempo_estimado = models.CharField(max_length=100, blank=True, verbose_name="Tiempo Restante (Ej: 2 semanas)")
    visible = models.BooleanField(default=True, verbose_name="Visible para usuarios")

    def __str__(self):
        return self.nombre
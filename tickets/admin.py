from django.contrib import admin
from .models import Area, Ticket, Articulo, PerfilUsuario, Comentario

# --- ÁREAS ---
@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

# --- TICKETS ---
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    # Qué columnas ver en la lista
    list_display = ('id', 'titulo', 'area', 'prioridad', 'estado', 'creado_por', 'fecha_creacion')
    
    # Filtros laterales para buscar rápido
    list_filter = ('estado', 'prioridad', 'area')
    
    # Buscador por título o descripción
    search_fields = ('titulo', 'descripcion')
    
    # Para que el ID del ticket sea un link
    list_display_links = ('id', 'titulo')

# --- BASE DE CONOCIMIENTOS (WIKI) ---
@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha_publicacion')
    search_fields = ('titulo', 'contenido') # ¡Buscador de tutoriales!

# --- OTROS ---
admin.site.register(PerfilUsuario)
admin.site.register(Comentario)
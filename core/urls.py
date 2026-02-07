from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Importamos TODAS las vistas (Incluyendo la nueva de Proyectos)
from tickets.views import (
    lista_tickets, 
    crear_ticket, 
    detalle_ticket, 
    gestion_usuarios, 
    crear_usuario, 
    editar_usuario, 
    eliminar_usuario,
    reportes,
    exportar_excel,
    registro,
    base_conocimientos,
    exportar_pdf,
    tablero_kanban,
    gestion_proyectos # <--- ¡NO OLVIDES ESTA IMPORTACIÓN!
)

urlpatterns = [
    # Panel de Admin
    path('admin/', admin.site.urls),
    
    # Login / Logout / Registro
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('registro/', registro, name='registro'),
    
    # Tickets
    path('', lista_tickets, name='lista_tickets'),
    path('nuevo/', crear_ticket, name='crear_ticket'),
    path('ticket/<int:pk>/', detalle_ticket, name='detalle_ticket'),
    
    # Reportes y Exportación
    path('reportes/', reportes, name='reportes'),
    path('exportar/', exportar_excel, name='exportar_excel'),
    path('exportar-pdf/', exportar_pdf, name='exportar_pdf'),
    
    # Base de Conocimientos (Wiki)
    path('conocimientos/', base_conocimientos, name='base_conocimientos'),
    
    # Usuarios (Gestión Admin)
    path('usuarios/', gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/nuevo/', crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:pk>/', editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', eliminar_usuario, name='eliminar_usuario'),

    # Herramientas Staff
    path('tablero/', tablero_kanban, name='tablero_kanban'),
    
    # --- NUEVA RUTA: GESTIÓN DE PROYECTOS ---
    path('proyectos/', gestion_proyectos, name='gestion_proyectos'),
]

# Configuración para ver imágenes en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
import openpyxl
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login 
from .models import Ticket, Area, Comentario, PerfilUsuario, Articulo, HistorialTicket, Etiqueta, Proyecto
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q 
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.template.loader import get_template 
from xhtml2pdf import pisa 
from .forms import RegistroUsuarioForm, EditarUsuarioForm 
from django.utils import timezone
import datetime

# --- VISTAS DE TICKETS ---

@login_required
def lista_tickets(request):
    try:
        proyectos = Proyecto.objects.filter(visible=True)
    except:
        proyectos = [] 

    if request.user.is_staff:
        tickets = Ticket.objects.all().order_by('-fecha_creacion')
        query = request.GET.get('q')
        if query:
            tickets = tickets.filter(
                Q(id__icontains=query) | 
                Q(titulo__icontains=query) | 
                Q(creado_por__username__icontains=query)
            )
        context = {
            'tickets': tickets,
            'total_tickets': tickets.count(),
            'criticos': tickets.filter(prioridad='CRITICA').count(),
            'resueltos': tickets.filter(estado='RESUELTO').count(),
            'pendientes': tickets.filter(estado='PENDIENTE').count(),
            'proyectos': proyectos 
        }
        return render(request, 'tickets/lista_tickets.html', context)
    else:
        mis_tickets = Ticket.objects.filter(creado_por=request.user).order_by('-fecha_creacion')
        context = {
            'tickets': mis_tickets,
            'mis_pendientes': mis_tickets.exclude(estado='RESUELTO').exclude(estado='CANCELADO').count(),
            'mis_resueltos': mis_tickets.filter(estado='RESUELTO').count(),
            'proyectos': proyectos 
        }
        return render(request, 'tickets/portal_usuario.html', context)
    
@login_required
def crear_ticket(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        area_id = request.POST.get('area')
        prioridad = request.POST.get('prioridad')
        categoria = request.POST.get('categoria') # <--- ¡NUEVO! ATRAPAMOS LA CATEGORÍA
        archivo = request.FILES.get('archivo')
        
        if area_id:
            area_obj = Area.objects.get(id=area_id)
            nuevo_ticket = Ticket.objects.create(
                titulo=titulo,
                descripcion=descripcion,
                area=area_obj,
                categoria=categoria, # <--- ¡NUEVO! LO GUARDAMOS EN LA BD
                prioridad=prioridad,
                archivo=archivo,
                creado_por=request.user 
            )
            
            # Historial
            HistorialTicket.objects.create(
                ticket=nuevo_ticket, 
                usuario=request.user, 
                accion=f"Creó el ticket en la categoría {categoria}"
            )
            
            # Notificación (Ahora incluye la categoría)
            asunto = f'🔥 Nuevo Ticket #{nuevo_ticket.id}: {titulo}'
            mensaje = f"""
            El usuario {request.user.username} ha reportado una incidencia.
            
            Categoría: {categoria}
            Prioridad: {prioridad}
            Área: {area_obj.nombre}
            
            Descripción:
            {descripcion}
            """
            try:
                send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=True)
            except:
                pass

            return redirect('lista_tickets')
    
    areas = Area.objects.all()
    area_usuario_id = None
    try:
        if hasattr(request.user, 'perfil') and request.user.perfil.area:
            area_usuario_id = request.user.perfil.area.id
    except:
        pass 

    return render(request, 'tickets/crear_ticket.html', {
        'areas': areas,
        'area_usuario_id': area_usuario_id 
    })

@login_required
def detalle_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if not request.user.is_staff and ticket.creado_por != request.user:
        return redirect('lista_tickets')
    
    if request.method == 'POST':
        # 1. ASIGNAR TICKET A MÍ
        if 'asignar_a_mi' in request.POST and request.user.is_staff:
            ticket.asignado_a = request.user
            ticket.estado = 'EN_PROCESO'
            ticket.save()
            HistorialTicket.objects.create(ticket=ticket, usuario=request.user, accion="Se asignó el ticket")

        # 2. CAMBIAR ESTADO
        elif 'cambiar_estado' in request.POST and request.user.is_staff:
            nuevo_estado = request.POST.get('estado')
            if nuevo_estado and nuevo_estado != ticket.estado:
                ticket.estado = nuevo_estado
                if not ticket.asignado_a:
                    ticket.asignado_a = request.user
                ticket.save()
                
                HistorialTicket.objects.create(ticket=ticket, usuario=request.user, accion=f"Cambió estado a {nuevo_estado}")

                if nuevo_estado == 'RESUELTO' and ticket.creado_por.email:
                    asunto = f'✅ Ticket #{ticket.id} Resuelto'
                    mensaje = f"Hola {ticket.creado_por.username},\n\nTu incidencia '{ticket.titulo}' ha sido marcada como RESUELTA.\nGracias."
                    try:
                        send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [ticket.creado_por.email], fail_silently=True)
                    except:
                        pass
        
        # 3. AGREGAR ETIQUETA
        elif 'add_etiqueta' in request.POST and request.user.is_staff:
            nombre_tag = request.POST.get('nombre_etiqueta')
            color_tag = request.POST.get('color_etiqueta', '#3b82f6')
            if nombre_tag:
                etiqueta, created = Etiqueta.objects.get_or_create(nombre=nombre_tag, defaults={'color': color_tag})
                ticket.etiquetas.add(etiqueta)
                HistorialTicket.objects.create(ticket=ticket, usuario=request.user, accion=f"Agregó etiqueta: {nombre_tag}")

        # 4. NUEVO COMENTARIO
        elif 'nuevo_comentario' in request.POST:
            texto = request.POST.get('texto')
            if texto:
                Comentario.objects.create(
                    ticket=ticket,
                    usuario=request.user,
                    texto=texto
                )
        return redirect('detalle_ticket', pk=pk)
            
    return render(request, 'tickets/detalle_ticket.html', {'ticket': ticket})

# --- VISTA: TABLERO KANBAN ---
@staff_member_required
def tablero_kanban(request):
    pendientes = Ticket.objects.filter(estado='PENDIENTE').order_by('-prioridad')
    proceso = Ticket.objects.filter(estado='EN_PROCESO').order_by('-prioridad')
    resueltos = Ticket.objects.filter(estado='RESUELTO').order_by('-fecha_actualizacion')[:10]
    
    return render(request, 'tickets/kanban.html', {
        'pendientes': pendientes,
        'proceso': proceso,
        'resueltos': resueltos
    })

# --- GESTIÓN DE USUARIOS ---

@staff_member_required
def gestion_usuarios(request):
    query = request.GET.get('q')
    if query:
        usuarios = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query)).order_by('-date_joined')
    else:
        usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'tickets/gestion_usuarios.html', {'usuarios': usuarios})

@staff_member_required
def crear_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion_usuarios')
    else:
        form = UserCreationForm()
    
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-800 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500 transition placeholder-slate-400'})
    
    return render(request, 'tickets/crear_usuario.html', {'form': form})

@staff_member_required 
def editar_usuario(request, pk):
    usuario_editar = get_object_or_404(User, pk=pk)
    
    form_info = EditarUsuarioForm(instance=usuario_editar)
    form_pass = SetPasswordForm(user=usuario_editar) 

    if request.method == 'POST':
        if 'btn_info' in request.POST:
            form_info = EditarUsuarioForm(request.POST, instance=usuario_editar)
            if form_info.is_valid():
                form_info.save()
                
                perfil, created = PerfilUsuario.objects.get_or_create(user=usuario_editar)
                area_id = request.POST.get('area')
                if area_id: perfil.area_id = area_id
                else: perfil.area = None
                
                if 'avatar' in request.FILES:
                    perfil.avatar = request.FILES['avatar']
                
                perfil.save()
                messages.success(request, f"Datos de {usuario_editar.username} actualizados.")
                return redirect('gestion_usuarios')

        elif 'btn_pass' in request.POST:
            form_pass = SetPasswordForm(usuario_editar, request.POST)
            if form_pass.is_valid():
                form_pass.save()
                messages.success(request, f"¡Contraseña de {usuario_editar.username} cambiada con éxito!")
                return redirect('gestion_usuarios')
            else:
                messages.error(request, "Error al cambiar la contraseña.")

    area_actual_id = None
    avatar_url = None
    if hasattr(usuario_editar, 'perfil'):
        if usuario_editar.perfil.area:
            area_actual_id = usuario_editar.perfil.area.id
        if usuario_editar.perfil.avatar:
            avatar_url = usuario_editar.perfil.avatar.url
        
    areas = Area.objects.all()

    return render(request, 'tickets/editar_usuario.html', {
        'form_info': form_info,
        'form_pass': form_pass,
        'usuario_editar': usuario_editar,
        'areas': areas,
        'area_actual_id': area_actual_id,
        'avatar_url': avatar_url 
    })

@staff_member_required
def eliminar_usuario(request, pk):
    usuario_a_borrar = get_object_or_404(User, pk=pk)
    if usuario_a_borrar == request.user:
        return redirect('gestion_usuarios')
    if request.method == 'POST':
        usuario_a_borrar.delete()
        return redirect('gestion_usuarios')
    return render(request, 'tickets/eliminar_usuario.html', {'usuario': usuario_a_borrar})

# --- REPORTES Y EXPORTACIÓN ---

@staff_member_required
def reportes(request):
    # 1. Ticket Base
    tickets = Ticket.objects.all()
    
    # 2. Filtrar por Rango de Fechas
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        # Filtramos por fecha de creación (rango inclusivo)
        tickets = tickets.filter(fecha_creacion__date__range=[fecha_inicio, fecha_fin])

    # 3. Calcular métricas SOBRE LOS TICKETS FILTRADOS
    pendientes = tickets.filter(estado='PENDIENTE').count()
    proceso = tickets.filter(estado='EN_PROCESO').count()
    resueltos = tickets.filter(estado='RESUELTO').count()
    cancelados = tickets.filter(estado='CANCELADO').count()
    
    baja = tickets.filter(prioridad='BAJA').count()
    normal = tickets.filter(prioridad='MEDIA').count()
    alta = tickets.filter(prioridad='ALTA').count()
    critica = tickets.filter(prioridad='CRITICA').count()
    
    # Áreas (Solo contamos tickets que están dentro del rango de fecha)
    areas = Area.objects.annotate(
        num_tickets=Count('tickets', filter=Q(tickets__in=tickets))
    ).order_by('-num_tickets')
    
    labels_areas = [a.nombre for a in areas if a.num_tickets > 0]
    data_areas = [a.num_tickets for a in areas if a.num_tickets > 0]

    context = {
        'pendientes': pendientes, 
        'proceso': proceso, 
        'resueltos': resueltos, 
        'cancelados': cancelados, 
        'baja': baja, 
        'normal': normal, 
        'alta': alta, 
        'critica': critica, 
        'labels_areas': labels_areas, 
        'data_areas': data_areas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    return render(request, 'tickets/reportes.html', context)

@staff_member_required
def exportar_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tickets HelpDesk"
    headers = ["ID", "Asunto", "Usuario", "Área", "Categoría", "Prioridad", "Estado", "Fecha"]
    ws.append(headers)
    tickets = Ticket.objects.all().order_by('-fecha_creacion')
    for t in tickets:
        fecha_simple = t.fecha_creacion.replace(tzinfo=None)
        ws.append([t.id, t.titulo, t.creado_por.username, t.area.nombre, t.get_categoria_display(), t.get_prioridad_display(), t.get_estado_display(), fecha_simple])
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['H'].width = 20
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Tickets.xlsx"'
    wb.save(response)
    return response

@staff_member_required
def exportar_pdf(request):
    pendientes = Ticket.objects.filter(estado='PENDIENTE').count()
    proceso = Ticket.objects.filter(estado='EN_PROCESO').count()
    resueltos = Ticket.objects.filter(estado='RESUELTO').count()
    criticos = Ticket.objects.filter(prioridad='CRITICA').count()
    
    tickets = Ticket.objects.all().order_by('-fecha_creacion')

    context = {
        'pendientes': pendientes,
        'proceso': proceso,
        'resueltos': resueltos,
        'criticos': criticos,
        'tickets': tickets,
        'usuario': request.user
    }

    template_path = 'tickets/reporte_pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_helpdesk.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Tuvimos errores <pre>' + html + '</pre>')
    
    return response

# --- VISTA DE REGISTRO PÚBLICO ---
def registro(request):
    if request.user.is_authenticated:
        return redirect('lista_tickets')

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save() 
            login(request, user) 
            return redirect('lista_tickets')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/registro.html', {'form': form})

# --- WIKI ---
@login_required
def base_conocimientos(request):
    query = request.GET.get('q')
    if query:
        articulos = Articulo.objects.filter(
            Q(titulo__icontains=query) | 
            Q(contenido__icontains=query)
        )
    else:
        articulos = Articulo.objects.all().order_by('-fecha_publicacion')
        
    return render(request, 'tickets/base_conocimientos.html', {'articulos': articulos})

# --- GESTIÓN DE PROYECTOS (EL ESCUDO) ---
@staff_member_required
def gestion_proyectos(request):
    if request.method == 'POST':
        # Eliminar
        if 'delete_id' in request.POST:
            p = get_object_or_404(Proyecto, pk=request.POST.get('delete_id'))
            p.delete()
            messages.success(request, "Proyecto eliminado.")
        
        # Crear o Editar
        else:
            nombre = request.POST.get('nombre')
            progreso = request.POST.get('progreso')
            estado = request.POST.get('estado')
            tiempo = request.POST.get('tiempo')
            
            Proyecto.objects.create(
                nombre=nombre,
                progreso=progreso,
                estado_texto=estado,
                tiempo_estimado=tiempo
            )
            messages.success(request, "Proyecto actualizado.")
        return redirect('gestion_proyectos')

    proyectos = Proyecto.objects.all()
    return render(request, 'tickets/gestion_proyectos.html', {'proyectos': proyectos})
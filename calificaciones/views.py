from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Prefetch, Q, Count
from django.http import JsonResponse
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
import csv
import io
from datetime import datetime
from django.http import HttpResponse



# Modelos
from .models import Calificacion, Calificaciontributaria, Factortributario
from instrumentos.models import Instrumento, Mercado
from usuarios.models import Usuario, Estado
from auditoria.models import Log
from archivos.models import Archivo

# Forms (Con las nuevas listas de factores F19)
from .forms import (
    CalificacionFilterForm, CalificacionForm,
    FACTORES_BASE_UI, FACTORES_CALCULADOS_UI, FACTORES_DIRECTOS_UI
)

# Decorators
from usuarios.decorators import login_requerido_personalizado, rol_requerido


# ==========================================================
#  VISTA 1: Lista/Grilla (Modificada para F19)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Corredor', 'Administrador', 'Auditor'])
def calificacion_list_view(request):
    
    form = CalificacionFilterForm(request.GET or None)
    id_usuario_actual = request.session.get('id_usuario')
    rol_usuario_actual = request.session.get('rol_nombre')
    
    qs_base = Calificacion.objects.select_related(
        'id_instrumento', 'id_mercado', 'id_usuario', 'id_estado'
    )
    
    if rol_usuario_actual in ['Administrador', 'Auditor']:
        qs = qs_base.all()
    else:
        qs = qs_base.filter(
            Q(id_usuario_id=id_usuario_actual) | 
            Q(id_usuario__isnull=True)
        )
        
    if form.is_valid():
        if form.cleaned_data.get('mercado'):
            qs = qs.filter(id_mercado=form.cleaned_data['mercado'])
        if form.cleaned_data.get('anio'):
            qs = qs.filter(calificaciontributaria__anio=form.cleaned_data['anio'])
        if form.cleaned_data.get('origen'):
            origen = form.cleaned_data['origen']
            if origen == 'manual':
                qs = qs.filter(id_usuario_id=id_usuario_actual, id_archivo__isnull=True)
            elif origen == 'archivo':
                qs = qs.filter(id_archivo__isnull=False)

    qs = qs.prefetch_related(
        'calificaciontributaria_set__factortributario_set'
    )

    calificaciones_aplanadas = []
    
    # --- CAMBIO: Lista de códigos de BBDD ahora usa F19 ---
    codigos_factores_deseados = [
        'F08', 'F09', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 
        'F18', 'F19', 'F20', 'F21', 'F22', 'F23', 'F24', 'F25', 'F26', 'F27', 
        'F28', 'F29', 'F30', 'F31', 'F32', 'F33', 'F34', 'F35', 'F36', 'F37'
    ]

    for calif in qs:
        datos_calif = {
            'calificacion': calif,
            'tributaria': None,
            'factores': {}
        }
        calif_tributaria_lista = calif.calificaciontributaria_set.all()
        
        if calif_tributaria_lista:
            tributaria = calif_tributaria_lista[0]
            datos_calif['tributaria'] = tributaria
            factores_lista = tributaria.factortributario_set.all()
            
            if factores_lista:
                factores_dict = {f.codigo_factor: f.valor_factor for f in factores_lista}
                for codigo in codigos_factores_deseados:
                    datos_calif['factores'][codigo] = factores_dict.get(codigo, None)
        
        calificaciones_aplanadas.append(datos_calif)

    context = {
        'form_filtros': form,
        'calificaciones': calificaciones_aplanadas,
        'factores_header': codigos_factores_deseados
    }
    
    return render(request, 'calificaciones/mantenedor_lista.html', context)


# ==========================================================
#  VISTA 2: Crear Calificación (Modificada para F19)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Corredor', 'Administrador'])
@transaction.atomic
def calificacion_create_view(request):
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        
        if form.is_valid():
            try:
                data = form.cleaned_data
                usuario_app = Usuario.objects.get(id_usuario=request.session['id_usuario'])
                estado_activo = get_object_or_404(Estado, id_estado=5) 
                instrumento, created = Instrumento.objects.get_or_create(
                    nombre=data['instrumento_nombre'],
                    defaults={'tipo': 'Desconocido', 'moneda': 'N/A'}
                )

                nueva_calificacion = Calificacion.objects.create(
                    fecha_pago=data['fecha_pago'],
                    id_usuario=usuario_app,
                    id_instrumento=instrumento,
                    id_mercado=data['mercado'],
                    id_archivo=None,
                    id_estado=estado_activo,
                    fecha_registro=timezone.now(),
                    activo=True 
                )

                nueva_calif_trib = Calificaciontributaria.objects.create(
                    id_calificacion=nueva_calificacion,
                    secuencia_evento=data['secuencia_evento'],
                    evento_capital=data['evento_capital'],
                    anio=data['anio'],
                    valor_historico=data['valor_historico'],
                    descripcion=data['descripcion'],
                    ingreso_por_montos=data['ingreso_por_montos']
                )

                valores_finales = {}
                
                if data['ingreso_por_montos']:
                    suma_total_montos = Decimal('0.0')
                    for campo in FACTORES_BASE_UI: # (Usa F19)
                        suma_total_montos += data.get(campo) or Decimal('0.0')
                    precision = Decimal('0.00000001')
                    if suma_total_montos > 0:
                        for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                            monto_campo = data.get(campo) or Decimal('0.0')
                            factor_calculado = (monto_campo / suma_total_montos).quantize(precision, rounding=ROUND_HALF_UP)
                            valores_finales[campo] = factor_calculado
                    else:
                        for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                            valores_finales[campo] = Decimal('0.0')
                    for campo in FACTORES_DIRECTOS_UI:
                        valores_finales[campo] = data.get(campo) or Decimal('0.0')
                else:
                    todos_los_factores = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI + FACTORES_DIRECTOS_UI
                    for campo in todos_los_factores:
                        valores_finales[campo] = data.get(campo) or Decimal('0.0')
                
                factores_para_crear = []
                for nombre_campo, valor_factor in valores_finales.items():
                    if valor_factor is not None and valor_factor != Decimal('0.0'):
                        # --- CAMBIO: Mapeo de BBDD (ej. 'factor_19' -> 'F19') ---
                        codigo_factor_bruto = nombre_campo.split('_')[-1] # '08', '09', '19'
                        codigo_factor = f"F{codigo_factor_bruto.zfill(2)}" # 'F08', 'F09', 'F19'
                        
                        factores_para_crear.append(
                            Factortributario(
                                id_calificacion_tributaria=nueva_calif_trib,
                                codigo_factor=codigo_factor,
                                descripcion_factor=form.fields[nombre_campo].label,
                                valor_factor=valor_factor
                            )
                        )
                Factortributario.objects.bulk_create(factores_para_crear)

                """  Log.objects.create(
                    fecha=timezone.now(),
                    accion='INSERT',
                    detalle=f'Creación de Calificacion ID {nueva_calificacion.id_calificacion} por {usuario_app.nombre}',
                    id_usuario=usuario_app,
                    id_calificacion=nueva_calificacion
                ) """
                messages.success(request, f'Calificación (ID {nueva_calificacion.id_calificacion}) ingresada exitosamente.')
                return redirect('calificaciones:lista_calificaciones')
            except Exception as e:
                messages.error(request, f'Error al guardar la calificación: {e}')
                
    else:
        form = CalificacionForm()
    context = {
        'form': form,
        'titulo_pagina': 'Ingresar Calificación Tributaria'
    }
    return render(request, 'calificaciones/mantenedor_form.html', context)


# ==========================================================
#  VISTA 3: Calculadora (Modificada para F19)
# ==========================================================
@transaction.atomic 
def calcular_factores_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        valores_finales = {}
        
        # --- CAMBIO: Usa FACTORES_BASE_UI (con F19) ---
        suma_total_montos = Decimal('0.0')
        for campo in FACTORES_BASE_UI: 
            monto_str = data.get(campo) or '0.0'
            suma_total_montos += Decimal(monto_str)

        precision = Decimal('0.00000001')
        if suma_total_montos > 0:
            for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                monto_str = data.get(campo) or '0.0'
                factor_calculado = (Decimal(monto_str) / suma_total_montos).quantize(precision, rounding=ROUND_HALF_UP)
                valores_finales[campo] = str(factor_calculado)
        else:
            for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                valores_finales[campo] = '0.00000000'
        
        for campo in FACTORES_DIRECTOS_UI:
            valores_finales[campo] = data.get(campo) or '0.00'

        return JsonResponse({'factores': valores_finales})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==========================================================
#  VISTA 4: Eliminar (Sin cambios)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Corredor', 'Administrador'])
@transaction.atomic
def calificacion_delete_view(request, pk):
    calif = get_object_or_404(Calificacion.objects_all, id_calificacion=pk)
    id_usuario_actual = request.session.get('id_usuario')
    rol_usuario_actual = request.session.get('rol_nombre')
    es_propietario = (calif.id_usuario_id == id_usuario_actual)
    
    if rol_usuario_actual == 'Corredor' and not es_propietario:
        messages.error(request, 'No tienes permisos para eliminar esta calificación (no es tuya).')
        return redirect('calificaciones:lista_calificaciones')

    if request.method == 'POST':
        calif.activo = False
        calif.save()
        try:
            usuario_app = Usuario.objects.get(id_usuario=id_usuario_actual)
            Log.objects.create(
                fecha=timezone.now(),
                accion='DELETE',
                detalle=f'Borrado lógico de Calificacion ID {calif.id_calificacion} por {usuario_app.nombre}',
                id_usuario=usuario_app,
                id_calificacion=calif
            )
        except Usuario.DoesNotExist:
            pass 
        
        messages.success(request, f'Calificación ID {calif.id_calificacion} ha sido eliminada (dada de baja).')
        return redirect('calificaciones:lista_calificaciones')

    context = {
        'calificacion': calif
    }
    return render(request, 'calificaciones/mantenedor_confirm_delete.html', context)


# ==========================================================
#  VISTA 5: Modificar (Modificada para F19)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Corredor', 'Administrador'])
@transaction.atomic
def calificacion_update_view(request, pk):
    
    calif = get_object_or_404(Calificacion.objects.select_related('id_instrumento', 'id_mercado'), id_calificacion=pk)
    try:
        calif_trib = Calificaciontributaria.objects.get(id_calificacion=calif)
    except Calificaciontributaria.DoesNotExist:
        messages.error(request, 'Error: No se encontraron datos tributarios para esta calificación.')
        return redirect('calificaciones:lista_calificaciones')

    id_usuario_actual = request.session.get('id_usuario')
    rol_usuario_actual = request.session.get('rol_nombre')
    es_propietario = (calif.id_usuario_id == id_usuario_actual)
    
    if rol_usuario_actual == 'Corredor' and not es_propietario:
        messages.error(request, 'No tienes permisos para modificar esta calificación.')
        return redirect('calificaciones:lista_calificaciones')

    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                usuario_app = Usuario.objects.get(id_usuario=id_usuario_actual)
                instrumento, created = Instrumento.objects.get_or_create(
                    nombre=data['instrumento_nombre'],
                    defaults={'tipo': 'Desconocido', 'moneda': 'N/A'}
                )

                # Actualizar Padre e Hijo
                calif.fecha_pago = data['fecha_pago']
                calif.id_instrumento = instrumento
                calif.id_mercado = data['mercado']
                
                # Si la calificación venía de un archivo (Bolsa) y un 
                # usuario (Corredor o Admin) la modifica, ese usuario
                # toma "propiedad" de ella y se convierte en "Manual".
                if calif.id_archivo is not None:
                    # Solo un CORREDOR toma posesión.
                    if rol_usuario_actual == 'Corredor':
                        calif.id_archivo = None
                        calif.id_usuario = usuario_app
                    # Si un Admin edita, el registro sigue siendo 'Archivo'
                    # (no hacemos nada y se mantiene 'id_usuario=NULL')
                
                calif.save()
                calif_trib.secuencia_evento = data['secuencia_evento']
                calif_trib.evento_capital = data['evento_capital']
                calif_trib.anio = data['anio']
                calif_trib.valor_historico = data['valor_historico']
                calif_trib.descripcion = data['descripcion']
                calif_trib.ingreso_por_montos = data['ingreso_por_montos']
                calif_trib.save()

                # Lógica de Cálculo (ya usa FACTORES_BASE_UI con F19)
                valores_finales = {}
                if data['ingreso_por_montos']:
                    suma_total_montos = Decimal('0.0')
                    for campo in FACTORES_BASE_UI:
                        suma_total_montos += data.get(campo) or Decimal('0.0')
                    precision = Decimal('0.00000001')
                    if suma_total_montos > 0:
                        for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                            monto_campo = data.get(campo) or Decimal('0.0')
                            factor_calculado = (monto_campo / suma_total_montos).quantize(precision, rounding=ROUND_HALF_UP)
                            valores_finales[campo] = factor_calculado
                    else:
                        for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                            valores_finales[campo] = Decimal('0.0')
                    for campo in FACTORES_DIRECTOS_UI:
                        valores_finales[campo] = data.get(campo) or Decimal('0.0')
                else:
                    todos_los_factores = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI + FACTORES_DIRECTOS_UI
                    for campo in todos_los_factores:
                        valores_finales[campo] = data.get(campo) or Decimal('0.0')
                
                # Actualizar Nietos
                Factortributario.objects.filter(id_calificacion_tributaria=calif_trib).delete()
                factores_para_crear = []
                for nombre_campo, valor_factor in valores_finales.items():
                    if valor_factor is not None and valor_factor != Decimal('0.0'):
                        codigo_factor_bruto = nombre_campo.split('_')[-1] # '08', '09', '19'
                        codigo_factor = f"F{codigo_factor_bruto.zfill(2)}" # 'F08', 'F09', 'F19'
                        
                        factores_para_crear.append(
                            Factortributario(
                                id_calificacion_tributaria=calif_trib,
                                codigo_factor=codigo_factor,
                                descripcion_factor=form.fields[nombre_campo].label,
                                valor_factor=valor_factor
                            )
                        )
                Factortributario.objects.bulk_create(factores_para_crear)

                """ # Log de Auditoría
                Log.objects.create(
                    fecha=timezone.now(),
                    accion='UPDATE',
                    detalle=f'Modificación de Calificacion ID {calif.id_calificacion} por {usuario_app.nombre}',
                    id_usuario=usuario_app,
                    id_calificacion=calif
                ) """
                messages.success(request, f'Calificación (ID {calif.id_calificacion}) modificada exitosamente.')
                return redirect('calificaciones:lista_calificaciones')
            except Exception as e:
                messages.error(request, f'Error al guardar la modificación: {e}')
        
        context = {
            'form': form,
            'titulo_pagina': f'Modificar Calificación (ID: {calif.id_calificacion})',
            'calificacion': calif 
        }
    else:
        # --- Lógica GET (Rellenar el formulario) ---
        factores_actuales = Factortributario.objects.filter(id_calificacion_tributaria=calif_trib)
        factores_dict = {f.codigo_factor: f.valor_factor for f in factores_actuales}
        initial_data = {
            'mercado': calif.id_mercado,
            'instrumento_nombre': calif.id_instrumento.nombre,
            'fecha_pago': calif.fecha_pago,
            'secuencia_evento': calif_trib.secuencia_evento,
            'evento_capital': calif_trib.evento_capital,
            'anio': calif_trib.anio,
            'valor_historico': calif_trib.valor_historico,
            'descripcion': calif_trib.descripcion,
            'ingreso_por_montos': calif_trib.ingreso_por_montos,
        }
        
        # --- CAMBIO: Rellenar con F19 ---
        todos_los_factores_ui = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI + FACTORES_DIRECTOS_UI
        for nombre_campo in todos_los_factores_ui:
            codigo_factor_bruto = nombre_campo.split('_')[-1]
            codigo_factor_db = f"F{codigo_factor_bruto.zfill(2)}" # 'F08', 'F09', 'F19'
            initial_data[nombre_campo] = factores_dict.get(codigo_factor_db, Decimal('0.00'))

        form = CalificacionForm(initial=initial_data)
        context = {
            'form': form,
            'titulo_pagina': f'Modificar Calificación (ID: {calif.id_calificacion})',
            'calificacion': calif 
        }
    return render(request, 'calificaciones/mantenedor_form.html', context)


# ==========================================================
#  VISTA 6: Carga Masiva (Reescrita con Validación Fila-a-Fila)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Corredor', 'Administrador'])
def calificacion_carga_masiva_view(request):
    
    if request.method == 'POST':
        archivo_csv = request.FILES.get('archivo_csv')
        if not archivo_csv:
            messages.error(request, 'No se seleccionó ningún archivo.')
            return redirect('calificaciones:carga_masiva')
        if not archivo_csv.name.endswith('.csv'):
            messages.error(request, 'El archivo no es un CSV.')
            return redirect('calificaciones:carga_masiva')

        # --- Definir cabeceras CSV (basado en tu spec) ---
        cabeceras_base = [
            'Ejercicio', 'Mercado', 'Instrumento', 'Fecha', 
            'Secuencia', 'Numero de dividendo', 'Tipo sociedad', 'Valor Historico'
        ]
        # (Usamos F19, no F19A)
        cabeceras_factores_csv = [f'Factor {i}' for i in range(8, 38)]
        cabeceras_requeridas = cabeceras_base + cabeceras_factores_csv

        # --- Obtener objetos necesarios ---
        id_usuario_actual = request.session.get('id_usuario')
        usuario_app = get_object_or_404(Usuario, id_usuario=id_usuario_actual)
        
        # --- NUEVA LÓGICA DE ESTADOS ---
        try:
            estado_valido = Estado.objects.get(nombre='Activo') # ID 5
            estado_invalido = Estado.objects.get(nombre='Invalido') # El que acabas de crear
        except Estado.DoesNotExist:
            messages.error(request, 'Error crítico: Los estados "Activo" o "Invalido" no existen en la BBDD.')
            return redirect('calificaciones:carga_masiva')

        # Crear el registro del Archivo
        nuevo_archivo = Archivo.objects.create(
            nombre_archivo=archivo_csv.name,
            fecha_carga=timezone.now(),
            estado_validacion='Pendiente',
            id_usuario=usuario_app,
            id_estado=estado_valido # El archivo en sí está 'Activo'
        )

        # Contadores y log de errores
        registros_validos = 0
        registros_invalidos = 0
        errores_fila = []

        try:
            data_set = archivo_csv.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)
            
            # 1. Validar cabeceras (esto sí es "todo o nada")
            if not all(col in reader.fieldnames for col in cabeceras_requeridas):
                missing = [col for col in cabeceras_requeridas if col not in reader.fieldnames]
                messages.error(request, f'El archivo CSV no tiene las cabeceras requeridas. Faltan: {", ".join(missing)}')
                raise Exception('Cabeceras inválidas') # Abortar carga

            # 2. Procesar fila por fila
            for i, fila in enumerate(reader, 2): # Empezar en 2 (contando la cabecera)
                
                estado_actual = estado_valido
                descripcion_log = f"Carga Masiva - Tipo: {fila.get('Tipo sociedad', 'N/A')}"
                
                try:
                    # --- INICIO DE VALIDACIÓN Y PROCESO POR FILA ---
                    # Usamos una transacción por fila
                    with transaction.atomic():
                    
                        # --- A. Validación de Formato (Fecha) ---
                        try:
                            fecha_pago_dt = datetime.strptime(fila['Fecha'], '%d-%m-%Y')
                            fecha_pago_db = fecha_pago_dt.strftime('%Y-%m-%d')
                        except ValueError:
                            raise Exception(f"Formato de fecha inválido '{fila['Fecha']}'. Use DD-MM-AAAA.")

                        # --- B. Validación de Negocio (Suma de Factores) ---
                        suma_factores_base = Decimal('0.0')
                        for j in range(8, 20): # Factores 8 al 19
                            valor_str = fila.get(f'Factor {j}')
                            suma_factores_base += Decimal(valor_str or '0.0')
                        
                        if suma_factores_base > Decimal('1.00000001'):
                            estado_actual = estado_invalido 
                            # Guardamos la razón del error
                            descripcion_log = f"Error: Suma de factores base ({suma_factores_base}) > 1"

                        # --- C. Buscar/Crear objetos relacionados ---
                        instrumento, _ = Instrumento.objects.get_or_create(
                            nombre=fila['Instrumento'],
                            defaults={'tipo': 'Desconocido', 'moneda': 'N/A'}
                        )
                        mercado, _ = Mercado.objects.get_or_create(
                            nombre=fila['Mercado'],
                            defaults={'pais': 'N/A'}
                        )

                        # --- D. Crear 'Calificacion' (Padre) ---
                        nueva_calificacion = Calificacion.objects.create(
                            fecha_pago=fecha_pago_db,
                            id_usuario=usuario_app,
                            id_instrumento=instrumento,
                            id_mercado=mercado,
                            id_archivo=nuevo_archivo, 
                            id_estado=estado_actual,
                            fecha_registro=timezone.now(),
                            activo=True # Siempre activo (visible), el estado indica validez
                        )

                        # --- E. Crear 'CalificacionTributaria' (Hijo) ---
                        nueva_calif_trib = Calificaciontributaria.objects.create(
                            id_calificacion=nueva_calificacion,
                            secuencia_evento=fila['Secuencia'],
                            evento_capital=fila['Numero de dividendo'],
                            anio=fila['Ejercicio'],
                            valor_historico=Decimal(fila['Valor Historico'] or '0.0'),
                            descripcion=descripcion_log, # Guardamos el log del error aquí
                            ingreso_por_montos=False
                        )
                        
                        # --- F. Crear 'Factortributario' (Nietos) ---
                        # Guardamos los factores *incluso si son inválidos* # para que el usuario pueda ver qué cargó.
                        factores_para_crear = []
                        for codigo_factor_csv in cabeceras_factores_csv: # 'Factor 8', 'Factor 9'...
                            valor_str = fila.get(codigo_factor_csv)
                            if valor_str:
                                valor_factor = Decimal(valor_str)
                                if valor_factor != Decimal('0.0'):
                                    codigo_num_str = codigo_factor_csv.split(' ')[-1]
                                    codigo_db = f"F{codigo_num_str.zfill(2)}"
                                    factores_para_crear.append(
                                        Factortributario(
                                            id_calificacion_tributaria=nueva_calif_trib,
                                            codigo_factor=codigo_db,
                                            descripcion_factor=codigo_factor_csv,
                                            valor_factor=valor_factor
                                        )
                                    )
                        if factores_para_crear:
                            Factortributario.objects.bulk_create(factores_para_crear)

                        # --- G. Actualizar contadores ---
                        if estado_actual == estado_valido:
                            registros_validos += 1
                        else:
                            registros_invalidos += 1
                
                # --- FIN DEL TRY POR FILA ---
                except Exception as e_fila:
                    # Si algo falló (formato de fecha, BBDD, etc.), se revierte la fila
                    registros_invalidos += 1
                    errores_fila.append(f"Fila {i}: {e_fila}")

            # --- 3. Finalizar Proceso ---
            nuevo_archivo.estado_validacion = 'Validado'
            nuevo_archivo.save()
            
            # Log general
            detalle_log = f'Carga Masiva: {registros_validos} válidos, {registros_invalidos} inválidos desde {nuevo_archivo.nombre_archivo}.'
            if errores_fila:
                detalle_log += f" Errores: {'; '.join(errores_fila)}"
                
            Log.objects.create(
                fecha=timezone.now(),
                accion='IMPORT',
                detalle=detalle_log,
                id_usuario=usuario_app,
                id_calificacion=None
            )
            
            messages.success(request, f'¡Proceso completado! Se guardaron {registros_validos} calificaciones válidas.')
            if registros_invalidos > 0:
                messages.warning(request, f'Se encontraron {registros_invalidos} calificaciones inválidas. Revise la grilla (filtrando por estado) o el log de auditoría para más detalles.')
            
            return redirect('calificaciones:lista_calificaciones')

        except Exception as e_general:
            # Captura errores generales (ej. cabeceras)
            nuevo_archivo.estado_validacion = 'Rechazado'
            nuevo_archivo.save()
            Log.objects.create(
                fecha=timezone.now(),
                accion='IMPORT',
                detalle=f'Error fatal en Carga Masiva (archivo: {nuevo_archivo.nombre_archivo}). Error: {e_general}',
                id_usuario=usuario_app,
                id_calificacion=None
            )
            messages.error(request, f'Error al procesar el archivo: {e_general}. No se guardó ningún registro.')
            return redirect('calificaciones:carga_masiva')

    else:
        return render(request, 'calificaciones/carga_masiva.html')
    
# ==========================================================
#  VISTA 7: Exportar a CSV (CU7)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Administrador', 'Auditor']) # Opcional: ¿Corredores también?
def calificacion_export_csv_view(request):
    
    # --- 1. LÓGICA DE FILTROS (Copiada de 'calificacion_list_view') ---
    # Usamos request.GET para leer los mismos filtros de la URL (ej. ?anio=2025)
    form = CalificacionFilterForm(request.GET or None)
    
    id_usuario_actual = request.session.get('id_usuario')
    rol_usuario_actual = request.session.get('rol_nombre')
    
    qs_base = Calificacion.objects.select_related(
        'id_instrumento', 'id_mercado', 'id_usuario', 'id_estado'
    )
    
    # (Lógica de permisos para la consulta)
    qs = qs_base.all()
        
    if form.is_valid():
        if form.cleaned_data.get('mercado'):
            qs = qs.filter(id_mercado=form.cleaned_data['mercado'])
        if form.cleaned_data.get('anio'):
            qs = qs.filter(calificaciontributaria__anio=form.cleaned_data['anio'])
        if form.cleaned_data.get('origen'):
            origen = form.cleaned_data['origen']
            if origen == 'manual':
                qs = qs.filter(id_usuario_id=id_usuario_actual, id_archivo__isnull=True)
            elif origen == 'archivo':
                qs = qs.filter(id_archivo__isnull=False)

    # --- 2. LÓGICA DE PIVOTEO (Copiada de 'calificacion_list_view') ---
    qs = qs.prefetch_related(
        'calificaciontributaria_set__factortributario_set'
    )
    
    # (Usamos F19, como definimos en el último paso)
    codigos_factores_db = [
        'F08', 'F09', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 
        'F18', 'F19', 'F20', 'F21', 'F22', 'F23', 'F24', 'F25', 'F26', 'F27', 
        'F28', 'F29', 'F30', 'F31', 'F32', 'F33', 'F34', 'F35', 'F36', 'F37'
    ]

    # --- 3. PREPARAR EL ARCHIVO CSV ---
    
    # Definir el nombre del archivo
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="reporte_calificaciones.csv"'},
    )
    response.write(u'\ufeff'.encode('utf8')) # BOM para que Excel reconozca UTF-8

    # Definir las cabeceras del CSV (basado en la spec del cliente)
    cabeceras_csv = [
        'Ejercicio', 'Mercado', 'Instrumento', 'Fecha', 
        'Secuencia', 'Numero de dividendo', 'Valor Historico',
        'Estado', 'Origen'
    ]
    # Nombres de factor: "Factor 8", "Factor 9", ...
    cabeceras_factores_csv = [f'Factor {i}' for i in range(8, 38)] 
    
    # Crear el escritor de CSV
    writer = csv.writer(response, delimiter=';') # Usamos ';' para Excel en español
    writer.writerow(cabeceras_csv + cabeceras_factores_csv)

    # --- 4. ESCRIBIR LAS FILAS ---
    for calif in qs:
        # Procesar los datos (lógica de pivoteo simplificada)
        tributaria = calif.calificaciontributaria_set.first()
        factores_dict = {}
        if tributaria:
            factores_lista = tributaria.factortributario_set.all()
            factores_dict = {f.codigo_factor: f.valor_factor for f in factores_lista}
        
        # Preparar la fila base
        fila = [
            tributaria.anio if tributaria else '',
            calif.id_mercado.nombre if calif.id_mercado else '',
            calif.id_instrumento.nombre if calif.id_instrumento else '',
            calif.fecha_pago.strftime('%d-%m-%Y') if calif.fecha_pago else '',
            tributaria.secuencia_evento if tributaria else '',
            tributaria.evento_capital if tributaria else '',
            tributaria.valor_historico if tributaria else '',
            calif.id_estado.nombre if calif.id_estado else '',
            'Archivo' if calif.id_archivo else 'Manual',
        ]
        
        # Añadir los factores a la fila
        for codigo in codigos_factores_db: # F08, F09...
            valor = factores_dict.get(codigo, Decimal('0.00'))
            fila.append(valor)
        
        # Escribir la fila en el archivo
        writer.writerow(fila)

    return response


# ==========================================================
#  VISTA 8: Carga Masiva de Montos (DJ1948)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Corredor', 'Administrador'])
def calificacion_carga_montos_view(request):
    
    if request.method == 'POST':
        archivo_csv = request.FILES.get('archivo_csv')
        if not archivo_csv:
            messages.error(request, 'No se seleccionó ningún archivo.')
            return redirect('calificaciones:carga_masiva_montos')
        if not archivo_csv.name.endswith('.csv'):
            messages.error(request, 'El archivo no es un CSV.')
            return redirect('calificaciones:carga_masiva_montos')

        # --- Definir cabeceras CSV (basado en tu nueva spec) ---
        cabeceras_base = [
            'Ejercicio', 'Mercado', 'Instrumento', 'Fecha', 
            'Secuencia', 'Numero de dividendo', 'Tipo sociedad', 'Valor Historico'
        ]
        # (Usamos F19, no F19A)
        cabeceras_montos_csv = [f'Monto_{i:02d}' for i in range(8, 38)] # Monto_08 ... Monto_37
        cabeceras_requeridas = cabeceras_base + cabeceras_montos_csv

        # --- Obtener objetos necesarios ---
        id_usuario_actual = request.session.get('id_usuario')
        usuario_app = get_object_or_404(Usuario, id_usuario=id_usuario_actual)
        try:
            estado_valido = Estado.objects.get(nombre='Activo')
            estado_invalido = Estado.objects.get(nombre='Invalido')
        except Estado.DoesNotExist:
            messages.error(request, 'Error crítico: Los estados "Activo" o "Invalido" no existen.')
            return redirect('calificaciones:carga_masiva_montos')

        nuevo_archivo = Archivo.objects.create(
            nombre_archivo=archivo_csv.name,
            fecha_carga=timezone.now(),
            estado_validacion='Pendiente',
            id_usuario=usuario_app,
            id_estado=estado_valido
        )

        # Contadores y log de errores
        registros_validos = 0
        registros_invalidos = 0
        errores_fila = []

        try:
            data_set = archivo_csv.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            # Usamos separador coma (,)
            reader = csv.DictReader(io_string, delimiter=',')
            
            # 1. Validar cabeceras
            if not all(col in reader.fieldnames for col in cabeceras_requeridas):
                missing = [col for col in cabeceras_requeridas if col not in reader.fieldnames]
                messages.error(request, f'El archivo CSV no tiene las cabeceras requeridas. Faltan: {", ".join(missing)}')
                raise Exception('Cabeceras inválidas')

            # 2. Procesar fila por fila
            for i, fila in enumerate(reader, 2):
                
                estado_actual = estado_valido
                descripcion_log = f"Carga Masiva (Montos) - Tipo: {fila.get('Tipo sociedad', 'N/A')}"
                valores_finales = {} # Para guardar los *factores calculados*
                
                try:
                    # --- INICIO DE VALIDACIÓN Y PROCESO POR FILA ---
                    with transaction.atomic():
                    
                        # --- A. Validación de Formato (Fecha AAAA-MM-DD) ---
                        try:
                            fecha_pago_db = fila['Fecha']
                            datetime.strptime(fecha_pago_db, '%Y-%m-%d')
                        except ValueError:
                            raise Exception(f"Formato de fecha inválido '{fila['Fecha']}'. Use AAAA-MM-DD.")

                        # --- B. LÓGICA DE CÁLCULO (Montos -> Factores) ---
                        # (Idéntica a 'calificacion_create_view')
                        
                        # 1. Sumar montos base (Monto_08 a Monto_19)
                        suma_total_montos = Decimal('0.0')
                        for campo_ui in FACTORES_BASE_UI: # 'factor_08', 'factor_09'...
                            codigo_monto_csv = f"Monto_{campo_ui.split('_')[-1]}" # 'Monto_08', 'Monto_09'...
                            suma_total_montos += Decimal(fila.get(codigo_monto_csv) or '0.0')

                        precision = Decimal('0.00000001')
                        
                        if suma_total_montos > 0:
                            # 2. Calcular factores 8-33
                            campos_a_calcular = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI
                            for campo_ui in campos_a_calcular:
                                codigo_monto_csv = f"Monto_{campo_ui.split('_')[-1]}"
                                codigo_factor_db = f"F{campo_ui.split('_')[-1].zfill(2)}" # F08, F09, F19...
                                
                                monto_campo = Decimal(fila.get(codigo_monto_csv) or '0.0')
                                factor_calculado = (monto_campo / suma_total_montos).quantize(precision, rounding=ROUND_HALF_UP)
                                valores_finales[codigo_factor_db] = factor_calculado
                        else:
                            # 3. Si suma es 0, todos los factores calculados son 0
                            campos_a_calcular = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI
                            for campo_ui in campos_a_calcular:
                                codigo_factor_db = f"F{campo_ui.split('_')[-1].zfill(2)}"
                                valores_finales[codigo_factor_db] = Decimal('0.0')
                        
                        # 4. Los factores directos (34-37) se toman del monto
                        for campo_ui in FACTORES_DIRECTOS_UI:
                            codigo_monto_csv = f"Monto_{campo_ui.split('_')[-1]}"
                            codigo_factor_db = f"F{campo_ui.split('_')[-1].zfill(2)}"
                            valores_finales[codigo_factor_db] = Decimal(fila.get(codigo_monto_csv) or '0.0')

                        # --- C. Buscar/Crear objetos relacionados ---
                        instrumento, _ = Instrumento.objects.get_or_create(
                            nombre=fila['Instrumento'],
                            defaults={'tipo': 'Desconocido', 'moneda': 'N/A'}
                        )
                        mercado, _ = Mercado.objects.get_or_create(
                            nombre=fila['Mercado'],
                            defaults={'pais': 'N/A'}
                        )

                        # --- D. Crear 'Calificacion' (Padre) ---
                        nueva_calificacion = Calificacion.objects.create(
                            fecha_pago=fecha_pago_db,
                            id_usuario=usuario_app, # El usuario que carga
                            id_instrumento=instrumento,
                            id_mercado=mercado,
                            id_archivo=nuevo_archivo, 
                            id_estado=estado_actual, # Siempre Válido (no hay validación de suma en montos)
                            fecha_registro=timezone.now(),
                            activo=True 
                        )

                        # --- E. Crear 'CalificacionTributaria' (Hijo) ---
                        nueva_calif_trib = Calificaciontributaria.objects.create(
                            id_calificacion=nueva_calificacion,
                            secuencia_evento=fila['Secuencia'],
                            evento_capital=fila['Numero de dividendo'],
                            anio=fila['Ejercicio'],
                            valor_historico=Decimal(fila['Valor Historico'] or '0.0'),
                            descripcion=descripcion_log,
                            ingreso_por_montos=True 
                        )
                        
                        # --- F. Crear 'Factortributario' (Nietos) ---
                        # Guardamos los *factores calculados*
                        factores_para_crear = []
                        for codigo_db, valor_factor in valores_finales.items():
                            if valor_factor is not None and valor_factor != Decimal('0.0'):
                                factores_para_crear.append(
                                    Factortributario(
                                        id_calificacion_tributaria=nueva_calif_trib,
                                        codigo_factor=codigo_db,
                                        descripcion_factor=f"Factor-{codigo_db[1:]}",
                                        valor_factor=valor_factor
                                    )
                                )
                        if factores_para_crear:
                            Factortributario.objects.bulk_create(factores_para_crear)

                        registros_validos += 1
                
                # --- FIN DEL TRY POR FILA ---
                except Exception as e_fila:
                    registros_invalidos += 1
                    errores_fila.append(f"Fila {i}: {e_fila}")

            # --- 3. Finalizar Proceso ---
            nuevo_archivo.estado_validacion = 'Validado'
            nuevo_archivo.save()
            
            detalle_log = f'Carga Masiva (Montos): {registros_validos} válidos, {registros_invalidos} inválidos desde {nuevo_archivo.nombre_archivo}.'
            if errores_fila:
                detalle_log += f" Errores: {'; '.join(errores_fila)}"
            
            Log.objects.create(
                fecha=timezone.now(),
                accion='IMPORT',
                detalle=detalle_log,
                id_usuario=usuario_app,
                id_calificacion=None
            )
            
            messages.success(request, f'¡Proceso completado! Se guardaron {registros_validos} calificaciones válidas.')
            if registros_invalidos > 0:
                messages.warning(request, f'Se encontraron {registros_invalidos} filas con errores. Revise el log de auditoría para más detalles.')
            
            return redirect('calificaciones:lista_calificaciones')

        except Exception as e_general:
            nuevo_archivo.estado_validacion = 'Rechazado'
            nuevo_archivo.save()
            Log.objects.create(
                fecha=timezone.now(),
                accion='IMPORT',
                detalle=f'Error fatal en Carga Masiva (Montos): {e_general}',
                id_usuario=usuario_app,
                id_calificacion=None
            )
            messages.error(request, f'Error al procesar el archivo: {e_general}. No se guardó ningún registro.')
            return redirect('calificaciones:carga_masiva_montos')

    else:
        # --- Lógica GET ---
        return render(request, 'calificaciones/carga_masiva_montos.html')
    
# ==========================================================
#  VISTA 9: Dashboard (Criterio 1)
# ==========================================================
@login_requerido_personalizado
def dashboard_view(request):
    
    # --- 1. Estadísticas para Tarjetas (Cards) ---
    total_calificaciones = Calificacion.objects.count()
    
    # Lógica de Origen (Manual vs. Sistema)
    manual_count = Calificacion.objects.filter(id_usuario__isnull=False).count()
    sistema_count = Calificacion.objects.filter(id_usuario__isnull=True).count()
    
    # --- 2. Datos para Gráfico de Estado (Válido vs. Inválido) ---
    # (Usamos el Manager 'objects_all' para contar también las borradas/inactivas)
    qs_estados = Calificacion.objects_all.values(
        'id_estado__nombre' # Agrupar por el nombre del estado
    ).annotate(
        count=Count('id_calificacion') # Contar cuántas hay en cada grupo
    ).order_by('-count')

    # Convertir a formato Chart.js
    chart_estados_data = {
        "labels": [item['id_estado__nombre'] for item in qs_estados],
        "data": [item['count'] for item in qs_estados],
    }

    # --- 3. Datos para Gráfico de Mercado (Top 5) ---
    qs_mercados = Calificacion.objects.values(
        'id_mercado__nombre'
    ).annotate(
        count=Count('id_calificacion')
    ).order_by('-count')[:5] # Tomar los 5 principales

    chart_mercados_data = {
        "labels": [item['id_mercado__nombre'] for item in qs_mercados],
        "data": [item['count'] for item in qs_mercados],
    }

    context = {
        'total_calificaciones': total_calificaciones,
        'manual_count': manual_count,
        'sistema_count': sistema_count,
        
        # Pasamos los datos como JSON para que JavaScript los lea
        'chart_estados_json': json.dumps(chart_estados_data),
        'chart_mercados_json': json.dumps(chart_mercados_data),
    }
    
    # Usaremos la misma plantilla 'home_temporal.html', pero con datos
    return render(request, 'home_temporal.html', context)
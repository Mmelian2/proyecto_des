
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from persona.models import TablaDepartamento, TablaLocalidad, TablaMunicipio, TablaProvincia, ubicaciones
from .forms import CuitForm, OferenteForm, UbiComercio
from .models import Oferente, ubicacionesComercio
from afip import Afip
from geopy.distance import geodesic
from geopy.distance import distance

cert = open('oferente/certificado.crt').read()
key = open('oferente/private_key.key').read()

afip = Afip({
    "CUIT": 23395413929,
    "cert": cert,
    "key": key,
    "access_token": "xkGoHbluDKEPBiW9kFGqsHdwb54q2rAEU06WCZHE8cJsYz77nF0by7Vy09WT4Ken",
    "production": True
})


def verificarCuit(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Para registrar tu comercio primero debes iniciar sesión')
        # Redirige al usuario a la página de inicio de sesión, pasando la URL actual como `next`
        login_url = f"{reverse('login')}?next={request.path}"
        return redirect(login_url)
    nombre = apellido = direccion = '-----'  # Inicializa las variables

    if request.method == 'POST':
        form = CuitForm(request.POST)
        if form.is_valid():
            cuit = form.cleaned_data['cuit']
            # Verificar si el CUIT ya está registrado en la base de datos
            if Oferente.objects.filter(cuit=cuit).exists():
                messages.error(request, f"El CUIT {cuit} ya está registrado.")
                return render(request, 'oferente/verificarCuit.html', {'form': form})
            try:
                
                # Verificar si el CUIT está inscrito en el padrón de AFIP
                res = afip.RegisterInscriptionProof.getTaxpayerDetails(cuit)
                print(res)
                datos_generales = res.get('datosGenerales', {})
                error_constancia = res.get('errorConstancia', {})
                
                if datos_generales:             
                    nombre = datos_generales.get('razonSocial', '---')
                    apellido = datos_generales.get('apellido', '--')
                    
                    domicilio_fiscal = datos_generales.get('domicilioFiscal', {})
                    direccion = domicilio_fiscal.get('direccion', '----')
                    
                    messages.success(request, f"ESTÁS INSCRIPTO EN AFIP. El CUIT {cuit} pertenece a {nombre} {apellido} con dirección {direccion}. Puedes continuar")
                    request.session['cuit_validado'] = cuit
                    request.session['nombre']=nombre
                    request.session['apellido']=apellido
                    request.session['direccion']=direccion
                    return redirect('registrar_comercio')
                
                elif error_constancia:
                    nombre = error_constancia.get('razonSocial', '--')
                    apellido = error_constancia.get('apellido', '---')
                    
                    domicilio_fiscal = error_constancia.get('domicilioFiscal', {})
                    direccion = error_constancia.get('direccion', '----')
                    
                    messages.success(request, f"ESTÁS INSCRIPTO EN AFIP. El CUIT {cuit} pertenece a {nombre} {apellido} con dirección {direccion}. Puedes continuar")
                    request.session['cuit_validado'] = cuit
                    request.session['nombre']=nombre
                    request.session['apellido']=apellido
                    request.session['direccion']=direccion
                    return redirect('registrar_comercio')
                
            except Exception as e:
                messages.error(request, f"No se encontró el CUIT ingresado: {cuit}. Error")
        else:
            messages.error(request, "Formulario no válido")
    else:
        form = CuitForm()
    
    return render(request, 'oferente/verificarCuit.html', {'form': form})


def registrarComercio(request):
    nombre = request.session.get('nombre', '-----')
    apellido = request.session.get('apellido', '-----')
    direccion = request.session.get('direccion', '-----')
    cuit=request.session.get('cuit_validado')
    if request.method == 'POST':
        cuit = request.session.get('cuit_validado')
        nombre = request.session.get('nombre')
        apellido = request.session.get('apellido')
        direccion = request.session.get('direccion')
        form = OferenteForm(request.POST)
        if form.is_valid():
            oferente = form.save(commit=False)
            oferente.cuit = cuit
            oferente.id_usuario = request.user  # Relaciona el usuario autenticado
            oferente.save()
            messages.success(request, 'El comercio ha sido registrado exitosamente.')
            return redirect('ubicacion_comercio',comercio_id=oferente.pk)
        else:
            messages.error(request, "Verifique los datos ingresados.")
    else:
        form = OferenteForm()
    
    return render(request, 'oferente/registrarComercio.html', {'form': form,'cuit':cuit, 'nombre':nombre,'apellido':apellido,'direccion':direccion,})




def load_provincias(request):
    pais_id = request.GET.get('cod_pais') 
    if pais_id:
        provincias = TablaProvincia.objects.filter(pais_id_id=pais_id).order_by('nom_pcia')
        data = list(provincias.values('cod_pcia', 'nom_pcia'))
    else:
        data = []
    return JsonResponse(data, safe=False)

def load_deptos(request):
    provincia_id = request.GET.get('cod_pcia')  
    if provincia_id:
        departamentos = TablaDepartamento.objects.filter(provincia_id_id=provincia_id).order_by('nom_depto')
        data = list(departamentos.values('cod_depto', 'nom_depto'))
    else:
        data = []
    return JsonResponse(data, safe=False)

def load_municipios(request):
    depto_id = request.GET.get('depto_id')  
    if depto_id:
        municipios = TablaMunicipio.objects.filter(departamento_id_id=depto_id).order_by('nom_agl')
        data = list(municipios.values('cod_agl', 'nom_agl'))
    else:
        data = []
    return JsonResponse(data, safe=False)


def load_localidad(request):
    municipio_id = request.GET.get('municipio_id')  
    if municipio_id:
        localidades = TablaLocalidad.objects.filter(municipio_id_id=municipio_id).order_by('nombre')
        data = list(localidades.values('cod_ase', 'nombre'))
    else:
        data = []
    return JsonResponse(data, safe=False)

def ubicacion_comercio(request,comercio_id):
    comercio=get_object_or_404(Oferente,pk=comercio_id)
    if request.method=='POST':
        form=UbiComercio(request.POST)
        if form.is_valid():
            ubicacion= form.save(commit=False)
            ubicacion.comercio_id=comercio
            ubicacion.save()
            return redirect('index')
        else: messages.error(request, 'Verifique los datos registrados')
    else:
        form = UbiComercio()
    return render(request, 'oferente/ubicaciones_comercio.html', {'form': form})

def lista_comercio(request):
    if request.user.is_authenticated:
        # Filtrar los comercios asociados al usuario logueado
        comercios = Oferente.objects.filter(id_usuario=request.user)
        
        # Crear una lista organizada con los comercios y sus ubicaciones
        comercios_con_ubicaciones = []
        for comercio in comercios:
            # Obtener las ubicaciones relacionadas con el comercio actual
            ubicaciones = ubicacionesComercio.objects.filter(comercio_id=comercio)
            
            # Agregar al diccionario la información del comercio y sus ubicaciones
            comercios_con_ubicaciones.append({
                'comercio': comercio,
                'ubicaciones': ubicaciones
            })
        
        return render(request, 'oferente/lista_comercios.html', {
            'comercios_con_ubicaciones': comercios_con_ubicaciones
        })
    else:
        return redirect('login')
    
def perfil_comercio(request, comercio_id):
        comercio = get_object_or_404(Oferente, id=comercio_id)

        return render(request, 'oferente/perfil_comercio.html', {'comercio': comercio})


def comercios(request):
    comercios_en_radio = []
    if request.user.is_authenticated:
        try:
            persona = request.user.persona_id
            ubicacion_usuario = get_object_or_404(ubicaciones, persona_id=persona)

            lat_usuario = float(ubicacion_usuario.latitud)
            lon_usuario = float(ubicacion_usuario.longitud)

            # Limita la distancia en kilómetros
            radio_km = 100
            ubicaciones_comercio = ubicacionesComercio.objects.filter(comercio_id__habilitado=True)

            for comercio in ubicaciones_comercio:
                if comercio.comercio_id and comercio.comercio_id.nombrecomercio:
                    distancia_km = distance(
                        (lat_usuario, lon_usuario),
                        (float(comercio.latitud), float(comercio.longitud))
                    ).km
                    if distancia_km <= radio_km:
                        comercios_en_radio.append({
                            "id": comercio.comercio_id.id,
                            "nombre": comercio.comercio_id.nombrecomercio,
                            "latitud": float(comercio.latitud),
                            "longitud": float(comercio.longitud),
                        })
            # Verificar si el usuario tiene comercios registrados
            tiene_comercios = Oferente.objects.filter(id_usuario=request.user).exists()
        except ubicaciones.DoesNotExist:
            pass
    else:
        ubicaciones_comercio = ubicacionesComercio.objects.filter(comercio_id__habilitado=True)
        for comercio in ubicaciones_comercio:
            if comercio.comercio_id and comercio.comercio_id.nombrecomercio:
                comercios_en_radio.append({
                    "id": comercio.comercio_id.id,
                    "nombre": comercio.comercio_id.nombrecomercio,
                    "latitud": str(comercio.latitud).replace(',', '.'),
                    "longitud": str(comercio.longitud).replace(',', '.'),
                })
    return render(request, 'usuarios/comercios.html', {
        'ubicacion_usuario': {
            'latitud': float(ubicacion_usuario.latitud) if ubicacion_usuario else None,
            'longitud': float(ubicacion_usuario.longitud) if ubicacion_usuario else None,
        } if request.user.is_authenticated else None,
        'comercios_en_radio': comercios_en_radio,
        'usuario_autenticado': request.user.is_authenticated,  # Nuevo parámetro
        'tiene_comercios': tiene_comercios,  # Variable para mostrar botones en el nav en el template
    })
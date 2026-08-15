import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- FUNCIONES DE FORMATO Y AYUDA ---

def format_moneda(valor):
    try:
        return f"${float(valor):,.2f} USD"
    except (ValueError, TypeError):
        return "$0.00 USD"

def format_fecha_ingles(fecha):
    if not fecha:
        return ""
    return fecha.strftime("%B %d, %Y")

# --- GENERACIÓN DEL HTML DE CORREO ---

def generar_html_cotizacion(datos_generales, lista_habitaciones):
    # Generar la sección de opciones de habitaciones dinámicamente
    bloques_habitaciones_html = ""
    
    for i, hab in enumerate(lista_habitaciones, 1):
        monto_estadia = hab['noches'] * hab['precio_noche']
        
        bloques_habitaciones_html += f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="width: 100% !important; margin-bottom: 20px; background-color: #F8FAFC; border-radius: 6px; border: 1px solid #E2E8F0; padding: 15px;">
          <tr>
            <td align="left" style="color: #1E3A8A; font-weight: bold; font-size: 16px; padding-bottom: 8px;">
              Option {i}: {hab['tipo']} ({hab['tarifa_tipo']})
            </td>
          </tr>
          <tr>
            <td align="left" style="font-size: 14px; color: #555; padding-bottom: 10px;">
              <strong>Nights:</strong> {hab['noches']} | <strong>Rate per night:</strong> {format_moneda(hab['precio_noche'])} (Taxes included)
            </td>
          </tr>
          <tr>
            <td align="left" style="font-size: 14px; color: #333; padding-top: 8px; border-top: 1px dashed #CBD5E1;">
              <strong>Stay Subtotal:</strong> {format_moneda(monto_estadia)}
            </td>
          </tr>
        </table>
        """

    # Fila opcional de servicios adicionales
    fila_servicio_html = ""
    if datos_generales['monto_servicio'] > 0:
        fila_servicio_html = f"""
        <tr>
          <td align="left" style="padding: 10px 0; color: #555; font-style: italic; border-top: 1px solid #E2E8F0;">
            Additional Services: <span style="font-size: 13px; color: #64748B; font-style: normal;">{datos_generales['texto_servicio']}</span>
          </td>
          <td align="right" style="padding: 10px 0; color: #444; border-top: 1px solid #E2E8F0; font-weight: bold;">
            {format_moneda(datos_generales['monto_servicio'])}
          </td>
        </tr>"""

    # Plantilla Base (600px para Emails)
    cuerpo_html = f"""
    <table width="600" border="0" cellpadding="0" cellspacing="0" align="left" style="width: 600px; min-width: 600px; font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; background-color: #ffffff; border: 1px solid #eeeeee;">
      <tr>
        <td align="left" style="padding: 30px; border-bottom: 3px solid #D4AF37;">
          <img src="https://www.loscabosguide.com/wp-content/uploads/2019/03/logo-casa-dorada-los-cabos-2019-1024x268.jpg" width="280" style="display: block; border: 0;">
        </td>
      </tr>
      <tr>
        <td align="left" style="padding: 30px;">
          <h2 style="color: #1E3A8A; margin: 0 0 20px 0; font-weight: normal;">Your Custom Quotation</h2>
          <p style="font-size: 16px; line-height: 1.5; margin: 0 0 12px 0;">Dear <strong>{datos_generales['nombre']}</strong>,</p>
          <p style="font-size: 15px; line-height: 1.6; color: #555; margin: 0 0 20px 0;">Thank you for considering <strong>Casa Dorada Los Cabos Resort & Spa</strong>. Here are your personalized room options:</p>
          
          <!-- General Details -->
          <table width="100%" border="0" cellpadding="0" cellspacing="0" style="width: 100% !important; font-size: 14px; margin-bottom: 25px;">
            <tr style="border-bottom: 1px solid #eee;"><td align="left" style="padding: 8px 0; color: #888; width: 30%; font-size: 11px; font-weight: bold; text-transform: uppercase;">Arrival</td><td align="left" style="padding: 8px 0; font-weight: bold;">{format_fecha_ingles(datos_generales['llegada'])}</td></tr>
            <tr style="border-bottom: 1px solid #eee;"><td align="left" style="padding: 8px 0; color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase;">Departure</td><td align="left" style="padding: 8px 0; font-weight: bold;">{format_fecha_ingles(datos_generales['salida'])}</td></tr>
            <tr style="border-bottom: 1px solid #eee;"><td align="left" style="padding: 8px 0; color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase;">Guests</td><td align="left" style="padding: 8px 0;">{datos_generales['huespedes']}</td></tr>
          </table>

          <!-- Room Options Header -->
          <h3 style="color: #1E3A8A; font-size: 16px; margin: 0 0 15px 0;">Available Options</h3>
          
          {bloques_habitaciones_html}
          
          {fila_servicio_html}

          <!-- CTA & Policies -->
          <table width="100%" border="0" cellpadding="0" cellspacing="0" style="width: 100% !important; margin-top: 25px;">
            <tr>
              <td align="left">
                <a href="{datos_generales['link_pago']}" style="background-color: #1E3A8A; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block; text-transform: uppercase; font-size: 14px;">Secure Your Booking</a>
                <p style="font-size: 12px; color: #999; margin: 15px 0 0 0;">Quote valid until: <strong>{format_fecha_ingles(datos_generales['valido_hasta'])}</strong></p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td align="left" style="background-color: #EDF2F7; padding: 25px 30px; border-top: 1px solid #E2E8F0; font-size: 13px; color: #555;">
          <h4 style="margin: 0 0 10px 0; color: #1E3A8A; text-transform: uppercase; font-size: 12px;">Policies</h4>
          <p style="margin: 0 0 5px 0; line-height: 1.4;"><strong>Deposit:</strong> {datos_generales['deposito']}</p>
          <p style="margin: 0; line-height: 1.4;"><strong>Cancellation:</strong> {datos_generales['cancelacion']}</p>
        </td>
      </tr>
      <tr>
        <td align="left" style="background-color: #1a1a1a; padding: 20px 30px; color: #999; font-size: 11px;">
          <p style="color: #fff; margin: 0 0 5px 0; font-weight: bold;">Casa Dorada Los Cabos Resort & Spa</p>
          <p style="margin: 0;">Av. del Pescador s/n, Cabo San Lucas, B.C.S. | US: 1-866-448-0151</p>
        </td>
      </tr>
    </table>
    """
    return cuerpo_html

# --- FUNCIÓN GMAIL API PARA CREAR BORRADOR ---

def crear_borrador_gmail(email_destino, asunto, cuerpo_html, credenciales_json):
    try:
        creds = Credentials.from_authorized_user_info(credenciales_json)
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEMultipart()
        message['to'] = email_destino
        message['subject'] = asunto

        msg_html = MIMEText(cuerpo_html, 'html')
        message.attach(msg_html)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': raw_message}}

        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        return True, draft['id']
    except Exception as e:
        return False, str(e)

# --- INTERFAZ STREAMLIT ---

st.set_page_config(page_title="Cotizador - Casa Dorada", layout="wide")
st.title("🏨 Generador de Cotizaciones - Casa Dorada")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. Datos Generales")
    nombre = st.text_input("Nombre del Huésped", "John Doe")
    email = st.text_input("Email del Huésped", "cliente@example.com")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        llegada = st.date_input("Fecha de Llegada", datetime.date.today())
    with col_f2:
        salida = st.date_input("Fecha de Salida", datetime.date.today() + datetime.timedelta(days=3))

    huespedes = st.text_input("Total de Huéspedes", "2 Adults, 1 Child")
    link_pago = st.text_input("Link de Pago", "https://casadorada.com/pay")
    valido_hasta = st.date_input("Válido Hasta", datetime.date.today() + datetime.timedelta(days=5))

    st.subheader("2. Habitaciones y Tarifas")
    
    # Manejo dinámico de opciones de habitación mediante Session State
    if 'habitaciones' not in st.session_state:
        st.session_state.habitaciones = []

    def agregar_habitacion():
        st.session_state.habitaciones.append({
            "tipo": "Junior Suite Ocean View",
            "tarifa_tipo": "Flexible Rate",
            "noches": (salida - llegada).days,
            "precio_noche": 350.00
        })

    def eliminar_habitacion(index):
        st.session_state.habitaciones.pop(index)

    if st.button("➕ Agregar Opción de Habitación"):
        agregar_habitacion()

    for idx, hab in enumerate(st.session_state.habitaciones):
        with st.expander(f"Opción #{idx+1}: {hab['tipo']}", expanded=True):
            hab['tipo'] = st.selectbox(f"Tipo Habitación #{idx+1}", [
                "Junior Suite Ocean View", 
                "One Bedroom Suite", 
                "Two Bedroom Suite", 
                "Penthouse"
            ], key=f"tipo_{idx}")
            
            hab['tarifa_tipo'] = st.radio(f"Tipo de Tarifa #{idx+1}", [
                "Flexible Rate (Refundable)", 
                "Non-Refundable Rate", 
                "All Inclusive Rate"
            ], key=f"tarifa_{idx}")
            
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                hab['noches'] = st.number_input(f"Noches #{idx+1}", min_value=1, value=hab['noches'], key=f"noches_{idx}")
            with col_h2:
                hab['precio_noche'] = st.number_input(f"Precio por Noche (con imp) #{idx+1}", min_value=0.0, value=hab['precio_noche'], key=f"precio_{idx}")
            
            if st.button(f"🗑️ Eliminar Opción #{idx+1}", key=f"del_{idx}"):
                eliminar_habitacion(idx)
                st.rerun()

    st.subheader("3. Servicios Adicionales y Políticas")
    texto_servicio = st.text_input("Descripción Servicio Adicional", "Roundtrip Airport Transportation")
    monto_servicio = st.number_input("Precio Servicio Adicional ($ USD)", min_value=0.0, value=150.00)
    
    deposito = st.text_area("Política de Depósito", "1 night deposit required at booking.")
    cancelacion = st.text_area("Política de Cancelación", "Free cancellation up to 7 days before arrival.")

# Estructurar Datos
datos_generales = {
    "nombre": nombre,
    "email": email,
    "llegada": llegada,
    "salida": salida,
    "huespedes": huespedes,
    "link_pago": link_pago,
    "valido_hasta": valido_hasta,
    "texto_servicio": texto_servicio,
    "monto_servicio": monto_servicio,
    "deposito": deposito,
    "cancelacion": cancelacion
}

html_correo = generar_html_cotizacion(datos_generales, st.session_state.habitaciones)

# Vista previa a la derecha
with col_right:
    st.subheader("👁️ Vista Previa del Email")
    st.components.v1.html(html_correo, height=750, scrolling=True)

    if st.button("🚀 Crear Borrador en Gmail", type="primary"):
        # NOTA: Debes configurar tus credenciales de OAuth2 en Gmail
        # Para pruebas locales puedes usar un token guardado en st.secrets
        if "gmail_credentials" in st.secrets:
            exito, resp = crear_borrador_gmail(
                email, 
                f"Special Quotation | Casa Dorada Los Cabos", 
                html_correo, 
                dict(st.secrets["gmail_credentials"])
            )
            if exito:
                st.success(f"¡Borrador creado con éxito! ID: {resp}")
            else:
                st.error(f"Error al conectar con Gmail: {resp}")
        else:
            st.warning("Debes configurar las credenciales OAuth2 de Gmail en `.streamlit/secrets.toml`.")

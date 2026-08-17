import base64
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import streamlit as st

# --- CATÁLOGO DE RECORRIDOS VIRTUALES ---
VIRTUAL_TOURS = {
    "Junior Suite Ocean View": "https://my.matterport.com/show/?m=ejemplo_jr_suite",
    "One Bedroom Suite": "https://my.matterport.com/show/?m=ejemplo_1bed_suite",
    "Two Bedroom Suite": "https://my.matterport.com/show/?m=ejemplo_2bed_suite",
    "Penthouse": "https://my.matterport.com/show/?m=ejemplo_penthouse",
}

# --- FUNCIONES DE FORMATO ---


def format_moneda(valor, moneda="USD"):
  try:
    val = float(valor)
    if moneda == "MXN":
      return f"${val:,.2f} MXN"
    return f"${val:,.2f} USD"
  except (ValueError, TypeError):
    return "$0.00 USD" if moneda == "USD" else "$0.00 MXN"


def format_fecha_ingles(fecha):
  return fecha.strftime("%B %d, %Y") if fecha else ""


# --- GENERADOR DE PLANTILLA HTML ---


def generar_html_cotizacion(datos, habitaciones, moneda="USD", tipo_cambio=20.0):
  bloques_habitaciones_html = ""

  for i, hab in enumerate(habitaciones, 1):
    # Ajuste de moneda
    factor = tipo_cambio if moneda == "MXN" else 1.0
    precio_noche = hab["precio_noche"] * factor
    monto_estadia = hab["noches"] * precio_noche

    # Tour Virtual
    tour_url = VIRTUAL_TOURS.get(hab["tipo"], "")
    tour_btn = ""
    if tour_url:
      tour_btn = f"""
            <a href="{tour_url}" target="_blank" style="display: inline-block; margin-top: 10px; color: #D4AF37; font-weight: bold; text-decoration: none; font-size: 13px;">
              &#127760; Take 360&deg; Virtual Tour &rarr;
            </a>
            """

    # Beneficios / Valores Agregados
    beneficios_list = ""
    if hab.get("beneficios"):
      items = "".join(
          [f"<li style='margin-bottom: 4px;'>{b.strip()}</li>" for b in hab["beneficios"].split(",") if b.strip()]
      )
      beneficios_list = f"""
            <div style="margin-top: 12px; padding-top: 10px; border-top: 1px dashed #CBD5E1;">
              <strong style="color: #1E3A8A; font-size: 12px; text-transform: uppercase;">Included Plan Benefits:</strong>
              <ul style="margin: 6px 0 0 18px; padding: 0; color: #475569; font-size: 13px;">
                {items}
              </ul>
            </div>
            """

    # Link de pago específico
    link_pago_hab = hab.get("link_pago", datos["link_pago_general"])
    pago_btn = f"""
        <div style="margin-top: 15px; text-align: right;">
          <a href="{link_pago_hab}" target="_blank" style="background-color: #1E3A8A; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block; font-size: 13px;">
            Book Option {i}
          </a>
        </div>
        """

    bloques_habitaciones_html += f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 25px; background-color: #FFFFFF; border-radius: 8px; border: 1px solid #D4AF37; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
          <tr>
            <td align="left" style="color: #1E3A8A; font-weight: bold; font-size: 18px; padding-bottom: 5px;">
              Option {i}: {hab['tipo']}
            </td>
          </tr>
          <tr>
            <td align="left" style="color: #D4AF37; font-weight: bold; font-size: 14px; text-transform: uppercase; padding-bottom: 10px;">
              Rate Plan: {hab['tarifa_tipo']}
            </td>
          </tr>
          <tr>
            <td align="left" style="font-size: 14px; color: #555; padding-bottom: 10px;">
              <strong>Nights:</strong> {hab['noches']} | <strong>Rate per night:</strong> {format_moneda(precio_noche, moneda)} <span style="font-size: 11px; color: #888;">(Taxes incl.)</span>
            </td>
          </tr>
          <tr>
            <td align="left" style="font-size: 15px; color: #1E3A8A; padding-top: 8px; border-top: 1px solid #E2E8F0;">
              <strong>Total Stay:</strong> <span style="font-size: 18px; font-weight: bold;">{format_moneda(monto_estadia, moneda)}</span>
            </td>
          </tr>
          <tr>
            <td align="left">
              {tour_btn}
            </td>
          </tr>
          <tr>
            <td align="left">
              {beneficios_list}
            </td>
          </tr>
          <tr>
            <td align="left">
              {pago_btn}
            </td>
          </tr>
        </table>
        """

  # Servicios Adicionales
  monto_serv = datos["monto_servicio"] * (
      tipo_cambio if moneda == "MXN" else 1.0
  )
  fila_servicio_html = ""
  if monto_serv > 0:
    fila_servicio_html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 20px; background-color: #F8FAFC; padding: 12px 15px; border-radius: 6px;">
          <tr>
            <td align="left" style="color: #555; font-size: 14px;">
              <strong>Additional Service:</strong> {datos['texto_servicio']}
            </td>
            <td align="right" style="color: #1E3A8A; font-weight: bold; font-size: 14px;">
              {format_moneda(monto_serv, moneda)}
            </td>
          </tr>
        </table>"""

  cuerpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #0F172A; font-family: 'Georgia', serif;">
      <center>
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #0F172A; padding: 30px 0;">
          <tr>
            <td align="center">
              <table width="650" border="0" cellpadding="0" cellspacing="0" style="max-width: 650px; width: 100%; font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; background-color: #F8FAFC; border-radius: 8px; overflow: hidden;">
                <!-- Header Gold / Blue -->
                <tr>
                  <td align="center" style="background-color: #1E3A8A; padding: 35px 30px; border-bottom: 4px solid #D4AF37;">
                    <h1 style="color: #FFFFFF; font-family: 'Georgia', serif; margin: 0; font-size: 26px; letter-spacing: 1px;">CASA DORADA</h1>
                    <p style="color: #D4AF37; margin: 5px 0 0 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px;">LOS CABOS RESORT & SPA</p>
                  </td>
                </tr>
                <!-- Body -->
                <tr>
                  <td align="left" style="padding: 35px;">
                    <h2 style="color: #1E3A8A; margin: 0 0 10px 0; font-weight: normal; font-family: 'Georgia', serif;">Personalized Quotation</h2>
                    <p style="font-size: 15px; color: #64748B; margin: 0 0 25px 0;">Prepared exclusively for <strong>{datos['nombre']}</strong></p>
                    
                    <!-- Trip Details Table -->
                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 14px; margin-bottom: 30px;">
                      <tr>
                        <td style="padding: 12px 15px; border-bottom: 1px solid #E2E8F0; color: #64748B; width: 33%;"><strong>CHECK-IN:</strong><br><span style="color: #1E3A8A; font-size: 15px;">{format_fecha_ingles(datos['llegada'])}</span></td>
                        <td style="padding: 12px 15px; border-bottom: 1px solid #E2E8F0; color: #64748B; width: 33%;"><strong>CHECK-OUT:</strong><br><span style="color: #1E3A8A; font-size: 15px;">{format_fecha_ingles(datos['salida'])}</span></td>
                        <td style="padding: 12px 15px; border-bottom: 1px solid #E2E8F0; color: #64748B;"><strong>GUESTS:</strong><br><span style="color: #1E3A8A; font-size: 15px;">{datos['huespedes']}</span></td>
                      </tr>
                    </table>

                    <h3 style="color: #1E3A8A; font-size: 18px; margin: 0 0 20px 0; font-family: 'Georgia', serif; border-bottom: 2px solid #D4AF37; padding-bottom: 5px;">Suites & Rate Options</h3>
                    
                    {bloques_habitaciones_html}
                    {fila_servicio_html}

                    <p style="font-size: 12px; color: #94A3B8; text-align: center; margin-top: 25px;">
                      * This quotation is valid until <strong>{format_fecha_ingles(datos['valido_hasta'])}</strong> and subject to availability.
                    </p>
                  </td>
                </tr>
                <!-- Policies -->
                <tr>
                  <td align="left" style="background-color: #F1F5F9; padding: 25px 35px; border-top: 1px solid #E2E8F0; font-size: 13px; color: #475569;">
                    <h4 style="margin: 0 0 10px 0; color: #1E3A8A; text-transform: uppercase; font-size: 12px;">Resort Policies</h4>
                    <p style="margin: 0 0 6px 0;"><strong>Deposit:</strong> {datos['deposito']}</p>
                    <p style="margin: 0;"><strong>Cancellation:</strong> {datos['cancelacion']}</p>
                  </td>
                </tr>
                <!-- Footer -->
                <tr>
                  <td align="center" style="background-color: #0F172A; padding: 25px 30px; color: #94A3B8; font-size: 11px;">
                    <p style="color: #D4AF37; margin: 0 0 5px 0; font-weight: bold;">Casa Dorada Los Cabos Resort & Spa</p>
                    <p style="margin: 0;">Av. del Pescador s/n, Medano Beach, Cabo San Lucas, B.C.S. | Toll-Free US: 1-866-448-0151</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </center>
    </body>
    </html>
    """
  return cuerpo_html


# --- CONFIGURACIÓN DE STREAMLIT ---
st.set_page_config(
    page_title="Cotizador Luxury - Casa Dorada", layout="wide"
)

st.title("🏨 Cotizador Corporativo - Casa Dorada Los Cabos")

# Configuración Multimoneda
st.sidebar.header("⚙️ Configuración de Moneda")
moneda_seleccionada = st.sidebar.radio("Moneda de Cotización", ["USD", "MXN"])
tipo_cambio_val = st.sidebar.number_input(
    "Tipo de Cambio (MXN por 1 USD)", min_value=1.0, value=20.0
)

col_left, col_right = st.columns([1, 1])

with col_left:
  st.subheader("1. Información de la Reserva")
  nombre = st.text_input("Nombre del Huésped", "John Smith")
  email = st.text_input("Email del Huésped", "jsmith@example.com")

  col_f1, col_f2 = st.columns(2)
  with col_f1:
    llegada = st.date_input("Check-In", datetime.date.today())
  with col_f2:
    salida = st.date_input(
        "Check-Out", datetime.date.today() + datetime.timedelta(days=3)
    )

  noches_calc = (salida - llegada).days if salida > llegada else 1
  huespedes = st.text_input("Huéspedes", "2 Adults, 1 Child")
  link_pago_gen = st.text_input(
      "Link de Pago General", "https://casadorada.com/pay"
  )
  valido_hasta = st.date_input(
      "Cotización Válida Hasta",
      datetime.date.today() + datetime.timedelta(days=5),
  )

  st.subheader("2. Comparativa de Opciones de Habitación")

  # Inicializar Opciones por Defecto (Room Only vs All Inclusive)
  if "habitaciones" not in st.session_state:
    st.session_state.habitaciones = [
        {
            "tipo": "Junior Suite Ocean View",
            "tarifa_tipo": "European Plan (Room Only)",
            "noches": noches_calc,
            "precio_noche": 320.00,
            "beneficios": (
                "Ocean view private balcony, Access to pools & beach, Free"
                " Wi-Fi"
            ),
            "link_pago": "https://casadorada.com/pay/opt1",
        },
        {
            "tipo": "Junior Suite Ocean View",
            "tarifa_tipo": "All Inclusive Plan",
            "noches": noches_calc,
            "precio_noche": 480.00,
            "beneficios": (
                "All gourmet meals & unlimited premium drinks, 24-hr Room"
                " Service, Access to Kids Club, Poolside service"
            ),
            "link_pago": "https://casadorada.com/pay/opt2",
        },
    ]

  if st.button("➕ Agregar Otra Opción de Cotización"):
    st.session_state.habitaciones.append({
        "tipo": "One Bedroom Suite",
        "tarifa_tipo": "European Plan (Room Only)",
        "noches": noches_calc,
        "precio_noche": 450.00,
        "beneficios": "Full kitchen, Living room, Private balcony",
        "link_pago": link_pago_gen,
    })

  for idx, hab in enumerate(st.session_state.habitaciones):
    with st.expander(f"Opción #{idx+1}: {hab['tipo']} ({hab['tarifa_tipo']})"):
      hab["tipo"] = st.selectbox(
          f"Habitación #{idx+1}",
          list(VIRTUAL_TOURS.keys()),
          index=list(VIRTUAL_TOURS.keys()).index(hab["tipo"])
          if hab["tipo"] in VIRTUAL_TOURS
          else 0,
          key=f"tipo_{idx}",
      )

      # Muestra el link 360 detectado automáticamente
      tour_detectado = VIRTUAL_TOURS.get(hab["tipo"], "")
      if tour_detectado:
        st.caption(f"🌐 Tour 360° asignado: [{tour_detectado}]({tour_detectado})")

      hab["tarifa_tipo"] = st.text_input(
          f"Plan de Tarifa #{idx+1}", hab["tarifa_tipo"], key=f"tarifa_{idx}"
      )

      col_h1, col_h2 = st.columns(2)
      with col_h1:
        hab["noches"] = st.number_input(
            f"Noches #{idx+1}",
            min_value=1,
            value=int(hab["noches"]),
            key=f"noches_{idx}",
        )
      with col_h2:
        hab["precio_noche"] = st.number_input(
            f"Precio/Noche (USD) #{idx+1}",
            min_value=0.0,
            value=float(hab["precio_noche"]),
            key=f"precio_{idx}",
        )

      hab["beneficios"] = st.text_area(
          f"Valores Agregados / Incluidos (separados por coma) #{idx+1}",
          hab["beneficios"],
          key=f"beneficios_{idx}",
      )
      hab["link_pago"] = st.text_input(
          f"Link de Pago Opción #{idx+1}",
          hab.get("link_pago", link_pago_gen),
          key=f"link_{idx}",
      )

      if st.button(f"🗑️ Eliminar Opción #{idx+1}", key=f"del_{idx}"):
        st.session_state.habitaciones.pop(idx)
        st.rerun()

  st.subheader("3. Extras y Políticas")
  texto_servicio = st.text_input(
      "Servicio Adicional", "Roundtrip Airport Transportation"
  )
  monto_servicio = st.number_input(
      "Precio Servicio Adicional (USD)", min_value=0.0, value=150.00
  )

  deposito = st.text_area(
      "Garantía/Depósito", "1 night deposit required at the time of booking."
  )
  cancelacion = st.text_area(
      "Política de Cancelación",
      "Free cancellation up to 7 days prior to arrival date.",
  )

datos_generales = {
    "nombre": nombre,
    "email": email,
    "llegada": llegada,
    "salida": salida,
    "huespedes": huespedes,
    "link_pago_general": link_pago_gen,
    "valido_hasta": valido_hasta,
    "texto_servicio": texto_servicio,
    "monto_servicio": monto_servicio,
    "deposito": deposito,
    "cancelacion": cancelacion,
}

html_correo = generar_html_cotizacion(
    datos_generales,
    st.session_state.habitaciones,
    moneda=moneda_seleccionada,
    tipo_cambio=tipo_cambio_val,
)

with col_right:
  st.subheader("👁️ Previsualización del Email Cotización")
  st.components.v1.html(html_correo, height=800, scrolling=True)

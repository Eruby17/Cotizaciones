import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st

st.set_page_config(
    page_title="Cotizador Casa Dorada Los Cabos", page_icon="🏨", layout="wide"
)

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES & ENVÍO DE CORREO
# -----------------------------------------------------------------------------


def enviar_correo_directo(
    email_destino,
    asunto,
    cuerpo_html,
    smtp_server,
    smtp_port,
    remitente,
    password,
    nombre_remitente,
):
  try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"{nombre_remitente} - Casa Dorada <{remitente}>"
    msg["To"] = email_destino

    part_html = MIMEText(cuerpo_html, "html")
    msg.attach(part_html)

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
      server.login(remitente, password)
      server.sendmail(remitente, email_destino, msg.as_string())

    return True, "Cotización enviada exitosamente."
  except Exception as e:
    return False, str(e)


def formatear_precio(monto, moneda, tipo_cambio):
  """Calcula y formatea el precio en USD o MXN según la selección."""
  if moneda == "MXN":
    monto_convertido = monto * tipo_cambio
    return f"${monto_convertido:,.2f} MXN"
  return f"${monto:,.2f} USD"


# -----------------------------------------------------------------------------
# BARRA LATERAL (AGENTES Y CONFIGURACIÓN)
# -----------------------------------------------------------------------------
st.sidebar.header("👤 Perfil de Agente")

# Cargar agentes guardados en st.secrets si existen
agentes_dict = st.secrets.get("agentes", {})

if agentes_dict:
  lista_agentes = [datos["nombre"] for datos in agentes_dict.values()]
  agente_seleccionado = st.sidebar.selectbox(
      "¿Quién envía la cotización?", lista_agentes
  )

  # Extraer datos del agente seleccionado
  for clave, datos in agentes_dict.items():
    if datos["nombre"] == agente_seleccionado:
      remitente_nombre = datos["nombre"]
      remitente_email = datos["email"]
      remitente_password = datos["password"]
      break
else:
  st.sidebar.warning(
      "⚠️ No se encontraron agentes en secrets.toml. Ingresa tus datos"
      " manualmente:"
  )
  remitente_nombre = st.sidebar.text_input("Tu Nombre", "Ejecutivo de Ventas")
  remitente_email = st.sidebar.text_input(
      "Tu Correo", "ventas@casadorada.com"
  )
  remitente_password = st.sidebar.text_input(
      "Contraseña de Aplicación (16 dígitos)", type="password"
  )

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Ajustes de Cotización")

# Selector de Moneda y Tipo de Cambio
moneda_seleccionada = st.sidebar.radio(
    "Moneda de visualización:", ["USD", "MXN"], index=0
)
tipo_cambio = st.sidebar.number_input(
    "Tipo de cambio (USD a MXN):", min_value=1.0, value=20.0, step=0.1
)

# -----------------------------------------------------------------------------
# DATOS DE LA RESERVACIÓN
# -----------------------------------------------------------------------------
st.title("🏨 Cotizador de Reservaciones — Casa Dorada Los Cabos")

col_datos1, col_datos2 = st.columns(2)

with col_datos1:
  nombre_huesped = st.text_input("Nombre del Huésped", "John Doe")
  email_huesped = st.text_input("Correo del Huésped", "huesped@email.com")
  noches = st.number_input("Número de Noches", min_value=1, value=3)

with col_datos2:
  tarifa_ep_usd = st.number_input(
      "Tarifa por noche - European Plan (USD)", min_value=0.0, value=320.0
  )
  tarifa_ai_usd = st.number_input(
      "Tarifa por noche - All Inclusive (USD)", min_value=0.0, value=480.0
  )
  traslado_usd = st.number_input(
      "Traslado Aeropuerto Roundtrip (USD)", min_value=0.0, value=150.0
  )

# Cálculos dinámicos según la moneda elegida
total_ep_usd = tarifa_ep_usd * noches
total_ai_usd = tarifa_ai_usd * noches

# Formateo de precios para la vista previa e interfaz
tarifa_ep_txt = formatear_precio(
    tarifa_ep_usd, moneda_seleccionada, tipo_cambio
)
total_ep_txt = formatear_precio(
    total_ep_usd, moneda_seleccionada, tipo_cambio
)

tarifa_ai_txt = formatear_precio(
    tarifa_ai_usd, moneda_seleccionada, tipo_cambio
)
total_ai_txt = formatear_precio(
    total_ai_usd, moneda_seleccionada, tipo_cambio
)

traslado_txt = formatear_precio(traslado_usd, moneda_seleccionada, tipo_cambio)

# -----------------------------------------------------------------------------
# VISTA PREVIA DE LA COTIZACIÓN (ACTUALIZACIÓN DINÁMICA)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("👁️ Vista Previa de la Cotización")

st.markdown(f"""
**Cotización para:** {nombre_huesped} | **Moneda:** {moneda_seleccionada}

---

**Vista Previa — Opción 1: European Plan (Room Only)**  
*Junior Suite Ocean View*

* **Estancia:** {noches} Noches
* **Tarifa por noche:** {tarifa_ep_txt} *(Impuestos incluidos)*
* **Subtotal Estancia:** {total_ep_txt}
* **Recorrido Virtual 360°:** 🌐 [Explorar Junior Suite en 360°](https://my.matterport.com/show/?m=ejemplo_jr_suite)

**Valores Agregados Incluidos:**
* Balcón privado con vista panorámica al mar.
* Acceso ilimitado a albercas y área de playa Medano.
* Wi-Fi de alta velocidad en suite y áreas comunes.

---

**Vista Previa — Opción 2: All Inclusive Plan**  
*Junior Suite Ocean View*

* **Estancia:** {noches} Noches
* **Tarifa por noche:** {tarifa_ai_txt} *(Impuestos incluidos)*
* **Subtotal Estancia:** {total_ai_txt}
* **Recorrido Virtual 360°:** 🌐 [Explorar Junior Suite en 360°](https://my.matterport.com/show/?m=ejemplo_jr_suite)

**Valores Agregados Incluidos:**
* Alimentos gourmet y bebidas premium ilimitadas.
* Servicio a la habitación 24 horas.
* Acceso al Kids Club y servicio de meseros en albercas y playa.

---

**Servicios Adicionales & Políticas:**
* **Traslado:** Roundtrip Airport Transportation — {traslado_txt}
* **Depósito:** 1 noche de depósito requerida al momento de reservar.
* **Cancelación:** Cancelación gratuita hasta 7 días antes de la llegada.
""")

# -----------------------------------------------------------------------------
# PLANTILLA HTML PARA ENVÍO POR CORREO
# -----------------------------------------------------------------------------
html_correo = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333333; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }}
        .header {{ background-color: #0b2545; color: #ffffff; padding: 15px; text-align: center; border-radius: 6px 6px 0 0; }}
        .option-box {{ background-color: #f9f9f9; border-left: 4px solid #134074; padding: 15px; margin: 15px 0; }}
        .price {{ font-size: 18px; font-weight: bold; color: #134074; }}
        .footer {{ font-size: 12px; color: #777777; margin-top: 20px; border-top: 1px solid #eeeeee; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Casa Dorada Los Cabos Resort & Spa</h2>
        </div>
        <p>Estimado/a <strong>{nombre_huesped}</strong>,</p>
        <p>Es un placer saludarle. A continuación le presentamos la cotización personalizada para su próxima estancia:</p>
        
        <div class="option-box">
            <h3>Opción 1: European Plan (Room Only)</h3>
            <p><strong>Habitación:</strong> Junior Suite Ocean View<br>
            <strong>Estancia:</strong> {noches} Noches<br>
            <strong>Tarifa por noche:</strong> {tarifa_ep_txt}<br>
            <span class="price">Total Estancia: {total_ep_txt}</span></p>
        </div>

        <div class="option-box">
            <h3>Opción 2: All Inclusive Plan</h3>
            <p><strong>Habitación:</strong> Junior Suite Ocean View<br>
            <strong>Estancia:</strong> {noches} Noches<br>
            <strong>Tarifa por noche:</strong> {tarifa_ai_txt}<br>
            <span class="price">Total Estancia: {total_ai_txt}</span></p>
        </div>

        <p><strong>Servicios Adicionales:</strong><br>
        • Traslado Aeropuerto (Roundtrip): {traslado_txt}</p>

        <p>Quedo a su entera disposición para confirmar su reservación o resolver cualquier duda.</p>
        
        <div class="footer">
            <p>Atentamente,<br>
            <strong>{remitente_nombre}</strong><br>
            Casa Dorada Los Cabos Resort & Spa<br>
            {remitente_email}</p>
        </div>
    </div>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# BOTÓN DE ACCIÓN / ENVÍO
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📤 Enviar Cotización")

if st.button("🚀 Enviar Directo al Huésped", type="primary"):
  if not remitente_email or not remitente_password:
    st.error(
        "⚠️ Falta configurar el correo o la contraseña de aplicación del"
        " agente seleccionado."
    )
  elif not email_huesped:
    st.error("⚠️ Por favor ingresa el correo del huésped.")
  else:
    with st.spinner("Enviando correo..."):
      exito, res = enviar_correo_directo(
          email_destino=email_huesped,
          asunto=(
              f"Cotización Especial | Casa Dorada Los Cabos - {nombre_huesped}"
          ),
          cuerpo_html=html_correo,
          smtp_server="smtp.gmail.com",
          smtp_port=465,
          remitente=remitente_email,
          password=remitente_password,
          nombre_remitente=remitente_nombre,
      )
      if exito:
        st.success(
            f"¡Cotización enviada exitosamente a **{email_huesped}** desde la"
            f" cuenta de **{remitente_nombre}**!"
        )
      else:
        st.error(f"Error al enviar el correo: {res}")

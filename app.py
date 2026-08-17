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


def formatear_precio(monto_usd, moneda, tipo_cambio):
  if moneda == "MXN":
    monto_convertido = monto_usd * tipo_cambio
    return f"${monto_convertido:,.2f} MXN"
  return f"${monto_usd:,.2f} USD"


# -----------------------------------------------------------------------------
# BARRA LATERAL (SELECCIÓN DE AGENTE Y CONFIGURACIÓN DE MONEDA)
# -----------------------------------------------------------------------------
st.sidebar.header("👤 Perfil de Agente")

agentes_dict = st.secrets.get("agentes", {})

if agentes_dict:
  lista_agentes = [datos["nombre"] for datos in agentes_dict.values()]
  agente_seleccionado = st.sidebar.selectbox(
      "¿Quién envía la cotización?", lista_agentes
  )

  for clave, datos in agentes_dict.items():
    if datos["nombre"] == agente_seleccionado:
      remitente_nombre = datos["nombre"]
      remitente_email = datos["email"]
      remitente_password = datos["password"]
      break
else:
  st.sidebar.warning("⚠️ No se encontraron agentes configurados en Secrets.")
  remitente_nombre = st.sidebar.text_input("Tu Nombre", "Ejecutivo de Ventas")
  remitente_email = st.sidebar.text_input(
      "Tu Correo", "ventas@casadorada.com"
  )
  remitente_password = st.sidebar.text_input(
      "Contraseña de Aplicación", type="password"
  )

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Ajustes de Moneda")

moneda_seleccionada = st.sidebar.radio(
    "Moneda de visualización:", ["USD", "MXN"], index=0
)
tipo_cambio = st.sidebar.number_input(
    "Tipo de cambio (USD a MXN):", min_value=1.0, value=20.0, step=0.1
)

# -----------------------------------------------------------------------------
# DATOS DE ENTRADA (BASE)
# -----------------------------------------------------------------------------
noches = 3
tarifa_ep_usd = 320.00
tarifa_ai_usd = 480.00
traslado_usd = 150.00

# Cálculos
subtotal_ep_usd = tarifa_ep_usd * noches
subtotal_ai_usd = tarifa_ai_usd * noches

# Formateo dinámico según la moneda seleccionada
tarifa_ep_txt = formatear_precio(
    tarifa_ep_usd, moneda_seleccionada, tipo_cambio
)
subtotal_ep_txt = formatear_precio(
    subtotal_ep_usd, moneda_seleccionada, tipo_cambio
)

tarifa_ai_txt = formatear_precio(
    tarifa_ai_usd, moneda_seleccionada, tipo_cambio
)
subtotal_ai_txt = formatear_precio(
    subtotal_ai_usd, moneda_seleccionada, tipo_cambio
)

traslado_txt = formatear_precio(traslado_usd, moneda_seleccionada, tipo_cambio)

# -----------------------------------------------------------------------------
# VISTA PREVIA ORIGINAL CON PRECIOS DINÁMICOS
# -----------------------------------------------------------------------------
st.markdown(f"""
**Vista Previa — Opción 1: European Plan (Room Only)**  
*Junior Suite Ocean View*

* **Estancia:** {noches} Noches
* **Tarifa por noche:** {tarifa_ep_txt} *(Impuestos incluidos)*
* **Subtotal Estancia:** {subtotal_ep_txt}
* **Recorrido Virtual 360°:** 🌐 [Explorar Junior Suite en 360°](https://my.matterport.com/show/?m=ejemplo_jr_suite)

**Valores Agregados Incluidos:**
* Balcón privado con vista panorámica al mar.
* Acceso ilimitado a albercas y área de playa Medano.
* Wi-Fi de alta velocidad en suite y áreas comunes.

[Reservar Opción 1 — European Plan](https://casadorada.com/pay/opt1)

---

**Vista Previa — Opción 2: All Inclusive Plan**  
*Junior Suite Ocean View*

* **Estancia:** {noches} Noches
* **Tarifa por noche:** {tarifa_ai_txt} *(Impuestos incluidos)*
* **Subtotal Estancia:** {subtotal_ai_txt}
* **Recorrido Virtual 360°:** 🌐 [Explorar Junior Suite en 360°](https://my.matterport.com/show/?m=ejemplo_jr_suite)

**Valores Agregados Incluidos:**
* Alimentos gourmet y bebidas premium ilimitadas.
* Servicio a la habitación 24 horas.
* Acceso al Kids Club y servicio de meseros en albercas y playa.

[Reservar Opción 2 — All Inclusive](https://casadorada.com/pay/opt2)

---

**Servicios Adicionales & Políticas:**
* **Traslado:** Roundtrip Airport Transportation — {traslado_txt}
* **Depósito:** 1 noche de depósito requerida al momento de reservar.
* **Cancelación:** Cancelación gratuita hasta 7 días antes de la llegada.
""")

# -----------------------------------------------------------------------------
# ENVÍO DE CORREO
# -----------------------------------------------------------------------------
st.markdown("---")
email_huesped = st.text_input("Correo del Huésped", "huesped@email.com")

if st.button("🚀 Enviar Directo al Huésped", type="primary"):
  if not remitente_email or not remitente_password:
    st.error(
        "⚠️ Falta configurar el correo o la contraseña del agente seleccionado."
    )
  else:
    cuerpo_html = f"""
        <h2>Casa Dorada Los Cabos Resort & Spa</h2>
        <p>A continuación le presentamos la cotización personalizada:</p>
        
        <h3>Opción 1: European Plan</h3>
        <p>Tarifa por noche: {tarifa_ep_txt}<br>Subtotal Estancia: {subtotal_ep_txt}</p>
        
        <h3>Opción 2: All Inclusive Plan</h3>
        <p>Tarifa por noche: {tarifa_ai_txt}<br>Subtotal Estancia: {subtotal_ai_txt}</p>
        
        <p><strong>Traslado:</strong> {traslado_txt}</p>
        <p>Atentamente,<br>{remitente_nombre}</p>
        """

    exito, res = enviar_correo_directo(
        email_destino=email_huesped,
        asunto="Cotización Especial | Casa Dorada Los Cabos",
        cuerpo_html=cuerpo_html,
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        remitente=remitente_email,
        password=remitente_password,
        nombre_remitente=remitente_nombre,
    )
    if exito:
      st.success(
          f"¡Cotización enviada a **{email_huesped}** desde **{remitente_nombre}**!"
      )
    else:
      st.error(f"Error al enviar: {res}")

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st

st.set_page_config(page_title="Cotizador Casa Dorada", layout="wide")

# -----------------------------------------------------------------------------
# 1. BARRA LATERAL: AGENTES Y SELECCIÓN DE MONEDA
# -----------------------------------------------------------------------------
st.sidebar.header("👤 Agente de Ventas")

# Carga de agentes desde secrets.toml
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
  st.sidebar.warning("⚠️ Sin agentes en secrets.toml")
  remitente_nombre = st.sidebar.text_input("Tu Nombre", "Ejecutivo de Ventas")
  remitente_email = st.sidebar.text_input(
      "Tu Correo", "ventas@casadorada.com"
  )
  remitente_password = st.sidebar.text_input(
      "Contraseña de Aplicación", type="password"
  )

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuración de Moneda")

moneda = st.sidebar.radio("Selecciona Moneda:", ["USD", "MXN"], index=0)
tipo_cambio = st.sidebar.number_input(
    "Tipo de Cambio (USD a MXN):", min_value=1.0, value=20.0, step=0.1
)

# -----------------------------------------------------------------------------
# 2. CÁLCULO Y FORMATEO DINÁMICO DE PRECIOS
# -----------------------------------------------------------------------------
# Precios base en USD
tarifa_ep_usd = 320.00
total_ep_usd = 960.00

tarifa_ai_usd = 480.00
total_ai_usd = 1440.00

traslado_usd = 150.00


# Función para cambiar los precios en pantalla según la moneda
def formatear(monto_usd):
  if moneda == "MXN":
    return f"${monto_usd * tipo_cambio:,.2f} MXN"
  return f"${monto_usd:,.2f} USD"


# Strings formateados para la vista previa
p_tarifa_ep = formatear(tarifa_ep_usd)
p_total_ep = formatear(total_ep_usd)

p_tarifa_ai = formatear(tarifa_ai_usd)
p_total_ai = formatear(total_ai_usd)

p_traslado = formatear(traslado_usd)

# -----------------------------------------------------------------------------
# 3. TU VISTA PREVIA ORIGINAL (TAL CUAL)
# -----------------------------------------------------------------------------
st.markdown(f"""
**Vista Previa — Opción 1: European Plan (Room Only)**
*Junior Suite Ocean View*

* **Estancia:** 3 Noches
* **Tarifa por noche:** {p_tarifa_ep} *(Impuestos incluidos)*
* **Subtotal Estancia:** {p_total_ep}
* **Recorrido Virtual 360°:** 🌐 [Explorar Junior Suite en 360°](https://my.matterport.com/show/?m=ejemplo_jr_suite)

**Valores Agregados Incluidos:**
* Balcón privado con vista panorámica al mar.
* Acceso ilimitado a albercas y área de playa Medano.
* Wi-Fi de alta velocidad en suite y áreas comunes.

[Reservar Opción 1 — European Plan](https://casadorada.com/pay/opt1)

---

**Vista Previa — Opción 2: All Inclusive Plan**
*Junior Suite Ocean View*

* **Estancia:** 3 Noches
* **Tarifa por noche:** {p_tarifa_ai} *(Impuestos incluidos)*
* **Subtotal Estancia:** {p_total_ai}
* **Recorrido Virtual 360°:** 🌐 [Explorar Junior Suite en 360°](https://my.matterport.com/show/?m=ejemplo_jr_suite)

**Valores Agregados Incluidos:**
* Alimentos gourmet y bebidas premium ilimitadas.
* Servicio a la habitación 24 horas.
* Acceso al Kids Club y servicio de meseros en albercas y playa.

[Reservar Opción 2 — All Inclusive](https://casadorada.com/pay/opt2)

---

**Servicios Adicionales & Políticas:**
* **Traslado:** Roundtrip Airport Transportation — {p_traslado}
* **Depósito:** 1 noche de depósito requerida al momento de reservar.
* **Cancelación:** Cancelación gratuita hasta 7 días antes de la llegada.
""")

# -----------------------------------------------------------------------------
# 4. ENVÍO DE CORREO SMTP
# -----------------------------------------------------------------------------
st.markdown("---")
email_huesped = st.text_input("Correo del Huésped", "huesped@email.com")

if st.button("🚀 Enviar Directo al Huésped", type="primary"):
  if not remitente_email or not remitente_password:
    st.error("⚠️ Configura el correo y contraseña del agente en el menú lateral.")
  else:
    cuerpo_html = f"""
        <h2>Casa Dorada Los Cabos Resort & Spa</h2>
        <p>Vista Previa de Cotización:</p>
        <p><strong>Opción 1 European Plan:</strong> Tarifa por noche: {p_tarifa_ep} | Total: {p_total_ep}</p>
        <p><strong>Opción 2 All Inclusive:</strong> Tarifa por noche: {p_tarifa_ai} | Total: {p_total_ai}</p>
        <p><strong>Traslado:</strong> {p_traslado}</p>
        <p>Atentamente,<br>{remitente_nombre}</p>
        """
    try:
      msg = MIMEMultipart("alternative")
      msg["Subject"] = "Cotización Especial | Casa Dorada Los Cabos"
      msg["From"] = f"{remitente_nombre} <{remitente_email}>"
      msg["To"] = email_huesped
      msg.attach(MIMEText(cuerpo_html, "html"))

      with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(remitente_email, remitente_password)
        server.sendmail(remitente_email, email_huesped, msg.as_string())

      st.success(
          f"¡Cotización enviada a **{email_huesped}** desde **{remitente_email}**!"
      )
    except Exception as e:
      st.error(f"Error al enviar: {e}")

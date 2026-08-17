from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import smtplib
import time
import streamlit as st

st.set_page_config(
    page_title="Cotizador Casa Dorada", layout="wide", initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. BARRA LATERAL: AGENTES Y CONFIGURACIÓN DE MONEDA
# -----------------------------------------------------------------------------
st.sidebar.header("👤 Agente de Ventas")

agentes_dict = st.secrets.get("agentes", {})

if agentes_dict:
  lista_agentes = [datos["nombre"] for datos in agentes_dict.values()]
  agente_seleccionado = st.sidebar.selectbox(
      "¿Quién prepara la cotización?", lista_agentes
  )

  for clave, datos in agentes_dict.items():
    if datos["nombre"] == agente_seleccionado:
      remitente_nombre = datos["nombre"]
      remitente_email = datos["email"]
      remitente_pass = datos["password"]  # Contraseña de aplicación
      break
else:
  st.sidebar.warning("⚠️ Sin agentes configurados en secrets.toml")
  remitente_nombre = "Ejecutivo de Ventas"
  remitente_email = "ventas@casadorada.com"
  remitente_pass = ""

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuración de Moneda")

moneda = st.sidebar.radio("Selecciona Moneda:", ["USD", "MXN"], index=0)
tipo_cambio = st.sidebar.number_input(
    "Tipo de Cambio (USD a MXN):", min_value=1.0, value=20.0, step=0.1
)

# -----------------------------------------------------------------------------
# 2. ENTRADA MANUAL DE DATOS (COLUMNA IZQUIERDA)
# -----------------------------------------------------------------------------
col_input, col_preview = st.columns([1, 1], gap="large")

with col_input:
  st.header("📝 Datos de la Cotización")

  nombre_huesped = st.text_input("Nombre del Huésped", "John Doe")
  email_huesped = st.text_input("Correo del Huésped", "huesped@email.com")

  noches = st.number_input("Número de Noches", min_value=1, value=3, step=1)

  st.subheader("Tarifas (en USD)")
  tarifa_ep_usd = st.number_input(
      "Tarifa por noche - European Plan (USD)",
      min_value=0.0,
      value=320.00,
      step=10.0,
  )
  tarifa_ai_usd = st.number_input(
      "Tarifa por noche - All Inclusive (USD)",
      min_value=0.0,
      value=480.00,
      step=10.0,
  )
  traslado_usd = st.number_input(
      "Traslado Roundtrip Aeropuerto (USD)",
      min_value=0.0,
      value=150.00,
      step=10.0,
  )

  # Carga de archivos adjuntos
  st.subheader("📎 Archivos Adjuntos")
  archivos_adjuntos = st.file_uploader(
      "Adjuntar folletos, PDF o imágenes (opcional):",
      accept_multiple_files=True,
  )

  # CÁLCULO DE TOTALES
  total_ep_usd = tarifa_ep_usd * noches
  total_ai_usd = tarifa_ai_usd * noches


  def formatear(monto_usd):
    if moneda == "MXN":
      return f"${monto_usd * tipo_cambio:,.2f} MXN"
    return f"${monto_usd:,.2f} USD"


  p_tarifa_ep = formatear(tarifa_ep_usd)
  p_total_ep = formatear(total_ep_usd)
  p_tarifa_ai = formatear(tarifa_ai_usd)
  p_total_ai = formatear(total_ai_usd)
  p_traslado = formatear(traslado_usd)

  # PLANTILLA HTML DISEÑO AZUL Y DORADO
  cuerpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Georgia', 'Times New Roman', serif; background-color: #f4f4f6; color: #1a1a1a; margin: 0; padding: 20px; }}
            .card {{ max-width: 650px; margin: 0 auto; background: #ffffff; border: 1px solid #dcdcdc; border-radius: 4px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .header {{ background-color: #0b2545; padding: 30px 20px; text-align: center; border-bottom: 3px solid #c5a059; }}
            .header img {{ max-width: 180px; height: auto; }}
            .content {{ padding: 30px; line-height: 1.7; }}
            .greeting {{ font-size: 18px; color: #0b2545; margin-bottom: 20px; font-weight: bold; }}
            .option-box {{ border: 1px solid #e2e8f0; border-top: 3px solid #c5a059; background-color: #fafafa; padding: 20px; margin-bottom: 25px; border-radius: 2px; }}
            .option-title {{ color: #0b2545; font-size: 18px; margin-top: 0; margin-bottom: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }}
            .price-tag {{ color: #c5a059; font-size: 16px; font-weight: bold; }}
            .total-tag {{ font-size: 18px; color: #0b2545; font-weight: bold; background: #eef2f7; padding: 6px 12px; display: inline-block; margin-top: 10px; border-radius: 3px; }}
            .details-list {{ list-style-type: none; padding-left: 0; margin: 10px 0; font-size: 14px; color: #4a5568; }}
            .details-list li {{ margin-bottom: 6px; padding-left: 15px; position: relative; }}
            .details-list li::before {{ content: "•"; color: #c5a059; position: absolute; left: 0; font-weight: bold; }}
            .btn {{ display: inline-block; background-color: #0b2545; color: #ffffff !important; text-decoration: none; padding: 10px 20px; border-radius: 3px; font-size: 13px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-top: 10px; border-bottom: 2px solid #c5a059; }}
            .footer {{ background-color: #0b2545; color: #a0aec0; text-align: center; padding: 20px; font-size: 12px; border-top: 1px solid #c5a059; }}
            .footer strong {{ color: #ffffff; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <img src="https://casadorada.com/wp-content/uploads/2021/04/logo-casa-dorada.png" alt="Casa Dorada Los Cabos Resort & Spa">
            </div>
            <div class="content">
                <div class="greeting">Estimado/a {nombre_huesped},</div>
                <p>Es un verdadero placer saludarle desde <strong>Casa Dorada Los Cabos Resort & Spa</strong>. A continuación, nos complace presentarle nuestra propuesta personalizada para su próxima estancia:</p>
                
                <div class="option-box">
                    <div class="option-title">Opción 1: European Plan (Room Only)</div>
                    <p style="margin: 5px 0;"><em>Junior Suite Ocean View</em></p>
                    <ul class="details-list">
                        <li><strong>Estancia:</strong> {noches} Noches</li>
                        <li><strong>Tarifa por noche:</strong> <span class="price-tag">{p_tarifa_ep}</span> (Impuestos incluidos)</li>
                    </ul>
                    <div class="total-tag">Subtotal Estancia: {p_total_ep}</div>
                    <br><br>
                    <strong>Beneficios Incluidos:</strong>
                    <ul class="details-list">
                        <li>Balcón privado con vista panorámica al mar.</li>
                        <li>Acceso ilimitado a albercas y área de playa Médano.</li>
                        <li>Wi-Fi de alta velocidad en suite y áreas comunes.</li>
                    </ul>
                    <a href="https://casadorada.com/pay/opt1" class="btn">Reservar Opción 1</a>
                </div>

                <div class="option-box">
                    <div class="option-title">Opción 2: All Inclusive Plan</div>
                    <p style="margin: 5px 0;"><em>Junior Suite Ocean View</em></p>
                    <ul class="details-list">
                        <li><strong>Estancia:</strong> {noches} Noches</li>
                        <li><strong>Tarifa por noche:</strong> <span class="price-tag">{p_tarifa_ai}</span> (Impuestos incluidos)</li>
                    </ul>
                    <div class="total-tag">Subtotal Estancia: {p_total_ai}</div>
                    <br><br>
                    <strong>Beneficios Incluidos:</strong>
                    <ul class="details-list">
                        <li>Alimentos gourmet y bebidas premium ilimitadas.</li>
                        <li>Servicio a la habitación 24 horas.</li>
                        <li>Acceso al Kids Club y servicio de meseros en alberca y playa.</li>
                    </ul>
                    <a href="https://casadorada.com/pay/opt2" class="btn">Reservar Opción 2</a>
                </div>

                <div style="border-top: 1px solid #e2e8f0; padding-top: 15px; margin-top: 20px;">
                    <p style="margin: 5px 0; font-size: 14px;"><strong>Servicios Adicionales:</strong> Roundtrip Airport Transportation — <span class="price-tag">{p_traslado}</span></p>
                    <p style="margin: 5px 0; font-size: 13px; color: #718096;"><strong>Políticas:</strong> Depósito de 1 noche requerido al reservar. Cancelación gratuita hasta 7 días antes de la llegada.</p>
                </div>
            </div>
            <div class="footer">
                <strong>{remitente_nombre}</strong><br>
                Casa Dorada Los Cabos Resort & Spa<br>
                <span style="color: #c5a059;">Medano Beach, Cabo San Lucas, BCS</span>
            </div>
        </div>
    </body>
    </html>
    """

  st.markdown("---")


  # FUNCIÓN AUXILIAR PARA ARMAR EL MENSAJE MIME
  def crear_mensaje_mime():
    msg = MIMEMultipart()
    msg["From"] = f"{remitente_nombre} <{remitente_email}>"
    msg["To"] = email_huesped
    msg["Subject"] = (
        f"Cotización Especial | Casa Dorada Los Cabos - {nombre_huesped}"
    )
    msg.attach(MIMEText(cuerpo_html, "html"))

    if archivos_adjuntos:
      for archivo in archivos_adjuntos:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(archivo.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {archivo.name}",
        )
        msg.attach(part)
        archivo.seek(0)  # Resetear el puntero para reuso
    return msg


  col_btn1, col_btn2 = st.columns(2)

  with col_btn1:
    btn_enviar = st.button("🚀 Enviar Ahora", use_container_width=True)

  with col_btn2:
    btn_borrador = st.button(
        "📝 Guardar en Borradores", type="primary", use_container_width=True
    )

  # LÓGICA DE ENVÍO / GUARDADO
  if btn_enviar or btn_borrador:
    if not remitente_pass:
      st.error(
          "⚠️ Falta la contraseña de aplicación del agente en secrets.toml"
      )
    else:
      msg_mime = crear_mensaje_mime()

      if btn_enviar:
        try:
          with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remitente_email, remitente_pass)
            server.send_message(msg_mime)
          st.success(f"¡Correo enviado exitosamente a **{email_huesped}**!")
        except Exception as e:
          st.error(f"Error al enviar por SMTP: {e}")

      elif btn_borrador:
        try:
          # Conexión IMAP para subir directamente a Borradores (Drafts)
          imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
          imap.login(remitente_email, remitente_pass)

          # Para cuentas en español la carpeta suele ser '[Gmail]/Borradores', en inglés '[Gmail]/Drafts'
          # Intentamos seleccionar la carpeta de borradores estándar
          res, _ = imap.select('"[Gmail]/Borradores"')
          if res != "OK":
            res, _ = imap.select('"[Gmail]/Drafts"')

          # Inserción del correo en formato de cadena bytes con flag \Draft
          raw_msg = msg_mime.as_bytes()
          imap.append(
              '"[Gmail]/Borradores"' if res == "OK" else '"[Gmail]/Drafts"',
              "\\Draft",
              imaplib.Time2Internaldate(time.time()),
              raw_msg,
          )
          imap.logout()

          st.success(
              f"¡Borrador guardado correctamente en la cuenta de"
              f" **{remitente_email}**!"
          )
        except Exception as e:
          st.error(f"Error al guardar en Borradores por IMAP: {e}")

# -----------------------------------------------------------------------------
# 3. VISTA PREVIA
# -----------------------------------------------------------------------------
with col_preview:
  st.header("👁️ Vista Previa")
  st.components.v1.html(cuerpo_html, height=800, scrolling=True)

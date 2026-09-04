import streamlit as st
import smtplib
import imaplib
import time
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Cotizador | Casa Dorada Los Cabos",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# COLORES CASA DORADA
# ============================================================

AZUL = "#0A2342"
AZUL_OSCURO = "#06182E"
DORADO = "#C9A227"
DORADO_CLARO = "#D8B85A"
FONDO = "#F4F6F8"
BLANCO = "#FFFFFF"
TEXTO = "#243447"
GRIS = "#6B7280"


# ============================================================
# CSS PERSONALIZADO
# ============================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background-color: {FONDO};
    }}

    /* -----------------------------
       HEADER PRINCIPAL
    ----------------------------- */

    .main-header {{
        background: linear-gradient(135deg, {AZUL_OSCURO}, {AZUL});
        padding: 28px 35px;
        border-radius: 14px;
        border-bottom: 5px solid {DORADO};
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 5px 18px rgba(0,0,0,0.12);
    }}

    .main-header h1 {{
        color: white !important;
        margin: 0;
        font-size: 32px;
        font-weight: 700;
    }}

    .main-header p {{
        color: {DORADO_CLARO};
        margin: 5px 0 0 0;
        font-size: 14px;
        letter-spacing: 1px;
    }}

    /* -----------------------------
       SIDEBAR
    ----------------------------- */

    [data-testid="stSidebar"] {{
        background-color: {AZUL};
    }}

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label {{
        color: white !important;
    }}

    /* -----------------------------
       TITULOS
    ----------------------------- */

    h1, h2, h3 {{
        color: {AZUL};
    }}

    /* -----------------------------
       TARJETAS
    ----------------------------- */

    .quote-card {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        border-top: 4px solid {DORADO};
        box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }}

    /* -----------------------------
       METRICAS
    ----------------------------- */

    [data-testid="stMetric"] {{
        background-color: white;
        padding: 16px;
        border-radius: 10px;
        border-left: 4px solid {DORADO};
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}

    /* -----------------------------
       BOTONES
    ----------------------------- */

    .stButton > button {{
        background-color: {AZUL};
        color: white;
        border: 1px solid {DORADO};
        border-radius: 8px;
        font-weight: 600;
        min-height: 46px;
    }}

    .stButton > button:hover {{
        background-color: {DORADO};
        color: {AZUL};
        border-color: {DORADO};
    }}

    /* -----------------------------
       INPUTS
    ----------------------------- */

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input {{
        border-radius: 8px;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES
# ============================================================

def formatear_moneda(monto_usd, moneda, tipo_cambio):
    """
    Convierte y formatea un monto USD a la moneda seleccionada.
    """

    if moneda == "MXN":
        monto = monto_usd * tipo_cambio
        return f"${monto:,.2f} MXN"

    return f"${monto_usd:,.2f} USD"


def calcular_total(tarifa, noches):
    return tarifa * noches


def obtener_texto_politica(tipo_politica):
    """
    Devuelve el texto de política seleccionado.
    """

    if tipo_politica == "Flexible":

        return """
        Reservation is guaranteed with first night deposit.
        The remaining balance must be paid according to the
        terms and conditions of the reservation.
        """

    elif tipo_politica == "No reembolsable":

        return """
        This reservation is non-refundable and cannot be cancelled
        or modified without applicable penalties.
        """

    else:

        return """
        Reservation terms and cancellation policies will be provided
        according to the selected rate and booking conditions.
        """


def obtener_beneficios(plan):
    """
    Beneficios dependiendo del plan.
    """

    if plan == "European Plan":

        return [
            "Accommodation in the selected suite.",
            "Access to the swimming pools and resort facilities.",
            "Wi-Fi access in the suite and common areas.",
            "Access to Médano Beach."
        ]

    return [
        "Accommodation in the selected suite.",
        "Unlimited access to participating food and beverage outlets.",
        "Selected domestic beverages.",
        "Access to the swimming pools and resort facilities.",
        "Wi-Fi access in the suite and common areas."
    ]


def crear_mensaje_mime(
    remitente_nombre,
    remitente_email,
    email_huesped,
    nombre_huesped,
    cuerpo_html,
    archivos_adjuntos,
):
    """
    Crea el mensaje MIME con HTML y archivos adjuntos.
    """

    msg = MIMEMultipart()

    msg["From"] = f"{remitente_nombre} <{remitente_email}>"
    msg["To"] = email_huesped
    msg["Subject"] = (
        f"Personalized Stay Proposal | Casa Dorada Los Cabos | "
        f"{nombre_huesped}"
    )

    msg.attach(MIMEText(cuerpo_html, "html"))

    if archivos_adjuntos:

        for archivo in archivos_adjuntos:

            part = MIMEBase(
                "application",
                "octet-stream"
            )

            part.set_payload(
                archivo.getvalue()
            )

            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{archivo.name}"'
            )

            msg.attach(part)

    return msg


# ============================================================
# HEADER PRINCIPAL
# ============================================================

st.markdown(
    """
    <div class="main-header">
        <h1>CASA DORADA</h1>
        <p>LOS CABOS RESORT & SPA · COTIZADOR DE RESERVACIONES</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## 👤 Agente de Ventas")


agentes_dict = st.secrets.get(
    "agentes",
    {}
)


if agentes_dict:

    lista_agentes = [
        datos["nombre"]
        for datos in agentes_dict.values()
    ]

    agente_seleccionado = st.sidebar.selectbox(
        "Selecciona el agente",
        lista_agentes
    )

    remitente_nombre = "Reservations"
    remitente_email = ""
    remitente_pass = ""

    for clave, datos in agentes_dict.items():

        if datos["nombre"] == agente_seleccionado:

            remitente_nombre = datos["nombre"]

            remitente_email = datos["email"]

            remitente_pass = datos["password"]

            break

else:

    st.sidebar.warning(
        "No hay agentes configurados en secrets.toml"
    )

    remitente_nombre = "Reservations"
    remitente_email = ""
    remitente_pass = ""


st.sidebar.markdown("---")


# ============================================================
# MONEDA
# ============================================================

st.sidebar.markdown("## 💱 Moneda")


moneda = st.sidebar.radio(
    "Mostrar cotización en:",
    ["USD", "MXN"]
)


tipo_cambio = st.sidebar.number_input(
    "Tipo de cambio USD → MXN",
    min_value=1.0,
    value=20.00,
    step=0.10
)


st.sidebar.markdown("---")


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.sidebar.markdown("## ⚙️ Configuración")


tipo_politica = st.sidebar.selectbox(
    "Política de reserva",
    [
        "Flexible",
        "No reembolsable",
        "Política personalizada"
    ]
)


incluir_transporte = st.sidebar.checkbox(
    "Incluir transporte aeropuerto"
)


# ============================================================
# COLUMNAS PRINCIPALES
# ============================================================

col_input, col_preview = st.columns(
    [1, 1.15],
    gap="large"
)


# ============================================================
# FORMULARIO
# ============================================================

with col_input:

    st.header("📝 Información de la Cotización")


    # --------------------------------------------------------
    # DATOS DEL HUESPED
    # --------------------------------------------------------

    st.subheader("👤 Datos del Huésped")

    nombre_huesped = st.text_input(
        "Nombre completo",
        placeholder="Ej. John Smith"
    )

    email_huesped = st.text_input(
        "Correo electrónico",
        placeholder="guest@email.com"
    )


    # --------------------------------------------------------
    # FECHAS
    # --------------------------------------------------------

    st.subheader("📅 Fechas de Estancia")

    fecha_col1, fecha_col2 = st.columns(2)


    with fecha_col1:

        check_in = st.date_input(
            "Check In",
            value=date.today(),
            min_value=date.today()
        )


    with fecha_col2:

        check_out = st.date_input(
            "Check Out",
            value=date.today(),
            min_value=check_in
        )


    noches = (
        check_out - check_in
    ).days


    if noches <= 0:

        st.warning(
            "La fecha de Check Out debe ser posterior al Check In."
        )

        noches = 1


    # --------------------------------------------------------
    # HUÉSPEDES
    # --------------------------------------------------------

    st.subheader("👥 Huéspedes")

    guest_col1, guest_col2 = st.columns(2)


    with guest_col1:

        adultos = st.number_input(
            "Adultos",
            min_value=1,
            value=2,
            step=1
        )


    with guest_col2:

        ninos = st.number_input(
            "Niños",
            min_value=0,
            value=0,
            step=1
        )


    # --------------------------------------------------------
    # HABITACIÓN
    # --------------------------------------------------------

    st.subheader("🛏️ Suite")

    tipos_suite = [
        "Junior Suite",
        "One Bedroom Suite",
        "One Bedroom Plus with Jacuzzi",
        "Executive Suite",
        "Two Bedroom Suite",
        "One Bedroom Penthouse"
    ]


    # ========================================================
    # OPCIÓN 1
    # ========================================================

    st.markdown("---")

    st.subheader("OPTION 1")

    activar_opcion_1 = True


    opcion1_col1, opcion1_col2 = st.columns(2)


    with opcion1_col1:

        suite_1 = st.selectbox(
            "Tipo de Suite",
            tipos_suite,
            key="suite_1"
        )


    with opcion1_col2:

        plan_1 = st.selectbox(
            "Plan",
            [
                "European Plan",
                "All Inclusive"
            ],
            key="plan_1"
        )


    tarifa_1 = st.number_input(
        "Tarifa por noche USD",
        min_value=0.0,
        value=320.0,
        step=10.0,
        key="tarifa_1"
    )


    # ========================================================
    # OPCIÓN 2
    # ========================================================

    st.markdown("---")

    activar_opcion_2 = st.checkbox(
        "Agregar OPTION 2"
    )


    suite_2 = None
    plan_2 = None
    tarifa_2 = 0.0


    if activar_opcion_2:

        opcion2_col1, opcion2_col2 = st.columns(2)


        with opcion2_col1:

            suite_2 = st.selectbox(
                "Tipo de Suite",
                tipos_suite,
                key="suite_2"
            )


        with opcion2_col2:

            plan_2 = st.selectbox(
                "Plan",
                [
                    "European Plan",
                    "All Inclusive"
                ],
                key="plan_2"
            )


        tarifa_2 = st.number_input(
            "Tarifa por noche USD",
            min_value=0.0,
            value=480.0,
            step=10.0,
            key="tarifa_2"
        )


    # ========================================================
    # OPCIÓN 3
    # ========================================================

    st.markdown("---")

    activar_opcion_3 = st.checkbox(
        "Agregar OPTION 3"
    )


    suite_3 = None
    plan_3 = None
    tarifa_3 = 0.0


    if activar_opcion_3:

        opcion3_col1, opcion3_col2 = st.columns(2)


        with opcion3_col1:

            suite_3 = st.selectbox(
                "Tipo de Suite",
                tipos_suite,
                key="suite_3"
            )


        with opcion3_col2:

            plan_3 = st.selectbox(
                "Plan",
                [
                    "European Plan",
                    "All Inclusive"
                ],
                key="plan_3"
            )


        tarifa_3 = st.number_input(
            "Tarifa por noche USD",
            min_value=0.0,
            value=650.0,
            step=10.0,
            key="tarifa_3"
        )


    # --------------------------------------------------------
    # TRANSPORTE
    # --------------------------------------------------------

    transporte_usd = 0.0


    if incluir_transporte:

        st.markdown("---")

        st.subheader("🚗 Transportation")

        transporte_usd = st.number_input(
            "Roundtrip Airport Transportation USD",
            min_value=0.0,
            value=259.0,
            step=10.0
        )


    # --------------------------------------------------------
    # ARCHIVOS
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader("📎 Archivos Adjuntos")

    archivos_adjuntos = st.file_uploader(
        "Adjuntar PDF, imágenes o documentos",
        accept_multiple_files=True
    )


# ============================================================
# CÁLCULOS
# ============================================================

total_1_usd = calcular_total(
    tarifa_1,
    noches
)


total_2_usd = calcular_total(
    tarifa_2,
    noches
) if activar_opcion_2 else 0


total_3_usd = calcular_total(
    tarifa_3,
    noches
) if activar_opcion_3 else 0


# ============================================================
# FORMATEAR FECHAS
# ============================================================

check_in_texto = check_in.strftime(
    "%B %d, %Y"
)

check_out_texto = check_out.strftime(
    "%B %d, %Y"
)


# ============================================================
# CREAR HTML DE OPCIONES
# ============================================================

def crear_opcion_html(
    numero,
    suite,
    plan,
    tarifa_usd,
    total_usd
):

    beneficios = obtener_beneficios(
        plan
    )


    beneficios_html = ""

    for beneficio in beneficios:

        beneficios_html += f"""
        <li>{beneficio}</li>
        """


    return f"""
    <div class="option-box">

        <div class="option-number">
            OPTION {numero}
        </div>

        <div class="option-title">
            {suite}
        </div>

        <div class="plan">
            {plan}
        </div>

        <div class="price-row">

            <div>
                <span class="label">
                    Rate per night
                </span>

                <strong>
                    {formatear_moneda(
                        tarifa_usd,
                        moneda,
                        tipo_cambio
                    )}
                </strong>
            </div>

            <div>
                <span class="label">
                    Stay
                </span>

                <strong>
                    {noches} nights
                </strong>
            </div>

        </div>

        <div class="total-box">

            TOTAL STAY

            <strong>
                {formatear_moneda(
                    total_usd,
                    moneda,
                    tipo_cambio
                )}
            </strong>

        </div>

        <div class="benefits">

            <strong>
                Included:
            </strong>

            <ul>
                {beneficios_html}
            </ul>

        </div>

    </div>
    """


# ============================================================
# OPCIONES HTML
# ============================================================

opciones_html = ""


opciones_html += crear_opcion_html(
    1,
    suite_1,
    plan_1,
    tarifa_1,
    total_1_usd
)


if activar_opcion_2:

    opciones_html += crear_opcion_html(
        2,
        suite_2,
        plan_2,
        tarifa_2,
        total_2_usd
    )


if activar_opcion_3:

    opciones_html += crear_opcion_html(
        3,
        suite_3,
        plan_3,
        tarifa_3,
        total_3_usd
    )


# ============================================================
# TRANSPORTE HTML
# ============================================================

transporte_html = ""


if incluir_transporte:

    transporte_html = f"""

    <div class="transport-box">

        <h3>
            Airport Transportation
        </h3>

        <p>
            Roundtrip Airport Transportation
        </p>

        <strong>
            {formatear_moneda(
                transporte_usd,
                moneda,
                tipo_cambio
            )}
        </strong>

    </div>

    """


# ============================================================
# CUERPO HTML DEL EMAIL
# ============================================================

cuerpo_html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<style>

body {{
    margin: 0;
    padding: 0;
    background-color: #F4F6F8;
    font-family: Arial, Helvetica, sans-serif;
    color: #243447;
}}

.wrapper {{
    width: 100%;
    background-color: #F4F6F8;
    padding: 25px 0;
}}

.container {{
    max-width: 650px;
    margin: auto;
    background-color: #FFFFFF;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}}

.header {{
    background: #0A2342;
    text-align: center;
    padding: 28px 20px;
    border-bottom: 5px solid #C9A227;
}}

.logo {{
    max-width: 190px;
    height: auto;
}}

.content {{
    padding: 35px 30px;
}}

.greeting {{
    color: #0A2342;
    font-size: 20px;
    font-weight: bold;
}}

.intro {{
    font-size: 15px;
    line-height: 1.7;
    color: #4B5563;
}}

.stay-box {{
    background: #F7F8FA;
    border-left: 4px solid #C9A227;
    padding: 20px;
    margin: 25px 0;
}}

.stay-title {{
    color: #0A2342;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 15px;
}}

.stay-grid {{
    width: 100%;
}}

.stay-grid td {{
    padding: 7px 0;
    font-size: 14px;
}}

.label {{
    display: block;
    font-size: 11px;
    text-transform: uppercase;
    color: #6B7280;
    letter-spacing: 1px;
    margin-bottom: 4px;
}}

.option-box {{
    border: 1px solid #E5E7EB;
    border-top: 4px solid #C9A227;
    margin: 25px 0;
    padding: 24px;
    border-radius: 6px;
}}

.option-number {{
    color: #C9A227;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
}}

.option-title {{
    color: #0A2342;
    font-size: 22px;
    font-weight: bold;
    margin-top: 8px;
}}

.plan {{
    color: #6B7280;
    margin: 5px 0 20px 0;
    font-size: 14px;
}}

.price-row {{
    display: flex;
    justify-content: space-between;
    background: #F7F8FA;
    padding: 15px;
}}

.price-row strong {{
    color: #0A2342;
    font-size: 15px;
}}

.total-box {{
    background: #0A2342;
    color: white;
    padding: 15px;
    margin-top: 15px;
    text-align: center;
    font-size: 12px;
    letter-spacing: 1px;
}}

.total-box strong {{
    display: block;
    color: #D8B85A;
    font-size: 24px;
    margin-top: 5px;
}}

.benefits {{
    margin-top: 20px;
    font-size: 14px;
}}

.benefits ul {{
    padding-left: 18px;
    color: #4B5563;
}}

.benefits li {{
    margin-bottom: 7px;
}}

.transport-box {{
    background: #F7F8FA;
    border: 1px solid #E5E7EB;
    padding: 20px;
    margin-top: 25px;
}}

.transport-box h3 {{
    color: #0A2342;
    margin-top: 0;
}}

.transport-box strong {{
    color: #C9A227;
    font-size: 20px;
}}

.policy {{
    margin-top: 30px;
    border-top: 1px solid #E5E7EB;
    padding-top: 20px;
    font-size: 12px;
    line-height: 1.6;
    color: #6B7280;
}}

.footer {{
    background: #0A2342;
    color: #FFFFFF;
    text-align: center;
    padding: 25px;
    font-size: 13px;
}}

.footer strong {{
    color: #D8B85A;
    font-size: 15px;
}}

.footer a {{
    color: #D8B85A;
    text-decoration: none;
}}

@media only screen and (max-width: 600px) {{

    .content {{
        padding: 25px 20px;
    }}

    .price-row {{
        display: block;
    }}

    .price-row div {{
        margin-bottom: 12px;
    }}

}}

</style>

</head>


<body>

<div class="wrapper">

<div class="container">


<div class="header">

<img
class="logo"
src="https://casadorada.com/wp-content/uploads/2021/04/logo-casa-dorada.png"
alt="Casa Dorada Los Cabos Resort & Spa"
>

</div>


<div class="content">


<div class="greeting">

Dear {nombre_huesped if nombre_huesped else "Guest"},

</div>


<p class="intro">

Thank you for considering
<strong>Casa Dorada Los Cabos Resort & Spa</strong>
for your upcoming stay.

It is our pleasure to share the following personalized
accommodation proposal for your consideration.

</p>


<div class="stay-box">

<div class="stay-title">

YOUR STAY

</div>


<table class="stay-grid">

<tr>

<td>

<span class="label">

Check In

</span>

<strong>

{check_in_texto}

</strong>

</td>


<td>

<span class="label">

Check Out

</span>

<strong>

{check_out_texto}

</strong>

</td>

</tr>


<tr>

<td>

<span class="label">

Guests

</span>

<strong>

{adultos} Adults
{" / " + str(ninos) + " Children" if ninos > 0 else ""}

</strong>

</td>


<td>

<span class="label">

Length of Stay

</span>

<strong>

{noches} Nights

</strong>

</td>

</tr>

</table>

</div>


{opciones_html}


{transporte_html}


<div class="policy">

<strong>

Reservation Information

</strong>

<br><br>

{obtener_texto_politica(tipo_politica)}

</div>


<p class="intro">

Please let us know if you would like to proceed with any of
these options or if you would like us to explore additional
alternatives for your stay.

We will be delighted to assist you.

</p>


</div>


<div class="footer">

<strong>

{remitente_nombre}

</strong>

<br><br>

Casa Dorada Los Cabos Resort & Spa

<br>

Medano Beach · Cabo San Lucas · Baja California Sur · Mexico

<br><br>

<a href="https://casadorada.com">

www.casadorada.com

</a>

</div>


</div>

</div>

</body>

</html>
"""


# ============================================================
# VISTA PREVIA
# ============================================================

with col_preview:

    st.header("👁️ Vista Previa")


    metric_col1, metric_col2, metric_col3 = st.columns(3)


    with metric_col1:

        st.metric(
            "NOCHES",
            noches
        )


    with metric_col2:

        st.metric(
            "OPCIÓN 1",
            formatear_moneda(
                total_1_usd,
                moneda,
                tipo_cambio
            )
        )


    with metric_col3:

        opciones_activas = 1

        if activar_opcion_2:
            opciones_activas += 1

        if activar_opcion_3:
            opciones_activas += 1


        st.metric(
            "OPCIONES",
            opciones_activas
        )


    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )


    st.components.v1.html(
        cuerpo_html,
        height=900,
        scrolling=True
    )


# ============================================================
# BOTONES PRINCIPALES
# ============================================================

st.markdown("---")


btn_col1, btn_col2, btn_col3 = st.columns(
    [1, 1, 2]
)


with btn_col1:

    btn_enviar = st.button(
        "🚀 Enviar Cotización",
        use_container_width=True
    )


with btn_col2:

    btn_borrador = st.button(
        "📝 Guardar en Borradores",
        use_container_width=True
    )


# ============================================================
# VALIDACIONES
# ============================================================

def validar_datos():

    if not nombre_huesped.strip():

        st.error(
            "Por favor ingresa el nombre del huésped."
        )

        return False


    if not email_huesped.strip():

        st.error(
            "Por favor ingresa el correo electrónico del huésped."
        )

        return False


    if not remitente_email:

        st.error(
            "No hay correo configurado para el agente."
        )

        return False


    if not remitente_pass:

        st.error(
            "Falta la contraseña de aplicación en secrets.toml."
        )

        return False


    return True


# ============================================================
# ENVIAR CORREO
# ============================================================

if btn_enviar:

    if validar_datos():

        with st.spinner(
            "Enviando cotización..."
        ):

            try:

                msg_mime = crear_mensaje_mime(
                    remitente_nombre,
                    remitente_email,
                    email_huesped,
                    nombre_huesped,
                    cuerpo_html,
                    archivos_adjuntos
                )


                with smtplib.SMTP(
                    "smtp.gmail.com",
                    587
                ) as server:

                    server.starttls()

                    server.login(
                        remitente_email,
                        remitente_pass
                    )

                    server.send_message(
                        msg_mime
                    )


                st.success(
                    f"""
                    ¡Cotización enviada correctamente a
                    {email_huesped}!
                    """
                )


            except smtplib.SMTPAuthenticationError:

                st.error(
                    """
                    Error de autenticación.

                    Verifica el correo electrónico y la
                    contraseña de aplicación.
                    """
                )


            except Exception as e:

                st.error(
                    f"Error al enviar el correo: {e}"
                )


# ============================================================
# GUARDAR EN BORRADORES
# ============================================================

if btn_borrador:

    if validar_datos():

        with st.spinner(
            "Guardando en borradores..."
        ):

            try:

                msg_mime = crear_mensaje_mime(
                    remitente_nombre,
                    remitente_email,
                    email_huesped,
                    nombre_huesped,
                    cuerpo_html,
                    archivos_adjuntos
                )


                imap = imaplib.IMAP4_SSL(
                    "imap.gmail.com",
                    993
                )


                imap.login(
                    remitente_email,
                    remitente_pass
                )


                # Intentamos diferentes nombres de carpeta

                posibles_carpetas = [

                    '"[Gmail]/Drafts"',

                    '"[Gmail]/Borradores"',

                    "Drafts",

                    "Borradores"

                ]


                draft_folder = None


                for carpeta in posibles_carpetas:

                    resultado, _ = imap.select(
                        carpeta
                    )


                    if resultado == "OK":

                        draft_folder = carpeta

                        break


                if not draft_folder:

                    raise Exception(
                        "No se encontró la carpeta de borradores."
                    )


                raw_msg = msg_mime.as_bytes()


                resultado, _ = imap.append(

                    draft_folder,

                    "\\Draft",

                    imaplib.Time2Internaldate(
                        time.time()
                    ),

                    raw_msg

                )


                imap.logout()


                if resultado != "OK":

                    raise Exception(
                        "No se pudo guardar el mensaje."
                    )


                st.success(
                    f"""
                    ¡Borrador guardado correctamente en
                    {remitente_email}!
                    """
                )


            except imaplib.IMAP4.error as e:

                st.error(
                    f"Error de IMAP: {e}"
                )


            except Exception as e:

                st.error(
                    f"Error al guardar en borradores: {e}"
                )

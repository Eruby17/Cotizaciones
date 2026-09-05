import base64
from datetime import date
from email.message import EmailMessage

import streamlit as st

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Cotizador Casa Dorada",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GOOGLE OAUTH
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose"
]


# ============================================================
# COLORES CASA DORADA
# ============================================================

AZUL = "#071A2F"
AZUL_2 = "#0B2545"
AZUL_3 = "#102F52"

DORADO = "#C9A227"
DORADO_CLARO = "#E0C15A"

FONDO = "#050D18"
CARD = "#0B1726"
CARD_2 = "#101F32"

BLANCO = "#F5F7FA"
GRIS = "#AAB6C5"
GRIS_2 = "#6F7D8D"

VERDE = "#42C88A"
ROJO = "#E56B6F"


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background: {FONDO};
        color: {BLANCO};
    }}

    [data-testid="stHeader"] {{
        background: {FONDO};
    }}

    [data-testid="stSidebar"] {{
        background: {AZUL};
        border-right: 1px solid {AZUL_3};
    }}

    [data-testid="stSidebar"] * {{
        color: {BLANCO};
    }}

    h1, h2, h3, h4 {{
        color: {BLANCO} !important;
    }}

    p, label {{
        color: {GRIS};
    }}

    .main-title {{
        font-size: 32px;
        font-weight: 700;
        color: {BLANCO};
        margin-bottom: 4px;
    }}

    .subtitle {{
        color: {GRIS};
        font-size: 15px;
        margin-bottom: 25px;
    }}

    .top-card {{
        background: linear-gradient(135deg, {AZUL_2}, {CARD});
        border: 1px solid {AZUL_3};
        border-bottom: 3px solid {DORADO};
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 25px;
    }}

    .section-card {{
        background: {CARD};
        border: 1px solid {AZUL_3};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }}

    .gold-text {{
        color: {DORADO_CLARO};
    }}

    .connected {{
        background: rgba(66, 200, 138, 0.12);
        border: 1px solid {VERDE};
        color: {VERDE};
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
    }}

    .disconnected {{
        background: rgba(229, 107, 111, 0.10);
        border: 1px solid {ROJO};
        color: {ROJO};
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
    }}

    .metric-box {{
        background: {CARD_2};
        border: 1px solid {AZUL_3};
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }}

    .metric-label {{
        color: {GRIS};
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .metric-value {{
        color: {DORADO_CLARO};
        font-size: 22px;
        font-weight: 700;
        margin-top: 4px;
    }}

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input {{
        background: {CARD_2} !important;
        color: {BLANCO} !important;
        border: 1px solid {AZUL_3} !important;
        border-radius: 8px !important;
    }}

    .stSelectbox div[data-baseweb="select"] > div {{
        background: {CARD_2} !important;
        color: {BLANCO} !important;
        border-color: {AZUL_3} !important;
    }}

    .stTextArea textarea {{
        background: {CARD_2} !important;
        color: {BLANCO} !important;
        border: 1px solid {AZUL_3} !important;
    }}

    button[kind="primary"] {{
        background: {DORADO} !important;
        color: #000000 !important;
        border: none !important;
        font-weight: 700 !important;
    }}

    button[kind="secondary"] {{
        background: {AZUL_2} !important;
        color: {BLANCO} !important;
        border: 1px solid {DORADO} !important;
    }}

    .preview-container {{
        background: #ffffff;
        border-radius: 10px;
        padding: 5px;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES GOOGLE
# ============================================================

def get_google_client_config():
    """
    Obtiene las credenciales desde Streamlit Secrets.
    """

    return {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                st.secrets["google_oauth"]["redirect_uri"]
            ],
        }
    }


def create_oauth_flow():
    """
    Crea el flujo OAuth.
    """

    config = get_google_client_config()

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
    )

    return flow


def iniciar_google_login():
    """
    Genera la URL de autorización.

    IMPORTANTE:
    El flow se guarda en session_state para conservar
    el code_verifier de PKCE.
    """

    if "oauth_flow" not in st.session_state:

        flow = create_oauth_flow()

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        st.session_state["oauth_flow"] = flow
        st.session_state["oauth_state"] = state
        st.session_state["oauth_url"] = authorization_url


def procesar_callback_google():
    """
    Procesa el regreso de Google después del login.
    """

    code = st.query_params.get("code")

    if not code:
        return None

    flow = st.session_state.get("oauth_flow")

    if flow is None:
        st.error(
            "La sesión de Google expiró. "
            "Haz clic nuevamente en Iniciar sesión con Google."
        )

        return None

    estado_google = st.query_params.get("state")
    estado_guardado = st.session_state.get("oauth_state")

    if (
        estado_google
        and estado_guardado
        and estado_google != estado_guardado
    ):
        st.error(
            "No fue posible validar la sesión de Google."
        )

        return None

    try:

        flow.fetch_token(code=code)

        credentials = flow.credentials

        st.session_state["google_credentials"] = credentials

        st.session_state.pop("oauth_flow", None)
        st.session_state.pop("oauth_state", None)
        st.session_state.pop("oauth_url", None)

        st.query_params.clear()

        return credentials

    except Exception as e:

        st.error(
            f"No fue posible completar la conexión con Google: {e}"
        )

        return None


def obtener_credentials():
    """
    Recupera las credenciales actuales.
    """

    credentials = st.session_state.get(
        "google_credentials"
    )

    if credentials is None:
        return None

    if isinstance(credentials, dict):

        credentials = Credentials.from_authorized_user_info(
            credentials,
            SCOPES,
        )

        st.session_state["google_credentials"] = credentials

    if credentials.expired and credentials.refresh_token:

        try:

            credentials.refresh(Request())

            st.session_state["google_credentials"] = credentials

        except Exception:
            st.session_state.pop(
                "google_credentials",
                None
            )

            return None

    return credentials


def obtener_gmail_service():
    """
    Construye el servicio Gmail API.
    """

    credentials = obtener_credentials()

    if not credentials:
        return None

    try:

        service = build(
            "gmail",
            "v1",
            credentials=credentials,
        )

        return service

    except Exception as e:

        st.error(
            f"No fue posible conectar con Gmail: {e}"
        )

        return None


def obtener_email_usuario():
    """
    Obtiene el email de la cuenta autenticada.
    """

    service = obtener_gmail_service()

    if not service:
        return None

    try:

        profile = (
            service.users()
            .getProfile(userId="me")
            .execute()
        )

        return profile.get("emailAddress")

    except Exception as e:

        st.error(
            f"No fue posible identificar la cuenta de Gmail: {e}"
        )

        return None


# ============================================================
# PROCESAR CALLBACK ANTES DE DIBUJAR LA APP
# ============================================================

if "code" in st.query_params:

    procesar_callback_google()


# ============================================================
# LOGIN AUTOMÁTICO
# ============================================================

credentials = obtener_credentials()

if credentials is None:

    iniciar_google_login()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"""
        <div style="
            text-align:center;
            padding:10px 0 20px 0;
        ">
            <div style="
                color:{DORADO_CLARO};
                font-size:25px;
                font-weight:700;
            ">
                CASA DORADA
            </div>

            <div style="
                color:{GRIS};
                font-size:12px;
                letter-spacing:1px;
            ">
                LOS CABOS RESORT & SPA
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.subheader("🔐 Cuenta de Gmail")

    credentials = obtener_credentials()

    if credentials:

        email_usuario = obtener_email_usuario()

        if email_usuario:

            st.markdown(
                f"""
                <div class="connected">
                    ✓ Gmail conectado<br>
                    <strong>{email_usuario}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.success("✓ Gmail conectado")

        if st.button(
            "Cerrar sesión",
            use_container_width=True,
        ):

            for key in [
                "google_credentials",
                "oauth_flow",
                "oauth_state",
                "oauth_url",
            ]:
                st.session_state.pop(
                    key,
                    None,
                )

            st.rerun()

    else:

        st.markdown(
            """
            <div class="disconnected">
                Gmail no conectado
            </div>
            """,
            unsafe_allow_html=True,
        )

        if "oauth_url" in st.session_state:

            st.link_button(
                "🔐 Iniciar sesión con Google",
                st.session_state["oauth_url"],
                use_container_width=True,
            )

    st.markdown("---")

    st.subheader("⚙️ Configuración")

    moneda = st.radio(
        "Moneda",
        ["USD", "MXN"],
        index=0,
    )

    tipo_cambio = st.number_input(
        "Tipo de cambio USD → MXN",
        min_value=1.0,
        value=20.0,
        step=0.1,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="top-card">

        <div class="main-title">
            Cotizador Casa Dorada
        </div>

        <div class="subtitle">
            Crea cotizaciones profesionales y guárdalas
            directamente en tu cuenta de Gmail.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SI NO HAY LOGIN
# ============================================================

credentials = obtener_credentials()

if not credentials:

    st.info(
        "Para utilizar el cotizador debes iniciar sesión con Google."
    )

    if "oauth_url" in st.session_state:

        st.link_button(
            "🔐 Iniciar sesión con Google",
            st.session_state["oauth_url"],
        )

    st.stop()


# ============================================================
# EMAIL DEL AGENTE
# ============================================================

email_usuario = obtener_email_usuario()

if not email_usuario:

    st.error(
        "No fue posible identificar tu cuenta de Gmail."
    )

    st.stop()


# ============================================================
# COLUMNAS PRINCIPALES
# ============================================================

col_input, col_preview = st.columns(
    [1, 1],
    gap="large",
)


# ============================================================
# INPUTS
# ============================================================

with col_input:

    st.header("📝 Datos de la Cotización")

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    nombre_huesped = st.text_input(
        "Nombre del huésped",
        placeholder="John Smith",
    )

    email_huesped = st.text_input(
        "Correo del huésped",
        placeholder="guest@email.com",
    )

    col1, col2 = st.columns(2)

    with col1:

        fecha_checkin = st.date_input(
            "Check in",
            value=date.today(),
        )

    with col2:

        fecha_checkout = st.date_input(
            "Check out",
            value=date.today(),
        )

    if fecha_checkout > fecha_checkin:

        noches = (
            fecha_checkout - fecha_checkin
        ).days

    else:

        noches = 1

        if fecha_checkout < fecha_checkin:

            st.warning(
                "El check out no puede ser anterior al check in."
            )

    col1, col2 = st.columns(2)

    with col1:

        adultos = st.number_input(
            "Adultos",
            min_value=1,
            value=2,
            step=1,
        )

    with col2:

        menores = st.number_input(
            "Menores",
            min_value=0,
            value=0,
            step=1,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# OPCIONES DE COTIZACIÓN
# ============================================================

with col_input:

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.subheader("🏨 Opciones de estancia")

    # --------------------------------------------------------
    # OPCIÓN 1
    # --------------------------------------------------------

    st.markdown(
        f"### Opción 1"
    )

    col1, col2 = st.columns(2)

    with col1:

        suite_1 = st.selectbox(
            "Suite",
            [
                "Junior Suite",
                "One Bedroom Suite",
                "One Bedroom Plus w/ Jacuzzi",
                "Executive Suite",
                "Two Bedroom Suite",
                "One Bedroom Penthouse",
            ],
            key="suite_1",
        )

    with col2:

        plan_1 = st.selectbox(
            "Plan",
            [
                "European Plan",
                "All Inclusive",
            ],
            key="plan_1",
        )

    tarifa_1 = st.number_input(
        "Tarifa por noche USD",
        min_value=0.0,
        value=320.0,
        step=10.0,
        key="tarifa_1",
    )

    link_1 = st.text_input(
        "Link de reserva Opción 1",
        value="",
        placeholder="https://...",
        key="link_1",
    )

    # --------------------------------------------------------
    # OPCIÓN 2
    # --------------------------------------------------------

    st.markdown(
        "### Opción 2"
    )

    col1, col2 = st.columns(2)

    with col1:

        suite_2 = st.selectbox(
            "Suite",
            [
                "Junior Suite",
                "One Bedroom Suite",
                "One Bedroom Plus w/ Jacuzzi",
                "Executive Suite",
                "Two Bedroom Suite",
                "One Bedroom Penthouse",
            ],
            key="suite_2",
        )

    with col2:

        plan_2 = st.selectbox(
            "Plan",
            [
                "European Plan",
                "All Inclusive",
            ],
            key="plan_2",
        )

    tarifa_2 = st.number_input(
        "Tarifa por noche USD",
        min_value=0.0,
        value=480.0,
        step=10.0,
        key="tarifa_2",
    )

    link_2 = st.text_input(
        "Link de reserva Opción 2",
        value="",
        placeholder="https://...",
        key="link_2",
    )

    # --------------------------------------------------------
    # OPCIÓN 3
    # --------------------------------------------------------

    st.markdown(
        "### Opción 3"

    )

    col1, col2 = st.columns(2)

    with col1:

        suite_3 = st.selectbox(
            "Suite",
            [
                "Junior Suite",
                "One Bedroom Suite",
                "One Bedroom Plus w/ Jacuzzi",
                "Executive Suite",
                "Two Bedroom Suite",
                "One Bedroom Penthouse",
            ],
            key="suite_3",
        )

    with col2:

        plan_3 = st.selectbox(
            "Plan",
            [
                "European Plan",
                "All Inclusive",
            ],
            key="plan_3",
        )

    tarifa_3 = st.number_input(
        "Tarifa por noche USD",
        min_value=0.0,
        value=0.0,
        step=10.0,
        key="tarifa_3",
    )

    link_3 = st.text_input(
        "Link de reserva Opción 3",
        value="",
        placeholder="Opcional",
        key="link_3",
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# TRANSPORTACIÓN
# ============================================================

with col_input:

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.subheader("🚐 Transportación")

    incluir_transportacion = st.checkbox(
        "Incluir transportación aeropuerto",
        value=False,
    )

    if incluir_transportacion:

        traslado_usd = st.number_input(
            "Roundtrip Airport Transportation USD",
            min_value=0.0,
            value=267.0,
            step=1.0,
        )

    else:

        traslado_usd = 0.0

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# ARCHIVOS
# ============================================================

with col_input:

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.subheader("📎 Archivos adjuntos")

    archivos_adjuntos = st.file_uploader(
        "Adjuntar PDF, imágenes u otros archivos",
        accept_multiple_files=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# TEXTO PERSONALIZADO
# ============================================================

with col_input:

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.subheader("💬 Mensaje adicional")

    mensaje_adicional = st.text_area(
        "Opcional",
        placeholder=(
            "Agrega información adicional para el huésped..."
        ),
        height=120,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# FUNCIONES DE FORMATO
# ============================================================

def formatear(monto_usd):

    if moneda == "MXN":

        return (
            f"${monto_usd * tipo_cambio:,.2f} MXN"
        )

    return f"${monto_usd:,.2f} USD"


def formatear_fecha_es(fecha):

    meses = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]

    return (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )


# ============================================================
# TOTALES
# ============================================================

total_1 = tarifa_1 * noches
total_2 = tarifa_2 * noches
total_3 = tarifa_3 * noches

# ============================================================
# EMAIL HTML
# ============================================================

fecha_checkin_texto = formatear_fecha_es(
    fecha_checkin
)

fecha_checkout_texto = formatear_fecha_es(
    fecha_checkout
)


def crear_bloque_opcion(
    numero,
    suite,
    plan,
    tarifa,
    total,
    link,
):

    if tarifa <= 0:
        return ""

    boton = ""

    if link.strip():

        boton = f"""
        <a
            href="{link}"
            style="
                display:inline-block;
                background:#0B2545;
                color:#ffffff;
                text-decoration:none;
                padding:12px 22px;
                border-radius:6px;
                font-weight:bold;
                margin-top:10px;
                border-bottom:3px solid #C9A227;
            "
        >
            RESERVAR OPCIÓN {numero}
        </a>
        """

    return f"""
    <div style="
        border:1px solid #D9DEE5;
        border-top:4px solid #C9A227;
        border-radius:8px;
        padding:22px;
        margin-bottom:22px;
        background:#FAFAFA;
    ">

        <div style="
            font-size:19px;
            font-weight:bold;
            color:#0B2545;
            margin-bottom:8px;
        ">
            Opción {numero}: {plan}
        </div>

        <div style="
            color:#555555;
            font-size:16px;
            margin-bottom:12px;
        ">
            <strong>{suite}</strong>
        </div>

        <div style="
            color:#444444;
            line-height:1.7;
        ">

            <strong>Estancia:</strong>
            {fecha_checkin_texto}
            al
            {fecha_checkout_texto}
            ({noches} noches)

            <br>

            <strong>Huéspedes:</strong>
            {adultos} adultos
            {f" y {menores} menores" if menores > 0 else ""}

            <br>

            <strong>Tarifa por noche:</strong>
            <span style="
                color:#B18A19;
                font-weight:bold;
            ">
                {formatear(tarifa)}
            </span>

        </div>

        <div style="
            display:inline-block;
            background:#EEF2F7;
            color:#0B2545;
            font-size:18px;
            font-weight:bold;
            padding:9px 14px;
            margin-top:14px;
            border-radius:5px;
        ">
            Total estancia: {formatear(total)}
        </div>

        <br>

        {boton}

    </div>
    """


bloques_opciones = ""

bloques_opciones += crear_bloque_opcion(
    1,
    suite_1,
    plan_1,
    tarifa_1,
    total_1,
    link_1,
)

bloques_opciones += crear_bloque_opcion(
    2,
    suite_2,
    plan_2,
    tarifa_2,
    total_2,
    link_2,
)

bloques_opciones += crear_bloque_opcion(
    3,
    suite_3,
    plan_3,
    tarifa_3,
    total_3,
    link_3,
)


transportacion_html = ""

if incluir_transportacion:

    transportacion_html = f"""
    <div style="
        border-top:1px solid #D9DEE5;
        padding-top:18px;
        margin-top:20px;
    ">

        <strong>Servicios adicionales</strong>

        <p>
            Roundtrip Airport Transportation:
            <strong style="color:#B18A19;">
                {formatear(traslado_usd)}
            </strong>
        </p>

    </div>
    """


mensaje_adicional_html = ""

if mensaje_adicional.strip():

    mensaje_adicional_html = f"""
    <div style="
        background:#F5F5F5;
        padding:15px;
        border-radius:6px;
        margin-top:20px;
    ">
        {mensaje_adicional}
    </div>
    """


cuerpo_html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

</head>

<body style="
    margin:0;
    padding:20px;
    background:#F4F5F7;
    font-family:Arial,Helvetica,sans-serif;
">

<div style="
    max-width:680px;
    margin:auto;
    background:#ffffff;
    border-radius:10px;
    overflow:hidden;
">

    <div style="
        background:#0B2545;
        padding:30px;
        text-align:center;
        border-bottom:4px solid #C9A227;
    ">

        <img
            src="https://casadorada.com/wp-content/uploads/2021/04/logo-casa-dorada.png"
            alt="Casa Dorada Los Cabos Resort & Spa"
            style="
                max-width:220px;
                width:100%;
                height:auto;
            "
        >

    </div>


    <div style="
        padding:30px;
        color:#333333;
        line-height:1.65;
    ">

        <p style="
            color:#0B2545;
            font-size:19px;
            font-weight:bold;
        ">
            Estimado/a {nombre_huesped},
        </p>


        <p>
            Es un verdadero placer saludarle desde
            <strong>
                Casa Dorada Los Cabos Resort & Spa
            </strong>.
        </p>


        <p>
            A continuación, nos complace presentarle
            nuestra propuesta personalizada para su
            próxima estancia:
        </p>


        {bloques_opciones}


        {transportacion_html}


        {mensaje_adicional_html}


        <div style="
            border-top:1px solid #D9DEE5;
            padding-top:20px;
            margin-top:25px;
            font-size:13px;
            color:#666666;
        ">

            <strong>Políticas:</strong>

            <br>

            Reservation is guaranteed with first night deposit.

            <br>

            Cancelación de acuerdo con la tarifa seleccionada.

        </div>

    </div>


    <div style="
        background:#0B2545;
        color:#AAB6C5;
        text-align:center;
        padding:22px;
        font-size:12px;
        border-top:2px solid #C9A227;
    ">

        <strong style="color:#ffffff;">
            {email_usuario}
        </strong>

        <br>

        Casa Dorada Los Cabos Resort & Spa

        <br>

        Medano Beach, Cabo San Lucas, BCS

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

    st.markdown(
        f"""
        <div class="metric-box">

            <div class="metric-label">
                Huésped
            </div>

            <div class="metric-value">
                {nombre_huesped if nombre_huesped else "Sin nombre"}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.components.v1.html(
        cuerpo_html,
        height=900,
        scrolling=True,
    )


# ============================================================
# CREAR MENSAJE MIME
# ============================================================

def crear_mensaje_mime():

    msg = EmailMessage()

    msg["From"] = email_usuario

    msg["To"] = email_huesped

    msg["Subject"] = (
        f"Cotización Especial | "
        f"Casa Dorada Los Cabos - "
        f"{nombre_huesped}"
    )

    msg.set_content(
        "Por favor visualice este correo en un cliente "
        "de correo compatible con HTML."
    )

    msg.add_alternative(
        cuerpo_html,
        subtype="html",
    )

    if archivos_adjuntos:

        for archivo in archivos_adjuntos:

            contenido = archivo.getvalue()

            nombre_archivo = archivo.name

            tipo_mime = archivo.type

            if tipo_mime and "/" in tipo_mime:

                maintype, subtype = tipo_mime.split(
                    "/",
                    1,
                )

            else:

                maintype = "application"
                subtype = "octet-stream"

            msg.add_attachment(
                contenido,
                maintype=maintype,
                subtype=subtype,
                filename=nombre_archivo,
            )

    return msg


# ============================================================
# FUNCIONES GMAIL API
# ============================================================

def mensaje_raw_base64(msg):

    raw_message = base64.urlsafe_b64encode(
        msg.as_bytes()
    ).decode()

    return raw_message


def guardar_borrador():

    service = obtener_gmail_service()

    if not service:
        raise Exception(
            "No existe conexión con Gmail."
        )

    msg = crear_mensaje_mime()

    raw_message = mensaje_raw_base64(msg)

    body = {
        "message": {
            "raw": raw_message
        }
    }

    resultado = (
        service.users()
        .drafts()
        .create(
            userId="me",
            body=body,
        )
        .execute()
    )

    return resultado


def enviar_correo():

    service = obtener_gmail_service()

    if not service:
        raise Exception(
            "No existe conexión con Gmail."
        )

    msg = crear_mensaje_mime()

    raw_message = mensaje_raw_base64(msg)

    body = {
        "raw": raw_message
    }

    resultado = (
        service.users()
        .messages()
        .send(
            userId="me",
            body=body,
        )
        .execute()
    )

    return resultado


# ============================================================
# BOTONES
# ============================================================

st.markdown("---")

col_btn1, col_btn2 = st.columns(2)


with col_btn1:

    btn_borrador = st.button(
        "📝 Guardar en Borradores",
        type="primary",
        use_container_width=True,
    )


with col_btn2:

    btn_enviar = st.button(
        "🚀 Enviar Ahora",
        use_container_width=True,
    )


# ============================================================
# VALIDACIONES
# ============================================================

def validar_cotizacion():

    errores = []

    if not nombre_huesped.strip():

        errores.append(
            "Ingresa el nombre del huésped."
        )

    if not email_huesped.strip():

        errores.append(
            "Ingresa el correo del huésped."
        )

    if "@" not in email_huesped:

        errores.append(
            "El correo del huésped no parece válido."
        )

    if tarifa_1 <= 0:

        errores.append(
            "La Opción 1 debe tener una tarifa."
        )

    if fecha_checkout <= fecha_checkin:

        errores.append(
            "La fecha de check out debe ser posterior "
            "al check in."
        )

    return errores


# ============================================================
# GUARDAR BORRADOR
# ============================================================

if btn_borrador:

    errores = validar_cotizacion()

    if errores:

        for error in errores:

            st.error(error)

    else:

        with st.spinner(
            "Guardando borrador en Gmail..."
        ):

            try:

                resultado = guardar_borrador()

                draft_id = resultado.get(
                    "id",
                    "N/A",
                )

                st.success(
                    f"✓ Borrador guardado correctamente "
                    f"en **{email_usuario}**."
                )

                st.caption(
                    f"Draft ID: {draft_id}"
                )

            except Exception as e:

                st.error(
                    f"No fue posible guardar el borrador: {e}"
                )


# ============================================================
# ENVIAR EMAIL
# ============================================================

if btn_enviar:

    errores = validar_cotizacion()

    if errores:

        for error in errores:

            st.error(error)

    else:

        with st.spinner(
            "Enviando correo..."
        ):

            try:

                resultado = enviar_correo()

                message_id = resultado.get(
                    "id",
                    "N/A",
                )

                st.success(
                    f"✓ Correo enviado correctamente "
                    f"desde **{email_usuario}** "
                    f"a **{email_huesped}**."
                )

                st.caption(
                    f"Message ID: {message_id}"
                )

            except Exception as e:

                st.error(
                    f"No fue posible enviar el correo: {e}"
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
    <div style="
        text-align:center;
        color:{GRIS_2};
        font-size:11px;
        padding:30px 0 10px 0;
    ">

        Casa Dorada Cotizador
        <br>
        Gmail conectado: {email_usuario}

    </div>
    """,
    unsafe_allow_html=True,
)

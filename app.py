import streamlit as st
import base64
import json
import os
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Cotizador Casa Dorada",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# COLORES
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
# CSS DARK MODE
# ============================================================

st.markdown(
    f"""
    <style>

    /* ==============================
       GLOBAL
       ============================== */

    .stApp {{
        background:
            radial-gradient(
                circle at top right,
                rgba(201,162,39,0.07),
                transparent 35%
            ),
            {FONDO};
        color: {BLANCO};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: {AZUL};
        border-right: 1px solid rgba(255,255,255,0.08);
    }}

    [data-testid="stSidebar"] * {{
        color: {BLANCO};
    }}


    /* ==============================
       TEXTOS
       ============================== */

    h1, h2, h3, h4 {{
        color: {BLANCO} !important;
    }}

    p, label {{
        color: {GRIS} !important;
    }}


    /* ==============================
       INPUTS
       ============================== */

    div[data-baseweb="input"] {{
        background: {CARD_2};
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 8px;
    }}

    div[data-baseweb="input"] input {{
        color: {BLANCO} !important;
    }}

    div[data-baseweb="textarea"] {{
        background: {CARD_2};
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 8px;
    }}

    textarea {{
        color: {BLANCO} !important;
    }}


    /* SELECTBOX */

    div[data-baseweb="select"] > div {{
        background: {CARD_2};
        border: 1px solid rgba(255,255,255,0.10);
        color: {BLANCO};
        border-radius: 8px;
    }}

    div[data-baseweb="select"] span {{
        color: {BLANCO} !important;
    }}


    /* DATE INPUT */

    div[data-testid="stDateInput"] input {{
        background: {CARD_2};
        color: {BLANCO} !important;
        border: 1px solid rgba(255,255,255,0.10);
    }}


    /* NUMBER INPUT */

    div[data-testid="stNumberInput"] input {{
        background: {CARD_2};
        color: {BLANCO} !important;
    }}


    /* ==============================
       BUTTONS
       ============================== */

    .stButton > button {{
        width: 100%;
        border-radius: 8px;
        border: 1px solid {DORADO};
        background: transparent;
        color: {DORADO_CLARO};
        font-weight: 600;
        min-height: 44px;
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        background: {DORADO};
        color: #081321;
        border-color: {DORADO};
    }}


    /* ==============================
       FILE UPLOADER
       ============================== */

    [data-testid="stFileUploader"] {{
        background: {CARD};
        border: 1px dashed rgba(201,162,39,0.45);
        border-radius: 10px;
        padding: 10px;
    }}


    /* ==============================
       HEADER
       ============================== */

    .main-header {{
        background:
            linear-gradient(
                135deg,
                {AZUL_2},
                {AZUL}
            );

        border: 1px solid rgba(201,162,39,0.20);
        border-radius: 16px;

        padding: 24px 28px;
        margin-bottom: 24px;

        box-shadow:
            0 15px 40px rgba(0,0,0,0.25);
    }}

    .brand {{
        font-size: 28px;
        font-weight: 700;
        color: {BLANCO};
        letter-spacing: 0.5px;
    }}

    .brand span {{
        color: {DORADO_CLARO};
    }}

    .subtitle {{
        color: {GRIS};
        font-size: 14px;
        margin-top: 4px;
    }}


    /* ==============================
       SECTION TITLE
       ============================== */

    .section-title {{
        display: flex;
        align-items: center;
        gap: 10px;

        margin-top: 18px;
        margin-bottom: 14px;

        font-size: 18px;
        font-weight: 700;

        color: {BLANCO};
    }}

    .section-title::before {{
        content: "";
        width: 4px;
        height: 22px;

        background: {DORADO};
        border-radius: 10px;
    }}


    /* ==============================
       CARDS
       ============================== */

    .card {{
        background: {CARD};

        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;

        padding: 20px;

        margin-bottom: 18px;

        box-shadow:
            0 10px 30px rgba(0,0,0,0.18);
    }}

    .quote-card {{
        background:
            linear-gradient(
                145deg,
                {CARD_2},
                {CARD}
            );

        border: 1px solid rgba(201,162,39,0.22);
        border-radius: 14px;

        padding: 22px;

        min-height: 220px;
    }}

    .quote-title {{
        color: {DORADO_CLARO};
        font-size: 18px;
        font-weight: 700;
    }}

    .quote-price {{
        color: {BLANCO};
        font-size: 27px;
        font-weight: 700;
        margin-top: 15px;
    }}

    .quote-small {{
        color: {GRIS};
        font-size: 13px;
    }}


    /* ==============================
       TOTAL
       ============================== */

    .total-box {{
        background:
            linear-gradient(
                135deg,
                rgba(201,162,39,0.18),
                rgba(201,162,39,0.05)
            );

        border: 1px solid rgba(201,162,39,0.45);
        border-radius: 14px;

        padding: 22px;
        text-align: right;

        margin-top: 20px;
    }}

    .total-label {{
        color: {GRIS};
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .total {{
        color: {DORADO_CLARO};
        font-size: 32px;
        font-weight: 800;
    }}


    /* ==============================
       GMAIL STATUS
       ============================== */

    .gmail-connected {{
        background: rgba(66,200,138,0.08);
        border: 1px solid rgba(66,200,138,0.30);
        border-radius: 10px;

        padding: 13px 16px;

        color: {VERDE};
        font-weight: 600;
    }}

    .gmail-disconnected {{
        background: rgba(229,107,111,0.08);
        border: 1px solid rgba(229,107,111,0.30);
        border-radius: 10px;

        padding: 13px 16px;

        color: {ROJO};
        font-weight: 600;
    }}


    /* ==============================
       SIDEBAR
       ============================== */

    .sidebar-title {{
        font-size: 20px;
        font-weight: 700;
        color: {DORADO_CLARO};
        margin-bottom: 20px;
    }}

    .agent-box {{
        background: rgba(255,255,255,0.04);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }}

    .agent-label {{
        color: {GRIS_2};
        font-size: 12px;
        text-transform: uppercase;
    }}

    .agent-name {{
        color: {BLANCO};
        font-weight: 600;
        margin-top: 4px;
    }}


    /* ==============================
       ALERTS
       ============================== */

    div[data-testid="stAlert"] {{
        border-radius: 10px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# GOOGLE OAUTH
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose"
]


def get_google_client_config():

    client_id = st.secrets["google_oauth"]["client_id"]
    client_secret = st.secrets["google_oauth"]["client_secret"]

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                st.secrets["google_oauth"]["redirect_uri"]
            ]
        }
    }


def create_oauth_flow():

    config = get_google_client_config()

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES
    )

    flow.redirect_uri = st.secrets["google_oauth"]["redirect_uri"]

    return flow


def get_credentials():

    if "google_credentials" not in st.session_state:
        return None

    credentials_data = st.session_state["google_credentials"]

    credentials = Credentials(
        token=credentials_data.get("token"),
        refresh_token=credentials_data.get("refresh_token"),
        token_uri=credentials_data.get("token_uri"),
        client_id=credentials_data.get("client_id"),
        client_secret=credentials_data.get("client_secret"),
        scopes=credentials_data.get("scopes")
    )

    if credentials.expired and credentials.refresh_token:

        try:

            credentials.refresh(Request())

            st.session_state["google_credentials"] = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes
            }

        except Exception:

            st.session_state.pop(
                "google_credentials",
                None
            )

            return None

    return credentials


# ============================================================
# PROCESAR CALLBACK GOOGLE
# ============================================================

if "code" in st.query_params:

    code = st.query_params["code"]

    try:

        flow = create_oauth_flow()

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        st.session_state["google_credentials"] = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }

        st.query_params.clear()

        st.rerun()

    except Exception as e:

        st.error(
            f"No fue posible completar la conexión con Google: {e}"
        )


# ============================================================
# GOOGLE LOGIN
# ============================================================

def google_login():

    flow = create_oauth_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    st.session_state["oauth_state"] = state

    return authorization_url


# ============================================================
# GMAIL SERVICE
# ============================================================

def get_gmail_service():

    credentials = get_credentials()

    if not credentials:
        return None

    return build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False
    )


# ============================================================
# CREAR MENSAJE MIME
# ============================================================

def create_email(
    sender_name,
    sender_email,
    guest_email,
    subject,
    html_body,
    attachments
):

    message = EmailMessage()

    message["From"] = formataddr(
        (sender_name, sender_email)
    )

    message["To"] = guest_email

    message["Subject"] = subject

    message.set_content(
        "Please view this email in an HTML-compatible email client."
    )

    message.add_alternative(
        html_body,
        subtype="html"
    )

    for attachment in attachments:

        file_data = attachment.getvalue()

        file_name = attachment.name

        mime_type = attachment.type or "application/octet-stream"

        if "/" in mime_type:

            maintype, subtype = mime_type.split(
                "/",
                1
            )

        else:

            maintype = "application"
            subtype = "octet-stream"

        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=file_name
        )

    return message


# ============================================================
# GUARDAR BORRADOR
# ============================================================

def save_draft(
    guest_email,
    subject,
    html_body,
    sender_name,
    sender_email,
    attachments
):

    service = get_gmail_service()

    if not service:

        raise Exception(
            "Gmail no está conectado."
        )

    message = create_email(
        sender_name=sender_name,
        sender_email=sender_email,
        guest_email=guest_email,
        subject=subject,
        html_body=html_body,
        attachments=attachments
    )

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    body = {
        "message": {
            "raw": raw_message
        }
    }

    draft = service.users().drafts().create(
        userId="me",
        body=body
    ).execute()

    return draft


# ============================================================
# ENVIAR DIRECTAMENTE
# ============================================================

def send_email(
    guest_email,
    subject,
    html_body,
    sender_name,
    sender_email,
    attachments
):

    service = get_gmail_service()

    if not service:

        raise Exception(
            "Gmail no está conectado."
        )

    message = create_email(
        sender_name=sender_name,
        sender_email=sender_email,
        guest_email=guest_email,
        subject=subject,
        html_body=html_body,
        attachments=attachments
    )

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    body = {
        "raw": raw_message
    }

    result = service.users().messages().send(
        userId="me",
        body=body
    ).execute()

    return result


# ============================================================
# AGENTES
# ============================================================

AGENTES = {

    "Agente 1": {
        "nombre": "Agente 1",
        "email": "correo1@casadorada.com"
    },

    "Agente 2": {
        "nombre": "Agente 2",
        "email": "correo2@casadorada.com"
    },

    "Agente 3": {
        "nombre": "Agente 3",
        "email": "correo3@casadorada.com"
    }

}


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">CASA DORADA</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        "### Agente"
    )

    agente_seleccionado = st.selectbox(
        "Seleccionar agente",
        list(AGENTES.keys())
    )

    agente = AGENTES[
        agente_seleccionado
    ]

    st.markdown(
        f"""
        <div class="agent-box">

            <div class="agent-label">
                Agente
            </div>

            <div class="agent-name">
                {agente["nombre"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown(
        "### Gmail"
    )

    credentials = get_credentials()

    if credentials:

        st.markdown(
            """
            <div class="gmail-connected">
                ● Gmail conectado
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        if st.button(
            "Desconectar Gmail"
        ):

            st.session_state.pop(
                "google_credentials",
                None
            )

            st.rerun()

    else:

        st.markdown(
            """
            <div class="gmail-disconnected">
                ● Gmail no conectado
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        auth_url = google_login()

        st.link_button(
            "🔐 Conectar mi Gmail",
            auth_url,
            use_container_width=True
        )

        st.caption(
            "Cada agente conecta su propia cuenta de Gmail."
        )

    st.divider()

    st.markdown(
        "### Configuración"
    )

    moneda = st.selectbox(
        "Moneda",
        ["USD", "MXN"]
    )

    tipo_cambio = st.number_input(
        "Tipo de cambio",
        min_value=1.0,
        value=18.50,
        step=0.10
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">

        <div class="brand">
            CASA <span>DORADA</span>
        </div>

        <div class="subtitle">
            Los Cabos Resort & Spa · Reservations
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATOS DEL HUÉSPED
# ============================================================

st.markdown(
    '<div class="section-title">Datos del huésped</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    guest_name = st.text_input(
        "Nombre del huésped",
        placeholder="John Smith"
    )

with col2:

    guest_email = st.text_input(
        "Correo electrónico",
        placeholder="guest@email.com"
    )


col3, col4, col5, col6 = st.columns(4)

with col3:

    check_in = st.date_input(
        "Check in",
        value=date.today()
    )

with col4:

    check_out = st.date_input(
        "Check out",
        value=date.today()
    )

with col5:

    adults = st.number_input(
        "Adultos",
        min_value=1,
        value=2
    )

with col6:

    children = st.number_input(
        "Niños",
        min_value=0,
        value=0
    )


# ============================================================
# NOCHES
# ============================================================

nights = (
    check_out - check_in
).days

if nights <= 0:

    st.warning(
        "La fecha de salida debe ser posterior al check in."
    )

    nights = 0


# ============================================================
# OPCIONES
# ============================================================

st.markdown(
    '<div class="section-title">Opciones de cotización</div>',
    unsafe_allow_html=True
)


suite_options = [
    "Junior Suite",
    "One Bedroom Suite",
    "One Bedroom Plus w/ Jacuzzi",
    "Executive Suite",
    "Two Bedroom Suite",
    "One Bedroom Penthouse"
]


plan_options = [
    "EP",
    "All Inclusive"
]


# ============================================================
# OPCIÓN 1
# ============================================================

col1, col2, col3 = st.columns([2, 1, 1])

with col1:

    suite_1 = st.selectbox(
        "Suite · Opción 1",
        suite_options,
        key="suite1"
    )

with col2:

    plan_1 = st.selectbox(
        "Plan",
        plan_options,
        key="plan1"
    )

with col3:

    rate_1 = st.number_input(
        "Tarifa por noche",
        min_value=0.0,
        value=350.0,
        step=10.0,
        key="rate1"
    )


# ============================================================
# OPCIÓN 2
# ============================================================

col1, col2, col3 = st.columns([2, 1, 1])

with col1:

    suite_2 = st.selectbox(
        "Suite · Opción 2",
        suite_options,
        index=1,
        key="suite2"
    )

with col2:

    plan_2 = st.selectbox(
        "Plan",
        plan_options,
        index=1,
        key="plan2"
    )

with col3:

    rate_2 = st.number_input(
        "Tarifa por noche",
        min_value=0.0,
        value=425.0,
        step=10.0,
        key="rate2"
    )


# ============================================================
# OPCIÓN 3
# ============================================================

usar_opcion_3 = st.checkbox(
    "Agregar tercera opción"
)

suite_3 = None
plan_3 = None
rate_3 = 0.0

if usar_opcion_3:

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:

        suite_3 = st.selectbox(
            "Suite · Opción 3",
            suite_options,
            index=2,
            key="suite3"
        )

    with col2:

        plan_3 = st.selectbox(
            "Plan",
            plan_options,
            key="plan3"
        )

    with col3:

        rate_3 = st.number_input(
            "Tarifa por noche",
            min_value=0.0,
            value=500.0,
            step=10.0,
            key="rate3"
        )


# ============================================================
# TRANSPORTACIÓN
# ============================================================

st.markdown(
    '<div class="section-title">Transportación</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 3])

with col1:

    incluir_transportacion = st.checkbox(
        "Incluir transporte"
    )

with col2:

    transportacion = st.number_input(
        "Transportación roundtrip USD",
        min_value=0.0,
        value=267.0,
        step=10.0,
        disabled=not incluir_transportacion
    )


# ============================================================
# ARCHIVOS
# ============================================================

st.markdown(
    '<div class="section-title">Archivos adjuntos</div>',
    unsafe_allow_html=True
)

attachments = st.file_uploader(
    "Adjuntar archivos a la cotización",
    accept_multiple_files=True
)

if attachments is None:
    attachments = []


# ============================================================
# TOTALES
# ============================================================

total_1 = rate_1 * nights
total_2 = rate_2 * nights

total_3 = 0

if usar_opcion_3:
    total_3 = rate_3 * nights


# ============================================================
# MOSTRAR TARJETAS
# ============================================================

cards = []

cards.append(
    f"""
    <div class="quote-card">

        <div class="quote-title">
            {suite_1}
        </div>

        <div class="quote-small">
            {plan_1}
        </div>

        <div class="quote-price">
            USD ${rate_1:,.2f}
        </div>

        <div class="quote-small">
            por noche
        </div>

        <hr style="border-color:rgba(255,255,255,0.08);">

        <div class="quote-small">
            {nights} noches
        </div>

        <div class="quote-small">
            Total alojamiento:
            <strong>
                USD ${total_1:,.2f}
            </strong>
        </div>

    </div>
    """
)

cards.append(
    f"""
    <div class="quote-card">

        <div class="quote-title">
            {suite_2}
        </div>

        <div class="quote-small">
            {plan_2}
        </div>

        <div class="quote-price">
            USD ${rate_2:,.2f}
        </div>

        <div class="quote-small">
            por noche
        </div>

        <hr style="border-color:rgba(255,255,255,0.08);">

        <div class="quote-small">
            {nights} noches
        </div>

        <div class="quote-small">
            Total alojamiento:
            <strong>
                USD ${total_2:,.2f}
            </strong>
        </div>

    </div>
    """
)

if usar_opcion_3:

    cards.append(
        f"""
        <div class="quote-card">

            <div class="quote-title">
                {suite_3}
            </div>

            <div class="quote-small">
                {plan_3}
            </div>

            <div class="quote-price">
                USD ${rate_3:,.2f}
            </div>

            <div class="quote-small">
                por noche
            </div>

            <hr style="border-color:rgba(255,255,255,0.08);">

            <div class="quote-small">
                {nights} noches
            </div>

            <div class="quote-small">
                Total alojamiento:
                <strong>
                    USD ${total_3:,.2f}
                </strong>
            </div>

        </div>
        """
    )


columns = st.columns(
    len(cards)
)

for column, card in zip(
    columns,
    cards
):

    with column:

        st.markdown(
            card,
            unsafe_allow_html=True
        )


# ============================================================
# TOTAL TRANSPORTACIÓN
# ============================================================

st.markdown(
    f"""
    <div class="total-box">

        <div class="total-label">
            Transportación
        </div>

        <div class="total">
            USD ${transportacion:,.2f}
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# EMAIL HTML
# ============================================================

subject = (
    f"Casa Dorada Los Cabos - "
    f"Accommodation Quote for {guest_name}"
)


transport_html = ""

if incluir_transportacion:

    transport_html = f"""
        <tr>
            <td style="padding:10px 0;">
                Airport Transportation
            </td>

            <td style="
                padding:10px 0;
                text-align:right;
                font-weight:bold;
            ">
                USD ${transportacion:,.2f}
            </td>
        </tr>
    """


def option_html(
    suite,
    plan,
    rate,
    total
):

    return f"""
    <div style="
        border:1px solid #d7dce3;
        border-radius:10px;
        padding:20px;
        margin-bottom:18px;
    ">

        <h2 style="
            color:#0A2342;
            margin-top:0;
        ">
            {suite}
        </h2>

        <p>
            <strong>Plan:</strong> {plan}
        </p>

        <p>
            <strong>Rate:</strong>
            USD ${rate:,.2f} per night
        </p>

        <p>
            <strong>Stay:</strong>
            {nights} nights
        </p>

        <p style="
            font-size:20px;
            font-weight:bold;
            color:#C9A227;
        ">
            USD ${total:,.2f}
        </p>

    </div>
    """


options_html = ""

options_html += option_html(
    suite_1,
    plan_1,
    rate_1,
    total_1
)

options_html += option_html(
    suite_2,
    plan_2,
    rate_2,
    total_2
)

if usar_opcion_3:

    options_html += option_html(
        suite_3,
        plan_3,
        rate_3,
        total_3
)


email_html = f"""
<!DOCTYPE html>

<html>

<body style="
    margin:0;
    padding:0;
    background:#f3f5f7;
    font-family:Arial,Helvetica,sans-serif;
">

<div style="
    max-width:720px;
    margin:auto;
    background:white;
">

    <div style="
        background:#0A2342;
        padding:30px;
        text-align:center;
    ">

        <h1 style="
            color:white;
            margin:0;
        ">
            CASA <span style="color:#D8B85A;">
                DORADA
            </span>
        </h1>

        <p style="
            color:#d8dee7;
            margin-bottom:0;
        ">
            Los Cabos Resort & Spa
        </p>

    </div>


    <div style="
        padding:30px;
    ">

        <h2 style="
            color:#0A2342;
        ">
            Accommodation Quote
        </h2>

        <p>
            Dear {guest_name},
        </p>

        <p>
            Thank you for considering Casa Dorada Los Cabos
            for your upcoming stay.
        </p>

        <div style="
            background:#f5f7f9;
            padding:18px;
            border-radius:8px;
            margin:20px 0;
        ">

            <strong>Stay details</strong>

            <p style="margin-bottom:5px;">
                Check in:
                {check_in.strftime("%B %d, %Y")}
            </p>

            <p style="margin-bottom:5px;">
                Check out:
                {check_out.strftime("%B %d, %Y")}
            </p>

            <p style="margin-bottom:5px;">
                Guests:
                {adults} adults
                {f"and {children} children" if children else ""}
            </p>

        </div>


        <h2 style="
            color:#0A2342;
        ">
            Accommodation Options
        </h2>

        {options_html}


        {f'''
        <table style="
            width:100%;
            border-collapse:collapse;
            margin-top:20px;
        ">

            {transport_html}

        </table>
        ''' if incluir_transportacion else ""}


        <div style="
            margin-top:30px;
            padding:20px;
            background:#0A2342;
            color:white;
            border-radius:8px;
        ">

            <p style="
                margin:0;
                color:#D8B85A;
                font-size:13px;
            ">
                RESERVATION
            </p>

            <p>
                Reservation is guaranteed with first night
                deposit.
            </p>

        </div>


        <p style="
            margin-top:30px;
        ">
            We look forward to welcoming you to
            Casa Dorada Los Cabos.
        </p>

        <p>
            Best regards,<br>
            <strong>{agente["nombre"]}</strong><br>
            Reservations<br>
            Casa Dorada Los Cabos Resort & Spa
        </p>

    </div>


    <div style="
        background:#0A2342;
        padding:20px;
        text-align:center;
        color:#aab6c5;
        font-size:12px;
    ">

        Casa Dorada Los Cabos Resort & Spa

    </div>

</div>

</body>

</html>
"""


# ============================================================
# PREVIEW
# ============================================================

st.markdown(
    '<div class="section-title">Vista previa del correo</div>',
    unsafe_allow_html=True
)

with st.expander(
    "👁 Ver correo completo"
):

    st.components.v1.html(
        email_html,
        height=900,
        scrolling=True
    )


# ============================================================
# BOTONES
# ============================================================

st.markdown("")

col1, col2 = st.columns(2)


with col1:

    if st.button(
        "💾 GUARDAR EN BORRADORES",
        use_container_width=True
    ):

        if not credentials:

            st.error(
                "Primero debes conectar tu Gmail."
            )

        elif not guest_email:

            st.error(
                "Ingresa el correo del huésped."
            )

        elif not guest_name:

            st.error(
                "Ingresa el nombre del huésped."
            )

        else:

            try:

                draft = save_draft(
                    guest_email=guest_email,
                    subject=subject,
                    html_body=email_html,
                    sender_name=agente["nombre"],
                    sender_email=agente["email"],
                    attachments=attachments
                )

                st.success(
                    "✅ Cotización guardada correctamente "
                    "en los borradores de tu Gmail."
                )

            except Exception as e:

                st.error(
                    f"Error al crear el borrador: {e}"
                )


with col2:

    if st.button(
        "📤 ENVIAR CORREO",
        use_container_width=True
    ):

        if not credentials:

            st.error(
                "Primero debes conectar tu Gmail."
            )

        elif not guest_email:

            st.error(
                "Ingresa el correo del huésped."
            )

        else:

            try:

                result = send_email(
                    guest_email=guest_email,
                    subject=subject,
                    html_body=email_html,
                    sender_name=agente["nombre"],
                    sender_email=agente["email"],
                    attachments=attachments
                )

                st.success(
                    "✅ Correo enviado correctamente."
                )

            except Exception as e:

                st.error(
                    f"Error al enviar el correo: {e}"
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:50px;
        padding:20px;
        color:#6F7D8D;
        font-size:12px;
    ">
        Casa Dorada Los Cabos · Reservations
    </div>
    """,
    unsafe_allow_html=True
)

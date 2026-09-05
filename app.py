import streamlit as st
import base64
import hashlib
import hmac
import json
import secrets
import html
from datetime import date, datetime
from email.message import EmailMessage
from urllib.parse import urlencode

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Cotizador Casa Dorada",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# COLORES
# ============================================================

AZUL = "#173B63"
AZUL_OSCURO = "#102C4A"
AZUL_SUAVE = "#EAF1F7"
DORADO = "#C6A15B"
DORADO_SUAVE = "#F6F0E4"

FONDO = "#F5F7FA"
BLANCO = "#FFFFFF"
TEXTO = "#263238"
GRIS = "#667085"
BORDE = "#E4E7EC"

VERDE = "#16855B"
ROJO = "#B42318"


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
        Roboto, Helvetica, Arial, sans-serif;
    }}

    .stApp {{
        background: {FONDO};
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1350px;
    }}

    /* SIDEBAR */

    section[data-testid="stSidebar"] {{
        background: {BLANCO};
        border-right: 1px solid {BORDE};
    }}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {AZUL};
    }}

    /* HEADER */

    .app-header {{
        background: linear-gradient(
            135deg,
            {AZUL_OSCURO},
            {AZUL}
        );
        padding: 28px 34px;
        border-radius: 16px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 5px 18px rgba(16,44,74,0.12);
    }}

    .app-header-title {{
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 5px;
    }}

    .app-header-subtitle {{
        font-size: 14px;
        opacity: .85;
    }}

    /* CARDS */

    .card {{
        background: {BLANCO};
        border: 1px solid {BORDE};
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(16,24,40,0.04);
    }}

    .section-title {{
        color: {AZUL};
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 5px;
    }}

    .section-subtitle {{
        color: {GRIS};
        font-size: 13px;
        margin-bottom: 18px;
    }}

    /* OPTION CARD */

    .option-title {{
        color: {AZUL};
        font-size: 19px;
        font-weight: 700;
        padding-bottom: 10px;
        margin-bottom: 16px;
        border-bottom: 2px solid {DORADO};
    }}

    /* GOOGLE STATUS */

    .google-connected {{
        background: #ECFDF3;
        border: 1px solid #ABEFC6;
        color: {VERDE};
        padding: 12px 15px;
        border-radius: 10px;
        font-size: 13px;
        margin-bottom: 12px;
    }}

    .google-disconnected {{
        background: #FFF7ED;
        border: 1px solid #FED7AA;
        color: #9A3412;
        padding: 12px 15px;
        border-radius: 10px;
        font-size: 13px;
        margin-bottom: 12px;
    }}

    /* BUTTONS */

    .stButton > button {{
        border-radius: 9px;
        border: 1px solid {AZUL};
        font-weight: 600;
        min-height: 42px;
    }}

    .stButton > button:hover {{
        border-color: {DORADO};
    }}

    /* INPUTS */

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    textarea {{
        border-radius: 8px !important;
    }}

    /* PREVIEW */

    .preview-wrapper {{
        background: #EEF2F6;
        border-radius: 12px;
        padding: 20px;
    }}

    /* SMALL LABEL */

    .small-label {{
        color: {GRIS};
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .4px;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIGURACIÓN DE HABITACIONES
# ============================================================
#
# MODIFICA AQUÍ LAS HABITACIONES.
#
# Puedes agregar habitaciones nuevas siguiendo el mismo formato.
#
# El campo "default_includes" se utilizará como base cuando
# selecciones esa habitación.
#
# El campo "360_url" es opcional.
#
# ============================================================

ROOM_TYPES = {

    "Junior Suite": {
        "default_includes": [
            "Accommodation",
            "Daily breakfast",
            "WiFi"
        ],
        "360_url": ""
    },

    "One Bedroom Suite": {
        "default_includes": [
            "Accommodation",
            "Daily breakfast",
            "WiFi"
        ],
        "360_url": ""
    },

    "One Bedroom Plus w/ Jacuzzi": {
        "default_includes": [
            "Accommodation",
            "Daily breakfast",
            "WiFi",
            "Private Jacuzzi"
        ],
        "360_url": ""
    },

    "Executive Suite": {
        "default_includes": [
            "Accommodation",
            "Daily breakfast",
            "WiFi"
        ],
        "360_url": ""
    },

    "Two Bedroom Suite": {
        "default_includes": [
            "Accommodation",
            "Daily breakfast",
            "WiFi"
        ],
        "360_url": ""
    },

    "One Bedroom Penthouse": {
        "default_includes": [
            "Accommodation",
            "Daily breakfast",
            "WiFi"
        ],
        "360_url": ""
    },

}


# ============================================================
# PLANES
# ============================================================

MEAL_PLANS = {

    "EP": {
        "name": "European Plan",
        "includes": [
            "Accommodation",
            "Daily breakfast"
        ]
    },

    "AI": {
        "name": "All Inclusive",
        "includes": [
            "Accommodation",
            "All Inclusive",
            "Food and beverages",
            "Domestic beverages"
        ]
    },

}


# ============================================================
# GOOGLE OAUTH
# ============================================================

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.compose",
]


def get_google_client_config():

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

    config = get_google_client_config()

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
    )

    return flow


# ============================================================
# STATE OAUTH SIN DEPENDER DE SESSION STATE
# ============================================================

def get_state_secret():

    return st.secrets["google_oauth"]["client_secret"].encode("utf-8")


def create_signed_state(code_verifier):

    payload = {
        "code_verifier": code_verifier,
        "timestamp": int(datetime.now().timestamp()),
        "nonce": secrets.token_urlsafe(16),
    }

    payload_json = json.dumps(
        payload,
        separators=(",", ":")
    )

    payload_encoded = base64.urlsafe_b64encode(
        payload_json.encode()
    ).decode().rstrip("=")

    signature = hmac.new(
        get_state_secret(),
        payload_encoded.encode(),
        hashlib.sha256
    ).digest()

    signature_encoded = base64.urlsafe_b64encode(
        signature
    ).decode().rstrip("=")

    return f"{payload_encoded}.{signature_encoded}"


def decode_signed_state(state):

    try:

        payload_encoded, signature_encoded = state.split(".")

        expected_signature = hmac.new(
            get_state_secret(),
            payload_encoded.encode(),
            hashlib.sha256
        ).digest()

        received_signature = base64.urlsafe_b64decode(
            signature_encoded + "=" * (
                4 - len(signature_encoded) % 4
            )
        )

        if not hmac.compare_digest(
            expected_signature,
            received_signature
        ):
            return None

        payload = base64.urlsafe_b64decode(
            payload_encoded + "=" * (
                4 - len(payload_encoded) % 4
            )
        )

        data = json.loads(payload.decode())

        # Expira después de 10 minutos
        if (
            int(datetime.now().timestamp())
            - data["timestamp"]
            > 600
        ):
            return None

        return data

    except Exception:
        return None


def generate_pkce():

    code_verifier = secrets.token_urlsafe(64)

    digest = hashlib.sha256(
        code_verifier.encode("ascii")
    ).digest()

    code_challenge = base64.urlsafe_b64encode(
        digest
    ).decode("ascii").rstrip("=")

    return code_verifier, code_challenge


def get_google_login_url():

    flow = create_oauth_flow()

    code_verifier, code_challenge = generate_pkce()

    state = create_signed_state(code_verifier)

    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode({
            "client_id": st.secrets["google_oauth"]["client_id"],
            "redirect_uri": st.secrets["google_oauth"]["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        })
    )

    return authorization_url


def process_google_callback():

    code = st.query_params.get("code")
    state = st.query_params.get("state")

    if not code or not state:
        return None

    state_data = decode_signed_state(state)

    if not state_data:
        st.error(
            "No fue posible validar la conexión con Google. "
            "Intenta nuevamente."
        )
        return None

    code_verifier = state_data["code_verifier"]

    try:

        flow = create_oauth_flow()

        flow.fetch_token(
            code=code,
            code_verifier=code_verifier
        )

        credentials = flow.credentials

        st.session_state["google_credentials"] = (
            credentials_to_dict(credentials)
        )

        st.query_params.clear()

        st.rerun()

    except Exception as e:

        st.error(
            f"No fue posible completar la conexión con Google: {e}"
        )

        return None


def credentials_to_dict(credentials):

    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


def get_credentials():

    data = st.session_state.get(
        "google_credentials"
    )

    if not data:
        return None

    try:

        credentials = Credentials(
            token=data["token"],
            refresh_token=data.get("refresh_token"),
            token_uri=data["token_uri"],
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            scopes=data.get("scopes"),
        )

        if credentials.expired and credentials.refresh_token:

            credentials.refresh(Request())

            st.session_state["google_credentials"] = (
                credentials_to_dict(credentials)
            )

        return credentials

    except Exception:

        return None


def disconnect_google():

    if "google_credentials" in st.session_state:
        del st.session_state["google_credentials"]

    st.rerun()


def get_gmail_service():

    credentials = get_credentials()

    if not credentials:
        return None

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


def get_connected_email():

    service = get_gmail_service()

    if not service:
        return None

    try:

        profile = (
            service.users()
            .getProfile(userId="me")
            .execute()
        )

        return profile.get("emailAddress")

    except Exception:

        return None


# ============================================================
# CALLBACK GOOGLE
# ============================================================

process_google_callback()


# ============================================================
# FUNCIONES DE FORMATO
# ============================================================

def escape_html(value):

    if value is None:
        return ""

    return html.escape(str(value))


def format_currency(value):

    try:

        number = float(value)

        return (
            "$"
            + f"{number:,.2f}"
            + " USD"
        )

    except Exception:

        return "$0.00 USD"


def format_date_english(value):

    if not value:
        return ""

    if isinstance(value, date):

        return value.strftime(
            "%B %-d, %Y"
        )

    try:

        parsed = datetime.strptime(
            str(value),
            "%Y-%m-%d"
        )

        return parsed.strftime(
            "%B %-d, %Y"
        )

    except Exception:

        return str(value)


def includes_to_html(includes):

    if not includes:
        return "<p style='margin:0;color:#777;'>None</p>"

    items = ""

    for item in includes:

        if str(item).strip():

            items += f"""
            <li style="
                margin-bottom:5px;
                color:#444;
                line-height:1.45;
            ">
                {escape_html(item.strip())}
            </li>
            """

    return f"""
    <ul style="
        margin:0;
        padding-left:20px;
    ">
        {items}
    </ul>
    """


def text_to_includes(text):

    if not text:
        return []

    lines = []

    for line in text.splitlines():

        clean = line.strip()

        if clean:
            lines.append(clean)

    return lines


# ============================================================
# CREAR HTML DEL CORREO
# ============================================================

def create_email_html(
    guest_name,
    arrival,
    departure,
    nights,
    adults,
    children,
    options,
    deposit_policy,
    cancellation_policy,
):

    guest_name = escape_html(guest_name)

    children_text = ""

    if children > 0:
        children_text = f" + {children} Children"

    options_html = ""

    for index, option in enumerate(options, start=1):

        room = escape_html(
            option["room"]
        )

        plan = escape_html(
            option["plan"]
        )

        includes_html = includes_to_html(
            option["includes"]
        )

        rate_before = format_currency(
            option["rate_before"]
        )

        rate_tax = format_currency(
            option["rate_tax"]
        )

        stay_total = (
            option["rate_tax"]
            * nights
        )

        additional_amount = option.get(
            "additional_amount",
            0
        )

        grand_total = (
            stay_total
            + additional_amount
        )

        additional_html = ""

        if additional_amount > 0:

            additional_description = escape_html(
                option.get(
                    "additional_description",
                    "Additional Services"
                )
            )

            additional_html = f"""
            <tr>
                <td style="
                    padding:10px 0;
                    color:#555;
                    border-top:1px solid #E2E8F0;
                ">
                    Additional Services:
                    <span style="
                        color:#64748B;
                    ">
                        {additional_description}
                    </span>
                </td>

                <td style="
                    padding:10px 0;
                    font-weight:bold;
                    border-top:1px solid #E2E8F0;
                    white-space:nowrap;
                ">
                    {format_currency(additional_amount)}
                </td>
            </tr>
            """

        buttons_html = ""

        room_360 = option.get(
            "room_360",
            ""
        )

        payment_link = option.get(
            "payment_link",
            ""
        )

        if room_360:

            buttons_html += f"""
            <a href="{escape_html(room_360)}"
               style="
                   background-color:#F6F0E4;
                   color:#173B63;
                   border:1px solid #C6A15B;
                   padding:13px 20px;
                   text-decoration:none;
                   border-radius:5px;
                   font-weight:bold;
                   display:inline-block;
                   font-size:13px;
                   margin-right:8px;
               ">
               VIEW ROOM
            </a>
            """

        if payment_link:

            buttons_html += f"""
            <a href="{escape_html(payment_link)}"
               style="
                   background-color:#173B63;
                   color:#ffffff;
                   padding:13px 20px;
                   text-decoration:none;
                   border-radius:5px;
                   font-weight:bold;
                   display:inline-block;
                   font-size:13px;
               ">
               SECURE YOUR BOOKING
            </a>
            """

        valid_until_html = ""

        if option.get("valid_until"):

            valid_until_html = f"""
            <p style="
                font-size:12px;
                color:#999;
                margin:13px 0 0 0;
            ">
                Quote valid until:
                <strong>
                    {format_date_english(option["valid_until"])}
                </strong>
            </p>
            """

        options_html += f"""

        <!-- OPTION {index} -->

        <table
            width="100%"
            border="0"
            cellpadding="0"
            cellspacing="0"
            style="
                width:100%;
                margin-bottom:25px;
                border:1px solid #E2E8F0;
                border-radius:7px;
                overflow:hidden;
            "
        >

            <tr>
                <td style="
                    background-color:#173B63;
                    color:#ffffff;
                    padding:15px 20px;
                    font-size:14px;
                    font-weight:bold;
                    letter-spacing:.3px;
                ">
                    OPTION {index}
                </td>
            </tr>

            <tr>
                <td style="
                    padding:20px;
                ">

                    <h3 style="
                        margin:0 0 5px 0;
                        color:#173B63;
                        font-size:20px;
                    ">
                        {room}
                    </h3>

                    <p style="
                        margin:0 0 18px 0;
                        color:#777;
                        font-size:13px;
                    ">
                        {plan} · {nights} Nights
                    </p>

                    <table
                        width="100%"
                        border="0"
                        cellpadding="0"
                        cellspacing="0"
                        style="
                            width:100%;
                            font-size:14px;
                        "
                    >

                        <tr>

                            <td style="
                                width:50%;
                                vertical-align:top;
                                padding-right:15px;
                            ">

                                <div style="
                                    color:#888;
                                    font-size:10px;
                                    font-weight:bold;
                                    text-transform:uppercase;
                                    margin-bottom:8px;
                                ">
                                    Inclusions
                                </div>

                                {includes_html}

                            </td>

                            <td style="
                                width:50%;
                                vertical-align:top;
                            ">

                                <table
                                    width="100%"
                                    border="0"
                                    cellpadding="0"
                                    cellspacing="0"
                                >

                                    <tr>
                                        <td style="
                                            padding-bottom:7px;
                                            color:#666;
                                        ">
                                            Rate per night
                                            before taxes:
                                        </td>

                                        <td style="
                                            padding-bottom:7px;
                                            text-align:right;
                                            white-space:nowrap;
                                        ">
                                            {rate_before}
                                        </td>
                                    </tr>

                                    <tr>

                                        <td style="
                                            padding-bottom:10px;
                                            color:#666;
                                            border-bottom:
                                            1px solid #EEEEEE;
                                        ">
                                            Rate per night
                                            taxes included:
                                        </td>

                                        <td style="
                                            padding-bottom:10px;
                                            text-align:right;
                                            border-bottom:
                                            1px solid #EEEEEE;
                                            white-space:nowrap;
                                        ">
                                            {rate_tax}
                                        </td>

                                    </tr>

                                    <tr>

                                        <td style="
                                            padding:14px 0 5px 0;
                                            color:#444;
                                        ">
                                            Stay Total
                                            ({nights} nights):
                                        </td>

                                        <td style="
                                            padding:14px 0 5px 0;
                                            text-align:right;
                                            font-weight:bold;
                                            white-space:nowrap;
                                        ">
                                            {format_currency(stay_total)}
                                        </td>

                                    </tr>

                                    {additional_html}

                                    <tr>

                                        <td style="
                                            padding-top:14px;
                                            color:#173B63;
                                            font-size:17px;
                                            font-weight:bold;
                                            border-top:
                                            2px solid #CBD5E1;
                                        ">
                                            TOTAL AMOUNT:
                                        </td>

                                        <td style="
                                            padding-top:14px;
                                            text-align:right;
                                            color:#173B63;
                                            font-size:17px;
                                            font-weight:bold;
                                            border-top:
                                            2px solid #CBD5E1;
                                            white-space:nowrap;
                                        ">
                                            {format_currency(grand_total)}
                                        </td>

                                    </tr>

                                </table>

                            </td>

                        </tr>

                    </table>

                    <div style="
                        margin-top:20px;
                    ">

                        {buttons_html}

                        {valid_until_html}

                    </div>

                </td>
            </tr>

        </table>
        """

    # ========================================================
    # EMAIL COMPLETO
    # ========================================================

    cuerpo = f"""
    <!DOCTYPE html>

    <html>

    <body style="
        margin:0;
        padding:20px 0;
        background-color:#F3F4F6;
        font-family:Arial, Helvetica, sans-serif;
        color:#333333;
    ">

    <table
        width="600"
        border="0"
        cellpadding="0"
        cellspacing="0"
        align="center"
        style="
            width:600px;
            max-width:600px;
            background-color:#ffffff;
            border:1px solid #EEEEEE;
        "
    >

        <!-- HEADER -->

        <tr>

            <td style="
                padding:30px;
                border-bottom:3px solid #C6A15B;
                background-color:#ffffff;
            ">

                <img
                    src="https://umutu.com/wp-content/uploads/2021/02/Logo-2-3.png"
                    width="280"
                    alt="Casa Dorada Los Cabos Resort & Spa"
                    style="
                        display:block;
                        width:280px;
                        max-width:100%;
                        height:auto;
                        border:0;
                    "
                >

            </td>

        </tr>


        <!-- BODY -->

        <tr>

            <td style="
                padding:30px;
            ">

                <h2 style="
                    color:#173B63;
                    margin:0 0 20px 0;
                    font-size:24px;
                    font-weight:500;
                ">
                    Your Custom Quotation
                </h2>

                <p style="
                    font-size:16px;
                    line-height:1.5;
                    margin:0 0 12px 0;
                ">
                    Hola <strong>{guest_name}</strong>,
                </p>

                <p style="
                    font-size:15px;
                    line-height:1.6;
                    color:#555555;
                    margin:0 0 22px 0;
                ">
                    Thank you for considering
                    <strong>
                        Casa Dorada Los Cabos Resort & Spa
                    </strong>
                    as an option to enjoy Cabo.
                    It is our pleasure to present the details
                    of your requested stay.
                </p>


                <!-- STAY DETAILS -->

                <table
                    width="100%"
                    border="0"
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        width:100%;
                        font-size:14px;
                        margin-bottom:28px;
                    "
                >

                    <tr>

                        <td style="
                            padding:10px 0;
                            color:#888888;
                            width:40%;
                            font-size:10px;
                            font-weight:bold;
                            text-transform:uppercase;
                            border-bottom:1px solid #EEEEEE;
                        ">
                            Arrival
                        </td>

                        <td style="
                            padding:10px 0;
                            font-weight:bold;
                            border-bottom:1px solid #EEEEEE;
                        ">
                            {format_date_english(arrival)}
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:10px 0;
                            color:#888888;
                            font-size:10px;
                            font-weight:bold;
                            text-transform:uppercase;
                            border-bottom:1px solid #EEEEEE;
                        ">
                            Departure
                        </td>

                        <td style="
                            padding:10px 0;
                            font-weight:bold;
                            border-bottom:1px solid #EEEEEE;
                        ">
                            {format_date_english(departure)}
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:10px 0;
                            color:#888888;
                            font-size:10px;
                            font-weight:bold;
                            text-transform:uppercase;
                            border-bottom:1px solid #EEEEEE;
                        ">
                            Guests
                        </td>

                        <td style="
                            padding:10px 0;
                            border-bottom:1px solid #EEEEEE;
                        ">
                            {adults} Adults{children_text}
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:10px 0;
                            color:#888888;
                            font-size:10px;
                            font-weight:bold;
                            text-transform:uppercase;
                        ">
                            Stay
                        </td>

                        <td style="
                            padding:10px 0;
                            font-weight:bold;
                        ">
                            {nights} Nights
                        </td>

                    </tr>

                </table>


                <!-- OPTIONS -->

                <h3 style="
                    color:#173B63;
                    font-size:17px;
                    margin:0 0 15px 0;
                ">
                    Accommodation Options
                </h3>

                {options_html}

            </td>

        </tr>


        <!-- POLICIES -->

        <tr>

            <td style="
                background-color:#F8FAFC;
                padding:25px 30px;
                border-top:1px solid #E2E8F0;
                font-size:13px;
                color:#555555;
            ">

                <h4 style="
                    margin:0 0 12px 0;
                    color:#173B63;
                    text-transform:uppercase;
                    font-size:12px;
                ">
                    Booking Policies
                </h4>

                <p style="
                    margin:0 0 7px 0;
                    line-height:1.5;
                ">
                    <strong>Deposit:</strong>
                    {escape_html(deposit_policy)}
                </p>

                <p style="
                    margin:0;
                    line-height:1.5;
                ">
                    <strong>Cancellation:</strong>
                    {escape_html(cancellation_policy)}
                </p>

            </td>

        </tr>


        <!-- FOOTER -->

        <tr>

            <td style="
                background-color:#173B63;
                padding:25px 30px;
                color:#C9D3DE;
                font-size:11px;
            ">

                <p style="
                    color:#ffffff;
                    margin:0 0 6px 0;
                    font-weight:bold;
                    font-size:12px;
                ">
                    Casa Dorada Los Cabos Resort & Spa
                </p>

                <p style="
                    margin:0;
                    line-height:1.5;
                ">
                    Av. del Pescador s/n,
                    Cabo San Lucas, B.C.S.
                </p>

            </td>

        </tr>

    </table>

    </body>
    </html>
    """

    return cuerpo


# ============================================================
# CREAR MIME
# ============================================================

def create_email_message(
    sender,
    recipient,
    subject,
    html_body,
    attachments=None,
):

    message = EmailMessage()

    message["To"] = recipient
    message["From"] = sender
    message["Subject"] = subject

    message.set_content(
        "Please view this email in an HTML compatible email client."
    )

    message.add_alternative(
        html_body,
        subtype="html"
    )

    if attachments:

        for attachment in attachments:

            file_name = attachment["name"]
            file_type = attachment["type"]
            file_data = attachment["data"]

            if "/" in file_type:

                maintype, subtype = file_type.split(
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
# GMAIL DRAFT
# ============================================================

def save_gmail_draft(
    service,
    message,
):

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    body = {
        "message": {
            "raw": raw_message
        }
    }

    result = (
        service.users()
        .drafts()
        .create(
            userId="me",
            body=body
        )
        .execute()
    )

    return result


# ============================================================
# GMAIL SEND
# ============================================================

def send_gmail_message(
    service,
    message,
):

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    body = {
        "raw": raw_message
    }

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body=body
        )
        .execute()
    )

    return result


# ============================================================
# HEADER DE LA APP
# ============================================================

st.markdown(
    """
    <div class="app-header">

        <div class="app-header-title">
            Cotizador Casa Dorada
        </div>

        <div class="app-header-subtitle">
            Create, preview and send professional quotations
            directly from your Casa Dorada Gmail account.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### Gmail"
    )

    connected_email = get_connected_email()

    if connected_email:

        st.markdown(
            f"""
            <div class="google-connected">
                ✓ Google connected<br>
                <strong>{escape_html(connected_email)}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Disconnect Google",
            use_container_width=True
        ):

            disconnect_google()

    else:

        st.markdown(
            """
            <div class="google-disconnected">
                Google account not connected.
            </div>
            """,
            unsafe_allow_html=True
        )

        login_url = get_google_login_url()

        # IMPORTANTE:
        # target="_blank" hace que Google OAuth se abra
        # en una nueva pestaña.

        st.markdown(
            f"""
            <a href="{login_url}"
               target="_blank"
               rel="noopener noreferrer"
               style="
                   display:block;
                   width:100%;
                   box-sizing:border-box;
                   text-align:center;
                   text-decoration:none;
                   background:#173B63;
                   color:white;
                   padding:12px 15px;
                   border-radius:9px;
                   font-weight:600;
                   margin-bottom:15px;
               ">
               Connect Google Account
            </a>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            "Google authorization will open in a new tab."
        )

    st.divider()

    st.markdown(
        "### Default Policies"
    )

    deposit_policy = st.text_area(
        "Deposit Policy",
        value=(
            "Reservation is guaranteed with first night deposit."
        ),
        height=90,
        key="deposit_policy"
    )

    cancellation_policy = st.text_area(
        "Cancellation Policy",
        value=(
            "Cancellation policies vary according to the selected rate."
        ),
        height=110,
        key="cancellation_policy"
    )


# ============================================================
# INFORMACIÓN DEL HUÉSPED
# ============================================================

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">Guest Information</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Enter the details of the requested stay.</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    guest_name = st.text_input(
        "Guest Name",
        placeholder="John Smith"
    )

with col2:

    guest_email = st.text_input(
        "Guest Email",
        placeholder="guest@email.com"
    )

col1, col2, col3, col4 = st.columns(4)

with col1:

    arrival = st.date_input(
        "Arrival",
        value=date.today(),
        format="MM/DD/YYYY"
    )

with col2:

    departure = st.date_input(
        "Departure",
        value=date.today(),
        format="MM/DD/YYYY"
    )

with col3:

    adults = st.number_input(
        "Adults",
        min_value=1,
        max_value=20,
        value=2
    )

with col4:

    children = st.number_input(
        "Children",
        min_value=0,
        max_value=20,
        value=0
    )

if departure >= arrival:

    nights = (
        departure - arrival
    ).days

else:

    nights = 0
    st.error(
        "Departure must be after Arrival."
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# OPCIONES
# ============================================================

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">Quotation Options</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Choose how many accommodation options you want to include in the email.'
    '</div>',
    unsafe_allow_html=True
)

number_options = st.radio(
    "Number of quotation options",
    options=[1, 2, 3],
    horizontal=True,
    index=0
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# CREACIÓN DE OPCIONES
# ============================================================

options = []

for option_number in range(1, number_options + 1):

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="option-title">
            Option {option_number}
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [2.2, 1.2, 1.2]
    )

    with col1:

        room = st.selectbox(
            "Room Type",
            options=list(ROOM_TYPES.keys()),
            key=f"room_{option_number}"
        )

    with col2:

        plan = st.selectbox(
            "Plan",
            options=list(MEAL_PLANS.keys()),
            key=f"plan_{option_number}"
        )

    with col3:

        valid_until = st.date_input(
            "Quote Valid Until",
            value=date.today(),
            key=f"valid_until_{option_number}",
            format="MM/DD/YYYY"
        )

    col1, col2 = st.columns(2)

    with col1:

        rate_before = st.number_input(
            "Rate Per Night Before Taxes",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key=f"rate_before_{option_number}"
        )

    with col2:

        rate_tax = st.number_input(
            "Rate Per Night Taxes Included",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key=f"rate_tax_{option_number}"
        )

    # --------------------------------------------------------
    # INCLUSIONES
    # --------------------------------------------------------

    default_includes = (
        ROOM_TYPES[room]["default_includes"]
        +
        MEAL_PLANS[plan]["includes"]
    )

    # Eliminamos duplicados manteniendo orden

    unique_includes = []

    for item in default_includes:

        if item not in unique_includes:
            unique_includes.append(item)

    default_text = "\n".join(
        unique_includes
    )

    include_key = f"includes_{option_number}"

    if include_key not in st.session_state:

        st.session_state[include_key] = default_text

    includes_text = st.text_area(
        "Included Values",
        key=include_key,
        height=130,
        help=(
            "One inclusion per line. "
            "You can freely modify these values."
        )
    )

    # --------------------------------------------------------
    # LINKS
    # --------------------------------------------------------

    st.markdown(
        '<div class="small-label">Optional Links</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        include_360 = st.checkbox(
            "Include 360° Room View",
            key=f"include_360_{option_number}"
        )

        room_360 = ""

        if include_360:

            # Si la habitación ya tiene un link configurado,
            # lo ponemos automáticamente.

            room_360 = st.text_input(
                "360° Room URL",
                value=ROOM_TYPES[room].get(
                    "360_url",
                    ""
                ),
                key=f"room_360_{option_number}",
                placeholder="https://..."
            )

    with col2:

        include_payment = st.checkbox(
            "Include Payment Link",
            key=f"include_payment_{option_number}"
        )

        payment_link = ""

        if include_payment:

            payment_link = st.text_input(
                "Payment URL",
                key=f"payment_{option_number}",
                placeholder="https://..."
            )

    # --------------------------------------------------------
    # SERVICIO ADICIONAL
    # --------------------------------------------------------

    include_additional = st.checkbox(
        "Include Additional Service",
        key=f"include_additional_{option_number}"
    )

    additional_description = ""
    additional_amount = 0.0

    if include_additional:

        col1, col2 = st.columns(2)

        with col1:

            additional_description = st.text_input(
                "Service Description",
                placeholder="Airport Transportation"
            )

        with col2:

            additional_amount = st.number_input(
                "Service Amount",
                min_value=0.0,
                step=10.0,
                key=f"additional_amount_{option_number}"
            )

    options.append(
        {
            "room": room,
            "plan": plan,
            "valid_until": valid_until,
            "rate_before": rate_before,
            "rate_tax": rate_tax,
            "includes": text_to_includes(
                includes_text
            ),
            "room_360": room_360
                if include_360
                else "",
            "payment_link": payment_link
                if include_payment
                else "",
            "additional_description":
                additional_description,
            "additional_amount":
                additional_amount,
        }
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# ARCHIVOS
# ============================================================

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">Attachments</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Optional files to attach to the email.'
    '</div>',
    unsafe_allow_html=True
)

uploaded_files = st.file_uploader(
    "Upload files",
    accept_multiple_files=True,
    type=[
        "pdf",
        "jpg",
        "jpeg",
        "png",
        "doc",
        "docx",
        "xls",
        "xlsx"
    ]
)

attachments = []

if uploaded_files:

    for file in uploaded_files:

        attachments.append(
            {
                "name": file.name,
                "type": file.type,
                "data": file.getvalue(),
            }
        )

        st.write(
            f"✓ {file.name}"
        )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# PREPARAR HTML
# ============================================================

email_subject = (
    "Special Quotation | Casa Dorada Los Cabos"
)

email_html = create_email_html(
    guest_name=guest_name or "Guest",
    arrival=arrival,
    departure=departure,
    nights=nights,
    adults=adults,
    children=children,
    options=options,
    deposit_policy=deposit_policy,
    cancellation_policy=cancellation_policy,
)


# ============================================================
# PREVIEW
# ============================================================

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">Quotation Preview</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'This is how the quotation will appear in the email.'
    '</div>',
    unsafe_allow_html=True
)

st.components.v1.html(
    email_html,
    height=1000,
    scrolling=True
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# ACTIONS
# ============================================================

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">Email Actions</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    save_draft_button = st.button(
        "Save to Gmail Drafts",
        use_container_width=True
    )

with col2:

    send_button = st.button(
        "Send Email",
        use_container_width=True
    )


# ============================================================
# VALIDACIÓN
# ============================================================

if save_draft_button or send_button:

    if not guest_email:

        st.error(
            "Please enter the guest email."
        )

        st.stop()

    if "@" not in guest_email:

        st.error(
            "Please enter a valid email address."
        )

        st.stop()

    if nights <= 0:

        st.error(
            "Please verify the arrival and departure dates."
        )

        st.stop()

    credentials = get_credentials()

    if not credentials:

        st.error(
            "Please connect your Google account first."
        )

        st.stop()

    service = get_gmail_service()

    if not service:

        st.error(
            "Could not connect to Gmail."
        )

        st.stop()

    sender_email = get_connected_email()

    if not sender_email:

        st.error(
            "Could not identify the connected Gmail account."
        )

        st.stop()

    message = create_email_message(
        sender=sender_email,
        recipient=guest_email,
        subject=email_subject,
        html_body=email_html,
        attachments=attachments
    )

    # --------------------------------------------------------
    # SAVE DRAFT
    # --------------------------------------------------------

    if save_draft_button:

        try:

            result = save_gmail_draft(
                service,
                message
            )

            st.success(
                "✓ Quotation saved successfully in Gmail Drafts."
            )

            st.info(
                f"Draft created in: {sender_email}"
            )

        except Exception as e:

            st.error(
                f"Could not save the draft: {e}"
            )

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    if send_button:

        try:

            result = send_gmail_message(
                service,
                message
            )

            st.success(
                f"✓ Email sent successfully from {sender_email}."
            )

        except Exception as e:

            st.error(
                f"Could not send the email: {e}"
            )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)

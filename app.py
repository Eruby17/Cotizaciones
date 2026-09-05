import streamlit as st
import base64
import hashlib
import hmac
import json
import secrets
from datetime import date, datetime
from email.message import EmailMessage
from urllib.parse import urlencode

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Cotizador Casa Dorada",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# GOOGLE OAUTH
# ============================================================

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.compose",
]


# ============================================================
# CONFIGURACIÓN DE HABITACIONES
# ============================================================

ROOM_TYPES = {
    "Junior Suite": {
        "default_inclusions": [
            "Accommodation",
            "Daily breakfast",
            "WiFi",
        ],
        "360_url": "",
    },

    "One Bedroom Suite": {
        "default_inclusions": [
            "Accommodation",
            "Daily breakfast",
            "WiFi",
        ],
        "360_url": "",
    },

    "One Bedroom Plus w/ Jacuzzi": {
        "default_inclusions": [
            "Accommodation",
            "Daily breakfast",
            "WiFi",
        ],
        "360_url": "",
    },

    "Executive Suite": {
        "default_inclusions": [
            "Accommodation",
            "Daily breakfast",
            "WiFi",
        ],
        "360_url": "",
    },

    "Two Bedroom Suite": {
        "default_inclusions": [
            "Accommodation",
            "Daily breakfast",
            "WiFi",
        ],
        "360_url": "",
    },

    "One Bedroom Penthouse": {
        "default_inclusions": [
            "Accommodation",
            "Daily breakfast",
            "WiFi",
        ],
        "360_url": "",
    },
}


# ============================================================
# PLANES
# ============================================================

MEAL_PLANS = {
    "EP": {
        "name": "European Plan",
        "default_inclusions": [
            "Accommodation",
            "Daily breakfast",
        ],
    },

    "AI": {
        "name": "All Inclusive",
        "default_inclusions": [
            "Accommodation",
            "All Inclusive",
            "Food and beverages",
            "Domestic beverages",
        ],
    },
}


# ============================================================
# LISTA CENTRAL DE BENEFICIOS
#
# AQUÍ PUEDES AGREGAR / QUITAR BENEFICIOS
# ============================================================

AVAILABLE_INCLUSIONS = [
    "Accommodation",
    "Daily breakfast",
    "All Inclusive",
    "Food and beverages",
    "Domestic beverages",
    "WiFi",
    "Airport transportation",
    "Welcome amenity",
]


# ============================================================
# LOGO
#
# SOLO SE UTILIZA DENTRO DEL EMAIL
# ============================================================

EMAIL_LOGO_URL = (
    "https://umutu.com/wp-content/uploads/2021/02/Logo-2-3.png"
)


# ============================================================
# POLÍTICAS
# ============================================================

DEFAULT_POLICIES = """
Reservation is guaranteed with first night deposit.

The remaining balance is due 45 days prior to arrival.

Non refundable rates cannot be cancelled or modified.

All reservations are subject to hotel availability and confirmation.
"""


# ============================================================
# ESTILOS DE LA APLICACIÓN
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at top right,
                rgba(43, 70, 100, 0.25),
                transparent 35%
            ),
            #111827;
        color: #f3f4f6;
    }

    .main {
        background: transparent;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {
        background: #0b1220;
        border-right: 1px solid #263244;
    }

    section[data-testid="stSidebar"] * {
        color: #f3f4f6;
    }


    /* ======================================================
       INPUTS
       ====================================================== */

    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        background-color: #182235 !important;
        border-color: #334155 !important;
    }

    input,
    textarea {
        color: #f8fafc !important;
    }

    div[data-baseweb="select"] span {
        color: #f8fafc !important;
    }

    label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }


    /* ======================================================
       TÍTULOS
       ====================================================== */

    h1, h2, h3, h4 {
        color: #f8fafc !important;
    }


    /* ======================================================
       CARDS
       ====================================================== */

    .dark-card {
        background: #182235;
        border: 1px solid #2c3a4f;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
    }

    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 14px;
    }

    .section-subtitle {
        color: #94a3b8;
        font-size: 13px;
        margin-bottom: 15px;
    }


    /* ======================================================
       OPTION CARD
       ====================================================== */

    .option-header {
        background: linear-gradient(
            135deg,
            #22324a,
            #1b2739
        );
        border: 1px solid #34445c;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 15px;
    }

    .option-number {
        font-size: 17px;
        font-weight: 700;
        color: #ffffff;
    }

    .option-description {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 3px;
    }


    /* ======================================================
       CHECKBOXES
       ====================================================== */

    div[data-testid="stCheckbox"] {
        background: #141e2f;
        border: 1px solid #27364b;
        border-radius: 8px;
        padding: 6px 10px;
        margin-bottom: 5px;
    }

    div[data-testid="stCheckbox"]:hover {
        border-color: #64748b;
        background: #1b293d;
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    .stButton > button {
        border-radius: 9px;
        border: 1px solid #475569;
        background: #1e293b;
        color: #f8fafc;
        font-weight: 600;
        min-height: 42px;
    }

    .stButton > button:hover {
        border-color: #94a3b8;
        color: #ffffff;
    }


    /* ======================================================
       STATUS
       ====================================================== */

    .connected-box {
        background: rgba(22, 163, 74, 0.12);
        border: 1px solid rgba(34, 197, 94, 0.35);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 15px;
    }

    .connected-title {
        color: #86efac;
        font-weight: 700;
        font-size: 14px;
    }

    .connected-email {
        color: #bbf7d0;
        font-size: 13px;
        margin-top: 3px;
        word-break: break-all;
    }


    /* ======================================================
       PREVIEW
       ====================================================== */

    .preview-wrapper {
        background: #0b1220;
        border: 1px solid #2c3a4f;
        border-radius: 14px;
        padding: 18px;
    }

    .preview-title {
        color: #f8fafc;
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 12px;
    }


    /* ======================================================
       DIVIDER
       ====================================================== */

    hr {
        border-color: #293548 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPERS OAUTH
# ============================================================

def b64url_encode(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def b64url_decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def get_oauth_config():

    config = st.secrets["google_oauth"]

    return {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
    }


def get_state_secret():

    config = get_oauth_config()

    return config["client_secret"].encode("utf-8")


def sign_state(payload):

    payload_json = json.dumps(
        payload,
        separators=(",", ":")
    ).encode("utf-8")

    encoded = b64url_encode(payload_json)

    signature = hmac.new(
        get_state_secret(),
        encoded.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return encoded + "." + b64url_encode(signature)


def verify_state(state):

    try:

        encoded, signature = state.split(".", 1)

        expected = hmac.new(
            get_state_secret(),
            encoded.encode("utf-8"),
            hashlib.sha256
        ).digest()

        received = b64url_decode(signature)

        if not hmac.compare_digest(expected, received):
            return None

        payload = json.loads(
            b64url_decode(encoded).decode("utf-8")
        )

        return payload

    except Exception:
        return None


def create_oauth_flow(code_verifier=None):

    config = get_oauth_config()

    client_config = {
        "web": {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                config["redirect_uri"]
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=config["redirect_uri"],
    )

    if code_verifier:
        flow.code_verifier = code_verifier

    return flow


def get_google_login_url():

    code_verifier = (
        secrets.token_urlsafe(64)
        .replace("-", "")
        .replace("_", "")
    )

    flow = create_oauth_flow(
        code_verifier=code_verifier
    )

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            code_challenge_method="S256",
            code_challenge=(
                hashlib.sha256(
                    code_verifier.encode("utf-8")
                ).digest()
            )
        )
    )

    payload = {
        "oauth_state": state,
        "code_verifier": code_verifier,
        "created_at": datetime.utcnow().timestamp(),
    }

    signed_state = sign_state(payload)

    parsed = authorization_url.split("?")[0]

    query = urlencode({
        "client_id": get_oauth_config()["client_id"],
        "redirect_uri": get_oauth_config()["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": signed_state,
        "code_challenge": b64url_encode(
            hashlib.sha256(
                code_verifier.encode("utf-8")
            ).digest()
        ),
        "code_challenge_method": "S256",
    })

    return parsed + "?" + query


def process_google_callback():

    query_params = st.query_params

    code = query_params.get("code")
    state = query_params.get("state")

    if not code or not state:
        return False

    payload = verify_state(state)

    if not payload:
        st.error(
            "No fue posible validar la sesión de Google."
        )
        return False

    code_verifier = payload.get("code_verifier")

    if not code_verifier:
        st.error(
            "No se encontró el código de seguridad de OAuth."
        )
        return False

    try:

        flow = create_oauth_flow(
            code_verifier=code_verifier
        )

        flow.fetch_token(
            code=code,
            code_verifier=code_verifier
        )

        credentials = flow.credentials

        st.session_state.google_credentials = (
            credentials_to_dict(credentials)
        )

        st.session_state.google_connected = True

        st.query_params.clear()

        return True

    except Exception as e:

        st.error(
            f"Error conectando con Google: {e}"
        )

        return False


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

    credentials_data = st.session_state.get(
        "google_credentials"
    )

    if not credentials_data:
        return None

    credentials = Credentials(
        token=credentials_data.get("token"),
        refresh_token=credentials_data.get(
            "refresh_token"
        ),
        token_uri=credentials_data.get(
            "token_uri"
        ),
        client_id=credentials_data.get(
            "client_id"
        ),
        client_secret=credentials_data.get(
            "client_secret"
        ),
        scopes=credentials_data.get(
            "scopes"
        ),
    )

    if credentials.expired and credentials.refresh_token:

        try:

            credentials.refresh(Request())

            st.session_state.google_credentials = (
                credentials_to_dict(credentials)
            )

        except Exception:

            return None

    return credentials


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
# EMAIL
# ============================================================

def html_escape(value):

    if value is None:
        return ""

    value = str(value)

    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def money(value):

    try:

        return "${:,.2f} USD".format(
            float(value)
        )

    except Exception:

        return "$0.00 USD"


def format_date_email(value):

    if not value:
        return ""

    try:

        if isinstance(value, date):
            d = value
        else:
            d = datetime.strptime(
                str(value),
                "%Y-%m-%d"
            ).date()

        return d.strftime(
            "%B %d, %Y"
        )

    except Exception:

        return str(value)


def calculate_total(
    nightly_rate,
    nights,
    taxes_included
):

    try:

        nightly = float(nightly_rate)

    except Exception:

        nightly = 0

    try:

        number_nights = int(nights)

    except Exception:

        number_nights = 0

    total_before_taxes = (
        nightly * number_nights
    )

    if taxes_included:

        return total_before_taxes

    return total_before_taxes * 1.30


def build_option_html(
    option_number,
    room_type,
    plan,
    valid_until,
    nightly_rate,
    taxes_included,
    selected_inclusions,
    payment_url,
    room_360_url,
    additional_service,
    nights,
):

    rate_label = (
        "Rate taxes included"
        if taxes_included
        else "Rate before taxes"
    )

    total = calculate_total(
        nightly_rate,
        nights,
        taxes_included
    )

    if taxes_included:
        total_label = "Stay total"
    else:
        total_label = "Stay total including taxes"

    inclusions_html = ""

    if selected_inclusions:

        for inclusion in selected_inclusions:

            inclusions_html += f"""
            <li style="
                margin-bottom:7px;
                color:#444444;
                font-size:14px;
                line-height:1.4;
            ">
                {html_escape(inclusion)}
            </li>
            """

    else:

        inclusions_html = """
        <li style="
            margin-bottom:7px;
            color:#777777;
            font-size:14px;
        ">
            No inclusions selected
        </li>
        """

    buttons_html = ""

    if room_360_url:

        buttons_html += f"""
        <a href="{html_escape(room_360_url)}"
           target="_blank"
           style="
               display:inline-block;
               background:#ffffff;
               color:#1f4f78;
               border:1px solid #1f4f78;
               text-decoration:none;
               padding:11px 18px;
               border-radius:5px;
               font-size:13px;
               font-weight:bold;
               margin-right:7px;
           ">
           VIEW ROOM
        </a>
        """

    if payment_url:

        buttons_html += f"""
        <a href="{html_escape(payment_url)}"
           target="_blank"
           style="
               display:inline-block;
               background:#c9a227;
               color:#ffffff;
               text-decoration:none;
               padding:12px 18px;
               border-radius:5px;
               font-size:13px;
               font-weight:bold;
           ">
           SECURE YOUR BOOKING
        </a>
        """

    additional_service_html = ""

    if additional_service:

        additional_service_html = f"""
        <tr>
            <td style="
                padding:6px 0;
                color:#555555;
                font-size:14px;
            ">
                Additional services
            </td>

            <td style="
                padding:6px 0;
                color:#222222;
                font-size:14px;
                text-align:right;
            ">
                {html_escape(additional_service)}
            </td>
        </tr>
        """

    return f"""

    <table width="100%"
           cellpadding="0"
           cellspacing="0"
           border="0"
           style="
               border:1px solid #dddddd;
               border-radius:8px;
               margin-bottom:22px;
               background:#ffffff;
           ">

        <tr>
            <td style="
                padding:20px;
            ">

                <div style="
                    color:#1f4f78;
                    font-size:18px;
                    font-weight:bold;
                    margin-bottom:5px;
                ">
                    Option {option_number}
                </div>

                <div style="
                    color:#333333;
                    font-size:20px;
                    font-weight:bold;
                    margin-bottom:3px;
                ">
                    {html_escape(room_type)}
                </div>

                <div style="
                    color:#777777;
                    font-size:13px;
                    margin-bottom:18px;
                ">
                    {html_escape(plan)}
                </div>


                <table width="100%"
                       cellpadding="0"
                       cellspacing="0"
                       border="0">

                    <tr>
                        <td style="
                            padding:6px 0;
                            color:#555555;
                            font-size:14px;
                        ">
                            {html_escape(rate_label)}
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(nightly_rate)}
                            / night
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding:6px 0;
                            color:#555555;
                            font-size:14px;
                        ">
                            Number of nights
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                        ">
                            {html_escape(nights)}
                        </td>
                    </tr>

                    {additional_service_html}

                </table>


                <div style="
                    margin-top:20px;
                    margin-bottom:8px;
                    color:#1f4f78;
                    font-size:15px;
                    font-weight:bold;
                ">
                    Included
                </div>

                <ul style="
                    padding-left:22px;
                    margin-top:8px;
                    margin-bottom:20px;
                ">
                    {inclusions_html}
                </ul>


                <div style="
                    border-top:1px solid #eeeeee;
                    padding-top:15px;
                ">

                    <table width="100%"
                           cellpadding="0"
                           cellspacing="0"
                           border="0">

                        <tr>

                            <td style="
                                color:#555555;
                                font-size:14px;
                            ">
                                {html_escape(total_label)}
                            </td>

                            <td style="
                                color:#222222;
                                font-size:17px;
                                font-weight:bold;
                                text-align:right;
                            ">
                                {money(total)}
                            </td>

                        </tr>

                    </table>

                </div>


                <div style="
                    margin-top:20px;
                ">
                    {buttons_html}
                </div>


                <div style="
                    margin-top:16px;
                    color:#777777;
                    font-size:12px;
                ">
                    Quote valid until:
                    <strong>
                        {html_escape(
                            format_date_email(valid_until)
                        )}
                    </strong>
                </div>

            </td>
        </tr>

    </table>

    """


def build_email_html(
    guest_name,
    arrival,
    departure,
    adults,
    children,
    nights,
    options,
    policies,
):

    options_html = ""

    for index, option in enumerate(
        options,
        start=1
    ):

        options_html += build_option_html(
            option_number=index,
            room_type=option["room_type"],
            plan=option["plan"],
            valid_until=option["valid_until"],
            nightly_rate=option["nightly_rate"],
            taxes_included=option["taxes_included"],
            selected_inclusions=option[
                "selected_inclusions"
            ],
            payment_url=option["payment_url"],
            room_360_url=option["room_360_url"],
            additional_service=option[
                "additional_service"
            ],
            nights=nights,
        )


    children_text = ""

    if children > 0:

        children_text = f"""
        <tr>
            <td style="
                padding:5px 0;
                color:#666666;
                font-size:14px;
            ">
                Children
            </td>

            <td style="
                padding:5px 0;
                color:#222222;
                font-size:14px;
                text-align:right;
            ">
                {html_escape(children)}
            </td>
        </tr>
        """


    policies_html = ""

    for line in policies.splitlines():

        line = line.strip()

        if line:

            policies_html += f"""
            <li style="
                margin-bottom:8px;
                color:#555555;
                font-size:13px;
                line-height:1.5;
            ">
                {html_escape(line)}
            </li>
            """


    return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0">

<title>Your Custom Quotation</title>

</head>


<body style="
    margin:0;
    padding:0;
    background:#f3f4f6;
    font-family:Arial,Helvetica,sans-serif;
">

<table width="100%"
       cellpadding="0"
       cellspacing="0"
       border="0">

<tr>

<td align="center"
    style="padding:30px 10px;">

<table width="600"
       cellpadding="0"
       cellspacing="0"
       border="0"
       style="
           width:600px;
           max-width:100%;
           background:#ffffff;
           border-radius:8px;
           overflow:hidden;
           box-shadow:
               0 2px 8px rgba(0,0,0,0.08);
       ">


<!-- HEADER -->

<tr>

<td align="center"
    style="
        background:#ffffff;
        padding:25px 25px 15px 25px;
    ">

<img src="{EMAIL_LOGO_URL}"
     alt="Casa Dorada"
     style="
         max-width:220px;
         width:100%;
         height:auto;
         display:block;
     ">

</td>

</tr>


<!-- TITLE -->

<tr>

<td style="
    padding:15px 35px 5px 35px;
    text-align:center;
">

<div style="
    color:#1f4f78;
    font-size:25px;
    font-weight:bold;
">

Your Custom Quotation

</div>

</td>

</tr>


<!-- GREETING -->

<tr>

<td style="
    padding:15px 35px 10px 35px;
">

<p style="
    color:#333333;
    font-size:15px;
    line-height:1.6;
    margin:0 0 12px 0;
">

Dear {html_escape(guest_name)},

</p>

<p style="
    color:#555555;
    font-size:14px;
    line-height:1.6;
    margin:0;
">

Thank you for considering
Casa Dorada Los Cabos Resort & Spa
for your upcoming stay.

Please find below your personalized
quotation and available options.

</p>

</td>

</tr>


<!-- STAY DETAILS -->

<tr>

<td style="
    padding:15px 35px;
">

<table width="100%"
       cellpadding="0"
       cellspacing="0"
       border="0"
       style="
           background:#f7f7f7;
           border-radius:6px;
           padding:15px;
       ">

<tr>

<td style="
    padding:5px 0;
    color:#666666;
    font-size:14px;
">

Arrival

</td>

<td style="
    padding:5px 0;
    color:#222222;
    font-size:14px;
    text-align:right;
    font-weight:bold;
">

{html_escape(
    format_date_email(arrival)
)}

</td>

</tr>


<tr>

<td style="
    padding:5px 0;
    color:#666666;
    font-size:14px;
">

Departure

</td>

<td style="
    padding:5px 0;
    color:#222222;
    font-size:14px;
    text-align:right;
    font-weight:bold;
">

{html_escape(
    format_date_email(departure)
)}

</td>

</tr>


<tr>

<td style="
    padding:5px 0;
    color:#666666;
    font-size:14px;
">

Adults

</td>

<td style="
    padding:5px 0;
    color:#222222;
    font-size:14px;
    text-align:right;
">

{html_escape(adults)}

</td>

</tr>


{children_text}


<tr>

<td style="
    padding:5px 0;
    color:#666666;
    font-size:14px;
">

Nights

</td>

<td style="
    padding:5px 0;
    color:#222222;
    font-size:14px;
    text-align:right;
">

{html_escape(nights)}

</td>

</tr>

</table>

</td>

</tr>


<!-- OPTIONS -->

<tr>

<td style="
    padding:15px 35px 5px 35px;
">

<div style="
    color:#1f4f78;
    font-size:19px;
    font-weight:bold;
    margin-bottom:15px;
">

Available Options

</div>

{options_html}

</td>

</tr>


<!-- POLICIES -->

<tr>

<td style="
    padding:10px 35px 30px 35px;
">

<div style="
    color:#1f4f78;
    font-size:18px;
    font-weight:bold;
    margin-bottom:10px;
">

Booking Policies

</div>

<ul style="
    margin:0;
    padding-left:20px;
">

{policies_html}

</ul>

</td>

</tr>


<!-- FOOTER -->

<tr>

<td style="
    background:#1f4f78;
    padding:22px 30px;
    text-align:center;
">

<div style="
    color:#ffffff;
    font-size:14px;
    font-weight:bold;
    margin-bottom:6px;
">

Casa Dorada Los Cabos Resort & Spa

</div>

<div style="
    color:#dbeafe;
    font-size:12px;
    line-height:1.5;
">

Medano Beach, Cabo San Lucas, Mexico

</div>

</td>

</tr>


</table>

</td>

</tr>

</table>

</body>

</html>
"""


# ============================================================
# GMAIL MESSAGE
# ============================================================

def create_gmail_message(
    to_email,
    subject,
    html_body,
    attachments=None,
):

    message = EmailMessage()

    message["To"] = to_email
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

            file_name = attachment.name

            file_bytes = attachment.getvalue()

            mime_type = attachment.type or (
                "application/octet-stream"
            )

            if "/" in mime_type:

                maintype, subtype = (
                    mime_type.split("/", 1)
                )

            else:

                maintype = "application"
                subtype = "octet-stream"

            message.add_attachment(
                file_bytes,
                maintype=maintype,
                subtype=subtype,
                filename=file_name,
            )

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    return {
        "raw": encoded_message
    }


def save_gmail_draft(
    to_email,
    subject,
    html_body,
    attachments=None,
):

    service = get_gmail_service()

    if not service:
        raise Exception(
            "No hay una cuenta de Gmail conectada."
        )

    message = create_gmail_message(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        attachments=attachments,
    )

    draft = {
        "message": message
    }

    return (
        service.users()
        .drafts()
        .create(
            userId="me",
            body=draft
        )
        .execute()
    )


def send_gmail_message(
    to_email,
    subject,
    html_body,
    attachments=None,
):

    service = get_gmail_service()

    if not service:
        raise Exception(
            "No hay una cuenta de Gmail conectada."
        )

    message = create_gmail_message(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        attachments=attachments,
    )

    return (
        service.users()
        .messages()
        .send(
            userId="me",
            body=message
        )
        .execute()
    )


# ============================================================
# SESSION STATE
# ============================================================

if "google_connected" not in st.session_state:

    st.session_state.google_connected = False


if "google_credentials" not in st.session_state:

    st.session_state.google_credentials = None


# ============================================================
# PROCESAR CALLBACK DE GOOGLE
# ============================================================

if "code" in st.query_params and "state" in st.query_params:

    process_google_callback()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size:20px;
            font-weight:700;
            margin-bottom:18px;
            color:#f8fafc;
        ">
            Gmail
        </div>
        """,
        unsafe_allow_html=True
    )


    connected_email = get_connected_email()


    if connected_email:

        st.markdown(
            f"""
            <div class="connected-box">

                <div class="connected-title">
                    ✓ Connected
                </div>

                <div class="connected-email">
                    {html_escape(connected_email)}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        login_url = get_google_login_url()

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
                   background:#2563eb;
                   color:white;
                   padding:12px 10px;
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
            "Google se abrirá en una nueva pestaña."
        )


    st.divider()


    st.markdown(
        """
        <div style="
            font-size:16px;
            font-weight:700;
            color:#f8fafc;
            margin-bottom:12px;
        ">
            Quote Settings
        </div>
        """,
        unsafe_allow_html=True
    )


    number_options = st.selectbox(
        "Number of quotation options",
        options=[1, 2, 3],
        index=0,
    )


    st.divider()


    st.markdown(
        """
        <div style="
            color:#94a3b8;
            font-size:12px;
            line-height:1.5;
        ">
        Cada opción puede tener habitación,
        tarifa, beneficios, link de pago y
        vista 360° diferentes.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# TÍTULO PRINCIPAL
# ============================================================

st.markdown(
    """
    <h1 style="
        margin-bottom:5px;
        font-size:28px;
    ">
        Create Quotation
    </h1>

    <div style="
        color:#94a3b8;
        font-size:14px;
        margin-bottom:25px;
    ">
        Create a professional quotation and
        save it directly to your Casa Dorada Gmail.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATOS DEL HUÉSPED
# ============================================================

st.markdown(
    """
    <div class="dark-card">

        <div class="section-title">
            Guest Information
        </div>

        <div class="section-subtitle">
            Basic information for the quotation.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


guest_col1, guest_col2 = st.columns(2)

with guest_col1:

    guest_name = st.text_input(
        "Guest name",
        placeholder="John Smith"
    )

with guest_col2:

    guest_email = st.text_input(
        "Guest email",
        placeholder="guest@email.com"
    )


guest_col3, guest_col4 = st.columns(2)

with guest_col3:

    arrival = st.date_input(
        "Arrival",
        value=date.today()
    )

with guest_col4:

    departure = st.date_input(
        "Departure",
        value=date.today()
    )


guest_col5, guest_col6, guest_col7 = st.columns(3)

with guest_col5:

    adults = st.number_input(
        "Adults",
        min_value=1,
        max_value=20,
        value=2,
        step=1
    )

with guest_col6:

    children = st.number_input(
        "Children",
        min_value=0,
        max_value=20,
        value=0,
        step=1
    )

with guest_col7:

    calculated_nights = (
        departure - arrival
    ).days

    if calculated_nights < 1:
        calculated_nights = 1

    nights = st.number_input(
        "Nights",
        min_value=1,
        max_value=365,
        value=calculated_nights,
        step=1
    )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# OPCIONES DE COTIZACIÓN
# ============================================================

all_options = []


for option_number in range(
    1,
    number_options + 1
):

    st.markdown(
        f"""
        <div class="dark-card">

            <div class="option-header">

                <div class="option-number">
                    Quotation Option {option_number}
                </div>

                <div class="option-description">
                    Configure this option independently.
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # ROOM + PLAN
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        room_type = st.selectbox(
            "Room type",
            options=list(
                ROOM_TYPES.keys()
            ),
            key=f"room_type_{option_number}",
        )


    with col2:

        plan_code = st.selectbox(
            "Meal plan",
            options=list(
                MEAL_PLANS.keys()
            ),
            format_func=lambda x:
                MEAL_PLANS[x]["name"],
            key=f"plan_{option_number}",
        )


    # --------------------------------------------------------
    # RATE
    # --------------------------------------------------------

    rate_col1, rate_col2, rate_col3 = (
        st.columns(3)
    )


    with rate_col1:

        nightly_rate = st.number_input(
            "Nightly rate (USD)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            format="%.2f",
            key=f"nightly_rate_{option_number}",
        )


    with rate_col2:

        taxes_included = st.checkbox(
            "Rate includes taxes",
            value=True,
            key=f"taxes_included_{option_number}",
        )


    with rate_col3:

        valid_until = st.date_input(
            "Quote valid until",
            value=date.today(),
            key=f"valid_until_{option_number}",
        )


    # --------------------------------------------------------
    # INCLUSIONS
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top:18px;
            margin-bottom:8px;
            font-size:15px;
            font-weight:700;
            color:#f8fafc;
        ">
            Included Benefits
        </div>

        <div style="
            color:#94a3b8;
            font-size:12px;
            margin-bottom:12px;
        ">
            Select independently what is included
            in this quotation option.
        </div>
        """,
        unsafe_allow_html=True
    )


    defaults = list(
        ROOM_TYPES[room_type][
            "default_inclusions"
        ]
    )

    for inclusion in MEAL_PLANS[
        plan_code
    ]["default_inclusions"]:

        if inclusion not in defaults:

            defaults.append(inclusion)


    signature = (
        f"{room_type}|"
        f"{plan_code}|"
        f"{'|'.join(AVAILABLE_INCLUSIONS)}"
    )


    signature_key = (
        f"inclusion_signature_"
        f"{option_number}"
    )


    previous_signature = st.session_state.get(
        signature_key
    )


    if previous_signature != signature:

        for index, inclusion in enumerate(
            AVAILABLE_INCLUSIONS
        ):

            checkbox_key = (
                f"inclusion_"
                f"{option_number}_"
                f"{index}"
            )

            st.session_state[
                checkbox_key
            ] = inclusion in defaults


        st.session_state[
            signature_key
        ] = signature


    inclusion_columns = st.columns(2)

    selected_inclusions = []


    for index, inclusion in enumerate(
        AVAILABLE_INCLUSIONS
    ):

        with inclusion_columns[
            index % 2
        ]:

            checkbox_key = (
                f"inclusion_"
                f"{option_number}_"
                f"{index}"
            )

            checked = st.checkbox(
                inclusion,
                key=checkbox_key,
            )

            if checked:

                selected_inclusions.append(
                    inclusion
                )


    # --------------------------------------------------------
    # OPTIONAL LINKS
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top:20px;
            margin-bottom:10px;
            font-size:15px;
            font-weight:700;
            color:#f8fafc;
        ">
            Optional Links
        </div>
        """,
        unsafe_allow_html=True
    )


    link_col1, link_col2 = st.columns(2)


    with link_col1:

        room_360_url = st.text_input(
            "360° room view link",
            value=ROOM_TYPES[
                room_type
            ].get("360_url", ""),
            placeholder="https://...",
            key=f"room_360_{option_number}",
        )


    with link_col2:

        payment_url = st.text_input(
            "Payment link",
            placeholder="https://...",
            key=f"payment_url_{option_number}",
        )


    # --------------------------------------------------------
    # ADDITIONAL SERVICE
    # --------------------------------------------------------

    additional_service = st.text_input(
        "Additional service",
        placeholder=(
            "Optional. Example: "
            "Roundtrip airport transportation"
        ),
        key=f"additional_service_{option_number}",
    )


    option_data = {
        "room_type": room_type,
        "plan": MEAL_PLANS[
            plan_code
        ]["name"],
        "valid_until": valid_until,
        "nightly_rate": nightly_rate,
        "taxes_included": taxes_included,
        "selected_inclusions": selected_inclusions,
        "payment_url": payment_url,
        "room_360_url": room_360_url,
        "additional_service": additional_service,
    }


    all_options.append(
        option_data
    )


    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )


# ============================================================
# POLÍTICAS
# ============================================================

st.markdown(
    """
    <div class="dark-card">

        <div class="section-title">
            Booking Policies
        </div>

        <div class="section-subtitle">
            These policies will appear at the bottom
            of the quotation email.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


policies = st.text_area(
    "Policies",
    value=DEFAULT_POLICIES,
    height=150,
)


# ============================================================
# GENERAR HTML
# ============================================================

email_html = build_email_html(
    guest_name=guest_name or "Guest",
    arrival=arrival,
    departure=departure,
    adults=adults,
    children=children,
    nights=nights,
    options=all_options,
    policies=policies,
)


# ============================================================
# PREVIEW
# ============================================================

st.markdown(
    "<br>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="preview-wrapper">

        <div class="preview-title">
            Email Preview
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


st.components.v1.html(
    email_html,
    height=(
        850 +
        (number_options * 500)
    ),
    scrolling=True,
)


# ============================================================
# ACCIONES
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

action_col1, action_col2 = st.columns(2)


subject = (
    f"Your Custom Quotation "
    f"Casa Dorada Los Cabos"
)


with action_col1:

    if st.button(
        "💾 Save Draft to Gmail",
        use_container_width=True,
    ):

        if not guest_email:

            st.error(
                "Please enter the guest email."
            )

        elif not get_gmail_service():

            st.error(
                "Please connect your Google Account first."
            )

        else:

            try:

                draft = save_gmail_draft(
                    to_email=guest_email,
                    subject=subject,
                    html_body=email_html,
                    attachments=None,
                )

                st.success(
                    "Draft saved successfully in Gmail."
                )

            except Exception as e:

                st.error(
                    f"Could not save draft: {e}"
                )


with action_col2:

    if st.button(
        "📤 Send Email",
        use_container_width=True,
    ):

        if not guest_email:

            st.error(
                "Please enter the guest email."
            )

        elif not get_gmail_service():

            st.error(
                "Please connect your Google Account first."
            )

        else:

            try:

                send_gmail_message(
                    to_email=guest_email,
                    subject=subject,
                    html_body=email_html,
                    attachments=None,
                )

                st.success(
                    "Email sent successfully."
                )

            except Exception as e:

                st.error(
                    f"Could not send email: {e}"
                )

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
    page_title="Casa Dorada Quotation",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURACIÓN DE GOOGLE
# ============================================================

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.compose",
]


# ============================================================
# IMPUESTOS
# ============================================================

TAX_RATE = 0.30


# ============================================================
# LOGO
# SOLO SE UTILIZA EN EL EMAIL
# ============================================================

EMAIL_LOGO_URL = (
    "https://umutu.com/wp-content/uploads/2021/02/Logo-2-3.png"
)


# ============================================================
# TIPOS DE HABITACIÓN
# ============================================================

ROOM_TYPES = {
    "Junior Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Breakfast Buffet at Maydan Restaurant",
        ],
        "360_url": "",
    },

    "One Bedroom Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Breakfast Buffet at Maydan Restaurant",
        ],
        "360_url": "",
    },

    "One Bedroom Plus w/ Jacuzzi": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Breakfast Buffet at Maydan Restaurant",
        ],
        "360_url": "",
    },

    "Executive Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Breakfast Buffet at Maydan Restaurant",
        ],
        "360_url": "",
    },

    "Two Bedroom Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Breakfast Buffet at Maydan Restaurant",
        ],
        "360_url": "",
    },

    "One Bedroom Penthouse": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Breakfast Buffet at Maydan Restaurant",
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
        "default_inclusions": [],
    },

    "AI": {
        "name": "All Inclusive",
        "default_inclusions": [
            "All Inclusive Package",
        ],
    },
}


# ============================================================
# BENEFICIOS
#
# PUEDES AGREGAR O QUITAR BENEFICIOS AQUÍ
# ============================================================

AVAILABLE_INCLUSIONS = [
    "Free Wi-Fi",

    "Free Valet Parking",

    "Free Breakfast Buffet at Maydan Restaurant",

    "30% discount on food and beverages "
    "(does not apply to room service, minibar, or other promotions)",

    "25% discount on food and beverages "
    "(does not apply to room service, minibar, or other promotions)",

    "25% discount at Saltwater Spa "
    "(50 and 80 minute massages)",

    "30% discount at Saltwater Spa "
    "(50 and 80 minute massages)",

    "All Inclusive Package",

    "30% Discount for Room Service",

    "Free Spa Access (Wet Areas)",

    "20% discount at Saltwater Spa "
    "(No Salon Services)",

    "Buy one Full Body Massage 80 minutes at Saltwater Spa "
    "and the second is free",

    "USD $100.00 Food and Beverage Credit "
    "(This credit is non-transferable and non-redeemable "
    "for cash, credits are non-cumulative, per reservation)",

    "USD $100.00 Dining Credit "
    "(This credit is non-transferable and non-redeemable "
    "for cash, credits are non-cumulative, per reservation)",

    "$100.00 USD Dinner Credit at 12 Tribes "
    "(This credit is non-transferable and non-redeemable "
    "for cash, credits are non-cumulative, per reservation)",

    "Round Trip Transportation",

    "One Way Transportation",

    "Romantic Three-Course Dinner on the Beach",

    "1 Seasonal Fruit Amenity per Stay",

    "12 drinks included per day "
    "(4 beers, 4 soft drinks and 4 bottles of water)",

    "1 bottle of house wine upon arrival per stay "
    "(bottle available in stock)",
]


# ============================================================
# SERVICIOS ADICIONALES
#
# LOS PRECIOS SON EN USD
# ============================================================

ADDITIONAL_SERVICES = {
    "Round Trip Transportation": 267.00,
    "One Way Transportation": 149.00,
    "Early Check In": 130.00,
    "Late Check Out": 130.00,
}


# ============================================================
# DEPOSIT POLICIES
# ============================================================

DEPOSIT_POLICIES = [
    "The deposit for the whole stay with taxes included "
    "is required upon booking.",

    "The deposit for the first night with taxes included "
    "is required upon booking.",
]


# ============================================================
# CANCELLATION POLICIES
# ============================================================

CANCELLATION_POLICIES = [

    "Non-refundable, no modifications are allowed. "
    "In case of early departure or no show, "
    "no reimbursement will apply.",

    "Reservations can be canceled 4 days before arrival "
    "free of charge. 1 night stay (tax included) penalty "
    "charge if canceled less than 4 days before arrival.",

    "Reservations can be canceled 14 days before arrival "
    "free of charge. 1 night stay (tax included) penalty "
    "charge if canceled less than 14 days before arrival.",

    "Reservations can be cancelled 45 days prior to arrival "
    "without charge. Full stay (tax included) charges "
    "penalty if cancelled less than 45 days prior to arrival. "
    "Time is based on the property's local time.",
]


# ============================================================
# CSS DE LA APLICACIÓN
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at top right,
                rgba(47, 73, 105, 0.25),
                transparent 35%
            ),
            #101827;
        color: #f8fafc;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }


    /* SIDEBAR */

    section[data-testid="stSidebar"] {
        background: #0a1220;
        border-right: 1px solid #273449;
    }

    section[data-testid="stSidebar"] * {
        color: #f8fafc;
    }


    /* INPUTS */

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


    /* CHECKBOXES */

    div[data-testid="stCheckbox"] {
        background: #151f30;
        border: 1px solid #2b394d;
        border-radius: 8px;
        padding: 6px 10px;
        margin-bottom: 6px;
    }

    div[data-testid="stCheckbox"]:hover {
        border-color: #64748b;
        background: #1b293d;
    }


    /* BUTTONS */

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
        color: white;
    }


    /* CONNECTION */

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


    /* OPTION */

    .option-card {
        background: #182235;
        border: 1px solid #2d3b50;
        border-radius: 14px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 20px;
    }


    /* PREVIEW */

    .preview-header {
        background: #0b1220;
        border: 1px solid #2d3b50;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
    }


    hr {
        border-color: #293548 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES OAUTH
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

    return get_oauth_config()[
        "client_secret"
    ].encode("utf-8")


def sign_state(payload):

    payload_json = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    encoded = b64url_encode(
        payload_json
    )

    signature = hmac.new(
        get_state_secret(),
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return (
        encoded
        + "."
        + b64url_encode(signature)
    )


def verify_state(state):

    try:

        encoded, signature = state.split(
            ".",
            1,
        )

        expected = hmac.new(
            get_state_secret(),
            encoded.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        received = b64url_decode(
            signature
        )

        if not hmac.compare_digest(
            expected,
            received,
        ):
            return None

        return json.loads(
            b64url_decode(
                encoded
            ).decode("utf-8")
        )

    except Exception:

        return None


def create_oauth_flow(
    code_verifier=None
):

    config = get_oauth_config()

    client_config = {
        "web": {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "auth_uri": (
                "https://accounts.google.com/"
                "o/oauth2/v2/auth"
            ),
            "token_uri": (
                "https://oauth2.googleapis.com/token"
            ),
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

    code_challenge = b64url_encode(
        hashlib.sha256(
            code_verifier.encode("utf-8")
        ).digest()
    )

    payload = {
        "code_verifier": code_verifier,
        "created_at": datetime.utcnow().timestamp(),
    }

    signed_state = sign_state(
        payload
    )

    config = get_oauth_config()

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": signed_state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    return (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(params)
    )


def process_google_callback():

    code = st.query_params.get("code")
    state = st.query_params.get("state")

    if not code or not state:

        return False

    payload = verify_state(state)

    if not payload:

        st.error(
            "No fue posible validar la sesión de Google."
        )

        return False

    code_verifier = payload.get(
        "code_verifier"
    )

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
            code_verifier=code_verifier,
        )

        credentials = flow.credentials

        st.session_state.google_credentials = (
            credentials_to_dict(
                credentials
            )
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

    data = st.session_state.get(
        "google_credentials"
    )

    if not data:

        return None

    credentials = Credentials(
        token=data.get("token"),
        refresh_token=data.get(
            "refresh_token"
        ),
        token_uri=data.get(
            "token_uri"
        ),
        client_id=data.get(
            "client_id"
        ),
        client_secret=data.get(
            "client_secret"
        ),
        scopes=data.get(
            "scopes"
        ),
    )

    if (
        credentials.expired
        and credentials.refresh_token
    ):

        try:

            credentials.refresh(
                Request()
            )

            st.session_state.google_credentials = (
                credentials_to_dict(
                    credentials
                )
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
        credentials=credentials,
    )


def get_connected_email():

    service = get_gmail_service()

    if not service:

        return None

    try:

        profile = (
            service.users()
            .getProfile(
                userId="me"
            )
            .execute()
        )

        return profile.get(
            "emailAddress"
        )

    except Exception:

        return None


# ============================================================
# FUNCIONES DE CÁLCULO
# ============================================================

def calculate_rate_values(
    stay_total_tax_included,
    nights,
):

    try:

        total_with_tax = float(
            stay_total_tax_included
        )

    except Exception:

        total_with_tax = 0.0

    try:

        number_nights = int(
            nights
        )

    except Exception:

        number_nights = 1

    if number_nights <= 0:

        number_nights = 1

    total_before_tax = (
        total_with_tax
        / (1 + TAX_RATE)
    )

    taxes = (
        total_with_tax
        - total_before_tax
    )

    nightly_with_tax = (
        total_with_tax
        / number_nights
    )

    nightly_before_tax = (
        total_before_tax
        / number_nights
    )

    return {
        "total_with_tax": total_with_tax,
        "total_before_tax": total_before_tax,
        "taxes": taxes,
        "nightly_with_tax": nightly_with_tax,
        "nightly_before_tax": nightly_before_tax,
    }


def money(value):

    try:

        return "${:,.2f} USD".format(
            float(value)
        )

    except Exception:

        return "$0.00 USD"


def html_escape(value):

    if value is None:

        return ""

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


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


# ============================================================
# EMAIL OPTION
# ============================================================

def build_option_html(
    option_number,
    room_type,
    plan,
    valid_until,
    nights,
    stay_total_tax_included,
    selected_inclusions,
    selected_services,
    deposit_policy,
    cancellation_policy,
    payment_url,
    room_360_url,
):

    calculations = calculate_rate_values(
        stay_total_tax_included,
        nights,
    )

    total_with_tax = calculations[
        "total_with_tax"
    ]

    total_before_tax = calculations[
        "total_before_tax"
    ]

    taxes = calculations[
        "taxes"
    ]

    nightly_with_tax = calculations[
        "nightly_with_tax"
    ]

    nightly_before_tax = calculations[
        "nightly_before_tax"
    ]


    # --------------------------------------------------------
    # BENEFICIOS
    # --------------------------------------------------------

    inclusions_html = ""

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


    if not inclusions_html:

        inclusions_html = """
        <li style="
            color:#777777;
            font-size:14px;
        ">
            No inclusions selected
        </li>
        """


    # --------------------------------------------------------
    # SERVICIOS
    # --------------------------------------------------------

    services_html = ""

    additional_services_total = 0.0


    for service in selected_services:

        price = ADDITIONAL_SERVICES[
            service
        ]

        additional_services_total += price

        services_html += f"""
        <tr>

            <td style="
                padding:6px 0;
                color:#555555;
                font-size:14px;
            ">
                {html_escape(service)}
            </td>

            <td style="
                padding:6px 0;
                color:#222222;
                font-size:14px;
                text-align:right;
            ">
                {money(price)}
            </td>

        </tr>
        """


    if not services_html:

        services_html = """
        <tr>

            <td colspan="2"
                style="
                    padding:6px 0;
                    color:#777777;
                    font-size:14px;
                ">
                No additional services
            </td>

        </tr>
        """


    final_total = (
        total_with_tax
        + additional_services_total
    )


    # --------------------------------------------------------
    # BOTONES
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

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
                    margin-bottom:4px;
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


                <!-- RATES -->

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
                            Rate per night before taxes
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                        ">
                            {money(nightly_before_tax)}
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:6px 0;
                            color:#555555;
                            font-size:14px;
                        ">
                            Rate per night taxes included
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(nightly_with_tax)}
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


                    <tr>

                        <td style="
                            padding:6px 0;
                            color:#555555;
                            font-size:14px;
                        ">
                            Stay total before taxes
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                        ">
                            {money(total_before_tax)}
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:6px 0;
                            color:#555555;
                            font-size:14px;
                        ">
                            Taxes
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                        ">
                            {money(taxes)}
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:8px 0;
                            color:#1f4f78;
                            font-size:15px;
                            font-weight:bold;
                        ">
                            Stay total taxes included
                        </td>

                        <td style="
                            padding:8px 0;
                            color:#1f4f78;
                            font-size:16px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(total_with_tax)}
                        </td>

                    </tr>


                </table>


                <!-- INCLUDED -->

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


                <!-- ADDITIONAL SERVICES -->

                <div style="
                    margin-top:20px;
                    margin-bottom:8px;
                    color:#1f4f78;
                    font-size:15px;
                    font-weight:bold;
                ">
                    Additional Services
                </div>


                <table width="100%"
                       cellpadding="0"
                       cellspacing="0"
                       border="0">

                    {services_html}


                    <tr>

                        <td style="
                            border-top:1px solid #eeeeee;
                            padding-top:10px;
                            color:#555555;
                            font-size:14px;
                            font-weight:bold;
                        ">
                            Additional services total
                        </td>

                        <td style="
                            border-top:1px solid #eeeeee;
                            padding-top:10px;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(additional_services_total)}
                        </td>

                    </tr>

                </table>


                <!-- FINAL TOTAL -->

                <div style="
                    margin-top:18px;
                    padding:15px;
                    background:#f5f7fa;
                    border-radius:6px;
                ">

                    <table width="100%"
                           cellpadding="0"
                           cellspacing="0"
                           border="0">

                        <tr>

                            <td style="
                                color:#1f4f78;
                                font-size:17px;
                                font-weight:bold;
                            ">
                                TOTAL AMOUNT
                            </td>

                            <td style="
                                color:#1f4f78;
                                font-size:20px;
                                font-weight:bold;
                                text-align:right;
                            ">
                                {money(final_total)}
                            </td>

                        </tr>

                    </table>

                </div>


                <!-- POLICIES -->

                <div style="
                    margin-top:20px;
                    padding-top:15px;
                    border-top:1px solid #eeeeee;
                ">

                    <div style="
                        color:#1f4f78;
                        font-size:14px;
                        font-weight:bold;
                        margin-bottom:6px;
                    ">
                        Deposit Policy
                    </div>

                    <div style="
                        color:#555555;
                        font-size:13px;
                        line-height:1.5;
                    ">
                        {html_escape(deposit_policy)}
                    </div>


                    <div style="
                        color:#1f4f78;
                        font-size:14px;
                        font-weight:bold;
                        margin-top:15px;
                        margin-bottom:6px;
                    ">
                        Cancellation Policy
                    </div>

                    <div style="
                        color:#555555;
                        font-size:13px;
                        line-height:1.5;
                    ">
                        {html_escape(cancellation_policy)}
                    </div>

                </div>


                <!-- BUTTONS -->

                <div style="
                    margin-top:20px;
                ">

                    {buttons_html}

                </div>


                <!-- VALID UNTIL -->

                <div style="
                    margin-top:16px;
                    color:#777777;
                    font-size:12px;
                ">

                    Quote valid until:
                    <strong>
                        {html_escape(
                            format_date_email(
                                valid_until
                            )
                        )}
                    </strong>

                </div>


            </td>

        </tr>

    </table>

    """


# ============================================================
# EMAIL COMPLETO
# ============================================================

def build_email_html(
    guest_name,
    arrival,
    departure,
    adults,
    children,
    nights,
    options,
):

    options_html = ""


    for index, option in enumerate(
        options,
        start=1,
    ):

        options_html += build_option_html(
            option_number=index,
            room_type=option["room_type"],
            plan=option["plan"],
            valid_until=option["valid_until"],
            nights=nights,
            stay_total_tax_included=option[
                "stay_total_tax_included"
            ],
            selected_inclusions=option[
                "selected_inclusions"
            ],
            selected_services=option[
                "selected_services"
            ],
            deposit_policy=option[
                "deposit_policy"
            ],
            cancellation_policy=option[
                "cancellation_policy"
            ],
            payment_url=option[
                "payment_url"
            ],
            room_360_url=option[
                "room_360_url"
            ],
        )


    children_html = ""


    if children > 0:

        children_html = f"""
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


    return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

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


<!-- LOGO -->

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


{children_html}


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
        subtype="html",
    )


    if attachments:

        for attachment in attachments:

            file_name = attachment.name
            file_bytes = attachment.getvalue()

            mime_type = (
                attachment.type
                or "application/octet-stream"
            )

            if "/" in mime_type:

                maintype, subtype = (
                    mime_type.split(
                        "/",
                        1,
                    )
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


    encoded_message = (
        base64.urlsafe_b64encode(
            message.as_bytes()
        )
        .decode()
    )

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

    return (
        service.users()
        .drafts()
        .create(
            userId="me",
            body={
                "message": message
            },
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
            body=message,
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
# CALLBACK GOOGLE
# ============================================================

if (
    "code" in st.query_params
    and "state" in st.query_params
):

    process_google_callback()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## Gmail"
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
            unsafe_allow_html=True,
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
                   color:#ffffff;
                   padding:12px 10px;
                   border-radius:9px;
                   font-weight:600;
                   margin-bottom:10px;
               ">
               Connect Google Account
            </a>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Google se abrirá en una nueva pestaña."
        )


    st.divider()


    st.markdown(
        "### Quote Settings"
    )


    number_options = st.selectbox(
        "Number of quotation options",
        [1, 2, 3],
        index=0,
    )


    st.divider()


    st.caption(
        "Cada opción es independiente y puede "
        "tener diferente habitación, tarifa, "
        "beneficios, servicios y políticas."
    )


# ============================================================
# TÍTULO PRINCIPAL
# ============================================================

st.title(
    "Create Quotation"
)

st.caption(
    "Create a professional quotation "
    "for your guest."
)


# ============================================================
# GUEST INFORMATION
# ============================================================

st.markdown(
    "## Guest Information"
)

st.caption(
    "Basic information for the quotation."
)


guest_col1, guest_col2 = st.columns(2)


with guest_col1:

    guest_name = st.text_input(
        "Guest name",
        placeholder="John Smith",
    )


with guest_col2:

    guest_email = st.text_input(
        "Guest email",
        placeholder="guest@email.com",
    )


guest_col3, guest_col4 = st.columns(2)


with guest_col3:

    arrival = st.date_input(
        "Arrival",
        value=date.today(),
    )


with guest_col4:

    departure = st.date_input(
        "Departure",
        value=date.today(),
    )


guest_col5, guest_col6, guest_col7 = (
    st.columns(3)
)


calculated_nights = (
    departure - arrival
).days


if calculated_nights < 1:

    calculated_nights = 1


with guest_col5:

    adults = st.number_input(
        "Adults",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )


with guest_col6:

    children = st.number_input(
        "Children",
        min_value=0,
        max_value=20,
        value=0,
        step=1,
    )


with guest_col7:

    nights = st.number_input(
        "Nights",
        min_value=1,
        max_value=365,
        value=calculated_nights,
        step=1,
    )


# ============================================================
# ATTACHMENTS
# ============================================================

st.markdown(
    "### Attachments"
)

attachments = st.file_uploader(
    "Optional files to attach to the email",
    accept_multiple_files=True,
)


st.divider()


# ============================================================
# COTIZACIONES
# ============================================================

all_options = []


for option_number in range(
    1,
    number_options + 1,
):

    st.markdown(
        f"## Quotation Option {option_number}"
    )

    st.caption(
        "Configure this quotation option independently."
    )


    # --------------------------------------------------------
    # HABITACIÓN Y PLAN
    # --------------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        room_type = st.selectbox(
            "Room type",
            list(
                ROOM_TYPES.keys()
            ),
            key=f"room_type_{option_number}",
        )


    with col2:

        plan_code = st.selectbox(
            "Meal plan",
            list(
                MEAL_PLANS.keys()
            ),
            format_func=lambda x:
                MEAL_PLANS[x]["name"],
            key=f"meal_plan_{option_number}",
        )


    # --------------------------------------------------------
    # TOTAL DE ESTANCIA
    # --------------------------------------------------------

    st.markdown(
        "### Rate"
    )

    st.caption(
        "Enter the total stay amount with taxes included. "
        "The system will calculate all rates automatically."
    )


    rate_col1, rate_col2 = st.columns(2)


    with rate_col1:

        stay_total_tax_included = st.number_input(
            "Stay Total Taxes Included (USD)",
            min_value=0.00,
            value=0.00,
            step=100.00,
            format="%.2f",
            key=(
                f"stay_total_tax_included_"
                f"{option_number}"
            ),
        )


    with rate_col2:

        valid_until = st.date_input(
            "Quote valid until",
            value=date.today(),
            key=(
                f"valid_until_"
                f"{option_number}"
            ),
        )


    calculations = calculate_rate_values(
        stay_total_tax_included,
        nights,
    )


    rate_col3, rate_col4, rate_col5, rate_col6 = (
        st.columns(4)
    )


    with rate_col3:

        st.metric(
            "Nightly Before Taxes",
            money(
                calculations[
                    "nightly_before_tax"
                ]
            ),
        )


    with rate_col4:

        st.metric(
            "Nightly Taxes Included",
            money(
                calculations[
                    "nightly_with_tax"
                ]
            ),
        )


    with rate_col5:

        st.metric(
            "Stay Before Taxes",
            money(
                calculations[
                    "total_before_tax"
                ]
            ),
        )


    with rate_col6:

        st.metric(
            "Taxes 30%",
            money(
                calculations[
                    "taxes"
                ]
            ),
        )


    # --------------------------------------------------------
    # BENEFICIOS
    # --------------------------------------------------------

    st.markdown(
        "### Included Benefits"
    )

    st.caption(
        "Select independently the benefits included "
        "in this quotation option."
    )


    defaults = list(
        ROOM_TYPES[
            room_type
        ][
            "default_inclusions"
        ]
    )


    for inclusion in MEAL_PLANS[
        plan_code
    ][
        "default_inclusions"
    ]:

        if inclusion not in defaults:

            defaults.append(
                inclusion
            )


    inclusion_signature = (
        room_type
        + "|"
        + plan_code
        + "|"
        + "|".join(
            AVAILABLE_INCLUSIONS
        )
    )


    signature_key = (
        "inclusion_signature_"
        + str(option_number)
    )


    old_signature = st.session_state.get(
        signature_key
    )


    if old_signature != inclusion_signature:

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
            ] = (
                inclusion in defaults
            )


        st.session_state[
            signature_key
        ] = inclusion_signature


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
    # SERVICIOS ADICIONALES
    # --------------------------------------------------------

    st.markdown(
        "### Additional Services"
    )

    st.caption(
        "Select any additional services. "
        "Their prices will be added automatically."
    )


    service_columns = st.columns(2)


    selected_services = []


    for index, (
        service,
        price
    ) in enumerate(
        ADDITIONAL_SERVICES.items()
    ):

        with service_columns[
            index % 2
        ]:

            service_key = (
                f"service_"
                f"{option_number}_"
                f"{index}"
            )

            selected = st.checkbox(
                f"{service} — {money(price)}",
                key=service_key,
            )

            if selected:

                selected_services.append(
                    service
                )


    services_total = sum(
        ADDITIONAL_SERVICES[
            service
        ]
        for service in selected_services
    )


    final_total = (
        calculations[
            "total_with_tax"
        ]
        + services_total
    )


    st.metric(
        "Total Amount",
        money(final_total),
    )


    # --------------------------------------------------------
    # DEPOSIT POLICY
    # --------------------------------------------------------

    st.markdown(
        "### Deposit Policy"
    )


    deposit_policy = st.selectbox(
        "Select deposit policy",
        DEPOSIT_POLICIES,
        key=(
            f"deposit_policy_"
            f"{option_number}"
        ),
    )


    # --------------------------------------------------------
    # CANCELLATION POLICY
    # --------------------------------------------------------

    st.markdown(
        "### Cancellation Policy"
    )


    cancellation_policy = st.selectbox(
        "Select cancellation policy",
        CANCELLATION_POLICIES,
        key=(
            f"cancellation_policy_"
            f"{option_number}"
        ),
    )


    # --------------------------------------------------------
    # LINKS
    # --------------------------------------------------------

    st.markdown(
        "### Optional Links"
    )


    link_col1, link_col2 = st.columns(2)


    with link_col1:

        default_360 = ROOM_TYPES[
            room_type
        ].get(
            "360_url",
            ""
        )


        room_360_url = st.text_input(
            "360° Room View Link",
            value=default_360,
            placeholder="https://...",
            key=(
                f"room_360_url_"
                f"{option_number}"
            ),
        )


    with link_col2:

        payment_url = st.text_input(
            "Payment Link",
            placeholder="https://...",
            key=(
                f"payment_url_"
                f"{option_number}"
            ),
        )


    option_data = {
        "room_type": room_type,

        "plan": MEAL_PLANS[
            plan_code
        ]["name"],

        "valid_until": valid_until,

        "stay_total_tax_included":
            stay_total_tax_included,

        "selected_inclusions":
            selected_inclusions,

        "selected_services":
            selected_services,

        "deposit_policy":
            deposit_policy,

        "cancellation_policy":
            cancellation_policy,

        "payment_url":
            payment_url,

        "room_360_url":
            room_360_url,
    }


    all_options.append(
        option_data
    )


    st.divider()


# ============================================================
# GENERAR EMAIL
# ============================================================

email_html = build_email_html(
    guest_name=guest_name or "Guest",
    arrival=arrival,
    departure=departure,
    adults=adults,
    children=children,
    nights=nights,
    options=all_options,
)


# ============================================================
# PREVIEW
# ============================================================

st.markdown(
    "## Email Preview"
)

st.caption(
    "This preview simulates the actual email your guest will receive."
)


st.components.v1.html(
    email_html,
    height=(
        850
        + number_options * 750
    ),
    scrolling=True,
)


# ============================================================
# ACCIONES
# ============================================================

st.markdown(
    "## Actions"
)


action_col1, action_col2 = st.columns(2)


subject = (
    "Your Custom Quotation "
    "Casa Dorada Los Cabos"
)


# ============================================================
# SAVE DRAFT
# ============================================================

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

                save_gmail_draft(
                    to_email=guest_email,
                    subject=subject,
                    html_body=email_html,
                    attachments=attachments,
                )

                st.success(
                    "Draft saved successfully in Gmail."
                )

            except Exception as e:

                st.error(
                    f"Could not save draft: {e}"
                )


# ============================================================
# SEND EMAIL
# ============================================================

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
                    attachments=attachments,
                )

                st.success(
                    "Email sent successfully."
                )

            except Exception as e:

                st.error(
                    f"Could not send email: {e}"
                )

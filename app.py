import streamlit as st
import base64
import hashlib
import hmac
import json
import secrets
import requests

from datetime import date, datetime
from email.message import EmailMessage
from urllib.parse import urlencode

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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
# GMAIL OAUTH SCOPES
# ============================================================

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
]


# ============================================================
# IMPUESTOS
# ============================================================

TAX_RATE = 0.30


# ============================================================
# LOGO
# ============================================================

EMAIL_LOGO_URL = (
    "https://umutu.com/wp-content/uploads/2021/02/Logo-2-3.png"
)


# ============================================================
# ROOM TYPES
# ============================================================

ROOM_TYPES = {

    "Standard Pool View": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": "",
    },

    "Standard Two Double Beds Garden View": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": (
            "https://my.matterport.com/show/?m=6Zo1QcjJvS3"
        ),
    },

    "Junior Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": (
            "https://my.matterport.com/models/"
            "asDp8M3WB35?section=media&mediasection=showcase"
        ),
    },

    "One Bedroom Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": (
            "https://my.matterport.com/models/"
            "Atpb4Tt7URH?section=media&mediasection=showcase"
        ),
    },

    "One Bedroom Plus": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": "",
    },

    "Executive Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": (
            "https://my.matterport.com/show/?m=KeDqsnXnaMC"
        ),
    },

    "Two Bedroom Suite": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": (
            "https://my.matterport.com/models/v5byckDjTex"
        ),
    },

    "One Bedroom Penthouse": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": (
            "https://my.matterport.com/show/?m=1fiBeobaV6D"
        ),
    },

    "Two Bedroom Penthouse": {
        "default_inclusions": [
            "Free Wi-Fi",
            "Free Valet Parking",
        ],
        "360_url": (
            "https://my.matterport.com/show/?m=oXToa8PNnKL"
        ),
    },
}


# ============================================================
# BENEFICIOS
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
# CSS
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
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1450px;
        margin-left: 0 !important;
        margin-right: auto !important;
    }

    section[data-testid="stSidebar"] {
        background: #0a1220;
        border-right: 1px solid #273449;
    }

    section[data-testid="stSidebar"] * {
        color: #f8fafc;
    }

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
        text-align: left !important;
    }

    div[data-testid="stCheckbox"] {
        background: #151f30;
        border: 1px solid #2b394d;
        border-radius: 8px;
        padding: 6px 10px;
        margin-bottom: 6px;
        text-align: left !important;
    }

    div[data-testid="stCheckbox"]:hover {
        border-color: #64748b;
        background: #1b293d;
    }

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

    div[data-testid="stMetric"] {
        background: #151f30;
        border: 1px solid #2b394d;
        border-radius: 9px;
        padding: 10px 12px;
        text-align: left !important;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div {
        text-align: left !important;
    }

    hr {
        border-color: #293548 !important;
    }

    h1, h2, h3, h4, h5, h6,
    p,
    div,
    span {
        text-align: left;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GOOGLE OAUTH CONFIG
# ============================================================

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


# ============================================================
# SUPABASE CONFIG
# ============================================================

def get_supabase_config():

    if "supabase" not in st.secrets:
        return None

    config = st.secrets["supabase"]

    return {
        "url": config["url"].rstrip("/"),
        "key": config["service_role_key"],
    }


# ============================================================
# SUPABASE TOKEN STORAGE
# ============================================================

def save_refresh_token(
    email,
    refresh_token,
):

    if not email or not refresh_token:
        return False

    config = get_supabase_config()

    if not config:
        return False

    endpoint = (
        f"{config['url']}/rest/v1/google_tokens"
    )

    headers = {
        "apikey": config["key"],
        "Authorization": (
            f"Bearer {config['key']}"
        ),
        "Content-Type": "application/json",
        "Prefer": (
            "resolution=merge-duplicates,"
            "return=minimal"
        ),
    }

    now = datetime.utcnow().isoformat()

    payload = {
        "email": email.lower().strip(),
        "refresh_token": refresh_token,
        "created_at": now,
        "updated_at": now,
    }

    try:

        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=15,
        )

        if response.status_code in [
            200,
            201,
            204,
        ]:

            return True

        st.session_state.supabase_save_error = (
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

        return False

    except Exception as e:

        st.session_state.supabase_save_error = str(e)

        return False


def get_saved_refresh_token(email):

    if not email:
        return None

    config = get_supabase_config()

    if not config:
        return None

    endpoint = (
        f"{config['url']}/rest/v1/google_tokens"
    )

    headers = {
        "apikey": config["key"],
        "Authorization": (
            f"Bearer {config['key']}"
        ),
    }

    params = {
        "email": f"eq.{email.lower().strip()}",
        "select": "refresh_token",
        "limit": "1",
    }

    try:

        response = requests.get(
            endpoint,
            headers=headers,
            params=params,
            timeout=15,
        )

        if response.status_code != 200:

            st.session_state.supabase_get_error = (
                f"HTTP {response.status_code}: "
                f"{response.text}"
            )

            return None

        data = response.json()

        if not data:
            return None

        return data[0].get(
            "refresh_token"
        )

    except Exception as e:

        st.session_state.supabase_get_error = str(e)

        return None


# ============================================================
# IDENTIDAD DEL USUARIO
# ============================================================

def get_logged_in_email():

    try:

        if (
            hasattr(st, "user")
            and st.user.is_logged_in
        ):

            email = st.user.email

            if email:

                email = email.lower().strip()

                if not email.endswith(
                    "@casadorada.com"
                ):

                    return None

                return email

    except Exception:

        pass

    return None


# ============================================================
# VALIDACIÓN DE USUARIO
# ============================================================

def validate_logged_in_user():

    try:

        if (
            hasattr(st, "user")
            and st.user.is_logged_in
        ):

            authenticated_email = (
                st.user.email
            )

            if authenticated_email:

                authenticated_email = (
                    authenticated_email
                    .lower()
                    .strip()
                )

                if not authenticated_email.endswith(
                    "@casadorada.com"
                ):

                    st.error(
                        "This account is not authorized. "
                        "Please use your @casadorada.com account."
                    )

                    st.logout()

                    st.stop()

                return authenticated_email

    except Exception:

        pass

    return None


# ============================================================
# BASE64
# ============================================================

def b64url_encode(data):

    return base64.urlsafe_b64encode(
        data
    ).decode().rstrip("=")


def b64url_decode(value):

    padding = "=" * (-len(value) % 4)

    return base64.urlsafe_b64decode(
        value + padding
    )


# ============================================================
# OAUTH STATE
# ============================================================

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

        payload = json.loads(
            b64url_decode(
                encoded
            ).decode("utf-8")
        )

        created_at = payload.get(
            "created_at",
            0,
        )

        current_time = (
            datetime.utcnow().timestamp()
        )

        if (
            current_time
            - float(created_at)
            > 900
        ):

            return None

        return payload

    except Exception:

        return None


# ============================================================
# GOOGLE GMAIL LOGIN URL
# ============================================================

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

        "code_verifier":
            code_verifier,

        "created_at":
            datetime.utcnow().timestamp(),
    }

    signed_state = sign_state(
        payload
    )

    config = get_oauth_config()

    params = {

        "client_id":
            config["client_id"],

        "redirect_uri":
            config["redirect_uri"],

        "response_type":
            "code",

        "scope":
            " ".join(GMAIL_SCOPES),

        "access_type":
            "offline",

        "include_granted_scopes":
            "false",

        "prompt":
            "consent",

        "state":
            signed_state,

        "code_challenge":
            code_challenge,

        "code_challenge_method":
            "S256",
    }

    return (
        "https://accounts.google.com/"
        "o/oauth2/v2/auth?"
        + urlencode(params)
    )


# ============================================================
# CREDENTIALS TO DICT
# ============================================================

def credentials_to_dict(credentials):

    return {

        "token":
            credentials.token,

        "refresh_token":
            credentials.refresh_token,

        "token_uri":
            credentials.token_uri,

        "client_id":
            credentials.client_id,

        "client_secret":
            credentials.client_secret,

        "scopes":
            credentials.scopes,
    }


# ============================================================
# PROCESS GOOGLE GMAIL CALLBACK
# ============================================================

def process_google_callback():

    code = st.query_params.get(
        "code"
    )

    state = st.query_params.get(
        "state"
    )

    if not code or not state:
        return False

    payload = verify_state(
        state
    )

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

        config = get_oauth_config()

        token_response = requests.post(

            "https://oauth2.googleapis.com/token",

            data={

                "code":
                    code,

                "client_id":
                    config["client_id"],

                "client_secret":
                    config["client_secret"],

                "redirect_uri":
                    config["redirect_uri"],

                "grant_type":
                    "authorization_code",

                "code_verifier":
                    code_verifier,
            },

            timeout=20,
        )

        if token_response.status_code != 200:

            raise Exception(
                "Google token exchange failed "
                f"(HTTP {token_response.status_code}): "
                f"{token_response.text}"
            )

        token_data = (
            token_response.json()
        )

        access_token = (
            token_data.get(
                "access_token"
            )
        )

        refresh_token = (
            token_data.get(
                "refresh_token"
            )
        )

        if not access_token:

            raise Exception(
                "Google did not return an access token."
            )

        if not refresh_token:

            raise Exception(
                "Google did not return a refresh token. "
                "Please authorize Gmail again."
            )

        credentials = Credentials(

            token=access_token,

            refresh_token=refresh_token,

            token_uri=(
                "https://oauth2.googleapis.com/token"
            ),

            client_id=config[
                "client_id"
            ],

            client_secret=config[
                "client_secret"
            ],

            scopes=GMAIL_SCOPES,
        )

        service = build(

            "gmail",
            "v1",
            credentials=credentials,
        )

        profile = (
            service.users()
            .getProfile(
                userId="me"
            )
            .execute()
        )

        email = profile.get(
            "emailAddress"
        )

        if not email:

            raise Exception(
                "No fue posible obtener el email de Gmail."
            )

        email = email.lower().strip()

        if not email.endswith(
            "@casadorada.com"
        ):

            st.error(
                "The Gmail account must be a "
                "@casadorada.com account."
            )

            st.query_params.clear()

            return False

        logged_email = get_logged_in_email()

        if not logged_email:

            st.error(
                "Please sign in with your "
                "@casadorada.com account first."
            )

            st.query_params.clear()

            return False

        if email != logged_email:

            st.error(
                "The Gmail account must match "
                "your authenticated @casadorada.com account."
            )

            st.query_params.clear()

            return False

        saved = save_refresh_token(

            email=email,

            refresh_token=refresh_token,
        )

        if not saved:

            error_detail = (
                st.session_state.get(
                    "supabase_save_error"
                )
            )

            st.error(
                "Gmail was authorized, but the "
                "connection could not be saved."
            )

            if error_detail:

                with st.expander(
                    "Technical details"
                ):

                    st.code(
                        error_detail
                    )

            st.query_params.clear()

            return False

        st.session_state.google_credentials = (
            credentials_to_dict(
                credentials
            )
        )

        st.session_state.google_email = email

        st.session_state.google_connected = True

        st.session_state.gmail_auth_error = None

        st.session_state.supabase_get_error = None

        st.query_params.clear()

        pending_quote = (
            st.session_state.get(
                "pending_quote"
            )
        )

        pending_action = (
            st.session_state.get(
                "pending_action"
            )
        )

        if (
            pending_quote
            and pending_action
        ):

            try:

                if pending_action == "draft":

                    save_gmail_draft(

                        to_email=
                            pending_quote[
                                "guest_email"
                            ],

                        subject=
                            pending_quote[
                                "subject"
                            ],

                        html_body=
                            pending_quote[
                                "email_html"
                            ],

                        plain_text_body=
                            pending_quote[
                                "plain_text_email"
                            ],
                    )

                    st.session_state.pending_quote = None

                    st.session_state.pending_action = None

                    st.session_state.auto_draft_success = True

                elif pending_action == "send":

                    send_gmail_message(

                        to_email=
                            pending_quote[
                                "guest_email"
                            ],

                        subject=
                            pending_quote[
                                "subject"
                            ],

                        html_body=
                            pending_quote[
                                "email_html"
                            ],

                        plain_text_body=
                            pending_quote[
                                "plain_text_email"
                            ],
                    )

                    st.session_state.pending_quote = None

                    st.session_state.pending_action = None

                    st.session_state.auto_send_success = True

            except Exception as e:

                st.session_state.pending_action_error = str(e)

                st.session_state.pending_quote = None

                st.session_state.pending_action = None

        return True

    except Exception as e:

        st.session_state.gmail_auth_error = str(e)

        st.error(
            f"Error connecting Gmail: {e}"
        )

        return False


# ============================================================
# GET CREDENTIALS
# ============================================================

def get_credentials():

    logged_email = get_logged_in_email()

    if not logged_email:
        return None

    logged_email = (
        logged_email
        .lower()
        .strip()
    )

    data = st.session_state.get(
        "google_credentials"
    )

    if data:

        credentials = Credentials(

            token=data.get(
                "token"
            ),

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

        if credentials.valid:
            return credentials

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

                st.session_state.google_connected = True

                return credentials

            except Exception as e:

                st.session_state.google_credentials = None

                st.session_state.google_connected = False

                st.session_state.gmail_auth_error = (
                    str(e)
                )

    refresh_token = (
        get_saved_refresh_token(
            logged_email
        )
    )

    if not refresh_token:
        return None

    config = get_oauth_config()

    credentials = Credentials(

        token=None,

        refresh_token=refresh_token,

        token_uri=(
            "https://oauth2.googleapis.com/token"
        ),

        client_id=config[
            "client_id"
        ],

        client_secret=config[
            "client_secret"
        ],

        scopes=GMAIL_SCOPES,
    )

    try:

        credentials.refresh(
            Request()
        )

        st.session_state.google_credentials = (
            credentials_to_dict(
                credentials
            )
        )

        st.session_state.google_email = (
            logged_email
        )

        st.session_state.google_connected = True

        st.session_state.gmail_auth_error = None

        return credentials

    except Exception as e:

        st.session_state.google_credentials = None

        st.session_state.google_connected = False

        st.session_state.gmail_auth_error = (
            str(e)
        )

        return None


# ============================================================
# GMAIL SERVICE
# ============================================================

def get_gmail_service():

    credentials = get_credentials()

    if not credentials:
        return None

    try:

        service = build(

            "gmail",
            "v1",
            credentials=credentials,
        )

        service.users().getProfile(
            userId="me"
        ).execute()

        return service

    except Exception as e:

        st.session_state.gmail_auth_error = (
            str(e)
        )

        st.session_state.google_connected = False

        return None


# ============================================================
# CONNECTED EMAIL
# ============================================================

def get_connected_email():

    credentials = get_credentials()

    if not credentials:
        return None

    try:

        service = build(

            "gmail",
            "v1",
            credentials=credentials,
        )

        profile = (
            service.users()
            .getProfile(
                userId="me"
            )
            .execute()
        )

        email = profile.get(
            "emailAddress"
        )

        if not email:
            return None

        email = email.lower().strip()

        if not email.endswith(
            "@casadorada.com"
        ):
            return None

        logged_email = get_logged_in_email()

        if (
            logged_email
            and email != logged_email
        ):
            return None

        st.session_state.google_email = email

        st.session_state.google_connected = True

        return email

    except Exception as e:

        st.session_state.google_connected = False

        st.session_state.gmail_auth_error = (
            str(e)
        )

        return None


# ============================================================
# RATE CALCULATIONS
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

        "total_with_tax":
            total_with_tax,

        "total_before_tax":
            total_before_tax,

        "taxes":
            taxes,

        "nightly_with_tax":
            nightly_with_tax,

        "nightly_before_tax":
            nightly_before_tax,
    }


# ============================================================
# MONEY
# ============================================================

def money(value):

    try:

        return "${:,.2f} USD".format(
            float(value)
        )

    except Exception:

        return "$0.00 USD"


# ============================================================
# HTML ESCAPE
# ============================================================

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


# ============================================================
# DATE FORMAT
# ============================================================

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
# OPTION HTML
# ============================================================

def build_option_html(
    option_number,
    room_type,
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

    nightly_with_tax = calculations[
        "nightly_with_tax"
    ]

    nightly_before_tax = calculations[
        "nightly_before_tax"
    ]

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
                text-align:left;
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
                    text-align:left;
                ">
                No additional services
            </td>

        </tr>
        """

    final_total = (
        total_with_tax
        + additional_services_total
    )

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

    return f"""

    <table width="100%"
           cellpadding="0"
           cellspacing="0"
           border="0"
           style="
               border:1px solid #dddddd;
               background:#ffffff;
               margin-bottom:22px;
           ">

        <tr>

            <td style="
                padding:20px;
                text-align:left;
            ">

                <div style="
                    color:#1f4f78;
                    font-size:18px;
                    font-weight:bold;
                    margin-bottom:5px;
                    text-align:left;
                ">
                    Option {option_number}
                </div>

                <div style="
                    color:#333333;
                    font-size:20px;
                    font-weight:bold;
                    margin-bottom:18px;
                    text-align:left;
                ">
                    {html_escape(room_type)}
                </div>

                <div style="
                    color:#1f4f78;
                    font-size:15px;
                    font-weight:bold;
                    margin-bottom:8px;
                    text-align:left;
                ">
                    Rate Details
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
                            text-align:left;
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
                            text-align:left;
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
                            text-align:left;
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
                            border-top:1px solid #eeeeee;
                            padding:10px 0 6px 0;
                            color:#1f4f78;
                            font-size:15px;
                            font-weight:bold;
                            text-align:left;
                        ">
                            Stay total taxes included
                        </td>

                        <td style="
                            border-top:1px solid #eeeeee;
                            padding:10px 0 6px 0;
                            color:#1f4f78;
                            font-size:16px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(total_with_tax)}
                        </td>

                    </tr>

                </table>

                <div style="
                    margin-top:20px;
                    margin-bottom:8px;
                    color:#1f4f78;
                    font-size:15px;
                    font-weight:bold;
                    text-align:left;
                ">
                    Included
                </div>

                <ul style="
                    padding-left:22px;
                    margin-top:8px;
                    margin-bottom:20px;
                    text-align:left;
                ">

                    {inclusions_html}

                </ul>

                <div style="
                    margin-top:20px;
                    margin-bottom:8px;
                    color:#1f4f78;
                    font-size:15px;
                    font-weight:bold;
                    text-align:left;
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
                            text-align:left;
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

                <div style="
                    margin-top:18px;
                    padding:15px;
                    background:#f5f7fa;
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
                                text-align:left;
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

                <div style="
                    margin-top:20px;
                    padding-top:15px;
                    border-top:1px solid #eeeeee;
                    text-align:left;
                ">

                    <div style="
                        color:#1f4f78;
                        font-size:14px;
                        font-weight:bold;
                        margin-bottom:6px;
                        text-align:left;
                    ">
                        Deposit Policy
                    </div>

                    <div style="
                        color:#555555;
                        font-size:13px;
                        line-height:1.5;
                        text-align:left;
                    ">
                        {html_escape(deposit_policy)}
                    </div>

                    <div style="
                        color:#1f4f78;
                        font-size:14px;
                        font-weight:bold;
                        margin-top:15px;
                        margin-bottom:6px;
                        text-align:left;
                    ">
                        Cancellation Policy
                    </div>

                    <div style="
                        color:#555555;
                        font-size:13px;
                        line-height:1.5;
                        text-align:left;
                    ">
                        {html_escape(cancellation_policy)}
                    </div>

                </div>

                <div style="
                    margin-top:20px;
                    text-align:left;
                ">

                    {buttons_html}

                </div>

                <div style="
                    margin-top:16px;
                    color:#777777;
                    font-size:12px;
                    text-align:left;
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
# PLAIN TEXT EMAIL
# ============================================================

def build_plain_text(
    guest_name,
    arrival,
    departure,
    adults,
    children,
    nights,
    options,
):

    lines = []

    lines.append(
        "YOUR CUSTOM QUOTATION"
    )

    lines.append("")

    lines.append(
        f"Dear {guest_name},"
    )

    lines.append("")

    lines.append(
        "Thank you for considering "
        "Casa Dorada Los Cabos Resort & Spa "
        "for your upcoming stay."
    )

    lines.append("")

    lines.append(
        "YOUR STAY"
    )

    lines.append(
        f"Guests: {adults} Adults"
    )

    if children > 0:

        lines.append(
            f"Children: {children}"
        )

    lines.append(
        f"Nights: {nights}"
    )

    lines.append(
        f"Arrival: {format_date_email(arrival)}"
    )

    lines.append(
        f"Departure: {format_date_email(departure)}"
    )

    lines.append("")

    lines.append(
        "AVAILABLE OPTIONS"
    )

    lines.append("")

    for index, option in enumerate(
        options,
        start=1,
    ):

        calculations = calculate_rate_values(
            option[
                "stay_total_tax_included"
            ],
            nights,
        )

        services_total = sum(

            ADDITIONAL_SERVICES[
                service
            ]

            for service in option[
                "selected_services"
            ]

        )

        final_total = (
            calculations[
                "total_with_tax"
            ]
            + services_total
        )

        lines.append(
            f"OPTION {index}"
        )

        lines.append(
            f"Room: {option['room_type']}"
        )

        lines.append(
            f"Rate per night before taxes: "
            f"{money(calculations['nightly_before_tax'])}"
        )

        lines.append(
            f"Rate per night taxes included: "
            f"{money(calculations['nightly_with_tax'])}"
        )

        lines.append(
            f"Number of nights: {nights}"
        )

        lines.append(
            f"Stay total taxes included: "
            f"{money(calculations['total_with_tax'])}"
        )

        lines.append("")

        lines.append(
            "Included:"
        )

        for inclusion in option[
            "selected_inclusions"
        ]:

            lines.append(
                f"• {inclusion}"
            )

        lines.append("")

        lines.append(
            "Additional Services:"
        )

        if option[
            "selected_services"
        ]:

            for service in option[
                "selected_services"
            ]:

                lines.append(
                    f"• {service}: "
                    f"{money(ADDITIONAL_SERVICES[service])}"
                )

        else:

            lines.append(
                "No additional services"
            )

        lines.append("")

        lines.append(
            f"TOTAL AMOUNT: "
            f"{money(final_total)}"
        )

        lines.append("")

        lines.append(
            "Deposit Policy:"
        )

        lines.append(
            option[
                "deposit_policy"
            ]
        )

        lines.append("")

        lines.append(
            "Cancellation Policy:"
        )

        lines.append(
            option[
                "cancellation_policy"
            ]
        )

        lines.append("")

        lines.append(
            f"Quote valid until: "
            f"{format_date_email(option['valid_until'])}"
        )

        lines.append("")

        lines.append(
            "----------------------------------------"
        )

        lines.append("")

    lines.append(
        "Casa Dorada Los Cabos Resort & Spa"
    )

    lines.append(
        "Av. del Pescador s/n, "
        "Cabo San Lucas, B.C.S."
    )

    lines.append(
        "US: 1-866-448-0151"
    )

    return "\n".join(lines)


# ============================================================
# COMPLETE EMAIL HTML
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

    # IMPORTANTE:
    # Se recorren TODAS las opciones.

    for index, option in enumerate(
        options,
        start=1,
    ):

        options_html += build_option_html(

            option_number=index,

            room_type=option[
                "room_type"
            ],

            valid_until=option[
                "valid_until"
            ],

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

    guest_summary = (
        f"{adults} Adults"
    )

    if children > 0:

        guest_summary += (
            f" + {children} Children"
        )

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

<td align="left"
    style="padding:30px 10px;">

<table width="600"
       cellpadding="0"
       cellspacing="0"
       border="0"
       style="
           width:600px;
           max-width:100%;
           background:#ffffff;
       ">

<tr>

<td align="left"
    style="
        background:#ffffff;
        padding:25px 35px 15px 35px;
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

<tr>

<td style="
    padding:15px 35px 5px 35px;
    text-align:left;
">

<div style="
    color:#1f4f78;
    font-size:25px;
    font-weight:bold;
    text-align:left;
">

Your Custom Quotation

</div>

</td>

</tr>

<tr>

<td style="
    padding:15px 35px 10px 35px;
    text-align:left;
">

<p style="
    color:#333333;
    font-size:15px;
    line-height:1.6;
    margin:0 0 12px 0;
    text-align:left;
">

Dear {html_escape(guest_name)},

</p>

<p style="
    color:#555555;
    font-size:14px;
    line-height:1.6;
    margin:0;
    text-align:left;
">

Thank you for considering
Casa Dorada Los Cabos Resort & Spa
for your upcoming stay.

Please find below your personalized
quotation and available options.

</p>

</td>

</tr>

<tr>

<td style="
    padding:20px 35px 15px 35px;
    text-align:left;
">

<div style="
    color:#1f4f78;
    font-size:19px;
    font-weight:bold;
    margin-bottom:12px;
    text-align:left;
">

Your Stay

</div>

<table width="100%"
       cellpadding="0"
       cellspacing="0"
       border="0"
       style="
           background:#f7f8fa;
           border:1px solid #e5e7eb;
       ">

<tr>

<td style="
    padding:10px 14px;
    width:35%;
    color:#777777;
    font-size:13px;
    font-weight:bold;
    text-align:left;
    border-bottom:1px solid #e5e7eb;
">

Guests

</td>

<td style="
    padding:10px 14px;
    color:#1f2937;
    font-size:13px;
    font-weight:bold;
    text-align:left;
    border-bottom:1px solid #e5e7eb;
">

{html_escape(guest_summary)}

</td>

</tr>

<tr>

<td style="
    padding:10px 14px;
    color:#777777;
    font-size:13px;
    font-weight:bold;
    text-align:left;
    border-bottom:1px solid #e5e7eb;
">

Nights

</td>

<td style="
    padding:10px 14px;
    color:#1f2937;
    font-size:13px;
    font-weight:bold;
    text-align:left;
    border-bottom:1px solid #e5e7eb;
">

{html_escape(nights)}
{" Night" if nights == 1 else " Nights"}

</td>

</tr>

<tr>

<td style="
    padding:10px 14px;
    color:#777777;
    font-size:13px;
    font-weight:bold;
    text-align:left;
    border-bottom:1px solid #e5e7eb;
">

Arrival

</td>

<td style="
    padding:10px 14px;
    color:#1f2937;
    font-size:13px;
    font-weight:bold;
    text-align:left;
    border-bottom:1px solid #e5e7eb;
">

{html_escape(
    format_date_email(arrival)
)}

</td>

</tr>

<tr>

<td style="
    padding:10px 14px;
    color:#777777;
    font-size:13px;
    font-weight:bold;
    text-align:left;
">

Departure

</td>

<td style="
    padding:10px 14px;
    color:#1f2937;
    font-size:13px;
    font-weight:bold;
    text-align:left;
">

{html_escape(
    format_date_email(departure)
)}

</td>

</tr>

</table>

</td>

</tr>

<tr>

<td style="
    padding:15px 35px 5px 35px;
    text-align:left;
">

<div style="
    color:#1f4f78;
    font-size:19px;
    font-weight:bold;
    margin-bottom:15px;
    text-align:left;
">

Available Options

</div>

{options_html}

</td>

</tr>

<tr>

<td style="
    background:#1f4f78;
    padding:22px 30px;
    text-align:left;
">

<div style="
    color:#ffffff;
    font-size:14px;
    font-weight:bold;
    margin-bottom:6px;
    text-align:left;
">

Casa Dorada Los Cabos Resort & Spa

</div>

<div style="
    color:#dbeafe;
    font-size:12px;
    line-height:1.5;
    text-align:left;
">

Av. del Pescador s/n,
Cabo San Lucas, B.C.S.

</div>

<div style="
    color:#dbeafe;
    font-size:12px;
    line-height:1.5;
    text-align:left;
">

US:
<a href="tel:18664480151"
   style="
       color:#ffffff;
       text-decoration:none;
   ">
1-866-448-0151
</a>

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
    plain_text_body,
):

    message = EmailMessage()

    message["To"] = to_email

    message["Subject"] = subject

    message.set_content(
        plain_text_body
    )

    message.add_alternative(
        html_body,
        subtype="html",
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


# ============================================================
# SAVE DRAFT
# ============================================================

def save_gmail_draft(
    to_email,
    subject,
    html_body,
    plain_text_body,
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

        plain_text_body=plain_text_body,
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


# ============================================================
# SEND EMAIL
# ============================================================

def send_gmail_message(
    to_email,
    subject,
    html_body,
    plain_text_body,
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

        plain_text_body=plain_text_body,
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

SESSION_DEFAULTS = {

    "google_connected": False,

    "google_credentials": None,

    "google_email": None,

    "gmail_auth_error": None,

    "supabase_save_error": None,

    "supabase_get_error": None,

    "pending_quote": None,

    "pending_action": None,

    "auto_draft_success": False,

    "auto_send_success": False,

    "pending_action_error": None,

}


for key, default_value in SESSION_DEFAULTS.items():

    if key not in st.session_state:

        st.session_state[key] = default_value


# ============================================================
# VALIDAR USUARIO OIDC
# ============================================================

validate_logged_in_user()


# ============================================================
# GMAIL CALLBACK
# ============================================================

if (
    "code" in st.query_params
    and "state" in st.query_params
):

    process_google_callback()


# ============================================================
# RESTORE GMAIL CONNECTION
# ============================================================

logged_email = get_logged_in_email()

if logged_email:

    st.session_state.google_email = logged_email

    restored_credentials = get_credentials()

    if restored_credentials:

        st.session_state.google_connected = True

    else:

        st.session_state.google_connected = False


# ============================================================
# MOSTRAR RESULTADOS AUTOMÁTICOS
# ============================================================

if st.session_state.get(
    "auto_draft_success"
):

    st.success(
        "Draft saved successfully in Gmail."
    )

    st.session_state.auto_draft_success = False


if st.session_state.get(
    "auto_send_success"
):

    st.success(
        "Email sent successfully."
    )

    st.session_state.auto_send_success = False


if st.session_state.get(
    "pending_action_error"
):

    st.error(
        "The quotation was recovered, "
        "but the email action could not be completed."
    )

    with st.expander(
        "Technical details"
    ):

        st.code(
            st.session_state.pending_action_error
        )

    st.session_state.pending_action_error = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## Gmail"
    )

    connected_email = (
        get_connected_email()
    )

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

        st.caption(
            "Tu conexión de Gmail se guarda de forma "
            "segura y puede recuperarse después de "
            "actualizar la página."
        )

    else:

        try:

            user_logged_in = (
                st.user.is_logged_in
            )

        except Exception:

            user_logged_in = False

        if not user_logged_in:

            st.info(
                "Gmail se conectará automáticamente "
                "cuando intentes guardar o enviar una cotización."
            )

        else:

            login_url = (
                get_google_login_url()
            )

            st.markdown(
                f"""
                <a href="{login_url}"
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
                   Connect Gmail
                </a>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                "Opcional. También puedes conectar Gmail "
                "antes de crear una cotización."
            )

            gmail_error = (
                st.session_state.get(
                    "gmail_auth_error"
                )
            )

            supabase_error = (
                st.session_state.get(
                    "supabase_get_error"
                )
            )

            if gmail_error or supabase_error:

                with st.expander(
                    "Connection diagnostics"
                ):

                    if gmail_error:

                        st.write(
                            "Gmail:"
                        )

                        st.code(
                            gmail_error
                        )

                    if supabase_error:

                        st.write(
                            "Supabase:"
                        )

                        st.code(
                            supabase_error
                        )


    st.divider()


    st.markdown(
        "### Quote Settings"
    )


    # ========================================================
    # AHORA PERMITE HASTA 5 OPCIONES
    # ========================================================

    number_options = st.selectbox(

        "Number of quotation options",

        [1, 2, 3, 4, 5],

        index=0,
    )


    st.divider()


    st.caption(
        "Cada opción es independiente y puede "
        "tener diferente habitación, tarifa, "
        "beneficios, servicios y políticas."
    )


# ============================================================
# MAIN TITLE
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


st.divider()


# ============================================================
# QUOTATION OPTIONS
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
    # ROOM
    # --------------------------------------------------------

    room_type = st.selectbox(

        "Room type",

        list(
            ROOM_TYPES.keys()
        ),

        key=(
            f"room_type_"
            f"{option_number}"
        ),
    )


    # --------------------------------------------------------
    # RATE
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

        stay_total_tax_included = (
            st.number_input(

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


    calculations = (
        calculate_rate_values(
            stay_total_tax_included,
            nights,
        )
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
    # INCLUDED BENEFITS
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


    inclusion_signature = (
        room_type
        + "|"
        + "|".join(
            AVAILABLE_INCLUSIONS
        )
    )


    signature_key = (
        "inclusion_signature_"
        + str(option_number)
    )


    old_signature = (
        st.session_state.get(
            signature_key
        )
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
    # ADDITIONAL SERVICES
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
    # OPTIONAL LINKS
    # --------------------------------------------------------

    st.markdown(
        "### Optional Links"
    )


    link_col1, link_col2 = st.columns(2)


    # ========================================================
    # 360 LINK
    #
    # SE ACTUALIZA AUTOMÁTICAMENTE SEGÚN LA HABITACIÓN
    # ========================================================

    with link_col1:

        room_360_url = ROOM_TYPES[
            room_type
        ].get(
            "360_url",
            ""
        )

        st.text_input(

            "360° Room View Link",

            value=room_360_url,

            placeholder="https://...",

            key=(
                f"room_360_url_display_"
                f"{option_number}_"
                f"{room_type}"
            ),

            disabled=True,
        )


    # ========================================================
    # PAYMENT LINK
    # ========================================================

    with link_col2:

        payment_url = st.text_input(

            "Payment Link",

            placeholder="https://...",

            key=(
                f"payment_url_"
                f"{option_number}"
            ),
        )


    # ========================================================
    # SAVE OPTION
    #
    # MUY IMPORTANTE:
    # ESTE BLOQUE ESTÁ DENTRO DEL FOR.
    #
    # Por eso se guardan las opciones 1, 2, 3, 4 y 5.
    # ========================================================

    option_data = {

        "room_type":
            room_type,

        "valid_until":
            valid_until,

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
# BUILD EMAIL
# ============================================================

email_html = build_email_html(

    guest_name=(
        guest_name
        or "Guest"
    ),

    arrival=arrival,

    departure=departure,

    adults=adults,

    children=children,

    nights=nights,

    options=all_options,
)


plain_text_email = build_plain_text(

    guest_name=(
        guest_name
        or "Guest"
    ),

    arrival=arrival,

    departure=departure,

    adults=adults,

    children=children,

    nights=nights,

    options=all_options,
)


# ============================================================
# EMAIL PREVIEW
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
# ACTIONS
# ============================================================

st.markdown(
    "## Actions"
)


action_col1, action_col2 = (
    st.columns(2)
)


subject = (
    "Your Custom Quotation "
    "Casa Dorada Los Cabos"
)


# ============================================================
# FUNCIÓN PARA GUARDAR COTIZACIÓN PENDIENTE
# ============================================================

def store_pending_quote(
    action,
    guest_email,
    email_html,
    plain_text_email,
):

    st.session_state.pending_quote = {

        "guest_email":
            guest_email,

        "subject":
            subject,

        "email_html":
            email_html,

        "plain_text_email":
            plain_text_email,
    }

    st.session_state.pending_action = action


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

        else:

            gmail_service = get_gmail_service()

            if gmail_service:

                try:

                    save_gmail_draft(

                        to_email=guest_email,

                        subject=subject,

                        html_body=email_html,

                        plain_text_body=(
                            plain_text_email
                        ),
                    )

                    st.success(
                        "Draft saved successfully in Gmail."
                    )

                except Exception as e:

                    st.error(
                        f"Could not save draft: {e}"
                    )

            else:

                store_pending_quote(

                    action="draft",

                    guest_email=guest_email,

                    email_html=email_html,

                    plain_text_email=plain_text_email,
                )

                try:

                    user_logged_in = (
                        st.user.is_logged_in
                    )

                except Exception:

                    user_logged_in = False


                if not user_logged_in:

                    st.info(
                        "Your quotation has been saved. "
                        "Sign in with your @casadorada.com account "
                        "to continue."
                    )

                    st.login()

                else:

                    login_url = (
                        get_google_login_url()
                    )

                    st.warning(
                        "Your quotation is saved. "
                        "Connect Gmail to continue."
                    )

                    st.markdown(
                        f"""
                        <a href="{login_url}"
                           rel="noopener noreferrer"
                           style="
                               display:inline-block;
                               background:#2563eb;
                               color:#ffffff;
                               padding:13px 22px;
                               border-radius:9px;
                               text-decoration:none;
                               font-weight:600;
                               margin-top:8px;
                           ">
                           Continue with Google
                        </a>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.caption(
                        "After authorization, your quotation "
                        "will be saved automatically as a Gmail draft."
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

        else:

            gmail_service = get_gmail_service()

            if gmail_service:

                try:

                    send_gmail_message(

                        to_email=guest_email,

                        subject=subject,

                        html_body=email_html,

                        plain_text_body=(
                            plain_text_email
                        ),
                    )

                    st.success(
                        "Email sent successfully."
                    )

                except Exception as e:

                    st.error(
                        f"Could not send email: {e}"
                    )

            else:

                store_pending_quote(

                    action="send",

                    guest_email=guest_email,

                    email_html=email_html,

                    plain_text_email=plain_text_email,
                )

                try:

                    user_logged_in = (
                        st.user.is_logged_in
                    )

                except Exception:

                    user_logged_in = False


                if not user_logged_in:

                    st.info(
                        "Your quotation has been saved. "
                        "Sign in with your @casadorada.com account "
                        "to continue."
                    )

                    st.login()

                else:

                    login_url = (
                        get_google_login_url()
                    )

                    st.warning(
                        "Your quotation is saved. "
                        "Connect Gmail to continue."
                    )

                    st.markdown(
                        f"""
                        <a href="{login_url}"
                           rel="noopener noreferrer"
                           style="
                               display:inline-block;
                               background:#2563eb;
                               color:#ffffff;
                               padding:13px 22px;
                               border-radius:9px;
                               text-decoration:none;
                               font-weight:600;
                               margin-top:8px;
                           ">
                           Continue with Google
                        </a>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.caption(
                        "After authorization, the email "
                        "will be sent automatically."
                    )

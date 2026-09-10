import streamlit as st
import base64
import hashlib
import hmac
import json
import secrets
import requests

from datetime import date, datetime, timezone
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
# TRANSLATIONS DICTIONARY
# ============================================================

TRANSLATIONS = {
    "en": {
        "custom_quotation": "Your Custom Quotation",
        "reservation_confirmation": "Reservation Confirmation",
        "dear": "Dear",
        "quote_intro": "Thank you for considering Casa Dorada Los Cabos Resort & Spa for your upcoming stay. Please find below your personalized quotation and available options.",
        "conf_intro": "We are delighted to confirm your reservation at Casa Dorada Los Cabos Resort & Spa.",
        "your_stay": "Your Stay",
        "reservation_details": "Reservation Details",
        "guests": "Guests",
        "adults": "Adults",
        "children": "Children",
        "nights": "Nights",
        "night": "Night",
        "arrival": "Arrival",
        "departure": "Departure",
        "available_options": "Available Options",
        "option": "Option",
        "room_type": "Room Type",
        "rate_details": "Rate Details",
        "rate_before_taxes": "Rate per night before taxes",
        "rate_with_taxes": "Rate per night taxes included",
        "number_nights": "Number of nights",
        "stay_total": "Stay total taxes included",
        "included": "Included",
        "included_benefits": "Included Benefits",
        "additional_services": "Additional Services",
        "additional_total": "Additional services total",
        "total_amount": "TOTAL AMOUNT",
        "deposit_policy": "Deposit Policy",
        "cancellation_policy": "Cancellation Policy",
        "quote_valid": "Quote valid until",
        "conf_number": "Confirmation Number",
        "payment_status": "Payment Status",
        "deposit": "Deposit",
        "balance_due": "Balance Due",
        "special_requests": "Special Requests",
        "no_inclusions": "No inclusions selected",
        "no_services": "No additional services",
        "view_room": "VIEW ROOM",
        "secure_booking": "SECURE YOUR BOOKING",
        "fully_paid": "Fully Paid",
        "first_night_deposit": "First Night Deposit",
        "fully_paid_policy": "Reservation is fully paid.",
        "first_night_policy": "Reservation is guaranteed with the first night deposit, balance to pay due check in: "
    },
    "es": {
        "custom_quotation": "Su Cotización Personalizada",
        "reservation_confirmation": "Confirmación de Reservación",
        "dear": "Estimado/a",
        "quote_intro": "Gracias por considerar a Casa Dorada Los Cabos Resort & Spa para su próxima estadía. A continuación encontrará su cotización personalizada y las opciones disponibles.",
        "conf_intro": "Estamos encantados de confirmar su reservación en Casa Dorada Los Cabos Resort & Spa.",
        "your_stay": "Su Estadía",
        "reservation_details": "Detalles de la Reservación",
        "guests": "Huéspedes",
        "adults": "Adultos",
        "children": "Niños",
        "nights": "Noches",
        "night": "Noche",
        "arrival": "Llegada",
        "departure": "Salida",
        "available_options": "Opciones Disponibles",
        "option": "Opción",
        "room_type": "Tipo de Habitación",
        "rate_details": "Detalles de la Tarifa",
        "rate_before_taxes": "Tarifa por noche sin impuestos",
        "rate_with_taxes": "Tarifa por noche con impuestos",
        "number_nights": "Número de noches",
        "stay_total": "Total de la estadía con impuestos",
        "included": "Incluye",
        "included_benefits": "Beneficios Incluidos",
        "additional_services": "Servicios Adicionales",
        "additional_total": "Total de servicios adicionales",
        "total_amount": "MONTO TOTAL",
        "deposit_policy": "Política de Depósito",
        "cancellation_policy": "Política de Cancelación",
        "quote_valid": "Cotización válida hasta",
        "conf_number": "Número de Confirmación",
        "payment_status": "Estado de Pago",
        "deposit": "Depósito",
        "balance_due": "Saldo Pendiente",
        "special_requests": "Solicitudes Especiales",
        "no_inclusions": "Sin inclusiones seleccionadas",
        "no_services": "Sin servicios adicionales",
        "view_room": "VER HABITACIÓN",
        "secure_booking": "ASEGURE SU RESERVA",
        "fully_paid": "Pagado en su totalidad",
        "first_night_deposit": "Depósito de la primera noche",
        "fully_paid_policy": "La reservación está totalmente pagada.",
        "first_night_policy": "La reservación está garantizada con el depósito de la primera noche, saldo a pagar al check in: "
    }
}


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
# SUPABASE HEADERS
# ============================================================

def get_supabase_headers(
    prefer=None,
):

    config = get_supabase_config()

    if not config:
        return None

    headers = {

        "apikey":
            config["key"],

        "Authorization":
            f"Bearer {config['key']}",

        "Content-Type":
            "application/json",
    }

    if prefer:

        headers["Prefer"] = prefer

    return headers


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

    headers = get_supabase_headers(
        "resolution=merge-duplicates,return=minimal"
    )

    now = datetime.now(timezone.utc).isoformat()

    payload = {

        "email":
            email.lower().strip(),

        "refresh_token":
            refresh_token,

        "created_at":
            now,

        "updated_at":
            now,
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


def get_saved_refresh_token(
    email,
):

    if not email:
        return None

    config = get_supabase_config()

    if not config:
        return None

    endpoint = (
        f"{config['url']}/rest/v1/google_tokens"
    )

    headers = get_supabase_headers()

    params = {

        "email":
            f"eq.{email.lower().strip()}",

        "select":
            "refresh_token",

        "limit":
            "1",
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
# QUOTATIONS & CONFIRMATIONS DATABASE
# ============================================================

def generate_quotation_number():

    today = datetime.now(timezone.utc)

    date_part = today.strftime(
        "%y%m%d"
    )

    random_part = (
        secrets.randbelow(9000)
        + 1000
    )

    return (
        f"CD{date_part}-{random_part}"
    )


def generate_confirmation_number():

    today = datetime.now(timezone.utc)

    date_part = today.strftime(
        "%y%m%d"
    )

    random_part = (
        secrets.randbelow(9000)
        + 1000
    )

    return (
        f"CN{date_part}-{random_part}"
    )


def prepare_options_for_database(
    options,
    nights,
):

    database_options = []

    for option in options:

        calculations = (
            calculate_rate_values(
                option[
                    "stay_total_tax_included"
                ],
                nights,
            )
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

        database_options.append({

            "room_type":
                option[
                    "room_type"
                ],

            "adults":
                int(option.get(
                    "adults", 2
                )),

            "children":
                int(option.get(
                    "children", 0
                )),

            "valid_until":
                str(
                    option[
                        "valid_until"
                    ]
                ),

            "stay_total_tax_included":
                float(
                    option[
                        "stay_total_tax_included"
                    ]
                ),

            "nightly_before_tax":
                float(
                    calculations[
                        "nightly_before_tax"
                    ]
                ),

            "nightly_taxes_included":
                float(
                    calculations[
                        "nightly_with_tax"
                    ]
                ),

            "stay_total_before_tax":
                float(
                    calculations[
                        "total_before_tax"
                    ]
                ),

            "taxes":
                float(
                    calculations[
                        "taxes"
                    ]
                ),

            "selected_inclusions":
                option[
                    "selected_inclusions"
                ],

            "selected_services":
                option[
                    "selected_services"
                ],

            "additional_services_total":
                float(
                    services_total
                ),

            "final_total":
                float(
                    final_total
                ),

            "deposit_policy":
                option[
                    "deposit_policy"
                ],

            "cancellation_policy":
                option[
                    "cancellation_policy"
                ],

            "payment_url":
                option[
                    "payment_url"
                ],

            "room_360_url":
                option[
                    "room_360_url"
                ],
        })

    return database_options


def save_quotation_to_supabase(
    guest_name,
    guest_email,
    arrival,
    departure,
    nights,
    adults,
    children,
    options,
    created_by,
    status="QUOTED",
):

    config = get_supabase_config()

    if not config:
        return None

    endpoint = (
        f"{config['url']}/rest/v1/quotations"
    )

    headers = get_supabase_headers(
        "return=representation"
    )

    database_options = (
        prepare_options_for_database(
            options,
            nights,
        )
    )

    quotation_number = (
        generate_quotation_number()
    )

    payload = {

        "quotation_number":
            quotation_number,

        "guest_name":
            guest_name,

        "guest_email":
            guest_email,

        "arrival":
            str(arrival),

        "departure":
            str(departure),

        "nights":
            int(nights),

        "adults":
            int(adults),

        "children":
            int(children),

        "options":
            database_options,

        "total_amount":
            None,

        "payment_url":
            None,

        "status":
            status,

        "created_by":
            created_by,
    }

    try:

        response = requests.post(

            endpoint,

            headers=headers,

            json=payload,

            timeout=20,
        )

        if response.status_code not in [
            200,
            201,
        ]:

            st.session_state[
                "quotation_database_error"
            ] = (
                f"HTTP {response.status_code}: "
                f"{response.text}"
            )

            return None

        data = response.json()

        if not data:
            return None

        quotation = data[0]

        return quotation

    except Exception as e:

        st.session_state[
            "quotation_database_error"
        ] = str(e)

        return None


def search_quotations_in_supabase(search_term):
    
    config = get_supabase_config()

    if not config:
        return []

    endpoint = f"{config['url']}/rest/v1/quotations"

    headers = get_supabase_headers()

    term = search_term.strip()
    
    params = {
        "or": f"(quotation_number.ilike.*{term}*,guest_name.ilike.*{term}*,guest_email.ilike.*{term}*)",
        "order": "created_at.desc",
        "limit": "20",
    }
    
    try:

        response = requests.get(
            endpoint, 
            headers=headers, 
            params=params, 
            timeout=15
        )

        if response.status_code != 200:

            st.session_state["quotation_database_error"] = f"HTTP {response.status_code}: {response.text}"
            return []

        return response.json()

    except Exception as e:

        st.session_state["quotation_database_error"] = str(e)
        return []


def update_quotation_status(quotation_number, status="CONFIRMED"):

    config = get_supabase_config()

    if not config:
        return False
        
    endpoint = f"{config['url']}/rest/v1/quotations"

    headers = get_supabase_headers()

    params = {
        "quotation_number": f"eq.{quotation_number}"
    }

    payload = {
        "status": status
    }
    
    try:

        response = requests.patch(
            endpoint, 
            headers=headers, 
            params=params, 
            json=payload, 
            timeout=15
        )

        return response.status_code in [200, 204]

    except Exception:

        return False


def save_confirmation_to_supabase(
    confirmation_number,
    quotation_number,
    guest_name,
    guest_email,
    arrival,
    departure,
    nights,
    adults,
    children,
    room_type,
    rate_per_night,
    stay_total,
    first_night_amount,
    balance_due,
    payment_status,
    comments,
    special_requests,
    additional_services,
    created_by,
):

    config = get_supabase_config()

    if not config:
        return None

    endpoint = f"{config['url']}/rest/v1/confirmations"

    headers = get_supabase_headers("return=representation")

    payload = {
        "confirmation_number": confirmation_number,
        "quotation_number": quotation_number,
        "guest_name": guest_name,
        "guest_email": guest_email,
        "arrival": str(arrival),
        "departure": str(departure),
        "nights": int(nights),
        "adults": int(adults),
        "children": int(children),
        "room_type": room_type,
        "rate_per_night": float(rate_per_night),
        "stay_total": float(stay_total),
        "first_night_amount": float(first_night_amount),
        "balance_due": float(balance_due),
        "payment_status": payment_status,
        "comments": comments,
        "special_requests": special_requests,
        "additional_services": additional_services,
        "status": "CONFIRMED",
        "created_by": created_by,
        "confirmed_by": created_by,
    }

    try:

        response = requests.post(
            endpoint, 
            headers=headers, 
            json=payload, 
            timeout=20
        )

        if response.status_code not in [200, 201]:

            st.session_state["quotation_database_error"] = f"HTTP {response.status_code}: {response.text}"
            return None

        data = response.json()

        if not data:
            return None

        return data[0]

    except Exception as e:

        st.session_state["quotation_database_error"] = str(e)
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

                email = (
                    email
                    .lower()
                    .strip()
                )

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

    padding = "=" * (
        -len(value) % 4
    )

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

        encoded, signature = (
            state.split(
                ".",
                1,
            )
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
            datetime.now(timezone.utc).timestamp()
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

    code_challenge = (
        b64url_encode(
            hashlib.sha256(
                code_verifier.encode(
                    "utf-8"
                )
            ).digest()
        )
    )

    payload = {

        "code_verifier":
            code_verifier,

        "created_at":
            datetime.now(timezone.utc).timestamp(),
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
            " ".join(
                GMAIL_SCOPES
            ),

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

def credentials_to_dict(
    credentials,
):

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
# EXECUTE PENDING ACTIONS CORE LOGIC
# ============================================================

def execute_pending_quote():

    pending_quote = st.session_state.get("pending_quote")
    pending_action = st.session_state.get("pending_action")
    logged_email = get_logged_in_email()
    
    if not pending_quote or not pending_action:
        return False
        
    try:

        if pending_action == "draft":

            save_gmail_draft(
                to_email=pending_quote["guest_email"],
                subject=pending_quote["subject"],
                html_body=pending_quote["email_html"],
                plain_text_body=pending_quote["plain_text_email"],
            )

            quotation = save_quotation_to_supabase(
                guest_name=pending_quote["guest_name"],
                guest_email=pending_quote["guest_email"],
                arrival=pending_quote["arrival"],
                departure=pending_quote["departure"],
                nights=pending_quote["nights"],
                adults=pending_quote["options"][0].get("adults", 2) if pending_quote.get("options") else pending_quote.get("adults", 2),
                children=pending_quote["options"][0].get("children", 0) if pending_quote.get("options") else pending_quote.get("children", 0),
                options=pending_quote["options"],
                created_by=logged_email,
                status="QUOTED",
            )

            st.session_state.pending_quote = None
            st.session_state.pending_action = None

            if quotation:
                st.session_state.auto_draft_success = quotation["quotation_number"]
            else:
                st.session_state.auto_draft_success = "Draft saved successfully in Gmail."

        elif pending_action == "send":

            send_gmail_message(
                to_email=pending_quote["guest_email"],
                subject=pending_quote["subject"],
                html_body=pending_quote["email_html"],
                plain_text_body=pending_quote["plain_text_email"],
            )

            quotation = save_quotation_to_supabase(
                guest_name=pending_quote["guest_name"],
                guest_email=pending_quote["guest_email"],
                arrival=pending_quote["arrival"],
                departure=pending_quote["departure"],
                nights=pending_quote["nights"],
                adults=pending_quote["options"][0].get("adults", 2) if pending_quote.get("options") else pending_quote.get("adults", 2),
                children=pending_quote["options"][0].get("children", 0) if pending_quote.get("options") else pending_quote.get("children", 0),
                options=pending_quote["options"],
                created_by=logged_email,
                status="SENT",
            )

            st.session_state.pending_quote = None
            st.session_state.pending_action = None

            if quotation:
                st.session_state.auto_send_success = quotation["quotation_number"]
            else:
                st.session_state.auto_send_success = "Email sent successfully."

        return True

    except Exception as e:

        st.session_state.pending_action_error = str(e)
        st.session_state.pending_quote = None
        st.session_state.pending_action = None
        return False


def execute_pending_confirmation():

    pending_confirmation = st.session_state.get("pending_confirmation")
    pending_action = st.session_state.get("pending_action")
    logged_email = get_logged_in_email()
    
    if not pending_confirmation or not pending_action:
        return False
        
    try:

        if pending_action == "draft":

            save_gmail_draft(
                to_email=pending_confirmation["guest_email"],
                subject=pending_confirmation["subject"],
                html_body=pending_confirmation["email_html"],
                plain_text_body=pending_confirmation["plain_text_email"],
            )

        elif pending_action == "send":

            send_gmail_message(
                to_email=pending_confirmation["guest_email"],
                subject=pending_confirmation["subject"],
                html_body=pending_confirmation["email_html"],
                plain_text_body=pending_confirmation["plain_text_email"],
            )
        
        conf = save_confirmation_to_supabase(
            confirmation_number=pending_confirmation["confirmation_number"],
            quotation_number=pending_confirmation["quotation_number"],
            guest_name=pending_confirmation["guest_name"],
            guest_email=pending_confirmation["guest_email"],
            arrival=pending_confirmation["arrival"],
            departure=pending_confirmation["departure"],
            nights=pending_confirmation["nights"],
            adults=pending_confirmation["adults"],
            children=pending_confirmation["children"],
            room_type=pending_confirmation["room_type"],
            rate_per_night=pending_confirmation["rate_per_night"],
            stay_total=pending_confirmation["stay_total"],
            first_night_amount=pending_confirmation["first_night_amount"],
            balance_due=pending_confirmation["balance_due"],
            payment_status=pending_confirmation["payment_status"],
            comments=pending_confirmation["comments"],
            special_requests=pending_confirmation["special_requests"],
            additional_services=pending_confirmation["additional_services"],
            created_by=logged_email,
        )
        
        if conf and pending_confirmation["quotation_number"]:

            update_quotation_status(pending_confirmation["quotation_number"], "CONFIRMED")
            
        st.session_state.pending_confirmation = None
        st.session_state.pending_action = None
        
        if conf:

            if pending_action == "draft":
                st.session_state.conf_auto_draft_success = conf["confirmation_number"]
            else:
                st.session_state.conf_auto_send_success = conf["confirmation_number"]

        else:

            if pending_action == "draft":
                st.session_state.conf_auto_draft_success = "Action completed, but database save failed."
            else:
                st.session_state.conf_auto_send_success = "Action completed, but database save failed."

        return True

    except Exception as e:

        st.session_state.pending_action_error = str(e)
        st.session_state.pending_confirmation = None
        st.session_state.pending_action = None
        return False


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

        email = (
            email
            .lower()
            .strip()
        )

        if not email.endswith(
            "@casadorada.com"
        ):

            st.error(
                "The Gmail account must be a "
                "@casadorada.com account."
            )

            st.query_params.clear()

            return False

        logged_email = (
            get_logged_in_email()
        )

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

        if st.session_state.get("pending_quote"):

            execute_pending_quote()

        elif st.session_state.get("pending_confirmation"):

            execute_pending_confirmation()

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

    logged_email = (
        get_logged_in_email()
    )

    if not logged_email:
        return None

    logged_email = (
        logged_email
        .lower()
        .strip()
    )

    data = (
        st.session_state.get(
            "google_credentials"
        )
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

    credentials = (
        get_credentials()
    )

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

    credentials = (
        get_credentials()
    )

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

        email = (
            email
            .lower()
            .strip()
        )

        if not email.endswith(
            "@casadorada.com"
        ):
            return None

        logged_email = (
            get_logged_in_email()
        )

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

def money(value, currency="USD"):

    try:

        return "${:,.2f} {}".format(
            float(value),
            currency
        )

    except Exception:

        return "$0.00 {}".format(currency)


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

def format_date_email(value, lang="en"):

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

        if lang == "es":

            months_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            return f"{d.day} de {months_es[d.month-1]} de {d.year}"

        else:

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
    lang="en",
    currency="USD",
    adults=2,
    children=0
):

    t = TRANSLATIONS[lang]

    calculations = (
        calculate_rate_values(
            stay_total_tax_included,
            nights,
        )
    )

    total_with_tax = (
        calculations[
            "total_with_tax"
        ]
    )

    nightly_with_tax = (
        calculations[
            "nightly_with_tax"
        ]
    )

    nightly_before_tax = (
        calculations[
            "nightly_before_tax"
        ]
    )

    guest_summary = f"{adults} {t['adults']}"

    if children > 0:

        guest_summary += f" + {children} {t['children']}"

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

        inclusions_html = f"""
        <li style="
            color:#777777;
            font-size:14px;
        ">
            {t["no_inclusions"]}
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
                {money(price, currency)}
            </td>

        </tr>
        """

    if not services_html:

        services_html = f"""
        <tr>

            <td colspan="2"
                style="
                    padding:6px 0;
                    color:#777777;
                    font-size:14px;
                    text-align:left;
                ">
                {t["no_services"]}
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
           {t["view_room"]}
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
           {t["secure_booking"]}
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
                    {t["option"]} {option_number}
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
                    {t["rate_details"]}
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
                            {t["rate_before_taxes"]}
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                        ">
                            {money(nightly_before_tax, currency)}
                        </td>

                    </tr>

                    <tr>

                        <td style="
                            padding:6px 0;
                            color:#555555;
                            font-size:14px;
                            text-align:left;
                        ">
                            {t["rate_with_taxes"]}
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(nightly_with_tax, currency)}
                        </td>

                    </tr>

                    <tr>

                        <td style="
                            padding:6px 0;
                            color:#555555;
                            font-size:14px;
                            text-align:left;
                        ">
                            {t["number_nights"]}
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
                            text-align:left;
                        ">
                            {t["guests"]}
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                        ">
                            {html_escape(guest_summary)}
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
                            {t["stay_total"]}
                        </td>

                        <td style="
                            border-top:1px solid #eeeeee;
                            padding:10px 0 6px 0;
                            color:#1f4f78;
                            font-size:16px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(total_with_tax, currency)}
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
                    {t["included"]}
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
                    {t["additional_services"]}
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
                            {t["additional_total"]}
                        </td>

                        <td style="
                            border-top:1px solid #eeeeee;
                            padding-top:10px;
                            color:#222222;
                            font-size:14px;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {money(additional_services_total, currency)}
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
                                {t["total_amount"]}
                            </td>

                            <td style="
                                color:#1f4f78;
                                font-size:20px;
                                font-weight:bold;
                                text-align:right;
                            ">
                                {money(final_total, currency)}
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
                        {t["deposit_policy"]}
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
                        {t["cancellation_policy"]}
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

                    {t["quote_valid"]}: 
                    <strong>
                        {html_escape(
                            format_date_email(
                                valid_until, lang
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
    nights,
    options,
    lang="en",
    currency="USD"
):

    t = TRANSLATIONS[lang]

    lines = []

    lines.append(
        t["custom_quotation"].upper()
    )

    lines.append("")

    lines.append(
        f"{t['dear']} {guest_name},"
    )

    lines.append("")

    lines.append(
        t["quote_intro"]
    )

    lines.append("")

    lines.append(
        t["your_stay"].upper()
    )

    lines.append(
        f"{t['nights']}: {nights}"
    )

    lines.append(
        f"{t['arrival']}: {format_date_email(arrival, lang)}"
    )

    lines.append(
        f"{t['departure']}: {format_date_email(departure, lang)}"
    )

    lines.append("")

    lines.append(
        t["available_options"].upper()
    )

    lines.append("")

    for index, option in enumerate(
        options,
        start=1,
    ):

        calculations = (
            calculate_rate_values(
                option[
                    "stay_total_tax_included"
                ],
                nights,
            )
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

        opt_adults = option.get("adults", 2)
        opt_children = option.get("children", 0)

        guest_summary = f"{opt_adults} {t['adults']}"

        if opt_children > 0:

            guest_summary += f", {opt_children} {t['children']}"

        lines.append(
            f"{t['option'].upper()} {index}"
        )

        lines.append(
            f"{t['room_type']}: {option['room_type']}"
        )

        lines.append(
            f"{t['guests']}: {guest_summary}"
        )

        lines.append(
            f"{t['rate_before_taxes']}: "
            f"{money(calculations['nightly_before_tax'], currency)}"
        )

        lines.append(
            f"{t['rate_with_taxes']}: "
            f"{money(calculations['nightly_with_tax'], currency)}"
        )

        lines.append(
            f"{t['number_nights']}: {nights}"
        )

        lines.append(
            f"{t['stay_total']}: "
            f"{money(calculations['total_with_tax'], currency)}"
        )

        lines.append("")

        lines.append(
            f"{t['included']}:"
        )

        if option["selected_inclusions"]:
            for inclusion in option[
                "selected_inclusions"
            ]:

                lines.append(
                    f"• {inclusion}"
                )
        else:
            lines.append(t["no_inclusions"])

        lines.append("")

        lines.append(
            f"{t['additional_services']}:"
        )

        if option[
            "selected_services"
        ]:

            for service in option[
                "selected_services"
            ]:

                lines.append(
                    f"• {service}: "
                    f"{money(ADDITIONAL_SERVICES[service], currency)}"
                )

        else:

            lines.append(
                t["no_services"]
            )

        lines.append("")

        lines.append(
            f"{t['total_amount']}: "
            f"{money(final_total, currency)}"
        )

        lines.append("")

        lines.append(
            f"{t['deposit_policy']}:"
        )

        lines.append(
            option[
                "deposit_policy"
            ]
        )

        lines.append("")

        lines.append(
            f"{t['cancellation_policy']}:"
        )

        lines.append(
            option[
                "cancellation_policy"
            ]
        )

        lines.append("")

        lines.append(
            f"{t['quote_valid']}: "
            f"{format_date_email(option['valid_until'], lang)}"
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
    nights,
    options,
    lang="en",
    currency="USD"
):

    t = TRANSLATIONS[lang]

    options_html = ""

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

            lang=lang,
            
            currency=currency,

            adults=option.get(
                "adults", 2
            ),

            children=option.get(
                "children", 0
            )
        )

    return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>{t["custom_quotation"]}</title>

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

<table width="750"
       cellpadding="0"
       cellspacing="0"
       border="0"
       style="
           width:750px;
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

{t["custom_quotation"]}

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

{t["dear"]} {html_escape(guest_name)},

</p>

<p style="
    color:#555555;
    font-size:14px;
    line-height:1.6;
    margin:0;
    text-align:left;
">

{t["quote_intro"]}

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

{t["your_stay"]}

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

{t["nights"]}

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
{(" " + t["night"]) if nights == 1 else (" " + t["nights"])}

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

{t["arrival"]}

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
    format_date_email(arrival, lang)
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

{t["departure"]}

</td>

<td style="
    padding:10px 14px;
    color:#1f2937;
    font-size:13px;
    font-weight:bold;
    text-align:left;
">

{html_escape(
    format_date_email(departure, lang)
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

{t["available_options"]}

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
# CONFIRMATION EMAIL HTML
# ============================================================

def build_confirmation_email_html(
    confirmation_number,
    guest_name,
    arrival,
    departure,
    adults,
    children,
    nights,
    room_type,
    rate_per_night,
    stay_total,
    first_night_amount,
    balance_due,
    payment_status,
    special_requests,
    deposit_policy,
    cancellation_policy,
    selected_inclusions,
    selected_services,
    lang="en",
    currency="USD"
):

    t = TRANSLATIONS[lang]
    rate_before_taxes = float(rate_per_night) / (1 + TAX_RATE)

    guest_summary = f"{adults} {t['adults']}"

    if children > 0:
        guest_summary += f" + {children} {t['children']}"

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
        inclusions_html = f"""
        <li style="
            color:#777777; 
            font-size:14px;
        ">
            {t['no_inclusions']}
        </li>
        """

    services_html = ""

    if selected_services:
        for service in selected_services:
            services_html += f"""
            <tr>
                <td style="
                    padding:6px 0; 
                    color:#555555; 
                    font-size:14px; 
                    text-align:left;
                ">
                    • {html_escape(service)}
                </td>
            </tr>
            """
    else:
        services_html = f"""
        <tr>
            <td style="
                padding:6px 0; 
                color:#777777; 
                font-size:14px; 
                text-align:left;
            ">
                {t['no_services']}
            </td>
        </tr>
        """

    special_html = ""

    if special_requests:
        special_html = f"""
        <div style="
            color:#1f4f78; 
            font-size:14px; 
            font-weight:bold; 
            margin-top:15px; 
            margin-bottom:6px; 
            text-align:left;
        ">
            {t['special_requests']}
        </div>

        <div style="
            color:#555555; 
            font-size:13px; 
            line-height:1.5; 
            text-align:left;
        ">
            {html_escape(special_requests)}
        </div>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t['reservation_confirmation']}</title>
</head>
<body style="margin:0; padding:0; background:#f3f4f6; font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="left" style="padding:30px 10px;">
<table width="750" cellpadding="0" cellspacing="0" border="0" style="width:750px; max-width:100%; background:#ffffff; border:1px solid #dddddd;">
<tr>
<td align="left" style="background:#ffffff; padding:25px 35px 15px 35px;">
<img src="{EMAIL_LOGO_URL}" alt="Casa Dorada" style="max-width:220px; width:100%; height:auto; display:block;">
</td>
</tr>
<tr>
<td style="padding:15px 35px 5px 35px; text-align:left;">
<div style="color:#1f4f78; font-size:25px; font-weight:bold; text-align:left;">{t['reservation_confirmation']}</div>
<div style="color:#222222; font-size:16px; font-weight:bold; margin-top:5px;">{t['conf_number']}: {html_escape(confirmation_number)}</div>
</td>
</tr>
<tr>
<td style="padding:15px 35px 10px 35px; text-align:left;">
<p style="color:#333333; font-size:15px; line-height:1.6; margin:0 0 12px 0; text-align:left;">{t['dear']} {html_escape(guest_name)},</p>
<p style="color:#555555; font-size:14px; line-height:1.6; margin:0; text-align:left;">{t['conf_intro']}</p>
</td>
</tr>
<tr>
<td style="padding:20px 35px 20px 35px; text-align:left;">
<div style="color:#1f4f78; font-size:19px; font-weight:bold; margin-bottom:12px; text-align:left;">{t['reservation_details']}</div>
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="padding:6px 0; width:45%; color:#555555; font-size:14px; text-align:left;">{t['guests']}</td><td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{html_escape(guest_summary)}</td></tr>
<tr><td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t['arrival']}</td><td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{html_escape(format_date_email(arrival, lang))}</td></tr>
<tr><td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t['departure']}</td><td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{html_escape(format_date_email(departure, lang))}</td></tr>
<tr><td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t['nights']}</td><td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{html_escape(nights)}</td></tr>
<tr><td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t['room_type']}</td><td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{html_escape(room_type)}</td></tr>
<tr><td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t['rate_before_taxes']}</td><td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{money(rate_before_taxes, currency)}</td></tr>
<tr><td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t['rate_with_taxes']}</td><td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{money(rate_per_night, currency)}</td></tr>
<tr><td style="border-top:1px solid #eeeeee; padding:10px 0 6px 0; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">{t['total_amount']}</td><td style="border-top:1px solid #eeeeee; padding:10px 0 6px 0; color:#1f4f78; font-size:16px; text-align:right; font-weight:bold;">{money(stay_total, currency)}</td></tr>
</table>
<div style="margin-top:20px; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">{t['included_benefits']}</div>
<ul style="padding-left:22px; margin-top:8px; margin-bottom:15px; text-align:left;">{inclusions_html}</ul>
<div style="margin-top:15px; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">{t['additional_services']}</div>
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;">{services_html}</table>
<div style="margin-top:20px; padding-top:15px; border-top:1px solid #eeeeee;">
<div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-bottom:6px; text-align:left;">{t['deposit_policy']}</div>
<div style="color:#555555; font-size:13px; line-height:1.5; text-align:left;">{html_escape(deposit_policy)}</div>
<div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-top:15px; margin-bottom:6px; text-align:left;">{t['cancellation_policy']}</div>
<div style="color:#555555; font-size:13px; line-height:1.5; text-align:left;">{html_escape(cancellation_policy)}</div>
{special_html}
</div>
</td>
</tr>
<tr>
<td style="background:#1f4f78; padding:22px 30px; text-align:left;">
<div style="color:#ffffff; font-size:14px; font-weight:bold; margin-bottom:6px; text-align:left;">Casa Dorada Los Cabos Resort & Spa</div>
<div style="color:#dbeafe; font-size:12px; line-height:1.5; text-align:left;">Av. del Pescador s/n, Cabo San Lucas, B.C.S.</div>
<div style="color:#dbeafe; font-size:12px; line-height:1.5; text-align:left;">US: <a href="tel:18664480151" style="color:#ffffff; text-decoration:none;">1-866-448-0151</a></div>
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
# PLAIN TEXT EMAIL
# ============================================================

def build_confirmation_plain_text(
    confirmation_number, 
    guest_name, 
    arrival, 
    departure, 
    adults, 
    children, 
    nights,
    room_type, 
    rate_per_night, 
    stay_total, 
    first_night_amount, 
    balance_due,
    payment_status, 
    special_requests, 
    deposit_policy, 
    cancellation_policy,
    selected_inclusions, 
    selected_services,
    lang="en",
    currency="USD"
):

    t = TRANSLATIONS[lang]
    rate_before_taxes = float(rate_per_night) / (1 + TAX_RATE)

    lines = []

    lines.append(t["reservation_confirmation"].upper())
    lines.append(f"{t['conf_number']}: {confirmation_number}")
    lines.append("")
    lines.append(f"{t['dear']} {guest_name},")
    lines.append(t["conf_intro"])
    lines.append("")
    lines.append(t["reservation_details"].upper())
    
    if children > 0:
        lines.append(f"{t['guests']}: {adults} {t['adults']}, {children} {t['children']}")
    else:
        lines.append(f"{t['guests']}: {adults} {t['adults']}")

    lines.append(f"{t['arrival']}: {format_date_email(arrival, lang)}")
    lines.append(f"{t['departure']}: {format_date_email(departure, lang)}")
    lines.append(f"{t['nights']}: {nights}")
    lines.append(f"{t['room_type']}: {room_type}")
    lines.append(f"{t['rate_before_taxes']}: {money(rate_before_taxes, currency)}")
    lines.append(f"{t['rate_with_taxes']}: {money(rate_per_night, currency)}")
    lines.append(f"{t['total_amount']}: {money(stay_total, currency)}")
    lines.append("")
    lines.append(f"{t['included_benefits']}:")

    if selected_inclusions:
        for inc in selected_inclusions:
            lines.append(f"• {inc}")
    else:
        lines.append(t["no_inclusions"])

    lines.append("")
    lines.append(f"{t['additional_services']}:")

    if selected_services:
        for srv in selected_services:
            lines.append(f"• {srv}")
    else:
        lines.append(t["no_services"])

    lines.append("")
    lines.append(f"{t['deposit_policy']}:")
    lines.append(deposit_policy)
    lines.append("")
    lines.append(f"{t['cancellation_policy']}:")
    lines.append(cancellation_policy)

    if special_requests:
        lines.append("")
        lines.append(f"{t['special_requests']}:")
        lines.append(special_requests)

    lines.append("")
    lines.append("----------------------------------------")
    lines.append("Casa Dorada Los Cabos Resort & Spa")
    lines.append("Av. del Pescador s/n, Cabo San Lucas, B.C.S.")
    lines.append("US: 1-866-448-0151")

    return "\n".join(lines)

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

    "google_connected":
        False,

    "google_credentials":
        None,

    "google_email":
        None,

    "gmail_auth_error":
        None,

    "supabase_save_error":
        None,

    "supabase_get_error":
        None,

    "quotation_database_error":
        None,

    "pending_quote":
        None,

    "pending_confirmation":
        None,

    "pending_action":
        None,

    "auto_draft_success":
        False,

    "auto_send_success":
        False,

    "conf_auto_draft_success":
        False,

    "conf_auto_send_success":
        False,

    "pending_action_error":
        None,

    "confirm_search_results":
        [],

    "selected_quote":
        None,

    "app_lang": 
        "English",

    "app_currency": 
        "USD"

}


for key, default_value in (
    SESSION_DEFAULTS.items()
):

    if key not in st.session_state:

        st.session_state[
            key
        ] = default_value


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

logged_email = (
    get_logged_in_email()
)

if logged_email:

    st.session_state.google_email = (
        logged_email
    )

    restored_credentials = (
        get_credentials()
    )

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

    result = (
        st.session_state.auto_draft_success
    )

    if isinstance(result, str) and result.startswith(
        "CD"
    ):

        st.success(
            f"Draft saved successfully in Gmail. "
            f"Quotation #{result}"
        )

    else:

        st.success(
            "Draft saved successfully in Gmail."
        )

    st.session_state.auto_draft_success = False


if st.session_state.get(
    "auto_send_success"
):

    result = (
        st.session_state.auto_send_success
    )

    if isinstance(result, str) and result.startswith(
        "CD"
    ):

        st.success(
            f"Email sent successfully. "
            f"Quotation #{result}"
        )

    else:

        st.success(
            "Email sent successfully."
        )

    st.session_state.auto_send_success = False


if st.session_state.get(
    "pending_action_error"
):

    st.error(
        "The operation was recovered, "
        "but the email action could not be completed."
    )

    with st.expander(
        "Technical details"
    ):

        st.code(
            st.session_state.pending_action_error
        )

    st.session_state.pending_action_error = None


if st.session_state.get(
    "quotation_database_error"
):

    with st.expander(
        "Database diagnostics"
    ):

        st.code(
            st.session_state[
                "quotation_database_error"
            ]
        )

    st.session_state[
        "quotation_database_error"
    ] = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## Navigation"
    )

    app_mode = st.radio(
        "Select View", 
        [
            "Create Quotation", 
            "Confirm Quotation", 
            "Manual Confirmation"
        ]
    )

    st.divider()

    st.markdown(
        "## Global Settings"
    )

    st.session_state.app_lang = st.radio(
        "Language / Idioma", 
        ["English", "Español"], 
        index=0 if st.session_state.app_lang == "English" else 1
    )

    st.session_state.app_currency = st.radio(
        "Currency / Moneda", 
        ["USD", "MXN"], 
        index=0 if st.session_state.app_currency == "USD" else 1
    )

    lang_code = "en" if st.session_state.app_lang == "English" else "es"
    curr_code = st.session_state.app_currency

    st.divider()

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

    if app_mode == "Create Quotation":

        st.divider()

        st.markdown(
            "### Quote Settings"
        )

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
# WORKFLOW: CREATE QUOTATION
# ============================================================

if app_mode == "Create Quotation":

    st.title(
        "Create Quotation"
    )

    st.caption(
        "Create a professional quotation "
        "for your guest."
    )

    st.markdown(
        "## Guest Information"
    )

    st.caption(
        "Basic information for the quotation."
    )

    guest_col1, guest_col2 = (
        st.columns(2)
    )

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

    guest_col3, guest_col4, guest_col5 = (
        st.columns(3)
    )

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

    calculated_nights = (
        departure - arrival
    ).days

    if calculated_nights < 1:

        calculated_nights = 1

    with guest_col5:

        nights = st.number_input(
            "Nights",
            min_value=1,
            max_value=365,
            value=calculated_nights,
            step=1,
        )

    st.divider()

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

        st.markdown(
            "### Guests"
        )

        opt_g1, opt_g2 = (
            st.columns(2)
        )

        with opt_g1:

            opt_adults = st.number_input(
                "Adults", 
                min_value=1, 
                max_value=20, 
                value=2, 
                step=1, 
                key=f"adults_{option_number}"
            )

        with opt_g2:

            opt_children = st.number_input(
                "Children", 
                min_value=0, 
                max_value=20, 
                value=0, 
                step=1, 
                key=f"children_{option_number}"
            )

        st.markdown(
            "### Rate"
        )

        st.caption(
            "Enter the total stay amount with taxes included. "
            "The system will calculate all rates automatically."
        )

        rate_col1, rate_col2 = (
            st.columns(2)
        )

        with rate_col1:

            stay_total_tax_included = (
                st.number_input(

                    f"Stay Total Taxes Included ({curr_code})",

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
                    ],
                    curr_code
                ),
            )

        with rate_col4:

            st.metric(
                "Nightly Taxes Included",
                money(
                    calculations[
                        "nightly_with_tax"
                    ],
                    curr_code
                ),
            )

        with rate_col5:

            st.metric(
                "Stay Before Taxes",
                money(
                    calculations[
                        "total_before_tax"
                    ],
                    curr_code
                ),
            )

        with rate_col6:

            st.metric(
                "Taxes 30%",
                money(
                    calculations[
                        "taxes"
                    ],
                    curr_code
                ),
            )

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

        inclusion_columns = (
            st.columns(2)
        )

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

        st.markdown(
            "### Additional Services"
        )

        st.caption(
            "Select any additional services. "
            "Their prices will be added automatically."
        )

        service_columns = (
            st.columns(2)
        )

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

                    f"{service} — {money(price, curr_code)}",

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
            money(final_total, curr_code),
        )

        st.markdown(
            "### Deposit Policy"
        )

        if lang_code == "es":

            quotation_deposit_policies = [
                "Se requiere el pago total de la estadía con impuestos incluidos al momento de reservar.",
                "Se requiere el depósito de la primera noche con impuestos incluidos al momento de reservar."
            ]

        else:

            quotation_deposit_policies = [
                "The deposit for the whole stay with taxes included is required upon booking.",
                "The deposit for the first night with taxes included is required upon booking."
            ]

        deposit_policy = st.selectbox(

            "Select deposit policy",

            quotation_deposit_policies,

            key=(
                f"deposit_policy_"
                f"{option_number}"
            ),
        )
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

        st.markdown(
            "### Optional Links"
        )

        link_col1, link_col2 = (
            st.columns(2)
        )

        with link_col1:

            room_360_url = (
                ROOM_TYPES[
                    room_type
                ].get(
                    "360_url",
                    ""
                )
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

            "room_type":
                room_type,

            "adults":
                opt_adults,

            "children":
                opt_children,

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

    email_html = build_email_html(

        guest_name=(
            guest_name
            or "Guest"
        ),

        arrival=arrival,

        departure=departure,

        nights=nights,

        options=all_options,

        lang=lang_code,

        currency=curr_code
    )

    plain_text_email = build_plain_text(

        guest_name=(
            guest_name
            or "Guest"
        ),

        arrival=arrival,

        departure=departure,

        nights=nights,

        options=all_options,

        lang=lang_code,

        currency=curr_code
    )

    st.markdown(
        "## Email Preview"
    )

    st.caption(
        "This preview simulates the actual email your guest will receive."
    )

    b64_email = base64.b64encode(email_html.encode('utf-8')).decode('utf-8')
    iframe_height = 850 + number_options * 750
    iframe_html = f'<iframe src="data:text/html;base64,{b64_email}" width="100%" height="{iframe_height}" style="border:none; border-radius:8px; background:#fff;"></iframe>'
    st.markdown(iframe_html, unsafe_allow_html=True)

    st.markdown(
        "## Actions"
    )

    action_col1, action_col2 = (
        st.columns(2)
    )

    subject = (
        f"{TRANSLATIONS[lang_code]['custom_quotation']} | "
        "Casa Dorada Los Cabos"
    )

    def store_pending_quote_ui(
        action
    ):

        st.session_state.pending_quote = {

            "guest_name":
                guest_name,

            "guest_email":
                guest_email,

            "arrival":
                arrival,

            "departure":
                departure,

            "nights":
                nights,

            "options":
                all_options,

            "subject":
                subject,

            "email_html":
                email_html,

            "plain_text_email":
                plain_text_email,
        }

        st.session_state.pending_action = (
            action
        )

    with action_col1:

        if st.button(

            "💾 Save Draft to Gmail",

            use_container_width=True,
        ):

            if not guest_name:

                st.error(
                    "Please enter the guest name."
                )

            elif not guest_email:

                st.error(
                    "Please enter the guest email."
                )

            else:

                store_pending_quote_ui("draft")

                gmail_service = (
                    get_gmail_service()
                )

                if gmail_service:

                    execute_pending_quote()
                    st.rerun()

                else:

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

    with action_col2:

        if st.button(

            "📤 Send Email",

            use_container_width=True,
        ):

            if not guest_name:

                st.error(
                    "Please enter the guest name."
                )

            elif not guest_email:

                st.error(
                    "Please enter the guest email."
                )

            else:

                store_pending_quote_ui("send")

                gmail_service = (
                    get_gmail_service()
                )

                if gmail_service:

                    execute_pending_quote()
                    st.rerun()

                else:

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


# ============================================================
# WORKFLOW: CONFIRM QUOTATION
# ============================================================

elif app_mode == "Confirm Quotation":

    st.title(
        "Confirm Quotation"
    )

    st.caption(
        "Search for an existing quotation and convert it "
        "into a confirmed reservation."
    )
    
    st.markdown(
        "## Search Quotation"
    )

    search_term = st.text_input(
        "Enter Quotation Number, Guest Name, or Guest Email", 
        placeholder="e.g. CD240101-1234 or guest@email.com"
    )
    
    if st.button("Search", use_container_width=True):

        if search_term:

            results = search_quotations_in_supabase(search_term)
            st.session_state.confirm_search_results = results
            st.session_state.selected_quote = None

        else:

            st.warning("Please enter a search term.")
            
    results = st.session_state.confirm_search_results

    if results:

        st.markdown(
            "### Search Results"
        )

        for q in results:

            with st.container():

                col1, col2, col3, col4 = st.columns([2, 3, 2, 2])

                col1.write(f"**{q['quotation_number']}**")
                col2.write(f"{q['guest_name']} ({q['guest_email']})")
                col3.write(f"{q['arrival']} to {q['departure']}")
                col4.write(f"Status: **{q['status']}**")
                
                if st.button("Select", key=f"sel_{q['quotation_number']}"):

                    if q['status'] in ['CONFIRMED', 'CANCELLED']:

                        st.error(
                            f"Cannot confirm this quotation. "
                            f"Current status is {q['status']}."
                        )

                        st.session_state.selected_quote = None

                    else:

                        st.session_state.selected_quote = q

                st.divider()

    selected_quote = st.session_state.selected_quote

    if selected_quote:

        st.markdown(
            f"## Confirming: {selected_quote['quotation_number']}"
        )

        st.write(
            f"**Guest:** {selected_quote['guest_name']} | "
            f"**Email:** {selected_quote['guest_email']}"
        )

        st.write(
            f"**Stay:** {selected_quote['arrival']} to {selected_quote['departure']} "
            f"({selected_quote['nights']} nights)"
        )
        
        st.markdown(
            "### Select Options to Confirm"
        )

        options = selected_quote.get("options", [])
        
        selected_options = []

        for i, opt in enumerate(options):

            if st.checkbox(
                f"Option {i+1}: {opt['room_type']} - {money(opt['final_total'], curr_code)}", 
                key=f"chk_opt_{selected_quote['quotation_number']}_{i}"
            ):
                selected_options.append(opt)
            
        if not selected_options:

            st.warning("Please select at least one option to continue.")

        else:

            # Sumar huéspedes, totales y combinar cuartos
            selected_opt_adults = sum(opt.get("adults", selected_quote.get("adults", 2)) for opt in selected_options)
            selected_opt_children = sum(opt.get("children", selected_quote.get("children", 0)) for opt in selected_options)
            
            room_type_str = " + ".join([opt["room_type"] for opt in selected_options])
            
            stay_total = sum(opt["final_total"] for opt in selected_options)
            rate_per_night = sum(opt["nightly_taxes_included"] for opt in selected_options)

            # Combinar inclusiones y servicios sin duplicados
            comb_inclusions = []
            comb_services = []

            for opt in selected_options:
                for inc in opt.get("selected_inclusions", []):
                    if inc not in comb_inclusions:
                        comb_inclusions.append(inc)
                for srv in opt.get("selected_services", []):
                    if srv not in comb_services:
                        comb_services.append(srv)

            can_policy_default = selected_options[0].get("cancellation_policy", CANCELLATION_POLICIES[0])

            st.markdown(
                "### Payment & Comments"
            )

            payment_status = st.radio(
                "Payment Status", 
                ["First Night Deposit", "Fully Paid"]
            )
            
            if payment_status == "Fully Paid":

                deposit = stay_total
                balance = 0.00
                payment_status_trans = TRANSLATIONS[lang_code]["fully_paid"]

            else:

                deposit = rate_per_night
                balance = stay_total - deposit
                payment_status_trans = TRANSLATIONS[lang_code]["first_night_deposit"]
                
            col1, col2, col3 = st.columns(3)

            col1.metric("Total Amount", money(stay_total, curr_code))
            col2.metric("Deposit", money(deposit, curr_code))
            col3.metric("Balance Due", money(balance, curr_code))
            
            comments = st.text_area(
                "Comments (Internal Notes)", 
                placeholder="e.g. Payment received by transfer."
            )

            special_requests = st.text_area(
                "Special Requests (Guest Needs)", 
                placeholder="e.g. Early check-in, Anniversary setup."
            )

            st.markdown(
                "### Confirmation Details"
            )

            hotel_conf_number = st.text_input(
                "Hotel Confirmation Number", 
                placeholder="Leave blank to auto-generate (CN...)"
            )

            t_ui = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])

            if payment_status == "Fully Paid":
                conf_deposit_policy = t_ui.get("fully_paid_policy", "Reservation is fully paid." if lang_code == "en" else "La reservación está totalmente pagada.")
            else:
                conf_deposit_policy = f"{t_ui.get('first_night_policy', 'Reservation is guaranteed with the first night deposit, balance to pay due check in: ')}{money(balance, curr_code)}"

            st.markdown(
                "### Deposit Policy"
            )

            st.info(conf_deposit_policy)

            st.markdown(
                "### Actions"
            )

            col_act1, col_act2 = st.columns(2)
            
            def store_pending_confirmation_ui(action):

                conf_number = hotel_conf_number.strip() if hotel_conf_number.strip() else generate_confirmation_number()

                st.session_state.pending_confirmation = {

                    "confirmation_number": 
                        conf_number,

                    "quotation_number": 
                        selected_quote["quotation_number"],

                    "guest_name": 
                        selected_quote["guest_name"],

                    "guest_email": 
                        selected_quote["guest_email"],

                    "arrival": 
                        selected_quote["arrival"],

                    "departure": 
                        selected_quote["departure"],

                    "nights": 
                        selected_quote["nights"],

                    "adults": 
                        selected_opt_adults,

                    "children": 
                        selected_opt_children,

                    "room_type": 
                        room_type_str,

                    "rate_per_night": 
                        rate_per_night,

                    "stay_total": 
                        stay_total,

                    "first_night_amount": 
                        deposit,

                    "balance_due": 
                        balance,

                    "payment_status": 
                        payment_status_trans,

                    "comments": 
                        comments,

                    "special_requests": 
                        special_requests,

                    "additional_services": 
                        selected_options,

                    "subject": 
                        f"Booking Confirmation #{conf_number} | Casa Dorada Los Cabos",

                    "email_html": build_confirmation_email_html(
                        conf_number, selected_quote["guest_name"], selected_quote["arrival"], 
                        selected_quote["departure"], selected_opt_adults, selected_opt_children, 
                        selected_quote["nights"], room_type_str, rate_per_night, stay_total, 
                        deposit, balance, payment_status_trans, special_requests, 
                        conf_deposit_policy, can_policy_default, comb_inclusions, 
                        comb_services, lang_code, curr_code
                    ),

                    "plain_text_email": build_confirmation_plain_text(
                        conf_number, selected_quote["guest_name"], selected_quote["arrival"], 
                        selected_quote["departure"], selected_opt_adults, selected_opt_children, 
                        selected_quote["nights"], room_type_str, rate_per_night, stay_total, 
                        deposit, balance, payment_status_trans, special_requests, 
                        conf_deposit_policy, can_policy_default, comb_inclusions, 
                        comb_services, lang_code, curr_code
                    )
                }

                st.session_state.pending_action = action
                
            with col_act1:

                if st.button("💾 Generate & Save Draft", use_container_width=True):

                    store_pending_confirmation_ui("draft")

                    if get_gmail_service():

                        execute_pending_confirmation()
                        st.rerun()

                    else:

                        st.warning("Connect Gmail to generate confirmation.")

                        st.markdown(
                            f"""
                            <a href="{get_google_login_url()}" 
                               style="display:inline-block; background:#2563eb; color:#ffffff; padding:13px 22px; border-radius:9px; text-decoration:none;">
                               Connect Google
                            </a>
                            """, 
                            unsafe_allow_html=True
                        )

                if st.session_state.get("conf_auto_draft_success"):

                    result = st.session_state.conf_auto_draft_success

                    if isinstance(result, str) and "failed" in result:

                        st.warning(result)

                    else:

                        st.success(f"✅ Reservation Confirmed! Draft saved successfully. Confirmation #{result}")
                        st.balloons()

                    st.session_state.conf_auto_draft_success = False

            with col_act2:

                if st.button("📤 Generate & Send Email", use_container_width=True):

                    store_pending_confirmation_ui("send")

                    if get_gmail_service():

                        execute_pending_confirmation()
                        st.rerun()

                    else:

                        st.warning("Connect Gmail to generate confirmation.")

                        st.markdown(
                            f"""
                            <a href="{get_google_login_url()}" 
                               style="display:inline-block; background:#2563eb; color:#ffffff; padding:13px 22px; border-radius:9px; text-decoration:none;">
                               Connect Google
                            </a>
                            """, 
                            unsafe_allow_html=True
                        )

                if st.session_state.get("conf_auto_send_success"):

                    result = st.session_state.conf_auto_send_success

                    if isinstance(result, str) and "failed" in result:

                        st.warning(result)

                    else:

                        st.success(f"✅ Reservation Confirmed! Email sent successfully. Confirmation #{result}")
                        st.balloons()

                    st.session_state.conf_auto_send_success = False


# ============================================================
# WORKFLOW: MANUAL CONFIRMATION
# ============================================================

elif app_mode == "Manual Confirmation":

    st.title(
        "Manual Confirmation"
    )

    st.caption(
        "Create a reservation confirmation directly "
        "without a previous quotation."
    )
    
    st.markdown(
        "## Guest & Stay Information"
    )
    
    mc_col1, mc_col2 = st.columns(2)

    with mc_col1:

        m_guest_name = st.text_input("Guest name", placeholder="John Smith", key="m_gname")

    with mc_col2:

        m_guest_email = st.text_input("Guest email", placeholder="guest@email.com", key="m_gemail")

    mc_col3, mc_col4 = st.columns(2)

    with mc_col3:

        m_arrival = st.date_input("Arrival", value=date.today(), key="m_arr")

    with mc_col4:

        m_departure = st.date_input("Departure", value=date.today(), key="m_dep")

    mc_col5, mc_col6, mc_col7 = st.columns(3)

    m_calculated_nights = max(1, (m_departure - m_arrival).days)

    with mc_col5:

        m_adults = st.number_input("Adults", min_value=1, max_value=20, value=2, step=1, key="m_adults")

    with mc_col6:

        m_children = st.number_input("Children", min_value=0, max_value=20, value=0, step=1, key="m_child")

    with mc_col7:

        m_nights = st.number_input("Nights", min_value=1, max_value=365, value=m_calculated_nights, step=1, key="m_nights")
        
    st.divider()

    st.markdown(
        "## Reservation Information"
    )
    
    r_col1, r_col2 = st.columns(2)

    with r_col1:

        m_room_type = st.selectbox("Room type", list(ROOM_TYPES.keys()), key="m_rtype")

    with r_col2:

        m_stay_total = st.number_input(f"Stay Total Taxes Included ({curr_code})", min_value=0.00, value=0.00, step=100.00, format="%.2f", key="m_stotal")
        
    m_calc = calculate_rate_values(m_stay_total, m_nights)
    m_nightly_rate = m_calc["nightly_with_tax"]
    
    m_payment_status = st.radio("Payment Status", ["First Night Deposit", "Fully Paid"], key="m_pstat")
    
    if m_payment_status == "Fully Paid":

        m_deposit = float(m_stay_total)
        m_balance = 0.00
        payment_status_trans = TRANSLATIONS[lang_code]["fully_paid"]

    else:

        m_deposit = float(m_nightly_rate)
        m_balance = float(m_stay_total) - m_deposit
        payment_status_trans = TRANSLATIONS[lang_code]["first_night_deposit"]
        
    p_col1, p_col2, p_col3 = st.columns(3)

    p_col1.metric("Total Amount", money(m_stay_total, curr_code))
    p_col2.metric("Deposit", money(m_deposit, curr_code))
    p_col3.metric("Balance Due", money(m_balance, curr_code))

    st.markdown(
        "### Included Benefits"
    )

    m_defaults = list(
        ROOM_TYPES[m_room_type]["default_inclusions"]
    )

    m_inc_signature = (
        m_room_type 
        + "|" 
        + "|".join(AVAILABLE_INCLUSIONS)
    )

    m_sig_key = "m_inclusion_signature"

    if st.session_state.get(m_sig_key) != m_inc_signature:

        for index, inclusion in enumerate(AVAILABLE_INCLUSIONS):

            st.session_state[f"m_inc_{index}"] = (inclusion in m_defaults)

        st.session_state[m_sig_key] = m_inc_signature

    m_inc_cols = st.columns(2)
    m_selected_inclusions = []

    for index, inclusion in enumerate(AVAILABLE_INCLUSIONS):

        with m_inc_cols[index % 2]:

            if st.checkbox(inclusion, key=f"m_inc_{index}"):

                m_selected_inclusions.append(inclusion)

    st.markdown(
        "### Additional Services"
    )

    m_srv_cols = st.columns(2)
    m_selected_services = []

    for index, (service, price) in enumerate(ADDITIONAL_SERVICES.items()):

        with m_srv_cols[index % 2]:

            if st.checkbox(f"{service} — {money(price, curr_code)}", key=f"m_srv_{index}"):

                m_selected_services.append(service)
    
    m_comments = st.text_area("Comments (Internal Notes)", key="m_comm")
    m_special = st.text_area("Special Requests (Guest Needs)", key="m_spec")
    
    st.markdown(
        "### Policies"
    )

    po_col1, po_col2 = st.columns(2)

    with po_col1:

        t_ui = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])

        if m_payment_status == "Fully Paid":
            dynamic_m_dep = t_ui.get("fully_paid_policy", "Reservation is fully paid." if lang_code == "en" else "La reservación está totalmente pagada.")
        else:
            dynamic_m_dep = f"{t_ui.get('first_night_policy', 'Reservation is guaranteed with the first night deposit, balance to pay due check in: ')}{money(m_balance, curr_code)}"
            
        m_dep_pol = st.text_area(
            "Deposit Policy", 
            value=dynamic_m_dep, 
            key=f"m_dpol_{m_payment_status}", 
            height=68
        )

    with po_col2:

        m_can_pol = st.selectbox(
            "Cancellation Policy", 
            CANCELLATION_POLICIES, 
            key="m_cpol"
        )
        
    st.markdown(
        "### Confirmation Details"
    )

    m_hotel_conf_number = st.text_input(
        "Hotel Confirmation Number", 
        placeholder="Leave blank to auto-generate (CN...)", 
        key="m_hconf"
    )

    st.markdown(
        "### Actions"
    )

    m_act1, m_act2 = st.columns(2)
    
    def store_manual_pending_ui(action):

        conf_number = m_hotel_conf_number.strip() if m_hotel_conf_number.strip() else generate_confirmation_number()

        st.session_state.pending_confirmation = {

            "confirmation_number": 
                conf_number,

            "quotation_number": 
                None,

            "guest_name": 
                m_guest_name,

            "guest_email": 
                m_guest_email,

            "arrival": 
                m_arrival,

            "departure": 
                m_departure,

            "nights": 
                m_nights,

            "adults": 
                m_adults,

            "children": 
                m_children,

            "room_type": 
                m_room_type,

            "rate_per_night": 
                m_nightly_rate,

            "stay_total": 
                m_stay_total,

            "first_night_amount": 
                m_deposit,

            "balance_due": 
                m_balance,

            "payment_status": 
                payment_status_trans,

            "comments": 
                m_comments,

            "special_requests": 
                m_special,

            "additional_services": 
                {"source": "manual"},

            "subject": 
                f"Booking Confirmation #{conf_number} | Casa Dorada Los Cabos",

            "email_html": build_confirmation_email_html(
                conf_number, m_guest_name, m_arrival, m_departure, m_adults, m_children, m_nights,
                m_room_type, m_nightly_rate, m_stay_total, m_deposit, m_balance, payment_status_trans,
                m_special, m_dep_pol, m_can_pol, m_selected_inclusions, m_selected_services, lang_code, curr_code
            ),

            "plain_text_email": build_confirmation_plain_text(
                conf_number, m_guest_name, m_arrival, m_departure, m_adults, m_children, m_nights,
                m_room_type, m_nightly_rate, m_stay_total, m_deposit, m_balance, payment_status_trans,
                m_special, m_dep_pol, m_can_pol, m_selected_inclusions, m_selected_services, lang_code, curr_code
            )

        }

        st.session_state.pending_action = action

    with m_act1:

        if st.button("💾 Generate Manual Draft", use_container_width=True):

            if not m_guest_name or not m_guest_email:

                st.error("Guest name and email are required.")

            else:

                store_manual_pending_ui("draft")

                if get_gmail_service():

                    execute_pending_confirmation()
                    st.rerun()

                else:

                    st.warning("Connect Gmail to generate confirmation.")

                    st.markdown(
                        f"""
                        <a href="{get_google_login_url()}" 
                           style="display:inline-block; background:#2563eb; color:#ffffff; padding:13px 22px; border-radius:9px; text-decoration:none;">
                           Connect Google
                        </a>
                        """, 
                        unsafe_allow_html=True
                    )

        if st.session_state.get("conf_auto_draft_success"):

            result = st.session_state.conf_auto_draft_success

            if isinstance(result, str) and "failed" in result:

                st.warning(result)

            else:

                st.success(f"✅ Reservation Confirmed! Draft saved successfully. Confirmation #{result}")
                st.balloons()

            st.session_state.conf_auto_draft_success = False

    with m_act2:

        if st.button("📤 Generate & Send Email", use_container_width=True):

            if not m_guest_name or not m_guest_email:

                st.error("Guest name and email are required.")

            else:

                store_manual_pending_ui("send")

                if get_gmail_service():

                    execute_pending_confirmation()
                    st.rerun()

                else:

                    st.warning("Connect Gmail to generate confirmation.")

                    st.markdown(
                        f"""
                        <a href="{get_google_login_url()}" 
                           style="display:inline-block; background:#2563eb; color:#ffffff; padding:13px 22px; border-radius:9px; text-decoration:none;">
                           Connect Google
                        </a>
                        """, 
                        unsafe_allow_html=True
                    )

        if st.session_state.get("conf_auto_send_success"):

            result = st.session_state.conf_auto_send_success

            if isinstance(result, str) and "failed" in result:

                st.warning(result)

            else:

                st.success(f"✅ Reservation Confirmed! Email sent successfully. Confirmation #{result}")
                st.balloons()

            st.session_state.conf_auto_send_success = False

import streamlit as st
import base64
import hashlib
import hmac
import json
import secrets
import requests
import math
import pandas as pd
from zoneinfo import ZoneInfo

from datetime import date, datetime, timezone, timedelta
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

    "20% discount on food and beverages "
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

    "Minibar includes" " (8 soft drinks, 4 bottles of water, 6 domestic beers and 2 daily coffee kits)" ,

    "Minibar 12 drinks included per day "
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
# TIPO DE CAMBIO Y CALCULADORA DE SERVICIOS
# ============================================================
EXCHANGE_RATE = 17.00  # Puedes cambiar este número o enlazarlo a la interfaz después

def get_service_price(service, currency):
    """Obtiene el precio del servicio y lo convierte a MXN si es necesario."""
    base_price_usd = ADDITIONAL_SERVICES.get(service, 0.0)
    
    if currency == "MXN":
        return base_price_usd * EXCHANGE_RATE
    else:
        return base_price_usd

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
        "dear": "Hola",
        "quote_intro": "Thank you for considering Casa Dorada Los Cabos Resort & Spa for your upcoming stay. Please find below your personalized quotation and available options.",
        "conf_intro": "Thank you for choosing Casa Dorada Los Cabos Resort & Spa, please find below the details of your reservation.",
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
        "Complete_Payment": "Complete Payment",
        "fully_paid": "Fully Paid",
        "first_night_deposit": "First Night Deposit",
        "fully_paid_policy": "Reservation is fully paid.",
        "first_night_policy": "Reservation is guaranteed with the first night deposit, balance to pay due check in: ",
        "cancel_map": {
            "Non-refundable, no modifications are allowed. In case of early departure or no show, no reimbursement will apply.": "Non-refundable, no modifications are allowed. In case of early departure or no show, no reimbursement will apply.",
            "Reservations can be canceled 4 days before arrival free of charge. 1 night stay (tax included) penalty charge if canceled less than 4 days before arrival.": "Reservations can be canceled 4 days before arrival free of charge. 1 night stay (tax included) penalty charge if canceled less than 4 days before arrival.",
            "Reservations can be canceled 14 days before arrival free of charge. 1 night stay (tax included) penalty charge if canceled less than 14 days before arrival.": "Reservations can be canceled 14 days before arrival free of charge. 1 night stay (tax included) penalty charge if canceled less than 14 days before arrival.",
            "Reservations can be cancelled 45 days prior to arrival without charge. Full stay (tax included) charges penalty if cancelled less than 45 days prior to arrival. Time is based on the property's local time.": "Reservations can be cancelled 45 days prior to arrival without charge. Full stay (tax included) charges penalty if cancelled less than 45 days prior to arrival. Time is based on the property's local time."
        },
        "inclusions_map": {
            "Free Wi-Fi": "Free Wi-Fi",
            "Free Valet Parking": "Free Valet Parking",
            "Free Breakfast Buffet at Maydan Restaurant": "Free Breakfast Buffet at Maydan Restaurant",
            "30% discount on food and beverages (does not apply to room service, minibar, or other promotions)": "30% discount on food and beverages (does not apply to room service, minibar, or other promotions)",
            "25% discount on food and beverages (does not apply to room service, minibar, or other promotions)": "25% discount on food and beverages (does not apply to room service, minibar, or other promotions)",
            "25% discount at Saltwater Spa (50 and 80 minute massages)": "25% discount at Saltwater Spa (50 and 80 minute massages)",
            "30% discount at Saltwater Spa (50 and 80 minute massages)": "30% discount at Saltwater Spa (50 and 80 minute massages)",
            "All Inclusive Package": "All Inclusive Package",
            "30% Discount for Room Service": "30% Discount for Room Service",
            "Free Spa Access (Wet Areas)": "Free Spa Access (Wet Areas)",
            "20% discount at Saltwater Spa (No Salon Services)": "20% discount at Saltwater Spa (No Salon Services)",
            "Buy one Full Body Massage 80 minutes at Saltwater Spa and the second is free": "Buy one Full Body Massage 80 minutes at Saltwater Spa and the second is free",
            "USD $100.00 Food and Beverage Credit (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)": "USD $100.00 Food and Beverage Credit (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)",
            "USD $100.00 Dining Credit (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)": "USD $100.00 Dining Credit (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)",
            "$100.00 USD Dinner Credit at 12 Tribes (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)": "$100.00 USD Dinner Credit at 12 Tribes (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)",
            "Round Trip Transportation": "Round Trip Transportation",
            "One Way Transportation": "One Way Transportation",
            "Romantic Three-Course Dinner on the Beach": "Romantic Three-Course Dinner on the Beach",
            "1 Seasonal Fruit Amenity per Stay": "1 Seasonal Fruit Amenity per Stay",
            "12 drinks included per day (4 beers, 4 soft drinks and 4 bottles of water)": "12 drinks included per day (4 beers, 4 soft drinks and 4 bottles of water)",
            "1 bottle of house wine upon arrival per stay (bottle available in stock)": "1 bottle of house wine upon arrival per stay (bottle available in stock)"
        },
        "services_map": {
            "Round Trip Transportation": "Round Trip Transportation",
            "One Way Transportation": "One Way Transportation",
            "Early Check In": "Early Check In",
            "Late Check Out": "Late Check Out"
        }
    },
    "es": {
        "custom_quotation": "Su Cotización Personalizada",
        "reservation_confirmation": "Confirmación de Reservación",
        "dear": "Hola",
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
        "Complete_Payment": "Completar Pago de Su Reserva",
        "fully_paid": "Pagado en su totalidad",
        "first_night_deposit": "Depósito de la primera noche",
        "fully_paid_policy": "La reservación está totalmente pagada.",
        "first_night_policy": "La reservación está garantizada con el depósito de la primera noche, saldo a pagar al check in: ",
        "cancel_map": {
            "Non-refundable, no modifications are allowed. In case of early departure or no show, no reimbursement will apply.": "No reembolsable, no se permiten modificaciones. En caso de salida anticipada o no presentarse (no show), no aplicará ningún reembolso.",
            "Reservations can be canceled 4 days before arrival free of charge. 1 night stay (tax included) penalty charge if canceled less than 4 days before arrival.": "Puede cancelar sin cargo hasta 4 días antes de su llegada. Si cancela con menos de 4 días de anticipación, aplicará una penalidad de 1 noche de estancia (impuestos incluidos).",
            "Reservations can be canceled 14 days before arrival free of charge. 1 night stay (tax included) penalty charge if canceled less than 14 days before arrival.": "Puede cancelar sin cargo hasta 14 días antes de su llegada. Si cancela con menos de 14 días de anticipación, aplicará una penalidad de 1 noche de estancia (impuestos incluidos).",
            "Reservations can be cancelled 45 days prior to arrival without charge. Full stay (tax included) charges penalty if cancelled less than 45 days prior to arrival. Time is based on the property's local time.": "Puede cancelar sin cargo hasta 45 días antes de su llegada. Si cancela con menos de 45 días de anticipación, aplicará una penalidad por el total de la estancia (impuestos incluidos). El horario se basa en la hora local del hotel."
        },
        "inclusions_map": {
            "Free Wi-Fi": "Wi-Fi gratis",
            "Free Valet Parking": "Valet Parking gratis",
            "Free Breakfast Buffet at Maydan Restaurant": "Desayuno Buffet gratis en el Restaurante Maydan",
            "30% discount on food and beverages (does not apply to room service, minibar, or other promotions)": "30% de descuento en alimentos y bebidas (no aplica en room service, minibar ni otras promociones)",
            "25% discount on food and beverages (does not apply to room service, minibar, or other promotions)": "25% de descuento en alimentos y bebidas (no aplica en room service, minibar ni otras promociones)",
            "25% discount at Saltwater Spa (50 and 80 minute massages)": "25% de descuento en Saltwater Spa (masajes de 50 y 80 minutos)",
            "30% discount at Saltwater Spa (50 and 80 minute massages)": "30% de descuento en Saltwater Spa (masajes de 50 y 80 minutos)",
            "All Inclusive Package": "Paquete Todo Incluido",
            "30% Discount for Room Service": "30% de descuento en Room Service",
            "Free Spa Access (Wet Areas)": "Acceso gratis al Spa (Áreas húmedas)",
            "20% discount at Saltwater Spa (No Salon Services)": "20% de descuento en Saltwater Spa (No aplica en servicios de salón)",
            "Buy one Full Body Massage 80 minutes at Saltwater Spa and the second is free": "Compre un Masaje de Cuerpo Completo de 80 min en Saltwater Spa y el segundo es gratis",
            "USD $100.00 Food and Beverage Credit (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)": "$100.00 USD de Crédito en Alimentos y Bebidas (Intransferible, no canjeable por efectivo, no acumulable)",
            "USD $100.00 Dining Credit (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)": "$100.00 USD de Crédito para Cenas (Intransferible, no canjeable por efectivo, no acumulable)",
            "$100.00 USD Dinner Credit at 12 Tribes (This credit is non-transferable and non-redeemable for cash, credits are non-cumulative, per reservation)": "$100.00 USD de Crédito para Cena en 12 Tribes (Intransferible, no canjeable por efectivo, no acumulable)",
            "Round Trip Transportation": "Transportación Redonda",
            "One Way Transportation": "Transportación Sencilla",
            "Romantic Three-Course Dinner on the Beach": "Cena Romántica de Tres Tiempos en la Playa",
            "1 Seasonal Fruit Amenity per Stay": "1 Amenidad de Fruta de Temporada por Estancia",
            "12 drinks included per day (4 beers, 4 soft drinks and 4 bottles of water)": "12 bebidas incluidas por día (4 cervezas, 4 refrescos y 4 botellas de agua)",
            "1 bottle of house wine upon arrival per stay (bottle available in stock)": "1 botella de vino de la casa a la llegada por estancia"
        },
        "services_map": {
            "Round Trip Transportation": "Transportación Redonda",
            "One Way Transportation": "Transportación Sencilla",
            "Early Check In": "Check In Anticipado",
            "Late Check Out": "Check Out Tardío"
        }
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

            # Campo nuevo dentro del JSON options; no requiere cambio SQL.
            "currency": option.get("currency"),

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


# ============================================================
# UPDATE EXISTING QUOTATION
# ============================================================

def update_quotation_in_supabase(
    quotation_number,
    guest_name,
    guest_email,
    arrival,
    departure,
    nights,
    options,
    status,
):

    config = get_supabase_config()

    if not config:
        return None

    endpoint = f"{config['url']}/rest/v1/quotations"

    headers = get_supabase_headers(
        "return=representation"
    )

    database_options = prepare_options_for_database(
        options,
        nights,
    )

    first_option = options[0] if options else {}

    payload = {
        "guest_name": guest_name,
        "guest_email": guest_email,
        "arrival": str(arrival),
        "departure": str(departure),
        "nights": int(nights),
        "adults": int(first_option.get("adults", 2)),
        "children": int(first_option.get("children", 0)),
        "options": database_options,
        "status": status,
    }

    params = {
        "quotation_number": f"eq.{quotation_number}"
    }

    try:

        response = requests.patch(
            endpoint,
            headers=headers,
            params=params,
            json=payload,
            timeout=20,
        )

        if response.status_code not in [200, 204]:

            st.session_state[
                "quotation_database_error"
            ] = (
                f"HTTP {response.status_code}: "
                f"{response.text}"
            )

            return None

        if response.status_code == 204:
            return {
                "quotation_number": quotation_number
            }

        data = response.json()

        if not data:
            return {
                "quotation_number": quotation_number
            }

        return data[0]

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
    rooms=None,
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
        "rooms": rooms,
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


# ============================================================
# EXECUTE PENDING MODIFIED QUOTATION
# ============================================================

def execute_pending_modified_quote():

    pending_quote = st.session_state.get(
        "pending_modified_quote"
    )
    pending_action = st.session_state.get(
        "pending_action"
    )

    if not pending_quote or pending_action != "modify_draft":
        return False

    try:

        save_gmail_draft(
            to_email=pending_quote["guest_email"],
            subject=pending_quote["subject"],
            html_body=pending_quote["email_html"],
            plain_text_body=pending_quote["plain_text_email"],
        )

        quotation = update_quotation_in_supabase(
            quotation_number=pending_quote["quotation_number"],
            guest_name=pending_quote["guest_name"],
            guest_email=pending_quote["guest_email"],
            arrival=pending_quote["arrival"],
            departure=pending_quote["departure"],
            nights=pending_quote["nights"],
            options=pending_quote["options"],
            status=pending_quote["status"],
        )

        if not quotation:
            raise Exception(
                "The Gmail draft was created, but the quotation "
                "could not be updated in Supabase."
            )

        quotation_number = pending_quote[
            "quotation_number"
        ]

        st.session_state.pending_modified_quote = None
        st.session_state.pending_action = None
        st.session_state.modify_selected_quote = None
        st.session_state.modify_search_results = []
        st.session_state.modify_success = (
            f"Quotation #{quotation_number} was updated and "
            "saved as a new Gmail draft."
        )

        return True

    except Exception as e:

        st.session_state.pending_action_error = str(e)
        st.session_state.pending_modified_quote = None
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
            rooms=pending_confirmation.get("rooms"),
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

        elif st.session_state.get("pending_modified_quote"):

            execute_pending_modified_quote()

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

    calculations = calculate_rate_values(stay_total_tax_included, nights)
    total_with_tax = calculations["total_with_tax"]
    nightly_with_tax = calculations["nightly_with_tax"]
    nightly_before_tax = calculations["nightly_before_tax"]

    guest_summary = f"{adults} {t['adults']}"
    if children > 0:
        guest_summary += f" + {children} {t['children']}"

    # --- TRADUCCIÓN DE INCLUSIONES ---
    inclusions_html = ""
    for inclusion in selected_inclusions:
        translated_inc = t.get('inclusions_map', {}).get(inclusion, inclusion)
        inclusions_html += f"""
        <li style="margin-bottom:7px; color:#444444; font-size:14px; line-height:1.4;">
            {html_escape(translated_inc)}
        </li>
        """

    if not inclusions_html:
        inclusions_html = f"""
        <li style="color:#777777; font-size:14px;">
            {t["no_inclusions"]}
        </li>
        """

    # --- TRADUCCIÓN DE SERVICIOS ADICIONALES Y CALCULADORA ---
    services_html = ""
    additional_services_total = 0.0

    for service in selected_services:
        # AQUÍ USAMOS LA CALCULADORA NUEVA
        price = get_service_price(service, currency)
        
        additional_services_total += price
        translated_srv = t.get('services_map', {}).get(service, service)
        
        services_html += f"""
        <tr>
            <td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">
                {html_escape(translated_srv)}
            </td>
            <td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">
                {money(price, currency)}
            </td>
        </tr>
        """

    if not services_html:
        services_html = f"""
        <tr>
            <td colspan="2" style="padding:6px 0; color:#777777; font-size:14px; text-align:left;">
                {t["no_services"]}
            </td>
        </tr>
        """

    # --- TRADUCCIÓN DE CANCELACIÓN ---
    translated_cancel = t.get('cancel_map', {}).get(cancellation_policy, cancellation_policy)

    final_total = total_with_tax + additional_services_total

    buttons_html = ""
    if room_360_url:
        buttons_html += f"""
        <a href="{html_escape(room_360_url)}" target="_blank"
           style="display:inline-block; background:#ffffff; color:#1f4f78; border:1px solid #1f4f78; text-decoration:none; padding:11px 18px; border-radius:5px; font-size:13px; font-weight:bold; margin-right:7px;">
           {t["view_room"]}
        </a>
        """

    if payment_url:
        buttons_html += f"""
        <a href="{html_escape(payment_url)}" target="_blank"
           style="display:inline-block; background:#c9a227; color:#ffffff; text-decoration:none; padding:12px 18px; border-radius:5px; font-size:13px; font-weight:bold;">
           {t["Complete_Payment"]}
        </a>
        """

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #dddddd; background:#ffffff; margin-bottom:22px;">
        <tr>
            <td style="padding:20px; text-align:left;">
                <div style="color:#1f4f78; font-size:18px; font-weight:bold; margin-bottom:5px; text-align:left;">
                    {t["option"]} {option_number}
                </div>
                <div style="color:#333333; font-size:20px; font-weight:bold; margin-bottom:18px; text-align:left;">
                    {html_escape(room_type)}
                </div>
                <div style="color:#1f4f78; font-size:15px; font-weight:bold; margin-bottom:8px; text-align:left;">
                    {t["rate_details"]}
                </div>
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                        <td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t["rate_before_taxes"]}</td>
                        <td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{money(nightly_before_tax, currency)}</td>
                    </tr>
                    <tr>
                        <td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t["rate_with_taxes"]}</td>
                        <td style="padding:6px 0; color:#222222; font-size:14px; text-align:right; font-weight:bold;">{money(nightly_with_tax, currency)}</td>
                    </tr>
                    <tr>
                        <td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t["number_nights"]}</td>
                        <td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{html_escape(nights)}</td>
                    </tr>
                    <tr>
                        <td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">{t["guests"]}</td>
                        <td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">{html_escape(guest_summary)}</td>
                    </tr>
                    <tr>
                        <td style="border-top:1px solid #eeeeee; padding:10px 0 6px 0; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">{t["stay_total"]}</td>
                        <td style="border-top:1px solid #eeeeee; padding:10px 0 6px 0; color:#1f4f78; font-size:16px; text-align:right; font-weight:bold;">{money(total_with_tax, currency)}</td>
                    </tr>
                </table>

                <div style="margin-top:20px; margin-bottom:8px; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">
                    {t["included"]}
                </div>
                <ul style="padding-left:22px; margin-top:8px; margin-bottom:20px; text-align:left;">
                    {inclusions_html}
                </ul>

                <div style="margin-top:20px; margin-bottom:8px; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">
                    {t["additional_services"]}
                </div>
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                    {services_html}
                    <tr>
                        <td style="border-top:1px solid #eeeeee; padding-top:10px; color:#555555; font-size:14px; font-weight:bold; text-align:left;">{t["additional_total"]}</td>
                        <td style="border-top:1px solid #eeeeee; padding-top:10px; color:#222222; font-size:14px; text-align:right; font-weight:bold;">{money(additional_services_total, currency)}</td>
                    </tr>
                </table>

                <div style="margin-top:18px; padding:15px; background:#f5f7fa;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td style="color:#1f4f78; font-size:17px; font-weight:bold; text-align:left;">{t["total_amount"]}</td>
                            <td style="color:#1f4f78; font-size:20px; font-weight:bold; text-align:right;">{money(final_total, currency)}</td>
                        </tr>
                    </table>
                </div>

                <div style="margin-top:20px; padding-top:15px; border-top:1px solid #eeeeee; text-align:left;">
                    <div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-bottom:6px; text-align:left;">{t["deposit_policy"]}</div>
                    <div style="color:#555555; font-size:13px; line-height:1.5; text-align:left;">{html_escape(deposit_policy)}</div>
                    
                    <div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-top:15px; margin-bottom:6px; text-align:left;">{t["cancellation_policy"]}</div>
                    <div style="color:#555555; font-size:13px; line-height:1.5; text-align:left;">{html_escape(translated_cancel)}</div>
                </div>

                <div style="margin-top:20px; text-align:left;">
                    {buttons_html}
                </div>

                <div style="margin-top:16px; color:#777777; font-size:12px; text-align:left;">
                    {t["quote_valid"]}: <strong>{html_escape(format_date_email(valid_until, lang))}</strong>
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

    lines.append(t["custom_quotation"].upper())
    lines.append("")
    lines.append(f"{t['dear']} {guest_name},")
    lines.append("")
    lines.append(t["quote_intro"])
    lines.append("")
    lines.append(t["your_stay"].upper())
    lines.append(f"{t['nights']}: {nights}")
    lines.append(f"{t['arrival']}: {format_date_email(arrival, lang)}")
    lines.append(f"{t['departure']}: {format_date_email(departure, lang)}")
    lines.append("")
    lines.append(t["available_options"].upper())
    lines.append("")

    for index, option in enumerate(options, start=1):
        calculations = calculate_rate_values(option["stay_total_tax_included"], nights)
        
        # AQUÍ USAMOS LA CALCULADORA NUEVA PARA SUMAR LOS TOTALES
        services_total = sum(get_service_price(service, currency) for service in option["selected_services"])
        final_total = calculations["total_with_tax"] + services_total

        opt_adults = option.get("adults", 2)
        opt_children = option.get("children", 0)

        guest_summary = f"{opt_adults} {t['adults']}"
        if opt_children > 0:
            guest_summary += f", {opt_children} {t['children']}"

        lines.append(f"{t['option'].upper()} {index}")
        lines.append(f"{t['room_type']}: {option['room_type']}")
        lines.append(f"{t['guests']}: {guest_summary}")
        lines.append(f"{t['rate_before_taxes']}: {money(calculations['nightly_before_tax'], currency)}")
        lines.append(f"{t['rate_with_taxes']}: {money(calculations['nightly_with_tax'], currency)}")
        lines.append(f"{t['number_nights']}: {nights}")
        lines.append(f"{t['stay_total']}: {money(calculations['total_with_tax'], currency)}")
        lines.append("")
        lines.append(f"{t['included']}:")

        if option["selected_inclusions"]:
            for inclusion in option["selected_inclusions"]:
                translated_inc = t.get('inclusions_map', {}).get(inclusion, inclusion)
                lines.append(f"• {translated_inc}")
        else:
            lines.append(t["no_inclusions"])

        lines.append("")
        lines.append(f"{t['additional_services']}:")

        if option["selected_services"]:
            for service in option["selected_services"]:
                translated_srv = t.get('services_map', {}).get(service, service)
                
                # AQUÍ USAMOS LA CALCULADORA NUEVA PARA IMPRIMIR EL PRECIO
                lines.append(f"• {translated_srv}: {money(get_service_price(service, currency), currency)}")
        else:
            lines.append(t["no_services"])

        lines.append("")
        lines.append(f"{t['total_amount']}: {money(final_total, currency)}")
        lines.append("")
        
        lines.append(f"{t['deposit_policy']}:")
        lines.append(option["deposit_policy"])
        lines.append("")
        
        translated_cancel = t.get('cancel_map', {}).get(option["cancellation_policy"], option["cancellation_policy"])
        lines.append(f"{t['cancellation_policy']}:")
        lines.append(translated_cancel)
        
        lines.append("")
        lines.append(f"{t['quote_valid']}: {format_date_email(option['valid_until'], lang)}")
        lines.append("")
        lines.append("----------------------------------------")
        lines.append("")

    lines.append("Casa Dorada Los Cabos Resort & Spa")
    lines.append("Av. del Pescador s/n, Cabo San Lucas, B.C.S.")
    lines.append("US: 1-866-448-0151")

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
            room_type=option["room_type"],
            valid_until=option["valid_until"],
            nights=nights,
            stay_total_tax_included=option["stay_total_tax_included"],
            selected_inclusions=option["selected_inclusions"],
            selected_services=option["selected_services"],
            deposit_policy=option["deposit_policy"],
            cancellation_policy=option["cancellation_policy"],
            payment_url=option["payment_url"],
            room_360_url=option["room_360_url"],
            lang=lang,
            currency=currency,
            adults=option.get("adults", 2),
            children=option.get("children", 0)
        )

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t["custom_quotation"]}</title>
</head>
<body style="margin:0; padding:0; background:#f3f4f6; font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="left" style="padding:30px 10px;">
<table width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px; max-width:100%; background:#ffffff; border:1px solid #dddddd;">
<tr>
<td align="left" style="background:#ffffff; padding:25px 35px 15px 35px;">
<img src="{EMAIL_LOGO_URL}" alt="Casa Dorada" style="max-width:220px; width:100%; height:auto; display:block;">
</td>
</tr>
<tr>
<td style="padding:15px 35px 5px 35px; text-align:left;">
<div style="color:#1f4f78; font-size:25px; font-weight:bold; text-align:left;">
{t["custom_quotation"]}
</div>
</td>
</tr>
<tr>
<td style="padding:15px 35px 10px 35px; text-align:left;">
<p style="color:#333333; font-size:15px; line-height:1.6; margin:0 0 12px 0; text-align:left;">
{t["dear"]} {html_escape(guest_name)},
</p>
<p style="color:#555555; font-size:14px; line-height:1.6; margin:0; text-align:left;">
{t["quote_intro"]}
</p>
</td>
</tr>
<tr>
<td style="padding:20px 35px 15px 35px; text-align:left;">
<div style="color:#1f4f78; font-size:19px; font-weight:bold; margin-bottom:12px; text-align:left;">
{t["your_stay"]}
</div>
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f7f8fa; border:1px solid #e5e7eb;">
<tr>
<td style="padding:10px 14px; width:45%; color:#777777; font-size:13px; font-weight:bold; text-align:left; border-bottom:1px solid #e5e7eb;">
{t["nights"]}
</td>
<td style="padding:10px 14px; color:#1f2937; font-size:13px; font-weight:bold; text-align:right; border-bottom:1px solid #e5e7eb;">
{html_escape(nights)}{(" " + t["night"]) if nights == 1 else (" " + t["nights"])}
</td>
</tr>
<tr>
<td style="padding:10px 14px; width:45%; color:#777777; font-size:13px; font-weight:bold; text-align:left; border-bottom:1px solid #e5e7eb;">
{t["arrival"]}
</td>
<td style="padding:10px 14px; color:#1f2937; font-size:13px; font-weight:bold; text-align:right; border-bottom:1px solid #e5e7eb;">
{html_escape(format_date_email(arrival, lang))}
</td>
</tr>
<tr>
<td style="padding:10px 14px; width:45%; color:#777777; font-size:13px; font-weight:bold; text-align:left;">
{t["departure"]}
</td>
<td style="padding:10px 14px; color:#1f2937; font-size:13px; font-weight:bold; text-align:right;">
{html_escape(format_date_email(departure, lang))}
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:15px 35px 5px 35px; text-align:left;">
<div style="color:#1f4f78; font-size:19px; font-weight:bold; margin-bottom:15px; text-align:left;">
{t["available_options"]}
</div>
{options_html}
</td>
</tr>
<tr>
<td style="background:#1f4f78; padding:22px 30px; text-align:left;">
<div style="color:#ffffff; font-size:14px; font-weight:bold; margin-bottom:6px; text-align:left;">
Casa Dorada Los Cabos Resort & Spa
</div>
<div style="color:#dbeafe; font-size:12px; line-height:1.5; text-align:left;">
Av. del Pescador s/n, Cabo San Lucas, B.C.S.
</div>
<div style="color:#dbeafe; font-size:12px; line-height:1.5; text-align:left;">
US: <a href="tel:18664480151" style="color:#ffffff; text-decoration:none;">1-866-448-0151</a>
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
    currency="USD",
    rooms=None,
    total_amount=None,
):

    t = TRANSLATIONS[lang]

    # ============================================================
    # NORMALIZE ROOMS
    # ============================================================
    normalized_rooms = []

    if rooms:
        for room in rooms:
            normalized_rooms.append({
                "room_type": room.get("room_type", ""),
                "adults": int(room.get("adults", 0) or 0),
                "children": int(room.get("children", 0) or 0),
                "nights": int(room.get("nights", nights) or nights),
                "rate_per_night": float(room.get("rate_per_night", 0) or 0),
                "stay_total": float(room.get("stay_total", 0) or 0),
                "selected_inclusions": room.get("selected_inclusions", []) or [],
                "selected_services": room.get("selected_services", []) or [],
            })
    else:
        normalized_rooms = [{
            "room_type": room_type,
            "adults": int(adults or 0),
            "children": int(children or 0),
            "nights": int(nights or 1),
            "rate_per_night": float(rate_per_night or 0),
            "stay_total": float(stay_total or 0),
            "selected_inclusions": selected_inclusions or [],
            "selected_services": selected_services or [],
        }]

    accommodation_total = sum(
        room["stay_total"] for room in normalized_rooms
    )

    # ============================================================
    # ROOM CARDS - EACH ROOM IS SHOWN SEPARATELY
    # ============================================================
    room_label = "Habitación" if lang == "es" else "Room"
    room_total_label = "Total de la habitación" if lang == "es" else "Room Total"

    rooms_html = ""

    for index, room in enumerate(normalized_rooms, start=1):
        room_rate = float(room["rate_per_night"])
        room_rate_before_tax = room_rate / (1 + TAX_RATE)

        room_guest_summary = f"{room['adults']} {t['adults']}"
        if room["children"] > 0:
            room_guest_summary += f" + {room['children']} {t['children']}"

        rooms_html += f"""
        <div style="margin-top:{'0' if index == 1 else '14px'}; border:1px solid #e2e8f0; border-radius:7px; overflow:hidden;">
            <div style="background:#eef4f8; padding:11px 15px; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">
                {room_label} {index} — {html_escape(room['room_type'])}
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;">
                <tr>
                    <td style="padding:10px 15px; width:48%; color:#64748b; font-size:13px; font-weight:bold; border-bottom:1px solid #edf2f7;">{t['guests']}</td>
                    <td style="padding:10px 15px; color:#0f172a; font-size:14px; text-align:right; border-bottom:1px solid #edf2f7;">{html_escape(room_guest_summary)}</td>
                </tr>
                <tr>
                    <td style="padding:10px 15px; color:#64748b; font-size:13px; font-weight:bold; border-bottom:1px solid #edf2f7;">{t['nights']}</td>
                    <td style="padding:10px 15px; color:#0f172a; font-size:14px; text-align:right; border-bottom:1px solid #edf2f7;">{room['nights']}</td>
                </tr>
                <tr>
                    <td style="padding:10px 15px; color:#64748b; font-size:13px; font-weight:bold; border-bottom:1px solid #edf2f7;">{t['rate_before_taxes']}</td>
                    <td style="padding:10px 15px; color:#0f172a; font-size:14px; text-align:right; border-bottom:1px solid #edf2f7;">{money(room_rate_before_tax, currency)}</td>
                </tr>
                <tr>
                    <td style="padding:10px 15px; color:#64748b; font-size:13px; font-weight:bold; border-bottom:1px solid #edf2f7;">{t['rate_with_taxes']}</td>
                    <td style="padding:10px 15px; color:#0f172a; font-size:14px; text-align:right; border-bottom:1px solid #edf2f7;">{money(room_rate, currency)}</td>
                </tr>
                <tr>
                    <td style="padding:12px 15px; background:#f8fafc; color:#1f4f78; font-size:14px; font-weight:bold;">{room_total_label}</td>
                    <td style="padding:12px 15px; background:#f8fafc; color:#1f4f78; font-size:16px; font-weight:bold; text-align:right;">{money(room['stay_total'], currency)}</td>
                </tr>
            </table>
        </div>
        """

    # ============================================================
    # COMBINED INCLUSIONS
    # ============================================================
    combined_inclusions = []

    for room in normalized_rooms:
        for inclusion in room.get("selected_inclusions", []):
            if inclusion not in combined_inclusions:
                combined_inclusions.append(inclusion)

    # Fallback for legacy/manual flow.
    if not combined_inclusions:
        combined_inclusions = list(selected_inclusions or [])

    inclusions_html = ""

    if combined_inclusions:
        for inclusion in combined_inclusions:
            translated_inc = t.get("inclusions_map", {}).get(
                inclusion,
                inclusion,
            )
            inclusions_html += f"""
            <li style="margin-bottom:7px; color:#444444; font-size:14px; line-height:1.4;">
                {html_escape(translated_inc)}
            </li>
            """
    else:
        inclusions_html = f"""
        <li style="color:#777777; font-size:14px;">
            {t['no_inclusions']}
        </li>
        """

    # ============================================================
    # ADDITIONAL SERVICES
    # For multi-room confirmations, services are taken from each
    # room so repeated services are not accidentally lost.
    # ============================================================
    service_entries = []

    if rooms:
        for room_index, room in enumerate(normalized_rooms, start=1):
            for service in room.get("selected_services", []):
                service_entries.append((room_index, service))
    else:
        for service in selected_services or []:
            service_entries.append((None, service))

    services_rows = ""
    additional_services_total = 0.0

    for room_index, service in service_entries:
        price = get_service_price(service, currency)
        additional_services_total += price
        translated_srv = t.get("services_map", {}).get(service, service)

        if room_index is not None and len(normalized_rooms) > 1:
            service_name = f"{translated_srv} ({room_label} {room_index})"
        else:
            service_name = translated_srv

        services_rows += f"""
        <tr>
            <td style="padding:6px 0; color:#555555; font-size:14px; text-align:left;">
                • {html_escape(service_name)}
            </td>
            <td style="padding:6px 0; color:#222222; font-size:14px; text-align:right;">
                {money(price, currency)}
            </td>
        </tr>
        """

    if service_entries:
        services_rows += f"""
        <tr>
            <td style="border-top:1px solid #eeeeee; padding-top:10px; color:#555555; font-size:14px; font-weight:bold; text-align:left;">{t['additional_total']}</td>
            <td style="border-top:1px solid #eeeeee; padding-top:10px; color:#222222; font-size:14px; text-align:right; font-weight:bold;">{money(additional_services_total, currency)}</td>
        </tr>
        """

        services_section_html = f"""
        <div style="margin-top:15px; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">{t['additional_services']}</div>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;">{services_rows}</table>
        """
    else:
        services_section_html = ""

    if total_amount is None:
        final_total = accommodation_total + additional_services_total
    else:
        final_total = float(total_amount)

    translated_cancel = t.get("cancel_map", {}).get(
        cancellation_policy,
        cancellation_policy,
    )

    special_html = ""
    if special_requests:
        special_html = f"""
        <div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-top:15px; margin-bottom:6px; text-align:left;">
            {t['special_requests']}
        </div>
        <div style="color:#555555; font-size:13px; line-height:1.5; text-align:left;">
            {html_escape(special_requests)}
        </div>
        """

    if lang == "es":
        resort_policies_title = "Políticas del Resort"
        eco_tax = "<strong>Impuesto de Saneamiento Ambiental:</strong> El gobierno del municipio de Los Cabos implementa un impuesto de $82.12 MXN por habitación por noche (~$4.71 USD). Esta cantidad no está incluida en su tarifa prepagada, se reflejará en su cuenta final y debe pagarse al momento del check-in."
        incidental = "<strong>Depósito para Incidentales:</strong> Tenga en cuenta que se solicitará una tarjeta de crédito válida al momento del check-in para cubrir cualquier cargo incidental."
        cashless = "<strong>Política sin Efectivo (Cashless):</strong> Casa Dorada es un resort sin uso de efectivo. No se aceptan pagos en efectivo en nuestros restaurantes o bares."
        checkin_out = "<strong>Check-in:</strong> 3:00 p.m. | <strong>Check-out:</strong> 12:00 p.m. (mediodía)"
        accommodation_label = "Alojamiento"
    else:
        resort_policies_title = "Resort Policies"
        eco_tax = "<strong>Environmental Sanitation Tax:</strong> The County of Los Cabos government implements a tax of MXN $82.12 per room per night (~USD $4.71). This amount is not included in your prepaid rate, will be reflected on your final statement, and is payable at check-in."
        incidental = "<strong>Incidental Deposit:</strong> Please note that a valid credit card will be requested upon check-in to cover any incidental charges."
        cashless = "<strong>Cashless Policy:</strong> Casa Dorada is a cashless resort. Cash payments are not accepted at our restaurants or bars."
        checkin_out = "<strong>Check-in:</strong> 3:00 p.m. | <strong>Check-out:</strong> 12:00 noon"
        accommodation_label = "Accommodation"

    resort_policies_html = f"""
        <div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-top:20px; margin-bottom:6px; text-align:left;">
            {resort_policies_title}
        </div>
        <ul style="color:#555555; font-size:13px; line-height:1.5; text-align:left; padding-left:20px; margin-top:0;">
            <li style="margin-bottom:6px;">{eco_tax}</li>
            <li style="margin-bottom:6px;">{incidental}</li>
            <li style="margin-bottom:6px;">{cashless}</li>
            <li style="margin-bottom:0;">{checkin_out}</li>
        </ul>
    """

    guest_summary = f"{adults} {t['adults']}"
    if children > 0:
        guest_summary += f" + {children} {t['children']}"

    services_total_summary_row = ""
    if service_entries:
        services_total_summary_row = (
            f'<tr>'
            f'<td style="color:#555555; font-size:14px; text-align:left; padding-bottom:10px;">{t["additional_services"]}</td>'
            f'<td style="color:#222222; font-size:14px; text-align:right; padding-bottom:10px;">{money(additional_services_total, currency)}</td>'
            f'</tr>'
        )

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
<table width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px; max-width:100%; background:#ffffff; border:1px solid #dddddd;">
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

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; margin-bottom:18px;">
    <tr>
        <td style="padding:12px 15px; width:45%; color:#64748b; font-size:13px; font-weight:bold; text-align:left; border-bottom:1px solid #e2e8f0;">{t['guests']}</td>
        <td style="padding:12px 15px; color:#0f172a; font-size:14px; font-weight:bold; text-align:right; border-bottom:1px solid #e2e8f0;">{html_escape(guest_summary)}</td>
    </tr>
    <tr>
        <td style="padding:12px 15px; color:#64748b; font-size:13px; font-weight:bold; text-align:left; border-bottom:1px solid #e2e8f0;">{t['arrival']}</td>
        <td style="padding:12px 15px; color:#0f172a; font-size:14px; font-weight:bold; text-align:right; border-bottom:1px solid #e2e8f0;">{html_escape(format_date_email(arrival, lang))}</td>
    </tr>
    <tr>
        <td style="padding:12px 15px; color:#64748b; font-size:13px; font-weight:bold; text-align:left; border-bottom:1px solid #e2e8f0;">{t['departure']}</td>
        <td style="padding:12px 15px; color:#0f172a; font-size:14px; font-weight:bold; text-align:right; border-bottom:1px solid #e2e8f0;">{html_escape(format_date_email(departure, lang))}</td>
    </tr>
    <tr>
        <td style="padding:12px 15px; color:#64748b; font-size:13px; font-weight:bold; text-align:left;">{t['nights']}</td>
        <td style="padding:12px 15px; color:#0f172a; font-size:14px; font-weight:bold; text-align:right;">{html_escape(nights)}</td>
    </tr>
</table>

{rooms_html}

<div style="margin-top:20px; color:#1f4f78; font-size:15px; font-weight:bold; text-align:left;">{t['included_benefits']}</div>
<ul style="padding-left:22px; margin-top:8px; margin-bottom:15px; text-align:left;">{inclusions_html}</ul>

{services_section_html}

<div style="margin-top:18px; padding:15px; background:#f5f7fa; border-radius:6px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td style="color:#555555; font-size:14px; text-align:left; padding-bottom:7px;">{accommodation_label}</td>
            <td style="color:#222222; font-size:14px; text-align:right; padding-bottom:7px;">{money(accommodation_total, currency)}</td>
        </tr>
        {services_total_summary_row}
        <tr>
            <td style="border-top:1px solid #d8dee7; padding-top:11px; color:#1f4f78; font-size:17px; font-weight:bold; text-align:left;">{t['total_amount']}</td>
            <td style="border-top:1px solid #d8dee7; padding-top:11px; color:#1f4f78; font-size:20px; font-weight:bold; text-align:right;">{money(final_total, currency)}</td>
        </tr>
    </table>
</div>

<div style="margin-top:20px; padding-top:15px; border-top:1px solid #eeeeee;">
<div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-bottom:6px; text-align:left;">{t['deposit_policy']}</div>
<div style="color:#555555; font-size:13px; line-height:1.5; text-align:left;">{html_escape(deposit_policy)}</div>
<div style="color:#1f4f78; font-size:14px; font-weight:bold; margin-top:15px; margin-bottom:6px; text-align:left;">{t['cancellation_policy']}</div>
<div style="color:#555555; font-size:13px; line-height:1.5; text-align:left;">{html_escape(translated_cancel)}</div>
{special_html}
{resort_policies_html}
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
    currency="USD",
    rooms=None,
    total_amount=None,
):

    t = TRANSLATIONS[lang]
    translated_cancel = t.get("cancel_map", {}).get(
        cancellation_policy,
        cancellation_policy,
    )

    normalized_rooms = []

    if rooms:
        for room in rooms:
            normalized_rooms.append({
                "room_type": room.get("room_type", ""),
                "adults": int(room.get("adults", 0) or 0),
                "children": int(room.get("children", 0) or 0),
                "nights": int(room.get("nights", nights) or nights),
                "rate_per_night": float(room.get("rate_per_night", 0) or 0),
                "stay_total": float(room.get("stay_total", 0) or 0),
                "selected_inclusions": room.get("selected_inclusions", []) or [],
                "selected_services": room.get("selected_services", []) or [],
            })
    else:
        normalized_rooms = [{
            "room_type": room_type,
            "adults": int(adults or 0),
            "children": int(children or 0),
            "nights": int(nights or 1),
            "rate_per_night": float(rate_per_night or 0),
            "stay_total": float(stay_total or 0),
            "selected_inclusions": selected_inclusions or [],
            "selected_services": selected_services or [],
        }]

    accommodation_total = sum(
        room["stay_total"] for room in normalized_rooms
    )

    lines = []
    lines.append(t["reservation_confirmation"].upper())
    lines.append(f"{t['conf_number']}: {confirmation_number}")
    lines.append("")
    lines.append(f"{t['dear']} {guest_name},")
    lines.append(t["conf_intro"])
    lines.append("")
    lines.append(t["reservation_details"].upper())

    if children > 0:
        lines.append(
            f"{t['guests']}: {adults} {t['adults']}, "
            f"{children} {t['children']}"
        )
    else:
        lines.append(f"{t['guests']}: {adults} {t['adults']}")

    lines.append(f"{t['arrival']}: {format_date_email(arrival, lang)}")
    lines.append(f"{t['departure']}: {format_date_email(departure, lang)}")
    lines.append(f"{t['nights']}: {nights}")
    lines.append("")

    room_label = "HABITACIÓN" if lang == "es" else "ROOM"
    room_total_label = "Total de la habitación" if lang == "es" else "Room Total"

    for index, room in enumerate(normalized_rooms, start=1):
        room_rate_before_tax = room["rate_per_night"] / (1 + TAX_RATE)

        lines.append(f"{room_label} {index}")
        lines.append(f"{t['room_type']}: {room['room_type']}")

        room_guests = f"{room['adults']} {t['adults']}"
        if room["children"] > 0:
            room_guests += f", {room['children']} {t['children']}"

        lines.append(f"{t['guests']}: {room_guests}")
        lines.append(f"{t['nights']}: {room['nights']}")
        lines.append(
            f"{t['rate_before_taxes']}: "
            f"{money(room_rate_before_tax, currency)}"
        )
        lines.append(
            f"{t['rate_with_taxes']}: "
            f"{money(room['rate_per_night'], currency)}"
        )
        lines.append(
            f"{room_total_label}: {money(room['stay_total'], currency)}"
        )
        lines.append("")

    combined_inclusions = []
    for room in normalized_rooms:
        for inc in room.get("selected_inclusions", []):
            if inc not in combined_inclusions:
                combined_inclusions.append(inc)

    if not combined_inclusions:
        combined_inclusions = list(selected_inclusions or [])

    lines.append(f"{t['included_benefits']}:")

    if combined_inclusions:
        for inc in combined_inclusions:
            translated_inc = t.get("inclusions_map", {}).get(inc, inc)
            lines.append(f"• {translated_inc}")
    else:
        lines.append(t["no_inclusions"])

    service_entries = []

    if rooms:
        for room_index, room in enumerate(normalized_rooms, start=1):
            for srv in room.get("selected_services", []):
                service_entries.append((room_index, srv))
    else:
        for srv in selected_services or []:
            service_entries.append((None, srv))

    additional_services_total = 0.0

    if service_entries:
        lines.append("")
        lines.append(f"{t['additional_services']}:")

        for room_index, srv in service_entries:
            price = get_service_price(srv, currency)
            additional_services_total += price
            translated_srv = t.get("services_map", {}).get(srv, srv)

            if room_index is not None and len(normalized_rooms) > 1:
                suffix = (
                    f" ({'Habitación' if lang == 'es' else 'Room'} "
                    f"{room_index})"
                )
            else:
                suffix = ""

            lines.append(
                f"• {translated_srv}{suffix}: {money(price, currency)}"
            )

        lines.append(
            f"{t['additional_total']}: "
            f"{money(additional_services_total, currency)}"
        )

    if total_amount is None:
        final_total = accommodation_total + additional_services_total
    else:
        final_total = float(total_amount)

    lines.append("")
    lines.append(
        f"{'Alojamiento' if lang == 'es' else 'Accommodation'}: "
        f"{money(accommodation_total, currency)}"
    )
    lines.append(f"{t['total_amount']}: {money(final_total, currency)}")
    lines.append("")
    lines.append(f"{t['deposit_policy']}:")
    lines.append(deposit_policy)
    lines.append("")
    lines.append(f"{t['cancellation_policy']}:")
    lines.append(translated_cancel)

    if special_requests:
        lines.append("")
        lines.append(f"{t['special_requests']}:")
        lines.append(special_requests)

    if lang == "es":
        lines.append("")
        lines.append("POLÍTICAS DEL RESORT:")
        lines.append("• Impuesto de Saneamiento Ambiental: El gobierno del municipio de Los Cabos implementa un impuesto de $82.12 MXN por habitación por noche (~$4.71 USD). Esta cantidad no está incluida en su tarifa prepagada, se reflejará en su cuenta final y debe pagarse al momento del check-in.")
        lines.append("• Depósito para Incidentales: Tenga en cuenta que se solicitará una tarjeta de crédito válida al momento del check-in para cubrir cualquier cargo incidental.")
        lines.append("• Política sin Efectivo (Cashless): Casa Dorada es un resort sin uso de efectivo. No se aceptan pagos en efectivo en nuestros restaurantes o bares.")
        lines.append("• Check-in: 3:00 p.m. | Check-out: 12:00 p.m. (mediodía)")
    else:
        lines.append("")
        lines.append("RESORT POLICIES:")
        lines.append("• Environmental Sanitation Tax: The County of Los Cabos government implements a tax of MXN $82.12 per room per night (~USD $4.71). This amount is not included in your prepaid rate, will be reflected on your final statement, and is payable at check-in.")
        lines.append("• Incidental Deposit: Please note that a valid credit card will be requested upon check-in to cover any incidental charges.")
        lines.append("• Cashless Policy: Casa Dorada is a cashless resort. Cash payments are not accepted at our restaurants or bars.")
        lines.append("• Check-in: 3:00 p.m. | Check-out: 12:00 noon")

    lines.append("")
    lines.append("----------------------------------------")
    lines.append("Casa Dorada Los Cabos Resort & Spa")
    lines.append("Av. del Pescador s/n, Cabo San Lucas, B.C.S.")
    lines.append("US: 1-866-448-0151")

    return "\\n".join(lines)

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
# ADMIN - REPORTES DE REVENUE / RESERVACIONES CONFIRMADAS
# Los datos se leen de las tablas existentes de Supabase.
# ============================================================

def admin_number(value):
    try:
        number = float(value or 0)
        return number if math.isfinite(number) else 0.0
    except (TypeError, ValueError):
        return 0.0


def admin_json(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return default
    return value if isinstance(value, type(default)) else default


def admin_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def admin_created_date(value):
    """Usar fecha LOCAL de Los Cabos para el mes de confirmación."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo:
            return parsed.astimezone(ZoneInfo('America/Mazatlan')).date()
        return parsed.date()
    except (ValueError, TypeError):
        return admin_date(value)


@st.cache_data(ttl=120, show_spinner=False)
def admin_get_supabase_rows(table, select='*'):
    """Paginación: PostgREST normalmente devuelve un máximo de 1000 filas."""
    config = get_supabase_config()
    if not config:
        raise RuntimeError('No está configurada la conexión con Supabase.')
    endpoint = f"{config['url']}/rest/v1/{table}"
    rows = []
    size = 1000
    for offset in range(0, 200000, size):
        params = {
            'select': select,
            'limit': str(size),
            'offset': str(offset),
            'order': 'created_at.asc',
        }
        response = requests.get(
            endpoint, headers=get_supabase_headers(),
            params=params, timeout=30,
        )
        response.raise_for_status()
        batch = response.json()
        if not isinstance(batch, list):
            raise RuntimeError(f'Respuesta inesperada al consultar {table}.')
        rows.extend(batch)
        if len(batch) < size:
            return rows
    raise RuntimeError('Se alcanzó el límite de 200,000 filas. ' 
                       'Configure un reporte de Supabase para este volumen.')


def admin_normalize_confirmations(raw_rows, legacy_currency='SIN DEFINIR'):
    """Una confirmación -> N habitaciones, sin sumar dos veces su total."""
    # Si se vuelve a guardar el mismo número, conservar solo el último registro.
    deduplicated = {}
    for row in raw_rows:
        if str(row.get('status') or 'CONFIRMED').upper() != 'CONFIRMED':
            continue
        conf_number = str(row.get('confirmation_number') or row.get('id') or '')
        if not conf_number:
            continue
        deduplicated[conf_number] = row

    bookings = []
    for conf_number, rec in deduplicated.items():
        arrival = admin_date(rec.get('arrival'))
        departure = admin_date(rec.get('departure'))
        booking_date = admin_created_date(rec.get('created_at'))
        fallback_nights = int(admin_number(rec.get('nights')))
        if arrival and departure and departure > arrival:
            fallback_nights = (departure - arrival).days
        if fallback_nights <= 0:
            fallback_nights = 1

        saved_rooms = admin_json(rec.get('rooms'), [])
        if not saved_rooms:
            saved_rooms = [{
                'room_type': rec.get('room_type') or 'Sin categoría',
                'nights': fallback_nights,
                'stay_total': rec.get('stay_total'),
                'rate_per_night': rec.get('rate_per_night'),
                'selected_services': [],
            }]
        saved_rooms = [r for r in saved_rooms if isinstance(r, dict)]
        if not saved_rooms:
            continue

        identified = {str(r.get('currency')).upper() for r in saved_rooms
                      if r.get('currency') in ('USD', 'MXN')}
        currency = ('MIXTA' if len(identified) > 1 else
                    next(iter(identified)) if identified else legacy_currency)
        rooms = []
        for index, room in enumerate(saved_rooms, start=1):
            nights = int(admin_number(room.get('nights'))) or fallback_nights
            gross = admin_number(room.get('stay_total'))
            services = room.get('selected_services') or []
            # Usar solo importes históricos guardados, NO precios actuales.
            saved_services_total = room.get('additional_services_total')
            unknown_services = saved_services_total is None and bool(services)
            ancillary = admin_number(saved_services_total)
            rooms.append({
                'room_key': f'{conf_number}|{index}',
                'room_type': str(room.get('room_type') or 'Sin categoría'),
                'nights': nights,
                'room_gross': gross,
                'room_net': gross / (1 + TAX_RATE),
                'services': ancillary,
                'services_unquantified': unknown_services,
            })

        # Solo usar el total guardado a nivel de confirmación si es diferente
        # al detalle; distribuir la diferencia proporcionalmente entre cuartos.
        total_header = admin_number(rec.get('stay_total'))
        details_sum = sum(r['room_gross'] for r in rooms)
        if total_header > 0 and abs(total_header - details_sum) > 0.02:
            if details_sum > 0:
                ratio = total_header / details_sum
                for room in rooms:
                    room['room_gross'] *= ratio
                    room['room_net'] = room['room_gross'] / (1 + TAX_RATE)
            else:
                # Recuperar el total global cuando un registro antiguo carece
                # de desglose; la distribución por categoría será estimada.
                for room in rooms:
                    room['room_gross'] = total_header / len(rooms)
                    room['room_net'] = room['room_gross'] / (1 + TAX_RATE)

        bookings.append({
            'confirmation_number': conf_number,
            'quotation_number': rec.get('quotation_number'),
            'guest_name': rec.get('guest_name') or '',
            'arrival': arrival,
            'departure': departure,
            'booking_date': booking_date,
            'created_by': str(rec.get('confirmed_by') or rec.get('created_by') or 'Sin asignar'),
            'payment_status': str(rec.get('payment_status') or 'Sin dato'),
            'deposit': admin_number(rec.get('first_night_amount')),
            'balance_due': admin_number(rec.get('balance_due')),
            'source': 'Cotización' if rec.get('quotation_number') else 'Manual',
            'currency': currency,
            'rooms': rooms,
        })
    return bookings, len(raw_rows) - len(deduplicated)


def admin_allocate(bookings, period_mode):
    """Registro por cuarto y mes. Mes de estancia reparte según noches ocupadas."""
    allocations = []
    for book in bookings:
        if period_mode == 'Mes de llegada':
            month_day = book['arrival']
        else:
            month_day = book['booking_date']
        for room in book['rooms']:
            base = {
                'confirmation_number': book['confirmation_number'],
                'quotation_number': book['quotation_number'],
                'guest_name': book['guest_name'],
                'arrival': book['arrival'],
                'departure': book['departure'],
                'booking_date': book['booking_date'],
                'created_by': book['created_by'],
                'payment_status': book['payment_status'],
                'deposit': book['deposit'],
                'balance_due': book['balance_due'],
                'source': book['source'],
                'currency': book['currency'],
                'room_key': room['room_key'],
                'room_type': room['room_type'],
                'services_unquantified': room['services_unquantified'],
            }
            if period_mode != 'Mes de estancia':
                allocations.append({
                    **base,
                    'month': month_day.strftime('%Y-%m') if month_day else 'Sin fecha',
                    'room_nights': room['nights'],
                    'room_gross': room['room_gross'],
                    'room_net': room['room_net'],
                    'services': room['services'],
                })
            elif book['arrival'] and book['departure'] and book['departure'] > book['arrival']:
                # Prorrateo de alojamiento por cada noche ocupada.
                duration = (book['departure'] - book['arrival']).days
                for n in range(duration):
                    night_date = book['arrival'] + timedelta(days=n)
                    allocations.append({
                        **base,
                        'month': night_date.strftime('%Y-%m'),
                        'room_nights': 1,
                        'room_gross': room['room_gross'] / duration,
                        'room_net': room['room_net'] / duration,
                        # Servicios asociados al mes de llegada, una sola vez.
                        'services': room['services'] if n == 0 else 0.0,
                    })
            else:
                allocations.append({
                    **base,
                    'month': 'Sin fecha',
                    'room_nights': room['nights'],
                    'room_gross': room['room_gross'],
                    'room_net': room['room_net'],
                    'services': room['services'],
                })
    return allocations


def admin_monthly_summary(allocations):
    monthly = {}
    for a in allocations:
        key = a['month']
        target = monthly.setdefault(key, {
            'Mes': key, 'Confirmaciones': set(), 'Habitaciones': set(),
            'Noches habitación': 0, 'Revenue habitaciones neto': 0.0,
            'Impuestos alojamiento': 0.0, 'Revenue habitaciones con impuestos': 0.0,
            'Servicios registrados': 0.0, 'Revenue total registrado': 0.0,
            'ADR neto': 0.0,
        })
        target['Confirmaciones'].add(a['confirmation_number'])
        target['Habitaciones'].add(a['room_key'])
        target['Noches habitación'] += a['room_nights']
        target['Revenue habitaciones neto'] += a['room_net']
        target['Revenue habitaciones con impuestos'] += a['room_gross']
        target['Impuestos alojamiento'] += a['room_gross'] - a['room_net']
        target['Servicios registrados'] += a['services']
        target['Revenue total registrado'] += a['room_gross'] + a['services']
    result = []
    for m in sorted(monthly):
        row = dict(monthly[m])
        row['Confirmaciones'] = len(row['Confirmaciones'])
        row['Habitaciones'] = len(row['Habitaciones'])
        nights = row['Noches habitación']
        row['ADR neto'] = row['Revenue habitaciones neto'] / nights if nights else 0
        result.append(row)
    return result


def admin_table(allocations, group_field, label):
    groups = {}
    for row in allocations:
        key = row[group_field]
        agg = groups.setdefault(key, {
            label: key, 'Confirmaciones': set(), 'Habitaciones': set(),
            'Noches habitación': 0, 'Revenue neto': 0.0,
            'Revenue con impuestos': 0.0, 'Servicios registrados': 0.0,
        })
        agg['Confirmaciones'].add(row['confirmation_number'])
        agg['Habitaciones'].add(row['room_key'])
        agg['Noches habitación'] += row['room_nights']
        agg['Revenue neto'] += row['room_net']
        agg['Revenue con impuestos'] += row['room_gross']
        agg['Servicios registrados'] += row['services']
    values = []
    for group in groups.values():
        group['Confirmaciones'] = len(group['Confirmaciones'])
        group['Habitaciones'] = len(group['Habitaciones'])
        nights = group['Noches habitación']
        group['ADR neto'] = group['Revenue neto'] / nights if nights else 0.0
        values.append(group)
    return sorted(values, key=lambda r: r['Revenue neto'], reverse=True)


def admin_confirmation_detail(allocations):
    result = {}
    for a in allocations:
        key = a['confirmation_number']
        v = result.setdefault(key, {
            'Confirmación': key,
            'Cotización': a['quotation_number'] or '',
            'Huésped': a['guest_name'],
            'Fecha confirmación': str(a['booking_date'] or ''),
            'Llegada': str(a['arrival'] or ''),
            'Salida': str(a['departure'] or ''),
            'Agente': a['created_by'],
            'Origen': a['source'],
            'Estado de pago': a['payment_status'],
            'Depósito indicado (reserva completa)': a['deposit'],
            'Saldo indicado (reserva completa)': a['balance_due'],
            'Habitaciones': set(), 'Categorías': set(),
            'Noches habitación': 0, 'Revenue habitaciones neto': 0.0,
            'Revenue habitaciones con impuestos': 0.0,
            'Servicios registrados': 0.0, 'Total registrado': 0.0,
        })
        v['Habitaciones'].add(a['room_key'])
        v['Categorías'].add(a['room_type'])
        v['Noches habitación'] += a['room_nights']
        v['Revenue habitaciones neto'] += a['room_net']
        v['Revenue habitaciones con impuestos'] += a['room_gross']
        v['Servicios registrados'] += a['services']
        v['Total registrado'] += a['room_gross'] + a['services']
    rows = []
    for v in result.values():
        v['Habitaciones'] = len(v['Habitaciones'])
        v['Categorías'] = ', '.join(sorted(v['Categorías']))
        rows.append(v)
    return sorted(rows, key=lambda row: row['Fecha confirmación'], reverse=True)


def admin_download_csv(label, rows, file_name, key):
    if not rows:
        return
    df = pd.DataFrame(rows)
    # Impedir fórmulas maliciosas al abrir información de huéspedes en Excel.
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(
            lambda value: "'" + value if isinstance(value, str)
            and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r'))
            else value
        )
    st.download_button(
        label, data=df.to_csv(index=False).encode('utf-8-sig'),
        file_name=file_name, mime='text/csv', key=key,
        use_container_width=True,
    )


def admin_show_dashboard():
    st.title('Admin | Revenue & Confirmaciones')
    email = get_logged_in_email()
    if not email:
        st.warning('Inicia sesión con tu cuenta @casadorada.com para acceder a Admin.')
        return

    if st.session_state.get('admin_authorized_email') != email:
        st.session_state['admin_authorized_email'] = None

    if st.session_state.get('admin_authorized_email') != email:
        if st.session_state.get('admin_bad_attempts', 0) >= 5:
            st.error('Demasiados intentos fallidos en esta sesión. Cierra la sesión y contacta al administrador.')
            return
        with st.form('admin_login'):
            pin = st.text_input('Contraseña de Admin', type='password')
            submit = st.form_submit_button('Entrar a Admin', use_container_width=True)
        if submit:
            try:
                configured_password = str(st.secrets.get('admin_password', '1234'))
            except Exception:
                configured_password = '1234'
            if hmac.compare_digest(str(pin).encode('utf-8'), configured_password.encode('utf-8')):
                st.session_state['admin_authorized_email'] = email
                st.session_state['admin_bad_attempts'] = 0
                st.rerun()
            else:
                st.session_state['admin_bad_attempts'] = st.session_state.get('admin_bad_attempts', 0) + 1
                st.error('Contraseña incorrecta.')
        return

    left, right = st.columns([5, 1])
    with left:
        st.caption(f'Sesión administrativa: {email}')
    with right:
        if st.button('Cerrar Admin', use_container_width=True):
            st.session_state['admin_authorized_email'] = None
            st.rerun()

    if st.button('Actualizar datos de Supabase', key='admin_refresh'):
        admin_get_supabase_rows.clear()
        st.rerun()

    try:
        confirmations = admin_get_supabase_rows('confirmations')
    except Exception as exc:
        st.error('No fue posible consultar las confirmaciones en Supabase.')
        st.code(str(exc))
        return

    if not confirmations:
        st.info('Todavía no se encuentran confirmaciones guardadas en Supabase.')
        return

    st.markdown('### Configuración del reporte')
    legacy_choice = st.selectbox(
        'Moneda de confirmaciones antiguas sin moneda guardada',
        ['SIN DEFINIR', 'USD', 'MXN'], index=0,
        help='Las confirmaciones anteriores a este módulo no guardaban su moneda. '
             'Selecciona USD o MXN únicamente si puedes corroborarlo.',
    )
    bookings, removed_count = admin_normalize_confirmations(confirmations, legacy_choice)
    if not bookings:
        st.info('No hay confirmaciones vigentes para analizar.')
        return
    if any(b['currency'] == 'SIN DEFINIR' for b in bookings):
        st.warning('Hay registros históricos sin identificación de moneda. '
                   'Se muestran separados; no se suman como USD o MXN sin tu autorización.')
    if any(b['currency'] == 'MIXTA' for b in bookings):
        st.error('Hay confirmaciones con habitaciones en diferentes monedas; '
                 'están separadas en MIXTA y requieren revisión manual.')
    if removed_count:
        st.caption(f'{removed_count} registros repetidos o no confirmados no se contabilizaron.')

    filter1, filter2, filter3 = st.columns(3)
    with filter1:
        period_mode = st.selectbox(
            'Agrupar por', ['Mes de confirmación', 'Mes de llegada', 'Mes de estancia'],
            help='Mes de estancia prorratea el importe de alojamiento entre las noches de cada mes. '
                 'Los servicios se asignan al mes de llegada.',
        )
    with filter2:
        currencies = sorted({b['currency'] for b in bookings})
        currency = st.selectbox('Moneda del reporte (sin conversión)', currencies,
            index=currencies.index('USD') if 'USD' in currencies else 0)
    with filter3:
        source = st.selectbox('Origen', ['Todos', 'Cotización', 'Manual'])

    currency_bookings = [b for b in bookings if b['currency'] == currency and
                         (source == 'Todos' or b['source'] == source)]
    all_allocations = admin_allocate(currency_bookings, period_mode)
    if not all_allocations:
        st.info('No hay datos en esta combinación de filtros.')
        return

    month_values = sorted({row['month'] for row in all_allocations if row['month'] != 'Sin fecha'})
    years = sorted({m[:4] for m in month_values}, reverse=True)
    filter4, filter5, filter6 = st.columns(3)
    with filter4:
        year = st.selectbox('Año', ['Todos'] + years,
            index=1 if years else 0)
    with filter5:
        month = st.selectbox('Mes', ['Todos'] + [f'{i:02d}' for i in range(1, 13)])
    with filter6:
        agents = sorted({b['created_by'] for b in currency_bookings})
        agent = st.selectbox('Agente', ['Todos'] + agents)

    room_types = sorted({r['room_type'] for b in currency_bookings for r in b['rooms']})
    room_type = st.selectbox('Categoría de habitación', ['Todas'] + room_types)

    allocations = [a for a in all_allocations
                   if (year == 'Todos' or a['month'][:4] == year)
                   and (month == 'Todos' or a['month'][5:7] == month)
                   and (agent == 'Todos' or a['created_by'] == agent)
                   and (room_type == 'Todas' or a['room_type'] == room_type)]
    if not allocations:
        st.info('No hay confirmaciones para estos filtros.')
        return

    revenue_net = sum(a['room_net'] for a in allocations)
    revenue_gross = sum(a['room_gross'] for a in allocations)
    ancillary = sum(a['services'] for a in allocations)
    room_nights = sum(a['room_nights'] for a in allocations)
    unique_confs = {a['confirmation_number'] for a in allocations}
    unique_rooms = {a['room_key'] for a in allocations}
    incomplete_service_rooms = {a['room_key'] for a in allocations if a['services_unquantified']}

    st.divider()
    st.caption('Indicadores de reservaciones confirmadas (no equivalen a dinero cobrado). '
               'ADR y revenue neto de habitaciones excluyen el 30% de impuestos configurado en la app.')
    metrics = st.columns(4)
    metrics[0].metric('Revenue habitaciones (neto)', money(revenue_net, currency))
    metrics[1].metric('Revenue habitaciones (con impuestos)', money(revenue_gross, currency))
    metrics[2].metric('Noches habitación', f'{room_nights:,}')
    metrics[3].metric('ADR neto', money(revenue_net / room_nights if room_nights else 0, currency))
    metrics2 = st.columns(4)
    metrics2[0].metric('Confirmaciones', f'{len(unique_confs):,}')
    metrics2[1].metric('Habitaciones', f'{len(unique_rooms):,}')
    metrics2[2].metric('Servicios con precio registrado', money(ancillary, currency))
    metrics2[3].metric('Valor total registrado', money(revenue_gross + ancillary, currency))
    st.caption(
        f"Noches promedio por habitación en el periodo: "
        f"{room_nights / len(unique_rooms):.1f} noches. "
        f"Ingreso promedio por confirmación en el periodo: "
        f"{money((revenue_gross + ancillary) / len(unique_confs), currency)}."
    )

    if incomplete_service_rooms:
        st.warning(f'{len(incomplete_service_rooms)} habitación(es) antiguas contienen servicios '
                   'cuyo precio histórico no fue almacenado; los ingresos de esos servicios '
                   'NO se estiman con las tarifas actuales. El valor total podría ser mayor.')
    if currency in ('SIN DEFINIR', 'MIXTA'):
        st.warning('Los importes de este reporte NO tienen moneda verificada; revisa '
                   'los registros históricos antes de utilizarlos en un reporte financiero.')

    monthly_rows = admin_monthly_summary(allocations)
    category_rows = admin_table(allocations, 'room_type', 'Categoría')
    agent_rows = admin_table(allocations, 'created_by', 'Agente')
    detail_rows = admin_confirmation_detail(allocations)

    st.divider()
    tab_months, tab_rooms, tab_agents, tab_detail, tab_conversion = st.tabs([
        'Mensual', 'Categorías', 'Agentes', 'Reservaciones', 'Conversión',
    ])

    with tab_months:
        st.subheader('Evolución mensual')
        st.bar_chart(pd.DataFrame(monthly_rows).set_index('Mes')[
            ['Revenue habitaciones neto', 'Revenue habitaciones con impuestos']
        ])
        st.dataframe(pd.DataFrame(monthly_rows), hide_index=True, use_container_width=True)
        admin_download_csv('Descargar reporte mensual CSV', monthly_rows,
            'casa_dorada_revenue_mensual.csv', 'admin_monthly_csv')
    with tab_rooms:
        st.subheader('Producción por categoría')
        st.dataframe(pd.DataFrame(category_rows), hide_index=True, use_container_width=True)
        admin_download_csv('Descargar reporte por categoría CSV', category_rows,
            'casa_dorada_categorias.csv', 'admin_rooms_csv')
    with tab_agents:
        st.subheader('Producción por agente')
        st.dataframe(pd.DataFrame(agent_rows), hide_index=True, use_container_width=True)
        admin_download_csv('Descargar reporte por agente CSV', agent_rows,
            'casa_dorada_agentes.csv', 'admin_agents_csv')
    with tab_detail:
        st.subheader('Confirmaciones incluidas en el reporte')
        st.caption('Depósito y saldo son importes indicados en cada reserva, NO cobros verificados. '
                   'En filtros de categorías corresponden a la reserva completa. '
                   'En el modo Mes de estancia, los montos mostrados se limitan '
                   'a las noches correspondientes al periodo seleccionado.')
        st.dataframe(pd.DataFrame(detail_rows), hide_index=True, use_container_width=True)
        admin_download_csv('Descargar detalle de reservaciones CSV', detail_rows,
            'casa_dorada_confirmaciones.csv', 'admin_detail_csv')
    with tab_conversion:
        st.subheader('Seguimiento de cotizaciones')
        st.caption('Conversión por cohorte: cotizaciones creadas en el periodo '
                   'y que cuentan con al menos una confirmación guardada. '
                   'Las confirmaciones manuales quedan fuera de esta tasa.')
        try:
            quotes = admin_get_supabase_rows(
                'quotations', 'quotation_number,created_at,created_by,status'
            )
        except Exception as exc:
            st.error('No se pudo consultar la tabla quotations.')
            st.code(str(exc))
        else:
            # El filtro de cotizaciones usa la fecha de creación, NO la llegada/estancia.
            cohort = []
            seen = set()
            for q in quotes:
                qn = q.get('quotation_number')
                qdate = admin_created_date(q.get('created_at'))
                if not qn or qn in seen or not qdate:
                    continue
                if year != 'Todos' and str(qdate.year) != year:
                    continue
                if month != 'Todos' and f'{qdate.month:02d}' != month:
                    continue
                if agent != 'Todos' and (q.get('created_by') or '') != agent:
                    continue
                seen.add(qn)
                cohort.append(qn)
            confirmed_quote_numbers = {b['quotation_number'] for b in bookings
                                       if b['quotation_number']}
            converted = sum(qn in confirmed_quote_numbers for qn in cohort)
            c1, c2, c3 = st.columns(3)
            c1.metric('Cotizaciones creadas', f'{len(cohort):,}')
            c2.metric('Cotizaciones convertidas', f'{converted:,}')
            c3.metric('Conversión', f'{100 * converted / len(cohort):.1f}%'
                if cohort else 'N/D')
            st.caption('Las cotizaciones pueden confirmarse en meses posteriores. '
                       'Este porcentaje no depende del filtro de tipo de habitación ni moneda.')



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

    "pending_modified_quote":
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

    "modify_search_results":
        [],

    "modify_selected_quote":
        None,

    "modify_success":
        False,

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
            "Modify Quotation",
            "Confirm Quotation", 
            "Manual Confirmation",
            "Admin"
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

            "currency": curr_code,
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
# WORKFLOW: MODIFY QUOTATION
# ============================================================

elif app_mode == "Modify Quotation":

    st.title(
        "Modify Quotation"
    )

    st.caption(
        "Search for an existing quotation, edit it, and save "
        "the updated version without creating a new quotation number."
    )

    if st.session_state.get("modify_success"):

        st.success(
            st.session_state.modify_success
        )

        st.session_state.modify_success = False

    st.markdown(
        "## Search Quotation"
    )

    modify_search_term = st.text_input(
        "Enter Quotation Number, Guest Name, or Guest Email",
        placeholder="e.g. CD240101-1234 or guest@email.com",
        key="modify_search_term",
    )

    if st.button(
        "Search",
        use_container_width=True,
        key="modify_search_button",
    ):

        if modify_search_term:

            results = search_quotations_in_supabase(
                modify_search_term
            )

            st.session_state.modify_search_results = results
            st.session_state.modify_selected_quote = None

        else:

            st.warning(
                "Please enter a search term."
            )

    modify_results = (
        st.session_state.modify_search_results
    )

    if modify_results:

        st.markdown(
            "### Search Results"
        )

        for q in modify_results:

            with st.container():

                col1, col2, col3, col4, col5 = (
                    st.columns([2, 3, 2, 2, 1])
                )

                col1.write(
                    f"**{q['quotation_number']}**"
                )

                col2.write(
                    f"{q['guest_name']} ({q['guest_email']})"
                )

                col3.write(
                    f"{q['arrival']} to {q['departure']}"
                )

                col4.write(
                    f"Status: **{q['status']}**"
                )

                if col5.button(
                    "Select",
                    key=(
                        "modify_sel_"
                        f"{q['quotation_number']}"
                    ),
                ):

                    if q.get("status") in [
                        "CONFIRMED",
                        "CANCELLED",
                    ]:

                        st.error(
                            "This quotation cannot be modified because "
                            f"its current status is {q.get('status')}."
                        )

                        st.session_state.modify_selected_quote = None

                    else:

                        st.session_state.modify_selected_quote = q
                        st.rerun()

                st.divider()

    modify_quote = (
        st.session_state.modify_selected_quote
    )

    if modify_quote:

        quotation_number = modify_quote[
            "quotation_number"
        ]

        st.markdown(
            f"## Editing: {quotation_number}"
        )

        st.caption(
            "The quotation number will remain unchanged."
        )

        try:
            default_arrival = date.fromisoformat(
                str(modify_quote.get("arrival"))
            )
        except Exception:
            default_arrival = date.today()

        try:
            default_departure = date.fromisoformat(
                str(modify_quote.get("departure"))
            )
        except Exception:
            default_departure = date.today()

        edit_col1, edit_col2 = st.columns(2)

        with edit_col1:

            m_guest_name = st.text_input(
                "Guest name",
                value=modify_quote.get(
                    "guest_name",
                    "",
                ),
                key=(
                    "modify_guest_name_"
                    f"{quotation_number}"
                ),
            )

        with edit_col2:

            m_guest_email = st.text_input(
                "Guest email",
                value=modify_quote.get(
                    "guest_email",
                    "",
                ),
                key=(
                    "modify_guest_email_"
                    f"{quotation_number}"
                ),
            )

        edit_col3, edit_col4, edit_col5 = (
            st.columns(3)
        )

        with edit_col3:

            m_arrival = st.date_input(
                "Arrival",
                value=default_arrival,
                key=(
                    "modify_arrival_"
                    f"{quotation_number}"
                ),
            )

        with edit_col4:

            m_departure = st.date_input(
                "Departure",
                value=default_departure,
                key=(
                    "modify_departure_"
                    f"{quotation_number}"
                ),
            )

        m_calculated_nights = max(
            1,
            (m_departure - m_arrival).days,
        )

        with edit_col5:

            m_nights = st.number_input(
                "Nights",
                min_value=1,
                max_value=365,
                value=m_calculated_nights,
                step=1,
                key=(
                    "modify_nights_"
                    f"{quotation_number}"
                ),
            )

        original_options = modify_quote.get(
            "options",
            [],
        ) or []

        original_count = max(
            1,
            min(5, len(original_options)),
        )

        m_number_options = st.selectbox(
            "Number of quotation options",
            [1, 2, 3, 4, 5],
            index=original_count - 1,
            key=(
                "modify_number_options_"
                f"{quotation_number}"
            ),
        )

        st.divider()

        modified_options = []

        for option_index in range(
            m_number_options
        ):

            option_number = option_index + 1

            if option_index < len(original_options):
                existing_option = original_options[
                    option_index
                ] or {}
            else:
                existing_option = {}

            st.markdown(
                f"## Quotation Option {option_number}"
            )

            existing_room = existing_option.get(
                "room_type",
                list(ROOM_TYPES.keys())[0],
            )

            room_choices = list(
                ROOM_TYPES.keys()
            )

            if existing_room not in room_choices:
                room_choices.insert(
                    0,
                    existing_room,
                )

            room_index = room_choices.index(
                existing_room
            )

            m_room_type = st.selectbox(
                "Room type",
                room_choices,
                index=room_index,
                key=(
                    "modify_room_type_"
                    f"{quotation_number}_"
                    f"{option_number}"
                ),
            )

            st.markdown(
                "### Guests"
            )

            opt_g1, opt_g2 = st.columns(2)

            with opt_g1:

                m_opt_adults = st.number_input(
                    "Adults",
                    min_value=1,
                    max_value=20,
                    value=int(
                        existing_option.get(
                            "adults",
                            modify_quote.get(
                                "adults",
                                2,
                            ),
                        )
                    ),
                    step=1,
                    key=(
                        "modify_adults_"
                        f"{quotation_number}_"
                        f"{option_number}"
                    ),
                )

            with opt_g2:

                m_opt_children = st.number_input(
                    "Children",
                    min_value=0,
                    max_value=20,
                    value=int(
                        existing_option.get(
                            "children",
                            modify_quote.get(
                                "children",
                                0,
                            ),
                        )
                    ),
                    step=1,
                    key=(
                        "modify_children_"
                        f"{quotation_number}_"
                        f"{option_number}"
                    ),
                )

            st.markdown(
                "### Rate"
            )

            rate_col1, rate_col2 = st.columns(2)

            current_total = float(
                existing_option.get(
                    "stay_total_tax_included",
                    0.0,
                ) or 0.0
            )

            with rate_col1:

                m_stay_total = st.number_input(
                    f"Stay Total Taxes Included ({curr_code})",
                    min_value=0.00,
                    value=current_total,
                    step=100.00,
                    format="%.2f",
                    key=(
                        "modify_total_"
                        f"{quotation_number}_"
                        f"{option_number}"
                    ),
                )

            current_valid_until = (
                existing_option.get(
                    "valid_until"
                )
            )

            try:
                current_valid_until = (
                    date.fromisoformat(
                        str(current_valid_until)
                    )
                )
            except Exception:
                current_valid_until = date.today()

            with rate_col2:

                m_valid_until = st.date_input(
                    "Quote valid until",
                    value=current_valid_until,
                    key=(
                        "modify_valid_until_"
                        f"{quotation_number}_"
                        f"{option_number}"
                    ),
                )

            calculations = calculate_rate_values(
                m_stay_total,
                m_nights,
            )

            metric_col1, metric_col2, metric_col3 = (
                st.columns(3)
            )

            metric_col1.metric(
                "Rate per night before taxes",
                money(
                    calculations[
                        "nightly_before_tax"
                    ],
                    curr_code,
                ),
            )

            metric_col2.metric(
                "Rate per night taxes included",
                money(
                    calculations[
                        "nightly_with_tax"
                    ],
                    curr_code,
                ),
            )

            metric_col3.metric(
                "Stay total taxes included",
                money(
                    calculations[
                        "total_with_tax"
                    ],
                    curr_code,
                ),
            )

            st.markdown(
                "### Included Benefits"
            )

            current_inclusions = set(
                existing_option.get(
                    "selected_inclusions",
                    [],
                ) or []
            )

            m_selected_inclusions = []

            for inc_index, inclusion in enumerate(
                AVAILABLE_INCLUSIONS
            ):

                if st.checkbox(
                    inclusion,
                    value=(
                        inclusion in current_inclusions
                    ),
                    key=(
                        "modify_inc_"
                        f"{quotation_number}_"
                        f"{option_number}_"
                        f"{inc_index}"
                    ),
                ):

                    m_selected_inclusions.append(
                        inclusion
                    )

            st.markdown(
                "### Additional Services"
            )

            current_services = set(
                existing_option.get(
                    "selected_services",
                    [],
                ) or []
            )

            m_selected_services = []

            for service_index, service in enumerate(
                ADDITIONAL_SERVICES.keys()
            ):

                service_label = (
                    f"{service} - "
                    f"{money(get_service_price(service, curr_code), curr_code)}"
                )

                if st.checkbox(
                    service_label,
                    value=(
                        service in current_services
                    ),
                    key=(
                        "modify_service_"
                        f"{quotation_number}_"
                        f"{option_number}_"
                        f"{service_index}"
                    ),
                ):

                    m_selected_services.append(
                        service
                    )

            services_total = sum(
                get_service_price(
                    service,
                    curr_code,
                )
                for service in m_selected_services
            )

            st.metric(
                "Total Amount",
                money(
                    calculations[
                        "total_with_tax"
                    ] + services_total,
                    curr_code,
                ),
            )

            st.markdown(
                "### Deposit Policy"
            )

            if lang_code == "es":

                modify_deposit_policies = [
                    "Se requiere el pago total de la estadía con impuestos incluidos al momento de reservar.",
                    "Se requiere el depósito de la primera noche con impuestos incluidos al momento de reservar.",
                ]

            else:

                modify_deposit_policies = [
                    "The deposit for the whole stay with taxes included is required upon booking.",
                    "The deposit for the first night with taxes included is required upon booking.",
                ]

            current_deposit = existing_option.get(
                "deposit_policy",
                modify_deposit_policies[0],
            )

            if current_deposit not in modify_deposit_policies:
                modify_deposit_policies.insert(
                    0,
                    current_deposit,
                )

            m_deposit_policy = st.selectbox(
                "Select deposit policy",
                modify_deposit_policies,
                index=modify_deposit_policies.index(
                    current_deposit
                ),
                key=(
                    "modify_deposit_"
                    f"{quotation_number}_"
                    f"{option_number}"
                ),
            )

            st.markdown(
                "### Cancellation Policy"
            )

            current_cancellation = existing_option.get(
                "cancellation_policy",
                CANCELLATION_POLICIES[0],
            )

            cancellation_choices = list(
                CANCELLATION_POLICIES
            )

            if current_cancellation not in cancellation_choices:
                cancellation_choices.insert(
                    0,
                    current_cancellation,
                )

            m_cancellation_policy = st.selectbox(
                "Select cancellation policy",
                cancellation_choices,
                index=cancellation_choices.index(
                    current_cancellation
                ),
                key=(
                    "modify_cancel_"
                    f"{quotation_number}_"
                    f"{option_number}"
                ),
            )

            st.markdown(
                "### Optional Links"
            )

            link_col1, link_col2 = st.columns(2)

            m_room_360_url = ROOM_TYPES.get(
                m_room_type,
                {},
            ).get(
                "360_url",
                existing_option.get(
                    "room_360_url",
                    "",
                ),
            )

            with link_col1:

                st.text_input(
                    "360° Room View Link",
                    value=m_room_360_url,
                    key=(
                        "modify_360_"
                        f"{quotation_number}_"
                        f"{option_number}_"
                        f"{m_room_type}"
                    ),
                    disabled=True,
                )

            with link_col2:

                m_payment_url = st.text_input(
                    "Payment Link",
                    value=existing_option.get(
                        "payment_url",
                        "",
                    ) or "",
                    placeholder="https://...",
                    key=(
                        "modify_payment_"
                        f"{quotation_number}_"
                        f"{option_number}"
                    ),
                )

            modified_options.append({
                "room_type": m_room_type,
                "adults": m_opt_adults,
                "children": m_opt_children,
                "valid_until": m_valid_until,
                "stay_total_tax_included": m_stay_total,
                "selected_inclusions": m_selected_inclusions,
                "selected_services": m_selected_services,
                "deposit_policy": m_deposit_policy,
                "cancellation_policy": m_cancellation_policy,
                "payment_url": m_payment_url,
                "room_360_url": m_room_360_url,
                "currency": curr_code,
            })

            st.divider()

        modified_email_html = build_email_html(
            guest_name=(
                m_guest_name or "Guest"
            ),
            arrival=m_arrival,
            departure=m_departure,
            nights=m_nights,
            options=modified_options,
            lang=lang_code,
            currency=curr_code,
        )

        modified_plain_text = build_plain_text(
            guest_name=(
                m_guest_name or "Guest"
            ),
            arrival=m_arrival,
            departure=m_departure,
            nights=m_nights,
            options=modified_options,
            lang=lang_code,
            currency=curr_code,
        )

        st.markdown(
            "## Updated Email Preview"
        )

        st.caption(
            "This is the updated quotation that will be saved "
            "to Gmail Drafts."
        )

        b64_modified_email = base64.b64encode(
            modified_email_html.encode(
                "utf-8"
            )
        ).decode(
            "utf-8"
        )

        modify_iframe_height = (
            850 + m_number_options * 750
        )

        modify_iframe_html = (
            '<iframe '
            f'src="data:text/html;base64,{b64_modified_email}" '
            'width="100%" '
            f'height="{modify_iframe_height}" '
            'style="border:none; border-radius:8px; background:#fff;">'
            '</iframe>'
        )

        st.markdown(
            modify_iframe_html,
            unsafe_allow_html=True,
        )

        st.markdown(
            "## Actions"
        )

        modify_action_col1, modify_action_col2 = (
            st.columns(2)
        )

        modified_subject = (
            f"{TRANSLATIONS[lang_code]['custom_quotation']} | "
            "Casa Dorada Los Cabos"
        )

        with modify_action_col1:

            if st.button(
                "Save Changes",
                use_container_width=True,
                key=(
                    "modify_save_"
                    f"{quotation_number}"
                ),
            ):

                if not m_guest_name:

                    st.error(
                        "Please enter the guest name."
                    )

                elif not m_guest_email:

                    st.error(
                        "Please enter the guest email."
                    )

                else:

                    updated_quote = update_quotation_in_supabase(
                        quotation_number=quotation_number,
                        guest_name=m_guest_name,
                        guest_email=m_guest_email,
                        arrival=m_arrival,
                        departure=m_departure,
                        nights=m_nights,
                        options=modified_options,
                        status=modify_quote.get(
                            "status",
                            "QUOTED",
                        ),
                    )

                    if updated_quote:

                        st.success(
                            f"Quotation #{quotation_number} updated successfully."
                        )

                    else:

                        st.error(
                            "The quotation could not be updated."
                        )

        with modify_action_col2:

            if st.button(
                "Save Changes & Create Gmail Draft",
                use_container_width=True,
                key=(
                    "modify_draft_"
                    f"{quotation_number}"
                ),
            ):

                if not m_guest_name:

                    st.error(
                        "Please enter the guest name."
                    )

                elif not m_guest_email:

                    st.error(
                        "Please enter the guest email."
                    )

                else:

                    st.session_state.pending_modified_quote = {
                        "quotation_number": quotation_number,
                        "guest_name": m_guest_name,
                        "guest_email": m_guest_email,
                        "arrival": m_arrival,
                        "departure": m_departure,
                        "nights": m_nights,
                        "options": modified_options,
                        "status": modify_quote.get(
                            "status",
                            "QUOTED",
                        ),
                        "subject": modified_subject,
                        "email_html": modified_email_html,
                        "plain_text_email": modified_plain_text,
                    }

                    st.session_state.pending_action = (
                        "modify_draft"
                    )

                    gmail_service = get_gmail_service()

                    if gmail_service:

                        execute_pending_modified_quote()
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
                                "Your changes have been saved temporarily. "
                                "Sign in with your @casadorada.com account "
                                "to continue."
                            )

                            st.login()

                        else:

                            login_url = get_google_login_url()

                            st.warning(
                                "Your changes are saved temporarily. "
                                "Connect Gmail to create the updated draft."
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
                                "After authorization, the quotation will be "
                                "updated and the new Gmail draft will be "
                                "created automatically."
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

            # ============================================================
            # MULTIPLE ROOMS / SELECTED OPTIONS
            # ============================================================

            confirmation_rooms = []

            for opt in selected_options:

                confirmation_rooms.append({
                    "room_type": opt.get("room_type", ""),
                    "adults": int(
                        opt.get(
                            "adults",
                            selected_quote.get("adults", 2),
                        )
                    ),
                    "children": int(
                        opt.get(
                            "children",
                            selected_quote.get("children", 0),
                        )
                    ),
                    "nights": int(selected_quote.get("nights", 1)),
                    # Metadata guardada en JSONB rooms para reportes.
                    # Las cotizaciones antiguas no traían moneda;
                    # no inventar esa información al confirmar.
                    "currency": opt.get("currency"),
                    "additional_services_total": (
                        round(sum(
                            get_service_price(service, opt["currency"])
                            for service in (opt.get("selected_services") or [])
                        ), 2) if opt.get("currency") in ("USD", "MXN")
                        else None
                    ),
                    "rate_per_night": float(
                        opt.get("nightly_taxes_included", 0)
                    ),
                    # Base de habitación únicamente. Los servicios se agregan después
                    # para evitar contarlos dos veces.
                    "stay_total": float(
                        opt.get(
                            "stay_total_tax_included",
                            opt.get("final_total", 0)
                            - opt.get("additional_services_total", 0),
                        )
                    ),
                    "selected_inclusions": opt.get(
                        "selected_inclusions", []
                    ),
                    "selected_services": opt.get(
                        "selected_services", []
                    ),
                })

            selected_opt_adults = sum(
                room["adults"] for room in confirmation_rooms
            )

            selected_opt_children = sum(
                room["children"] for room in confirmation_rooms
            )

            stay_total = sum(
                room["stay_total"] for room in confirmation_rooms
            )

            rate_per_night = sum(
                room["rate_per_night"] for room in confirmation_rooms
            )

            # Legacy room_type field: keep the first room only.
            # The complete multi-room detail is stored in `rooms`.
            legacy_room_type = (
                confirmation_rooms[0]["room_type"]
                if confirmation_rooms
                else ""
            )

            # Combinar inclusiones y servicios sin duplicados.
            comb_inclusions = []
            comb_services = []

            for room in confirmation_rooms:
                for inc in room.get("selected_inclusions", []):
                    if inc not in comb_inclusions:
                        comb_inclusions.append(inc)

                for srv in room.get("selected_services", []):
                    if srv not in comb_services:
                        comb_services.append(srv)

            can_policy_default = selected_options[0].get(
                "cancellation_policy",
                CANCELLATION_POLICIES[0],
            )

            st.markdown("### Payment & Comments")

            payment_status = st.radio(
                "Payment Status",
                ["First Night Deposit", "Fully Paid"],
            )

            # ============================================================
            # ADDITIONAL SERVICES TOTAL
            # ============================================================

            additional_services_total = 0.00

            for room in confirmation_rooms:
                for service in room.get("selected_services", []):
                    additional_services_total += get_service_price(
                        service,
                        curr_code,
                    )

            # ============================================================
            # GRAND TOTAL
            # ============================================================

            grand_total = stay_total + additional_services_total

            # ============================================================
            # PAYMENT STATUS
            # ============================================================

            if payment_status == "Fully Paid":
                deposit = grand_total
                balance = 0.00
                payment_status_trans = TRANSLATIONS[lang_code][
                    "fully_paid"
                ]
            else:
                # First night deposit = suma de la primera noche
                # de TODOS los cuartos. Los servicios NO forman parte
                # del depósito inicial.
                deposit = rate_per_night
                balance = max(grand_total - deposit, 0.00)
                payment_status_trans = TRANSLATIONS[lang_code][
                    "first_night_deposit"
                ]

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Total Amount",
                money(grand_total, curr_code),
            )
            col2.metric(
                "Deposit",
                money(deposit, curr_code),
            )
            col3.metric(
                "Balance Due",
                money(balance, curr_code),
            )

            comments = st.text_area(
                "Comments (Internal Notes)",
                placeholder="e.g. Payment received by transfer.",
            )

            special_requests = st.text_area(
                "Special Requests (Guest Needs)",
                placeholder="e.g. Early check-in, Anniversary setup.",
            )

            st.markdown("### Confirmation Details")

            hotel_conf_number = st.text_input(
                "Hotel Confirmation Number",
                placeholder="Leave blank to auto-generate (CN...)",
            )

            t_ui = TRANSLATIONS.get(
                lang_code,
                TRANSLATIONS["en"],
            )

            if payment_status == "Fully Paid":
                conf_deposit_policy = t_ui.get(
                    "fully_paid_policy",
                    "Reservation is fully paid."
                    if lang_code == "en"
                    else "La reservación está totalmente pagada.",
                )
            else:
                conf_deposit_policy = (
                    t_ui.get(
                        "first_night_policy",
                        "Reservation is guaranteed with the first night deposit, "
                        "balance to pay due check in: ",
                    )
                    + money(balance, curr_code)
                )

            st.markdown("### Deposit Policy")
            st.info(conf_deposit_policy)

            st.markdown("### Actions")
            col_act1, col_act2 = st.columns(2)

            def store_pending_confirmation_ui(action):
                conf_number = (
                    hotel_conf_number.strip()
                    if hotel_conf_number.strip()
                    else generate_confirmation_number()
                )

                st.session_state.pending_confirmation = {
                    "confirmation_number": conf_number,
                    "quotation_number": selected_quote[
                        "quotation_number"
                    ],
                    "guest_name": selected_quote["guest_name"],
                    "guest_email": selected_quote["guest_email"],
                    "arrival": selected_quote["arrival"],
                    "departure": selected_quote["departure"],
                    "nights": selected_quote["nights"],
                    "adults": selected_opt_adults,
                    "children": selected_opt_children,
                    "room_type": legacy_room_type,
                    "rate_per_night": rate_per_night,
                    "stay_total": stay_total,
                    "first_night_amount": deposit,
                    "rooms": confirmation_rooms,
                    "total_amount": grand_total,
                    "balance_due": balance,
                    "payment_status": payment_status_trans,
                    "comments": comments,
                    "special_requests": special_requests,
                    # Conservamos cada opción original para mantener
                    # los detalles de habitaciones/servicios en Supabase.
                    "additional_services": selected_options,
                    "subject": (
                        f"Booking Confirmation #{conf_number} | "
                        "Casa Dorada Los Cabos"
                    ),
                    "email_html": build_confirmation_email_html(
                        conf_number,
                        selected_quote["guest_name"],
                        selected_quote["arrival"],
                        selected_quote["departure"],
                        selected_opt_adults,
                        selected_opt_children,
                        selected_quote["nights"],
                        legacy_room_type,
                        rate_per_night,
                        stay_total,
                        deposit,
                        balance,
                        payment_status_trans,
                        special_requests,
                        conf_deposit_policy,
                        can_policy_default,
                        comb_inclusions,
                        comb_services,
                        lang_code,
                        curr_code,
                        rooms=confirmation_rooms,
                        total_amount=grand_total,
                    ),
                    "plain_text_email": build_confirmation_plain_text(
                        conf_number,
                        selected_quote["guest_name"],
                        selected_quote["arrival"],
                        selected_quote["departure"],
                        selected_opt_adults,
                        selected_opt_children,
                        selected_quote["nights"],
                        legacy_room_type,
                        rate_per_night,
                        stay_total,
                        deposit,
                        balance,
                        payment_status_trans,
                        special_requests,
                        conf_deposit_policy,
                        can_policy_default,
                        comb_inclusions,
                        comb_services,
                        lang_code,
                        curr_code,
                        rooms=confirmation_rooms,
                        total_amount=grand_total,
                    ),
                }

                st.session_state.pending_action = action

            with col_act1:
                if st.button(
                    "💾 Generate & Save Draft",
                    use_container_width=True,
                ):
                    store_pending_confirmation_ui("draft")

                    if get_gmail_service():
                        execute_pending_confirmation()
                        st.rerun()
                    else:
                        st.warning(
                            "Connect Gmail to generate confirmation."
                        )
                        st.markdown(
                            f"""
                            <a href="{get_google_login_url()}"
                               style="display:inline-block; background:#2563eb; color:#ffffff; padding:13px 22px; border-radius:9px; text-decoration:none;">
                               Connect Google
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )

                if st.session_state.get("conf_auto_draft_success"):
                    result = st.session_state.conf_auto_draft_success

                    if isinstance(result, str) and "failed" in result:
                        st.warning(result)
                    else:
                        st.success(
                            "✅ Reservation Confirmed! Draft saved "
                            f"successfully. Confirmation #{result}"
                        )
                        st.balloons()

                    st.session_state.conf_auto_draft_success = False

            with col_act2:
                if st.button(
                    "📤 Generate & Send Email",
                    use_container_width=True,
                ):
                    store_pending_confirmation_ui("send")

                    if get_gmail_service():
                        execute_pending_confirmation()
                        st.rerun()
                    else:
                        st.warning(
                            "Connect Gmail to generate confirmation."
                        )
                        st.markdown(
                            f"""
                            <a href="{get_google_login_url()}"
                               style="display:inline-block; background:#2563eb; color:#ffffff; padding:13px 22px; border-radius:9px; text-decoration:none;">
                               Connect Google
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )

                if st.session_state.get("conf_auto_send_success"):
                    result = st.session_state.conf_auto_send_success

                    if isinstance(result, str) and "failed" in result:
                        st.warning(result)
                    else:
                        st.success(
                            "✅ Reservation Confirmed! Email sent "
                            f"successfully. Confirmation #{result}"
                        )
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

        m_nights = m_calculated_nights 
        st.number_input("Nights", min_value=1, value=m_nights, step=1, disabled=True,)
        
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
    
    st.markdown(
        "### Payment & Comments"
    )

    m_comments = st.text_area(
        "Comments (Internal Notes)", 
        placeholder="e.g. Payment received by transfer.", 
        key="m_comm"
    )
    
    m_special = st.text_area(
        "Special Requests (Guest Needs)", 
        placeholder="e.g. Early check-in, Anniversary setup.", 
        key="m_spec"
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
        "### Deposit Policy"
    )

    t_ui = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])

    if m_payment_status == "Fully Paid":
        dynamic_m_dep = t_ui.get("fully_paid_policy", "Reservation is fully paid." if lang_code == "en" else "La reservación está totalmente pagada.")
    else:
        dynamic_m_dep = f"{t_ui.get('first_night_policy', 'Reservation is guaranteed with the first night deposit, balance to pay due check in: ')}{money(m_balance, curr_code)}"
            
    m_dep_pol = dynamic_m_dep
    
    st.info(m_dep_pol)

    st.markdown(
        "### Cancellation Policy"
    )

    m_can_pol = st.selectbox(
        "Select cancellation policy", 
        CANCELLATION_POLICIES, 
        key="m_cpol"
    )

    st.markdown(
        "### Email Preview & Actions"
    )

    import streamlit.components.v1 as components

    # --- INICIO DEL PREVIEW ---
    with st.expander("👀 View Email Preview", expanded=False):
        if not m_guest_name:
            st.info("☝️ Enter the guest's name to generate the preview.")
        else:
            # Usamos un número temporal si aún no han escrito uno
            preview_conf_number = m_hotel_conf_number.strip() if m_hotel_conf_number.strip() else "CN-PREVIEW"
            
            preview_html = build_confirmation_email_html(
                preview_conf_number, m_guest_name, m_arrival, m_departure, m_adults, m_children, m_nights,
                m_room_type, m_nightly_rate, m_stay_total, m_deposit, m_balance, payment_status_trans,
                m_special, m_dep_pol, m_can_pol, m_selected_inclusions, m_selected_services, lang_code, curr_code
            )
            
            components.html(preview_html, height=650, scrolling=True)
    # --- FIN DEL PREVIEW ---

    m_act1, m_act2 = st.columns(2)

    def store_manual_pending_ui(action):
        # ... (aquí sigue tu código normal de store_manual_pending_ui) ...
        conf_number = m_hotel_conf_number.strip() if m_hotel_conf_number.strip() else generate_confirmation_number()

        st.session_state.pending_confirmation = {
            "confirmation_number": conf_number,
            "quotation_number": None,
            "guest_name": m_guest_name,
            "guest_email": m_guest_email,
            "arrival": m_arrival,
            "departure": m_departure,
            "nights": m_nights,
            "adults": m_adults,
            "children": m_children,
            "room_type": m_room_type,
            "rate_per_night": m_nightly_rate,
            "stay_total": m_stay_total,
            "first_night_amount": m_deposit,
            "rooms": [{
                "room_type": m_room_type,
                "adults": int(m_adults),
                "children": int(m_children),
                "nights": int(m_nights),
                "currency": curr_code,
                "additional_services_total": round(sum(
                    get_service_price(service, curr_code)
                    for service in m_selected_services
                ), 2),
                "rate_per_night": float(m_nightly_rate),
                "stay_total": float(m_stay_total),
                "selected_inclusions": m_selected_inclusions,
                "selected_services": m_selected_services,
            }],
            "balance_due": m_balance,
            "payment_status": payment_status_trans,
            "comments": m_comments,
            "special_requests": m_special,
            "additional_services": {"source": "manual"},
            "subject": f"Booking Confirmation #{conf_number} | Casa Dorada Los Cabos",
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

# ============================================================
# WORKFLOW: ADMIN
# ============================================================

elif app_mode == "Admin":
    admin_show_dashboard()

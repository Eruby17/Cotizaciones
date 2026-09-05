import streamlit as st
import traceback
import json
import base64
import hashlib
import hmac
import secrets
import mimetypes
from datetime import date
from email.message import EmailMessage


# ============================================================
# GOOGLE
# ============================================================

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Cotizador Casa Dorada",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose"
]


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
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background: {FONDO};
        color: {BLANCO};
    }}

    section[data-testid="stSidebar"] {{
        background: {AZUL};
        border-right: 1px solid #1D3553;
    }}

    section[data-testid="stSidebar"] * {{
        color: {BLANCO};
    }}

    h1, h2, h3, h4 {{
        color: {BLANCO} !important;
    }}

    p, label {{
        color: {GRIS} !important;
    }}

    .hero {{
        background: linear-gradient(
            135deg,
            {AZUL_2},
            {AZUL_3}
        );
        padding: 28px;
        border-radius: 16px;
        border: 1px solid #1D3553;
        margin-bottom: 25px;
    }}

    .hero-title {{
        color: {BLANCO};
        font-size: 34px;
        font-weight: 800;
    }}

    .hero-subtitle {{
        color: {GRIS};
        font-size: 16px;
        margin-top: 5px;
    }}

    .card {{
        background: {CARD};
        border: 1px solid #1D3553;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
    }}

    .section-title {{
        color: {DORADO_CLARO};
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 15px;
    }}

    .price-card {{
        background: {CARD_2};
        border: 1px solid #29496C;
        border-radius: 14px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 15px;
    }}

    .price {{
        color: {DORADO_CLARO};
        font-size: 27px;
        font-weight: 800;
        margin-top: 8px;
    }}

    .connected {{
        background: rgba(66, 200, 138, 0.12);
        border: 1px solid rgba(66, 200, 138, 0.4);
        color: {VERDE};
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 15px;
    }}

    .disconnected {{
        background: rgba(229, 107, 111, 0.10);
        border: 1px solid rgba(229, 107, 111, 0.35);
        color: {ROJO};
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 15px;
    }}

    .debug {{
        background: #020711;
        border: 1px solid #263A54;
        border-radius: 10px;
        padding: 15px;
    }}

    div.stButton > button {{
        background: {DORADO};
        color: #050D18;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        min-height: 44px;
    }}

    div.stButton > button:hover {{
        background: {DORADO_CLARO};
        color: #050D18;
    }}

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stTextArea textarea {{
        background-color: {CARD_2} !important;
        color: {BLANCO} !important;
        border: 1px solid #29496C !important;
        border-radius: 8px !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: {CARD_2} !important;
        color: {BLANCO} !important;
        border-color: #29496C !important;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# GOOGLE CONFIG
# ============================================================

def get_google_client_config():

    try:

        client_id = st.secrets[
            "google_oauth"
        ][
            "client_id"
        ]

        client_secret = st.secrets[
            "google_oauth"
        ][
            "client_secret"
        ]

        redirect_uri = st.secrets[
            "google_oauth"
        ][
            "redirect_uri"
        ]

        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,

                "auth_uri":
                    "https://accounts.google.com/o/oauth2/auth",

                "token_uri":
                    "https://oauth2.googleapis.com/token",

                "redirect_uris": [
                    redirect_uri
                ]
            }
        }

    except Exception as e:

        st.error(
            "❌ ERROR LEYENDO GOOGLE OAUTH"
        )

        st.exception(e)

        st.code(
            traceback.format_exc(),
            language="text"
        )

        return None


# ============================================================
# DATOS GOOGLE
# ============================================================

def get_google_secrets():

    return {
        "client_id": st.secrets[
            "google_oauth"
        ][
            "client_id"
        ],

        "client_secret": st.secrets[
            "google_oauth"
        ][
            "client_secret"
        ],

        "redirect_uri": st.secrets[
            "google_oauth"
        ][
            "redirect_uri"
        ]
    }


# ============================================================
# BASE64 URL SAFE
# ============================================================

def b64encode_text(text):

    return base64.urlsafe_b64encode(
        text.encode("utf-8")
    ).decode("utf-8").rstrip("=")


def b64decode_text(text):

    padding = "=" * (
        4 - len(text) % 4
    )

    return base64.urlsafe_b64decode(
        (text + padding).encode("utf-8")
    ).decode("utf-8")


# ============================================================
# CREAR STATE FIRMADO
# ============================================================

def crear_oauth_state(code_verifier):

    secrets_google = get_google_secrets()

    client_secret = secrets_google[
        "client_secret"
    ]

    nonce = secrets.token_urlsafe(
        24
    )

    payload = {
        "nonce": nonce,
        "code_verifier": code_verifier
    }

    payload_json = json.dumps(
        payload,
        separators=(",", ":")
    )

    payload_encoded = b64encode_text(
        payload_json
    )

    signature = hmac.new(
        client_secret.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return (
        payload_encoded
        + "."
        + signature
    )


# ============================================================
# LEER STATE FIRMADO
# ============================================================

def leer_oauth_state(state):

    secrets_google = get_google_secrets()

    client_secret = secrets_google[
        "client_secret"
    ]

    try:

        partes = state.split(".")

        if len(partes) != 2:

            raise ValueError(
                "Formato de state inválido."
            )

        payload_encoded = partes[0]
        signature_recibida = partes[1]

        signature_esperada = hmac.new(
            client_secret.encode("utf-8"),
            payload_encoded.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            signature_recibida,
            signature_esperada
        ):

            raise ValueError(
                "La firma del state no coincide."
            )

        payload_json = b64decode_text(
            payload_encoded
        )

        payload = json.loads(
            payload_json
        )

        if "code_verifier" not in payload:

            raise ValueError(
                "No existe code_verifier en state."
            )

        return payload

    except Exception as e:

        raise ValueError(
            f"No se pudo validar el state: {e}"
        )


# ============================================================
# CREAR CODE VERIFIER
# ============================================================

def crear_code_verifier():

    return secrets.token_urlsafe(
        64
    )


# ============================================================
# CREAR CODE CHALLENGE
# ============================================================

def crear_code_challenge(
    code_verifier
):

    digest = hashlib.sha256(
        code_verifier.encode("utf-8")
    ).digest()

    return base64.urlsafe_b64encode(
        digest
    ).decode("utf-8").rstrip("=")


# ============================================================
# CREAR FLOW
# ============================================================

def crear_flow():

    config = get_google_client_config()

    if config is None:

        return None

    redirect_uri = st.secrets[
        "google_oauth"
    ][
        "redirect_uri"
    ]

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    return flow


# ============================================================
# INICIAR LOGIN GOOGLE
# ============================================================

def iniciar_google_login():

    try:

        flow = crear_flow()

        if flow is None:

            return None

        # ----------------------------------------------------
        # Generar PKCE
        # ----------------------------------------------------

        code_verifier = (
            crear_code_verifier()
        )

        code_challenge = (
            crear_code_challenge(
                code_verifier
            )
        )

        # ----------------------------------------------------
        # Crear state firmado
        # ----------------------------------------------------

        state = crear_oauth_state(
            code_verifier
        )

        # ----------------------------------------------------
        # Construir URL
        # ----------------------------------------------------

        authorization_url, _ = (
            flow.authorization_url(

                access_type="offline",

                include_granted_scopes="true",

                prompt="consent",

                state=state,

                code_challenge=
                    code_challenge,

                code_challenge_method=
                    "S256"
            )
        )

        # Guardamos URL únicamente para
        # mostrarla en esta sesión.
        #
        # IMPORTANTE:
        # El OAuth ya NO depende de guardar
        # el Flow en session_state.
        st.session_state[
            "oauth_url"
        ] = authorization_url

        return authorization_url

    except Exception as e:

        st.error(
            "❌ ERROR INICIANDO LOGIN CON GOOGLE"
        )

        st.exception(e)

        st.code(
            traceback.format_exc(),
            language="text"
        )

        return None


# ============================================================
# PROCESAR CALLBACK
# ============================================================

def procesar_callback_google():

    try:

        query_params = dict(
            st.query_params
        )

    except Exception:

        query_params = {}

    # --------------------------------------------------------
    # Mostrar diagnóstico
    # --------------------------------------------------------

    with st.expander(
        "🔎 Diagnóstico de Google",
        expanded=True
    ):

        debug_params = {}

        for key, value in query_params.items():

            # NO mostrar tokens sensibles
            if key in [
                "access_token",
                "refresh_token"
            ]:

                debug_params[key] = (
                    "[OCULTO]"
                )

            else:

                debug_params[key] = value

        st.code(
            json.dumps(
                debug_params,
                indent=2,
                ensure_ascii=False
            ),
            language="json"
        )

    # --------------------------------------------------------
    # ERROR DE GOOGLE
    # --------------------------------------------------------

    google_error = st.query_params.get(
        "error"
    )

    if google_error:

        st.error(
            f"❌ GOOGLE DEVOLVIÓ UN ERROR: "
            f"{google_error}"
        )

        description = (
            st.query_params.get(
                "error_description"
            )
        )

        if description:

            st.error(
                f"Descripción: {description}"
            )

        return None

    # --------------------------------------------------------
    # CODE
    # --------------------------------------------------------

    code = st.query_params.get(
        "code"
    )

    if not code:

        return None

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    state = st.query_params.get(
        "state"
    )

    if not state:

        st.error(
            "❌ Google no devolvió el parámetro state."
        )

        return None

    # --------------------------------------------------------
    # RECUPERAR CODE VERIFIER DESDE STATE
    # --------------------------------------------------------

    try:

        payload = leer_oauth_state(
            state
        )

        code_verifier = payload[
            "code_verifier"
        ]

    except Exception as e:

        st.error(
            "❌ NO SE PUDO VALIDAR EL STATE"
        )

        st.exception(e)

        st.code(
            traceback.format_exc(),
            language="text"
        )

        return None

    # --------------------------------------------------------
    # DEBUG PKCE
    # --------------------------------------------------------

    with st.expander(
        "🔎 Diagnóstico PKCE",
        expanded=True
    ):

        st.code(
            json.dumps(
                {
                    "code_received": True,

                    "state_received": True,

                    "code_verifier_recovered":
                        bool(
                            code_verifier
                        ),

                    "code_verifier_length":
                        len(
                            code_verifier
                        ),

                    "redirect_uri":
                        st.secrets[
                            "google_oauth"
                        ][
                            "redirect_uri"
                        ],

                    "scope":
                        st.query_params.get(
                            "scope"
                        )
                },
                indent=2,
                ensure_ascii=False
            ),
            language="json"
        )

    # --------------------------------------------------------
    # CREAR NUEVO FLOW
    # --------------------------------------------------------

    try:

        flow = crear_flow()

        if flow is None:

            return None

        # ----------------------------------------------------
        # INTERCAMBIO DEL CODE
        # ----------------------------------------------------

        st.info(
            "🔄 Google autorizó la aplicación. "
            "Obteniendo credenciales..."
        )

        flow.fetch_token(
            code=code,
            code_verifier=code_verifier
        )

        credentials = (
            flow.credentials
        )

        # ----------------------------------------------------
        # VALIDAR
        # ----------------------------------------------------

        credential_debug = {

            "valid":
                credentials.valid,

            "expired":
                credentials.expired,

            "has_token":
                bool(
                    credentials.token
                ),

            "has_refresh_token":
                bool(
                    credentials.refresh_token
                ),

            "scopes":
                credentials.scopes
        }

        with st.expander(
            "🔎 Diagnóstico Credentials",
            expanded=True
        ):

            st.code(
                json.dumps(
                    credential_debug,
                    indent=2,
                    ensure_ascii=False
                ),
                language="json"
            )

        # ----------------------------------------------------
        # GUARDAR CREDENTIALS
        # ----------------------------------------------------

        st.session_state[
            "google_credentials"
        ] = credentials

        st.session_state.pop(
            "oauth_url",
            None
        )

        # ----------------------------------------------------
        # LIMPIAR URL
        # ----------------------------------------------------

        try:

            st.query_params.clear()

        except Exception:

            pass

        st.success(
            "✅ Google conectado correctamente."
        )

        # ----------------------------------------------------
        # RECARGAR
        # ----------------------------------------------------

        st.rerun()

        return credentials

    except Exception as e:

        st.error(
            "❌❌❌ ERROR COMPLETO DE GOOGLE OAUTH ❌❌❌"
        )

        st.exception(e)

        st.markdown(
            "### Traceback completo"
        )

        st.code(
            traceback.format_exc(),
            language="text"
        )

        st.markdown(
            "### Diagnóstico del intercambio"
        )

        try:

            st.code(
                json.dumps(
                    {
                        "code_received":
                            bool(code),

                        "state_received":
                            bool(state),

                        "code_verifier_recovered":
                            bool(
                                code_verifier
                            ),

                        "code_verifier_length":
                            len(
                                code_verifier
                            ),

                        "redirect_uri":
                            st.secrets[
                                "google_oauth"
                            ][
                                "redirect_uri"
                            ],

                        "scope":
                            st.query_params.get(
                                "scope"
                            )
                    },
                    indent=2,
                    ensure_ascii=False
                ),
                language="json"
            )

        except Exception as debug_error:

            st.exception(
                debug_error
            )

        return None


# ============================================================
# OBTENER CREDENTIALS
# ============================================================

def get_credentials():

    try:

        # ----------------------------------------------------
        # Credentials existentes
        # ----------------------------------------------------

        credentials = (
            st.session_state.get(
                "google_credentials"
            )
        )

        if credentials:

            if credentials.valid:

                return credentials

            # ------------------------------------------------
            # REFRESH
            # ------------------------------------------------

            if (
                credentials.expired
                and credentials.refresh_token
            ):

                try:

                    credentials.refresh(
                        Request()
                    )

                    st.session_state[
                        "google_credentials"
                    ] = credentials

                    return credentials

                except Exception as e:

                    st.error(
                        "❌ No se pudo renovar "
                        "la sesión de Google."
                    )

                    st.exception(e)

                    st.code(
                        traceback.format_exc(),
                        language="text"
                    )

                    st.session_state.pop(
                        "google_credentials",
                        None
                    )

        # ----------------------------------------------------
        # CALLBACK
        # ----------------------------------------------------

        if st.query_params.get(
            "code"
        ):

            return procesar_callback_google()

        return None

    except Exception as e:

        st.error(
            "❌ ERROR OBTENIENDO CREDENTIALS"
        )

        st.exception(e)

        st.code(
            traceback.format_exc(),
            language="text"
        )

        return None


# ============================================================
# GMAIL SERVICE
# ============================================================

def get_gmail_service():

    try:

        credentials = (
            get_credentials()
        )

        if not credentials:

            return None

        service = build(
            "gmail",
            "v1",
            credentials=credentials
        )

        return service

    except Exception as e:

        st.error(
            "❌ ERROR CREANDO SERVICIO GMAIL"
        )

        st.exception(e)

        st.code(
            traceback.format_exc(),
            language="text"
        )

        return None


# ============================================================
# MOSTRAR LOGIN
# ============================================================

def mostrar_login_google():

    credentials = (
        get_credentials()
    )

    # --------------------------------------------------------
    # CONECTADO
    # --------------------------------------------------------

    if credentials:

        try:

            service = (
                get_gmail_service()
            )

            if service:

                profile = (
                    service
                    .users()
                    .getProfile(
                        userId="me"
                    )
                    .execute()
                )

                email_google = (
                    profile.get(
                        "emailAddress",
                        "Correo desconocido"
                    )
                )

                st.markdown(
                    f"""
                    <div class="connected">
                        🟢 <b>Google conectado</b><br>
                        {email_google}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                return True

        except Exception as e:

            st.error(
                "❌ Google está conectado, "
                "pero no se pudo acceder a Gmail."
            )

            st.exception(e)

            st.code(
                traceback.format_exc(),
                language="text"
            )

            return False

    # --------------------------------------------------------
    # NO CONECTADO
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="disconnected">
            🔴 <b>Google no está conectado</b><br>
            Conecta tu cuenta para guardar
            borradores y enviar cotizaciones
            desde tu Gmail.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    auth_url = (
        st.session_state.get(
            "oauth_url"
        )
    )

    if not auth_url:

        auth_url = (
            iniciar_google_login()
        )

    if auth_url:

        st.markdown(
            f"""
            <a href="{auth_url}"
               target="_self"
               style="
                   display:block;
                   text-align:center;
                   padding:13px 18px;
                   background:{DORADO};
                   color:#050D18;
                   text-decoration:none;
                   border-radius:8px;
                   font-weight:700;
                   font-size:15px;
                   margin-bottom:10px;
               ">
               🔐 Iniciar sesión con Google
            </a>
            """,
            unsafe_allow_html=True
        )

    return False


# ============================================================
# CREAR EMAIL
# ============================================================

def crear_email(
    destinatario,
    asunto,
    html,
    attachments=None
):

    message = EmailMessage()

    message["To"] = destinatario
    message["Subject"] = asunto

    message.set_content(
        "Please view this email in HTML format."
    )

    message.add_alternative(
        html,
        subtype="html"
    )

    if attachments:

        for archivo in attachments:

            try:

                archivo.seek(0)

                archivo_bytes = (
                    archivo.read()
                )

                mime_type, _ = (
                    mimetypes.guess_type(
                        archivo.name
                    )
                )

                if mime_type:

                    maintype, subtype = (
                        mime_type.split(
                            "/",
                            1
                        )
                    )

                else:

                    maintype = "application"
                    subtype = "octet-stream"

                message.add_attachment(
                    archivo_bytes,
                    maintype=maintype,
                    subtype=subtype,
                    filename=archivo.name
                )

            except Exception as e:

                st.warning(
                    f"No se pudo adjuntar "
                    f"{archivo.name}: {e}"
                )

    return message


# ============================================================
# RAW EMAIL
# ============================================================

def email_to_raw(message):

    return base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()


# ============================================================
# GUARDAR BORRADOR
# ============================================================

def guardar_borrador_gmail(
    destinatario,
    asunto,
    html,
    attachments=None
):

    try:

        service = (
            get_gmail_service()
        )

        if not service:

            st.error(
                "❌ No hay conexión con Gmail."
            )

            return False

        profile = (
            service
            .users()
            .getProfile(
                userId="me"
            )
            .execute()
        )

        email_account = (
            profile.get(
                "emailAddress"
            )
        )

        message = crear_email(
            destinatario,
            asunto,
            html,
            attachments
        )

        raw_message = (
            email_to_raw(
                message
            )
        )

        result = (
            service
            .users()
            .drafts()
            .create(
                userId="me",
                body={
                    "message": {
                        "raw":
                            raw_message
                    }
                }
            )
            .execute()
        )

        st.success(
            f"✅ Borrador guardado en "
            f"{email_account}"
        )

        return True

    except Exception as e:

        st.error(
            "❌ ERROR GUARDANDO BORRADOR"
        )

        st.exception(e)

        st.code(
            traceback.format_exc(),
            language="text"
        )

        return False


# ============================================================
# ENVIAR EMAIL
# ============================================================

def enviar_email_gmail(
    destinatario,
    asunto,
    html,
    attachments=None
):

    try:

        service = (
            get_gmail_service()
        )

        if not service:

            st.error(
                "❌ No hay conexión con Gmail."
            )

            return False

        profile = (
            service
            .users()
            .getProfile(
                userId="me"
            )
            .execute()
        )

        email_account = (
            profile.get(
                "emailAddress"
            )
        )

        message = crear_email(
            destinatario,
            asunto,
            html,
            attachments
        )

        raw_message = (
            email_to_raw(
                message
            )
        )

        result = (
            service
            .users()
            .messages()
            .send(
                userId="me",
                body={
                    "raw":
                        raw_message
                }
            )
            .execute()
        )

        st.success(
            f"✅ Correo enviado desde "
            f"{email_account}"
        )

        return True

    except Exception as e:

        st.error(
            "❌ ERROR ENVIANDO CORREO"
        )

        st.exception(e)

        st.code(
            traceback.format_exc(),
            language="text"
        )

        return False


# ============================================================
# FECHA ESPAÑOL
# ============================================================

def format_date_es(fecha):

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
        "diciembre"
    ]

    return (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )


# ============================================================
# GENERAR HTML
# ============================================================

def generar_html_email(
    nombre,
    checkin,
    checkout,
    adultos,
    menores,
    opciones,
    transporte,
    mensaje
):

    noches = (
        checkout - checkin
    ).days

    opciones_html = ""

    for opcion in opciones:

        if not opcion["activa"]:
            continue

        suite = opcion[
            "suite"
        ]

        plan = opcion[
            "plan"
        ]

        tarifa = opcion[
            "tarifa"
        ]

        total = (
            tarifa * noches
        )

        opciones_html += f"""
        <div style="
            border:1px solid #dddddd;
            border-radius:12px;
            padding:20px;
            margin:15px 0;
            background:#ffffff;
        ">

            <div style="
                font-size:21px;
                font-weight:bold;
                color:#071A2F;
            ">
                {suite}
            </div>

            <div style="
                color:#666666;
                margin-top:6px;
            ">
                {plan}
            </div>

            <div style="
                color:#C9A227;
                font-size:26px;
                font-weight:bold;
                margin-top:12px;
            ">
                ${tarifa:,.2f} USD
            </div>

            <div style="
                color:#666666;
                margin-top:3px;
            ">
                per night
            </div>

            <div style="
                margin-top:12px;
                border-top:1px solid #eeeeee;
                padding-top:12px;
                color:#444444;
            ">
                Total for {noches} nights:
                <strong>
                    ${total:,.2f} USD
                </strong>
            </div>

        </div>
        """

    transporte_html = ""

    if transporte > 0:

        transporte_html = f"""
        <div style="
            margin-top:20px;
            padding:16px;
            background:#f5f5f5;
            border-radius:10px;
        ">

            <strong>
                Airport Transportation
            </strong>

            <br><br>

            Roundtrip transportation:
            ${transporte:,.2f} USD

        </div>
        """

    mensaje_html = ""

    if mensaje.strip():

        mensaje_html = f"""
        <div style="
            margin:20px 0;
            padding:15px;
            background:#f8f8f8;
            border-left:4px solid #C9A227;
        ">
            {mensaje}
        </div>
        """

    menores_html = ""

    if menores > 0:

        menores_html = (
            f" and {menores} children"
        )

    return f"""
    <!DOCTYPE html>

    <html>

    <body style="
        margin:0;
        padding:0;
        background:#eeeeee;
        font-family:Arial,Helvetica,sans-serif;
        color:#333333;
    ">

    <div style="
        max-width:700px;
        margin:auto;
        background:#ffffff;
    ">

        <div style="
            background:#071A2F;
            padding:30px;
            text-align:center;
        ">

            <div style="
                color:#C9A227;
                font-size:29px;
                font-weight:bold;
            ">
                CASA DORADA
            </div>

            <div style="
                color:#ffffff;
                font-size:14px;
                margin-top:5px;
            ">
                Los Cabos Resort & Spa
            </div>

        </div>


        <div style="
            padding:30px;
        ">

            <h2 style="
                color:#071A2F;
            ">
                Dear {nombre},
            </h2>

            {mensaje_html}

            <p>
                Thank you for considering
                Casa Dorada Los Cabos Resort & Spa
                for your upcoming stay.
            </p>


            <div style="
                background:#071A2F;
                color:#ffffff;
                padding:20px;
                border-radius:10px;
                margin:20px 0;
            ">

                <div style="
                    color:#E0C15A;
                    font-size:18px;
                    font-weight:bold;
                    margin-bottom:12px;
                ">
                    Stay Details
                </div>

                <div>
                    <strong>Check in:</strong>
                    {format_date_es(checkin)}
                </div>

                <div style="
                    margin-top:6px;
                ">
                    <strong>Check out:</strong>
                    {format_date_es(checkout)}
                </div>

                <div style="
                    margin-top:6px;
                ">
                    <strong>Guests:</strong>
                    {adultos} adults{menores_html}
                </div>

            </div>


            <h2 style="
                color:#071A2F;
            ">
                Accommodation Options
            </h2>

            {opciones_html}

            {transporte_html}


            <div style="
                margin-top:25px;
                padding:20px;
                background:#f7f7f7;
                border-radius:10px;
            ">

                <h3 style="
                    color:#071A2F;
                    margin-top:0;
                ">
                    Casa Dorada Benefits
                </h3>

                <ul>
                    <li>
                        Prime location in Cabo San Lucas
                    </li>

                    <li>
                        Access to Medano Beach
                    </li>

                    <li>
                        Spacious suite accommodations
                    </li>

                    <li>
                        Resort amenities and services
                    </li>

                    <li>
                        Personalized guest service
                    </li>
                </ul>

            </div>


            <div style="
                margin-top:25px;
                padding:20px;
                border:1px solid #dddddd;
                border-radius:10px;
            ">

                <h3 style="
                    color:#071A2F;
                    margin-top:0;
                ">
                    Reservation Policy
                </h3>

                <p>
                    Reservation is guaranteed with
                    first night deposit.
                </p>

                <p>
                    The remaining balance is due
                    45 days prior to arrival.
                </p>

            </div>


            <p style="
                margin-top:30px;
            ">
                We look forward to welcoming you
                to Casa Dorada Los Cabos.
            </p>

            <p>
                Best regards,<br>
                <strong>Reservations Team</strong><br>
                Casa Dorada Los Cabos Resort & Spa
            </p>

        </div>


        <div style="
            background:#071A2F;
            color:#aaaaaa;
            text-align:center;
            padding:20px;
            font-size:12px;
        ">

            Casa Dorada Los Cabos Resort & Spa<br>
            Cabo San Lucas, Mexico

        </div>

    </div>

    </body>

    </html>
    """


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-title">
            🏨 Cotizador Casa Dorada
        </div>

        <div class="hero-subtitle">
            Cotizaciones profesionales y gestión
            directa desde Gmail
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
        "## 📧 Gmail"
    )

    google_conectado = (
        mostrar_login_google()
    )

    st.divider()

    st.markdown(
        "## ⚙️ Configuración"
    )

    moneda = st.selectbox(
        "Moneda",
        [
            "USD",
            "MXN"
        ]
    )

    tipo_cambio = st.number_input(
        "Tipo de cambio",
        min_value=1.0,
        value=18.50,
        step=0.10
    )


# ============================================================
# HUÉSPED
# ============================================================

st.markdown(
    """
    <div class="card">
        <div class="section-title">
            👤 Información del huésped
        </div>
    """,
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    nombre = st.text_input(
        "Nombre del huésped",
        placeholder="John Smith"
    )

with col2:

    email = st.text_input(
        "Correo electrónico",
        placeholder="guest@email.com"
    )

col3, col4 = st.columns(2)

with col3:

    checkin = st.date_input(
        "Check in",
        value=date.today()
    )

with col4:

    checkout = st.date_input(
        "Check out",
        value=date.today()
    )

numero_noches = max(
    0,
    (checkout - checkin).days
)

st.info(
    f"🌙 Noches: **{numero_noches}**"
)

col5, col6 = st.columns(2)

with col5:

    adultos = st.number_input(
        "Adultos",
        min_value=1,
        value=2,
        step=1
    )

with col6:

    menores = st.number_input(
        "Menores",
        min_value=0,
        value=0,
        step=1
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# OPCIONES
# ============================================================

st.markdown(
    """
    <div class="card">
        <div class="section-title">
            🛏️ Opciones de alojamiento
        </div>
    """,
    unsafe_allow_html=True
)

opciones = []

suite_names = [
    "Junior Suite",
    "One Bedroom Suite",
    "One Bedroom Plus w/ Jacuzzi",
    "Executive Suite",
    "Two Bedroom Suite",
    "One Bedroom Penthouse"
]

planes = [
    "European Plan",
    "All Inclusive"
]

for i in range(1, 4):

    st.markdown(
        f"### Opción {i}"
    )

    activa = st.checkbox(
        f"Incluir opción {i}",
        value=(i == 1),
        key=f"activa_{i}"
    )

    if activa:

        col1, col2, col3 = st.columns(
            [1.4, 1, 1]
        )

        with col1:

            suite = st.selectbox(
                "Suite",
                suite_names,
                key=f"suite_{i}"
            )

        with col2:

            plan = st.selectbox(
                "Plan",
                planes,
                key=f"plan_{i}"
            )

        with col3:

            tarifa = st.number_input(
                "Tarifa por noche USD",
                min_value=0.0,
                value=221.0,
                step=1.0,
                key=f"tarifa_{i}"
            )

        total = (
            tarifa *
            numero_noches
        )

        st.markdown(
            f"""
            <div class="price-card">

                <div>
                    <strong>
                        {suite}
                    </strong>
                </div>

                <div style="
                    color:#AAB6C5;
                    margin-top:5px;
                ">
                    {plan}
                </div>

                <div class="price">
                    ${tarifa:,.2f} USD
                </div>

                <div style="
                    color:#AAB6C5;
                ">
                    Total:
                    <strong>
                        ${total:,.2f} USD
                    </strong>
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        suite = ""
        plan = ""
        tarifa = 0.0

    opciones.append(
        {
            "activa": activa,
            "suite": suite,
            "plan": plan,
            "tarifa": tarifa
        }
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# TRANSPORTACIÓN
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="section-title">
            🚐 Transportation
        </div>
    """,
    unsafe_allow_html=True
)

incluir_transporte = st.checkbox(
    "Incluir transportation",
    value=False
)

transporte = 0.0

if incluir_transporte:

    transporte = st.number_input(
        "Airport roundtrip transportation USD",
        min_value=0.0,
        value=267.0,
        step=1.0
    )

    st.caption(
        "Transportation must be arranged "
        "at least 48 hours prior to service."
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# ARCHIVOS
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="section-title">
            📎 Archivos adjuntos
        </div>
    """,
    unsafe_allow_html=True
)

attachments = st.file_uploader(
    "Adjuntar archivos",
    accept_multiple_files=True
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# MENSAJE
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="section-title">
            ✍️ Mensaje personalizado
        </div>
    """,
    unsafe_allow_html=True
)

mensaje = st.text_area(
    "Mensaje",
    placeholder=(
        "Thank you for considering "
        "Casa Dorada for your upcoming stay..."
    ),
    height=150
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# ASUNTO
# ============================================================

asunto = (
    "Casa Dorada Los Cabos "
    "Accommodation Proposal"
)


# ============================================================
# HTML EMAIL
# ============================================================

html_email = generar_html_email(
    nombre=nombre or "Guest",
    checkin=checkin,
    checkout=checkout,
    adultos=adultos,
    menores=menores,
    opciones=opciones,
    transporte=transporte,
    mensaje=mensaje
)


# ============================================================
# PREVIEW
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="section-title">
            👁️ Vista previa del correo
        </div>
    """,
    unsafe_allow_html=True
)

st.components.v1.html(
    html_email,
    height=900,
    scrolling=True
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# VALIDACIÓN
# ============================================================

def validar_cotizacion():

    errores = []

    if not nombre.strip():

        errores.append(
            "Falta el nombre del huésped."
        )

    if not email.strip():

        errores.append(
            "Falta el correo electrónico."
        )

    if "@" not in email:

        errores.append(
            "El correo electrónico no parece válido."
        )

    if checkout <= checkin:

        errores.append(
            "El check out debe ser posterior "
            "al check in."
        )

    if not any(
        opcion["activa"]
        for opcion in opciones
    ):

        errores.append(
            "Debes seleccionar al menos "
            "una opción."
        )

    return errores


# ============================================================
# BOTONES
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="section-title">
            📤 Acciones
        </div>
    """,
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    guardar = st.button(
        "💾 Guardar en borradores",
        use_container_width=True
    )

with col2:

    enviar = st.button(
        "📤 Enviar correo",
        use_container_width=True
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# GUARDAR
# ============================================================

if guardar:

    errores = validar_cotizacion()

    if errores:

        for error in errores:

            st.error(
                f"❌ {error}"
            )

    elif not google_conectado:

        st.error(
            "❌ Primero debes iniciar sesión con Google."
        )

    else:

        guardar_borrador_gmail(
            destinatario=email,
            asunto=asunto,
            html=html_email,
            attachments=attachments
        )


# ============================================================
# ENVIAR
# ============================================================

if enviar:

    errores = validar_cotizacion()

    if errores:

        for error in errores:

            st.error(
                f"❌ {error}"
            )

    elif not google_conectado:

        st.error(
            "❌ Primero debes iniciar sesión con Google."
        )

    else:

        enviar_email_gmail(
            destinatario=email,
            asunto=asunto,
            html=html_email,
            attachments=attachments
        )


# ============================================================
# DIAGNÓSTICO
# ============================================================

with st.expander(
    "🛠️ Diagnóstico técnico",
    expanded=False
):

    st.markdown(
        "### Estado de la aplicación"
    )

    diagnostico = {

        "google_credentials":
            "google_credentials"
            in st.session_state,

        "oauth_url":
            "oauth_url"
            in st.session_state,

        "query_params":
            dict(st.query_params),

        "session_keys":
            list(
                st.session_state.keys()
            )
    }

    st.code(
        json.dumps(
            diagnostico,
            indent=2,
            ensure_ascii=False
        ),
        language="json"
    )

    # --------------------------------------------------------
    # CREDENTIALS
    # --------------------------------------------------------

    credentials = (
        st.session_state.get(
            "google_credentials"
        )
    )

    if credentials:

        st.markdown(
            "### Estado de Gmail"
        )

        credential_info = {

            "valid":
                credentials.valid,

            "expired":
                credentials.expired,

            "has_token":
                bool(
                    credentials.token
                ),

            "has_refresh_token":
                bool(
                    credentials.refresh_token
                ),

            "scopes":
                credentials.scopes
        }

        st.code(
            json.dumps(
                credential_info,
                indent=2,
                ensure_ascii=False
            ),
            language="json"
        )

    # --------------------------------------------------------
    # CONFIG
    # --------------------------------------------------------

    st.markdown(
        "### Configuración Google"
    )

    try:

        google_config = (
            get_google_secrets()
        )

        # Nunca mostramos el secret
        google_debug = {

            "client_id_present":
                bool(
                    google_config[
                        "client_id"
                    ]
                ),

            "client_secret_present":
                bool(
                    google_config[
                        "client_secret"
                    ]
                ),

            "redirect_uri":
                google_config[
                    "redirect_uri"
                ],

            "scopes":
                SCOPES
        }

        st.code(
            json.dumps(
                google_debug,
                indent=2,
                ensure_ascii=False
            ),
            language="json"
        )

    except Exception as e:

        st.error(
            "❌ Error leyendo configuración"
        )

        st.exception(e)

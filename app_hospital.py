import streamlit as st
import datetime
import time
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
import smtplib
from email.mime.text import MIMEText
import re
import base64
import urllib.parse
import json
import io
import tempfile

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx2txt
except ImportError:
    docx2txt = None

try:
    import fitz
except ImportError:
    fitz = None

# ──────────────────────────────────────────
# CONFIGURAÇÕES
# ──────────────────────────────────────────
EMAIL_CONTA     = "rh@holhosvaledoaco.com.br"
SENHA_CONTA     = "20rhhova18"
IMAP_SERVER     = "email-ssl.com.br"
SMTP_SERVER     = "email-ssl.com.br"
SMTP_PORT       = 465
ENDERECO_HOVA   = "Rua Ponte Nova, 185 - Centro, Ipatinga/MG"
ARQUIVO_MEMORIA = "memoria_rh_hova.json"

PALAVRAS_CV = [
    "curriculo", "currículo", "curriculum", "cv ", " cv", "vaga", "candidato",
    "candidatura", "emprego", "seleção", "selecao", "oportunidade",
    "recepcionista", "enfermagem", "faturamento", "administrativo", "aprendiz"
]

MESES_NOMES = {
    1:"Janeiro", 2:"Fevereiro", 3:"Marco", 4:"Abril",
    5:"Maio",    6:"Junho",     7:"Julho", 8:"Agosto",
    9:"Setembro",10:"Outubro", 11:"Novembro", 12:"Dezembro"
}

# ──────────────────────────────────────────
# PÁGINA
# ──────────────────────────────────────────
st.set_page_config(
    page_title="HOVA | Seleção de Talentos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Forçar sidebar sempre aberta via JavaScript ──
st.markdown("""
<script>
(function forcarSidebar() {
    function abrirSidebar() {
        // Botão de reabrir quando está colapsada
        var btnReabrir = document.querySelector(
            'button[data-testid="collapsedControl"],' +
            'button[aria-label="Open sidebar"],' +
            'button[aria-label="Abrir barra lateral"],' +
            '[data-testid="stSidebarCollapseButton"]'
        );
        if (btnReabrir) { btnReabrir.click(); }
        
        // Esconder botão de fechar dentro da sidebar
        var btnsFechar = document.querySelectorAll(
            'section[data-testid="stSidebar"] button,' +
            'button[data-testid="stSidebarNavCollapseButton"]'
        );
        btnsFechar.forEach(function(b) {
            var label = (b.getAttribute("aria-label") || "").toLowerCase();
            if (label.includes("close") || label.includes("fechar") || label.includes("collapse")) {
                b.style.display = "none";
            }
        });
    }
    // Rodar imediatamente e a cada 500ms para garantir
    setTimeout(abrirSidebar, 100);
    setTimeout(abrirSidebar, 500);
    setTimeout(abrirSidebar, 1500);
    setInterval(abrirSidebar, 3000);
})();
</script>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# CSS — design moderno, verde petróleo + branco
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset ── */
#MainMenu {visibility:hidden;}
footer    {visibility:hidden;}
header    {visibility:hidden;}

/* ── Base ── */
html, body, .stApp, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif !important;
}
.stApp { background: #EAECEF; }

/* ═══════════════════════════════════════
   SIDEBAR — verde petróleo escuro, sempre visível
═══════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: #003329 !important;
    border-right: none !important;
    min-width: 240px !important;
    max-width: 280px !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* Esconder o botão de fechar dentro da sidebar */
section[data-testid="stSidebar"] button[aria-label*="Close"],
section[data-testid="stSidebar"] button[aria-label*="close"],
section[data-testid="stSidebar"] button[aria-label*="Fechar"],
section[data-testid="stSidebar"] button[aria-label*="Collapse"],
section[data-testid="stSidebar"] button[aria-label*="collapse"],
[data-testid="stSidebarNavCollapseButton"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Botão de reabrir (fora da sidebar, quando colapsada) — mantemos visível */
/* mas forçamos o estado via JS */

/* Garantir que a sidebar nunca some */
section[data-testid="stSidebar"][aria-expanded="false"] {
    transform: none !important;
    visibility: visible !important;
    display: block !important;
    position: relative !important;
    width: 240px !important;
    min-width: 240px !important;
}

/* Todos os textos da sidebar — branco */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] .stMarkdown {
    color: rgba(255,255,255,0.85) !important;
}
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption { color: rgba(255,255,255,0.45) !important; }

/* ── Radio buttons na sidebar — FIX VERMELHO ── */
section[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
section[data-testid="stSidebar"] .stRadio label {
    background: transparent !important;
    border-radius: 6px !important;
    padding: 8px 10px !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
    color: rgba(255,255,255,0.75) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #FFFFFF !important;
}
/* O círculo do radio — forçar verde petróleo */
section[data-testid="stSidebar"] input[type="radio"] {
    accent-color: #26A69A !important;
}
/* Label selecionado */
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked),
section[data-testid="stSidebar"] input[type="radio"]:checked + div {
    color: #FFFFFF !important;
}
/* Workaround direto para o ponto vermelho do radio */
section[data-testid="stSidebar"] [data-baseweb="radio"] [data-checked="true"] div,
section[data-testid="stSidebar"] [data-baseweb="radio"] div[role="radio"][aria-checked="true"] {
    border-color: #26A69A !important;
    background-color: #26A69A !important;
}
section[data-testid="stSidebar"] [data-baseweb="radio"] div[role="radio"] {
    border-color: rgba(255,255,255,0.3) !important;
    background-color: transparent !important;
}

/* ── Select/Slider na sidebar ── */
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stSelectbox select {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #FFFFFF !important;
    border-radius: 7px !important;
}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #26A69A !important;
    border-color: #26A69A !important;
}
section[data-testid="stSidebar"] .stSlider div[data-testid="stThumbValue"] {
    color: #FFFFFF !important;
}

/* ── Input na sidebar ── */
section[data-testid="stSidebar"] input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #FFFFFF !important;
    border-radius: 7px !important;
}
section[data-testid="stSidebar"] input::placeholder {
    color: rgba(255,255,255,0.35) !important;
}
section[data-testid="stSidebar"] input:focus {
    border-color: #26A69A !important;
    box-shadow: 0 0 0 2px rgba(38,166,154,0.25) !important;
}

/* ── Divisor na sidebar ── */
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
}

/* ── Botões na sidebar ── */
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    background: rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.8) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    height: 40px !important;
    font-size: 11px !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: rgba(255,255,255,0.15) !important;
    color: #FFFFFF !important;
    transform: none !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
    background: #26A69A !important;
    color: #FFFFFF !important;
    border: none !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"]:hover {
    background: #00897B !important;
}

/* ═══════════════════════════════════════
   ANIMAÇÕES
═══════════════════════════════════════ */
@keyframes fadeUp {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes scaleIn {
    from { opacity:0; transform:scale(0.97); }
    to   { opacity:1; transform:scale(1); }
}

/* ═══════════════════════════════════════
   HERO CARD — maior, mais impactante
═══════════════════════════════════════ */
.hero-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 44px 52px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    border: 1px solid #E2E6EA;
    animation: scaleIn 0.4s ease forwards;
    position: relative;
    overflow: hidden;
}
/* Linha decorativa lateral verde */
.hero-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 5px;
    background: linear-gradient(180deg, #004D40, #26A69A);
    border-radius: 20px 0 0 20px;
}
.hero-marca {
    font-size: 11px;
    font-weight: 600;
    color: #26A69A;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.hero-titulo {
    font-size: 52px;
    font-weight: 900;
    color: #0D1B2A;
    letter-spacing: -2px;
    line-height: 0.95;
    text-transform: uppercase;
}
.hero-titulo span {
    color: #004D40;
    display: block;
}
.hero-sub {
    font-size: 11px;
    color: #9AA5B4;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-top: 12px;
    font-weight: 500;
}
/* Stats — mais elegantes */
.hero-stats { display:flex; gap:10px; }
.stat-box {
    background: #F5F7FA;
    border: 1px solid #E2E6EA;
    border-radius: 14px;
    padding: 18px 24px;
    text-align: center;
    min-width: 88px;
    transition: transform 0.2s;
}
.stat-box:hover { transform: translateY(-2px); }
.stat-box .n {
    font-size: 32px;
    font-weight: 900;
    color: #004D40;
    line-height: 1;
    display: block;
    letter-spacing: -1px;
}
.stat-box .l {
    font-size: 9px;
    color: #9AA5B4;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 6px;
    display: block;
    font-weight: 600;
}

/* ═══════════════════════════════════════
   BOTÕES PRINCIPAIS — verde petróleo
═══════════════════════════════════════ */
div[data-testid="stButton"] button {
    height: 48px !important;
    border-radius: 9px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    transition: all 0.18s ease !important;
    border: none !important;
    cursor: pointer !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stButton"] button[kind="primary"] {
    background: #004D40 !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 10px rgba(0,77,64,0.25) !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background: #003329 !important;
    box-shadow: 0 5px 18px rgba(0,77,64,0.35) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"] button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #004D40 !important;
    border: 1.5px solid #B2DFDB !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #F0FAF8 !important;
    border-color: #004D40 !important;
    color: #003329 !important;
}
div[data-testid="stButton"] button[kind="secondary"]:focus {
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(0,77,64,0.12) !important;
}

/* ═══════════════════════════════════════
   ABAS
═══════════════════════════════════════ */
div[data-testid="stTabs"] {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 0 16px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    margin-bottom: 22px;
    border: 1px solid #E2E6EA;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    font-size: 10.5px !important;
    font-weight: 700 !important;
    padding: 16px 13px !important;
    color: #9AA5B4 !important;
    border-bottom: 2.5px solid transparent !important;
    background: transparent !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #004D40 !important;
    border-bottom: 2.5px solid #004D40 !important;
}

/* ═══════════════════════════════════════
   CARD CANDIDATO
═══════════════════════════════════════ */
.card-cand {
    background: #FFFFFF;
    border: 1px solid #E2E6EA;
    border-radius: 20px;
    padding: 48px 56px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    animation: fadeUp 0.3s ease forwards;
    text-align: center;
}
.cand-nome {
    font-size: 28px;
    font-weight: 800;
    color: #0D1B2A;
    text-transform: uppercase;
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin-bottom: 8px;
}
.cand-info { font-size: 13px; color: #9AA5B4; margin-bottom: 18px; line-height: 1.6; }

/* ═══════════════════════════════════════
   TAGS
═══════════════════════════════════════ */
.tag {
    display: inline-block;
    padding: 5px 13px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 3px;
}
.tag-verde  { background:#E6F4F1; color:#004D40; border:1px solid #B2DFDB; }
.tag-cinza  { background:#F1F3F5; color:#4A5568; border:1px solid #DDE1E7; }
.tag-azul   { background:#EBF4FF; color:#1A56DB; border:1px solid #C3D9F7; }
.tag-manual { background:#FFF8EC; color:#92540A; border:1px solid #F6D860; }

/* ═══════════════════════════════════════
   RESUMO CURRÍCULO
═══════════════════════════════════════ */
.cv-resumo {
    background: #F8FAFB;
    border: 1px solid #E2E6EA;
    border-radius: 12px;
    padding: 24px 28px;
    font-size: 13px;
    color: #4A5568;
    line-height: 1.85;
    text-align: left;
    margin-top: 20px;
}

/* ═══════════════════════════════════════
   AVATAR
═══════════════════════════════════════ */
.avatar {
    width: 82px; height: 82px;
    border-radius: 50%;
    background: linear-gradient(145deg, #004D40, #26A69A);
    color: #FFFFFF;
    display: flex; justify-content: center; align-items: center;
    font-size: 24px; font-weight: 800;
    margin: 0 auto 22px auto;
    box-shadow: 0 4px 16px rgba(0,77,64,0.25);
    letter-spacing: 1px;
}
.avatar-img {
    width: 88px; height: 88px;
    border-radius: 50%; object-fit: cover;
    border: 3px solid #B2DFDB;
    margin: 0 auto 22px auto; display: block;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1);
}

/* ═══════════════════════════════════════
   CARDS DE ETAPAS
═══════════════════════════════════════ */
.card-agendado {
    background: #FFFFFF;
    border: 1px solid #E2E6EA;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 12px;
    border-left: 4px solid #004D40;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
.card-agendado:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.card-contratado {
    background: linear-gradient(135deg, #F2FAF8, #E8F5F2);
    border: 1px solid #B2DFDB;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 12px;
    border-left: 4px solid #004D40;
}
.card-pendente {
    background: #FFFDF7;
    border: 1px solid #E8D9A6;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 10px;
    border-left: 4px solid #B7791F;
}
.card-alerta {
    background: #FFFAF8;
    border: 1px solid #E5BCBC;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 10px;
    border-left: 4px solid #9B2C2C;
}

/* ═══════════════════════════════════════
   FORMULÁRIO AGENDAMENTO
═══════════════════════════════════════ */
.form-sched {
    background: #F5FFFE;
    border: 1.5px solid #B2DFDB;
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 22px;
    box-shadow: 0 2px 10px rgba(0,77,64,0.06);
}

/* ═══════════════════════════════════════
   NOTIFICAÇÕES
═══════════════════════════════════════ */
.notif {
    border-radius: 9px;
    padding: 14px 20px;
    font-size: 13px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 16px;
    letter-spacing: 0.2px;
}
.notif-ok   { background:#EBF8F4; border:1px solid #9DCFBF; color:#00382E; }
.notif-info { background:#EBF4FF; border:1px solid #93C5FD; color:#1E40AF; }
.notif-warn { background:#FFFBEB; border:1px solid #D4A853; color:#92540A; }

/* ═══════════════════════════════════════
   ESTADO VAZIO
═══════════════════════════════════════ */
.empty { text-align:center; padding:72px 20px; }
.empty .e-title {
    font-size: 11px; font-weight: 700;
    color: #CDD5DF; letter-spacing: 3px; text-transform: uppercase;
}
.empty .e-sub { font-size: 12px; color: #DDE1E7; margin-top: 8px; }

/* ═══════════════════════════════════════
   INPUTS PRINCIPAIS
═══════════════════════════════════════ */
div[data-testid="stTextInput"] input {
    border-radius: 8px !important;
    border: 1.5px solid #D1D8E0 !important;
    font-size: 13px !important;
    color: #0D1B2A !important;
    padding: 10px 14px !important;
    background: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #004D40 !important;
    box-shadow: 0 0 0 3px rgba(0,77,64,0.09) !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #B0BAC8 !important; }

/* ── Barra de pesquisa — destaque ── */
div[data-testid="stTextInput"]:has(input[aria-label="busca_global"]) input,
div[data-testid="stTextInput"] input[id*="busca_global"] {
    height: 48px !important;
    font-size: 14px !important;
    padding-left: 18px !important;
}

/* ═══════════════════════════════════════
   BOTÃO WHATSAPP
═══════════════════════════════════════ */
.wa-btn {
    display: block;
    background: #00A884;
    color: #FFFFFF !important;
    text-decoration: none;
    border-radius: 9px;
    padding: 13px 18px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 10px;
    transition: background 0.18s;
    box-shadow: 0 2px 8px rgba(0,168,132,0.2);
}
.wa-btn:hover { background: #007F65; color:#FFFFFF !important; }

/* ═══════════════════════════════════════
   LABEL SIDEBAR
═══════════════════════════════════════ */
.sb-label {
    font-size: 9px;
    font-weight: 700;
    color: rgba(255,255,255,0.45);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: block;
}

/* ── Selectbox/Slider Streamlit — accent verde ── */
.stSelectbox [data-baseweb="select"] > div {
    border-color: #D1D8E0 !important;
    border-radius: 8px !important;
}
.stSelectbox [data-baseweb="select"] > div:focus-within {
    border-color: #004D40 !important;
    box-shadow: 0 0 0 2px rgba(0,77,64,0.1) !important;
}

/* ── Forçar accent-color global para verde (radio, checkbox, range) ── */
input[type="radio"]   { accent-color: #004D40 !important; }
input[type="checkbox"]{ accent-color: #004D40 !important; }
input[type="range"]   { accent-color: #26A69A !important; }

</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# PERSISTÊNCIA
# ──────────────────────────────────────────
def _serial(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)): return obj.isoformat()
    if isinstance(obj, datetime.time): return obj.strftime('%H:%M:%S')
    if isinstance(obj, bytes): return base64.b64encode(obj).decode('utf-8')
    raise TypeError(f"Não serializável: {type(obj)}")

def salvar_json():
    try:
        dados = {
            "aguardando":  st.session_state.aguardando_retorno,
            "agendados":   st.session_state.agendados,
            "contratados": st.session_state.contratados,
        }
        with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
            json.dump(dados, f, default=_serial, indent=2, ensure_ascii=False)
    except Exception as e:
        st.warning(f"Aviso ao salvar: {e}")

def _fix_datas(lista):
    for c in lista:
        for k in ['data_entrevista','data_inicio_contrato']:
            if k in c and isinstance(c[k], str):
                try: c[k] = datetime.date.fromisoformat(c[k])
                except: c[k] = None
        for k in ['hora_entrevista','opcao_1','opcao_2','opcao_3','hora_inicio_contrato']:
            if k in c and isinstance(c[k], str):
                try: c[k] = datetime.time.fromisoformat(c[k])
                except: c[k] = None
        for k in ['arquivo_bytes','foto']:
            if k in c and c[k]:
                try: c[k] = base64.b64decode(c[k])
                except: c[k] = None
    return lista

def carregar_json():
    if st.session_state.get('_carregado'): return
    try:
        if os.path.exists(ARQUIVO_MEMORIA):
            with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
                d = json.load(f)
            st.session_state.aguardando_retorno = _fix_datas(d.get("aguardando", []))
            st.session_state.agendados          = _fix_datas(d.get("agendados",  []))
            st.session_state.contratados        = _fix_datas(d.get("contratados",[]))
            # Constrói set de e-mails já em outras etapas (para dedup)
            proc = set()
            for lst in [st.session_state.aguardando_retorno,
                        st.session_state.agendados,
                        st.session_state.contratados]:
                for c in lst:
                    if c.get('email'): proc.add(c['email'].lower().strip())
            st.session_state._processados = proc
    except Exception as e:
        st.warning(f"Aviso ao carregar: {e}")
    finally:
        st.session_state._carregado = True

# ──────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────
_def = {
    'cvs': [], 'agendados': [], 'contratados': [],
    'aguardando_retorno': [], 'cvs_antigos': [],
    'historico_emails': set(),
    'candidato_foco': None, 'contratar_foco': None,
    'pular_idx': {},
    'sync_msg': None, 'sync_logs': [],
    'executar_sync': False, 'limite_sync': 30,
    '_processados': set(),
}
for k, v in _def.items():
    if k not in st.session_state:
        st.session_state[k] = v

carregar_json()

# ──────────────────────────────────────────
# UTILITÁRIOS
# ──────────────────────────────────────────
def send_email(dest, assunto, corpo):
    try:
        m = MIMEText(corpo, 'plain', 'utf-8')
        m['Subject'] = assunto
        m['From']    = EMAIL_CONTA
        m['To']      = dest
        m['Bcc']     = EMAIL_CONTA
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as s:
            s.login(EMAIL_CONTA, SENHA_CONTA)
            s.send_message(m)
        return True
    except: return False

def iniciais(nome):
    p = nome.strip().split()
    if len(p) >= 2: return f"{p[0][0]}{p[-1][0]}".upper()
    return nome[:2].upper() if nome else "CV"

def resumo(texto):
    pads = ['experiencia','formacao','historico profissional','cursos','qualificacoes','habilidades']
    tl   = texto.lower()
    ini  = min((tl.find(p) for p in pads if tl.find(p)!=-1), default=-1)
    r    = texto[ini:ini+1500] if ini!=-1 else texto[:1500]
    if len(texto) > len(r): r = r.rsplit(' ',1)[0]+"..."
    r = r.replace('\n',' ')
    r = re.sub(
        r'(QUALIFICACOES|FORMACAO|EXPERIENCIA|OBJETIVOS|RESUMO|CURSOS|HABILIDADES)',
        r'<br><br><b style="color:#004D40;font-size:12px;letter-spacing:1px;">\1</b><br>',
        r, flags=re.IGNORECASE
    )
    return r

def setor_cv(assunto, texto):
    t = f"{assunto} {texto}".lower()
    if any(p in t for p in ["recep","atendiment","telefonista","secretaria","recepcionista"]): return "RECEPCAO E ATENDIMENTO"
    if any(p in t for p in ["enfermagem","tec. enf","tecnico em enf","enfermeir"]): return "TECNICO E ENFERMAGEM"
    if any(p in t for p in ["faturamento","fatura","analista de fat"]): return "FATURAMENTO"
    if any(p in t for p in ["adm","assistente adm","auxiliar adm","financeiro"]): return "ADMINISTRATIVO"
    if any(p in t for p in ["aprendiz","jovem","menor aprendiz","primeiro emprego"]): return "JOVEM APRENDIZ"
    return "TRIAGEM GERAL"

def novo_manual(nome, email_c, tel, setor):
    now = datetime.datetime.now()
    return {
        "id": str(int(time.time()*1000)),
        "nome": nome.upper().strip(), "email": email_c.lower().strip(),
        "telefone": ''.join(filter(str.isdigit, tel)),
        "data": now.strftime("%d/%m/%Y"), "data_iso": now.strftime("%Y-%m-%d"),
        "mes_num": now.month, "cidade": "", "tags": [],
        "preview": "Cadastro manual — sem currículo físico.",
        "setor": setor, "nome_arquivo": "",
        "arquivo_bytes": None, "foto": None, "manual": True,
    }

def email_admissao(nome, dl, di, hi):
    return f"""Prezada(o) {nome.title()}, bom dia!

Aqui é a equipe de RH do Hospital de Olhos Vale do Aço.

Temos o prazer de informar que você foi selecionada(o) para integrar nossa equipe.
Seja muito bem-vinda(o)!

Para continuidade do processo de admissão, solicitamos o envio dos documentos abaixo
até o dia {dl.strftime('%d/%m/%Y')}, em formato PDF (um arquivo por documento).

Envie pelo WhatsApp para: +55 31 8860-0023 (PAULA)

Documentos necessários:
  - RG
  - CPF
  - Comprovante de residência
  - Cartão do PIS
  - Diploma (se houver)
  - Cartão de vacinação (Hepatite B e Tétano atualizados)
  - Certidão de casamento (se houver)
  - Certidão de nascimento dos filhos + CPF (se houver)
  - Declaração escolar dos filhos (se houver)

A foto 3x4 deverá ser entregue presencialmente.

Seu inicio sera no dia {di.strftime('%d/%m/%Y')} as {hi.strftime('%H:%M')}.

Caso necessite de vale-transporte, informe a(s) linha(s) utilizada(s).

Ficamos à disposição para qualquer dúvida.

Atenciosamente,
Equipe de RH — Hospital de Olhos Vale do Aço"""

# ──────────────────────────────────────────
# BUSCA DE CURRICULOS
# ──────────────────────────────────────────
def buscar_curriculos(limite):
    logs = []
    capturados = 0

    # 1. Conectar
    try:
        conn = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        conn.login(EMAIL_CONTA, SENHA_CONTA)
        conn.select("INBOX")
        logs.append("Conexao IMAP estabelecida.")
    except Exception as e:
        return 0, [f"ERRO de conexão: {e}"]

    # 2. Listar e-mails
    try:
        status, dados = conn.search(None, 'ALL')
        if status != 'OK' or not dados[0]:
            conn.logout()
            return 0, ["Nenhum e-mail encontrado na caixa."]
        ids = dados[0].split()
        # Mais recentes primeiro
        ids_varrer = ids[-limite:][::-1]
        logs.append(f"{len(ids)} e-mail(s) na caixa. Varrendo os {len(ids_varrer)} mais recentes.")
    except Exception as e:
        conn.logout()
        return 0, [f"Erro ao listar e-mails: {e}"]

    # 3. Processar
    emails_em_triagem = {c['email'] for c in st.session_state.cvs}
    emails_processados = st.session_state._processados

    for mid in ids_varrer:
        try:
            status, md = conn.fetch(mid, '(RFC822)')
            if status != 'OK' or not md or not isinstance(md[0], tuple):
                continue

            msg        = email.message_from_bytes(md[0][1])
            msg_id     = msg.get('Message-ID') or mid.decode()
            remetente  = email.utils.parseaddr(msg.get('From',''))[1].lower().strip()

            # Decodificar assunto
            assunto_raw = msg.get('Subject','')
            assunto = ''
            if assunto_raw:
                try:
                    dec, enc = decode_header(assunto_raw)[0]
                    assunto = dec.decode(enc or 'utf-8', errors='replace') if isinstance(dec, bytes) else str(dec)
                except:
                    assunto = assunto_raw
            al = assunto.lower()

            # Verificar se é CV
            tem_palavra = any(p in al for p in PALAVRAS_CV)
            tem_anexo   = any(
                (p.get_filename() or '').lower().endswith(('.pdf','.doc','.docx'))
                for p in msg.walk()
            )
            if not tem_palavra and not tem_anexo:
                continue

            for part in msg.walk():
                if part.get_content_maintype() == 'multipart': continue
                fn = part.get_filename() or ''
                if not fn.lower().endswith(('.pdf','.doc','.docx')): continue

                # Dedup por sessão
                chave = f"{msg_id}::{fn}"
                if chave in st.session_state.historico_emails:
                    logs.append(f"Sessão: já visto — {fn}")
                    continue

                payload = part.get_payload(decode=True)
                if not payload:
                    logs.append(f"Anexo vazio: {fn}")
                    continue

                # ── Extrair texto direto do payload (sem arquivo temp)
                # Usa io.BytesIO para compatibilidade com Streamlit Cloud
                txt  = ''
                foto = None

                if fn.lower().endswith('.pdf'):
                    # Tentativa 1: pdfplumber via BytesIO
                    if pdfplumber:
                        try:
                            buf = io.BytesIO(payload)
                            with pdfplumber.open(buf) as pdf:
                                paginas = []
                                for pg in pdf.pages:
                                    t = pg.extract_text()
                                    if t: paginas.append(t)
                                txt = "\n".join(paginas)
                        except Exception as e:
                            logs.append(f"pdfplumber erro: {e}")
                            txt = ''

                    # Tentativa 2: fitz (PyMuPDF) via stream
                    if not txt and fitz:
                        try:
                            doc = fitz.open(stream=payload, filetype="pdf")
                            txt = "\n".join(doc[i].get_text() for i in range(len(doc)))
                        except Exception as e:
                            logs.append(f"fitz erro: {e}")

                    # Tentativa 3: arquivo temp em /tmp (sempre gravável)
                    if not txt:
                        try:
                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                                tf.write(payload)
                                tfname = tf.name
                            if pdfplumber:
                                with pdfplumber.open(tfname) as pdf:
                                    txt = "\n".join(pg.extract_text() for pg in pdf.pages if pg.extract_text())
                            os.remove(tfname)
                        except Exception as e:
                            logs.append(f"temp fallback erro: {e}")

                    # Foto via fitz stream
                    if fitz:
                        try:
                            doc  = fitz.open(stream=payload, filetype="pdf")
                            imgs = doc.get_page_images(0) if len(doc) > 0 else []
                            if imgs:
                                foto = doc.extract_image(imgs[0][0])["image"]
                        except: pass

                elif fn.lower().endswith(('.doc', '.docx')) and docx2txt:
                    try:
                        ext = '.docx' if fn.lower().endswith('.docx') else '.doc'
                        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
                            tf.write(payload)
                            tfname = tf.name
                        txt = docx2txt.process(tfname)
                        os.remove(tfname)
                    except Exception as e:
                        txt = f"Erro Word: {e}"

                logs.append(f"Texto extraído: {len(txt)} chars — {fn}")

                # E-mail do candidato
                emails_pdf  = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', txt)
                email_cand  = emails_pdf[0].lower() if emails_pdf else remetente

                # Dedup por e-mail (outras etapas)
                if email_cand in emails_processados:
                    logs.append(f"Já em outra etapa: {email_cand}")
                    st.session_state.historico_emails.add(chave)
                    continue
                if email_cand in emails_em_triagem:
                    logs.append(f"Já na triagem: {email_cand}")
                    st.session_state.historico_emails.add(chave)
                    continue

                # Extrair outros dados
                cels    = re.findall(r'\(?\d{2}\)?\s?(?:9\s?)?\d{4}[\s\-]?\d{4}', txt)
                tel     = ''.join(filter(str.isdigit, cels[0])) if cels else ''
                cidades = ["ipatinga","coronel fabriciano","timoteo","santana do paraiso"]
                cidade  = next((c.title() for c in cidades if c in txt.lower() or c in al),'')
                sk_list = ["Atendimento","PABX","Pacote Office","Excel","Agendamento",
                           "Faturamento","Recepcao","Financeiro","Enfermagem","Triagem",
                           "Vendas","Administrativo"]
                tags    = [s for s in sk_list if s.lower() in txt.lower()]

                # Nome
                nome = assunto.upper()
                for r in ["CURRICULO","CURRÍCULO","CURRICULUM","CV","VAGA","PARA","DE",
                          "EMPREGO","CANDIDATURA","SELEÇÃO","SELECAO","-",":","/"]:
                    nome = nome.replace(r, " ")
                nome = re.sub(r'\s+',' ', nome).strip()
                if len(nome) < 3:
                    nome = (fn.upper()
                            .replace(".PDF","").replace(".DOCX","").replace(".DOC","")
                            .replace("_"," ").replace("-"," ").strip())
                if len(nome) < 3:
                    nome = remetente.split("@")[0].upper()

                setor = setor_cv(assunto, txt)

                try:
                    dt      = parsedate_to_datetime(msg.get('Date',''))
                    ds      = dt.strftime("%d/%m/%Y")
                    diso    = dt.strftime("%Y-%m-%d")
                    mes_n   = dt.month
                except:
                    now  = datetime.datetime.now()
                    ds   = now.strftime("%d/%m/%Y")
                    diso = now.strftime("%Y-%m-%d")
                    mes_n= now.month

                candidato = {
                    "id":str(int(time.time()*1000))+str(capturados),
                    "nome":nome, "email":email_cand, "telefone":tel,
                    "data":ds, "data_iso":diso, "mes_num":mes_n,
                    "cidade":cidade, "tags":tags,
                    "preview":resumo(txt),
                    "setor":setor, "nome_arquivo":fn,
                    "arquivo_bytes":payload, "foto":foto, "manual":False,
                }

                st.session_state.cvs.append(candidato)
                st.session_state.historico_emails.add(chave)
                emails_em_triagem.add(email_cand)
                capturados += 1
                logs.append(f"Capturado: {nome} | {setor} | {email_cand}")

        except Exception as e:
            logs.append(f"Erro msg {mid}: {e}")
            continue

    try:
        salvar_json()
        conn.logout()
    except: pass

    logs.append(f"Concluido. {capturados} novo(s) currículo(s) capturado(s).")
    return capturados, logs

# ──────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="background:linear-gradient(160deg,#003329,#004D40);
                margin:-1rem -1rem 0; padding:28px 24px 22px;
                border-bottom:1px solid rgba(255,255,255,0.08);">
        <div style="font-size:26px;font-weight:900;color:#FFFFFF;letter-spacing:-0.5px;">HOVA</div>
        <div style="font-size:9px;color:rgba(255,255,255,0.45);letter-spacing:3px;
                    text-transform:uppercase;margin-top:3px;font-weight:600;">
            Gestão de Talentos
        </div>
    </div>
    <div style="height:20px;"></div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown("<span class='sb-label'>Filtro de setor</span>", unsafe_allow_html=True)
    filtro_setor = st.radio("", [
        "TODOS","TRIAGEM GERAL","RECEPCAO E ATENDIMENTO",
        "TECNICO E ENFERMAGEM","ADMINISTRATIVO","FATURAMENTO","JOVEM APRENDIZ"
    ], label_visibility="collapsed")

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:18px 0;'>", unsafe_allow_html=True)
    st.markdown("<span class='sb-label'>Filtro de período</span>", unsafe_allow_html=True)
    filtro_mes = st.selectbox("", ["Todos os meses"]+list(MESES_NOMES.values()),
                               label_visibility="collapsed")

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:18px 0;'>", unsafe_allow_html=True)
    st.markdown("<span class='sb-label'>Quantidade de e-mails a varrer</span>", unsafe_allow_html=True)
    limite_busca = st.select_slider("", options=[10,30,50,100,200,300],
                                     value=30, label_visibility="collapsed")
    st.caption(f"Últimos {limite_busca} e-mails serão analisados")

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:18px 0;'>", unsafe_allow_html=True)
    st.markdown("<span class='sb-label'>Cadastro manual</span>", unsafe_allow_html=True)
    with st.form("form_manual", clear_on_submit=True):
        mn  = st.text_input("Nome completo", placeholder="Ex: Maria da Silva")
        me  = st.text_input("E-mail", placeholder="candidato@email.com")
        mt  = st.text_input("Telefone", placeholder="31999990000")
        ms  = st.selectbox("Setor", ["TRIAGEM GERAL","RECEPCAO E ATENDIMENTO",
                                      "TECNICO E ENFERMAGEM","ADMINISTRATIVO",
                                      "FATURAMENTO","JOVEM APRENDIZ"])
        ok_manual = st.form_submit_button("CADASTRAR", use_container_width=True, type="primary")
    if ok_manual:
        if mn and me:
            st.session_state.cvs.append(novo_manual(mn, me, mt, ms))
            salvar_json()
            st.success(f"{mn.upper()} cadastrado.")
        else:
            st.error("Nome e e-mail são obrigatórios.")

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:18px 0;'>", unsafe_allow_html=True)
    if st.button("LIMPAR MEMORIA", use_container_width=True):
        for k in ['cvs','agendados','contratados','aguardando_retorno','cvs_antigos']:
            st.session_state[k] = []
        st.session_state.historico_emails = set()
        st.session_state._processados     = set()
        st.session_state.candidato_foco   = None
        st.session_state.contratar_foco   = None
        st.session_state.pular_idx        = {}
        if os.path.exists(ARQUIVO_MEMORIA): os.remove(ARQUIVO_MEMORIA)
        st.success("Memoria zerada.")
        time.sleep(1)
        st.rerun()

# ──────────────────────────────────────────
# HELPERS DE FILTRO
# ──────────────────────────────────────────
def _por_mes(lista):
    if filtro_mes == "Todos os meses": return lista
    alvo = next((k for k,v in MESES_NOMES.items() if v==filtro_mes), None)
    return [c for c in lista if c.get('mes_num')==alvo] if alvo else lista

def _busca(lista, termo):
    if not termo.strip(): return lista
    t = termo.lower().strip()
    return [c for c in lista if
            t in c.get('nome','').lower() or
            t in c.get('email','').lower() or
            t in c.get('telefone','').lower()]

# ──────────────────────────────────────────
# CABEÇALHO
# ──────────────────────────────────────────
n_tri  = len(st.session_state.cvs)
n_ag   = len(st.session_state.aguardando_retorno)
n_agd  = len(st.session_state.agendados)
n_con  = len(st.session_state.contratados)

st.markdown(f"""
<div class="hero-card">
  <div class="hero-left">
    <div class="hero-marca">Hospital de Olhos Vale do Aço</div>
    <div class="hero-titulo">Seletor de<span>Talentos</span></div>
    <div class="hero-sub">Gestão de Processos Seletivos</div>
  </div>
  <div class="hero-stats">
    <div class="stat-box"><span class="n">{n_tri}</span><span class="l">Triagem</span></div>
    <div class="stat-box"><span class="n">{n_ag}</span><span class="l">Aguardando</span></div>
    <div class="stat-box"><span class="n">{n_agd}</span><span class="l">Agendados</span></div>
    <div class="stat-box"><span class="n">{n_con}</span><span class="l">Contratados</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# BARRA DE SINCRONIZAÇÃO
# ──────────────────────────────────────────
col_btn, col_msg = st.columns([1, 2])
with col_btn:
    if st.button("SINCRONIZAR CURRICULOS", type="primary", use_container_width=True):
        st.session_state.executar_sync = True
        st.session_state.limite_sync   = limite_busca
        st.rerun()
with col_msg:
    if st.session_state.sync_msg:
        m   = st.session_state.sync_msg
        css = "notif-ok" if m['tipo']=='ok' else ("notif-warn" if m['tipo']=='err' else "notif-info")
        st.markdown(f"<div class='notif {css}'>{m['texto']}</div>", unsafe_allow_html=True)

if st.session_state.get('sync_logs'):
    with st.expander("Ver log detalhado da última sincronização"):
        for ln in st.session_state.sync_logs:
            st.write(ln)

# Execução real (após rerun, fora de colunas)
if st.session_state.executar_sync:
    st.session_state.executar_sync = False
    with st.spinner(f"Conectando e varrendo {st.session_state.limite_sync} e-mails..."):
        qtd, logs = buscar_curriculos(st.session_state.limite_sync)
    st.session_state.sync_logs = logs
    st.session_state.sync_msg  = {
        'tipo': 'ok' if qtd>0 else ('err' if any('ERRO' in l for l in logs) else 'info'),
        'texto': f"{qtd} novo(s) currículo(s) capturado(s)." if qtd>0
                 else (next((l for l in logs if 'ERRO' in l), None) or
                       f"Nenhum novo currículo encontrado nos últimos {st.session_state.limite_sync} e-mails.")
    }
    st.rerun()

st.write("")

# ──────────────────────────────────────────
# BARRA DE PESQUISA
# ──────────────────────────────────────────
sc1, _ = st.columns([2, 1])
with sc1:
    # Não usar key de busca persistente — campo limpo a cada sessão
    # para não interferir com a triagem
    termo = st.text_input(
        "", placeholder="Pesquisar por nome, e-mail ou telefone...",
        label_visibility="collapsed", key="busca_global"
    )

st.write("")

# ──────────────────────────────────────────
# ABAS
# ──────────────────────────────────────────
abas = st.tabs([
    "TRIAGEM GERAL","RECEPCAO","TEC. ENFERMAGEM",
    "ADMINISTRATIVO","FATURAMENTO","JOVEM APRENDIZ",
    "AGENDADOS","AGUARDANDO RETORNO","CONTRATADOS","BANCO ANTIGOS"
])

SETORES = [
    "TRIAGEM GERAL","RECEPCAO E ATENDIMENTO","TECNICO E ENFERMAGEM",
    "ADMINISTRATIVO","FATURAMENTO","JOVEM APRENDIZ"
]

# ── ABAS 0-5: TRIAGEM ─────────────────────
for i, setor in enumerate(SETORES):
    with abas[i]:
        base     = [c for c in st.session_state.cvs if c['setor']==setor]
        if filtro_setor != "TODOS":
            base = [c for c in base if c['setor']==filtro_setor]
        base     = _por_mes(base)
        fila     = _busca(base, termo)
        fila     = sorted(fila, key=lambda x: x.get('data_iso',''), reverse=True)

        if fila:
            idx_ex = st.session_state.pular_idx.get(setor, 0) % len(fila)
            per    = f" — {filtro_mes}" if filtro_mes!="Todos os meses" else ""
            st.markdown(
                f"<div style='font-size:12px;color:#8A94A6;margin-bottom:14px;'>"
                f"<b style='color:#004D40;font-size:17px;'>{len(fila)}</b> candidato(s){per}"
                f" &nbsp;·&nbsp; Exibindo <b style='color:#004D40;'>{idx_ex+1}</b> de {len(fila)}"
                f"</div>", unsafe_allow_html=True
            )

        if not fila:
            st.session_state.pular_idx.pop(setor, None)
            st.markdown('<div class="empty"><div class="e-title">FILA VAZIA</div>'
                        '<div class="e-sub">Nenhum candidato com os filtros atuais.</div></div>',
                        unsafe_allow_html=True)
            continue

        # Candidato atual
        if st.session_state.candidato_foco:
            c = next((x for x in fila if x['id']==st.session_state.candidato_foco), None)
            if not c:
                idx = st.session_state.pular_idx.get(setor,0) % len(fila)
                c   = fila[idx]
        else:
            idx = st.session_state.pular_idx.get(setor,0) % len(fila)
            c   = fila[idx]

        # ── FORMULÁRIO AGENDAMENTO ──
        if st.session_state.candidato_foco == c['id']:
            st.markdown("<div class='form-sched'>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:16px;font-weight:800;color:#004D40;margin-bottom:20px;'>AGENDAR ENTREVISTA</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.caption("NOME DO CANDIDATO")
                ne = st.text_input("", value=c['nome'], key=f"ne_{c['id']}", label_visibility="collapsed")
            with c2:
                st.caption("E-MAIL")
                ee = st.text_input("", value=c['email'], key=f"ee_{c['id']}", label_visibility="collapsed")

            st.caption("DATA E HORARIOS (3 OPCOES)")
            cd, ch1, ch2, ch3 = st.columns(4)
            da  = cd.date_input("",  key=f"da_{c['id']}",  label_visibility="collapsed")
            h1  = ch1.time_input("", datetime.time(9, 0),  key=f"h1_{c['id']}", label_visibility="collapsed")
            h2  = ch2.time_input("", datetime.time(14,0),  key=f"h2_{c['id']}", label_visibility="collapsed")
            h3  = ch3.time_input("", datetime.time(16,0),  key=f"h3_{c['id']}", label_visibility="collapsed")

            msg_conv = (
                f"Olá {ne},\n\n"
                f"O Hospital de Olhos Vale do Aço analisou seu perfil e você foi selecionada(o) para a próxima fase do Processo Seletivo.\n\n"
                f"Temos disponibilidade para o dia {da.strftime('%d/%m/%Y')}. "
                f"Por gentileza, responda com o NUMERO da sua escolha de horário:\n\n"
                f"1 - {h1.strftime('%H:%M')}\n2 - {h2.strftime('%H:%M')}\n3 - {h3.strftime('%H:%M')}\n\n"
                f"Endereço: {ENDERECO_HOVA}\n"
                f"Ao chegar, informe na recepção que é referente à entrevista e pergunte por Josi ou Paula.\n\n"
                f"Atenciosamente,\nEquipe de RH — Hospital de Olhos Vale do Aço"
            )
            with st.expander("Visualizar e-mail que será enviado"):
                st.code(msg_conv, language=None)

            bc, benv = st.columns(2)
            with bc:
                if st.button("CANCELAR", key=f"canc_{c['id']}", type="secondary", use_container_width=True):
                    st.session_state.candidato_foco = None
                    st.rerun()
            with benv:
                if st.button("ENVIAR CONVITE", type="primary", key=f"conf_{c['id']}", use_container_width=True):
                    with st.spinner("Enviando convite..."):
                        ok = send_email(ee, "HOVA — Convite para Entrevista", msg_conv)
                    if ok:
                        c.update({'nome':ne,'email':ee,'data_entrevista':da,'opcao_1':h1,'opcao_2':h2,'opcao_3':h3})
                        st.session_state.aguardando_retorno.append(c)
                        st.session_state.cvs.remove(c)
                        st.session_state.candidato_foco = None
                        salvar_json()
                        st.rerun()
                    else:
                        st.error("Falha no envio. Verifique as configurações de e-mail.")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── CARD CANDIDATO ──
        else:
            if c.get('foto'):
                b64 = base64.b64encode(c['foto']).decode()
                av  = f"<img src='data:image/jpeg;base64,{b64}' class='avatar-img'>"
            else:
                av = f"<div class='avatar'>{iniciais(c['nome'])}</div>"

            manual_b = "<span class='tag tag-manual'>Manual</span>" if c.get('manual') else ""
            cid_b    = f"<span class='tag tag-cinza'>{c['cidade']}</span>" if c.get('cidade') else ""
            dat_b    = f"<span class='tag tag-azul'>{c['data']}</span>"
            tags_b   = "".join(f"<span class='tag tag-verde'>{t}</span>" for t in c.get('tags',[]))

            st.markdown(
                f"<div class='card-cand'>{av}"
                f"<div class='cand-nome'>{c['nome']} {manual_b}</div>"
                f"<div style='margin:8px 0;'>{cid_b} {dat_b}</div>"
                f"<div class='cand-info'>{c['email']}"
                f"{'  |  '+c['telefone'] if c.get('telefone') else ''}</div>"
                f"<div style='margin:10px 0;'>{tags_b}</div>"
                f"<div class='cv-resumo'>{c['preview']}</div></div>",
                unsafe_allow_html=True
            )

            if c.get('arquivo_bytes') and c.get('nome_arquivo'):
                with st.expander("Ver documento original"):
                    if c['nome_arquivo'].lower().endswith('.pdf'):
                        b64p     = base64.b64encode(c['arquivo_bytes']).decode()
                        data_uri = f"data:application/pdf;base64,{b64p}"

                        # ── Botão de download (sempre funciona) ──
                        st.download_button(
                            label    = f"Baixar PDF — {c['nome_arquivo']}",
                            data     = c['arquivo_bytes'],
                            file_name= c['nome_arquivo'],
                            mime     = "application/pdf",
                            use_container_width=True,
                            key      = f"dl_{c['id']}"
                        )

                        # ── Visualizador inline via <object> (mais compatível que iframe) ──
                        st.markdown(
                            f'<object data="{data_uri}" type="application/pdf"'
                            f' width="100%" height="700"'
                            f' style="border:1px solid #E2E6EA;border-radius:8px;'
                            f'display:block;margin-top:12px;">'
                            f'<p style="padding:20px;color:#8A94A6;font-size:13px;">'
                            f'Seu navegador não suporta visualização inline de PDF. '
                            f'Use o botão acima para baixar.</p>'
                            f'</object>',
                            unsafe_allow_html=True
                        )

                        # ── Link alternativo ──
                        st.markdown(
                            f'<a href="{data_uri}" target="_blank" download="{c["nome_arquivo"]}"'
                            f' style="font-size:12px;color:#004D40;font-weight:600;'
                            f'text-decoration:underline;display:inline-block;margin-top:8px;">'
                            f'Abrir em nova aba</a>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("Visualização direta disponível apenas para PDF.")
                        st.download_button(
                            f"Baixar arquivo — {c['nome_arquivo']}",
                            c['arquivo_bytes'], file_name=c['nome_arquivo'],
                            mime="application/octet-stream",
                            use_container_width=True, key=f"dl_{c['id']}"
                        )
            elif c.get('manual'):
                st.markdown("<div class='notif notif-info'>Candidato cadastrado manualmente — sem arquivo físico.</div>", unsafe_allow_html=True)

            st.write("")
            br, bp, bac = st.columns(3)
            with br:
                if st.button("REJEITAR", key=f"rej_{c['id']}", type="secondary", use_container_width=True):
                    mr = (f"Olá {c['nome'].title()},\n\n"
                          f"Agradecemos seu interesse no Hospital de Olhos Vale do Aço. "
                          f"No momento seu perfil não se enquadra nas vagas disponíveis, "
                          f"mas manteremos seu currículo em nossa base de dados.\n\n"
                          f"Atenciosamente,\nEquipe de RH — HOVA")
                    with st.spinner("Notificando candidato..."):
                        send_email(c['email'], "HOVA — Processo Seletivo", mr)
                    st.session_state.cvs.remove(c)
                    nt  = len([x for x in st.session_state.cvs if x['setor']==setor])
                    idx = st.session_state.pular_idx.get(setor,0)
                    st.session_state.pular_idx[setor] = max(0, min(idx, nt-1)) if nt>0 else 0
                    salvar_json()
                    st.rerun()
            with bp:
                if st.button("PULAR", key=f"pul_{c['id']}", use_container_width=True):
                    cur = st.session_state.pular_idx.get(setor, 0)
                    st.session_state.pular_idx[setor] = (cur+1) % len(fila)
                    st.rerun()
            with bac:
                if st.button("ACEITAR", key=f"acc_{c['id']}", type="primary", use_container_width=True):
                    st.session_state.candidato_foco = c['id']
                    st.rerun()

# ── ABA 6: AGENDADOS ──────────────────────
with abas[6]:
    ag_list = _busca(_por_mes(st.session_state.agendados), termo)
    if not ag_list:
        st.markdown('<div class="empty"><div class="e-title">SEM ENTREVISTAS</div>'
                    '<div class="e-sub">Nenhuma entrevista confirmada ainda.</div></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:12px;color:#8A94A6;margin-bottom:16px;'>"
                    f"<b style='color:#004D40;font-size:17px;'>{len(ag_list)}</b> entrevista(s) agendada(s)</div>",
                    unsafe_allow_html=True)
        for c in sorted(ag_list, key=lambda x: (x.get('data_entrevista') or datetime.date.min,
                                                  x.get('hora_entrevista') or datetime.time(0))):
            hf = c['hora_entrevista'].strftime('%H:%M') if c.get('hora_entrevista') else '—'
            df = c['data_entrevista'].strftime('%d/%m/%Y') if c.get('data_entrevista') else '—'

            st.markdown("<div class='card-agendado'>", unsafe_allow_html=True)
            ci, cd, ca = st.columns([1,3,3])
            with ci:
                st.markdown(f'<div class="avatar" style="width:64px;height:64px;font-size:18px;">{iniciais(c["nome"])}</div>', unsafe_allow_html=True)
            with cd:
                st.markdown(f"**{c['nome']}**")
                st.markdown(f"Data: **{df}** às **{hf}**")
                st.markdown(f"<span style='color:#8A94A6;font-size:12px;'>{c.get('setor','—')} | {c.get('email','—')}</span>", unsafe_allow_html=True)
            with ca:
                tel = c.get('telefone','')
                if tel:
                    mwa = f"Confirmando sua entrevista no Hospital de Olhos Vale do Aço em {df} às {hf}. Endereço: {ENDERECO_HOVA}. Pergunte por Josi ou Paula."
                    st.markdown(f'<a href="https://wa.me/{tel}?text={urllib.parse.quote(mwa)}" target="_blank" class="wa-btn">Confirmar via WhatsApp</a>', unsafe_allow_html=True)

                if st.session_state.contratar_foco == c['id']:
                    st.caption("DADOS DE ADMISSÃO")
                    cdl, cdi = st.columns(2)
                    dl = cdl.date_input("Prazo documentos:", key=f"dl_{c['id']}")
                    di = cdi.date_input("Data de início:", key=f"di_{c['id']}")
                    hi = st.time_input("Horário de entrada:", datetime.time(8,0), key=f"hi_{c['id']}")
                    tn = st.text_input("WhatsApp (só números):", value=tel, key=f"wa_{c['id']}")
                    cx, cok = st.columns(2)
                    with cx:
                        if st.button("CANCELAR", key=f"cx_{c['id']}", type="secondary", use_container_width=True):
                            st.session_state.contratar_foco = None
                            st.rerun()
                    with cok:
                        if st.button("CONFIRMAR", key=f"cok_{c['id']}", type="primary", use_container_width=True):
                            with st.spinner("Enviando e-mail de admissão..."):
                                ok = send_email(c['email'], "HOVA — Bem-vinda(o) a Nossa Equipe", email_admissao(c['nome'],dl,di,hi))
                            c.update({'data_inicio_contrato':di,'hora_inicio_contrato':hi,
                                      'telefone':tn,'email_admissao_enviado':ok})
                            st.session_state.contratados.append(c)
                            st.session_state.agendados.remove(c)
                            st.session_state.contratar_foco = None
                            salvar_json()
                            st.session_state.sync_msg = {
                                'tipo': 'ok' if ok else 'warn',
                                'texto': f"{c['nome']} contratado(a). E-mail de admissão enviado." if ok
                                         else f"{c['nome']} movido para Contratados. E-mail pendente."
                            }
                            time.sleep(1)
                            st.rerun()
                else:
                    if st.button("CONTRATAR", key=f"ct_{c['id']}", type="primary", use_container_width=True):
                        st.session_state.contratar_foco = c['id']
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ── ABA 7: AGUARDANDO RETORNO ─────────────
with abas[7]:
    pend = _busca(st.session_state.aguardando_retorno, termo)

    if st.button("LER RESPOSTAS E AGENDAR AUTOMATICO", type="primary", use_container_width=True):
        res_auto = []
        with st.spinner("Verificando respostas de e-mail..."):
            try:
                conn = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
                conn.login(EMAIL_CONTA, SENHA_CONTA)
                conn.select("INBOX")
                _, ids = conn.search(None, '(SUBJECT "Re: HOVA")')
                for mid in (ids[0].split() or [])[-50:]:
                    _, md = conn.fetch(mid,'(RFC822)')
                    msg  = email.message_from_bytes(md[0][1])
                    rem  = email.utils.parseaddr(msg.get('From',''))[1].lower()
                    corpo = ''
                    for pt in msg.walk():
                        if pt.get_content_type()=="text/plain":
                            try: corpo += pt.get_payload(decode=True).decode('utf-8',errors='ignore')
                            except: pass
                    op = next((o for o in ["1","2","3"] if o in corpo.lower()), None)
                    if not op: continue
                    cand = next((c for c in st.session_state.aguardando_retorno if c['email']==rem), None)
                    if not cand: continue
                    hmap = {"1":cand.get('opcao_1'),"2":cand.get('opcao_2'),"3":cand.get('opcao_3')}
                    hd   = hmap.get(op)
                    dd   = cand.get('data_entrevista')
                    conf = hd and any(a.get('data_entrevista')==dd and a.get('hora_entrevista')==hd
                                      for a in st.session_state.agendados)
                    if conf:
                        livres = [f"{n} - {h.strftime('%H:%M')}" for n,h in hmap.items()
                                  if h and not any(a.get('data_entrevista')==dd and a.get('hora_entrevista')==h
                                                   for a in st.session_state.agendados)]
                        if livres:
                            send_email(cand['email'],"HOVA — Atualizacao de Horário",
                                       f"Olá {cand['nome']},\n\nO horário de {hd.strftime('%H:%M')} foi preenchido.\n\nOpções disponíveis:\n"+"\n".join(livres)+"\n\nResponda com o número.\n\nRH — HOVA")
                            res_auto.append(('warn',f"Conflito para {cand['nome']} — novas opções enviadas."))
                        else:
                            send_email(cand['email'],"HOVA — Horários Preenchidos",
                                       f"Olá {cand['nome']}, todos os horários foram preenchidos. Entraremos em contato.\n\nRH — HOVA")
                            cand['alerta_lota'] = True
                            res_auto.append(('err',f"Horários esgotados para {cand['nome']}."))
                    else:
                        cand['hora_entrevista'] = hd
                        st.session_state.agendados.append(cand)
                        st.session_state.aguardando_retorno.remove(cand)
                        salvar_json()
                        res_auto.append(('ok',f"{cand['nome']} agendado(a) para {hd.strftime('%H:%M') if hd else '—'}."))
                    time.sleep(0.4)
                conn.logout()
                res_auto.append(('info','Varredura concluída.'))
            except Exception as e:
                res_auto.append(('err',f"Erro: {e}"))

        for tp, tx in res_auto:
            css = "notif-ok" if tp=='ok' else ("notif-warn" if tp in ('warn','err') else "notif-info")
            st.markdown(f"<div class='notif {css}'>{tx}</div>", unsafe_allow_html=True)
        time.sleep(1.5)
        st.rerun()

    st.write("")
    if not pend:
        st.markdown('<div class="empty"><div class="e-title">SEM PENDENCIAS</div>'
                    '<div class="e-sub">Nenhum candidato aguardando resposta.</div></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:12px;color:#8A94A6;margin-bottom:16px;'>"
                    f"<b style='color:#B7791F;font-size:17px;'>{len(pend)}</b> aguardando resposta</div>",
                    unsafe_allow_html=True)
        for c in pend:
            alerta = c.get('alerta_lota',False)
            df     = c['data_entrevista'].strftime('%d/%m/%Y') if c.get('data_entrevista') else '—'
            cls    = "card-alerta" if alerta else "card-pendente"
            st.markdown(f"<div class='{cls}'>", unsafe_allow_html=True)
            cc1, cc2 = st.columns([3,1])
            with cc1:
                st.markdown(f"**{c['nome']}**")
                st.markdown(f"<span style='font-size:12px;color:#8A94A6;'>{c.get('email','—')} &nbsp;·&nbsp; Entrevista: <b>{df}</b></span>", unsafe_allow_html=True)
                if alerta:
                    st.markdown("<span style='color:#9B2C2C;font-size:12px;font-weight:700;'>TODOS OS HORARIOS ESGOTARAM — REAGENDE MANUALMENTE.</span>", unsafe_allow_html=True)
            with cc2:
                if st.button("Mover", key=f"mv_{c['id']}", use_container_width=True):
                    c['hora_entrevista'] = c.get('opcao_1', datetime.time(9,0))
                    st.session_state.agendados.append(c)
                    st.session_state.aguardando_retorno.remove(c)
                    salvar_json()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ── ABA 8: CONTRATADOS ────────────────────
with abas[8]:
    con_list = _busca(st.session_state.contratados, termo)
    st.markdown(f"<div style='margin-bottom:20px;'>"
                f"<span style='font-size:26px;font-weight:800;color:#004D40;'>{len(con_list)}</span>"
                f" <span style='font-size:13px;color:#8A94A6;'>admissão(ões) registrada(s)</span></div>",
                unsafe_allow_html=True)
    if not con_list:
        st.markdown('<div class="empty"><div class="e-title">SEM CONTRATADOS</div>'
                    '<div class="e-sub">Nenhuma admissão registrada ainda.</div></div>',
                    unsafe_allow_html=True)
    else:
        for c in sorted(con_list, key=lambda x: x.get('data_inicio_contrato') or datetime.date.min, reverse=True):
            ini_f = c['data_inicio_contrato'].strftime('%d/%m/%Y') if c.get('data_inicio_contrato') else '—'
            hor_f = c['hora_inicio_contrato'].strftime('%H:%M') if c.get('hora_inicio_contrato') else '—'
            em_ok = "E-mail enviado" if c.get('email_admissao_enviado') else "E-mail pendente"
            st.markdown(f"""
            <div class="card-contratado">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div style="font-size:18px;font-weight:800;color:#004D40;">{c['nome']}</div>
                        <div style="margin-top:6px;font-size:13px;color:#2D6A4F;">
                            Inicio: <b>{ini_f}</b> às <b>{hor_f}</b> &nbsp;·&nbsp; <b>{c.get('setor','—')}</b>
                        </div>
                        <div style="margin-top:4px;font-size:12px;color:#4A5568;">
                            {c.get('email','—')} &nbsp;·&nbsp; {c.get('telefone','—')} &nbsp;·&nbsp; {em_ok}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── ABA 9: BANCO ANTIGOS ──────────────────
with abas[9]:
    c_mes, c_bsc = st.columns([1,2])
    with c_mes:
        fm_ant = st.selectbox("", ["Todos"]+list(MESES_NOMES.values()), key="fm_ant", label_visibility="collapsed")
    with c_bsc:
        bsc_ant = st.text_input("", placeholder="Pesquisar...", key="bsc_ant", label_visibility="collapsed")
    st.write("---")
    ant = st.session_state.cvs_antigos
    if fm_ant != "Todos":
        ant = [c for c in ant if c.get('mes_nome')==fm_ant]
    if bsc_ant.strip():
        t2 = bsc_ant.lower()
        ant = [c for c in ant if t2 in c.get('nome','').lower() or t2 in c.get('email','').lower()]
    if not ant:
        st.markdown('<div class="empty"><div class="e-title">BANCO VAZIO</div>'
                    '<div class="e-sub">Nenhum currículo encontrado.</div></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:12px;color:#8A94A6;margin-bottom:12px;'><b style='color:#004D40;'>{len(ant)}</b> currículo(s)</div>", unsafe_allow_html=True)
        for c in ant:
            st.markdown(f"""
            <div style="background:#FFF;padding:16px 20px;border-radius:10px;margin-bottom:8px;
                        border:1px solid #E4E7EB;border-left:3px solid #CBD5E0;">
                <div style="font-weight:700;font-size:14px;color:#0A1628;">{c['nome']}</div>
                <div style="color:#8A94A6;font-size:12px;margin-top:2px;">
                    {c.get('setor','—')} &nbsp;·&nbsp; {c.get('email','—')} &nbsp;·&nbsp; {c.get('data','—')}
                </div>
            </div>""", unsafe_allow_html=True)

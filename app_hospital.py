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

/* ═══════════════════════════════════════
   MÓDULO FUNCIONÁRIOS
═══════════════════════════════════════ */
.func-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}
.func-card {
    background: #FFFFFF;
    border: 1px solid #E2E6EA;
    border-radius: 16px;
    padding: 24px 16px 18px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    transition: transform 0.18s, box-shadow 0.18s;
    animation: fadeUp 0.3s ease forwards;
}
.func-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0,77,64,0.12);
}
.func-avatar {
    width: 80px; height: 80px;
    border-radius: 50%;
    background: linear-gradient(145deg, #004D40, #26A69A);
    color: #FFF;
    display: flex; justify-content: center; align-items: center;
    font-size: 26px; font-weight: 800;
    margin: 0 auto 14px auto;
    box-shadow: 0 4px 14px rgba(0,77,64,0.25);
}
.func-avatar-img {
    width: 80px; height: 80px;
    border-radius: 50%; object-fit: cover;
    border: 3px solid #B2DFDB;
    margin: 0 auto 14px auto; display: block;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1);
}
.func-nome {
    font-size: 13px; font-weight: 800;
    color: #0D1B2A; text-transform: uppercase;
    letter-spacing: 0.3px; line-height: 1.3;
    margin-bottom: 4px;
}
.func-cargo {
    font-size: 11px; color: #004D40;
    font-weight: 600; letter-spacing: 0.5px;
    text-transform: uppercase; margin-bottom: 4px;
}
.func-data {
    font-size: 10px; color: #9AA5B4;
    margin-bottom: 14px;
}
.dossie-card {
    background: #FFFFFF;
    border: 1px solid #E2E6EA;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    animation: fadeUp 0.3s ease;
}
.ex-func-card {
    background: #F8FAFB;
    border: 1px solid #E2E6EA;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    border-left: 3px solid #9AA5B4;
}

/* ── Abas internas do módulo ── */
.mod-tab-btn {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 11px; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    cursor: pointer; margin-right: 8px; margin-bottom: 16px;
    border: 1.5px solid #E2E6EA;
    background: #FFFFFF; color: #9AA5B4;
}
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
            "aguardando":      st.session_state.aguardando_retorno,
            "agendados":       st.session_state.agendados,
            "contratados":     st.session_state.contratados,
            "ex_funcionarios": st.session_state.ex_funcionarios,
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
            st.session_state.aguardando_retorno = _fix_datas(d.get("aguardando",      []))
            st.session_state.agendados          = _fix_datas(d.get("agendados",       []))
            st.session_state.contratados        = _fix_datas(d.get("contratados",     []))
            st.session_state.ex_funcionarios    = _fix_datas(d.get("ex_funcionarios", []))
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
    'ex_funcionarios': [],
    'favoritos': [],
    'historico_emails': set(),
    'candidato_foco': None, 'contratar_foco': None,
    'perfil_foco': None,
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

def resumo(texto: str) -> str:
    """
    Extração inteligente e gratuita — sem API, sem tokens.
    Foca no que o RH quer ver: endereço, experiências (empresa+cargo+período) e formação.
    """
    if not texto or len(texto.strip()) < 20:
        return "<i style='color:#9AA5B4;'>Nenhum texto extraído do documento.</i>"

    # Normalizar
    texto = re.sub(r'\r\n|\r', '\n', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto).strip()
    linhas = [l.strip() for l in texto.splitlines()]
    tl = texto.lower()

    html = []

    # ── 1. CIDADE / ENDEREÇO ─────────────────────────────────────
    cidades_vale = ["ipatinga", "coronel fabriciano", "timóteo", "timoteo",
                    "santana do paraíso", "santana do paraiso", "belo horizonte",
                    "governador valadares", "caratinga"]
    cidade_enc = ""
    for linha in linhas[:25]:   # endereço geralmente nas primeiras linhas
        ll = linha.lower()
        for cid in cidades_vale:
            if cid in ll:
                cidade_enc = linha
                break
        if cidade_enc:
            break

    # Fallback: procurar padrão "Cidade/UF" ou "Cidade - UF"
    if not cidade_enc:
        m = re.search(r'([A-ZÀ-Ú][a-zA-ZÀ-ú\s]+(?:do|de|da)?\s*[A-ZÀ-Ú][a-zA-ZÀ-ú]+)\s*/\s*MG', texto)
        if m:
            cidade_enc = m.group(0)

    # ── 2. TELEFONE ──────────────────────────────────────────────
    tel_enc = ""
    m_tel = re.search(r'\(?\d{2}\)?\s?(?:9\s?)?\d{4,5}[\s\-]?\d{4}', texto)
    if m_tel:
        tel_enc = re.sub(r'\s+', ' ', m_tel.group(0)).strip()

    # ── 3. EXPERIÊNCIAS PROFISSIONAIS ────────────────────────────
    # Localizar seção de experiência
    padroes_exp = [
        r'experi[eê]nci[as]\s+profissionais?',
        r'hist[oó]rico\s+profissional',
        r'atua[çc][aã]o\s+profissional',
        r'experi[eê]ncia',
    ]
    ini_exp = -1
    for p in padroes_exp:
        m = re.search(p, tl)
        if m:
            ini_exp = m.start()
            break

    # Localizar seção de formação para delimitar o bloco de experiência
    padroes_form = [
        r'forma[çc][aã]o\s+acad[eê]mica',
        r'forma[çc][aã]o\s+escolar',
        r'escolaridade',
        r'forma[çc][aã]o',
        r'instru[çc][aã]o',
    ]
    ini_form = len(texto)
    for p in padroes_form:
        m = re.search(p, tl)
        if m and m.start() > ini_exp:
            ini_form = m.start()
            break

    experiencias = []
    if ini_exp != -1:
        bloco_exp = texto[ini_exp:ini_form]
        linhas_exp = [l.strip() for l in bloco_exp.splitlines() if l.strip()]

        # Padrões de período: 01/2020 - 12/2022 | jan/2020 a dez/2022 | 2018-2020
        pat_periodo = re.compile(
            r'(?:'
            r'\d{2}/\d{4}\s*[–\-a]\s*\d{2}/\d{4}'      # 01/2020 - 12/2022
            r'|(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*/\d{4}'
            r'.*?(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*/\d{4}'
            r'|\d{2}/\d{2}/\d{4}\s*[–\-a_]\s*\d{2}/\d{2}/\d{4}'  # 17/07/2018_11/05/2020
            r'|\d{4}\s*[–\-]\s*(?:\d{4}|atual|presente|atualmente)'  # 2018 - atual
            r')',
            re.IGNORECASE
        )

        # Palavras que indicam cargo
        pat_cargo = re.compile(
            r'\b(auxiliar|assistente|analista|técnico|tecnico|enfermeiro|recepcionista|'
            r'atendente|operador|coordenador|supervisor|gerente|diretor|ajudante|'
            r'colaborador|agente|consultor|vendedor|caixa|balconista|estoquista|'
            r'faturista|secretária|secretario|motorista|porteiro|vigilante)\b',
            re.IGNORECASE
        )

        exp_atual: dict = {}
        for linha in linhas_exp[1:]:  # pular o título da seção
            ll_lower = linha.lower()

            # Ignorar títulos de seção
            if any(re.search(p, ll_lower) for p in padroes_exp + padroes_form):
                continue

            # Detectar período
            m_per = pat_periodo.search(linha)
            if m_per:
                if exp_atual:
                    experiencias.append(exp_atual)
                exp_atual = {"periodo": re.sub(r'\s+', ' ', linha).strip(),
                             "empresa": "", "cargo": ""}
                continue

            # Detectar cargo
            if pat_cargo.search(linha) and len(linha) < 80:
                if exp_atual:
                    if not exp_atual.get("cargo"):
                        exp_atual["cargo"] = linha
                    elif not exp_atual.get("empresa"):
                        exp_atual["empresa"] = linha
                continue

            # Linha com "EMPRESA:" ou "CARGO:" explícitos
            if re.match(r'empresa\s*:', ll_lower):
                val = re.sub(r'(?i)empresa\s*:\s*', '', linha).strip()
                if exp_atual:
                    exp_atual["empresa"] = val
                continue
            if re.match(r'cargo\s*:', ll_lower):
                val = re.sub(r'(?i)cargo\s*:\s*', '', linha).strip()
                if exp_atual:
                    exp_atual["cargo"] = val
                continue
            if re.match(r'per[ií]odo\s*:', ll_lower):
                val = re.sub(r'(?i)per[ií]odo\s*:\s*', '', linha).strip()
                if exp_atual and not exp_atual.get("periodo"):
                    exp_atual["periodo"] = val
                continue

            # Linha que parece nome de empresa (maiúsculas, sem ser título)
            if (linha.isupper() or re.match(r'^[A-ZÀ-Ú][A-Za-zÀ-ú\s\.\-&]+(?:LTDA|S\.A\.|ME|EIRELI|EPP)?$', linha)) \
                    and len(linha) > 3 and len(linha) < 70:
                if exp_atual and not exp_atual.get("empresa"):
                    exp_atual["empresa"] = linha

        if exp_atual and (exp_atual.get("empresa") or exp_atual.get("cargo") or exp_atual.get("periodo")):
            experiencias.append(exp_atual)

        # Limitar a 3 experiências
        experiencias = experiencias[:3]

    # ── 4. FORMAÇÃO ──────────────────────────────────────────────
    formacao_enc = ""
    graus = [
        r'ensino\s+m[eé]dio\s+completo', r'ensino\s+m[eé]dio\s+incompleto',
        r'ensino\s+fundamental\s+completo',
        r'gradua[çc][aã]o\s+em\s+[\w\s]+',
        r'p[oó]s[\s\-]gradua[çc][aã]o\s+em\s+[\w\s]+',
        r't[eé]cnico\s+em\s+[\w\s]+',
        r'superior\s+completo', r'superior\s+incompleto',
        r'faculdade\s+de\s+[\w\s]+',
    ]
    for p in graus:
        m = re.search(p, tl)
        if m:
            # Pegar a linha completa onde foi encontrado
            inicio_linha = tl.rfind('\n', 0, m.start()) + 1
            fim_linha    = tl.find('\n', m.end())
            formacao_enc = texto[inicio_linha: fim_linha if fim_linha != -1 else m.end()+60].strip()
            formacao_enc = formacao_enc.split('\n')[0].strip()
            break

    # ── 5. MONTAR HTML ───────────────────────────────────────────
    # Cidade + telefone
    meta = []
    if cidade_enc:
        meta.append(f"<span style='font-weight:600;color:#004D40;'>{cidade_enc[:60]}</span>")
    if tel_enc:
        meta.append(f"<span style='color:#4A5568;'>{tel_enc}</span>")
    if meta:
        html.append(
            "<div style='margin-bottom:14px;font-size:13px;padding:10px 14px;"
            "background:#F5F7FA;border-radius:8px;'>"
            + "&nbsp;&nbsp;·&nbsp;&nbsp;".join(meta) + "</div>"
        )

    # Experiências
    if experiencias:
        html.append(
            "<div style='font-size:9px;font-weight:800;color:#004D40;letter-spacing:2px;"
            "text-transform:uppercase;margin-bottom:8px;'>Experiências Profissionais</div>"
        )
        for ex in experiencias:
            empresa = ex.get("empresa", "").strip()
            cargo   = ex.get("cargo",   "").strip()
            periodo = ex.get("periodo", "").strip()
            if not (empresa or cargo):
                continue
            html.append(
                f"<div style='margin-bottom:8px;padding:10px 14px;"
                f"background:#F0FAF8;border-radius:8px;border-left:3px solid #004D40;'>"
                f"{'<div style=\"font-weight:700;font-size:13px;color:#0D1B2A;\">' + empresa + '</div>' if empresa else ''}"
                f"{'<div style=\"font-size:12px;color:#4A5568;margin-top:2px;\">' + cargo + '</div>' if cargo else ''}"
                f"{'<div style=\"font-size:11px;color:#9AA5B4;margin-top:2px;\">' + periodo + '</div>' if periodo else ''}"
                f"</div>"
            )
    else:
        # Sem experiência identificada — mostra trecho bruto da seção
        if ini_exp != -1:
            trecho = texto[ini_exp:ini_exp + 600].replace('\n', '<br>')
            html.append(
                f"<div style='font-size:12px;color:#4A5568;line-height:1.7;'>{trecho}</div>"
            )
        else:
            html.append(
                "<div style='color:#9AA5B4;font-size:12px;font-style:italic;'>"
                "Experiência não identificada no documento.</div>"
            )

    # Formação
    if formacao_enc:
        html.append(
            f"<div style='margin-top:10px;padding:8px 14px;background:#F5F7FA;"
            f"border-radius:8px;font-size:12px;'>"
            f"<span style='font-weight:700;font-size:9px;color:#004D40;"
            f"letter-spacing:2px;text-transform:uppercase;'>Formação</span>"
            f"&nbsp;&nbsp;<span style='color:#4A5568;'>{formacao_enc[:100]}</span></div>"
        )

    return "\n".join(html) if html else (
        "<i style='color:#9AA5B4;font-size:12px;'>Resumo não disponível — "
        "abra o documento original para ver o currículo completo.</i>"
    )




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
        for k in ['cvs','agendados','contratados','aguardando_retorno','cvs_antigos','ex_funcionarios','favoritos']:
            st.session_state[k] = []
        st.session_state.historico_emails = set()
        st.session_state._processados     = set()
        st.session_state.candidato_foco   = None
        st.session_state.contratar_foco   = None
        st.session_state.perfil_foco      = None
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
    "AGENDADOS","AGUARDANDO RETORNO","CONTRATADOS","FAVORITOS","BANCO ANTIGOS"
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
                        b64p = base64.b64encode(c['arquivo_bytes']).decode()

                        # ── Botão de download sempre visível ──
                        st.download_button(
                            label    = f"Baixar PDF — {c['nome_arquivo']}",
                            data     = c['arquivo_bytes'],
                            file_name= c['nome_arquivo'],
                            mime     = "application/pdf",
                            use_container_width=True,
                            key      = f"dl_{c['id']}"
                        )

                        # ── Viewer via PDF.js (Mozilla CDN) — funciona no Chrome/Streamlit Cloud ──
                        import streamlit.components.v1 as components
                        pdf_viewer_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:#F8FAFB; font-family:Inter,sans-serif; }}
    #pdf-container {{
      width:100%; height:720px;
      border:1px solid #E2E6EA; border-radius:8px;
      overflow:hidden; background:#525659;
    }}
    canvas {{ display:block; margin:0 auto; }}
    #toolbar {{
      background:#323639; padding:8px 16px;
      display:flex; align-items:center; gap:12px;
      border-radius:8px 8px 0 0;
    }}
    #toolbar button {{
      background:#004D40; color:#fff; border:none;
      padding:6px 14px; border-radius:6px; cursor:pointer;
      font-size:12px; font-weight:700; letter-spacing:0.5px;
    }}
    #toolbar button:hover {{ background:#00382E; }}
    #toolbar span {{ color:#ccc; font-size:12px; }}
    #canvas-wrapper {{
      height:672px; overflow-y:auto; background:#525659;
      display:flex; flex-direction:column; align-items:center;
      padding:16px 0; gap:12px;
    }}
    .page-canvas {{ box-shadow:0 2px 8px rgba(0,0,0,0.4); }}
  </style>
</head>
<body>
<div id="pdf-container">
  <div id="toolbar">
    <button onclick="anteriorPagina()">&#8592; Anterior</button>
    <span id="info-pagina">Carregando...</span>
    <button onclick="proximaPagina()">Próxima &#8594;</button>
    <button onclick="zoomMais()">+ Zoom</button>
    <button onclick="zoomMenos()">- Zoom</button>
  </div>
  <div id="canvas-wrapper"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

  const base64 = "{b64p}";
  const raw    = atob(base64);
  const arr    = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);

  let pdfDoc    = null;
  let paginaAtual = 1;
  let escala    = 1.4;
  const wrapper = document.getElementById('canvas-wrapper');
  const info    = document.getElementById('info-pagina');

  pdfjsLib.getDocument({{ data: arr }}).promise.then(pdf => {{
    pdfDoc = pdf;
    renderPagina(paginaAtual);
  }}).catch(err => {{
    info.textContent = 'Erro ao carregar PDF: ' + err.message;
  }});

  function renderPagina(num) {{
    wrapper.innerHTML = '';
    pdfDoc.getPage(num).then(page => {{
      const vp     = page.getViewport({{ scale: escala }});
      const canvas = document.createElement('canvas');
      canvas.className = 'page-canvas';
      canvas.width  = vp.width;
      canvas.height = vp.height;
      wrapper.appendChild(canvas);
      page.render({{ canvasContext: canvas.getContext('2d'), viewport: vp }});
      info.textContent = 'Página ' + num + ' de ' + pdfDoc.numPages;
    }});
  }}

  function anteriorPagina() {{
    if (paginaAtual > 1) {{ paginaAtual--; renderPagina(paginaAtual); }}
  }}
  function proximaPagina() {{
    if (paginaAtual < pdfDoc.numPages) {{ paginaAtual++; renderPagina(paginaAtual); }}
  }}
  function zoomMais()  {{ escala = Math.min(escala + 0.2, 3.0); renderPagina(paginaAtual); }}
  function zoomMenos() {{ escala = Math.max(escala - 0.2, 0.6); renderPagina(paginaAtual); }}
</script>
</body>
</html>
"""
                        components.html(pdf_viewer_html, height=740, scrolling=False)

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
            br, _, __ = st.columns(3)
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

            # Navegação ← → + Favoritar + Aceitar em 4 colunas
            b_vol, bp, b_fav, bac = st.columns(4)
            with b_vol:
                if st.button("← VOLTAR", key=f"vol_{c['id']}", use_container_width=True):
                    cur = st.session_state.pular_idx.get(setor, 0)
                    st.session_state.pular_idx[setor] = (cur - 1) % len(fila)
                    st.rerun()
            with bp:
                if st.button("PULAR →", key=f"pul_{c['id']}", use_container_width=True):
                    cur = st.session_state.pular_idx.get(setor, 0)
                    st.session_state.pular_idx[setor] = (cur + 1) % len(fila)
                    st.rerun()
            with b_fav:
                ja_fav = any(f['id'] == c['id'] for f in st.session_state.favoritos)
                label_fav = "FAVORITADO" if ja_fav else "FAVORITAR"
                if st.button(label_fav, key=f"fav_{c['id']}", use_container_width=True):
                    if ja_fav:
                        st.session_state.favoritos = [
                            f for f in st.session_state.favoritos if f['id'] != c['id']
                        ]
                    else:
                        st.session_state.favoritos.append(c)
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

# ── ABA 8: CENTRO DE GESTÃO DE PESSOAS ────
with abas[8]:

    # ── Função interna: e-mail para NTW com anexos ──────────────
    def enviar_ntw(func: dict) -> tuple[bool, str]:
        """Envia e-mail de admissão para a NTW Doctor com todos os PDFs do dossiê."""
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.base      import MIMEBase
            from email                import encoders

            nome      = func.get('nome','').title()
            cargo     = func.get('cargo_atual','—')
            carga_h   = func.get('carga_horaria','—')
            vt        = "Sim" if func.get('vale_transporte') else "Não"
            linhas    = func.get('linhas_onibus','—')
            data_ini  = func['data_inicio_contrato'].strftime('%d/%m/%Y') \
                        if func.get('data_inicio_contrato') else '—'
            data_exp  = func['data_inicio_experiencia'].strftime('%d/%m/%Y') \
                        if func.get('data_inicio_experiencia') else data_ini

            corpo = (
                f"Bom dia,\n\n"
                f"Seguem documentos para admissão a partir de {data_ini}.\n\n"
                f"Colaborador: {nome}\n"
                f"Cargo: {cargo}\n"
                f"Carga Horária: {carga_h}\n"
                f"Início da Experiência: {data_exp}\n"
                f"Vale Transporte: {vt}"
                + (f"\nLinhas: {linhas}" if vt == "Sim" else "")
                + f"\n\nAtenciosamente,\nEquipe de RH — Hospital de Olhos Vale do Aço"
            )

            msg = MIMEMultipart()
            msg['Subject'] = f"Admissão - {nome} - HOVA"
            msg['From']    = EMAIL_CONTA
            msg['To']      = "pessoal.expert@ntwdoctor.com.br"
            msg['Bcc']     = EMAIL_CONTA
            msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

            # Anexar todos os PDFs do dossiê
            docs = func.get('documentos', {})
            for nome_doc, bytes_doc in docs.items():
                if bytes_doc:
                    part = MIMEBase('application','octet-stream')
                    part.set_payload(bytes_doc)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    f'attachment; filename="{nome_doc}.pdf"')
                    msg.attach(part)

            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as s:
                s.login(EMAIL_CONTA, SENHA_CONTA)
                s.send_message(msg)
            return True, f"E-mail enviado para pessoal.expert@ntwdoctor.com.br"
        except Exception as e:
            return False, f"Erro ao enviar: {e}"

    # ── CSS ciano para este módulo ───────────────────────────────
    st.markdown("""
    <style>
    .ciano { color: #004D40 !important; }
    .btn-ciano div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg,#004D40,#26A69A) !important;
        box-shadow: 0 2px 10px rgba(0,77,64,0.25) !important;
    }
    .btn-ciano div[data-testid="stButton"] button[kind="primary"]:hover {
        background: #003329 !important;
    }
    .dossie-header {
        background: linear-gradient(160deg,#F2FAF8,#E6F4F1);
        border: 1px solid #B2DFDB;
        border-radius: 20px;
        padding: 36px 40px 28px;
        text-align: center;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .dossie-header::before {
        content:''; position:absolute; left:0; top:0; bottom:0;
        width:5px; background:linear-gradient(180deg,#004D40,#26A69A);
        border-radius:20px 0 0 20px;
    }
    .func-avatar-xl {
        width:110px; height:110px; border-radius:50%;
        background:linear-gradient(145deg,#004D40,#26A69A);
        color:#FFF; display:flex; justify-content:center; align-items:center;
        font-size:34px; font-weight:900;
        margin:0 auto 16px auto;
        box-shadow:0 6px 24px rgba(0,77,64,0.3);
        letter-spacing:1px;
    }
    .func-avatar-xl-foto {
        width:110px; height:110px; border-radius:50%;
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        border:4px solid #B2DFDB;
        margin:0 auto 16px auto;
        box-shadow:0 6px 24px rgba(0,0,0,0.15);
    }
    .ntw-box {
        background:#F2FAF8; border:1.5px solid #004D40;
        border-radius:14px; padding:22px 26px; margin-top:16px;
    }
    .func-card-v2 {
        background:#FFFFFF; border:1px solid #E2E6EA; border-radius:18px;
        padding:28px 16px 20px; text-align:center;
        box-shadow:0 2px 12px rgba(0,0,0,0.05);
        transition:transform 0.18s,box-shadow 0.18s;
        animation:fadeUp 0.3s ease;
    }
    .func-card-v2:hover { transform:translateY(-4px); box-shadow:0 8px 24px rgba(8,145,178,0.12); }
    </style>
    """, unsafe_allow_html=True)

    # ── Sub-navegação ────────────────────────────────────────────
    sub = st.radio("", ["Equipe Ativa", "Ex-Colaboradores"],
                   horizontal=True, label_visibility="collapsed", key="sub_func")

    # ── Expander: cadastrar colaborador já ativo ─────────────────
    with st.expander("Cadastrar Colaborador Existente"):
        with st.form("form_colab_antigo", clear_on_submit=True):
            st.markdown(
                "<div style='font-size:12px;font-weight:800;color:#004D40;"
                "letter-spacing:2px;text-transform:uppercase;margin-bottom:16px;'>"
                "Novo Colaborador</div>", unsafe_allow_html=True)

            ca1, ca2 = st.columns(2)
            ca_nome  = ca1.text_input("Nome completo *")
            ca_cargo = ca2.text_input("Cargo *", placeholder="Ex: Recepcionista")
            ca3, ca4 = st.columns(2)
            ca_setor = ca3.selectbox("Setor",["TRIAGEM GERAL","RECEPCAO E ATENDIMENTO",
                                               "TECNICO E ENFERMAGEM","ADMINISTRATIVO",
                                               "FATURAMENTO","JOVEM APRENDIZ"])
            ca_adm   = ca4.date_input("Data de admissão", value=datetime.date.today(),
                                       key="ca_adm2")
            ca5, ca6 = st.columns(2)
            ca_tel   = ca5.text_input("Telefone / WhatsApp", placeholder="31999990000")
            ca_email = ca6.text_input("E-mail")
            ca7, ca8 = st.columns(2)
            ca_unif  = ca7.text_input("Nº do Uniforme", placeholder="Ex: P / M / G")
            ca_carga = ca8.text_input("Carga Horária", placeholder="Ex: 6h semanais")
            ca_vt    = st.checkbox("Utiliza Vale Transporte")
            ca_linhas= st.text_input("Linhas de Ônibus", placeholder="Ex: 201, 405",
                                      disabled=not ca_vt)
            ca_foto  = st.file_uploader("Foto do colaborador (opcional)",
                                         type=["jpg","jpeg","png"],
                                         key="ca_foto_upload")
            ca_obs   = st.text_area("Observações", height=70,
                                     placeholder="Certificações, CNH, anotações...")

            st.markdown("<div class='btn-ciano'>", unsafe_allow_html=True)
            ok_ca = st.form_submit_button("CADASTRAR", type="primary",
                                           use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if ok_ca:
            if ca_nome and ca_cargo:
                foto_bytes = ca_foto.read() if ca_foto else None
                novo_func = {
                    "id":   str(int(time.time()*1000)),
                    "nome": ca_nome.upper().strip(),
                    "setor": ca_setor,
                    "email": ca_email.lower().strip(),
                    "telefone": ''.join(filter(str.isdigit, ca_tel)),
                    "data_inicio_contrato":    ca_adm,
                    "data_inicio_experiencia": ca_adm,
                    "hora_inicio_contrato":    datetime.time(8,0),
                    "cargo_atual":  ca_cargo.strip(),
                    "carga_horaria": ca_carga.strip(),
                    "num_uniforme":  ca_unif.strip(),
                    "vale_transporte": ca_vt,
                    "linhas_onibus": ca_linhas.strip(),
                    "observacoes":   ca_obs.strip(),
                    "foto":   foto_bytes,
                    "manual": True,
                    "email_admissao_enviado": False,
                    "documentos": {},   # {nome: bytes_pdf}
                    "docs_check": {     # checklist
                        "RG": False, "CPF": False, "PIS": False,
                        "Comprovante de Residência": False,
                        "Diploma": False, "Cartão de Vacina": False,
                        "Certidão de Casamento": False,
                        "Certidão de Nascimento dos Filhos": False,
                        "Foto 3x4": False,
                    },
                }
                st.session_state.contratados.append(novo_func)
                salvar_json()
                st.success(f"{ca_nome.upper()} cadastrado.")
                st.rerun()
            else:
                st.error("Nome e cargo são obrigatórios.")

    st.write("")

    # ════════════════════════════════════════════════════════════
    # EQUIPE ATIVA
    # ════════════════════════════════════════════════════════════
    if sub == "Equipe Ativa":
        ativos = _busca(st.session_state.contratados, termo)
        ativos = sorted(ativos, key=lambda x: x.get('data_inicio_contrato') or datetime.date.min)

        if not ativos:
            st.markdown('<div class="empty"><div class="e-title">NENHUM COLABORADOR ATIVO</div>'
                        '<div class="e-sub">Use o painel acima para cadastrar a equipe.</div></div>',
                        unsafe_allow_html=True)

        # ── DOSSIÊ ABERTO ────────────────────────────────────────
        elif st.session_state.perfil_foco:
            func = next((f for f in st.session_state.contratados
                         if f['id'] == st.session_state.perfil_foco), None)

            if not func:
                st.session_state.perfil_foco = None
                st.rerun()
            else:
                # Garantir campos novos em registros antigos
                func.setdefault('documentos', {})
                func.setdefault('docs_check', {
                    "RG":False,"CPF":False,"PIS":False,
                    "Comprovante de Residência":False,"Diploma":False,
                    "Cartão de Vacina":False,"Certidão de Casamento":False,
                    "Certidão de Nascimento dos Filhos":False,"Foto 3x4":False,
                })
                func.setdefault('carga_horaria','')
                func.setdefault('num_uniforme','')
                func.setdefault('vale_transporte',False)
                func.setdefault('linhas_onibus','')
                func.setdefault('data_inicio_experiencia',
                                func.get('data_inicio_contrato'))
                func.setdefault('ntw_enviado', False)

                ini_f = func['data_inicio_contrato'].strftime('%d/%m/%Y') \
                        if func.get('data_inicio_contrato') else '—'

                # ── Header do perfil ─────────────────────────────
                if func.get('foto'):
                    b64f    = base64.b64encode(func['foto']).decode()
                    av_html = (f"<div class='func-avatar-xl-foto'"
                               f" style='background-image:url(\"data:image/jpeg;"
                               f"base64,{b64f}\");'></div>")
                else:
                    av_html = (f"<div class='func-avatar-xl'>"
                               f"{iniciais(func['nome'])}</div>")

                ntw_badge = (
                    "<span style='background:#DCFCE7;color:#166534;font-size:10px;"
                    "font-weight:700;padding:3px 10px;border-radius:20px;"
                    "letter-spacing:1px;'>NTW ENVIADO</span>"
                    if func.get('ntw_enviado') else ""
                )

                st.markdown(
                    f"<div class='dossie-header'>"
                    f"{av_html}"
                    f"<div style='font-size:24px;font-weight:900;color:#0D1B2A;"
                    f"margin-bottom:4px;'>{func['nome']}</div>"
                    f"<div style='font-size:12px;color:#004D40;font-weight:700;"
                    f"letter-spacing:1.5px;text-transform:uppercase;'>"
                    f"{func.get('cargo_atual','—')}</div>"
                    f"<div style='font-size:11px;color:#9AA5B4;margin-top:6px;'>"
                    f"Admitido em {ini_f} &nbsp;·&nbsp; {func.get('setor','—')}"
                    f"&nbsp;&nbsp;{ntw_badge}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # ── 3 colunas de ação rápida ─────────────────────
                qa1, qa2, qa3 = st.columns(3)
                with qa1:
                    tel_wa = ''.join(filter(str.isdigit,
                                            func.get('telefone','')))
                    if tel_wa:
                        msg_wa = (f"Olá {func['nome'].title()}, aqui é o RH do HOVA. "
                                  f"Verificamos que há documentos pendentes no seu dossiê. "
                                  f"Pode confirmar o envio?")
                        url_wa = (f"https://wa.me/55{tel_wa}?"
                                  f"text={urllib.parse.quote(msg_wa)}")
                        st.markdown(
                            f'<a href="{url_wa}" target="_blank" class="wa-btn"'
                            f' style="display:block;text-align:center;">'
                            f'WhatsApp Colaborador</a>',
                            unsafe_allow_html=True)
                with qa2:
                    # WhatsApp Paula
                    msg_paula = (
                        f"Paula, os documentos de admissão de "
                        f"{func['nome'].title()} estão disponíveis no sistema. "
                        f"Cargo: {func.get('cargo_atual','—')}.")
                    url_paula = (f"https://wa.me/5531886000023?"
                                 f"text={urllib.parse.quote(msg_paula)}")
                    st.markdown(
                        f'<a href="{url_paula}" target="_blank"'
                        f' style="display:block;text-align:center;'
                        f'background:#00A884;color:#FFF;padding:13px 18px;'
                        f'border-radius:9px;font-size:11px;font-weight:700;'
                        f'letter-spacing:1px;text-transform:uppercase;'
                        f'text-decoration:none;">'
                        f'WhatsApp Paula</a>',
                        unsafe_allow_html=True)
                with qa3:
                    if st.button("VOLTAR A EQUIPE", key="voltar_grid",
                                 use_container_width=True):
                        st.session_state.perfil_foco = None
                        st.rerun()

                st.write("")

                # ── TABS internas do dossiê ──────────────────────
                tab_dados, tab_docs, tab_ntw = st.tabs([
                    "Dados & RH", "Documentos", "Enviar para Contabilidade"
                ])

                # ── TAB 1: DADOS ─────────────────────────────────
                with tab_dados:
                    with st.form(f"form_dados_{func['id']}"):
                        st.markdown(
                            "<div style='font-size:10px;font-weight:800;"
                            "color:#004D40;letter-spacing:2px;"
                            "text-transform:uppercase;margin-bottom:16px;'>"
                            "Informações Pessoais e Contratuais</div>",
                            unsafe_allow_html=True)

                        r1c1, r1c2 = st.columns(2)
                        novo_nome   = r1c1.text_input("Nome",  value=func.get('nome',''))
                        novo_cargo  = r1c2.text_input("Cargo", value=func.get('cargo_atual',''))

                        r2c1, r2c2 = st.columns(2)
                        novo_tel    = r2c1.text_input("Telefone/WhatsApp",
                                                      value=func.get('telefone',''))
                        novo_email  = r2c2.text_input("E-mail", value=func.get('email',''))

                        r3c1, r3c2 = st.columns(2)
                        SETORES_LIST = ["TRIAGEM GERAL","RECEPCAO E ATENDIMENTO",
                                        "TECNICO E ENFERMAGEM","ADMINISTRATIVO",
                                        "FATURAMENTO","JOVEM APRENDIZ"]
                        novo_setor  = r3c1.selectbox(
                            "Setor", SETORES_LIST,
                            index=SETORES_LIST.index(func['setor'])
                                  if func.get('setor') in SETORES_LIST else 0)
                        novo_unif   = r3c2.text_input("Nº Uniforme",
                                                      value=func.get('num_uniforme',''))

                        r4c1, r4c2 = st.columns(2)
                        novo_adm    = r4c1.date_input(
                            "Data de Admissão",
                            value=func.get('data_inicio_contrato') or datetime.date.today())
                        novo_exp    = r4c2.date_input(
                            "Início da Experiência",
                            value=func.get('data_inicio_experiencia')
                                  or func.get('data_inicio_contrato')
                                  or datetime.date.today())

                        r5c1, r5c2 = st.columns(2)
                        novo_carga  = r5c1.text_input("Carga Horária",
                                                      value=func.get('carga_horaria',''),
                                                      placeholder="Ex: 6h semanais")
                        novo_vt     = r5c2.checkbox("Vale Transporte",
                                                     value=func.get('vale_transporte',False))
                        novo_linhas = st.text_input("Linhas de Ônibus",
                                                    value=func.get('linhas_onibus',''),
                                                    placeholder="Ex: 201, 405",
                                                    disabled=not novo_vt)

                        # Upload de foto
                        nova_foto_up = st.file_uploader(
                            "Atualizar foto do perfil",
                            type=["jpg","jpeg","png"],
                            key=f"foto_edit_{func['id']}")

                        novo_obs = st.text_area(
                            "Observações de Desempenho",
                            value=func.get('observacoes',''), height=90,
                            placeholder="Feedbacks, advertências, elogios...")

                        st.markdown("<div style='height:8px;'></div>",
                                    unsafe_allow_html=True)
                        sb1, sb2, sb3 = st.columns(3)
                        salvar_ok   = sb1.form_submit_button(
                            "SALVAR", type="primary", use_container_width=True)
                        fechar_ok   = sb2.form_submit_button(
                            "FECHAR", use_container_width=True)
                        desligar_ok = sb3.form_submit_button(
                            "DESLIGAR", use_container_width=True)

                    if salvar_ok:
                        func['nome']               = novo_nome.upper().strip()
                        func['cargo_atual']        = novo_cargo.strip()
                        func['telefone']           = ''.join(filter(str.isdigit, novo_tel))
                        func['email']              = novo_email.lower().strip()
                        func['setor']              = novo_setor
                        func['num_uniforme']       = novo_unif.strip()
                        func['data_inicio_contrato']    = novo_adm
                        func['data_inicio_experiencia'] = novo_exp
                        func['carga_horaria']      = novo_carga.strip()
                        func['vale_transporte']    = novo_vt
                        func['linhas_onibus']      = novo_linhas.strip()
                        func['observacoes']        = novo_obs.strip()
                        if nova_foto_up:
                            func['foto'] = nova_foto_up.read()
                        salvar_json()
                        st.success("Dados salvos.")
                        st.rerun()

                    if fechar_ok:
                        st.session_state.perfil_foco = None
                        st.rerun()

                    if desligar_ok:
                        func['data_desligamento'] = datetime.date.today()
                        st.session_state.ex_funcionarios.append(func)
                        st.session_state.contratados.remove(func)
                        st.session_state.perfil_foco = None
                        salvar_json()
                        st.success(f"{func['nome']} desligado e movido para Histórico.")
                        st.rerun()

                # ── TAB 2: DOCUMENTOS ────────────────────────────
                with tab_docs:
                    st.markdown(
                        "<div style='font-size:10px;font-weight:800;color:#004D40;"
                        "letter-spacing:2px;text-transform:uppercase;"
                        "margin-bottom:16px;'>Checklist de Documentos</div>",
                        unsafe_allow_html=True)

                    DOCS_LISTA = [
                        "RG","CPF","PIS","Comprovante de Residência",
                        "Diploma","Cartão de Vacina",
                        "Certidão de Casamento",
                        "Certidão de Nascimento dos Filhos","Foto 3x4",
                    ]

                    checks_atuais = func.get('docs_check', {})
                    novos_checks  = {}
                    col_a, col_b = st.columns(2)
                    for idx, doc_nome in enumerate(DOCS_LISTA):
                        col = col_a if idx % 2 == 0 else col_b
                        with col:
                            val = st.checkbox(
                                doc_nome,
                                value=checks_atuais.get(doc_nome, False),
                                key=f"chk_{func['id']}_{doc_nome}")
                            novos_checks[doc_nome] = val

                    # Atualizar checklist em tempo real
                    func['docs_check'] = novos_checks

                    # Resumo
                    total_docs = len(DOCS_LISTA)
                    ok_docs    = sum(novos_checks.values())
                    pct        = int(ok_docs / total_docs * 100)
                    cor_pct    = "#166534" if pct == 100 else ("#004D40" if pct >= 50 else "#92540A")
                    st.markdown(
                        f"<div style='margin:16px 0 20px;padding:12px 18px;"
                        f"background:#F8FAFB;border-radius:10px;border:1px solid #E2E6EA;"
                        f"font-size:13px;color:{cor_pct};font-weight:700;'>"
                        f"{ok_docs} de {total_docs} documentos recebidos ({pct}%)"
                        f"</div>", unsafe_allow_html=True)

                    # Upload de PDFs
                    st.markdown(
                        "<div style='font-size:10px;font-weight:800;color:#004D40;"
                        "letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;'>"
                        "Adicionar PDF ao Dossiê</div>", unsafe_allow_html=True)

                    doc_up_nome = st.selectbox(
                        "Documento:", DOCS_LISTA, key=f"doc_sel_{func['id']}")
                    doc_up_file = st.file_uploader(
                        "Selecionar PDF", type=["pdf"],
                        key=f"doc_up_{func['id']}")

                    if st.button("SALVAR DOCUMENTO",
                                 key=f"salvar_doc_{func['id']}",
                                 type="primary", use_container_width=True):
                        if doc_up_file:
                            func['documentos'][doc_up_nome] = doc_up_file.read()
                            func['docs_check'][doc_up_nome] = True
                            salvar_json()
                            st.success(f"{doc_up_nome} salvo no dossiê.")
                            st.rerun()
                        else:
                            st.warning("Selecione um arquivo PDF primeiro.")

                    # Listar PDFs já enviados
                    if func.get('documentos'):
                        st.markdown(
                            "<div style='font-size:10px;font-weight:800;color:#004D40;"
                            "letter-spacing:2px;text-transform:uppercase;"
                            "margin:16px 0 8px;'>PDFs no Dossiê</div>",
                            unsafe_allow_html=True)
                        for nome_doc, bytes_doc in func['documentos'].items():
                            if bytes_doc:
                                dc1, dc2 = st.columns([3,1])
                                dc1.markdown(
                                    f"<div style='font-size:13px;color:#0D1B2A;"
                                    f"font-weight:600;padding:8px 0;'>"
                                    f"{nome_doc}</div>",
                                    unsafe_allow_html=True)
                                dc2.download_button(
                                    "Baixar", bytes_doc,
                                    file_name=f"{nome_doc}_{func['nome']}.pdf",
                                    mime="application/pdf",
                                    key=f"dwn_{func['id']}_{nome_doc}",
                                    use_container_width=True)

                    salvar_json()  # salvar checklist

                # ── TAB 3: ENVIAR PARA NTW ───────────────────────
                with tab_ntw:
                    st.markdown(
                        "<div class='ntw-box'>"
                        "<div style='font-size:14px;font-weight:800;color:#004D40;"
                        "margin-bottom:4px;'>Encaminhar para Contabilidade</div>"
                        "<div style='font-size:12px;color:#4A5568;'>"
                        "Envia e-mail para <b>pessoal.expert@ntwdoctor.com.br</b> "
                        "com os dados de admissão e todos os PDFs do dossiê anexados."
                        "</div></div>",
                        unsafe_allow_html=True)

                    st.write("")
                    with st.form(f"form_ntw_{func['id']}"):
                        n1, n2 = st.columns(2)
                        ntw_cargo  = n1.text_input(
                            "Cargo (confirmar)",
                            value=func.get('cargo_atual',''))
                        ntw_carga  = n2.text_input(
                            "Carga Horária",
                            value=func.get('carga_horaria',''),
                            placeholder="Ex: 44h semanais")
                        n3, n4 = st.columns(2)
                        ntw_adm = n3.date_input(
                            "Data de início",
                            value=func.get('data_inicio_contrato') or datetime.date.today())
                        ntw_exp = n4.date_input(
                            "Início da Experiência",
                            value=func.get('data_inicio_experiencia')
                                  or func.get('data_inicio_contrato')
                                  or datetime.date.today())
                        ntw_vt  = st.checkbox(
                            "Vale Transporte",
                            value=func.get('vale_transporte', False))
                        ntw_linhas = st.text_input(
                            "Linhas", value=func.get('linhas_onibus',''),
                            disabled=not ntw_vt)

                        # Mostrar PDFs que serão anexados
                        docs_disponiveis = [k for k,v in func.get('documentos',{}).items() if v]
                        if docs_disponiveis:
                            st.markdown(
                                f"<div style='font-size:12px;color:#004D40;"
                                f"font-weight:600;margin-top:8px;'>"
                                f"PDFs que serão anexados: "
                                f"{', '.join(docs_disponiveis)}</div>",
                                unsafe_allow_html=True)
                        else:
                            st.markdown(
                                "<div style='font-size:12px;color:#92540A;"
                                "font-weight:600;margin-top:8px;'>"
                                "Nenhum PDF no dossiê ainda. Adicione na aba Documentos.</div>",
                                unsafe_allow_html=True)

                        enviar_ntw_ok = st.form_submit_button(
                            "ENVIAR PARA NTW DOCTOR",
                            type="primary", use_container_width=True)

                    if enviar_ntw_ok:
                        # Atualizar dados antes de enviar
                        func['cargo_atual']             = ntw_cargo.strip()
                        func['carga_horaria']           = ntw_carga.strip()
                        func['data_inicio_contrato']    = ntw_adm
                        func['data_inicio_experiencia'] = ntw_exp
                        func['vale_transporte']         = ntw_vt
                        func['linhas_onibus']           = ntw_linhas.strip()

                        with st.spinner("Enviando para NTW Doctor..."):
                            ok_ntw, msg_ntw = enviar_ntw(func)

                        if ok_ntw:
                            func['ntw_enviado'] = True
                            salvar_json()
                            st.markdown(
                                f"<div class='notif notif-ok'>{msg_ntw}</div>",
                                unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f"<div class='notif notif-warn'>{msg_ntw}</div>",
                                unsafe_allow_html=True)

        # ── GRID DE CARDS — estilo referência ────────────────────
        else:
            n_ativos = len(ativos)
            st.markdown(
                f"<div style='font-size:12px;color:#8A94A6;margin-bottom:24px;'>"
                f"<b style='color:#004D40;font-size:26px;font-weight:900;letter-spacing:-1px;'>"
                f"{n_ativos}</b> colaborador(es) ativo(s)</div>",
                unsafe_allow_html=True)

            # CSS específico do grid — injetado uma vez
            st.markdown("""
            <style>
            .hova-card {
                background: #FFFFFF;
                border-radius: 18px;
                padding: 28px 16px 20px;
                text-align: center;
                box-shadow: 0 3px 16px rgba(0,0,0,0.08);
                border: 1px solid #E8EAED;
                transition: box-shadow 0.2s, transform 0.2s;
                margin-bottom: 4px;
            }
            .hova-card:hover {
                box-shadow: 0 8px 28px rgba(0,77,64,0.14);
                transform: translateY(-3px);
            }
            .hova-card-foto {
                width: 110px; height: 110px;
                border-radius: 50%;
                object-fit: cover;
                object-position: center top;
                border: 4px solid #E0F2F1;
                display: block;
                margin: 0 auto 16px auto;
                box-shadow: 0 4px 16px rgba(0,0,0,0.14);
            }
            .hova-card-iniciais {
                width: 110px; height: 110px;
                border-radius: 50%;
                background: linear-gradient(145deg, #004D40, #26A69A);
                color: #FFF;
                display: flex; justify-content: center; align-items: center;
                font-size: 36px; font-weight: 900;
                margin: 0 auto 16px auto;
                box-shadow: 0 4px 18px rgba(0,77,64,0.28);
                letter-spacing: 1px;
            }
            .hova-card-nome {
                font-size: 15px; font-weight: 800;
                color: #0D1B2A; text-transform: uppercase;
                letter-spacing: 0.8px; line-height: 1.2;
                margin-bottom: 10px;
            }
            .hova-card-cargo-bar {
                background: #003329;
                color: #FFFFFF;
                font-size: 11px; font-weight: 700;
                letter-spacing: 1.5px; text-transform: uppercase;
                padding: 8px 12px;
                border-radius: 8px;
                margin-bottom: 12px;
            }
            .hova-card-tel {
                font-size: 13px;
                color: #2D3748;
                margin-bottom: 10px;
                font-weight: 600;
            }
            .hova-card-data {
                font-size: 11px;
                color: #718096;
                margin-bottom: 4px;
                font-weight: 500;
            }
            .hova-card-ntw {
                background: #DCFCE7; color: #166534;
                font-size: 9px; font-weight: 700;
                padding: 3px 10px; border-radius: 20px;
                display: inline-block; margin-bottom: 8px;
                letter-spacing: 1px;
            }
            </style>
            """, unsafe_allow_html=True)

            N = 4
            for row_start in range(0, n_ativos, N):
                row  = ativos[row_start:row_start + N]
                cols = st.columns(N)

                for j, f in enumerate(row):
                    with cols[j]:
                        ini_f      = (f['data_inicio_contrato'].strftime('%d/%m/%Y')
                                      if f.get('data_inicio_contrato') else '—')
                        cargo_exib = (f.get('cargo_atual') or f.get('setor','—')).upper()
                        tel_fmt    = f.get('telefone','')
                        # Formatar telefone: 31999990000 → 31 9 9999-0000
                        if len(tel_fmt) == 11:
                            tel_fmt = f"{tel_fmt[:2]} {tel_fmt[2]} {tel_fmt[3:7]}-{tel_fmt[7:]}"
                        elif len(tel_fmt) == 10:
                            tel_fmt = f"{tel_fmt[:2]} {tel_fmt[2:6]}-{tel_fmt[6:]}"

                        # Avatar
                        if f.get('foto'):
                            b64f = base64.b64encode(f['foto']).decode()
                            av   = (f"<img src='data:image/jpeg;base64,{b64f}'"
                                    f" class='hova-card-foto'>")
                        else:
                            av   = (f"<div class='hova-card-iniciais'>"
                                    f"{iniciais(f['nome'])}</div>")

                        ntw_html = ("<div class='hova-card-ntw'>NTW ENVIADO</div>"
                                    if f.get('ntw_enviado') else "")
                        tel_html = (f"<div class='hova-card-tel'>{tel_fmt}</div>"
                                    if tel_fmt else "")

                        st.markdown(
                            f"<div class='hova-card'>"
                            f"{av}"
                            f"<div class='hova-card-nome'>{f['nome']}</div>"
                            f"<div class='hova-card-cargo-bar'>{cargo_exib}</div>"
                            f"{tel_html}"
                            f"{ntw_html}"
                            f"<div class='hova-card-data'>Desde {ini_f}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown("<div style='height:4px;'></div>",
                                    unsafe_allow_html=True)
                        if st.button("ACESSAR PERFIL",
                                     key=f"perfil_{f['id']}",
                                     use_container_width=True,
                                     type="primary"):
                            st.session_state.perfil_foco = f['id']
                            st.rerun()

                # Preencher colunas vazias
                for j in range(len(row), N):
                    cols[j].empty()
                st.write("")


    # ════════════════════════════════════════════════════════════
    # EX-COLABORADORES
    # ════════════════════════════════════════════════════════════
    else:
        ex_list = _busca(st.session_state.ex_funcionarios, termo)
        ex_list = sorted(ex_list,
                         key=lambda x: x.get('data_desligamento') or datetime.date.min,
                         reverse=True)

        if not ex_list:
            st.markdown('<div class="empty"><div class="e-title">NENHUM REGISTRO</div>'
                        '<div class="e-sub">O histórico de ex-colaboradores aparecerá aqui.</div></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='font-size:12px;color:#8A94A6;margin-bottom:16px;'>"
                f"<b style='color:#9AA5B4;font-size:18px;'>{len(ex_list)}</b>"
                f" ex-colaborador(es)</div>", unsafe_allow_html=True)

            for f in ex_list:
                adm_f = f['data_inicio_contrato'].strftime('%d/%m/%Y') \
                        if f.get('data_inicio_contrato') else '—'
                dem_f = f['data_desligamento'].strftime('%d/%m/%Y') \
                        if f.get('data_desligamento') else '—'
                docs_count = len([v for v in f.get('documentos',{}).values() if v])

                xc1, xc2 = st.columns([4,1])
                with xc1:
                    st.markdown(
                        f"<div class='ex-func-card'>"
                        f"<div style='font-weight:700;font-size:14px;color:#4A5568;'>"
                        f"{f['nome']}</div>"
                        f"<div style='font-size:12px;color:#9AA5B4;margin-top:3px;'>"
                        f"{f.get('cargo_atual') or f.get('setor','—')}"
                        f" &nbsp;·&nbsp; Admissão: {adm_f}"
                        f" &nbsp;·&nbsp; Desligamento: {dem_f}"
                        f" &nbsp;·&nbsp; {docs_count} doc(s) no dossiê"
                        f"</div></div>",
                        unsafe_allow_html=True)
                with xc2:
                    # Botão para reativar
                    if st.button("Reativar", key=f"reativar_{f['id']}",
                                 use_container_width=True):
                        f.pop('data_desligamento', None)
                        st.session_state.contratados.append(f)
                        st.session_state.ex_funcionarios.remove(f)
                        salvar_json()
                        st.success(f"{f['nome']} reativado.")
                        st.rerun()

# ── ABA 9: FAVORITOS ──────────────────────
with abas[9]:
    favs = _busca(st.session_state.favoritos, termo)
    n_fav = len(favs)

    st.markdown(
        f"<div style='font-size:12px;color:#8A94A6;margin-bottom:20px;'>"
        f"<b style='color:#004D40;font-size:22px;font-weight:900;'>{n_fav}</b>"
        f" currículo(s) favoritado(s)</div>",
        unsafe_allow_html=True)

    if not favs:
        st.markdown(
            '<div class="empty">'
            '<div class="e-title">NENHUM FAVORITO</div>'
            '<div class="e-sub">Durante a triagem, clique em FAVORITAR para guardar '
            'candidatos que te interessam.</div></div>',
            unsafe_allow_html=True)
    else:
        N = 4
        for row_start in range(0, n_fav, N):
            row  = favs[row_start:row_start+N]
            cols = st.columns(N)
            for j, c in enumerate(row):
                with cols[j]:
                    cargo_exib = (c.get('setor','—')).upper()
                    tel_fmt    = c.get('telefone','')
                    if len(tel_fmt) == 11:
                        tel_fmt = f"{tel_fmt[:2]} {tel_fmt[2]} {tel_fmt[3:7]}-{tel_fmt[7:]}"

                    if c.get('foto'):
                        b64f = base64.b64encode(c['foto']).decode()
                        av   = (f"<div style='width:88px;height:88px;border-radius:50%;"
                                f"background-image:url(\"data:image/jpeg;base64,{b64f}\");"
                                f"background-size:cover;background-position:center;"
                                f"border:3px solid #004D40;"
                                f"margin:0 auto 14px auto;"
                                f"box-shadow:0 4px 14px rgba(0,77,64,0.2);'></div>")
                    else:
                        av = (f"<div style='width:88px;height:88px;border-radius:50%;"
                              f"background:linear-gradient(145deg,#004D40,#26A69A);"
                              f"color:#FFF;display:flex;justify-content:center;"
                              f"align-items:center;font-size:28px;font-weight:900;"
                              f"margin:0 auto 14px auto;"
                              f"box-shadow:0 4px 14px rgba(0,77,64,0.25);'>"
                              f"{iniciais(c['nome'])}</div>")

                    st.markdown(
                        f"<div class='hova-card'>"
                        f"{av}"
                        f"<div class='hova-card-nome'>{c['nome']}</div>"
                        f"<div class='hova-card-cargo-bar'>{cargo_exib}</div>"
                        f"<div class='hova-card-tel'>{tel_fmt}</div>"
                        f"<div class='hova-card-data'>{c.get('data','—')}</div>"
                        f"</div>",
                        unsafe_allow_html=True)

                    fc1, fc2 = st.columns(2)
                    with fc1:
                        # Remover dos favoritos
                        if st.button("Remover", key=f"desfav_{c['id']}",
                                     use_container_width=True):
                            st.session_state.favoritos = [
                                f for f in st.session_state.favoritos
                                if f['id'] != c['id']
                            ]
                            st.rerun()
                    with fc2:
                        # Aceitar direto dos favoritos
                        if st.button("ACEITAR", key=f"fav_acc_{c['id']}",
                                     type="primary", use_container_width=True):
                            st.session_state.candidato_foco = c['id']
                            st.rerun()

            for j in range(len(row), N):
                cols[j].empty()
            st.write("")

# ── ABA 10: BANCO ANTIGOS ─────────────────
with abas[10]:
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

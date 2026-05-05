import os
import io
import json
import base64
import datetime
import difflib
import math
import re
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import plotly.graph_objects as go
from scipy.stats import poisson

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

# ── PWA / Mobile: icone (caricate prima di set_page_config per usarle come page_icon) ──
def _load_icon_b64(path: str):
    try:
        import base64
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return ""

_BASE_DIR  = os.path.dirname(__file__) if "__file__" in globals() else "."
_ICON_PATH_192 = os.path.join(_BASE_DIR, "icon-192.png")
_ICON_PATH_512 = os.path.join(_BASE_DIR, "icon-512.png")
_ICON_192 = _load_icon_b64(_ICON_PATH_192)
_ICON_512 = _load_icon_b64(_ICON_PATH_512)

# page_icon: se trovo il PNG locale lo uso, altrimenti fallback emoji 🏀
_PAGE_ICON = _ICON_PATH_192 if os.path.exists(_ICON_PATH_192) else "🏀"

st.set_page_config(page_title="NBA Whale Pro",
                   page_icon=_PAGE_ICON,
                   layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"About": "NBA Whale Pro · analisi statistica NBA"})

# ── PWA / Mobile (manifest inline + meta) ──────────────────────────────────
_icon_entries = []
if _ICON_192:
    _icon_entries.append('{"src":"data:image/png;base64,' + _ICON_192 + '","sizes":"192x192","type":"image/png","purpose":"any maskable"}')
if _ICON_512:
    _icon_entries.append('{"src":"data:image/png;base64,' + _ICON_512 + '","sizes":"512x512","type":"image/png","purpose":"any maskable"}')

# iOS/Android PWA cache bust + icone pubbliche (se disponibili) per evitare fallback Streamlit
_PWA_ICON_192_URL = os.environ.get(
    "PWA_ICON_192_URL",
    "https://raw.githubusercontent.com/victoriacaraman/nba-whale-pro/main/icon-192.png",
).strip()
_PWA_ICON_512_URL = os.environ.get(
    "PWA_ICON_512_URL",
    "https://raw.githubusercontent.com/victoriacaraman/nba-whale-pro/main/icon-512.png",
).strip()
# VERSION è definita più avanti: qui usiamo un cache tag statico sicuro
_PWA_CACHE_TAG = "v=1"

if _PWA_ICON_192_URL and _PWA_ICON_512_URL:
    _manifest_icons = (
        f'{{"src":"{_PWA_ICON_192_URL}?{_PWA_CACHE_TAG}","sizes":"192x192","type":"image/png","purpose":"any maskable"}},'
        f'{{"src":"{_PWA_ICON_512_URL}?{_PWA_CACHE_TAG}","sizes":"512x512","type":"image/png","purpose":"any maskable"}}'
    )
else:
    _manifest_icons = ",".join(_icon_entries)

_PWA_MANIFEST = (
    '{'
    '"name":"NBA Whale Pro",'
    '"short_name":"NBA Whale",'
    '"id":"/?source=pwa",'
    '"start_url":"/",'
    '"scope":"/",'
    '"display":"standalone",'
    '"orientation":"portrait",'
    '"background_color":"#0E1117",'
    '"theme_color":"#00D4AA",'
    f'"icons":[{_manifest_icons}]'
    '}'
)
# Codifico in base64 per passarlo dentro lo script JS senza problemi di escaping
_MANIFEST_B64 = base64.b64encode(_PWA_MANIFEST.encode("utf-8")).decode("ascii")

# Favicon (sostituisce quello di default di Streamlit)
if _PWA_ICON_192_URL and _PWA_ICON_512_URL:
    _favicon_192 = f'<link rel="icon" type="image/png" sizes="192x192" href="{_PWA_ICON_192_URL}?{_PWA_CACHE_TAG}">'
    _favicon_512 = f'<link rel="icon" type="image/png" sizes="512x512" href="{_PWA_ICON_512_URL}?{_PWA_CACHE_TAG}">'
    _shortcut_icon = f'<link rel="shortcut icon" type="image/png" href="{_PWA_ICON_192_URL}?{_PWA_CACHE_TAG}">'
else:
    _favicon_192 = (
        f'<link rel="icon" type="image/png" sizes="192x192" href="data:image/png;base64,{_ICON_192}">'
        if _ICON_192 else ""
    )
    _favicon_512 = (
        f'<link rel="icon" type="image/png" sizes="512x512" href="data:image/png;base64,{_ICON_512}">'
        if _ICON_512 else ""
    )
    _shortcut_icon = (
        f'<link rel="shortcut icon" type="image/png" href="data:image/png;base64,{_ICON_192}">'
        if _ICON_192 else ""
    )

# Apple-touch-icon (per "Aggiungi a Home" su iOS Safari)
if _PWA_ICON_192_URL and _PWA_ICON_512_URL:
    _apple_icon_tag = f'<link rel="apple-touch-icon" sizes="192x192" href="{_PWA_ICON_192_URL}?{_PWA_CACHE_TAG}">'
    _apple_icon_512 = f'<link rel="apple-touch-icon" sizes="512x512" href="{_PWA_ICON_512_URL}?{_PWA_CACHE_TAG}">'
else:
    _apple_icon_tag = (
        f'<link rel="apple-touch-icon" sizes="192x192" href="data:image/png;base64,{_ICON_192}">'
        if _ICON_192 else ""
    )
    _apple_icon_512 = (
        f'<link rel="apple-touch-icon" sizes="512x512" href="data:image/png;base64,{_ICON_512}">'
        if _ICON_512 else ""
    )

_PWA_HEAD = f"""
<link rel="manifest" href='data:application/manifest+json;utf8,{_PWA_MANIFEST}'>
{_favicon_192}
{_favicon_512}
{_shortcut_icon}
{_apple_icon_tag}
{_apple_icon_512}
<meta name="theme-color" content="#00D4AA">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="NBA Whale">
<meta name="mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
"""
st.markdown(_PWA_HEAD, unsafe_allow_html=True)

# ── Bootstrap PWA: sostituisce manifest+favicon di Streamlit (e li tiene fissi) ──
# Streamlit re-inietta i propri tag nell'<head> ad ogni render React, quindi non
# basta sostituirli una volta: usiamo un MutationObserver che li rimette a posto
# ogni volta che Streamlit cerca di rimetterceli. Lo script gira in un iframe
# components.html ma raggiunge window.parent.document.
if _ICON_192 and _ICON_512:
    _PWA_BOOTSTRAP = f"""
<script>
(function() {{
    var MANIFEST_B64 = '{_MANIFEST_B64}';
    var ICON_192     = '{_ICON_192}';
    var ICON_512     = '{_ICON_512}';
    var TARGET_TITLE = 'NBA Whale Pro';

    function applyOnce() {{
        try {{
            var doc = window.parent && window.parent.document;
            if (!doc) return false;
            var head = doc.head;
            if (!head) return false;

            // 1) Rimuovi qualunque manifest/favicon/theme-color esistente
            ['link[rel="manifest"]',
             'link[rel="icon"]',
             'link[rel="shortcut icon"]',
             'link[rel="apple-touch-icon"]',
             'link[rel="apple-touch-icon-precomposed"]',
             'meta[name="theme-color"]'].forEach(function(sel) {{
                head.querySelectorAll(sel).forEach(function(el) {{
                    if (!el.dataset.nbaWhale) {{ el.parentNode.removeChild(el); }}
                }});
            }});

            // Se i miei tag sono già presenti non duplico
            if (head.querySelector('link[rel="manifest"][data-nba-whale]')) {{
                if (doc.title !== TARGET_TITLE) doc.title = TARGET_TITLE;
                return true;
            }}

            // 2) Aggiungi il mio manifest
            var manifestJson = atob(MANIFEST_B64);
            var manifest = doc.createElement('link');
            manifest.rel = 'manifest';
            manifest.dataset.nbaWhale = '1';
            manifest.href = 'data:application/manifest+json;utf8,' + encodeURIComponent(manifestJson);
            head.appendChild(manifest);

            // 3) Aggiungi favicon e apple-touch-icon
            function addLink(rel, sizes, b64) {{
                var l = doc.createElement('link');
                l.rel = rel;
                l.type = 'image/png';
                l.dataset.nbaWhale = '1';
                if (sizes) l.setAttribute('sizes', sizes);
                l.href = 'data:image/png;base64,' + b64;
                head.appendChild(l);
            }}
            addLink('icon',              '192x192', ICON_192);
            addLink('icon',              '512x512', ICON_512);
            addLink('shortcut icon',     '',        ICON_192);
            addLink('apple-touch-icon',  '192x192', ICON_192);
            addLink('apple-touch-icon',  '512x512', ICON_512);

            // 4) theme-color
            var meta = doc.createElement('meta');
            meta.name = 'theme-color';
            meta.content = '#00D4AA';
            meta.dataset.nbaWhale = '1';
            head.appendChild(meta);

            // 5) Titolo
            doc.title = TARGET_TITLE;

            console.log('[NBA Whale] PWA manifest e favicon installati.');
            return true;
        }} catch (e) {{
            console.error('[NBA Whale] PWA bootstrap failed:', e);
            return false;
        }}
    }}

    // Esegui subito + dopo qualche tick (Streamlit potrebbe non aver ancora montato l'<head>)
    applyOnce();
    [50, 200, 500, 1000, 2000, 4000].forEach(function(ms) {{
        setTimeout(applyOnce, ms);
    }});

    // Tieni l'<head> sotto controllo: se Streamlit cancella i nostri tag, li rimettiamo
    try {{
        var doc = window.parent && window.parent.document;
        if (doc && doc.head && window.MutationObserver) {{
            var obs = new MutationObserver(function() {{ applyOnce(); }});
            obs.observe(doc.head, {{ childList: true, subtree: true }});
            // Anche sul title perché Streamlit lo cambia ad ogni rerun
            if (doc.querySelector('title')) {{
                obs.observe(doc.querySelector('title'), {{ childList: true, characterData: true }});
            }}
        }}
    }} catch (e) {{ /* ignore */ }}
}})();
</script>
"""
    components.html(_PWA_BOOTSTRAP, height=0, width=0)

def _get_secret(key: str, default: str = "") -> str:
    """Legge una credenziale con priorità:
       1. st.secrets (Streamlit Cloud → Settings → Secrets, oppure file
          .streamlit/secrets.toml in locale)
       2. variabile d'ambiente
       3. default (vuoto)
    Nessuna chiave viene mai hard-coded nel sorgente."""
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            val = st.secrets[key]
            if val is not None:
                return str(val)
    except Exception:
        pass
    return os.environ.get(key, default)


# ── Credenziali (lette da st.secrets / env, MAI committate nel codice) ────
API_KEY      = _get_secret("API_SPORTS_KEY", "")
ODDS_API_KEY = _get_secret("ODDS_API_KEY", "")

BASE_URL    = "https://v2.nba.api-sports.io"
SEASON      = "2025"
STAT_LABELS = {"PTS": "Punti", "REB": "Rimbalzi", "AST": "Assist"}

# ── Tooltip / spiegazioni riusabili (passati a `help=` di st.metric) ───────────
TOOLTIPS = {
    "score": (
        "📊 SCORE 0–100\n\n"
        "Punteggio aggregato che combina:\n"
        "• 40% probabilità Poisson di superare la linea\n"
        "• 40% hit rate storico (quante volte ha superato la linea)\n"
        "• 20% forma recente del giocatore\n\n"
        "Soglie:\n"
        "• <32 → BET UNDER\n"
        "• 32-43 → Under probabile\n"
        "• 43-57 → SKIP / incerto\n"
        "• 57-68 → Over probabile\n"
        "• 68+ → BET OVER"
    ),
    "poisson": (
        "🎲 PROBABILITÀ POISSON\n\n"
        "Probabilità che il giocatore superi la linea Over basata su un modello "
        "statistico chiamato 'distribuzione di Poisson'.\n\n"
        "In pratica: prende la sua media (es. 25 punti a partita) e calcola "
        "la probabilità che in una data partita faccia PIÙ della linea (es. 22.5).\n\n"
        "È la probabilità 'modello' (cosa dice la matematica).\n"
        "Formula semplificata: 1 − P(X ≤ linea) dove X ~ Poisson(media)."
    ),
    "hit_rate": (
        "🎯 HIT RATE (storico)\n\n"
        "Percentuale di partite recenti in cui il giocatore ha effettivamente "
        "superato la linea Over.\n\n"
        "Esempio: linea 22.5 PTS, in 10 partite ha fatto Over 7 volte → "
        "Hit Rate = 70%.\n\n"
        "È la probabilità 'storica' (cosa è realmente successo)."
    ),
    "forma": (
        "🔥 FORMA 0–100\n\n"
        "Indicatore di come sta giocando ULTIMAMENTE rispetto alla sua media stagionale.\n\n"
        "• 100 = sta giocando molto meglio del solito\n"
        "• 50 = in linea con la sua media\n"
        "• 0 = sta giocando molto peggio del solito\n\n"
        "Si calcola dal trend ultime 3 partite vs ultime 10 partite, "
        "con bonus per consistency (poche oscillazioni)."
    ),
    "trend": (
        "📈 TREND (Ultime 3G - Ultime 10G)\n\n"
        "Differenza tra la media delle ultime 3 partite e la media delle ultime 10.\n\n"
        "Positivo = in salita (in forma)\n"
        "Negativo = in calo\n\n"
        "Esempio: +2.0 PTS = ultime 3 partite ~2 punti sopra la media delle ultime 10."
    ),
    "confidenza": (
        "🎚️ CONFIDENZA 0–100\n\n"
        "Quanto è prevedibile la sua performance partita per partita.\n\n"
        "• ≥75 = molto stabile (puoi fidarti dei numeri)\n"
        "• 50-75 = abbastanza stabile\n"
        "• <50 = ballerino, attenzione\n\n"
        "Si calcola come 100 − CV*100, dove CV è il coefficient of variation."
    ),
    "cv": (
        "📐 CV (Coefficient of Variation)\n\n"
        "Misura standard di volatilità: deviazione standard / media.\n\n"
        "• <0.25 → stabile\n"
        "• 0.25-0.40 → medio\n"
        "• >0.40 → ballerino"
    ),
    "z_score": (
        "📏 Z-SCORE LINEA\n\n"
        "Distanza standardizzata della linea dalla sua media, espressa in deviazioni standard.\n\n"
        "• Negativo → la linea è sotto la sua media (favorisce Over)\n"
        "• Positivo → la linea è sopra la sua media (favorisce Under)\n\n"
        "Esempio: Z = -0.8 significa che la linea è ~0.8 dev std sotto la media → "
        "matematicamente probabile l'Over."
    ),
    "edge": (
        "💡 EDGE (vantaggio)\n\n"
        "Differenza tra la TUA probabilità stimata e la probabilità implicita "
        "nella quota del bookmaker.\n\n"
        "Esempio: tu stimi 60% Over, la quota 1.90 implica 52.6% → edge +7.4pp.\n\n"
        "• ≥+7pp → value bet forte\n"
        "• ≥+3pp → value bet moderata\n"
        "• ≤-7pp → quota troppo bassa, NO BET"
    ),
}
STAT_COLORS = {"PTS": "#00D4AA", "REB": "#3B9EFF", "AST": "#FF9F40"}
VERSION     = "3.0"
REQ_TIMEOUT = 15
MAX_RETRIES = 3
EPLAY24_BASE_URL = "https://www.eplay24.com"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# ── Telegram bot (opzionale, per notifiche value alert) ────────────────────
TELEGRAM_API_BASE   = "https://api.telegram.org"
TELEGRAM_BOT_TOKEN  = _get_secret("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = _get_secret("TELEGRAM_CHAT_ID", "")

# ── Persistenza bankroll su file (effimera su Streamlit Cloud, persistente in locale) ──
BANKROLL_FILE = os.path.join(
    os.path.dirname(__file__) if "__file__" in globals() else ".",
    "bankroll_data.json",
)

st.markdown("""
<style>
:root {
    --bg:#0E1117;--card:#161B22;--border:#30363D;
    --accent:#00D4AA;--danger:#FF5252;--warn:#FFD600;
    --text:#E6EDF3;--muted:#8B949E;
}
html,body,[class*="css"]{background-color:var(--bg);color:var(--text);font-family:'Inter',sans-serif;}
section[data-testid="stSidebar"]{background-color:#0D1117;border-right:1px solid var(--border);}
section[data-testid="stSidebar"] .block-container{padding-top:0.9rem;}
section[data-testid="stSidebar"] hr{margin:0.65rem 0 0.85rem 0;border-color:#27313a;}
section[data-testid="stSidebar"] [data-testid="stRadio"] > div{gap:0.25rem;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{
  background:#111722;border:1px solid #24303b;border-radius:10px;padding:8px 10px;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){
  border-color:#00D4AA;background:rgba(0,212,170,0.10);
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .stSlider,
section[data-testid="stSidebar"] [data-testid="stCheckbox"]{
  background:#10161f;border:1px solid #24303b;border-radius:10px;padding:4px 8px;
}
.sb-card{
  background:linear-gradient(135deg,#0F1520 0%,#101924 100%);
  border:1px solid #24303b;border-radius:14px;padding:12px 12px;margin-bottom:10px;
}
.sb-title{color:#E6EDF3;font-size:0.76rem;font-weight:700;letter-spacing:.5px;text-transform:uppercase;}
.sb-sub{color:#8B949E;font-size:0.72rem;}
.sb-chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:0.66rem;font-weight:700;margin-left:6px;}
.sb-chip-ok{background:rgba(0,212,170,.18);color:#00D4AA;border:1px solid rgba(0,212,170,.4);}
.sb-chip-off{background:rgba(255,82,82,.14);color:#ff8b8b;border:1px solid rgba(255,82,82,.35);}
.whale-header{background:linear-gradient(135deg,#0E1117 0%,#161B22 100%);
  border:1px solid var(--border);border-radius:12px;padding:24px 32px;margin-bottom:24px;}
.whale-header h1{margin:0;font-size:2rem;font-weight:800;letter-spacing:-1px;color:var(--accent);}
.whale-header p{margin:4px 0 0;color:var(--muted);font-size:0.85rem;}
.badge{display:inline-block;background:var(--accent);color:#0E1117;font-size:0.65rem;
  font-weight:700;padding:2px 8px;border-radius:20px;margin-left:8px;vertical-align:middle;}
[data-testid="metric-container"]{background:var(--card);border:1px solid var(--border);
  border-radius:10px;padding:16px !important;}
.verdict-box{border-radius:10px;padding:18px 20px;margin:10px 0;border-left:4px solid;}
.verdict-green{background:rgba(0,212,170,0.08);border-color:#00D4AA;}
.verdict-yellow{background:rgba(255,214,0,0.08);border-color:#FFD600;}
.verdict-red{background:rgba(255,82,82,0.08);border-color:#FF5252;}
.disclaimer{text-align:center;font-size:0.72rem;color:var(--muted);
  padding:16px;border-top:1px solid var(--border);margin-top:32px;}

/* Mobile responsive */
@media (max-width: 768px){
  .whale-header{padding:14px 16px;}
  .whale-header h1{font-size:1.4rem;}
  .whale-header p{font-size:0.75rem;}
  [data-testid="metric-container"]{padding:10px !important;}
  [data-testid="metric-container"] [data-testid="stMetricValue"]{font-size:1rem !important;}
  [data-testid="metric-container"] label{font-size:0.7rem !important;}
  .verdict-box{padding:12px 14px;font-size:0.85rem;}
  div[data-testid="stHorizontalBlock"]{flex-wrap:wrap !important;}
  div[data-testid="stHorizontalBlock"] > div{min-width:48% !important;}
  section[data-testid="stSidebar"]{width:80vw !important;}
  div[role="tab"]{font-size:0.75rem !important;padding:6px 10px !important;}
  table{font-size:0.75rem !important;}
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER DICTIONARY  (nome → api-sports ID)
# ══════════════════════════════════════════════════════════════════════════════

PLAYER_IDS = {
    "Aaron Gordon": 195, "Aaron Nesmith": 2626, "Aaron Wiggins": 2863,
    "Al Horford": 248, "Alec Burks": 84, "Alex Caruso": 631,
    "Alperen Sengun": 2847, "Andre Drummond": 147, "Andrew Nembhard": 3476,
    "Andrew Wiggins": 548, "Anfernee Simons": 1023, "Anthony Black": 4010,
    "Anthony Davis": 126, "Anthony Edwards": 2584, "Austin Reaves": 2845,
    "Ayo Dosunmu": 2802, "Bam Adebayo": 724, "Bennedict Mathurin": 3466,
    "Ben Sheppard": 3979, "Ben Simmons": 481, "Bobby Portis": 431,
    "Bogdan Bogdanovic": 743, "Bradley Beal": 45, "Brandon Ingram": 260,
    "Brandon Miller": 3950, "Brook Lopez": 323, "Bruce Brown": 944,
    "Buddy Hield": 236, "Cade Cunningham": 2801, "Caleb Martin": 2242,
    "Cam Thomas": 2855, "Cameron Johnson": 1871, "Cameron Payne": 417,
    "Cam Reddish": 1889, "Caris LeVert": 317, "Cason Wallace": 4009,
    "Chet Holmgren": 3448, "CJ McCollum": 347, "Clint Capela": 92,
    "Coby White": 1900, "Cole Anthony": 2563, "Collin Sexton": 1021,
    "Daeqwon Plowden": 3478, "Damian Lillard": 319, "D'Angelo Russell": 462,
    "Daniel Gafford": 1859, "Dante Exum": 164, "Dario Saric": 468,
    "Darius Garland": 1860, "Davion Mitchell": 2834, "Day'Ron Sharpe": 2848,
    "De'Aaron Fox": 776, "Deandre Ayton": 930, "De'Andre Hunter": 1868,
    "DeMar DeRozan": 136, "Deni Avdija": 2564, "Dennis Schroder": 472,
    "Derrick White": 897, "Desmond Bane": 2568, "Devin Booker": 64,
    "Devonte' Graham": 973, "Dillon Brooks": 749, "Domantas Sabonis": 463,
    "Donovan Mitchell": 840, "Donte DiVincenzo": 962, "Dorian Finney-Smith": 175,
    "Draymond Green": 204, "Duncan Robinson": 1018, "Dyson Daniels": 3406,
    "Eric Gordon": 196, "Evan Mobley": 2835, "Franz Wagner": 2858,
    "Fred VanVleet": 527, "Giannis Antetokounmpo": 20, "Gradey Dick": 4027,
    "Grant Williams": 1901, "Grayson Allen": 926, "Guerschon Yabusele": 904,
    "Haywood Highsmith": 1815, "Herbert Jones": 2822, "Immanuel Quickley": 2636,
    "Isaiah Hartenstein": 978, "Isaiah Stewart": 2648, "Ivica Zubac": 575,
    "Jabari Smith Jr.": 3489, "Jaden Hardy": 3407, "Jaden Ivey": 3451,
    "Jaden McDaniels": 2621, "Jake LaRavia": 3460, "Jakob Poeltl": 428,
    "Jalen Brunson": 946, "Jalen Duren": 3433, "Jalen Green": 2810,
    "Jalen Johnson": 2819, "Jalen McDaniels": 1880, "Jalen Suggs": 2852,
    "Jalen Williams": 3504, "Jalen Wilson": 3946, "Jamal Murray": 383,
    "James Harden": 216, "Ja Morant": 1881, "Jaren Jackson Jr.": 982,
    "Jarrett Allen": 727, "Jaylen Brown": 75, "Jayson Tatum": 882,
    "Jerami Grant": 200, "Jimmy Butler": 86, "Joel Embiid": 159,
    "John Collins": 761, "Jonas Valanciunas": 525, "Jonathan Kuminga": 2827,
    "Jordan Clarkson": 109, "Josh Giddey": 2808, "Josh Green": 2593,
    "Josh Hart": 791, "Jrue Holiday": 242, "Julius Randle": 441,
    "Jusuf Nurkic": 398, "Karl-Anthony Towns": 519, "Kawhi Leonard": 314,
    "Keegan Murray": 3475, "Kelly Oubre Jr.": 407, "Kentavious Caldwell-Pope": 89,
    "Kenyon Martin Jr.": 2617, "Kevin Durant": 153, "Kevin Huerter": 980,
    "Kevin Love": 326, "Khris Middleton": 361, "Klay Thompson": 514,
    "Kris Dunn": 152, "Kristaps Porzingis": 432, "Kyle Anderson": 18,
    "Kyle Kuzma": 820, "Kyle Lowry": 327, "Kyrie Irving": 261,
    "LaMelo Ball": 2566, "Lauri Markkanen": 830, "LeBron James": 265,
    "Lonzo Ball": 735, "Luka Doncic": 963, "Luguentz Dort": 2040,
    "Mac McClung": 2833, "Malik Beasley": 46, "Malik Monk": 842,
    "Marcus Smart": 486, "Markelle Fultz": 779, "Mark Williams": 3506,
    "Matisse Thybulle": 1896, "Max Christie": 3427, "Maxi Kleber": 817,
    "Max Strus": 2051, "Michael Porter Jr.": 1014, "Mikal Bridges": 940,
    "Mike Conley": 114, "Miles Bridges": 941, "Miles McBride": 2832,
    "Mitchell Robinson": 1020, "Mo Bamba": 932, "Moses Moody": 2836,
    "Myles Turner": 522, "Naji Marshall": 2668, "Naz Reid": 2146,
    "Nic Claxton": 1854, "Nickeil Alexander-Walker": 1845, "Nicolas Batum": 40,
    "Nikola Jokic": 279, "Nikola Vucevic": 534, "Noah Clowney": 3944,
    "Norman Powell": 434, "O.G. Anunoby": 732, "Obi Toppin": 2658,
    "Ochai Agbaji": 3411, "Onyeka Okongwu": 2629, "Paolo Banchero": 3414,
    "Pascal Siakam": 479, "Pat Connaughton": 115, "Patrick Williams": 2664,
    "Paul George": 189, "Payton Pritchard": 2635, "P.J. Washington": 1897,
    "Precious Achiuwa": 2561, "Quentin Grimes": 2811, "RJ Barrett": 1846,
    "Robert Williams III": 1045, "Royce O'Neale": 851, "Rudy Gobert": 192,
    "Rui Hachimura": 1862, "Russell Westbrook": 544, "Santi Aldama": 2786,
    "Scoot Henderson": 3408, "Scottie Barnes": 2789, "Seth Curry": 123,
    "Shaedon Sharpe": 3487, "Shai Gilgeous-Alexander": 972,
    "Spencer Dinwiddie": 142, "Stephen Curry": 124, "T.J. McConnell": 348,
    "Tari Eason": 3435, "Taurean Prince": 437, "Taylor Hendricks": 4031,
    "Terance Mann": 1877, "Terry Rozier": 458, "Tim Hardaway Jr.": 215,
    "Tobias Harris": 222, "Trae Young": 1046, "Tristan Thompson": 515,
    "Tyler Herro": 1866, "Tyrese Haliburton": 2595, "Tyrese Maxey": 2619,
    "Tyus Jones": 285, "Victor Wembanyama": 3457,
    "Wendell Carter Jr.": 950, "Zach LaVine": 308, "Zion Williamson": 1902,
    "Bogdan Bogdanovic": 743, "Brandin Podziemski": 3975,
    "Brandon Boston Jr.": 2792, "Bronny James": 4125, "Cam Whitmore": 3978,
    "Cole Anthony": 2563, "Colby Jones": 4020, "Dalton Knecht": 4126,
    "Damion Lee": 599, "Dariq Whitehead": 3945, "Davion Mitchell": 2834,
    "Dereck Lively II": 4044, "Dillon Brooks": 749, "Dwight Powell": 433,
    "EJ Liddell": 3462, "Franz Wagner": 2858, "GG Jackson": 3994,
    "Gui Santos": 3485, "Harry Giles III": 4041, "Hunter Tyson": 3967,
    "Isaiah Collier": 4178, "Jaden Springer": 2851, "Jarace Walker": 3981,
    "Jared Butler": 2796, "Jared McCain": 4159, "Javonte Green": 2404,
    "Jaxson Hayes": 1864, "Jaylen Clark": 4000, "Jaylen Wells": 4133,
    "Jaylin Williams": 3505, "JD Davison": 3429, "Jeff Green": 207,
    "Joe Ingles": 258, "Johnny Juzang": 3454, "Jonathan Mogbo": 4175,
    "Jordan Hawkins": 4002, "Jordan McLaughlin": 997, "Jordan Miller": 3984,
    "Josh Minott": 3470, "Josh Okogie": 1010, "Josh Richardson": 446,
    "Julian Phillips": 3954, "Julian Strawther": 3966, "Justin Edwards": 4217,
    "Keon Ellis": 3436, "Keyonte George": 4029, "KJ Simpson": 4096,
    "Kobe Brown": 3983, "Kobe Bufkin": 3938, "Larry Nance Jr.": 385,
    "Leonard Miller": 4001, "Lonnie Walker IV": 1038, "Luka Garza": 2807,
    "Luke Kennard": 814, "Malcolm Hill": 3380, "Marcus Sasser": 3970,
    "MarJon Beauchamp": 3405, "Markieff Morris": 374, "Markquis Nowell": 4028,
    "Marvin Bagley III": 931, "Mason Plumlee": 426, "Matas Buzelis": 4098,
    "Maxwell Lewis": 3991, "Miles Norris": 3942, "Monte Morris": 845,
    "Moritz Wagner": 1037, "Moses Brown": 2160, "Moussa Diabate": 3431,
    "Neemias Queta": 2844, "Nick Richards": 2639, "Nick Smith Jr.": 4042,
    "Nikola Jovic": 3453, "Ochai Agbaji": 3411, "Olivier-Maxence Prosper": 3960,
    "Orlando Robinson": 3482, "Ousmane Dieng": 3432, "Pacome Dadiet": 4147,
    "Patrick Baldwin Jr.": 3413, "Paul Reed": 2638, "Peyton Watson": 3498,
    "Pete Nance": 3957, "Quenton Jackson": 3452, "Reed Sheppard": 4117,
    "Reggie Jackson": 264, "Ricky Council IV": 4049, "Rob Dillingham": 4142,
    "Ron Harper Jr.": 3447, "Ron Holland II": 4111, "Ryan Dunn": 4162,
    "Sam Hauser": 2812, "Sam Merrill": 2623, "Sidy Cissoko": 4024,
    "Simone Fontecchio": 3438, "T.J. Warren": 540, "Talen Horton-Tucker": 1867,
    "Terrence Shannon Jr.": 4144, "Terry Taylor": 2853, "Thomas Bryant": 753,
    "Tidjane Salaun": 4095, "Toumani Camara": 4015, "Trayce Jackson-Davis": 3973,
    "Tre Jones": 2606, "Tre Mann": 2831,
    "TyTy Washington Jr.": 3497, "Vince Williams Jr.": 3508, "Vit Krejci": 2608,
    "Wendell Moore Jr.": 3474, "Xavier Tillman": 2656, "Yves Missi": 4145,
    "Zaccharie Risacher": 4090, "Zach Collins": 762, "Zach Edey": 4130,
    "Zeke Nnaji": 2627, "Ziaire Williams": 2864,
    "Alperen Sengun": 2847, "Amen Thompson": 3977, "Ausar Thompson": 3971,
    "Chet Holmgren": 3448, "Dereon Seabron": 3486, "Drew Timme": 3999,
    "Gradey Dick": 4027, "Isaiah Mobley": 3472, "Jabari Walker": 3496,
    "Jalen Hood-Schifino": 3990, "Jalen Slawson": 4021, "Jalen Pickett": 3965,
    "Jamal Shead": 4176, "James Akinjo": 4139,
    "Jordan Walsh": 3943, "Kessler Edwards": 2805, "Keyontae Johnson": 4008,
    "Killian Hayes": 2599, "Landry Shamet": 1022,
    "Mac McClung": 2833, "Malcolm Brogdon": 2041, "Nate Darling": 2578,
    "Noah Clowney": 3944, "Oshae Brissett": 2110, "Scottie Pippen Jr.": 3477,
    "Seth Lundy": 3941, "Taj Gibson": 190, "Taze Moore": 3724,
    "Trey Murphy III": 2837, "Wenyen Gabriel": 2649,
}

# alias comuni (nomi brevi / soprannomi → nome ufficiale)
PLAYER_ALIASES = {
    "lebron": "LeBron James", "giannis": "Giannis Antetokounmpo",
    "jokic": "Nikola Jokic", "curry": "Stephen Curry", "steph": "Stephen Curry",
    "kd": "Kevin Durant", "durant": "Kevin Durant",
    "luka": "Luka Doncic", "tatum": "Jayson Tatum", "jayson": "Jayson Tatum",
    "ja": "Ja Morant", "morant": "Ja Morant", "ad": "Anthony Davis",
    "embiid": "Joel Embiid", "wemby": "Victor Wembanyama",
    "dame": "Damian Lillard", "lillard": "Damian Lillard",
    "bron": "LeBron James", "king james": "LeBron James",
    "sga": "Shai Gilgeous-Alexander", "shai": "Shai Gilgeous-Alexander",
    "kawhi": "Kawhi Leonard", "paul george": "Paul George",
    "pg13": "Paul George", "pg": "Paul George",
    "doncic": "Luka Doncic", "zion": "Zion Williamson",
    "trae": "Trae Young", "lamelo": "LaMelo Ball", "melo": "LaMelo Ball",
    "fox": "De'Aaron Fox", "booker": "Devin Booker", "bam": "Bam Adebayo",
    "jalen b": "Jalen Brunson", "brunson": "Jalen Brunson",
    "ant": "Anthony Edwards", "ant edwards": "Anthony Edwards",
    "edwards": "Anthony Edwards", "tyrese": "Tyrese Haliburton",
    "haliburton": "Tyrese Haliburton", "maxey": "Tyrese Maxey",
    "demar": "DeMar DeRozan", "sabonis": "Domantas Sabonis",
    "gobert": "Rudy Gobert", "siakam": "Pascal Siakam",
    "middleton": "Khris Middleton", "holiday": "Jrue Holiday",
    "jrue": "Jrue Holiday", "herro": "Tyler Herro",
    "mitchell": "Donovan Mitchell", "donovan": "Donovan Mitchell",
}


def find_player(query: str):
    """
    Trova (nome, id) per una query libera.
    Ritorna (None, None) se non trovato.
    """
    q = query.strip().lower()
    if q in PLAYER_ALIASES:
        name = PLAYER_ALIASES[q]
        return name, PLAYER_IDS[name]

    # corrispondenza esatta (case-insensitive)
    for name, pid in PLAYER_IDS.items():
        if name.lower() == q:
            return name, pid

    # corrispondenza parziale
    for name, pid in PLAYER_IDS.items():
        if q in name.lower():
            return name, pid

    # fuzzy matching
    matches = difflib.get_close_matches(
        q, [n.lower() for n in PLAYER_IDS], n=1, cutoff=0.55
    )
    if matches:
        for name in PLAYER_IDS:
            if name.lower() == matches[0]:
                return name, PLAYER_IDS[name]

    return None, None


def all_player_names():
    return sorted(PLAYER_IDS.keys())


def _sanitize_player_maps():
    """Pulisce aliases che puntano a player non presenti."""
    clean_aliases = {k: v for k, v in PLAYER_ALIASES.items() if v in PLAYER_IDS}
    return clean_aliases


PLAYER_ALIASES = _sanitize_player_maps()


def player_integrity_report():
    id_to_names = {}
    for name, pid in PLAYER_IDS.items():
        id_to_names.setdefault(pid, []).append(name)
    collisions = {pid: names for pid, names in id_to_names.items() if len(names) > 1}
    return {"players": len(PLAYER_IDS), "collisions": collisions}


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LAYER
# ══════════════════════════════════════════════════════════════════════════════

def _hdrs():
    return {"x-apisports-key": API_KEY, "x-apisports-host": "v2.nba.api-sports.io"}


def _safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _game_status_short(game_obj: dict) -> int | None:
    """`status.short` da API NBA: 1=Not Started · 2=Live · 3=Finished · 4+
    Vedi docs api-sports.io."""
    try:
        st = (game_obj.get("status") or {}).get("short")
        return int(st) if st is not None and st != "" else None
    except (TypeError, ValueError):
        return None


def _side_score_total(side_scores: dict) -> float:
    """Punteggio finale casa/trasferta da `scores.home` / `scores.visitors`.

    L'API v2 usa in genere `points`; alcuni contesti espongono `total` o solo
    `linescore` (quarti)."""
    if not side_scores:
        return 0.0
    pts = side_scores.get("points")
    if pts is not None and str(pts).strip() != "":
        return _safe_float(pts)
    tot = side_scores.get("total")
    if tot is not None and str(tot).strip() != "":
        return _safe_float(tot)
    ls = side_scores.get("linescore")
    if isinstance(ls, (list, tuple)) and ls:
        return sum(_safe_float(q) for q in ls)
    return 0.0


def _api_get(path: str, params: dict):
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                f"{BASE_URL}{path}",
                headers=_hdrs(),
                params=params,
                timeout=REQ_TIMEOUT,
            )
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as err:
            last_err = err
            if attempt < MAX_RETRIES:
                continue
    raise last_err


def _normalize_phase_label(raw_value) -> str:
    s = str(raw_value or "").strip().lower()
    if any(k in s for k in ["play-in", "play in", "playin"]):
        return "Play-In"
    if any(k in s for k in ["playoff", "play-off", "postseason", "post-season"]):
        return "Playoff"
    if any(k in s for k in ["regular", "regular season", "reg"]):
        return "Regular Season"
    return "Unknown"


def _phase_matches(phase_selected: str, phase_value: str) -> bool:
    if phase_selected == "Tutte":
        return True
    if phase_selected == "Regular Season":
        return phase_value in {"Regular Season", "Unknown"}
    return phase_value == phase_selected


# Whitelist ufficiale 30 franchigie NBA (codici 3 lettere) per filtrare l'API
NBA_TEAM_CODES = {
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS",
}
NBA_TEAM_NAMES = {
    "atlanta hawks", "boston celtics", "brooklyn nets", "charlotte hornets",
    "chicago bulls", "cleveland cavaliers", "dallas mavericks", "denver nuggets",
    "detroit pistons", "golden state warriors", "houston rockets", "indiana pacers",
    "la clippers", "los angeles clippers", "los angeles lakers", "memphis grizzlies",
    "miami heat", "milwaukee bucks", "minnesota timberwolves", "new orleans pelicans",
    "new york knicks", "oklahoma city thunder", "orlando magic", "philadelphia 76ers",
    "phoenix suns", "portland trail blazers", "sacramento kings", "san antonio spurs",
    "toronto raptors", "utah jazz", "washington wizards",
}


def _is_nba_team(name: str, code: str = "", raw: dict | None = None) -> bool:
    """Vero solo per le 30 franchigie NBA. Filtra G-League, All-Star, internazionali."""
    code_norm = (code or "").upper().strip()
    name_norm = (name or "").lower().strip()
    if code_norm in NBA_TEAM_CODES:
        # Esclude squadre All-Star che a volte condividono codici brevi
        if raw and (raw.get("allStar") or raw.get("nbaFranchise") is False):
            return False
        return True
    if name_norm in NBA_TEAM_NAMES:
        return True
    # Se l'API espone esplicitamente nbaFranchise=True, accettiamo
    if raw and raw.get("nbaFranchise") is True and not raw.get("allStar"):
        return True
    return False


@st.cache_data(ttl=21600)
def fetch_teams(season: str):
    teams_map = {}

    def _add_team(tid, name, code, raw=None):
        if not tid or not name:
            return
        if not _is_nba_team(str(name), str(code or ""), raw):
            return
        label = f"{name} ({code})" if code else str(name)
        teams_map[int(tid)] = {"id": int(tid), "name": str(name), "label": label}

    # Tentativo 1: endpoint teams con season
    try:
        r = _api_get("/teams", {"season": season})
        for t in r.json().get("response", []):
            _add_team(t.get("id"), t.get("name"), t.get("code") or "", raw=t)
    except Exception:
        pass

    # Tentativo 2: endpoint teams senza season (alcuni piani/API lo richiedono)
    if len(teams_map) < 30:
        try:
            r = _api_get("/teams", {})
            for t in r.json().get("response", []):
                _add_team(t.get("id"), t.get("name"), t.get("code") or "", raw=t)
        except Exception:
            pass

    # Tentativo 3 (fallback forte): ricava team da games della season
    if len(teams_map) < 30:
        try:
            r = _api_get("/games", {"season": season})
            for g in r.json().get("response", []):
                tm = g.get("teams", {}) or {}
                home = tm.get("home", {}) or {}
                vis = tm.get("visitors", {}) or {}
                _add_team(home.get("id"), home.get("name") or home.get("nickname"), home.get("code") or "", raw=home)
                _add_team(vis.get("id"), vis.get("name") or vis.get("nickname"), vis.get("code") or "", raw=vis)
        except Exception:
            pass

    return sorted(list(teams_map.values()), key=lambda x: x["name"])


@st.cache_data(ttl=3600)
def fetch_team_players(team_id: int, season: str):
    try:
        r = _api_get("/players", {"team": team_id, "season": season})
        players_map = {}
        for p in r.json().get("response", []):
            pid = p.get("id")
            firstname = (p.get("firstname") or "").strip()
            lastname = (p.get("lastname") or "").strip()
            full_name = f"{firstname} {lastname}".strip()
            if not full_name or not pid:
                continue
            players_map[int(pid)] = {
                "id": int(pid),
                "name": full_name,
                "label": f"{full_name} (ID {int(pid)})",
                "team_id": int(team_id),
            }
        return sorted(list(players_map.values()), key=lambda x: x["name"])
    except Exception:
        return []


@st.cache_data(ttl=900)
def fetch_team_injuries(team_id: int, season: str):
    """
    Prova a scaricare injury report dal provider.
    Ritorna lista di dict con name/status/position, oppure [] se non disponibile.
    """
    try:
        r = _api_get("/injuries", {"team": team_id, "season": season})
        resp = r.json().get("response", [])
        out = []
        for it in resp:
            player = (it.get("player") or {})
            firstname = (player.get("firstname") or "").strip()
            lastname = (player.get("lastname") or "").strip()
            full_name = f"{firstname} {lastname}".strip() or (player.get("name") or "").strip() or "Unknown"
            status = (
                (it.get("status") or "")
                or (it.get("injury") or {}).get("status", "")
                or (it.get("reason") or "")
            )
            position = (player.get("leagues", {}) or {}).get("standard", {}).get("pos", "") or player.get("position", "")
            out.append({"name": full_name, "status": str(status), "position": str(position)})
        return out
    except Exception:
        return []


def _position_weight(pos: str) -> float:
    p = str(pos or "").upper()
    if p in {"G", "PG", "SG"}:
        return 1.15
    if p in {"F", "SF", "PF"}:
        return 1.0
    if p in {"C"}:
        return 0.9
    return 1.0


def infer_injury_impact(injuries: list):
    """
    Trasforma injury list in metriche operative: out_count, usage_loss, weighted_impact.
    """
    if not injuries:
        return {
            "out_count": 0,
            "questionable_count": 0,
            "usage_loss_pct": 0.0,
            "weighted_impact": 0.0,
            "notes": [],
        }
    out_count = 0
    questionable_count = 0
    usage_loss = 0.0
    weighted_impact = 0.0
    notes = []
    for item in injuries:
        status = str(item.get("status", "")).lower()
        pos = str(item.get("position", ""))
        w = _position_weight(pos)
        if any(k in status for k in ["out", "inactive", "dnp", "suspended"]):
            out_count += 1
            usage_loss += 3.5 * w
            weighted_impact += 4.0 * w
            notes.append(f"OUT: {item.get('name')} ({pos or '?'})")
        elif any(k in status for k in ["questionable", "probable", "doubt", "gtd"]):
            questionable_count += 1
            usage_loss += 1.3 * w
            weighted_impact += 1.8 * w
            notes.append(f"Q: {item.get('name')} ({pos or '?'})")
    return {
        "out_count": out_count,
        "questionable_count": questionable_count,
        "usage_loss_pct": round(usage_loss, 2),
        "weighted_impact": round(weighted_impact, 2),
        "notes": notes[:10],
    }


@st.cache_data(ttl=1800)
def fetch_team_games(team_id: int, season: str, api_key: str) -> dict:
    """Ritorna dict: game_id → metadata matchup/team phase."""
    try:
        r = _api_get("/games", {"season": season, "team": team_id})
        games = {}
        for g in r.json().get("response", []):
            gid  = g.get("id")
            date = (g.get("date", {}) or {}).get("start", "")[:10]
            home_id   = (g.get("teams", {}) or {}).get("home",     {}).get("id")
            home_code = (g.get("teams", {}) or {}).get("home",     {}).get("code", "?")
            vis_code  = (g.get("teams", {}) or {}).get("visitors", {}).get("code", "?")
            stage_val = (
                g.get("stage")
                or (g.get("week", {}) or {}).get("name")
                or (g.get("league", {}) or {}).get("stage")
                or ""
            )
            phase = _normalize_phase_label(stage_val)
            games[gid] = {"date": date, "home_id": home_id,
                          "home_code": home_code, "vis_code": vis_code,
                          "phase": phase}
        return games
    except Exception:
        return {}


def _player_team_id_from_df(df_all: pd.DataFrame):
    """Estrae il team_id del giocatore dalla partita più recente in archivio."""
    if df_all is None or df_all.empty or "TEAM_ID" not in df_all.columns:
        return None
    try:
        sorted_df = df_all.sort_values("GAME_DATE", ascending=False)
        return int(sorted_df.iloc[0]["TEAM_ID"])
    except Exception:
        return None


@st.cache_data(ttl=600)
def find_next_game_for_team(team_id: int, season: str):
    """Ritorna il prossimo game non finito per un team, o None."""
    if not team_id:
        return None
    try:
        r = _api_get("/games", {"team": int(team_id), "season": season})
        games = r.json().get("response", []) or []
    except Exception:
        return None

    today = datetime.date.today()
    upcoming = []
    for g in games:
        is_finished, _, is_live = _game_status_flags(g)
        if is_finished:
            continue
        date_str = ((g.get("date") or {}).get("start", "") or "")[:10]
        if not date_str:
            continue
        try:
            d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            continue
        # Includiamo anche le partite "live" e quelle di oggi
        if d < today:
            continue
        upcoming.append((d, is_live, g))
    if not upcoming:
        return None
    # Ordina: prima i live (oggi), poi per data crescente
    upcoming.sort(key=lambda x: (not x[1], x[0]))
    return upcoming[0][2]


def _opponent_info_from_game(game: dict, my_team_id: int) -> dict:
    """Da un game raw + mio team_id ricava: opponent_id, opponent_name, opponent_code,
    location ('Home'/'Away'), datetime di start (UTC isoformat)."""
    teams = game.get("teams", {}) or {}
    home = teams.get("home", {}) or {}
    vis = teams.get("visitors", {}) or {}
    home_id = int(home.get("id") or 0)
    vis_id  = int(vis.get("id") or 0)
    if my_team_id == home_id:
        opp = vis
        location = "Home"
    elif my_team_id == vis_id:
        opp = home
        location = "Away"
    else:
        opp = vis if vis_id else home
        location = "?"
    date_obj = game.get("date", {}) or {}
    status_obj = game.get("status", {}) or {}
    return {
        "opponent_id":   int(opp.get("id") or 0),
        "opponent_name": opp.get("name") or opp.get("nickname") or "Avversario",
        "opponent_code": (opp.get("code") or "?").upper(),
        "location": location,
        "start_iso": date_obj.get("start", "") or "",
        "status_long": status_obj.get("long", "") or "",
    }


def _format_next_game_when(start_iso: str) -> tuple:
    """Da ISO datetime → (data_str, giorni_da_oggi)."""
    if not start_iso:
        return "Data sconosciuta", None
    try:
        # api-sports ritorna in UTC. Per l'utente è ok mostrare la data, l'orario Roma è +1/+2.
        dt = datetime.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        # Convertiamo in fuso italiano (CET/CEST) approssimando con +1 ore (è una stima, basta per la giornata)
        dt_local = dt + datetime.timedelta(hours=2)  # estate; durante l'inverno sarebbe +1
        days_from_now = (dt_local.date() - datetime.date.today()).days
        weekday_it = ["Lun","Mar","Mer","Gio","Ven","Sab","Dom"][dt_local.weekday()]
        date_str = f"{weekday_it} {dt_local.strftime('%d/%m/%Y')} alle {dt_local.strftime('%H:%M')} (ora ITA)"
        return date_str, days_from_now
    except Exception:
        return start_iso, None


@st.cache_data(ttl=1800)
def get_nba_data(player_id: int, player_name: str, season: str, api_key: str, phase_selected: str = "Tutte"):
    """
    Scarica statistiche del giocatore e le arricchisce con date e home/away.
    Ritorna DataFrame | "NO_KEY" | "ERROR" | None
    """
    if not api_key:
        return "NO_KEY"

    try:
        r = _api_get("/players/statistics", {"id": player_id, "season": season})
        stats = r.json().get("response", [])
        if not stats:
            return None

        # team ID dalla prima entry
        team_id = stats[0].get("team", {}).get("id")

        # partite con date e matchup
        game_map = fetch_team_games(team_id, season, api_key) if team_id else {}

        rows = []
        for entry in stats:
            gid = entry.get("game", {}).get("id")
            gm  = game_map.get(gid, {})

            pts = _safe_float(entry.get("points", 0))
            reb = _safe_float(entry.get("totReb", 0) or entry.get("rebounds", 0))
            ast = _safe_float(entry.get("assists", 0))
            stl = _safe_float(entry.get("steals", 0))
            blk = _safe_float(entry.get("blocks", 0))
            tov = _safe_float(entry.get("turnovers", 0))
            min_p = str(entry.get("min", "0") or "0")

            game_date  = gm.get("date", "")
            home_id    = gm.get("home_id")
            home_code  = gm.get("home_code", "?")
            vis_code   = gm.get("vis_code",  "?")
            phase      = gm.get("phase", "Unknown")

            loc     = "Home" if (home_id and team_id == home_id) else "Away"
            matchup = (f"{home_code} vs {vis_code}" if loc == "Home"
                       else f"{vis_code} @ {home_code}")

            rows.append({
                "GAME_DATE": game_date,
                "MATCHUP":   matchup,
                "LOC":       loc,
                "PHASE":     phase,
                "TEAM_ID":   team_id,
                "PTS": pts, "REB": reb, "AST": ast,
                "STL": stl, "BLK": blk, "TOV": tov,
                "MIN": min_p,
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce").dt.date
        df = df.dropna(subset=["GAME_DATE"])
        if "PHASE" in df.columns:
            df = df[df["PHASE"].apply(lambda p: _phase_matches(phase_selected, p))]
            if df.empty:
                return None
        df = df.sort_values("GAME_DATE", ascending=False).reset_index(drop=True)
        return df

    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            return "NO_KEY"
        return "ERROR"
    except Exception:
        return "ERROR"


def load_player(query: str):
    name, pid = find_player(query)
    if pid is None:
        return None, None, None
    phase_selected = st.session_state.get("phase_type", "Tutte")
    result = get_nba_data(pid, name, SEASON, API_KEY, phase_selected)
    return name, pid, result


def data_ok(result, name: str) -> bool:
    if isinstance(result, str) and result == "NO_KEY":
        st.error("❌ Chiave API mancante o non valida. Controlla `API_SPORTS_KEY`.")
        return False
    if isinstance(result, str) and result == "ERROR":
        st.error(f"❌ Errore API per **{name}**. Riprova tra qualche secondo.")
        return False
    if result is None:
        st.warning(f"⚠️ Nessun dato trovato per **{name}** nella stagione {SEASON}.")
        return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def compute_stat(df: pd.DataFrame, n: int, linea: float, col: str = "PTS"):
    df_r = df.head(n).copy()
    avg  = df_r[col].mean() if col in df_r.columns else 0.0
    prob = (1 - poisson.cdf(linea, avg)) * 100 if avg > 0 else 0.0
    hit  = (len(df_r[df_r[col] > linea]) / len(df_r) * 100) if len(df_r) > 0 else 0.0
    return df_r, avg, prob, hit


def form_score(df_r: pd.DataFrame, col: str = "PTS") -> float:
    if col not in df_r.columns or len(df_r) < 3:
        return 50.0
    avg_all  = df_r[col].mean()
    avg_last = df_r.head(3)[col].mean()
    if avg_all == 0:
        return 50.0
    return max(0.0, min(100.0, 50 + (avg_last / avg_all - 1) * 100))


def verdict_data(prob: float, hit: float, form: float):
    prob = max(0.0, min(100.0, prob))
    hit = max(0.0, min(100.0, hit))
    form = max(0.0, min(100.0, form))
    score = prob * 0.40 + hit * 0.40 + form * 0.20
    if score >= 68:
        return score, "BET OVER",        "✅", "green",  "Segnale forte: Poisson, hit rate e forma convergono sull'Over."
    elif score >= 57:
        return score, "OVER PROBABILE",  "⚡", "green",  "Segnale moderato per l'Over. Valuta la quota prima di giocare."
    elif score >= 43:
        return score, "SKIP",            "⚠️", "yellow", "Segnale debole o contrastante. Meglio evitare."
    elif score >= 32:
        return score, "UNDER PROBABILE", "🔻", "yellow", "Segnale moderato per l'Under. Tende a stare sotto la linea."
    else:
        return score, "BET UNDER",       "❌", "red",    "Segnale forte sull'Under: media bassa, hit rate scarso."


def show_verdict_block(prob: float, hit: float, df_r: pd.DataFrame,
                        linea: float, col: str = "PTS"):
    form  = form_score(df_r, col)
    score, lbl, emo, color, desc = verdict_data(prob, hit, form)
    stat_lbl  = STAT_LABELS.get(col, col)
    css_class = f"verdict-{color}"
    bar_color = "#00D4AA" if color == "green" else ("#FFD600" if color == "yellow" else "#FF5252")

    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Score",    f"{score:.0f}/100", help=TOOLTIPS["score"])
    v2.metric("Poisson",  f"{prob:.1f}%",     help=TOOLTIPS["poisson"])
    v3.metric("Hit Rate", f"{hit:.0f}%",      help=TOOLTIPS["hit_rate"])
    v4.metric("Forma",    f"{form:.0f}/100",  help=TOOLTIPS["forma"])
    st.caption(
        "💡 Passa il cursore sull'icona ❔ accanto a ogni metrica per la spiegazione completa. "
        "In breve: **Score** = giudizio finale 0–100 · **Poisson** = probabilità modello · "
        "**Hit Rate** = % partite reali sopra linea · **Forma** = trend recente vs media."
    )

    st.markdown(
        f'<div class="verdict-box {css_class}">'
        f'{emo} <strong>{lbl}</strong> — Linea {linea} {stat_lbl}<br>'
        f'<span style="font-size:0.85rem;color:#8B949E">{desc}</span>'
        f'</div>', unsafe_allow_html=True)

    # Barra orizzontale leggibile al posto del semicerchio
    pct = max(0.0, min(100.0, float(score)))
    band_label = (
        "BET UNDER" if pct < 32 else
        "Under probabile" if pct < 43 else
        "Skip / incerto" if pct < 57 else
        "Over probabile" if pct < 68 else
        "BET OVER"
    )
    st.markdown(
        f"""
<div style="margin:8px 0 4px 0;">
    <div style="display:flex;justify-content:space-between;font-size:0.85rem;color:#8B949E;">
        <span>Segnale {stat_lbl}</span>
        <span><strong style="color:{bar_color};font-size:1.05rem;">{pct:.0f}/100</strong> · {band_label}</span>
    </div>
    <div style="height:14px;background:#1c2230;border-radius:7px;overflow:hidden;margin-top:4px;
                background:linear-gradient(to right,
                    #FF5252 0%, #FF5252 32%,
                    #FFD600 32%, #FFD600 57%,
                    #00D4AA 57%, #00D4AA 100%);">
        <div style="height:100%;width:{pct}%;background:rgba(0,0,0,0.0);
                    border-right:3px solid white;box-shadow:0 0 8px white;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#8B949E;margin-top:2px;">
        <span>0</span><span>32</span><span>57</span><span>100</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("Score 0–100 = 40% Poisson + 40% Hit Rate + 20% Forma. "
               "Sotto 32 → Under, 32–57 → incerto, 57–68 → Over probabile, 68+ → Bet Over. "
               "Non è consulenza finanziaria.")


# ══════════════════════════════════════════════════════════════════════════════
#  CONTROPRONOSTICI
# ══════════════════════════════════════════════════════════════════════════════

def slump_info(avg_s: float, avg_r: float):
    if avg_s == 0:
        return 0.0, "NELLA NORMA", "✅", "yellow", "Media stagionale assente."
    delta = (avg_r - avg_s) / avg_s * 100
    if delta <= -20:
        return delta, "FORTE RIMBALZO ATTESO",         "🔥", "green",  f"Slump severo (−{abs(delta):.0f}%). Alta prob. di risalita."
    elif delta <= -10:
        return delta, "RIMBALZO PROBABILE",             "⚡", "green",  f"Sotto media del {abs(delta):.0f}%. Possibile rimbalzo."
    elif delta >= 20:
        return delta, "IN FORMA — RISCHIO REGRESSIONE","📉", "red",   f"Sopra media del {delta:.0f}%. Rischio calo."
    elif delta >= 10:
        return delta, "FORMA POSITIVA",                "📈", "yellow", f"Leggermente sopra media (+{delta:.0f}%)."
    else:
        return delta, "NELLA NORMA",                   "✅", "yellow", f"Rendimento in linea ({delta:+.0f}%)."


def show_contropronostici(name: str, df_all: pd.DataFrame, n_window: int):
    st.subheader(f"🔄 Contropronostici — {name}")
    st.caption(f"Ultimi {n_window} match vs intera stagione {SEASON}")
    df_rec = df_all.head(n_window)
    rows, bar_data = [], {}
    for col in ["PTS", "REB", "AST"]:
        if col not in df_all.columns:
            continue
        avg_s = df_all[col].mean()
        avg_r = df_rec[col].mean() if not df_rec.empty else avg_s
        delta, lbl, emo, color, desc = slump_info(avg_s, avg_r)
        bar_data[col] = (avg_s, avg_r)
        rows.append((col, avg_s, avg_r, delta, lbl, emo, f"verdict-{color}", desc))

    cols_ui = st.columns(len(rows)) if rows else []
    for i, (col, avg_s, avg_r, delta, lbl, emo, css, desc) in enumerate(rows):
        with cols_ui[i]:
            st.markdown(f"**{STAT_LABELS.get(col, col)}**")
            st.metric("Media recente", f"{avg_r:.1f}",
                      delta=f"{avg_r - avg_s:+.1f} vs {avg_s:.1f} stagionale")
            st.markdown(
                f'<div class="verdict-box {css}" style="padding:10px 14px;font-size:0.82rem;">'
                f'{emo} <strong>{lbl}</strong><br>{desc}</div>',
                unsafe_allow_html=True)

    if bar_data:
        fig = go.Figure()
        for col, (avg_s, avg_r) in bar_data.items():
            c = STAT_COLORS.get(col, "#aaa")
            fig.add_trace(go.Bar(name=f"{STAT_LABELS[col]} Stagione",
                                 x=[STAT_LABELS[col]], y=[avg_s],
                                 marker_color=c, opacity=0.4))
            fig.add_trace(go.Bar(name=f"{STAT_LABELS[col]} Recenti",
                                 x=[STAT_LABELS[col]], y=[avg_r],
                                 marker_color=c, opacity=1.0))
        fig.update_layout(barmode="group", height=290, template="plotly_dark",
                          title=f"Stagionale (chiaro) vs Ultimi {n_window} (pieno)",
                          legend=dict(orientation="h", y=-0.28),
                          yaxis_title="Valore medio", showlegend=False)
        st.plotly_chart(fig, width="stretch")


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _last_n_avg(df: pd.DataFrame, col: str, n: int):
    if col not in df.columns or df.empty:
        return 0.0
    n = max(1, min(n, len(df)))
    return float(df.head(n)[col].mean())


def _streak_over(df: pd.DataFrame, col: str, line: float):
    streak = 0
    if col not in df.columns:
        return 0
    for v in df[col]:
        if v > line:
            streak += 1
        else:
            break
    return streak


def _streak_under(df: pd.DataFrame, col: str, line: float):
    streak = 0
    if col not in df.columns:
        return 0
    for v in df[col]:
        if v <= line:
            streak += 1
        else:
            break
    return streak


def _z_score(df: pd.DataFrame, col: str, line: float):
    if col not in df.columns or len(df) < 2:
        return 0.0
    s = df[col].std(ddof=0)
    if s == 0 or pd.isna(s):
        return 0.0
    return float((line - df[col].mean()) / s)


def _recent_vs_season_delta(df_r: pd.DataFrame, df_all: pd.DataFrame, col: str):
    if col not in df_r.columns or col not in df_all.columns or df_r.empty or df_all.empty:
        return 0.0
    return float(df_r[col].mean() - df_all[col].mean())


def _consistency_index(df_r: pd.DataFrame, col: str):
    if col not in df_r.columns or df_r.empty:
        return 0.0
    avg = float(df_r[col].mean())
    std = float(df_r[col].std(ddof=0)) if len(df_r) > 1 else 0.0
    if avg <= 0:
        return 0.0
    return max(0.0, min(100.0, 100 - (std / avg) * 100))


def _ceiling_rate(df_r: pd.DataFrame, col: str):
    if col not in df_r.columns or df_r.empty:
        return 0.0
    q75 = float(df_r[col].quantile(0.75))
    return float((df_r[col] >= q75).mean() * 100)


def _floor_rate(df_r: pd.DataFrame, col: str):
    if col not in df_r.columns or df_r.empty:
        return 0.0
    q25 = float(df_r[col].quantile(0.25))
    return float((df_r[col] <= q25).mean() * 100)


def _momentum_index(df_r: pd.DataFrame, col: str):
    if col not in df_r.columns or len(df_r) < 5:
        return 50.0
    last3 = float(df_r.head(3)[col].mean())
    last10 = float(df_r.head(min(10, len(df_r)))[col].mean())
    if last10 == 0:
        return 50.0
    return max(0.0, min(100.0, 50 + (last3 / last10 - 1) * 100))


def _pressure_index(df_r: pd.DataFrame):
    # indicatore semplice di stress: più TOV, più pressione.
    if "TOV" not in df_r.columns or df_r.empty:
        return 50.0
    tov = float(df_r["TOV"].mean())
    return max(0.0, min(100.0, 100 - tov * 12))


def _two_way_impact(df_r: pd.DataFrame):
    if df_r.empty:
        return 0.0
    stl = float(df_r["STL"].mean()) if "STL" in df_r.columns else 0.0
    blk = float(df_r["BLK"].mean()) if "BLK" in df_r.columns else 0.0
    tov = float(df_r["TOV"].mean()) if "TOV" in df_r.columns else 0.0
    return float((stl + blk) * 10 - tov * 3)


def _availability_proxy(df_r: pd.DataFrame):
    if "MIN" not in df_r.columns or df_r.empty:
        return 0.0
    mins = pd.to_numeric(df_r["MIN"], errors="coerce").dropna()
    if mins.empty:
        return 0.0
    return float(mins.mean())


def _line_gap(avg_value: float, line: float):
    return float(avg_value - line)


def _fmt_signed(val: float, unit: str = "") -> str:
    sign = "+" if val > 0 else ("" if val == 0 else "")
    return f"{sign}{val:.2f}{unit}"


def _read_delta(val: float, stat_lbl: str) -> str:
    if val > 1.5:
        return f"📈 In netta crescita: ~{val:+.1f} {stat_lbl} sopra la sua media stagionale."
    if val > 0.4:
        return f"↗️ In leggera crescita: ~{val:+.1f} {stat_lbl} sopra la media stagionale."
    if val < -1.5:
        return f"📉 In netto calo: {val:+.1f} {stat_lbl} sotto la media stagionale."
    if val < -0.4:
        return f"↘️ In leggero calo: {val:+.1f} {stat_lbl} sotto la media stagionale."
    return f"➡️ Stabile: in linea con la sua media stagionale ({val:+.1f})."


def _read_consistency(val: float) -> str:
    if val >= 80: return f"🎯 Molto costante ({val:.0f}/100): performance simili partita per partita."
    if val >= 65: return f"✅ Buona costanza ({val:.0f}/100): poche oscillazioni."
    if val >= 45: return f"⚖️ Costanza media ({val:.0f}/100): qualche partita storta."
    return f"⚠️ Volatile ({val:.0f}/100): performance molto altalenanti."


def _read_pct_top(val: float, label: str) -> str:
    if val >= 35: return f"🚀 Spesso esplode in alto: {val:.0f}% delle partite top {label}."
    if val >= 20: return f"📊 Top {label} circa 1 partita su 4–5 ({val:.0f}%)."
    return f"😐 Raramente in modalità top {label} ({val:.0f}%)."


def _read_pct_bottom(val: float) -> str:
    if val >= 35: return f"🆘 Spesso fa flop: {val:.0f}% delle partite molto sotto la media."
    if val >= 20: return f"⚠️ Flop circa 1 su 4–5 partite ({val:.0f}%)."
    return f"💪 Raramente sotto soglia ({val:.0f}%)."


def _read_momentum(val: float) -> str:
    if val >= 65: return f"🔥 Forma in salita ({val:.0f}/100): ultime 3 nettamente meglio."
    if val >= 53: return f"⬆️ Forma in lieve crescita ({val:.0f}/100)."
    if val <= 35: return f"❄️ Forma in calo ({val:.0f}/100): ultime 3 sotto la media recente."
    if val <= 47: return f"⬇️ Forma in lieve discesa ({val:.0f}/100)."
    return f"➡️ Forma stabile ({val:.0f}/100)."


def _read_pressure(val: float) -> str:
    if val >= 75: return f"🧘 Bassa pressione ({val:.0f}/100): poche perse, gestisce bene il pallone."
    if val >= 55: return f"🙂 Pressione media ({val:.0f}/100)."
    return f"😰 Sotto pressione ({val:.0f}/100): troppe perse, errori sotto stress."


def _read_two_way(val: float) -> str:
    if val >= 25: return f"💎 Impatto difensivo elevato ({val:.1f}): tante stoppate/recuperi."
    if val >= 10: return f"✅ Buon impatto difensivo ({val:.1f})."
    if val >= 0:  return f"➖ Impatto difensivo modesto ({val:.1f})."
    return f"❌ Negativo ({val:.1f}): perse > stoppate+recuperi."


def _read_gap(val: float, stat_lbl: str) -> str:
    if val >= 3:   return f"💚 Media molto sopra la linea ({val:+.1f} {stat_lbl}): segnale forte Over."
    if val >= 1:   return f"🟢 Media sopra la linea ({val:+.1f} {stat_lbl}): leggermente Over."
    if val >= -1:  return f"🟡 Media vicinissima alla linea ({val:+.1f} {stat_lbl}): incerto."
    if val >= -3:  return f"🟠 Media sotto la linea ({val:+.1f} {stat_lbl}): leggermente Under."
    return f"🔴 Media molto sotto la linea ({val:+.1f} {stat_lbl}): segnale forte Under."


def _extract_opponent(matchup) -> str:
    """Estrae il codice della squadra avversaria da MATCHUP.
    Formati gestiti: 'LAL vs BOS' → 'BOS', 'LAL @ BOS' → 'BOS'."""
    if not isinstance(matchup, str):
        return "?"
    m = re.search(r"(?:vs|@)\s+([A-Za-z]{2,4})", matchup)
    return m.group(1) if m else "?"


def _parse_minutes(val) -> float:
    """Converte 'MM' o 'MM:SS' in float minuti."""
    if val is None:
        return 0.0
    s = str(val).strip()
    if not s:
        return 0.0
    if ":" in s:
        try:
            mn, sc = s.split(":", 1)
            return float(mn) + float(sc) / 60.0
        except Exception:
            return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def _diagnose_game(row: dict, season_avg_pts: float, season_std_pts: float,
                   season_avg_min: float) -> list:
    """Genera spiegazioni plausibili sul perché la performance devia dalla media stagionale.
    Non possiamo sapere con certezza degli infortuni storici, ma usiamo segnali indiretti
    (minutaggio, TOV, sede, gap rispetto alla media) per indicare le cause più probabili."""
    pts = float(row.get("PTS", 0) or 0)
    mins = _parse_minutes(row.get("MIN"))
    tov  = float(row.get("TOV", 0) or 0)
    loc  = row.get("LOC", "")
    delta_pts = pts - season_avg_pts

    reasons = []
    # Minutaggio anomalo
    if season_avg_min > 0 and mins < season_avg_min * 0.5 and mins > 0:
        reasons.append(f"⏱️ minuti molto sotto media ({mins:.0f} vs ~{season_avg_min:.0f}): "
                       "possibile gestione, infortunio, foul-trouble o blowout")
    elif season_avg_min > 0 and mins > season_avg_min * 1.25:
        reasons.append(f"💪 minuti elevati ({mins:.0f}): partita stretta o assenze nel suo team")

    # Performance fuori scala (high)
    if season_std_pts > 0 and delta_pts >= season_std_pts * 1.5 and pts > season_avg_pts:
        reasons.append("🚀 serata top: forse rivale debole, assenze nell'avversario o ritmo elevato")
    # Performance fuori scala (low)
    if season_std_pts > 0 and delta_pts <= -season_std_pts * 1.5 and pts < season_avg_pts:
        reasons.append("📉 serata sotto la media: difesa avversaria forte / ritmo basso / pressione")

    # Turnover alti
    if tov >= 5:
        reasons.append(f"🚨 tante palle perse ({int(tov)}): forte pressione difensiva")

    # Trasferta + sotto media
    if loc == "Away" and pts < season_avg_pts - 2:
        reasons.append("✈️ in trasferta: spesso rendimento più basso lontano da casa")

    # Default se niente di rilevante
    if not reasons:
        reasons.append("📊 performance in linea con la sua media stagionale")
    return reasons


def build_opponent_breakdown(df_r: pd.DataFrame, df_all: pd.DataFrame,
                             linee: dict) -> pd.DataFrame:
    """Aggrega le performance per squadra avversaria (su df_r, le partite recenti)."""
    if df_r.empty or "MATCHUP" not in df_r.columns:
        return pd.DataFrame()
    df = df_r.copy()
    df["OPP"] = df["MATCHUP"].apply(_extract_opponent)
    season_avg_pts = float(df_all["PTS"].mean()) if "PTS" in df_all.columns and not df_all.empty else 0.0

    rows = []
    for opp, sub in df.groupby("OPP"):
        if not opp or opp == "?":
            continue
        n = len(sub)
        avg_pts = float(sub["PTS"].mean()) if "PTS" in sub.columns else 0.0
        avg_reb = float(sub["REB"].mean()) if "REB" in sub.columns else 0.0
        avg_ast = float(sub["AST"].mean()) if "AST" in sub.columns else 0.0
        max_pts = float(sub["PTS"].max()) if "PTS" in sub.columns else 0.0
        min_pts = float(sub["PTS"].min()) if "PTS" in sub.columns else 0.0
        hit_pts = float((sub["PTS"] > linee["PTS"]).mean() * 100) if "PTS" in sub.columns else 0.0
        delta_vs_season = avg_pts - season_avg_pts
        if delta_vs_season >= 2.0:
            tag = "📈 sopra media"
        elif delta_vs_season <= -2.0:
            tag = "📉 sotto media"
        else:
            tag = "➡️ in media"
        rows.append({
            "Avversario": opp,
            "Partite": n,
            "Media PTS": round(avg_pts, 1),
            "Media REB": round(avg_reb, 1),
            "Media AST": round(avg_ast, 1),
            "Max / Min PTS": f"{max_pts:.0f} / {min_pts:.0f}",
            f"Hit Over {linee['PTS']}": f"{hit_pts:.0f}%",
            "Delta vs media stagione": round(delta_vs_season, 1),
            "Lettura": tag,
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("Media PTS", ascending=False).reset_index(drop=True)
    return out


def build_extra_10_tools(df_r: pd.DataFrame, df_all: pd.DataFrame, linee: dict):
    avg_pts  = float(df_r["PTS"].mean()) if "PTS" in df_r.columns and not df_r.empty else 0.0
    d_pts    = _recent_vs_season_delta(df_r, df_all, "PTS")
    d_reb    = _recent_vs_season_delta(df_r, df_all, "REB")
    d_ast    = _recent_vs_season_delta(df_r, df_all, "AST")
    cons_pts = _consistency_index(df_r, "PTS")
    ceil_pts = _ceiling_rate(df_r, "PTS")
    floor_pts = _floor_rate(df_r, "PTS")
    mom_pts  = _momentum_index(df_r, "PTS")
    press    = _pressure_index(df_r)
    two_way  = _two_way_impact(df_r)
    gap_pts  = _line_gap(avg_pts, linee.get("PTS", 0))

    rows = [
        ("E1",  "Trend PUNTI (recente vs stagione)",     _fmt_signed(d_pts, " PTS"),  _read_delta(d_pts, "PTS")),
        ("E2",  "Trend RIMBALZI (recente vs stagione)",  _fmt_signed(d_reb, " REB"),  _read_delta(d_reb, "REB")),
        ("E3",  "Trend ASSIST (recente vs stagione)",    _fmt_signed(d_ast, " AST"),  _read_delta(d_ast, "AST")),
        ("E4",  "Costanza nei PUNTI",                    f"{cons_pts:.0f}/100",       _read_consistency(cons_pts)),
        ("E5",  "Frequenza serata TOP nei PUNTI",        f"{ceil_pts:.0f}%",          _read_pct_top(ceil_pts, "PTS")),
        ("E6",  "Frequenza serata FLOP nei PUNTI",       f"{floor_pts:.0f}%",         _read_pct_bottom(floor_pts)),
        ("E7",  "Momentum (ultime 3 vs ultime 10) PTS",  f"{mom_pts:.0f}/100",        _read_momentum(mom_pts)),
        ("E8",  "Gestione palla / pressione",            f"{press:.0f}/100",          _read_pressure(press)),
        ("E9",  "Impatto difensivo (STL+BLK − TOV)",     f"{two_way:.1f}",            _read_two_way(two_way)),
        ("E10", "Gap PUNTI vs linea Over/Under",         _fmt_signed(gap_pts, " PTS"), _read_gap(gap_pts, "PTS")),
    ]
    return pd.DataFrame(rows, columns=["#", "Indicatore", "Valore", "Cosa significa"])


def build_40_tools(name: str, df_all: pd.DataFrame, df_r: pd.DataFrame, linee: dict):
    pts_l, reb_l, ast_l = linee["PTS"], linee["REB"], linee["AST"]
    p_over_pts = (1 - poisson.cdf(pts_l, _last_n_avg(df_r, "PTS", len(df_r)))) * 100 if not df_r.empty else 0
    p_over_reb = (1 - poisson.cdf(reb_l, _last_n_avg(df_r, "REB", len(df_r)))) * 100 if not df_r.empty else 0
    p_over_ast = (1 - poisson.cdf(ast_l, _last_n_avg(df_r, "AST", len(df_r)))) * 100 if not df_r.empty else 0
    hit_pts = (df_r["PTS"] > pts_l).mean() * 100 if "PTS" in df_r.columns and not df_r.empty else 0
    hit_reb = (df_r["REB"] > reb_l).mean() * 100 if "REB" in df_r.columns and not df_r.empty else 0
    hit_ast = (df_r["AST"] > ast_l).mean() * 100 if "AST" in df_r.columns and not df_r.empty else 0
    home = df_r[df_r["LOC"] == "Home"] if "LOC" in df_r.columns else pd.DataFrame()
    away = df_r[df_r["LOC"] == "Away"] if "LOC" in df_r.columns else pd.DataFrame()
    trend_pts = _last_n_avg(df_r, "PTS", 3) - _last_n_avg(df_r, "PTS", 10)
    trend_reb = _last_n_avg(df_r, "REB", 3) - _last_n_avg(df_r, "REB", 10)
    trend_ast = _last_n_avg(df_r, "AST", 3) - _last_n_avg(df_r, "AST", 10)
    tools = [
        ("1", "Media PTS 5G", _last_n_avg(df_r, "PTS", 5)),
        ("2", "Media PTS 10G", _last_n_avg(df_r, "PTS", 10)),
        ("3", "Media PTS Season", _last_n_avg(df_all, "PTS", len(df_all))),
        ("4", "Media REB 5G", _last_n_avg(df_r, "REB", 5)),
        ("5", "Media REB 10G", _last_n_avg(df_r, "REB", 10)),
        ("6", "Media REB Season", _last_n_avg(df_all, "REB", len(df_all))),
        ("7", "Media AST 5G", _last_n_avg(df_r, "AST", 5)),
        ("8", "Media AST 10G", _last_n_avg(df_r, "AST", 10)),
        ("9", "Media AST Season", _last_n_avg(df_all, "AST", len(df_all))),
        ("10", "Hit Rate Over PTS", hit_pts),
        ("11", "Hit Rate Over REB", hit_reb),
        ("12", "Hit Rate Over AST", hit_ast),
        ("13", "Prob Poisson Over PTS", p_over_pts),
        ("14", "Prob Poisson Over REB", p_over_reb),
        ("15", "Prob Poisson Over AST", p_over_ast),
        ("16", "Trend PTS (3G-10G)", trend_pts),
        ("17", "Trend REB (3G-10G)", trend_reb),
        ("18", "Trend AST (3G-10G)", trend_ast),
        ("19", "Dev.Std PTS", float(df_r["PTS"].std(ddof=0)) if "PTS" in df_r.columns else 0),
        ("20", "Dev.Std REB", float(df_r["REB"].std(ddof=0)) if "REB" in df_r.columns else 0),
        ("21", "Dev.Std AST", float(df_r["AST"].std(ddof=0)) if "AST" in df_r.columns else 0),
        ("22", "CV PTS", (float(df_r["PTS"].std(ddof=0))/max(_last_n_avg(df_r, "PTS", len(df_r)), 0.1)) if "PTS" in df_r.columns else 0),
        ("23", "CV REB", (float(df_r["REB"].std(ddof=0))/max(_last_n_avg(df_r, "REB", len(df_r)), 0.1)) if "REB" in df_r.columns else 0),
        ("24", "CV AST", (float(df_r["AST"].std(ddof=0))/max(_last_n_avg(df_r, "AST", len(df_r)), 0.1)) if "AST" in df_r.columns else 0),
        ("25", "Max PTS (finestra)", float(df_r["PTS"].max()) if "PTS" in df_r.columns and not df_r.empty else 0),
        ("26", "Min PTS (finestra)", float(df_r["PTS"].min()) if "PTS" in df_r.columns and not df_r.empty else 0),
        ("27", "Max REB (finestra)", float(df_r["REB"].max()) if "REB" in df_r.columns and not df_r.empty else 0),
        ("28", "Min REB (finestra)", float(df_r["REB"].min()) if "REB" in df_r.columns and not df_r.empty else 0),
        ("29", "Max AST (finestra)", float(df_r["AST"].max()) if "AST" in df_r.columns and not df_r.empty else 0),
        ("30", "Min AST (finestra)", float(df_r["AST"].min()) if "AST" in df_r.columns and not df_r.empty else 0),
        ("31", "Streak Over PTS", _streak_over(df_r, "PTS", pts_l)),
        ("32", "Streak Under PTS", _streak_under(df_r, "PTS", pts_l)),
        ("33", "Streak Over REB", _streak_over(df_r, "REB", reb_l)),
        ("34", "Streak Under REB", _streak_under(df_r, "REB", reb_l)),
        ("35", "Streak Over AST", _streak_over(df_r, "AST", ast_l)),
        ("36", "Streak Under AST", _streak_under(df_r, "AST", ast_l)),
        ("37", "Home PTS Avg", float(home["PTS"].mean()) if "PTS" in home.columns and not home.empty else 0),
        ("38", "Away PTS Avg", float(away["PTS"].mean()) if "PTS" in away.columns and not away.empty else 0),
        ("39", "Z-Score linea PTS", _z_score(df_r, "PTS", pts_l)),
        ("40", "Confidenza (100-CV*100)", max(0.0, 100 - ((float(df_r["PTS"].std(ddof=0))/max(_last_n_avg(df_r, "PTS", len(df_r)), 0.1))*100 if "PTS" in df_r.columns else 50))),
    ]
    out = pd.DataFrame(tools, columns=["#", "Strumento", "Valore"])
    out["Valore"] = out["Valore"].apply(lambda x: 0.0 if (isinstance(x, float) and (math.isinf(x) or math.isnan(x))) else x)
    out["Giocatore"] = name
    return out


def build_50_context_tools(
    name: str,
    df_all: pd.DataFrame,
    df_r: pd.DataFrame,
    linee: dict,
    teammate_out_count: int,
    opp_out_count: int,
    teammate_usage_loss: float,
    opp_def_weakness: float,
    expected_min_delta: float,
    b2b_flag: bool,
):
    pts_l, reb_l, ast_l = linee["PTS"], linee["REB"], linee["AST"]
    pts_mean = _last_n_avg(df_r, "PTS", len(df_r))
    reb_mean = _last_n_avg(df_r, "REB", len(df_r))
    ast_mean = _last_n_avg(df_r, "AST", len(df_r))
    min_series = pd.to_numeric(df_r["MIN"], errors="coerce") if "MIN" in df_r.columns else pd.Series(dtype=float)
    min_avg = float(min_series.mean()) if not min_series.empty else 0.0
    min_std = float(min_series.std(ddof=0)) if len(min_series) > 1 else 0.0
    min_last3 = float(min_series.head(3).mean()) if len(min_series) >= 1 else 0.0

    base_over_pts = (1 - poisson.cdf(pts_l, pts_mean)) * 100 if pts_mean > 0 else 0.0
    base_over_reb = (1 - poisson.cdf(reb_l, reb_mean)) * 100 if reb_mean > 0 else 0.0
    base_over_ast = (1 - poisson.cdf(ast_l, ast_mean)) * 100 if ast_mean > 0 else 0.0

    usage_boost = teammate_usage_loss * 0.35 + teammate_out_count * 1.8
    mins_boost = expected_min_delta * 1.25
    opp_boost = opp_def_weakness * 0.45 + opp_out_count * 1.4
    schedule_penalty = -4.0 if b2b_flag else 0.0
    total_adjust = usage_boost + mins_boost + opp_boost + schedule_penalty

    adj_pts_mean = max(0.0, pts_mean * (1 + total_adjust / 100))
    adj_reb_mean = max(0.0, reb_mean * (1 + (opp_boost + mins_boost * 0.5) / 100))
    adj_ast_mean = max(0.0, ast_mean * (1 + (usage_boost + mins_boost * 0.3) / 100))

    adj_over_pts = (1 - poisson.cdf(pts_l, adj_pts_mean)) * 100 if adj_pts_mean > 0 else 0.0
    adj_over_reb = (1 - poisson.cdf(reb_l, adj_reb_mean)) * 100 if adj_reb_mean > 0 else 0.0
    adj_over_ast = (1 - poisson.cdf(ast_l, adj_ast_mean)) * 100 if adj_ast_mean > 0 else 0.0

    home = df_r[df_r["LOC"] == "Home"] if "LOC" in df_r.columns else pd.DataFrame()
    away = df_r[df_r["LOC"] == "Away"] if "LOC" in df_r.columns else pd.DataFrame()

    recent_pts = _last_n_avg(df_r, "PTS", 5)
    season_pts = _last_n_avg(df_all, "PTS", len(df_all))
    recent_reb = _last_n_avg(df_r, "REB", 5)
    season_reb = _last_n_avg(df_all, "REB", len(df_all))
    recent_ast = _last_n_avg(df_r, "AST", 5)
    season_ast = _last_n_avg(df_all, "AST", len(df_all))

    p75_pts = float(df_r["PTS"].quantile(0.75)) if "PTS" in df_r.columns and not df_r.empty else 0.0
    p90_pts = float(df_r["PTS"].quantile(0.90)) if "PTS" in df_r.columns and not df_r.empty else 0.0
    p25_pts = float(df_r["PTS"].quantile(0.25)) if "PTS" in df_r.columns and not df_r.empty else 0.0
    iqr_pts = p75_pts - p25_pts

    expected_value_factor = adj_over_pts - (100 / 1.90)  # benchmark quota 1.90
    confidence = max(0.0, min(100.0, 70 + total_adjust - min_std))
    risk_score = max(0.0, min(100.0, 35 + min_std * 2 + (12 if b2b_flag else 0)))

    tools = [
        ("1", "Teammate OUT count", teammate_out_count),
        ("2", "Opponents OUT count", opp_out_count),
        ("3", "Teammate usage loss %", teammate_usage_loss),
        ("4", "Opponent defense weakness %", opp_def_weakness),
        ("5", "Expected minutes delta", expected_min_delta),
        ("6", "Back-to-back flag", 1 if b2b_flag else 0),
        ("7", "Usage boost model %", usage_boost),
        ("8", "Minutes boost model %", mins_boost),
        ("9", "Opponent boost model %", opp_boost),
        ("10", "Schedule penalty %", schedule_penalty),
        ("11", "Total adjustment %", total_adjust),
        ("12", "Min avg recent", min_avg),
        ("13", "Min std recent", min_std),
        ("14", "Min avg last3", min_last3),
        ("15", "PTS mean base", pts_mean),
        ("16", "PTS mean adjusted", adj_pts_mean),
        ("17", "REB mean base", reb_mean),
        ("18", "REB mean adjusted", adj_reb_mean),
        ("19", "AST mean base", ast_mean),
        ("20", "AST mean adjusted", adj_ast_mean),
        ("21", "Prob Over PTS base %", base_over_pts),
        ("22", "Prob Over PTS adj %", adj_over_pts),
        ("23", "Prob Over REB base %", base_over_reb),
        ("24", "Prob Over REB adj %", adj_over_reb),
        ("25", "Prob Over AST base %", base_over_ast),
        ("26", "Prob Over AST adj %", adj_over_ast),
        ("27", "Delta Prob PTS", adj_over_pts - base_over_pts),
        ("28", "Delta Prob REB", adj_over_reb - base_over_reb),
        ("29", "Delta Prob AST", adj_over_ast - base_over_ast),
        ("30", "Recent vs Season PTS", recent_pts - season_pts),
        ("31", "Recent vs Season REB", recent_reb - season_reb),
        ("32", "Recent vs Season AST", recent_ast - season_ast),
        ("33", "Home PTS avg", float(home["PTS"].mean()) if "PTS" in home.columns and not home.empty else 0),
        ("34", "Away PTS avg", float(away["PTS"].mean()) if "PTS" in away.columns and not away.empty else 0),
        ("35", "Home- Away PTS split", (float(home["PTS"].mean()) if "PTS" in home.columns and not home.empty else 0) - (float(away["PTS"].mean()) if "PTS" in away.columns and not away.empty else 0)),
        ("36", "PTS 75th percentile", p75_pts),
        ("37", "PTS 90th percentile", p90_pts),
        ("38", "PTS 25th percentile", p25_pts),
        ("39", "PTS IQR", iqr_pts),
        ("40", "Streak Over PTS", _streak_over(df_r, "PTS", pts_l)),
        ("41", "Streak Under PTS", _streak_under(df_r, "PTS", pts_l)),
        ("42", "Streak Over REB", _streak_over(df_r, "REB", reb_l)),
        ("43", "Streak Over AST", _streak_over(df_r, "AST", ast_l)),
        ("44", "Z-score linea PTS", _z_score(df_r, "PTS", pts_l)),
        ("45", "Model confidence %", confidence),
        ("46", "Model risk score %", risk_score),
        ("47", "Value edge vs 1.90 %", expected_value_factor),
        ("48", "Lean PTS", "OVER" if adj_over_pts >= 55 else ("UNDER" if adj_over_pts <= 45 else "SKIP")),
        ("49", "Lean REB", "OVER" if adj_over_reb >= 55 else ("UNDER" if adj_over_reb <= 45 else "SKIP")),
        ("50", "Lean AST", "OVER" if adj_over_ast >= 55 else ("UNDER" if adj_over_ast <= 45 else "SKIP")),
    ]
    out = pd.DataFrame(tools, columns=["#", "Strumento", "Valore"])
    out["Valore"] = out["Valore"].apply(lambda x: 0.0 if (isinstance(x, float) and (math.isinf(x) or math.isnan(x))) else x)
    out["Giocatore"] = name
    return out


def _tool_value(tools_df: pd.DataFrame, key: str, default: float = 0.0) -> float:
    """Estrae un valore dal DataFrame dei tool (colonne '#' / 'Valore') in modo sicuro."""
    try:
        rows = tools_df.loc[tools_df["#"] == key, "Valore"]
        if rows.empty:
            return default
        return float(rows.iloc[0])
    except Exception:
        return default


def _streak_label(streak_over: int, streak_under: int, stat: str) -> str:
    if streak_over > 0:
        if streak_over >= 5: return f"🔥 {streak_over} {stat} Over di fila"
        if streak_over >= 3: return f"📈 {streak_over} {stat} Over di fila"
        return f"🟢 {streak_over} {stat} Over"
    if streak_under > 0:
        if streak_under >= 5: return f"❄️ {streak_under} {stat} Under di fila"
        if streak_under >= 3: return f"📉 {streak_under} {stat} Under di fila"
        return f"🔴 {streak_under} {stat} Under"
    return f"➖ Nessuna serie {stat}"


def toolkit_pro_page(linee: dict, n_partite: int):
    st.subheader("🧰 Toolkit Tipster Pro")
    st.caption("Cruscotto visuale completo: medie, probabilità, trend, contesto e indicatori avanzati. "
               "Le tabelle numeriche grezze sono accessibili negli expander '📋 Vedi tabella raw'.")
    linee = render_line_inputs(expanded=False)
    query = st.text_input("Giocatore Toolkit", value="Luka Doncic", key="toolkit_player")
    if not query:
        return

    name, pid = find_player(query)
    if pid is None:
        st.warning("Giocatore non trovato.")
        return

    with st.spinner(f"Caricamento toolkit per {name}..."):
        phase_selected = st.session_state.get("phase_type", "Tutte")
        df_all = get_nba_data(pid, name, SEASON, API_KEY, phase_selected)
    if not data_ok(df_all, name):
        return

    n_eff = len(df_all) if st.session_state.get("use_all_games", False) else n_partite
    df_r = df_all.head(max(1, n_eff)).copy()

    t_base, t_ctx, t_adv = st.tabs([
        "📊 Stat & Probabilità",
        "🧠 Contesto & Value Bet",
        "🚀 Indicatori Avanzati",
    ])

    # ── TAB 1: Toolkit Base — visuale ────────────────────────────────────
    with t_base:
        tools_df = build_40_tools(name, df_all, df_r, linee)
        v = _tool_value  # alias

        # Sezione: 6 KPI riassuntivi in alto
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Media PTS 5G", f"{v(tools_df, '1'):.1f}",
                  help="Media punti nelle ultime 5 partite del giocatore.")
        k2.metric("Media PTS Stag.", f"{v(tools_df, '3'):.1f}",
                  help="Media punti su tutta la stagione (tutte le partite in archivio).")
        k3.metric("Hit Rate PTS", f"{v(tools_df, '10'):.0f}%", help=TOOLTIPS["hit_rate"])
        k4.metric("Prob Poisson PTS", f"{v(tools_df, '13'):.0f}%", help=TOOLTIPS["poisson"])
        k5.metric("Trend PTS (3G-10G)", f"{v(tools_df, '16'):+.2f}", help=TOOLTIPS["trend"])
        k6.metric("Confidenza", f"{v(tools_df, '40'):.0f}/100", help=TOOLTIPS["confidenza"])

        st.markdown("---")
        st.markdown("##### 📊 Medie a confronto · Ultime 5G · Ultime 10G · Stagione")
        fig_avg = go.Figure()
        for label, color, keys in [
            ("Ultime 5G",  "#00D4AA", ["1", "4", "7"]),
            ("Ultime 10G", "#3B9EFF", ["2", "5", "8"]),
            ("Stagione",   "#FFD600", ["3", "6", "9"]),
        ]:
            ys = [v(tools_df, k) for k in keys]
            fig_avg.add_trace(go.Bar(
                name=label, x=["Punti", "Rimbalzi", "Assist"], y=ys,
                marker_color=color,
                text=[f"{y:.1f}" for y in ys], textposition="outside",
            ))
        fig_avg.update_layout(barmode="group", height=320, template="plotly_dark",
                              legend=dict(orientation="h", y=1.12),
                              margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_avg, width="stretch")

        st.markdown("##### 🎯 Probabilità Over · Modello (Poisson) vs Storico (Hit Rate)")
        st.caption("Se entrambe le barre per una stat sono > 50% → segnale forte Over. "
                   "Se sono molto diverse, il modello sta vedendo qualcosa di nuovo.")
        fig_prob = go.Figure()
        poisson_ys = [v(tools_df, "13"), v(tools_df, "14"), v(tools_df, "15")]
        hit_ys     = [v(tools_df, "10"), v(tools_df, "11"), v(tools_df, "12")]
        fig_prob.add_trace(go.Bar(
            name="Modello Poisson", x=["Punti", "Rimbalzi", "Assist"], y=poisson_ys,
            marker_color="#00D4AA",
            text=[f"{y:.0f}%" for y in poisson_ys], textposition="outside",
        ))
        fig_prob.add_trace(go.Bar(
            name="Hit Rate storico", x=["Punti", "Rimbalzi", "Assist"], y=hit_ys,
            marker_color="#FF9F40",
            text=[f"{y:.0f}%" for y in hit_ys], textposition="outside",
        ))
        fig_prob.add_hline(y=50, line_dash="dash", line_color="white",
                           annotation_text="50% (testa o croce)", annotation_position="top right")
        fig_prob.update_layout(barmode="group", height=340, template="plotly_dark",
                               yaxis_title="Probabilità Over %", yaxis_range=[0, 110],
                               legend=dict(orientation="h", y=1.12),
                               margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_prob, width="stretch")

        st.markdown("##### 📈 Trend recente (ultime 3G vs 10G)")
        st.caption("Verde = in salita · Rosso = in calo. Misura il momentum di breve termine.")
        trend_vals = [v(tools_df, "16"), v(tools_df, "17"), v(tools_df, "18")]
        trend_colors = ["#00D4AA" if x >= 0 else "#FF5252" for x in trend_vals]
        fig_t = go.Figure(go.Bar(
            x=["Punti", "Rimbalzi", "Assist"], y=trend_vals,
            marker_color=trend_colors,
            text=[f"{x:+.2f}" for x in trend_vals], textposition="outside",
        ))
        fig_t.add_hline(y=0, line_color="white", line_width=1)
        fig_t.update_layout(height=280, template="plotly_dark", showlegend=False,
                            margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_t, width="stretch")

        st.markdown("##### 🏠 Casa vs ✈️ Trasferta · Media Punti")
        h_pts = v(tools_df, "37")
        a_pts = v(tools_df, "38")
        fig_ha = go.Figure(go.Bar(
            x=["🏠 Casa", "✈️ Trasferta"], y=[h_pts, a_pts],
            marker_color=["#00D4AA", "#FF9F40"],
            text=[f"{h_pts:.1f}", f"{a_pts:.1f}"], textposition="outside",
        ))
        fig_ha.update_layout(height=240, template="plotly_dark", showlegend=False,
                             margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_ha, width="stretch")

        st.markdown("##### 🔥 Streak attuali (consecutive partite Over/Under)")
        sg1, sg2, sg3 = st.columns(3)
        sg1.metric("PUNTI",     _streak_label(int(v(tools_df,"31")), int(v(tools_df,"32")), "PTS"))
        sg2.metric("RIMBALZI",  _streak_label(int(v(tools_df,"33")), int(v(tools_df,"34")), "REB"))
        sg3.metric("ASSIST",    _streak_label(int(v(tools_df,"35")), int(v(tools_df,"36")), "AST"))

        st.markdown("##### 🎚️ Volatilità & Z-Score (Punti)")
        cv_pts = v(tools_df, "22")
        conf   = v(tools_df, "40")
        z      = v(tools_df, "39")
        cv1, cv2, cv3 = st.columns(3)
        cv1.metric("Confidenza", f"{conf:.0f}/100", help=TOOLTIPS["confidenza"])
        cv2.metric("CV (volatilità)", f"{cv_pts:.2f}", help=TOOLTIPS["cv"])
        cv3.metric("Z-Score linea", f"{z:+.2f}", help=TOOLTIPS["z_score"])

        score_core = (
            v(tools_df, "13") * 0.25
            + v(tools_df, "10") * 0.25
            + max(0.0, v(tools_df, "40")) * 0.25
            + max(0.0, min(100.0, 50 + v(tools_df, "16") * 5)) * 0.25
        )
        st.markdown("---")
        st.markdown(f"#### 💎 Indice Pro Complessivo · **{score_core:.1f}/100**")
        if score_core >= 65:
            st.success("🚀 **Segnale forte favorevole all'Over PTS** · Tutti gli indicatori convergono.")
        elif score_core >= 50:
            st.info("⚖️ **Segnale moderato** · Alcuni indicatori positivi, valuta la quota.")
        elif score_core >= 35:
            st.warning("⚠️ **Segnale debole** · Indicatori contrastanti, meglio cautela.")
        else:
            st.error("❌ **Segnale contrario all'Over** · Forma e probabilità sotto soglia.")

        with st.expander("📋 Vedi tabella numerica completa (40 indicatori)"):
            st.dataframe(tools_df, width="stretch", hide_index=True)

        st.download_button(
            "⬇️ Esporta Toolkit Base (CSV)",
            data=df_to_csv(tools_df),
            file_name=f"{name.replace(' ', '_')}_toolkit_base.csv",
            mime="text/csv",
        )

    # ── TAB 2: Contesto & Value Bet ──────────────────────────────────────
    with t_ctx:
        st.markdown("##### 🩹 Input contesto partita")
        st.caption("Inserisci assenze e fattori della partita (o lascia auto-detect dai team scelti in '🏀 Squadre' / '⚔️ Confronto'). "
                   "Il modello applica un aggiustamento euristico alle probabilità.")
        auto_inj = st.checkbox("Auto-import injury report (beta)", value=True, key="auto_inj_beta")
        auto_summary = {}
        if auto_inj:
            tm_id = st.session_state.get("team_1_id")
            opp_id = st.session_state.get("team_2_id")
            if tm_id and opp_id:
                inj_tm = fetch_team_injuries(int(tm_id), SEASON)
                inj_opp = fetch_team_injuries(int(opp_id), SEASON)
                auto_tm = infer_injury_impact(inj_tm)
                auto_opp = infer_injury_impact(inj_opp)
                auto_summary = {
                    "teammate_out_count": auto_tm["out_count"],
                    "opp_out_count": auto_opp["out_count"],
                    "teammate_usage_loss": auto_tm["usage_loss_pct"],
                    "opp_def_weakness": auto_opp["weighted_impact"],
                    "expected_min_delta": min(10.0, auto_tm["out_count"] * 1.2 + auto_tm["questionable_count"] * 0.4),
                    "team_notes": auto_tm["notes"],
                    "opp_notes": auto_opp["notes"],
                }
                with st.expander("Dettaglio injury auto (beta)"):
                    st.write("**Team selezionato:**")
                    for note in auto_summary["team_notes"][:6]:
                        st.write(f"- {note}")
                    st.write("**Avversario selezionato:**")
                    for note in auto_summary["opp_notes"][:6]:
                        st.write(f"- {note}")
            else:
                st.caption("Per auto-injury, seleziona Team 1 e Team 2 in sidebar.")

        c1, c2, c3 = st.columns(3)
        teammate_out_count = c1.number_input("Compagni OUT", min_value=0, max_value=12,
            value=int(auto_summary.get("teammate_out_count", 1)), step=1)
        opp_out_count = c2.number_input("Avversari OUT", min_value=0, max_value=12,
            value=int(auto_summary.get("opp_out_count", 1)), step=1)
        b2b_flag = c3.checkbox("Back-to-back", value=False,
                               help="Seconda partita consecutiva: spesso minore rendimento.")
        c4, c5, c6 = st.columns(3)
        teammate_usage_loss = c4.slider("Usage perso compagni %", 0, 60,
            int(round(auto_summary.get("teammate_usage_loss", 12))),
            help="Quanto usage liberano i compagni assenti (più è alto più il giocatore aumenta tiri/passaggi).")
        opp_def_weakness = c5.slider("Debolezza difesa avversaria %", 0, 60,
            int(round(auto_summary.get("opp_def_weakness", 10))),
            help="Quanto è debole la difesa avversaria considerando le loro assenze.")
        expected_min_delta = c6.slider("Delta minuti atteso", -8, 12,
            int(round(auto_summary.get("expected_min_delta", 2))),
            help="Minuti in più o meno rispetto alla sua media.")
        market_odds = st.number_input("Quota mercato (es. 1.90)", min_value=1.01, value=1.90, step=0.01)

        ctx_df = build_50_context_tools(
            name=name, df_all=df_all, df_r=df_r, linee=linee,
            teammate_out_count=int(teammate_out_count),
            opp_out_count=int(opp_out_count),
            teammate_usage_loss=float(teammate_usage_loss),
            opp_def_weakness=float(opp_def_weakness),
            expected_min_delta=float(expected_min_delta),
            b2b_flag=bool(b2b_flag),
        )

        # Probabilità prima/dopo aggiustamento contesto (PTS)
        prob_base_pts = _tool_value(build_40_tools(name, df_all, df_r, linee), "13")
        prob_adj_pts  = _tool_value(ctx_df, "22")
        delta_pts = prob_adj_pts - prob_base_pts

        st.markdown("---")
        st.markdown("##### 🔄 Impatto del contesto sulla probabilità Over PUNTI")
        fig_ctx = go.Figure(go.Bar(
            x=["Probabilità base", "Dopo contesto"],
            y=[prob_base_pts, prob_adj_pts],
            marker_color=["#3B9EFF", "#00D4AA" if delta_pts >= 0 else "#FF5252"],
            text=[f"{prob_base_pts:.1f}%", f"{prob_adj_pts:.1f}% ({delta_pts:+.1f}pp)"],
            textposition="outside",
        ))
        fig_ctx.add_hline(y=50, line_dash="dash", line_color="white",
                          annotation_text="50%", annotation_position="top right")
        fig_ctx.update_layout(height=320, template="plotly_dark", showlegend=False,
                              yaxis_title="Probabilità %", yaxis_range=[0, 110],
                              margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_ctx, width="stretch")

        # Verdetto value bet
        implied_prob = 100 / market_odds if market_odds > 1 else 0.0
        edge = prob_adj_pts - implied_prob
        fair_odds = 100 / max(prob_adj_pts, 0.1)

        ev_c1, ev_c2, ev_c3 = st.columns(3)
        ev_c1.metric("Prob. Modello (PTS)", f"{prob_adj_pts:.1f}%",
                     help="La TUA probabilità stimata (Poisson + correzioni di contesto). È la probabilità che il giocatore superi la linea Over secondo il modello.")
        ev_c2.metric("Prob. implicita quota", f"{implied_prob:.1f}%",
                     help="Probabilità ricavata dalla quota del bookmaker: 100/quota. Esempio: quota 1.90 → 52.6%.")
        ev_c3.metric("Edge", f"{edge:+.1f}pp", delta=f"fair ~{fair_odds:.2f}",
                     help=TOOLTIPS["edge"])

        if edge >= 7:
            st.success(f"🟢 **VALUE BET FORTE (PTS)** · edge +{edge:.1f}pp · fair odds ~ {fair_odds:.2f}")
        elif edge >= 3:
            st.info(f"🔵 **VALUE BET MODERATA (PTS)** · edge +{edge:.1f}pp · fair odds ~ {fair_odds:.2f}")
        elif edge <= -7:
            st.error(f"🔴 **NO BET (PTS)** · edge {edge:.1f}pp · quota troppo bassa")
        else:
            st.warning(f"🟡 **EDGE LIMITATA (PTS)** · edge {edge:+.1f}pp")

        with st.expander("📋 Vedi tabella numerica completa (50 indicatori contesto)"):
            st.dataframe(ctx_df, width="stretch", hide_index=True)

        st.download_button(
            "⬇️ Esporta Toolkit Contesto (50) CSV",
            data=df_to_csv(ctx_df),
            file_name=f"{name.replace(' ', '_')}_toolkit_contesto_50.csv",
            mime="text/csv",
        )

    # ── TAB 3: Indicatori Avanzati ───────────────────────────────────────
    with t_adv:
        adv_df = build_advanced_20_tools(df_all, df_r, linee)
        v_adv = _tool_value

        # Hero: 3 indici Over (PTS/REB/AST) come metric grandi
        st.markdown("##### 🎯 Indici Over consolidati (Poisson + Hit Rate combinati)")
        ic1, ic2, ic3 = st.columns(3)
        idx_pts = v_adv(adv_df, "A17")
        idx_reb = v_adv(adv_df, "A18")
        idx_ast = v_adv(adv_df, "A19")

        def _signal(val):
            if val >= 65: return "🟢 Forte"
            if val >= 50: return "🔵 Moderato"
            if val >= 35: return "🟡 Debole"
            return "🔴 Contrario"

        ic1.metric("PUNTI",    f"{idx_pts:.0f}/100", delta=_signal(idx_pts))
        ic2.metric("RIMBALZI", f"{idx_reb:.0f}/100", delta=_signal(idx_reb))
        ic3.metric("ASSIST",   f"{idx_ast:.0f}/100", delta=_signal(idx_ast))

        st.markdown("---")
        st.markdown("##### 📊 Combo statistiche multiple (PRA / PA / PR)")
        st.caption("PRA = Punti+Rimbalzi+Assist (mercato comune). PA = Punti+Assist. PR = Punti+Rimbalzi.")
        combo_vals = [v_adv(adv_df, "A1"), v_adv(adv_df, "A2"), v_adv(adv_df, "A3")]
        fig_combo = go.Figure(go.Bar(
            x=["PRA", "PA", "PR"], y=combo_vals,
            marker_color=["#00D4AA", "#3B9EFF", "#FF9F40"],
            text=[f"{v:.1f}" for v in combo_vals], textposition="outside",
        ))
        fig_combo.update_layout(height=280, template="plotly_dark", showlegend=False,
                                margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_combo, width="stretch")

        st.markdown("##### 📈 Trend slope · correlazione di tendenza ultime 10G")
        st.caption("Scala da -1 (in netto calo) a +1 (in netto salita). Misura se la curva di performance sta puntando in alto o in basso.")
        slope_vals = [v_adv(adv_df, "A5"), v_adv(adv_df, "A6"), v_adv(adv_df, "A7")]
        slope_colors = ["#00D4AA" if x >= 0 else "#FF5252" for x in slope_vals]
        fig_slope = go.Figure(go.Bar(
            x=["Punti", "Rimbalzi", "Assist"], y=slope_vals,
            marker_color=slope_colors,
            text=[f"{v:+.2f}" for v in slope_vals], textposition="outside",
        ))
        fig_slope.add_hline(y=0, line_color="white", line_width=1)
        fig_slope.update_layout(height=280, template="plotly_dark", showlegend=False,
                                yaxis_range=[-1.1, 1.1],
                                margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_slope, width="stretch")

        st.markdown("##### 🚀 Distribuzione % delle partite (Punti)")
        st.caption("Quanto spesso il giocatore esplode (sopra media+1σ) o crolla (sotto media-1σ).")
        dist_vals = [v_adv(adv_df, "A12"), v_adv(adv_df, "A13"), v_adv(adv_df, "A14"),
                     v_adv(adv_df, "A11")]
        dist_labels = ["Sopra la media", "Esplosive (>μ+σ)", "Bust (<μ-σ)", "Over linea (10G)"]
        dist_colors = ["#3B9EFF", "#00D4AA", "#FF5252", "#FFD600"]
        fig_d = go.Figure(go.Bar(
            x=dist_labels, y=dist_vals,
            marker_color=dist_colors,
            text=[f"{v:.0f}%" for v in dist_vals], textposition="outside",
        ))
        fig_d.add_hline(y=50, line_dash="dash", line_color="white",
                        annotation_text="50%", annotation_position="top right")
        fig_d.update_layout(height=320, template="plotly_dark", showlegend=False,
                            yaxis_title="% partite", yaxis_range=[0, 110],
                            margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_d, width="stretch")

        st.markdown("##### 💎 Synergy & Ritmo")
        sy1, sy2, sy3 = st.columns(3)
        sy1.metric("Synergy Score", f"{v_adv(adv_df, 'A20'):.0f}/100",
                   help="Stabilità combinata di PRA. Alto = performance prevedibile su tutte le 3 stat.")
        sy2.metric("Pts per minuto", f"{v_adv(adv_df, 'A4'):.3f}",
                   help="Efficienza realizzativa. Sopra 0.7 = top scorer.")
        sy3.metric("Recent vs Stagione (PTS)", f"{v_adv(adv_df, 'A15'):+.1f}",
                   help="Differenza media ultime 5G vs stagione. Positivo = in forma.")

        with st.expander("📋 Vedi tabella numerica completa (20 indicatori avanzati)"):
            st.dataframe(adv_df, width="stretch", hide_index=True)

        st.download_button(
            "⬇️ Esporta Toolkit Avanzato (20) CSV",
            data=df_to_csv(adv_df),
            file_name=f"{name.replace(' ', '_')}_toolkit_avanzato_20.csv",
            mime="text/csv",
        )


def build_advanced_20_tools(df_all: pd.DataFrame, df_r: pd.DataFrame, linee: dict):
    pts_l = linee.get("PTS", 0)
    reb_l = linee.get("REB", 0)
    ast_l = linee.get("AST", 0)

    pts_series = df_r["PTS"] if "PTS" in df_r.columns else pd.Series(dtype=float)
    reb_series = df_r["REB"] if "REB" in df_r.columns else pd.Series(dtype=float)
    ast_series = df_r["AST"] if "AST" in df_r.columns else pd.Series(dtype=float)
    min_series = pd.to_numeric(df_r["MIN"], errors="coerce") if "MIN" in df_r.columns else pd.Series(dtype=float)

    def _safe_mean(s):
        return float(s.mean()) if not s.empty else 0.0

    def _safe_std(s):
        return float(s.std(ddof=0)) if len(s) > 1 else 0.0

    def _last_n(s, n):
        return float(s.head(n).mean()) if not s.empty else 0.0

    def _trend_slope(s, n=10):
        if s.empty:
            return 0.0
        sub = s.head(min(n, len(s))).reset_index(drop=True)
        if len(sub) < 3:
            return 0.0
        idx = list(range(len(sub)))
        return float(pd.Series(sub).corr(pd.Series(idx)) or 0.0)

    pts_mean = _safe_mean(pts_series)
    pts_std = _safe_std(pts_series)
    reb_mean = _safe_mean(reb_series)
    reb_std = _safe_std(reb_series)
    ast_mean = _safe_mean(ast_series)
    min_mean = _safe_mean(min_series)
    min_std = _safe_std(min_series)

    pra = (pts_mean + reb_mean + ast_mean)
    pa = (pts_mean + ast_mean)
    pr = (pts_mean + reb_mean)
    pts_per_min = (pts_mean / min_mean) if min_mean > 0 else 0.0
    over_streak3 = float((pts_series.head(3) > pts_l).mean() * 100) if len(pts_series) >= 1 else 0.0
    over_streak5 = float((pts_series.head(5) > pts_l).mean() * 100) if len(pts_series) >= 1 else 0.0
    over_streak10 = float((pts_series.head(10) > pts_l).mean() * 100) if len(pts_series) >= 1 else 0.0
    above_avg_pct = float((pts_series > pts_mean).mean() * 100) if not pts_series.empty else 0.0
    explosive_pct = float((pts_series >= pts_mean + max(pts_std, 1)).mean() * 100) if not pts_series.empty else 0.0

    last_5 = _last_n(pts_series, 5)
    last_10 = _last_n(pts_series, 10)
    season_avg = _safe_mean(df_all["PTS"]) if "PTS" in df_all.columns else 0.0

    tools = [
        ("A1", "PRA medio (PTS+REB+AST)", round(pra, 2)),
        ("A2", "PA medio (PTS+AST)", round(pa, 2)),
        ("A3", "PR medio (PTS+REB)", round(pr, 2)),
        ("A4", "Pts per minuto", round(pts_per_min, 3)),
        ("A5", "Trend slope PTS (corr 10G)", round(_trend_slope(pts_series, 10), 3)),
        ("A6", "Trend slope REB (corr 10G)", round(_trend_slope(reb_series, 10), 3)),
        ("A7", "Trend slope AST (corr 10G)", round(_trend_slope(ast_series, 10), 3)),
        ("A8", "Std minuti", round(min_std, 2)),
        ("A9", "% partite > linea PTS (3G)", round(over_streak3, 1)),
        ("A10", "% partite > linea PTS (5G)", round(over_streak5, 1)),
        ("A11", "% partite > linea PTS (10G)", round(over_streak10, 1)),
        ("A12", "% sopra media PTS", round(above_avg_pct, 1)),
        ("A13", "% game esplosive (>media+1σ)", round(explosive_pct, 1)),
        ("A14", "Bust rate PTS (≤media-1σ) %", round(float((pts_series <= pts_mean - pts_std).mean() * 100) if not pts_series.empty else 0.0, 1)),
        ("A15", "Recent vs Season PTS", round(last_5 - season_avg, 2)),
        ("A16", "Var ratio recent/season", round((pts_std / max(_safe_std(df_all["PTS"]), 0.01)) if "PTS" in df_all.columns else 0.0, 2)),
        ("A17", "Indice Over PTS (Poisson + hit)", round(((1 - poisson.cdf(pts_l, pts_mean)) * 100 if pts_mean > 0 else 0) * 0.5 + (over_streak10 * 0.5), 1)),
        ("A18", "Indice Over REB (Poisson + hit)", round(((1 - poisson.cdf(reb_l, reb_mean)) * 100 if reb_mean > 0 else 0) * 0.5 + (float((reb_series.head(10) > reb_l).mean() * 100) if len(reb_series) >= 1 else 0) * 0.5, 1)),
        ("A19", "Indice Over AST (Poisson + hit)", round(((1 - poisson.cdf(ast_l, ast_mean)) * 100 if ast_mean > 0 else 0) * 0.5 + (float((ast_series.head(10) > ast_l).mean() * 100) if len(ast_series) >= 1 else 0) * 0.5, 1)),
        ("A20", "Synergy Score (PRA stability)", round(max(0.0, 100 - (pts_std + reb_std)), 1)),
    ]
    return pd.DataFrame(tools, columns=["#", "Tool", "Valore"])


def export_summary(name, df_r, df_all, linee, n):
    rows = [["Giocatore", name], ["Stagione", SEASON],
            ["Partite analizzate", n], ["Data", str(datetime.date.today())], ["", ""]]
    for col in ["PTS", "REB", "AST"]:
        if col not in df_r.columns:
            continue
        linea = linee.get(col, 0)
        avg   = df_r[col].mean()
        prob  = (1 - poisson.cdf(linea, avg)) * 100
        hit   = len(df_r[df_r[col] > linea]) / len(df_r) * 100 if len(df_r) > 0 else 0
        form  = form_score(df_r, col)
        score, lbl, *_ = verdict_data(prob, hit, form)
        avg_s = df_all[col].mean()
        _, lbl_c, *_ = slump_info(avg_s, avg)
        rows += [
            [f"--- {STAT_LABELS.get(col, col)} ---", ""],
            ["Media", f"{avg:.2f}"], ["Linea Over", linea],
            ["Prob. Over", f"{prob:.1f}%"], ["Hit Rate", f"{hit:.0f}%"],
            ["Forma", f"{form:.0f}/100"], ["Score", f"{score:.0f}/100"],
            ["Verdetto", lbl], ["Contropronostico", lbl_c], ["", ""],
        ]
    buf = io.StringIO()
    pd.DataFrame(rows, columns=["Metrica", "Valore"]).to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  BANKROLL TRACKER
# ══════════════════════════════════════════════════════════════════════════════

def _load_bankroll_state():
    """Legge bankroll_start e bets dal file JSON (se esiste)."""
    try:
        if os.path.exists(BANKROLL_FILE):
            with open(BANKROLL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            return (
                float(data.get("bankroll_start", 1000.0)),
                list(data.get("bets", [])),
            )
    except Exception:
        pass
    return 1000.0, []


def _save_bankroll_state() -> bool:
    """Persiste bankroll_start e bets su file JSON. Su Streamlit Cloud il
    filesystem è effimero (al redeploy si perde): usare l'export CSV come backup."""
    try:
        data = {
            "bankroll_start": float(st.session_state.get("bankroll_start", 1000.0)),
            "bets": list(st.session_state.get("bets", [])),
            "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "version": VERSION,
        }
        with open(BANKROLL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def init_bankroll():
    if "bankroll_start" not in st.session_state or "bets" not in st.session_state:
        bk_start, bets = _load_bankroll_state()
        if "bankroll_start" not in st.session_state:
            st.session_state.bankroll_start = bk_start
        if "bets" not in st.session_state:
            st.session_state.bets = bets


# ── Telegram notifications ────────────────────────────────────────────────────
def _get_telegram_creds():
    """Ritorna (token, chat_id) con priorità: parametri runtime (session_state) → env."""
    token = st.session_state.get("tg_token_override", "") or TELEGRAM_BOT_TOKEN
    chat  = st.session_state.get("tg_chat_override", "")  or TELEGRAM_CHAT_ID
    return (token or "").strip(), (chat or "").strip()


def send_telegram_message(text: str, bot_token: str = "", chat_id: str = "",
                          parse_mode: str = "HTML"):
    """Invia un messaggio al bot Telegram. Ritorna (ok: bool, info: str)."""
    if not bot_token or not chat_id:
        tk, ch = _get_telegram_creds()
        bot_token = (bot_token or tk).strip()
        chat_id   = (chat_id   or ch).strip()
    bot_token = (bot_token or "").strip()
    chat_id   = (chat_id or "").strip()
    if not bot_token or not chat_id:
        return False, "Telegram non configurato (token / chat_id mancanti)."
    if not text:
        return False, "Messaggio vuoto."
    url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
    # Telegram limite messaggio ~4096 char: tronchiamo per sicurezza
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=REQ_TIMEOUT)
        if r.status_code == 200 and r.json().get("ok"):
            return True, "Messaggio inviato."
        try:
            desc = r.json().get("description", r.text)
        except Exception:
            desc = r.text
        return False, f"HTTP {r.status_code}: {desc}"
    except requests.RequestException as exc:
        return False, f"Errore rete: {exc}"
    except Exception as exc:
        return False, f"Errore: {exc}"


def _format_alerts_for_telegram(df: pd.DataFrame, max_rows: int = 10,
                                title: str = "🚨 Value Alert NBA",
                                source: str = "Manuale") -> str:
    """Costruisce il testo HTML da inviare su Telegram."""
    if df is None or df.empty:
        return ""
    today = datetime.date.today().strftime("%d/%m/%Y")
    lines = [f"<b>{title}</b> · {today} · <i>{source}</i>"]
    for _, r in df.head(max_rows).iterrows():
        giocatore = r.get("Giocatore", "?")
        stat      = r.get("Stat", "")
        linea     = r.get("Linea", "?")
        odd       = r.get("Quota Over", r.get("Quota", "?"))
        prob      = r.get("Prob Over %", "?")
        edge      = r.get("Edge %", "?")
        kelly     = r.get("Kelly €", 0) or 0
        signal    = r.get("Signal", "")
        bookmaker = r.get("Bookmaker", "")
        match     = r.get("Match", "")
        team      = r.get("Team", "")
        meta_bits = [b for b in [bookmaker, team, match] if b]
        meta = " · ".join(meta_bits)
        try:
            kelly_str = f"€{float(kelly):.2f}"
        except Exception:
            kelly_str = "—"
        line = (
            f"\n• <b>{giocatore}</b> {stat} OVER {linea} @ <b>{odd}</b>"
            f"\n   Prob {prob}% · Edge {edge}% · Kelly {kelly_str} · {signal}"
        )
        if meta:
            line += f"\n   <i>{meta}</i>"
        verifica = str(r.get("Verifica", "") or "").strip()
        if verifica:
            line += f"\n   ⚠️ <i>{verifica}</i>"
        bk_pl = str(r.get("Su bookmaker", "") or "").strip()
        if bk_pl and bk_pl != str(giocatore):
            line += f"\n   📌 Odds API name: <i>{bk_pl}</i>"
        lines.append(line)
    lines.append(f"\n<i>NBA Whale Pro v{VERSION}</i>")
    return "\n".join(lines)


def _recompute_bet_pnl(bet: dict) -> dict:
    """Ricalcola P&L coerentemente con stake/quota/risultato."""
    stake = float(bet.get("Stake €", 0) or 0)
    quota = float(bet.get("Quota", 0) or 0)
    res   = bet.get("Risultato", "In attesa")
    if res == "Vinto":
        bet["P&L €"] = round(stake * (quota - 1), 2)
    elif res == "Perso":
        bet["P&L €"] = round(-stake, 2)
    else:
        bet["P&L €"] = 0.0
    return bet


def bankroll_page():
    init_bankroll()
    st.subheader("💰 Bankroll Analytics")
    st.caption(
        "Dashboard operativa stile analytics: KPI, equity curve, breakdown per mercato/bookmaker "
        "e gestione completa dello storico."
    )

    if os.path.exists(BANKROLL_FILE):
        try:
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(BANKROLL_FILE))
            st.caption(f"💾 Auto-save locale attivo · ultimo salvataggio {mod_time.strftime('%d/%m/%Y %H:%M:%S')}")
        except Exception:
            pass
    else:
        st.caption("💾 Auto-save locale attivo (il file verrà creato al primo inserimento).")

    st.info(
        "Su Streamlit Cloud il file locale può resettarsi dopo deploy/restart. "
        "Usa **Esporta CSV** come backup periodico e **Importa CSV** per ripristino rapido."
    )

    with st.expander("⚙️ Setup bankroll", expanded=len(st.session_state.bets) == 0):
        new_start = st.number_input(
            "Bankroll iniziale (€)",
            value=float(st.session_state.bankroll_start),
            min_value=1.0,
            step=50.0,
        )
        if st.button("Aggiorna bankroll iniziale"):
            st.session_state.bankroll_start = float(new_start)
            _save_bankroll_state()
            st.rerun()

    st.markdown("#### ➕ Inserisci scommessa")
    with st.form("add_bet"):
        b0, b1, b2, b3 = st.columns(4)
        formato = b0.selectbox("Formato", ["Singola", "Multipla"])
        giocatore = b1.text_input("Giocatore")
        stat_bet = b2.selectbox("Mercato", ["Punti", "Rimbalzi", "Assist"])
        esito = b3.selectbox("Direzione", ["Over", "Under"])
        if formato == "Multipla":
            n_legs = int(st.number_input("Numero selezioni", min_value=2, max_value=10, value=2, step=1))
            st.caption("Compila le selezioni della schedina:")
            legs = []
            market_short = {"Punti": "PTS", "Rimbalzi": "REB", "Assist": "AST"}
            for i in range(n_legs):
                l1, l2, l3, l4 = st.columns([2.2, 1.3, 1.1, 1.2])
                lg_player = l1.text_input(f"Giocatore #{i+1}", key=f"mul_player_{i}")
                lg_market = l2.selectbox(f"Mercato #{i+1}", ["Punti", "Rimbalzi", "Assist"], key=f"mul_market_{i}")
                lg_side = l3.selectbox(f"Tipo #{i+1}", ["Over", "Under"], key=f"mul_side_{i}")
                lg_line = l4.number_input(f"Linea #{i+1}", value=10.5, step=0.5, key=f"mul_line_{i}")
                if str(lg_player).strip():
                    legs.append({
                        "player": str(lg_player).strip(),
                        "market": lg_market,
                        "side": lg_side,
                        "line": float(lg_line),
                    })
            dettagli_multipla = "\n".join(
                f"{x['player']} {x['side'].upper()} {x['line']} {market_short.get(x['market'], x['market'])}"
                for x in legs
            )
        else:
            n_legs = 1
            legs = []
            dettagli_multipla = ""
        c1, c2, c3, c4 = st.columns(4)
        linea_b = c1.number_input("Linea", value=20.0, step=0.5)
        quota = c2.number_input("Quota", value=1.90, step=0.05, min_value=1.01)
        stake = c3.number_input("Stake (€)", value=20.0, step=5.0, min_value=1.0)
        risultato = c4.selectbox("Risultato", ["In attesa", "Vinto", "Perso"])
        d1, d2 = st.columns(2)
        bookmaker = d1.text_input("Bookmaker (opzionale)")
        note = d2.text_input("Note (opzionale)")
        submit_bet = st.form_submit_button("Aggiungi scommessa")
        if submit_bet:
            if formato == "Singola" and not str(giocatore).strip():
                st.warning("Per una singola inserisci il giocatore.")
            elif formato == "Multipla" and len(legs) < 2:
                st.warning("Per una multipla inserisci almeno 2 selezioni complete.")
            else:
                profit = (round(stake * (quota - 1), 2) if risultato == "Vinto"
                          else (-stake if risultato == "Perso" else 0.0))
                stat_store = stat_bet if formato == "Singola" else "Multipla"
                tipo_store = esito if formato == "Singola" else "Parlay"
                giocatore_store = giocatore if formato == "Singola" else "MULTIPLA"
                st.session_state.bets.append({
                    "Data": str(datetime.date.today()),
                    "Formato": formato,
                    "Giocatore": giocatore_store,
                    "Stat": stat_store,
                    "Tipo": tipo_store,
                    "Linea": linea_b if formato == "Singola" else 0.0,
                    "Quota": quota,
                    "Stake €": stake,
                    "Risultato": risultato,
                    "P&L €": profit,
                    "Bookmaker": bookmaker,
                    "Numero Selezioni": int(n_legs) if formato == "Multipla" else 1,
                    "Dettagli Multipla": dettagli_multipla if formato == "Multipla" else "",
                    "Note": note,
                })
                _save_bankroll_state()
                label_ok = giocatore_store if formato == "Singola" else "multipla"
                st.success(f"✅ Scommessa {label_ok} registrata.")
                st.rerun()

    if not st.session_state.bets:
        st.info("Nessuna scommessa ancora. Inserisci dal form o importa CSV.")
        up = st.file_uploader(
            "📤 Importa storico da CSV",
            type=["csv"],
            key="bk_import_empty",
        )
        if up is not None:
            try:
                df_in = pd.read_csv(up)
                required = {"Data", "Giocatore", "Stat", "Tipo", "Linea", "Quota", "Stake €", "Risultato"}
                if not required.issubset(set(df_in.columns)):
                    st.error(f"Colonne mancanti. Servono: {sorted(required)}")
                else:
                    rows = df_in.to_dict("records")
                    for row in rows:
                        _recompute_bet_pnl(row)
                    st.session_state.bets = rows
                    _save_bankroll_state()
                    st.success(f"✅ Importate {len(rows)} scommesse.")
                    st.rerun()
            except Exception as exc:
                st.error(f"Errore import CSV: {exc}")
        return

    df_bets = pd.DataFrame(st.session_state.bets).copy()
    if "Bookmaker" not in df_bets.columns:
        df_bets["Bookmaker"] = ""
    if "Formato" not in df_bets.columns:
        df_bets["Formato"] = "Singola"
    if "Dettagli Multipla" not in df_bets.columns:
        df_bets["Dettagli Multipla"] = ""
    if "Numero Selezioni" not in df_bets.columns:
        df_bets["Numero Selezioni"] = 1
    if "Note" not in df_bets.columns:
        df_bets["Note"] = ""
    if "Data" in df_bets.columns:
        df_bets["Data_dt"] = pd.to_datetime(df_bets["Data"], errors="coerce")
    else:
        df_bets["Data_dt"] = pd.NaT
    df_bets = df_bets.sort_values("Data_dt", ascending=False).reset_index(drop=True)

    with st.expander("🔎 Filtri analisi", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        period_opt = f1.selectbox("Periodo", ["Tutto", "Ultimi 7 giorni", "Ultimi 30 giorni", "Ultimi 90 giorni"], index=0)
        stat_opts = sorted([s for s in df_bets["Stat"].dropna().unique().tolist() if s])
        stat_sel = f2.multiselect("Mercato", stat_opts, default=stat_opts)
        book_opts = sorted([b for b in df_bets["Bookmaker"].fillna("").unique().tolist() if str(b).strip()])
        book_sel = f3.multiselect("Bookmaker", book_opts, default=book_opts)
        res_sel = f4.multiselect("Risultato", ["In attesa", "Vinto", "Perso"], default=["In attesa", "Vinto", "Perso"])

    df_view = df_bets.copy()
    if period_opt != "Tutto":
        days = {"Ultimi 7 giorni": 7, "Ultimi 30 giorni": 30, "Ultimi 90 giorni": 90}[period_opt]
        cutoff = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=days))
        df_view = df_view[df_view["Data_dt"] >= cutoff]
    if stat_sel:
        df_view = df_view[df_view["Stat"].isin(stat_sel)]
    if book_sel:
        df_view = df_view[df_view["Bookmaker"].fillna("").isin(book_sel)]
    if res_sel:
        df_view = df_view[df_view["Risultato"].isin(res_sel)]

    chiuse = df_view[df_view["Risultato"] != "In attesa"].copy()
    pnl_tot = float(chiuse["P&L €"].sum()) if not chiuse.empty else 0.0
    stake_tot = float(chiuse["Stake €"].sum()) if not chiuse.empty else 0.0
    roi = (pnl_tot / stake_tot * 100) if stake_tot > 0 else 0.0
    bankroll_now = float(st.session_state.bankroll_start) + pnl_tot
    vinte = int((chiuse["Risultato"] == "Vinto").sum()) if not chiuse.empty else 0
    wr = (vinte / len(chiuse) * 100) if len(chiuse) > 0 else 0.0
    avg_odds = float(chiuse["Quota"].mean()) if not chiuse.empty else 0.0
    avg_stake = float(chiuse["Stake €"].mean()) if not chiuse.empty else 0.0
    yield_pct = (pnl_tot / stake_tot * 100) if stake_tot > 0 else 0.0
    pending_n = int((df_view["Risultato"] == "In attesa").sum()) if not df_view.empty else 0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Bankroll", f"€{bankroll_now:.2f}", delta=f"{pnl_tot:+.2f} €")
    k2.metric("Profit", f"€{pnl_tot:.2f}")
    k3.metric("ROI", f"{roi:.1f}%")
    k4.metric("Yield", f"{yield_pct:.1f}%")
    k5.metric("Win Rate", f"{wr:.0f}%")
    k6.metric("Pending", pending_n)
    k7, k8, k9 = st.columns(3)
    k7.metric("Bets chiuse", len(chiuse))
    k8.metric("Quota media", f"{avg_odds:.2f}" if avg_odds > 0 else "—")
    k9.metric("Stake medio", f"€{avg_stake:.2f}" if avg_stake > 0 else "—")

    st.markdown("---")

    c_left, c_right = st.columns([1.8, 1.2])
    with c_left:
        st.markdown("#### 📈 Equity Curve")
        st.caption(
            "Mostra l'andamento del bankroll nel tempo (una scommessa chiusa dopo l'altra). "
            "Linea in salita = crescita, in discesa = drawdown. "
            "La linea tratteggiata indica il bankroll iniziale."
        )
        if not chiuse.empty:
            chiuse_plot = chiuse.sort_values("Data_dt", ascending=True).copy()
            chiuse_plot["Equity"] = float(st.session_state.bankroll_start) + chiuse_plot["P&L €"].cumsum()
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=chiuse_plot["Data_dt"], y=chiuse_plot["Equity"],
                mode="lines+markers", name="Equity",
                line=dict(color="#00D4AA", width=2.5),
                fill="tozeroy", fillcolor="rgba(0,212,170,0.08)"
            ))
            fig_eq.add_hline(
                y=float(st.session_state.bankroll_start),
                line_dash="dash", line_color="#8B949E",
                annotation_text="Start"
            )
            fig_eq.update_layout(
                height=330, template="plotly_dark",
                xaxis_title="Data", yaxis_title="€",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_eq, width="stretch")
        else:
            st.info("Nessuna scommessa chiusa nel filtro corrente.")

    with c_right:
        st.markdown("#### 🧩 Breakdown Mercato")
        st.caption(
            "Confronta i risultati per mercato (Punti, Rimbalzi, Assist) per capire "
            "dove stai performando meglio: barre verdi = profit, rosse = perdita."
        )
        if not chiuse.empty:
            by_stat = chiuse.groupby("Stat", dropna=False).agg(
                Bets=("Stat", "count"),
                Stake=("Stake €", "sum"),
                Profit=("P&L €", "sum"),
            ).reset_index()
            by_stat["ROI %"] = by_stat.apply(
                lambda r: (r["Profit"] / r["Stake"] * 100) if r["Stake"] else 0.0,
                axis=1,
            )
            fig_stat = go.Figure(go.Bar(
                x=by_stat["Stat"], y=by_stat["Profit"],
                text=[f"€{v:.1f}" for v in by_stat["Profit"]],
                textposition="outside",
                marker_color=["#00D4AA" if v >= 0 else "#FF5252" for v in by_stat["Profit"]],
            ))
            fig_stat.update_layout(
                height=330, template="plotly_dark",
                yaxis_title="Profit €", margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_stat, width="stretch")
        else:
            st.info("Nessun breakdown disponibile.")

    st.markdown("#### 🏦 Breakdown Bookmaker")
    if not chiuse.empty and (chiuse["Bookmaker"].fillna("").str.strip() != "").any():
        by_book = chiuse.copy()
        by_book["Bookmaker"] = by_book["Bookmaker"].replace("", "N/A")
        book_tbl = by_book.groupby("Bookmaker", dropna=False).agg(
            Bets=("Bookmaker", "count"),
            Stake=("Stake €", "sum"),
            Profit=("P&L €", "sum"),
            WinRate=("Risultato", lambda x: (x == "Vinto").mean() * 100),
        ).reset_index().sort_values("Profit", ascending=False)
        book_tbl["ROI %"] = book_tbl.apply(
            lambda r: (r["Profit"] / r["Stake"] * 100) if r["Stake"] else 0.0,
            axis=1,
        )
        st.dataframe(book_tbl, width="stretch", hide_index=True)
    else:
        st.caption("Nessun bookmaker compilato nelle scommesse chiuse.")

    st.markdown("#### 🧠 Analyzer")
    if chiuse.empty:
        st.caption("Analyzer disponibile quando hai almeno 1 scommessa chiusa nel filtro attuale.")
    else:
        an1, an2 = st.columns(2)

        with an1:
            st.markdown("**Profit per fascia quota**")
            odds_bins = pd.cut(
                chiuse["Quota"].astype(float),
                bins=[1.0, 1.5, 1.8, 2.1, 2.5, 3.5, 10.0],
                labels=["1.01-1.50", "1.51-1.80", "1.81-2.10", "2.11-2.50", "2.51-3.50", "3.51+"],
                include_lowest=True,
            )
            by_odds = chiuse.assign(OddsBand=odds_bins).groupby("OddsBand", dropna=False).agg(
                Bets=("OddsBand", "count"),
                Profit=("P&L €", "sum"),
                Stake=("Stake €", "sum"),
            ).reset_index()
            by_odds["ROI %"] = by_odds.apply(
                lambda r: (r["Profit"] / r["Stake"] * 100) if r["Stake"] else 0.0,
                axis=1,
            )
            fig_odds = go.Figure(go.Bar(
                x=by_odds["OddsBand"].astype(str),
                y=by_odds["Profit"],
                text=[f"€{v:.1f}" for v in by_odds["Profit"]],
                textposition="outside",
                marker_color=["#00D4AA" if v >= 0 else "#FF5252" for v in by_odds["Profit"]],
            ))
            fig_odds.update_layout(
                height=300, template="plotly_dark",
                xaxis_title="Fascia quota", yaxis_title="Profit €",
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_odds, width="stretch")

        with an2:
            st.markdown("**Profit per fascia stake**")
            stake_vals = chiuse["Stake €"].astype(float)
            q1 = float(stake_vals.quantile(0.25))
            q2 = float(stake_vals.quantile(0.50))
            q3 = float(stake_vals.quantile(0.75))
            uniq_edges = sorted(set([0.0, q1, q2, q3, float(stake_vals.max()) + 0.01]))
            if len(uniq_edges) >= 4:
                stake_bins = pd.cut(
                    stake_vals,
                    bins=uniq_edges,
                    include_lowest=True,
                    duplicates="drop",
                )
                by_stake = chiuse.assign(StakeBand=stake_bins).groupby("StakeBand", dropna=False).agg(
                    Bets=("StakeBand", "count"),
                    Profit=("P&L €", "sum"),
                ).reset_index()
                fig_stake = go.Figure(go.Bar(
                    x=by_stake["StakeBand"].astype(str),
                    y=by_stake["Profit"],
                    text=[f"€{v:.1f}" for v in by_stake["Profit"]],
                    textposition="outside",
                    marker_color=["#00D4AA" if v >= 0 else "#FF5252" for v in by_stake["Profit"]],
                ))
                fig_stake.update_layout(
                    height=300, template="plotly_dark",
                    xaxis_title="Fascia stake", yaxis_title="Profit €",
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                st.plotly_chart(fig_stake, width="stretch")
            else:
                st.caption("Servono stake più vari per costruire fasce significative.")

        an3, an4 = st.columns(2)
        with an3:
            st.markdown("**Heatmap giorno × mercato (ROI %)**")
            chiuse_h = chiuse.copy()
            chiuse_h["Weekday"] = chiuse_h["Data_dt"].dt.day_name()
            order_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            chiuse_h["Weekday"] = pd.Categorical(chiuse_h["Weekday"], categories=order_days, ordered=True)
            pv = chiuse_h.pivot_table(
                index="Weekday",
                columns="Stat",
                values="P&L €",
                aggfunc="sum",
                fill_value=0.0,
            )
            pv_stake = chiuse_h.pivot_table(
                index="Weekday",
                columns="Stat",
                values="Stake €",
                aggfunc="sum",
                fill_value=0.0,
            ).replace(0, pd.NA)
            roi_mat = (pv / pv_stake * 100).fillna(0.0)
            fig_heat = go.Figure(data=go.Heatmap(
                z=roi_mat.values,
                x=[str(c) for c in roi_mat.columns],
                y=[str(i) for i in roi_mat.index],
                colorscale="RdYlGn",
                zmid=0,
                colorbar=dict(title="ROI %"),
            ))
            fig_heat.update_layout(
                height=320, template="plotly_dark",
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_heat, width="stretch")

        with an4:
            st.markdown("**Trend rolling ROI (7 bets) + Drawdown**")
            tr = chiuse.sort_values("Data_dt", ascending=True).copy()
            tr["CumPnl"] = tr["P&L €"].cumsum()
            tr["CumStake"] = tr["Stake €"].cumsum().replace(0, pd.NA)
            tr["CumROI"] = (tr["CumPnl"] / tr["CumStake"] * 100).fillna(0.0)
            tr["RollPnl"] = tr["P&L €"].rolling(7, min_periods=3).sum()
            tr["RollStake"] = tr["Stake €"].rolling(7, min_periods=3).sum().replace(0, pd.NA)
            tr["RollROI"] = (tr["RollPnl"] / tr["RollStake"] * 100).fillna(0.0)
            tr["Equity"] = float(st.session_state.bankroll_start) + tr["CumPnl"]
            tr["EqPeak"] = tr["Equity"].cummax()
            tr["Drawdown%"] = ((tr["Equity"] - tr["EqPeak"]) / tr["EqPeak"] * 100).fillna(0.0)
            dd_now = float(tr["Drawdown%"].iloc[-1]) if not tr.empty else 0.0
            dd_worst = float(tr["Drawdown%"].min()) if not tr.empty else 0.0
            st.caption(f"Drawdown attuale: **{dd_now:.1f}%** · Max drawdown: **{dd_worst:.1f}%**")

            fig_roll = go.Figure()
            fig_roll.add_trace(go.Scatter(
                x=tr["Data_dt"], y=tr["RollROI"], mode="lines+markers",
                name="ROI rolling (7 bets)", line=dict(color="#00D4AA", width=2)
            ))
            fig_roll.add_trace(go.Scatter(
                x=tr["Data_dt"], y=tr["CumROI"], mode="lines",
                name="ROI cumulato", line=dict(color="#FFD600", width=1.5, dash="dot")
            ))
            fig_roll.add_hline(y=0, line_dash="dash", line_color="#8B949E")
            fig_roll.update_layout(
                height=320, template="plotly_dark",
                yaxis_title="ROI %", xaxis_title="Data",
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_roll, width="stretch")

    # ── Editor scommesse pendenti ───────────────────────────────────────────
    pendenti_idx = [i for i, b in enumerate(st.session_state.bets)
                    if b.get("Risultato", "In attesa") == "In attesa"]
    if pendenti_idx:
        with st.expander(f"✏️ Aggiorna pendenti ({len(pendenti_idx)})", expanded=False):
            for i in pendenti_idx:
                b = st.session_state.bets[i]
                cols = st.columns([3, 1.2, 1.2, 1.2])
                cols[0].markdown(
                    f"**{b.get('Giocatore', '?')}** · {b.get('Stat', '')} {b.get('Tipo', '')} "
                    f"{b.get('Linea', '?')} @ {b.get('Quota', '?')} · stake €{b.get('Stake €', 0)} "
                    f"<span style='color:#8B949E'>({b.get('Data','')})</span>",
                    unsafe_allow_html=True,
                )
                if cols[1].button("✅ Vinto", key=f"win_{i}"):
                    b["Risultato"] = "Vinto"
                    _recompute_bet_pnl(b)
                    _save_bankroll_state()
                    st.rerun()
                if cols[2].button("❌ Perso", key=f"lose_{i}"):
                    b["Risultato"] = "Perso"
                    _recompute_bet_pnl(b)
                    _save_bankroll_state()
                    st.rerun()
                if cols[3].button("🗑️", key=f"rem_{i}"):
                    st.session_state.bets.pop(i)
                    _save_bankroll_state()
                    st.rerun()

    st.markdown("#### 📄 Storico Scommesse")
    show_cols = [
        c for c in ["Data", "Formato", "Numero Selezioni", "Giocatore", "Dettagli Multipla", "Stat", "Tipo", "Linea", "Quota", "Stake €", "Risultato", "P&L €", "Bookmaker", "Note"]
        if c in df_view.columns
    ]
    st.dataframe(df_view[show_cols], width="stretch", hide_index=True)

    col_del, col_exp, col_imp = st.columns([1, 2, 2])
    with col_del:
        if st.button("🗑️ Cancella tutto"):
            st.session_state.bets = []
            _save_bankroll_state()
            st.rerun()
    with col_exp:
        st.download_button(
            "⬇️ Esporta CSV",
            data=df_to_csv(df_bets[[c for c in df_bets.columns if c != "Data_dt"]]),
            file_name=f"bankroll_{datetime.date.today()}.csv",
            mime="text/csv",
        )
    with col_imp:
        up = st.file_uploader("📤 Importa CSV (accoda/sostituisce)", type=["csv"], key="bk_import_full")
        if up is not None:
            mode_imp = st.radio(
                "Modalità import",
                ["Accoda allo storico", "Sostituisci storico"],
                horizontal=True,
                key="bk_import_mode",
            )
            if st.button("Conferma import", key="bk_import_confirm"):
                try:
                    df_in = pd.read_csv(up)
                    required = {"Data", "Giocatore", "Stat", "Tipo", "Linea", "Quota", "Stake €", "Risultato"}
                    if not required.issubset(set(df_in.columns)):
                        st.error(f"Colonne mancanti. Servono: {sorted(required)}")
                    else:
                        rows = df_in.to_dict("records")
                        for row in rows:
                            _recompute_bet_pnl(row)
                        if mode_imp == "Sostituisci storico":
                            st.session_state.bets = rows
                        else:
                            st.session_state.bets.extend(rows)
                        _save_bankroll_state()
                        st.success(f"✅ Importate {len(rows)} righe ({mode_imp.lower()}).")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Errore import CSV: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  SINGLE PLAYER PAGE
# ══════════════════════════════════════════════════════════════════════════════

def single_player_page(linee: dict, n_partite: int, n_slump: int):
    linee = render_line_inputs(expanded=False)
    query = st.text_input("🔍 Cerca giocatore NBA",
                          value="Donovan Mitchell",
                          placeholder="Es: LeBron, Curry, Jokic, Giannis…",
                          key="sp_input")
    if not query:
        return

    resolved_name, pid = find_player(query)
    if pid is None:
        st.warning(f"⚠️ Giocatore **{query}** non trovato nel database. "
                   "Prova con il cognome o il nome completo.")
        close = difflib.get_close_matches(
            query.lower(), [n.lower() for n in PLAYER_IDS], n=5, cutoff=0.4)
        if close:
            st.info("Forse intendevi: " +
                    ", ".join(n for n in PLAYER_IDS if n.lower() in close))
        return

    with st.spinner(f"Caricamento dati per {resolved_name}…"):
        phase_selected = st.session_state.get("phase_type", "Tutte")
        df_all = get_nba_data(pid, resolved_name, SEASON, API_KEY, phase_selected)
    if not data_ok(df_all, resolved_name):
        return

    n_eff = len(df_all) if st.session_state.get("use_all_games", False) else n_partite
    n_eff = max(1, n_eff)
    df_r, avg_pts, prob_pts, hit_pts = compute_stat(df_all, n_eff, linee["PTS"], "PTS")
    _,    avg_reb, prob_reb, hit_reb = compute_stat(df_all, n_eff, linee["REB"], "REB")
    _,    avg_ast, prob_ast, hit_ast = compute_stat(df_all, n_eff, linee["AST"], "AST")

    st.markdown(
        f'<div class="whale-header">'
        f'<h1>{resolved_name}</h1>'
        f'<p>NBA · Stagione 20{SEASON}-20{int(SEASON)+1} · '
        f'Ultime {n_eff} partite · {len(df_all)} gare in archivio</p>'
        f'</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("PTS medi", f"{avg_pts:.1f}")
    c2.metric("REB medi", f"{avg_reb:.1f}")
    c3.metric("AST medi", f"{avg_ast:.1f}")
    if "STL" in df_r.columns: c4.metric("STL medi", f"{df_r['STL'].mean():.1f}")
    if "BLK" in df_r.columns: c5.metric("BLK medi", f"{df_r['BLK'].mean():.1f}")
    st.markdown("---")

    # ── 🗓️ Prossima Partita (auto da api-sports) ─────────────────────────
    my_team_id = _player_team_id_from_df(df_all)
    next_game = find_next_game_for_team(my_team_id, SEASON) if my_team_id else None

    if next_game:
        opp = _opponent_info_from_game(next_game, my_team_id)
        date_str, days_from_now = _format_next_game_when(opp["start_iso"])

        # Auto-fetch injuries (no manual input!)
        with st.spinner("Caricamento report infortuni..."):
            inj_my  = fetch_team_injuries(int(my_team_id), SEASON)
            inj_opp = fetch_team_injuries(int(opp["opponent_id"]), SEASON) if opp["opponent_id"] else []
        impact_my  = infer_injury_impact(inj_my)
        impact_opp = infer_injury_impact(inj_opp)

        # Header box
        sede_emoji  = "🏠 in casa" if opp["location"] == "Home" else ("✈️ in trasferta" if opp["location"] == "Away" else "")
        days_lbl = (
            "🔴 OGGI" if days_from_now == 0
            else "🟡 DOMANI" if days_from_now == 1
            else f"⏳ Tra {days_from_now} giorni" if days_from_now and days_from_now > 0
            else ""
        )
        st.markdown(
            f"""
<div style="background:linear-gradient(135deg,#161B22 0%,#1c2735 100%);
            border:1px solid #00D4AA;border-radius:12px;padding:18px 20px;margin-bottom:14px;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
            <span style="color:#8B949E;font-size:0.8rem;letter-spacing:1px;">🗓️ PROSSIMA PARTITA</span><br>
            <strong style="color:#00D4AA;font-size:1.4rem;">vs {opp['opponent_name']} ({opp['opponent_code']})</strong>
            <span style="color:#E6EDF3;font-size:1rem;margin-left:8px;">{sede_emoji}</span>
        </div>
        <div style="text-align:right;">
            <span style="color:#FFD600;font-size:1.05rem;font-weight:600;">{days_lbl}</span><br>
            <span style="color:#8B949E;font-size:0.85rem;">{date_str}</span>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Statistiche attese vs questo opponent (se ha già giocato in passato)
        df_vs_opp = pd.DataFrame()
        if "MATCHUP" in df_all.columns:
            mask = df_all["MATCHUP"].apply(_extract_opponent) == opp["opponent_code"]
            df_vs_opp = df_all[mask]

        # ── Box infortuni (auto) ────────────────────────────────────────────
        # Trova il nome del team del giocatore (best effort)
        my_team_label = ""
        try:
            for t in fetch_teams(SEASON):
                if int(t.get("id", 0)) == int(my_team_id):
                    my_team_label = t.get("name", "")
                    break
        except Exception:
            pass
        if not my_team_label:
            my_team_label = f"Squadra di {resolved_name.split()[0]}"

        ig1, ig2 = st.columns(2)
        with ig1:
            st.markdown(f"##### 🩹 Infortuni · **{my_team_label}**")
            if impact_my["out_count"] == 0 and impact_my["questionable_count"] == 0:
                st.info("✅ Nessun infortunio rilevato.")
            else:
                st.warning(f"OUT: {impact_my['out_count']} · Dubbi: {impact_my['questionable_count']} · "
                           f"Usage perso: {impact_my['usage_loss_pct']:.1f}%")
                for note in impact_my["notes"][:5]:
                    st.caption(f"  • {note}")
        with ig2:
            st.markdown(f"##### 🩹 Infortuni · **{opp['opponent_name']} ({opp['opponent_code']})**")
            if impact_opp["out_count"] == 0 and impact_opp["questionable_count"] == 0:
                st.info("✅ Nessun infortunio rilevato.")
            else:
                st.warning(f"OUT: {impact_opp['out_count']} · Dubbi: {impact_opp['questionable_count']} · "
                           f"Defense weakness: {impact_opp['weighted_impact']:.1f}")
                for note in impact_opp["notes"][:5]:
                    st.caption(f"  • {note}")

        # ── Stat attese contro l'avversario ────────────────────────────────
        st.markdown("##### 🎯 Stat attese per la prossima partita")

        # Base: media stagionale del giocatore. Se ha già giocato vs questo opponent, usa quella media (pesata).
        season_pts = float(df_all["PTS"].mean()) if "PTS" in df_all.columns and not df_all.empty else 0.0
        season_reb = float(df_all["REB"].mean()) if "REB" in df_all.columns and not df_all.empty else 0.0
        season_ast = float(df_all["AST"].mean()) if "AST" in df_all.columns and not df_all.empty else 0.0

        if not df_vs_opp.empty:
            vs_pts = float(df_vs_opp["PTS"].mean()) if "PTS" in df_vs_opp.columns else season_pts
            vs_reb = float(df_vs_opp["REB"].mean()) if "REB" in df_vs_opp.columns else season_reb
            vs_ast = float(df_vs_opp["AST"].mean()) if "AST" in df_vs_opp.columns else season_ast
            n_vs   = len(df_vs_opp)
            # Mix 50/50 fra media stagionale e media vs opponent (smoothing per pochi sample)
            blend = max(0.4, min(0.7, n_vs / 5.0))  # più sample → più peso alla media vs opponent
            exp_pts = vs_pts * blend + season_pts * (1 - blend)
            exp_reb = vs_reb * blend + season_reb * (1 - blend)
            exp_ast = vs_ast * blend + season_ast * (1 - blend)
            base_note = f"📊 Già giocate **{n_vs} partite** vs {opp['opponent_code']} (media PTS {vs_pts:.1f})."
        else:
            exp_pts, exp_reb, exp_ast = season_pts, season_reb, season_ast
            base_note = f"⚠️ Nessuna partita pregressa vs {opp['opponent_code']} questa stagione → uso media stagionale."

        # Adjustment euristico injuries: usage liberato dai miei compagni → boost prob; difesa avversaria debole → boost prob
        usage_boost   = impact_my["usage_loss_pct"] / 100.0    # es 12% → +0.12
        defense_boost = impact_opp["weighted_impact"] / 100.0   # es 10% → +0.10
        total_boost   = usage_boost * 0.6 + defense_boost * 0.4
        # Limite: ±25%
        total_boost = max(-0.25, min(0.25, total_boost))

        adj_pts = exp_pts * (1 + total_boost)
        adj_reb = exp_reb * (1 + total_boost * 0.6)
        adj_ast = exp_ast * (1 + total_boost * 0.6)

        st.caption(base_note + (
            f" Aggiustamento contesto applicato: **{total_boost*100:+.1f}%** "
            f"(usage compagni assenti +{usage_boost*100:.0f}% · "
            f"difesa avversaria +{defense_boost*100:.0f}%)."
            if total_boost != 0 else ""
        ))

        # Probabilità Over con stat attese
        p_pts = (1 - poisson.cdf(linee["PTS"], adj_pts)) * 100 if adj_pts > 0 else 0.0
        p_reb = (1 - poisson.cdf(linee["REB"], adj_reb)) * 100 if adj_reb > 0 else 0.0
        p_ast = (1 - poisson.cdf(linee["AST"], adj_ast)) * 100 if adj_ast > 0 else 0.0

        _help_attesi = (
            "Stat attese per la prossima partita.\n\n"
            "Si parte dalla media stagionale e si applicano correzioni di contesto:\n"
            "• boost se mancano compagni titolari (più usage)\n"
            "• boost se l'avversario è una difesa debole\n"
            "• malus se mancano playmaker chiave\n\n"
            "Il delta sotto mostra la linea Over/Under e la probabilità Poisson di superarla."
        )
        eg1, eg2, eg3 = st.columns(3)
        eg1.metric("PUNTI attesi",    f"{adj_pts:.1f}", delta=f"linea {linee['PTS']} · Over {p_pts:.0f}%", help=_help_attesi)
        eg2.metric("RIMBALZI attesi", f"{adj_reb:.1f}", delta=f"linea {linee['REB']} · Over {p_reb:.0f}%", help=_help_attesi)
        eg3.metric("ASSIST attesi",   f"{adj_ast:.1f}", delta=f"linea {linee['AST']} · Over {p_ast:.0f}%", help=_help_attesi)

        # Bar chart riepilogo
        fig_next = go.Figure()
        fig_next.add_trace(go.Bar(
            name="Atteso", x=["Punti", "Rimbalzi", "Assist"],
            y=[adj_pts, adj_reb, adj_ast],
            marker_color="#00D4AA",
            text=[f"{v:.1f}" for v in [adj_pts, adj_reb, adj_ast]],
            textposition="outside",
        ))
        fig_next.add_trace(go.Bar(
            name="Linea Over/Under", x=["Punti", "Rimbalzi", "Assist"],
            y=[linee["PTS"], linee["REB"], linee["AST"]],
            marker_color="#FF5252",
            text=[f"{v}" for v in [linee["PTS"], linee["REB"], linee["AST"]]],
            textposition="outside",
        ))
        fig_next.update_layout(barmode="group", height=320, template="plotly_dark",
                               legend=dict(orientation="h", y=1.12),
                               margin=dict(t=40, b=20, l=20, r=20),
                               yaxis_title="Valore atteso")
        st.plotly_chart(fig_next, width="stretch")

        st.markdown("---")
    else:
        st.info("📭 Nessuna partita programmata trovata per questo giocatore. "
                "Forse la stagione è finita o l'API non ha ancora il calendario aggiornato.")
        st.markdown("---")

    with st.expander("📚 Legenda acronimi (Analisi Singolo)"):
        st.markdown("""
- `PTS`: punti
- `REB`: rimbalzi totali
- `AST`: assist
- `STL`: steals (palle rubate)
- `BLK`: blocks (stoppate)
- `TOV`: turnovers (palle perse)
- `MIN`: minuti giocati
- `LOC`: sede partita (`Home`/`Away`)
- `PHASE`: tipo partita (`Regular Season`/`Play-In`/`Playoff`)
- `H2H`: head-to-head (testa a testa)
""")

    st.subheader("🎯 Verdetti Scommessa")
    t_pts, t_reb, t_ast = st.tabs(["📍 Punti", "📦 Rimbalzi", "🎁 Assist"])
    with t_pts: show_verdict_block(prob_pts, hit_pts, df_r, linee["PTS"], "PTS")
    with t_reb: show_verdict_block(prob_reb, hit_reb, df_r, linee["REB"], "REB")
    with t_ast: show_verdict_block(prob_ast, hit_ast, df_r, linee["AST"], "AST")
    st.markdown("---")

    show_contropronostici(resolved_name, df_all, min(n_slump, len(df_all)))
    st.markdown("---")

    st.subheader("📊 Andamento Prestazioni")
    st.caption("Barre verdi = partita SOPRA la linea (Over). Barre rosse = SOTTO (Under). "
               "Linea tratteggiata rossa = la tua linea, linea gialla = la media del periodo.")
    tg1, tg2, tg3 = st.tabs(["Punti", "Rimbalzi", "Assist"])
    for tab, col, linea in [
        (tg1, "PTS", linee["PTS"]),
        (tg2, "REB", linee["REB"]),
        (tg3, "AST", linee["AST"]),
    ]:
        with tab:
            if col in df_r.columns and not df_r.empty:
                avg_v = df_r[col].mean()
                # ordino dal più vecchio al più recente per leggere "da sinistra a destra"
                df_chart = df_r.sort_values("GAME_DATE")
                values = df_chart[col].astype(float)
                colors = ["#00D4AA" if v > linea else "#FF5252" for v in values]
                hits   = int((values > linea).sum())
                total  = len(values)
                # etichette x compatte (es. "12 Mar")
                try:
                    x_labels = pd.to_datetime(df_chart["GAME_DATE"]).dt.strftime("%d %b")
                except Exception:
                    x_labels = df_chart["GAME_DATE"].astype(str)

                k1, k2, k3 = st.columns(3)
                k1.metric("Sopra la linea", f"{hits}/{total}",
                          delta=f"{(hits/total*100):.0f}%" if total else "—",
                          help=TOOLTIPS["hit_rate"])
                k2.metric("Media periodo", f"{avg_v:.1f}",
                          help="Media della stat selezionata nelle partite mostrate nel grafico.")
                k3.metric("La tua linea", f"{linea}",
                          help="La linea Over/Under impostata nel pannello laterale. Le barre verdi sono partite sopra la linea, rosse sotto.")

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=x_labels, y=values,
                    marker_color=colors,
                    text=[f"{v:.0f}" for v in values],
                    textposition="outside",
                    name=STAT_LABELS[col],
                    hovertemplate="<b>%{x}</b><br>" + STAT_LABELS[col] + ": %{y}<extra></extra>",
                ))
                fig.add_hline(y=linea, line_dash="dash", line_color="#FF5252",
                              annotation_text=f"Linea {linea}",
                              annotation_position="top right")
                fig.add_hline(y=avg_v, line_dash="dot", line_color="#FFD600",
                              annotation_text=f"Media {avg_v:.1f}",
                              annotation_position="bottom right")
                fig.update_layout(height=380, template="plotly_dark",
                                  xaxis_title="", yaxis_title=STAT_LABELS[col],
                                  bargap=0.25, showlegend=False,
                                  margin=dict(t=40, b=40, l=40, r=20))
                st.plotly_chart(fig, width="stretch")
    st.markdown("---")

    # ── Performance per Squadra Avversaria ──────────────────────────────────
    st.subheader("🆚 Performance per Squadra Avversaria")
    st.caption("Come cambiano i suoi numeri a seconda dell'avversario (sulle ultime "
               f"{n_eff} partite). Valori sopra/sotto la sua media stagionale segnalano "
               "match favorevoli o difficili.")

    opp_df = build_opponent_breakdown(df_r, df_all, linee)
    season_avg_pts_global = float(df_all["PTS"].mean()) if "PTS" in df_all.columns and not df_all.empty else 0.0

    if opp_df.empty:
        st.info("Dati avversari insufficienti.")
    else:
        # Bar chart medie PTS per opponent (verde/rosso a seconda del delta vs media stagionale)
        fig_opp = go.Figure()
        bar_colors = []
        for _, r in opp_df.iterrows():
            d = float(r["Delta vs media stagione"])
            if d >= 2:
                bar_colors.append("#00D4AA")   # netto sopra
            elif d <= -2:
                bar_colors.append("#FF5252")   # netto sotto
            else:
                bar_colors.append("#FFD600")   # in linea
        fig_opp.add_trace(go.Bar(
            x=opp_df["Avversario"],
            y=opp_df["Media PTS"],
            marker_color=bar_colors,
            text=[f"{v:.1f}" for v in opp_df["Media PTS"]],
            textposition="outside",
            customdata=opp_df[["Partite", "Delta vs media stagione"]].values,
            hovertemplate="<b>%{x}</b><br>"
                          "Media PTS: %{y:.1f}<br>"
                          "Partite: %{customdata[0]}<br>"
                          "Delta vs media stagione: %{customdata[1]:+.1f}<extra></extra>",
        ))
        fig_opp.add_hline(y=season_avg_pts_global, line_dash="dot", line_color="#FFD600",
                          annotation_text=f"Media stagione {season_avg_pts_global:.1f}",
                          annotation_position="bottom right")
        fig_opp.add_hline(y=linee["PTS"], line_dash="dash", line_color="#FF5252",
                          annotation_text=f"Linea {linee['PTS']}",
                          annotation_position="top right")
        fig_opp.update_layout(
            height=380, template="plotly_dark",
            xaxis_title="Squadra avversaria",
            yaxis_title="Media PTS sulle partite vs quella squadra",
            bargap=0.3, showlegend=False,
            margin=dict(t=40, b=40, l=40, r=20),
        )
        st.plotly_chart(fig_opp, width="stretch")

        st.dataframe(opp_df, width="stretch", hide_index=True)
        st.caption("🟢 verde = media nettamente sopra la sua stagione · "
                   "🔴 rosso = nettamente sotto · 🟡 giallo = in linea.")

    # ── Partite anomale con possibili motivi ────────────────────────────────
    if not df_r.empty and "PTS" in df_r.columns and "PTS" in df_all.columns:
        season_avg_pts = float(df_all["PTS"].mean())
        season_std_pts = float(df_all["PTS"].std(ddof=0)) if len(df_all) > 1 else 0.0
        season_mins_series = df_all["MIN"].apply(_parse_minutes) if "MIN" in df_all.columns else pd.Series([0.0])
        season_avg_min = float(season_mins_series.mean()) if not season_mins_series.empty else 0.0

        if season_std_pts > 0:
            df_r_sorted = df_r.sort_values("GAME_DATE", ascending=False).copy()
            df_r_sorted["delta_pts"] = df_r_sorted["PTS"].astype(float) - season_avg_pts
            df_r_sorted["abs_delta"] = df_r_sorted["delta_pts"].abs()
            anomalies = df_r_sorted[df_r_sorted["abs_delta"] >= season_std_pts * 1.2]

            if not anomalies.empty:
                with st.expander(f"🔍 Partite anomale rilevate ({len(anomalies)}) — perché?", expanded=False):
                    st.caption("Partite con PTS molto sopra/sotto la media stagionale "
                               f"(soglia ±{season_std_pts*1.2:.1f} PTS). "
                               "Le diagnosi sono ipotesi basate su minuti, perse, sede e gap dalla media.")
                    for _, row in anomalies.head(8).iterrows():
                        reasons = _diagnose_game(row, season_avg_pts, season_std_pts, season_avg_min)
                        delta_pts = float(row["delta_pts"])
                        opp = _extract_opponent(row.get("MATCHUP"))
                        date_str = str(row.get("GAME_DATE", ""))
                        loc = row.get("LOC", "")
                        sign_color = "#00D4AA" if delta_pts > 0 else "#FF5252"
                        st.markdown(
                            f"<div style='border-left:3px solid {sign_color};padding:6px 12px;margin-bottom:8px;background:#161B22;border-radius:4px;'>"
                            f"<strong>{date_str} · vs {opp} ({loc})</strong> · "
                            f"<span style='color:{sign_color};font-weight:bold;'>"
                            f"{int(row['PTS'])} PTS ({delta_pts:+.1f} vs media)</span><br>"
                            + "<br>".join([f"&nbsp;&nbsp;{r}" for r in reasons])
                            + "</div>",
                            unsafe_allow_html=True,
                        )
                    if len(anomalies) > 8:
                        st.caption(f"…e altre {len(anomalies)-8} partite anomale non mostrate.")
            else:
                st.caption("✅ Nessuna partita anomala rilevata: rendimento costante.")
    st.markdown("---")

    if "LOC" in df_r.columns:
        st.subheader("🏠 vs ✈️ Split Home / Away")
        home_df = df_r[df_r["LOC"] == "Home"]
        away_df = df_r[df_r["LOC"] == "Away"]
        ha1, ha2 = st.columns(2)
        ha1.metric("Media PTS Casa",       f"{home_df['PTS'].mean():.1f}" if not home_df.empty else "—")
        ha1.caption(f"{len(home_df)} partite")
        ha2.metric("Media PTS Trasferta",  f"{away_df['PTS'].mean():.1f}" if not away_df.empty else "—")
        ha2.caption(f"{len(away_df)} partite")
        fig_ha = go.Figure()
        for subset, label, cx in [(home_df, "Casa 🏠", "#00D4AA"), (away_df, "Trasferta ✈️", "#FF5252")]:
            if not subset.empty:
                fig_ha.add_trace(go.Box(y=subset["PTS"], name=label, marker_color=cx))
        fig_ha.add_hline(y=linee["PTS"], line_dash="dash", line_color="#FF5252")
        fig_ha.update_layout(height=280, template="plotly_dark",
                             title="Distribuzione PTS per Sede")
        st.plotly_chart(fig_ha, width="stretch")
        st.markdown("---")

    st.subheader("📄 Log Partite Recenti")
    display_cols = [c for c in ["GAME_DATE","MATCHUP","LOC","PTS","REB","AST","STL","BLK","TOV","MIN"]
                    if c in df_r.columns]
    st.dataframe(df_r[display_cols].reset_index(drop=True),
                 width="stretch")

    ex1, ex2 = st.columns(2)
    with ex1:
        st.download_button("⬇️ Esporta Log CSV", data=df_to_csv(df_r[display_cols]),
                           file_name=f"{resolved_name.replace(' ','_')}_log.csv",
                           mime="text/csv")
    with ex2:
        st.download_button("⬇️ Esporta Report Analisi",
                           data=export_summary(resolved_name, df_r, df_all, linee, n_eff),
                           file_name=f"{resolved_name.replace(' ','_')}_analisi.csv",
                           mime="text/csv")
    st.markdown("---")
    st.subheader("🧠 10 Indicatori chiave del giocatore")
    st.caption("Valori di sintesi con interpretazione in italiano. "
               "Se l'indicatore è 'in crescita' o 'sopra la linea' → segnale a favore dell'Over.")
    extra_df = build_extra_10_tools(df_r, df_all, linee)
    st.dataframe(extra_df, width="stretch", hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  COMPARISON PAGE
# ══════════════════════════════════════════════════════════════════════════════

def comparison_page(linee: dict, n_partite: int, n_slump: int):
    st.subheader("⚔️ Confronto")
    cmp_mode = st.radio(
        "Tipo di confronto",
        ["👤 Giocatori", "🏀 Squadre"],
        horizontal=True,
        key="cmp_mode",
        label_visibility="collapsed",
    )
    if cmp_mode == "🏀 Squadre":
        teams_comparison_page(n_partite, embedded=True)
        return

    linee = render_line_inputs(expanded=False)
    cp1, cp2 = st.columns(2)
    q1 = cp1.text_input("Giocatore 1", value="LeBron James", key="cmp_p1",
                         placeholder="Es: LeBron, Curry…")
    q2 = cp2.text_input("Giocatore 2", value="Kevin Durant",  key="cmp_p2",
                         placeholder="Es: Durant, Giannis…")
    if not q1 or not q2:
        return

    n1, pid1 = find_player(q1)
    n2, pid2 = find_player(q2)
    if pid1 is None:
        st.warning(f"⚠️ Giocatore 1 non trovato: **{q1}**")
        return
    if pid2 is None:
        st.warning(f"⚠️ Giocatore 2 non trovato: **{q2}**")
        return

    with st.spinner("Caricamento dati…"):
        phase_selected = st.session_state.get("phase_type", "Tutte")
        df1_all = get_nba_data(pid1, n1, SEASON, API_KEY, phase_selected)
        df2_all = get_nba_data(pid2, n2, SEASON, API_KEY, phase_selected)
    if not data_ok(df1_all, n1) or not data_ok(df2_all, n2):
        return
    n_eff1 = len(df1_all) if st.session_state.get("use_all_games", False) else n_partite
    n_eff2 = len(df2_all) if st.session_state.get("use_all_games", False) else n_partite

    df1, avg1_pts, prob1_pts, hit1_pts = compute_stat(df1_all, n_eff1, linee["PTS"], "PTS")
    _,   avg1_reb, prob1_reb, hit1_reb = compute_stat(df1_all, n_eff1, linee["REB"], "REB")
    _,   avg1_ast, prob1_ast, hit1_ast = compute_stat(df1_all, n_eff1, linee["AST"], "AST")
    df2, avg2_pts, prob2_pts, hit2_pts = compute_stat(df2_all, n_eff2, linee["PTS"], "PTS")
    _,   avg2_reb, prob2_reb, hit2_reb = compute_stat(df2_all, n_eff2, linee["REB"], "REB")
    _,   avg2_ast, prob2_ast, hit2_ast = compute_stat(df2_all, n_eff2, linee["AST"], "AST")

    C1, C2 = "#00D4AA", "#FF5252"
    st.subheader(f"⚔️ {n1}  vs  {n2}")
    st.caption(f"Ultime {min(n_eff1, n_eff2)} partite · Stagione 20{SEASON}-20{int(SEASON)+1}")
    st.markdown("---")

    h1, h2 = st.columns(2)
    with h1:
        st.markdown(f"### 🟢 {n1}")
        m1,m2,m3 = st.columns(3)
        m1.metric("PTS",f"{avg1_pts:.1f}")
        m2.metric("REB",f"{avg1_reb:.1f}")
        m3.metric("AST",f"{avg1_ast:.1f}")
    with h2:
        st.markdown(f"### 🔴 {n2}")
        m4,m5,m6 = st.columns(3)
        m4.metric("PTS",f"{avg2_pts:.1f}", delta=f"{avg2_pts-avg1_pts:+.1f}")
        m5.metric("REB",f"{avg2_reb:.1f}", delta=f"{avg2_reb-avg1_reb:+.1f}")
        m6.metric("AST",f"{avg2_ast:.1f}", delta=f"{avg2_ast-avg1_ast:+.1f}")
    st.markdown("---")

    st.subheader("🎯 Verdetti Scommessa")
    vt1, vt2, vt3 = st.tabs(["📍 Punti","📦 Rimbalzi","🎁 Assist"])
    for tab, col, l, (p1v,h1v,p2v,h2v) in [
        (vt1,"PTS",linee["PTS"],(prob1_pts,hit1_pts,prob2_pts,hit2_pts)),
        (vt2,"REB",linee["REB"],(prob1_reb,hit1_reb,prob2_reb,hit2_reb)),
        (vt3,"AST",linee["AST"],(prob1_ast,hit1_ast,prob2_ast,hit2_ast)),
    ]:
        with tab:
            vd1, vd2 = st.columns(2)
            with vd1: show_verdict_block(p1v, h1v, df1, l, col)
            with vd2: show_verdict_block(p2v, h2v, df2, l, col)
    st.markdown("---")

    cc1, cc2 = st.columns(2)
    with cc1: show_contropronostici(n1, df1_all, min(n_slump, len(df1_all)))
    with cc2: show_contropronostici(n2, df2_all, min(n_slump, len(df2_all)))
    st.markdown("---")

    st.subheader("📊 Trend Diretto")
    st.caption("Confronto a barre raggruppate · ogni gruppo = 1 partita (G1 = più recente). "
               "Linea bianca tratteggiata = la tua linea Over/Under.")
    gt1, gt2, gt3 = st.tabs(["Punti","Rimbalzi","Assist"])
    for tab, col, linea in [
        (gt1, "PTS", linee["PTS"]),
        (gt2, "REB", linee["REB"]),
        (gt3, "AST", linee["AST"]),
    ]:
        with tab:
            n_pairs = min(len(df1), len(df2))
            if n_pairs == 0 or col not in df1.columns or col not in df2.columns:
                st.info("Dati insufficienti per il confronto su questa stat.")
                continue
            v1 = df1[col].astype(float).head(n_pairs).reset_index(drop=True)
            v2 = df2[col].astype(float).head(n_pairs).reset_index(drop=True)
            x_labels = [f"G{i+1}" for i in range(n_pairs)]

            wins1 = int((v1 > v2).sum())
            wins2 = int((v2 > v1).sum())
            ties  = n_pairs - wins1 - wins2
            over1 = int((v1 > linea).sum())
            over2 = int((v2 > linea).sum())

            k1, k2, k3 = st.columns(3)
            k1.metric(f"H2H · {n1}", f"{wins1}/{n_pairs}",
                      delta=f"{wins1-wins2:+d}" if wins1 != wins2 else "pari")
            k2.metric(f"H2H · {n2}", f"{wins2}/{n_pairs}")
            k3.metric("Over la linea", f"{n1}: {over1} · {n2}: {over2}")

            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=v1, name=n1, marker_color=C1,
                                 text=[f"{v:.0f}" for v in v1], textposition="outside",
                                 hovertemplate=f"<b>{n1}</b> · %{{x}}<br>{STAT_LABELS.get(col,col)}: %{{y}}<extra></extra>"))
            fig.add_trace(go.Bar(x=x_labels, y=v2, name=n2, marker_color=C2,
                                 text=[f"{v:.0f}" for v in v2], textposition="outside",
                                 hovertemplate=f"<b>{n2}</b> · %{{x}}<br>{STAT_LABELS.get(col,col)}: %{{y}}<extra></extra>"))
            fig.add_hline(y=linea, line_dash="dash", line_color="white",
                          annotation_text=f"Linea {linea}",
                          annotation_position="top right")
            fig.update_layout(
                height=400, template="plotly_dark",
                barmode="group", bargap=0.18, bargroupgap=0.05,
                xaxis_title="", yaxis_title=STAT_LABELS.get(col, col),
                legend=dict(orientation="h", y=1.12),
                margin=dict(t=40, b=40, l=40, r=20),
            )
            st.plotly_chart(fig, width="stretch")

    st.subheader("📊 Distribuzione Punti")
    fig_h = go.Figure()
    for df_x, nm, cx in [(df1,n1,C1),(df2,n2,C2)]:
        if "PTS" in df_x.columns:
            fig_h.add_trace(go.Histogram(x=df_x["PTS"], name=nm,
                                          marker_color=cx, opacity=0.75, nbinsx=10))
    fig_h.add_vline(x=linee["PTS"], line_dash="dash", line_color="white")
    fig_h.update_layout(barmode="overlay", height=300, template="plotly_dark",
                        xaxis_title="Punti", yaxis_title="Frequenza")
    st.plotly_chart(fig_h, width="stretch")

    st.subheader("📋 Riepilogo Statistico Completo")
    st.caption(f"Confronto su ultime {min(n_eff1, n_eff2)} partite. "
               f"Colonna **Migliore** indica chi spunta meglio per ogni metrica "
               f"(🟢 = {n1}, 🔴 = {n2}, ⚖️ = pareggio).")

    def _pick_winner(v_a, v_b, higher_is_better=True, tol=0.0):
        try:
            a, b = float(v_a), float(v_b)
        except Exception:
            return "⚖️"
        if abs(a - b) <= tol:
            return "⚖️"
        if higher_is_better:
            return f"🟢 {n1}" if a > b else f"🔴 {n2}"
        else:
            return f"🟢 {n1}" if a < b else f"🔴 {n2}"

    def _fmt(v, suffix=""):
        try:
            return f"{float(v):.1f}{suffix}"
        except Exception:
            return "—"

    def _fmt_int(v, suffix=""):
        try:
            return f"{float(v):.0f}{suffix}"
        except Exception:
            return "—"

    def _safe_stat(df, col, fn, default=0.0):
        if col not in df.columns or df.empty:
            return default
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            return default
        return float(fn(s))

    # Aggregati per giocatore 1
    p1 = {
        "PTS": {
            "media":    _safe_stat(df1, "PTS", lambda s: s.mean()),
            "mediana":  _safe_stat(df1, "PTS", lambda s: s.median()),
            "std":      _safe_stat(df1, "PTS", lambda s: s.std(ddof=0)),
            "max":      _safe_stat(df1, "PTS", lambda s: s.max()),
            "min":      _safe_stat(df1, "PTS", lambda s: s.min()),
            "over_n":   int((df1["PTS"] > linee["PTS"]).sum()) if "PTS" in df1.columns else 0,
            "totale":   int(len(df1)),
        },
        "REB": {
            "media":   _safe_stat(df1, "REB", lambda s: s.mean()),
            "mediana": _safe_stat(df1, "REB", lambda s: s.median()),
            "max":     _safe_stat(df1, "REB", lambda s: s.max()),
            "min":     _safe_stat(df1, "REB", lambda s: s.min()),
            "over_n":  int((df1["REB"] > linee["REB"]).sum()) if "REB" in df1.columns else 0,
        },
        "AST": {
            "media":   _safe_stat(df1, "AST", lambda s: s.mean()),
            "mediana": _safe_stat(df1, "AST", lambda s: s.median()),
            "max":     _safe_stat(df1, "AST", lambda s: s.max()),
            "min":     _safe_stat(df1, "AST", lambda s: s.min()),
            "over_n":  int((df1["AST"] > linee["AST"]).sum()) if "AST" in df1.columns else 0,
        },
        "MIN": _safe_stat(df1, "MIN", lambda s: s.mean()),
        "STL": _safe_stat(df1, "STL", lambda s: s.mean()),
        "BLK": _safe_stat(df1, "BLK", lambda s: s.mean()),
        "TOV": _safe_stat(df1, "TOV", lambda s: s.mean()),
        "trend_pts": _last_n_avg(df1, "PTS", 3) - _last_n_avg(df1, "PTS", 10),
        "consistency_pts": _consistency_index(df1, "PTS"),
    }
    p2 = {
        "PTS": {
            "media":    _safe_stat(df2, "PTS", lambda s: s.mean()),
            "mediana":  _safe_stat(df2, "PTS", lambda s: s.median()),
            "std":      _safe_stat(df2, "PTS", lambda s: s.std(ddof=0)),
            "max":      _safe_stat(df2, "PTS", lambda s: s.max()),
            "min":      _safe_stat(df2, "PTS", lambda s: s.min()),
            "over_n":   int((df2["PTS"] > linee["PTS"]).sum()) if "PTS" in df2.columns else 0,
            "totale":   int(len(df2)),
        },
        "REB": {
            "media":   _safe_stat(df2, "REB", lambda s: s.mean()),
            "mediana": _safe_stat(df2, "REB", lambda s: s.median()),
            "max":     _safe_stat(df2, "REB", lambda s: s.max()),
            "min":     _safe_stat(df2, "REB", lambda s: s.min()),
            "over_n":  int((df2["REB"] > linee["REB"]).sum()) if "REB" in df2.columns else 0,
        },
        "AST": {
            "media":   _safe_stat(df2, "AST", lambda s: s.mean()),
            "mediana": _safe_stat(df2, "AST", lambda s: s.median()),
            "max":     _safe_stat(df2, "AST", lambda s: s.max()),
            "min":     _safe_stat(df2, "AST", lambda s: s.min()),
            "over_n":  int((df2["AST"] > linee["AST"]).sum()) if "AST" in df2.columns else 0,
        },
        "MIN": _safe_stat(df2, "MIN", lambda s: s.mean()),
        "STL": _safe_stat(df2, "STL", lambda s: s.mean()),
        "BLK": _safe_stat(df2, "BLK", lambda s: s.mean()),
        "TOV": _safe_stat(df2, "TOV", lambda s: s.mean()),
        "trend_pts": _last_n_avg(df2, "PTS", 3) - _last_n_avg(df2, "PTS", 10),
        "consistency_pts": _consistency_index(df2, "PTS"),
    }

    # higher_is_better: True per quasi tutto. False per TOV (perse) e std (volatilità).
    rows = [
        ("📍 PUNTI",               "",                "",                ""),
        ("Media",                  _fmt(p1["PTS"]["media"]),    _fmt(p2["PTS"]["media"]),
                                   _pick_winner(p1["PTS"]["media"],   p2["PTS"]["media"], True, 0.05)),
        ("Mediana",                _fmt(p1["PTS"]["mediana"]),  _fmt(p2["PTS"]["mediana"]),
                                   _pick_winner(p1["PTS"]["mediana"], p2["PTS"]["mediana"], True, 0.05)),
        ("Deviazione std (volatilità)", _fmt(p1["PTS"]["std"]), _fmt(p2["PTS"]["std"]),
                                   _pick_winner(p1["PTS"]["std"], p2["PTS"]["std"], False, 0.05)),
        ("Massimo / Minimo",       f"{_fmt_int(p1['PTS']['max'])} / {_fmt_int(p1['PTS']['min'])}",
                                   f"{_fmt_int(p2['PTS']['max'])} / {_fmt_int(p2['PTS']['min'])}", ""),
        ("Probabilità Over (Poisson)", f"{prob1_pts:.1f}%",     f"{prob2_pts:.1f}%",
                                   _pick_winner(prob1_pts, prob2_pts, True, 0.5)),
        ("Hit Rate Over",          f"{hit1_pts:.0f}%",          f"{hit2_pts:.0f}%",
                                   _pick_winner(hit1_pts, hit2_pts, True, 0.5)),
        (f"Partite sopra linea {linee['PTS']}",
                                   f"{p1['PTS']['over_n']}/{p1['PTS']['totale']}",
                                   f"{p2['PTS']['over_n']}/{p2['PTS']['totale']}",
                                   _pick_winner(p1['PTS']['over_n'], p2['PTS']['over_n'], True, 0)),
        ("Trend ultime 3 vs 10",   _fmt(p1["trend_pts"]),       _fmt(p2["trend_pts"]),
                                   _pick_winner(p1["trend_pts"], p2["trend_pts"], True, 0.1)),
        ("Costanza (0-100)",       _fmt_int(p1["consistency_pts"]), _fmt_int(p2["consistency_pts"]),
                                   _pick_winner(p1["consistency_pts"], p2["consistency_pts"], True, 1)),

        ("📦 RIMBALZI",            "",                "",                ""),
        ("Media",                  _fmt(p1["REB"]["media"]),    _fmt(p2["REB"]["media"]),
                                   _pick_winner(p1["REB"]["media"], p2["REB"]["media"], True, 0.05)),
        ("Mediana",                _fmt(p1["REB"]["mediana"]),  _fmt(p2["REB"]["mediana"]),
                                   _pick_winner(p1["REB"]["mediana"], p2["REB"]["mediana"], True, 0.05)),
        ("Massimo / Minimo",       f"{_fmt_int(p1['REB']['max'])} / {_fmt_int(p1['REB']['min'])}",
                                   f"{_fmt_int(p2['REB']['max'])} / {_fmt_int(p2['REB']['min'])}", ""),
        ("Probabilità Over (Poisson)", f"{prob1_reb:.1f}%",     f"{prob2_reb:.1f}%",
                                   _pick_winner(prob1_reb, prob2_reb, True, 0.5)),
        ("Hit Rate Over",          f"{hit1_reb:.0f}%",          f"{hit2_reb:.0f}%",
                                   _pick_winner(hit1_reb, hit2_reb, True, 0.5)),
        (f"Partite sopra linea {linee['REB']}",
                                   f"{p1['REB']['over_n']}/{p1['PTS']['totale']}",
                                   f"{p2['REB']['over_n']}/{p2['PTS']['totale']}",
                                   _pick_winner(p1['REB']['over_n'], p2['REB']['over_n'], True, 0)),

        ("🎁 ASSIST",              "",                "",                ""),
        ("Media",                  _fmt(p1["AST"]["media"]),    _fmt(p2["AST"]["media"]),
                                   _pick_winner(p1["AST"]["media"], p2["AST"]["media"], True, 0.05)),
        ("Mediana",                _fmt(p1["AST"]["mediana"]),  _fmt(p2["AST"]["mediana"]),
                                   _pick_winner(p1["AST"]["mediana"], p2["AST"]["mediana"], True, 0.05)),
        ("Massimo / Minimo",       f"{_fmt_int(p1['AST']['max'])} / {_fmt_int(p1['AST']['min'])}",
                                   f"{_fmt_int(p2['AST']['max'])} / {_fmt_int(p2['AST']['min'])}", ""),
        ("Probabilità Over (Poisson)", f"{prob1_ast:.1f}%",     f"{prob2_ast:.1f}%",
                                   _pick_winner(prob1_ast, prob2_ast, True, 0.5)),
        ("Hit Rate Over",          f"{hit1_ast:.0f}%",          f"{hit2_ast:.0f}%",
                                   _pick_winner(hit1_ast, hit2_ast, True, 0.5)),
        (f"Partite sopra linea {linee['AST']}",
                                   f"{p1['AST']['over_n']}/{p1['PTS']['totale']}",
                                   f"{p2['AST']['over_n']}/{p2['PTS']['totale']}",
                                   _pick_winner(p1['AST']['over_n'], p2['AST']['over_n'], True, 0)),

        ("🛡️ DIFESA & GESTIONE",   "",                "",                ""),
        ("Minuti medi",            _fmt(p1["MIN"]),             _fmt(p2["MIN"]),
                                   _pick_winner(p1["MIN"], p2["MIN"], True, 0.5)),
        ("Recuperi (STL)",         _fmt(p1["STL"]),             _fmt(p2["STL"]),
                                   _pick_winner(p1["STL"], p2["STL"], True, 0.05)),
        ("Stoppate (BLK)",         _fmt(p1["BLK"]),             _fmt(p2["BLK"]),
                                   _pick_winner(p1["BLK"], p2["BLK"], True, 0.05)),
        ("Perse (TOV) — meno è meglio", _fmt(p1["TOV"]),        _fmt(p2["TOV"]),
                                   _pick_winner(p1["TOV"], p2["TOV"], False, 0.05)),
    ]

    summary_df = pd.DataFrame(rows, columns=["Statistica", n1, n2, "Migliore"])
    st.dataframe(summary_df, width="stretch", hide_index=True)

    # Verdetto finale aggregato (chi vince più metriche)
    wins_count_1 = sum(1 for r in rows if isinstance(r[3], str) and r[3].startswith("🟢"))
    wins_count_2 = sum(1 for r in rows if isinstance(r[3], str) and r[3].startswith("🔴"))
    ties_count   = sum(1 for r in rows if r[3] == "⚖️")
    cWin1, cWin2, cTie = st.columns(3)
    cWin1.metric(f"Metriche vinte da {n1}", wins_count_1)
    cWin2.metric(f"Metriche vinte da {n2}", wins_count_2)
    cTie.metric("Pareggi", ties_count)
    if wins_count_1 > wins_count_2:
        st.success(f"🏆 **Vincitore complessivo: {n1}** ({wins_count_1} metriche su {wins_count_1+wins_count_2+ties_count})")
    elif wins_count_2 > wins_count_1:
        st.success(f"🏆 **Vincitore complessivo: {n2}** ({wins_count_2} metriche su {wins_count_1+wins_count_2+ties_count})")
    else:
        st.info("⚖️ Confronto in equilibrio: nessuno emerge nettamente.")


@st.cache_data(ttl=1800)
def fetch_team_comparison_data(team_id: int, season: str, phase_selected: str):
    try:
        r = _api_get("/games", {"season": season, "team": team_id})
        rows = []
        for g in r.json().get("response", []):
            teams = g.get("teams", {}) or {}
            scores = g.get("scores", {}) or {}
            home = teams.get("home", {}) or {}
            vis = teams.get("visitors", {}) or {}
            date = ((g.get("date", {}) or {}).get("start", "") or "")[:10]
            stage_val = (
                g.get("stage")
                or (g.get("week", {}) or {}).get("name")
                or (g.get("league", {}) or {}).get("stage")
                or ""
            )
            phase = _normalize_phase_label(stage_val)
            if not _phase_matches(phase_selected, phase):
                continue

            # Solo partite TERMINATE (altrimenti calendario futuro = 0 punti e medie assurde ~20-30)
            st_code = _game_status_short(g)
            if st_code != 3:
                continue

            home_id = home.get("id")
            vis_id = vis.get("id")
            try:
                hid = int(home_id) if home_id is not None else None
                vid = int(vis_id) if vis_id is not None else None
                tid = int(team_id)
            except (TypeError, ValueError):
                continue
            if hid is None or vid is None:
                continue
            is_home = tid == hid
            home_score = _side_score_total(scores.get("home") or {})
            vis_score = _side_score_total(scores.get("visitors") or {})
            if home_score <= 0 or vis_score <= 0:
                continue
            pf = home_score if is_home else vis_score
            pa = vis_score if is_home else home_score
            rows.append({
                "GAME_DATE": pd.to_datetime(date, errors="coerce").date() if date else None,
                "PF": pf,
                "PA": pa,
                "DIFF": pf - pa,
                "RESULT": "W" if pf > pa else ("L" if pf < pa else "D"),
                "PHASE": phase,
            })
        if not rows:
            return None
        df = pd.DataFrame(rows).dropna(subset=["GAME_DATE"])
        if df.empty:
            return None
        return df.sort_values("GAME_DATE", ascending=False).reset_index(drop=True)
    except Exception:
        return "ERROR"


@st.cache_data(ttl=1800)
def fetch_head_to_head_data(team1_id: int, team2_id: int, season: str, phase_selected: str):
    """
    Ritorna storico testa-a-testa: PF/PA per entrambe le squadre.
    """
    try:
        r = _api_get("/games", {"season": season, "team": team1_id})
        rows = []
        for g in r.json().get("response", []):
            teams = g.get("teams", {}) or {}
            scores = g.get("scores", {}) or {}
            home = teams.get("home", {}) or {}
            vis = teams.get("visitors", {}) or {}
            try:
                hid = int(home.get("id"))
                vid = int(vis.get("id"))
                t1 = int(team1_id)
                t2 = int(team2_id)
            except (TypeError, ValueError):
                continue
            if {hid, vid} != {t1, t2}:
                continue
            stage_val = (
                g.get("stage")
                or (g.get("week", {}) or {}).get("name")
                or (g.get("league", {}) or {}).get("stage")
                or ""
            )
            phase = _normalize_phase_label(stage_val)
            if not _phase_matches(phase_selected, phase):
                continue

            if _game_status_short(g) != 3:
                continue

            home_score = _side_score_total(scores.get("home") or {})
            vis_score = _side_score_total(scores.get("visitors") or {})
            if home_score <= 0 or vis_score <= 0:
                continue
            date = ((g.get("date", {}) or {}).get("start", "") or "")[:10]

            if hid == t1:
                t1_pf, t1_pa = home_score, vis_score
                t2_pf, t2_pa = vis_score, home_score
            else:
                t1_pf, t1_pa = vis_score, home_score
                t2_pf, t2_pa = home_score, vis_score

            rows.append({
                "GAME_DATE": pd.to_datetime(date, errors="coerce").date() if date else None,
                "T1_PF": t1_pf, "T1_PA": t1_pa,
                "T2_PF": t2_pf, "T2_PA": t2_pa,
                "PHASE": phase,
            })
        if not rows:
            return None
        df = pd.DataFrame(rows).dropna(subset=["GAME_DATE"])
        if df.empty:
            return None
        return df.sort_values("GAME_DATE", ascending=False).reset_index(drop=True)
    except Exception:
        return "ERROR"


@st.cache_data(ttl=600)
def fetch_games_by_date(date_iso: str):
    try:
        r = _api_get("/games", {"date": date_iso})
        return r.json().get("response", [])
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_games_window(hours_ahead: int):
    """
    Ritorna partite tra adesso e N ore avanti (UTC-aware).
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    end_utc = now_utc + datetime.timedelta(hours=hours_ahead)
    days = sorted({now_utc.date(), end_utc.date()})
    games = []
    for d in days:
        games.extend(fetch_games_by_date(str(d)))

    out = []
    for g in games:
        start_raw = ((g.get("date", {}) or {}).get("start", "") or "").strip()
        if not start_raw:
            continue
        try:
            # API typically returns ISO string with Z suffix
            start_dt = datetime.datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        except Exception:
            continue
        if now_utc <= start_dt <= end_utc:
            out.append(g)
    return out


def _game_status_flags(game_obj: dict):
    status_obj = game_obj.get("status", {}) or {}
    status = str(status_obj.get("long", "") or "").lower()
    short = str(status_obj.get("short", "") or "").lower()
    is_finished = any(k in status for k in ["finished", "final", "after overtime"]) or short in {"ft", "aot", "fin"}
    is_not_started = any(k in status for k in ["not started", "scheduled"]) or short in {"ns", "sch"}
    is_live = any(k in status for k in ["in play", "live"]) or short in {"q1", "q2", "q3", "q4", "ht", "ot"}
    return is_finished, is_not_started, is_live


@st.cache_data(ttl=300)
def fetch_eplay24_reference_odds():
    """
    Best-effort quote sync da Eplay24.
    Restituisce dict con default PTS/REB/AST o None se non disponibile.
    """
    candidate_paths = [
        "/api/odds/nba",
        "/api/nba/odds",
        "/odds/nba",
        "/nba",
    ]
    for p in candidate_paths:
        try:
            r = requests.get(f"{EPLAY24_BASE_URL}{p}", timeout=8)
            if r.status_code != 200:
                continue
            content_type = r.headers.get("content-type", "").lower()
            text = r.text or ""
            # Caso JSON esplicito
            if "application/json" in content_type:
                payload = r.json()
                # supporta varie forme, fallback a default
                pts = _safe_float(payload.get("pts_over_odds", 1.90), 1.90)
                reb = _safe_float(payload.get("reb_over_odds", 1.90), 1.90)
                ast = _safe_float(payload.get("ast_over_odds", 1.90), 1.90)
                return {"PTS": max(1.01, pts), "REB": max(1.01, reb), "AST": max(1.01, ast)}

            # Caso HTML: estrazione euristica quote decimali tipo 1.85/1.90/2.05
            matches = re.findall(r"\b([1-9]\.\d{2})\b", text)
            odds = [float(x) for x in matches if 1.01 <= float(x) <= 5.00]
            if len(odds) >= 3:
                # usa mediana dei primi segmenti come riferimento generico
                sample = odds[:30]
                sample.sort()
                med = sample[len(sample)//2]
                val = max(1.01, min(3.5, med))
                return {"PTS": val, "REB": val, "AST": val}
        except Exception:
            continue
    return None


@st.cache_data(ttl=300)
def fetch_oddsapi_nba_events(api_key: str):
    if not api_key:
        return []
    try:
        r = requests.get(
            f"{ODDS_API_BASE}/sports/basketball_nba/events",
            params={"apiKey": api_key},
            timeout=12,
        )
        if r.status_code != 200:
            return []
        return r.json() or []
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_oddsapi_event_props(
    api_key: str,
    event_id: str,
    regions: str = "us,eu,uk",
    odds_pick_mode: str = "conservative",
    bookmaker_filter: str = "",
):
    """
    Restituisce dict con linee/quote per player_points, player_rebounds, player_assists.
    Formato: { player_name: { 'PTS': {'line': X, 'over_odds': Y, 'under_odds': Z}, ... } }
    odds_pick_mode:
      - conservative: quota OVER minima (piu' realistica/prudente)
      - best: quota OVER massima (ottimistica)
      - average: media quote OVER disponibili
    bookmaker_filter:
      keyword opzionale (es. "bovada", "bet365", "pinnacle"), case-insensitive.
    """
    if not api_key or not event_id:
        return {}
    markets = "player_points,player_rebounds,player_assists"
    try:
        r = requests.get(
            f"{ODDS_API_BASE}/sports/basketball_nba/events/{event_id}/odds",
            params={
                "apiKey": api_key,
                "markets": markets,
                "regions": regions,
                "oddsFormat": "decimal",
            },
            timeout=15,
        )
        if r.status_code != 200:
            return {}
        payload = r.json() or {}
    except Exception:
        return {}

    market_to_stat = {
        "player_points": "PTS",
        "player_rebounds": "REB",
        "player_assists": "AST",
    }
    def _pick_price(prices: list[float], mode: str):
        if not prices:
            return None
        if mode == "best":
            return float(max(prices))
        if mode == "average":
            return float(sum(prices) / len(prices))
        return float(min(prices))  # conservative

    raw = {}
    bf = (bookmaker_filter or "").strip().lower()

    for bookmaker in payload.get("bookmakers", []) or []:
        book_title = str(bookmaker.get("title", "") or "")
        if bf and bf not in book_title.lower():
            continue
        for market in bookmaker.get("markets", []) or []:
            mkey = market.get("key")
            stat_col = market_to_stat.get(mkey)
            if not stat_col:
                continue
            for outcome in market.get("outcomes", []) or []:
                player = (outcome.get("description") or outcome.get("name") or "").strip()
                if not player:
                    continue
                line_val = outcome.get("point")
                price = outcome.get("price")
                side = (outcome.get("name") or "").lower()
                if line_val is None or price is None:
                    continue
                slot = raw.setdefault(player, {}).setdefault(stat_col, {})
                line_key = float(line_val)
                bucket = slot.setdefault(line_key, {
                    "over_prices": [],
                    "under_prices": [],
                    "bookmakers": [],
                })
                if "over" in side:
                    bucket["over_prices"].append(float(price))
                    bucket["bookmakers"].append(book_title)
                elif "under" in side:
                    bucket["under_prices"].append(float(price))
                    bucket["bookmakers"].append(book_title)

    props = {}
    for player, by_stat in raw.items():
        for stat_col, lines_map in by_stat.items():
            # Scegli la linea con maggiore copertura (n book), poi la piu' "centrale" come tie-break.
            best_line = None
            best_bucket = None
            best_score = -1
            for ln, b in lines_map.items():
                n_prices = len(b["over_prices"]) + len(b["under_prices"])
                n_books = len(set(b["bookmakers"]))
                score = n_prices + n_books * 2
                if score > best_score:
                    best_score = score
                    best_line = ln
                    best_bucket = b
                elif score == best_score and best_line is not None:
                    # tie-break: preferisci la linea numericamente piu' bassa (piu' standard su over bassi)
                    if float(ln) < float(best_line):
                        best_line = ln
                        best_bucket = b
            if best_bucket is None:
                continue

            over_pick = _pick_price(best_bucket["over_prices"], odds_pick_mode)
            under_pick = _pick_price(best_bucket["under_prices"], odds_pick_mode)
            if over_pick is None and under_pick is None:
                continue
            book = ", ".join(sorted(set(best_bucket["bookmakers"])))[:180]
            props.setdefault(player, {})[stat_col] = {
                "line": float(best_line),
                "over_odds": over_pick,
                "under_odds": under_pick,
                "bookmaker": book or "N/A",
            }
    return props


def _normalize_player_key(name: str) -> str:
    s = (name or "").lower().strip()
    s = s.replace(".", "").replace("'", "").replace("-", " ")
    toks = " ".join(s.split()).split()
    _suffix = {"jr", "sr", "ii", "iii", "iv", "v", "junior", "senior"}
    while toks and toks[-1] in _suffix:
        toks.pop()
    return " ".join(toks)


def _first_name_similarity(a: str, b: str) -> float:
    """Similarità sul solo primo nome token (usa difflib)."""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _match_player_props(target_name: str, props_dict: dict):
    """Associa il nome roster al giocatore usato dal bookmaker nelle props Odds API.

    Non usare mai il solo cognome: su OKC coesistono ad es. *Jalen Williams* e *Jaylin Williams*;
    un match debole assegnerebbe la linea sbagliata e gonfierebbe probabilità/Kelly.

    Ritorna (dict stat → info, chiave_odd_api, tipo_match).
    tipo_match ∈ {'exact','fuzzy', 'none'}.
    """
    if not target_name or not props_dict:
        return None, None, "none"
    target_key = _normalize_player_key(target_name)
    for k in props_dict.keys():
        if _normalize_player_key(k) == target_key:
            return props_dict[k], k, "exact"

    t_parts = target_key.split()
    if len(t_parts) < 2:
        return None, None, "none"
    t_first, t_last = t_parts[0], t_parts[-1]

    best_k = None
    best_fn_ratio = -1.0

    for k in props_dict.keys():
        nk = _normalize_player_key(k)
        k_parts = nk.split()
        if len(k_parts) < 2:
            continue
        k_first, k_last = k_parts[0], k_parts[-1]
        if k_last != t_last:
            continue
        fn_ratio = _first_name_similarity(t_first, k_first)
        # Soglia stretta sul nome di battesimo quando il cognome coincide
        if fn_ratio >= 0.91:
            if fn_ratio > best_fn_ratio:
                best_fn_ratio = fn_ratio
                best_k = k

    if best_k is not None:
        return props_dict[best_k], best_k, f"fuzzy(fn={best_fn_ratio:.2f})"

    return None, None, "none"


def _injury_excludes_player_for_alerts(full_name: str, injuries: list) -> tuple[bool, str]:
    """True se l'injury report indica una esclusione prudenziale dagli alert automatici."""
    tk = _normalize_player_key(full_name)
    t_parts = tk.split()
    if len(t_parts) < 2 or not injuries:
        return False, ""
    t_first, t_last = t_parts[0], t_parts[-1]
    for it in injuries:
        ik = _normalize_player_key(it.get("name") or "")
        i_parts = ik.split()
        if len(i_parts) < 2:
            continue
        i_first, i_last = i_parts[0], i_parts[-1]
        if i_last != t_last:
            continue
        if _first_name_similarity(t_first, i_first) < 0.88:
            continue
        status = str(it.get("status", "") or "").lower()
        if any(k in status for k in ("out", "inactive", "dnp", "suspended")):
            return True, f"Injury: {str(it.get('status') or '').strip() or 'OUT'}"
        if "doubt" in status:
            return True, f"Injury: {str(it.get('status') or '').strip() or 'Doubts'}"
    return False, ""


def _alert_prop_line_credible(stat_col: str, line_val: float, season_avg: float) -> tuple[bool, str]:
    """Scarta combinazioni probabilmente errate (nome/prop mismatch)."""
    if line_val <= 0 or season_avg <= 0:
        return False, ""
    lv = float(line_val)
    av = float(season_avg)

    if stat_col == "PTS":
        # es. scorer ~19 PPP con prop 5.5 → quasi sempre errore sul giocatore
        if av >= 12 and lv < max(11.5, av * 0.58):
            return False, (
                "Linea troppo bassa vs media PPP — mismatch probabile con il nome sul bookmaker"
            )
        if lv > av + 12:
            return False, "Linea troppo alta vs media PPP"

    elif stat_col == "REB":
        if av >= 8 and lv < max(4.5, av * 0.55):
            return False, "Linea REB incoerente con la media"
        if lv > av + 8:
            return False, "Linea REB anomala"

    elif stat_col == "AST":
        if av >= 7 and lv < max(3.5, av * 0.55):
            return False, "Linea AST incoerente con la media"
        if lv > av + 7:
            return False, "Linea AST anomala"

    return True, ""


def _attack_delta_label(delta: float):
    if delta >= 4:
        return "🟢 Migliora forte"
    if delta >= 1:
        return "🟢 Migliora"
    if delta <= -4:
        return "🔴 Peggiora forte"
    if delta <= -1:
        return "🔴 Peggiora"
    return "🟡 Neutro"


def _defense_delta_label(delta_pa: float):
    # difesa migliora quando i punti subiti diminuiscono
    if delta_pa <= -4:
        return "🟢 Migliora forte"
    if delta_pa <= -1:
        return "🟢 Migliora"
    if delta_pa >= 4:
        return "🔴 Peggiora forte"
    if delta_pa >= 1:
        return "🔴 Peggiora"
    return "🟡 Neutro"


def _team_picker(label: str, key_prefix: str, default_label: str | None = None):
    """Renderizza un selectbox di squadra IN-PAGINA e ritorna (team_id, team_label).

    Aggiorna anche `st.session_state[f"{key_prefix}_id"]` e `_label`
    per retro-compatibilità con altre pagine che li leggono.
    """
    teams_opts = fetch_teams(SEASON)
    if not teams_opts:
        st.warning("Team list non disponibile (API). Riprova fra poco.")
        if st.button("🔄 Riprova caricamento team", key=f"retry_{key_prefix}"):
            fetch_teams.clear()
            st.rerun()
        return None, None

    labels = [t["label"] for t in teams_opts]
    fallback = default_label if default_label in labels else labels[0]
    current = st.session_state.get(f"{key_prefix}_label", fallback)
    if current not in labels:
        current = fallback
    idx = labels.index(current)
    chosen = st.selectbox(label, labels, index=idx, key=f"{key_prefix}_label")
    lookup = {t["label"]: t["id"] for t in teams_opts}
    team_id = lookup.get(chosen)
    st.session_state[f"{key_prefix}_id"] = team_id
    return team_id, chosen


def _current_streak(results: list) -> str:
    """Da una lista di 'W'/'L' più recenti in alto, ritorna la streak corrente."""
    if not results:
        return "—"
    first = results[0]
    n = 0
    for r in results:
        if r == first:
            n += 1
        else:
            break
    return f"{first}{n}"


def team_stats_page(n_partite: int):
    """Scheda statistica completa di UNA squadra: attacco, difesa e 12+ metriche."""
    st.subheader("🏀 Scheda Squadra")
    st.caption(
        "Statistiche complete di una singola squadra: attacco, difesa, trend, "
        "streak, distribuzione punteggi, casa/trasferta e altro."
    )
    phase_selected = st.session_state.get("phase_type", "Tutte")

    team_id, team_label = _team_picker(
        "🏀 Squadra da analizzare",
        key_prefix="team_1",
        default_label="Los Angeles Lakers (LAL)",
    )
    if not team_id:
        return

    with st.spinner(f"Caricamento dati {team_label}..."):
        df = fetch_team_comparison_data(team_id, SEASON, phase_selected)

    if isinstance(df, str) or df is None or df.empty:
        st.error("Nessun dato disponibile per questa squadra con i filtri attuali.")
        return

    n_eff = min(n_partite, len(df))
    d = df.head(n_eff).copy()
    st.caption(f"Filtro: {phase_selected} · Ultime {n_eff}/{len(df)} gare **terminate** disponibili")
    st.caption(
        "**Nota:** *PF* qui = **punti segnati** dalla squadra ('Punti Fatti'); *PA* = punti subiti — "
        "non sono i falli personali del box score NBA."
    )

    pf_mean = float(d["PF"].mean())
    pa_mean = float(d["PA"].mean())
    diff_mean = pf_mean - pa_mean
    wins = (d["RESULT"] == "W").sum()
    losses = (d["RESULT"] == "L").sum()
    win_rate = wins / len(d) * 100 if len(d) else 0.0
    pf_full = float(df["PF"].mean())
    pa_full = float(df["PA"].mean())

    wins_df = d[d["RESULT"] == "W"]
    losses_df = d[d["RESULT"] == "L"]
    avg_margin_w = float(wins_df["DIFF"].mean()) if not wins_df.empty else 0.0
    avg_margin_l = float(losses_df["DIFF"].mean()) if not losses_df.empty else 0.0

    high_score_pct = float((d["PF"] >= 120).mean() * 100)
    low_score_pct = float((d["PF"] < 100).mean() * 100)
    shutdown_pct = float((d["PA"] < 100).mean() * 100)
    blowout_pct = float((d["DIFF"].abs() >= 15).mean() * 100)

    streak_now = _current_streak(d["RESULT"].tolist())
    last5 = "".join(d["RESULT"].head(5).tolist())
    pf_max = int(d["PF"].max()) if not d.empty else 0
    pf_min = int(d["PF"].min()) if not d.empty else 0
    pa_max = int(d["PA"].max()) if not d.empty else 0
    pa_min = int(d["PA"].min()) if not d.empty else 0

    pf_recent = float(d.head(5)["PF"].mean()) if len(d) >= 1 else 0.0
    pa_recent = float(d.head(5)["PA"].mean()) if len(d) >= 1 else 0.0
    trend_att = pf_recent - pf_full
    trend_def = pa_recent - pa_full

    st.markdown(f"### 🟢 {team_label}")
    st.markdown(
        f'<div class="verdict-box" style="border-left:4px solid #00D4AA;">'
        f'📊 <strong>{wins}V – {losses}S</strong> '
        f'· Win Rate <strong>{win_rate:.0f}%</strong> '
        f'· Streak: <strong>{streak_now}</strong> '
        f'· Ultime 5: <code>{last5 or "—"}</code>'
        f'</div>', unsafe_allow_html=True)

    st.markdown("#### ⚔️ Attacco e Difesa")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Attacco (PF medi)", f"{pf_mean:.1f}",
              delta=f"{(pf_mean - pf_full):+.1f} vs stagione",
              help="Punti fatti in media dalla squadra nelle ultime gare. Più alti = attacco prolifico.")
    a2.metric("Difesa (PA medi)", f"{pa_mean:.1f}",
              delta=f"{(pa_mean - pa_full):+.1f} vs stagione", delta_color="inverse",
              help="Punti subiti in media. Più bassi = difesa più solida.")
    a3.metric("Net Rating", f"{diff_mean:+.1f}",
              help="Differenza punti media (PF − PA). Positivo = squadra dominante; negativo = in difficoltà.")
    a4.metric("Win Rate", f"{win_rate:.0f}%",
              delta=f"{wins}V / {losses}S",
              help="Percentuale di partite vinte sulle ultime gare considerate.")

    st.markdown("#### 📈 Forma e Trend recenti")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Trend Attacco (5G)", f"{pf_recent:.1f}", delta=f"{trend_att:+.1f}",
              help="Media PF ultime 5 partite vs media stagionale. Positivo = in forma offensiva.")
    t2.metric("Trend Difesa (5G)", f"{pa_recent:.1f}", delta=f"{trend_def:+.1f}",
              delta_color="inverse",
              help="Media PA ultime 5 vs stagionale. Negativo = difesa migliorata.")
    t3.metric("Streak attuale", streak_now,
              help="Sequenza di vittorie (W) o sconfitte (L) consecutive nelle gare più recenti.")
    t4.metric("Ultime 5", last5 or "—",
              help="Ordine cronologico (più recente a sinistra). Es. 'WWLWW' = 4 vinte e 1 persa nelle ultime 5.")

    st.markdown("#### 🎯 Profilo Performance")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("% gare ≥120 PF", f"{high_score_pct:.0f}%",
              help="Quante volte la squadra ha sfondato i 120 punti. Indicatore di attacco esplosivo.")
    p2.metric("% gare <100 PF", f"{low_score_pct:.0f}%",
              help="Quante volte la squadra è stata sotto i 100 punti. Attacco bloccato.")
    p3.metric("% gare con difesa <100", f"{shutdown_pct:.0f}%",
              help="Quante volte la difesa ha tenuto l'avversario sotto i 100 punti.")
    p4.metric("% blowout (±15)", f"{blowout_pct:.0f}%",
              help="Percentuale di partite chiuse con uno scarto ≥15 punti. Squadra polarizzata.")

    st.markdown("#### 📊 Estremi e Margini")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Margine medio nelle V", f"{avg_margin_w:+.1f}" if wins else "—",
              help="Quanto vince in media (differenza PF-PA nelle vittorie).")
    e2.metric("Margine medio nelle S", f"{avg_margin_l:+.1f}" if losses else "—",
              help="Quanto perde in media (differenza PF-PA nelle sconfitte).")
    e3.metric("Best PF", f"{pf_max}",
              help="Punteggio massimo segnato nelle gare considerate.")
    e4.metric("Worst PA", f"{pa_max}",
              help="Massimo punteggio subito nelle gare considerate (peggior performance difensiva).")

    st.markdown("---")
    st.markdown("#### 📈 Trend Punti Fatti / Subiti")
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(
        x=d["GAME_DATE"], y=d["PF"], mode="lines+markers", name="Punti Fatti",
        line=dict(color="#00D4AA", width=2.5)))
    fig_t.add_trace(go.Scatter(
        x=d["GAME_DATE"], y=d["PA"], mode="lines+markers", name="Punti Subiti",
        line=dict(color="#FF5252", width=2.5)))
    fig_t.add_hline(y=pf_mean, line_dash="dot", line_color="#00D4AA",
                    annotation_text=f"Media PF {pf_mean:.1f}")
    fig_t.add_hline(y=pa_mean, line_dash="dot", line_color="#FF5252",
                    annotation_text=f"Media PA {pa_mean:.1f}")
    fig_t.update_layout(height=360, template="plotly_dark",
                        xaxis_title="Data", yaxis_title="Punti",
                        margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_t, width="stretch")

    st.markdown("#### 🎲 Distribuzione esiti (W/L)")
    dist_fig = go.Figure(go.Bar(
        x=["Vittorie", "Sconfitte"], y=[int(wins), int(losses)],
        marker_color=["#00D4AA", "#FF5252"],
        text=[int(wins), int(losses)], textposition="outside",
    ))
    dist_fig.update_layout(height=260, template="plotly_dark",
                           margin=dict(t=20, b=20, l=20, r=20),
                           yaxis_title="Numero partite")
    st.plotly_chart(dist_fig, width="stretch")

    with st.expander("📋 Tabella partite considerate"):
        st.dataframe(d, width="stretch", hide_index=True)


def teams_comparison_page(n_partite: int, embedded: bool = False):
    if not embedded:
        st.subheader("🏀 Confronto Squadre")
        st.caption("Confronta due squadre NBA: attacco, difesa, trend e testa-a-testa.")
    phase_selected = st.session_state.get("phase_type", "Tutte")

    cps1, cps2 = st.columns(2)
    with cps1:
        team1_id, team1_label = _team_picker(
            "Squadra 1", key_prefix="team_1",
            default_label="Los Angeles Lakers (LAL)")
    with cps2:
        team2_id, team2_label = _team_picker(
            "Squadra 2", key_prefix="team_2",
            default_label="Boston Celtics (BOS)")

    if not team1_id or not team2_id:
        return
    if team1_id == team2_id:
        st.warning("Seleziona due squadre diverse.")
        return

    with st.spinner("Caricamento dati squadre..."):
        df1 = fetch_team_comparison_data(team1_id, SEASON, phase_selected)
        df2 = fetch_team_comparison_data(team2_id, SEASON, phase_selected)

    if isinstance(df1, str) or isinstance(df2, str) or df1 is None or df2 is None:
        st.error("Errore nel caricamento dati squadre per il filtro selezionato.")
        return

    d1 = df1.head(n_partite).copy()
    d2 = df2.head(n_partite).copy()
    st.caption(f"Filtro partite: {phase_selected} · Ultime **{n_partite} gare terminate** (ignoriamo "
               "partite non ancora giocate: altrimenti punteggio 0 falserebbe le medie).")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 🟢 {team1_label}")
        st.metric("Punti Fatti medi", f"{d1['PF'].mean():.1f}")
        st.metric("Punti Subiti medi", f"{d1['PA'].mean():.1f}")
        st.metric("Net Rating base", f"{(d1['PF'].mean() - d1['PA'].mean()):+.1f}")
        st.metric("Win Rate", f"{(d1['RESULT'] == 'W').mean() * 100:.0f}%")
    with c2:
        st.markdown(f"### 🔴 {team2_label}")
        st.metric("Punti Fatti medi", f"{d2['PF'].mean():.1f}", delta=f"{d2['PF'].mean()-d1['PF'].mean():+.1f}")
        st.metric("Punti Subiti medi", f"{d2['PA'].mean():.1f}", delta=f"{d2['PA'].mean()-d1['PA'].mean():+.1f}")
        st.metric("Net Rating base", f"{(d2['PF'].mean() - d2['PA'].mean()):+.1f}",
                  delta=f"{((d2['PF'].mean()-d2['PA'].mean())-(d1['PF'].mean()-d1['PA'].mean())):+.1f}")
        st.metric("Win Rate", f"{(d2['RESULT'] == 'W').mean() * 100:.0f}%",
                  delta=f"{((d2['RESULT'] == 'W').mean() - (d1['RESULT'] == 'W').mean()) * 100:+.0f}%")

    st.markdown("---")
    st.subheader("📈 Trend Punti Fatti")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d1["GAME_DATE"], y=d1["PF"], mode="lines+markers", name=team1_label,
        line=dict(color="#00D4AA", width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=d2["GAME_DATE"], y=d2["PF"], mode="lines+markers", name=team2_label,
        line=dict(color="#FF5252", width=2.5)
    ))
    fig.update_layout(height=340, template="plotly_dark", xaxis_title="Data", yaxis_title="Punti")
    st.plotly_chart(fig, width="stretch")

    st.subheader("📋 Riepilogo confronto squadre")
    summary = pd.DataFrame({
        "Stat": ["PF medi", "PA medi", "Diff medio", "Win Rate", "Max PF", "Min PF"],
        team1_label: [
            f"{d1['PF'].mean():.1f}",
            f"{d1['PA'].mean():.1f}",
            f"{d1['DIFF'].mean():+.1f}",
            f"{(d1['RESULT'] == 'W').mean() * 100:.0f}%",
            f"{d1['PF'].max():.0f}",
            f"{d1['PF'].min():.0f}",
        ],
        team2_label: [
            f"{d2['PF'].mean():.1f}",
            f"{d2['PA'].mean():.1f}",
            f"{d2['DIFF'].mean():+.1f}",
            f"{(d2['RESULT'] == 'W').mean() * 100:.0f}%",
            f"{d2['PF'].max():.0f}",
            f"{d2['PF'].min():.0f}",
        ],
    })
    st.dataframe(summary, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("🤝 Testa a Testa: Attacco/Difesa")
    h2h = fetch_head_to_head_data(team1_id, team2_id, SEASON, phase_selected)
    if isinstance(h2h, str) or h2h is None:
        st.info("Nessun head-to-head disponibile con i filtri attuali.")
        return

    h2h_n = h2h.head(n_partite).copy()
    t1_base_att = float(d1["PF"].mean())
    t1_base_def = float(d1["PA"].mean())
    t2_base_att = float(d2["PF"].mean())
    t2_base_def = float(d2["PA"].mean())

    t1_h2h_att = float(h2h_n["T1_PF"].mean())
    t1_h2h_def = float(h2h_n["T1_PA"].mean())
    t2_h2h_att = float(h2h_n["T2_PF"].mean())
    t2_h2h_def = float(h2h_n["T2_PA"].mean())

    t1_att_delta = t1_h2h_att - t1_base_att
    t1_def_delta = t1_h2h_def - t1_base_def
    t2_att_delta = t2_h2h_att - t2_base_att
    t2_def_delta = t2_h2h_def - t2_base_def

    h1, h2 = st.columns(2)
    with h1:
        st.markdown(f"**{team1_label}**")
        st.metric("Attacco H2H vs Baseline", f"{t1_h2h_att:.1f}", delta=f"{t1_att_delta:+.1f}")
        st.caption(_attack_delta_label(t1_att_delta))
        st.metric("Difesa H2H (PA) vs Baseline", f"{t1_h2h_def:.1f}", delta=f"{t1_def_delta:+.1f}")
        st.caption(_defense_delta_label(t1_def_delta))
    with h2:
        st.markdown(f"**{team2_label}**")
        st.metric("Attacco H2H vs Baseline", f"{t2_h2h_att:.1f}", delta=f"{t2_att_delta:+.1f}")
        st.caption(_attack_delta_label(t2_att_delta))
        st.metric("Difesa H2H (PA) vs Baseline", f"{t2_h2h_def:.1f}", delta=f"{t2_def_delta:+.1f}")
        st.caption(_defense_delta_label(t2_def_delta))

    h2h_summary = pd.DataFrame({
        "Metrica": ["Attacco baseline", "Attacco H2H", "Delta attacco", "Difesa baseline (PA)", "Difesa H2H (PA)", "Delta difesa (PA)"],
        team1_label: [f"{t1_base_att:.1f}", f"{t1_h2h_att:.1f}", f"{t1_att_delta:+.1f}", f"{t1_base_def:.1f}", f"{t1_h2h_def:.1f}", f"{t1_def_delta:+.1f}"],
        team2_label: [f"{t2_base_att:.1f}", f"{t2_h2h_att:.1f}", f"{t2_att_delta:+.1f}", f"{t2_base_def:.1f}", f"{t2_h2h_def:.1f}", f"{t2_def_delta:+.1f}"],
    })
    st.dataframe(h2h_summary, width="stretch", hide_index=True)


def _value_label(edge: float):
    if edge >= 8:
        return "VALUE FORTE"
    if edge >= 4:
        return "VALUE MODERATA"
    if edge >= 1:
        return "VALUE LEGGERA"
    return "NO BET"


def _kelly_stake(
    prob_pct: float,
    odd: float,
    bankroll: float,
    fraction: float = 1.0,
    max_pct_bankroll: float = 2.0,
) -> float:
    if odd <= 1 or prob_pct <= 0 or bankroll <= 0:
        return 0.0
    p = max(0.0, min(1.0, prob_pct / 100.0))
    b = odd - 1.0
    kelly = (b * p - (1 - p)) / b
    if kelly <= 0:
        return 0.0
    stake = bankroll * kelly * max(0.0, min(1.0, fraction))
    if max_pct_bankroll > 0 and bankroll > 0:
        cap = bankroll * (max_pct_bankroll / 100.0)
        stake = min(stake, cap)
    return round(stake, 2)


def _evaluate_player_value_rows(
    name: str,
    pid: int,
    linee: dict,
    odds: dict,
    n_partite: int,
    phase_selected: str,
    expected_team_id: int = None,
    bankroll: float = 1000.0,
    kelly_frac: float = 0.25,
):
    df_all = get_nba_data(pid, name, SEASON, API_KEY, phase_selected)
    if isinstance(df_all, str) or df_all is None or df_all.empty:
        return []
    if expected_team_id is not None and "TEAM_ID" in df_all.columns:
        real_team = int(df_all["TEAM_ID"].iloc[0])
        if real_team != int(expected_team_id):
            return []
    n_eff = len(df_all) if st.session_state.get("use_all_games", False) else n_partite
    n_eff = max(1, n_eff)
    df_r = df_all.head(n_eff).copy()

    rows = []
    for col in ["PTS", "REB", "AST"]:
        if col not in df_r.columns:
            continue
        line = linee[col]
        avg = float(df_r[col].mean())
        hit = float((df_r[col] > line).mean() * 100)
        prob = float((1 - poisson.cdf(line, avg)) * 100 if avg > 0 else 0.0)
        odd = float(odds[col])
        implied = 100 / odd if odd > 1 else 0.0
        edge = prob - implied
        kelly_eur = _kelly_stake(prob, odd, bankroll, kelly_frac)
        rows.append({
            "Giocatore": name,
            "Stat": col,
            "Linea": line,
            "Quota": odd,
            "Media": round(avg, 2),
            "Prob Over %": round(prob, 1),
            "Implied %": round(implied, 1),
            "Edge %": round(edge, 1),
            "Hit Rate %": round(hit, 1),
            "Kelly €": kelly_eur,
            "Signal": _value_label(edge),
        })
    return rows


def _scan_value_with_real_odds(
    api_key: str,
    n_partite: int,
    phase_selected: str,
    bankroll: float,
    kelly_frac: float,
    min_edge: float,
    min_hit: float,
    time_mode: str,
    odds_pick_mode: str = "conservative",
    bookmaker_filter: str = "",
    kelly_cap_pct: float = 2.0,
):
    """
    Modalità AUTO con linee/quote reali da The Odds API.
    """
    empty_quality = {
        "events_scanned": 0,
        "props_missing": 0,
        "players_seen": 0,
        "players_injury_blocked": 0,
        "players_name_miss": 0,
        "players_team_miss": 0,
        "rows_line_plausibility_drop": 0,
        "rows_created": 0,
    }
    events = fetch_oddsapi_nba_events(api_key)
    if not events:
        return None, "Nessun evento NBA disponibile (verifica API key The Odds API).", empty_quality

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    horizon = {
        "Prossime 6h": 6,
        "Prossime 12h": 12,
        "Prossime 24h": 24,
    }
    if time_mode in horizon:
        end_utc = now_utc + datetime.timedelta(hours=horizon[time_mode])
    else:
        end_utc = now_utc + datetime.timedelta(hours=36)

    filtered_events = []
    for ev in events:
        commence = ev.get("commence_time", "")
        try:
            ev_dt = datetime.datetime.fromisoformat(commence.replace("Z", "+00:00"))
        except Exception:
            continue
        if ev_dt >= now_utc and ev_dt <= end_utc:
            filtered_events.append((ev, ev_dt))

    if not filtered_events:
        return None, "Nessun evento NBA nel filtro orario richiesto.", empty_quality

    # mappa team API->roster locale
    teams_local = {t["id"]: t for t in fetch_teams(SEASON)}
    name_to_local_team = {}
    for t in teams_local.values():
        name_to_local_team[t["name"].lower()] = t

    rows = []
    debug_info = []
    quality = {
        "events_scanned": len(filtered_events),
        "props_missing": 0,
        "players_seen": 0,
        "players_injury_blocked": 0,
        "players_name_miss": 0,
        "players_team_miss": 0,
        "rows_line_plausibility_drop": 0,
        "rows_created": 0,
    }
    injury_cache: dict[int, list] = {}

    for ev, ev_dt in filtered_events:
        event_id = ev.get("id")
        home_name = ev.get("home_team", "")
        away_name = ev.get("away_team", "")
        props = fetch_oddsapi_event_props(
            api_key,
            event_id,
            odds_pick_mode=odds_pick_mode,
            bookmaker_filter=bookmaker_filter,
        )
        if not props:
            quality["props_missing"] += 1
            debug_info.append(f"{home_name} vs {away_name}: nessuna prop disponibile")
            continue

        # roster di entrambe le squadre dal nostro provider
        roster_players = []
        match_team_ids: list[int] = []
        for tname in [home_name, away_name]:
            local_t = name_to_local_team.get(tname.lower())
            if not local_t:
                # match parziale (Lakers, Celtics ecc.)
                for cand in teams_local.values():
                    if tname.lower().split()[-1] in cand["name"].lower():
                        local_t = cand
                        break
            if local_t:
                tid_i = int(local_t["id"])
                match_team_ids.append(tid_i)
                roster_players.extend(fetch_team_players(tid_i, SEASON))

        # injury report squadre dell'evento (cache soft)
        for tid_i in dict.fromkeys(match_team_ids):  # unici, ordine conservato
            if tid_i not in injury_cache:
                injury_cache[tid_i] = fetch_team_injuries(int(tid_i), SEASON) or []

        for p in roster_players:
            quality["players_seen"] += 1
            pid = p.get("id")
            pname = p.get("name")
            if not pid or not pname:
                continue
            team_tid = int(p.get("team_id"))
            injuries_ev = injury_cache.get(team_tid) or []

            blocked, inj_tag = _injury_excludes_player_for_alerts(pname, injuries_ev)
            if blocked:
                quality["players_injury_blocked"] += 1
                continue

            matched_props, matched_key, match_kind = _match_player_props(pname, props)
            if not matched_props:
                quality["players_name_miss"] += 1
                continue
            df_all = get_nba_data(int(pid), pname, SEASON, API_KEY, phase_selected)
            if isinstance(df_all, str) or df_all is None or df_all.empty:
                continue
            n_eff = len(df_all) if st.session_state.get("use_all_games", False) else n_partite
            df_r = df_all.head(max(1, n_eff)).copy()

            # verifica roster attuale nella partita dell'alert
            if "TEAM_ID" in df_r.columns:
                try:
                    roster_tid = int(df_r["TEAM_ID"].iloc[0])
                    if roster_tid != team_tid:
                        quality["players_team_miss"] += 1
                        continue
                except (TypeError, ValueError):
                    pass

            for stat_col, info in matched_props.items():
                line_val = float(info.get("line", 0))
                over_odd = info.get("over_odds")
                if stat_col not in df_r.columns or line_val <= 0:
                    continue
                avg = float(df_r[stat_col].mean())

                plausible, _msg = _alert_prop_line_credible(stat_col, line_val, avg)
                if not plausible:
                    quality["rows_line_plausibility_drop"] += 1
                    continue

                hit = float((df_r[stat_col] > line_val).mean() * 100)
                raw_prob = float((1 - poisson.cdf(line_val, avg)) * 100 if avg > 0 else 0.0)
                # Evita saturation irrealistica (Poisson instabile sugli scenario estremi)
                prob = min(round(raw_prob, 1), 96.5)

                # OVER only (Eplay24 supporta solo Over per player props)
                if over_odd:
                    implied = 100 / over_odd
                    edge = prob - implied
                    book_label = (matched_key or pname).strip()
                    note_txt = ""
                    if _normalize_player_key(book_label) != _normalize_player_key(pname):
                        note_txt = (
                            f"Prop sul book intestata «{book_label}» ≠ roster «{pname}» · {match_kind}"
                        )
                    elif match_kind != "exact":
                        note_txt = f"Variante grafica nome · {match_kind}"

                    rows.append({
                        "Giocatore": pname,
                        "Stat": stat_col,
                        "Linea": line_val,
                        "Quota Over": round(float(over_odd), 2),
                        "Bookmaker": info.get("bookmaker", ""),
                        "Su bookmaker": book_label,
                        "Media": round(avg, 2),
                        "Prob Over %": round(prob, 1),
                        "Implied %": round(implied, 1),
                        "Edge %": round(edge, 1),
                        "Hit Rate %": round(hit, 1),
                        # Kelly capped per rischio operativo
                        "Kelly €": _kelly_stake(
                            prob, float(over_odd), bankroll, kelly_frac,
                            max_pct_bankroll=kelly_cap_pct
                        ),
                        "Signal": _value_label(edge),
                        "Match": f"{away_name} @ {home_name}",
                        "Verifica": note_txt,
                        "Quote As Of (UTC)": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    quality["rows_created"] += 1

    if not rows:
        hint = "; ".join(debug_info[:12]) if debug_info else ""
        base = ("Nessuna prop incrociabile coi roster dopo i nuovi filtri di sicurezza, oppure soglie troppo strette.")
        return None, f"{base}" + (f"\n\n(Dettaglio: {hint})" if hint else ""), quality

    df = pd.DataFrame(rows)
    # dedup forte: stessa pick (match+giocatore+stat+linea) una sola volta, tenendo edge migliore
    dedup_keys = ["Match", "Giocatore", "Stat", "Linea"]
    df = df.sort_values(["Edge %", "Prob Over %"], ascending=False)
    df = df.drop_duplicates(subset=dedup_keys, keep="first").reset_index(drop=True)
    df = df[(df["Edge %"] >= min_edge) & (df["Hit Rate %"] >= min_hit)]
    if df.empty:
        return None, "Nessuna value bet con i filtri correnti.", quality
    df = df.sort_values(["Edge %", "Prob Over %"], ascending=False).reset_index(drop=True)
    return df, None, quality


def value_alerts_page(linee: dict, n_partite: int):
    st.subheader("🚨 Alert Value Giornata")
    st.caption("Scanner value-bet con linee/quote reali da The Odds API + fallback manuale.")
    phase_selected = st.session_state.get("phase_type", "Tutte")

    with st.expander("🏀 Squadre della giornata (per modalità manuale)", expanded=False):
        st.caption("Le due squadre selezionate qui vengono usate solo dallo scanner manuale "
                   "per scegliere i giocatori. La modalità Auto le ignora.")
        cva, cvb = st.columns(2)
        with cva:
            team1_id, team1_label = _team_picker(
                "Team 1", key_prefix="team_1",
                default_label="Los Angeles Lakers (LAL)")
        with cvb:
            team2_id, team2_label = _team_picker(
                "Team 2", key_prefix="team_2",
                default_label="Boston Celtics (BOS)")

    if not team1_id or not team2_id:
        st.info("Seleziona Team 1 e Team 2 dall'expander qui sopra.")
        return

    mode = st.radio(
        "Modalità scanner",
        ["🔌 Auto (linee reali via The Odds API)", "✍️ Manuale (linee/quote sidebar)"],
        index=0,
        horizontal=True,
        key="alert_mode_real",
    )

    if mode.startswith("🔌"):
        st.markdown("#### Connessione The Odds API")
        st.caption("Free tier 500 req/mese. Chiave letta da configurazione sicura (secrets/env).")
        odds_key = ODDS_API_KEY
        f1, f2, f3 = st.columns(3)
        min_edge_a = f1.slider("Edge minimo (%)", -5, 20, 4, key="alert_min_edge_auto")
        min_hit_a = f2.slider("Hit rate minimo (%)", 30, 90, 50, key="alert_min_hit_auto")
        time_mode_a = f3.selectbox(
            "Filtro orario",
            ["Prossime 6h", "Prossime 12h", "Prossime 24h", "Solo non iniziate"],
            index=2,
            key="alert_time_mode_auto",
        )
        k1, k2 = st.columns(2)
        bankroll_for_kelly_a = k1.number_input("Bankroll riferimento (€)", min_value=10.0, value=1000.0, step=50.0, key="alert_bk_ref_auto")
        kelly_fraction_a = k2.slider("Kelly frazionato", 0.05, 1.0, 0.25, step=0.05, key="alert_kelly_frac_auto")
        kelly_cap_pct_a = st.slider(
            "Cap stake Kelly (% bankroll)",
            0.5, 5.0, 2.0, step=0.1,
            key="alert_kelly_cap_pct_auto",
            help="Limite massimo stake per pick. Es. 2.0 = max 2% del bankroll anche se Kelly teorico e' piu' alto."
        )
        o1, o2 = st.columns(2)
        odds_mode_label = o1.selectbox(
            "Strategia quote",
            ["Conservativa (quota minima)", "Media bookmaker", "Ottimistica (quota massima)"],
            index=0,
            key="alert_odds_pick_mode",
        )
        bookmaker_filter = o2.text_input(
            "Filtro bookmaker (opzionale)",
            value="",
            placeholder="es. bovada / bet365 / pinnacle",
            key="alert_bookmaker_filter",
        )
        odds_mode_map = {
            "Conservativa (quota minima)": "conservative",
            "Media bookmaker": "average",
            "Ottimistica (quota massima)": "best",
        }

        if not st.button("🔎 Scansiona linee reali"):
            st.info("Premi per scaricare linee/quote reali e generare alert.")
            return
        if not odds_key:
            st.error("Inserisci l'API key di The Odds API per la modalità auto.")
            return

        with st.spinner("Scarico eventi NBA, props e calcolo value..."):
            df_auto, err, qstats = _scan_value_with_real_odds(
                api_key=odds_key,
                n_partite=n_partite,
                phase_selected=phase_selected,
                bankroll=float(bankroll_for_kelly_a),
                kelly_frac=float(kelly_fraction_a),
                min_edge=float(min_edge_a),
                min_hit=float(min_hit_a),
                time_mode=time_mode_a,
                odds_pick_mode=odds_mode_map.get(odds_mode_label, "conservative"),
                bookmaker_filter=bookmaker_filter,
                kelly_cap_pct=float(kelly_cap_pct_a),
            )
        if err:
            st.warning(err)
            return
        st.success(f"Trovate {len(df_auto)} value bet OVER reali (linee + quote da bookmakers).")
        st.info(
            "**Controlli anti-errore:** le props del bookmaker si collegano al roster solo se **nome e cognome** "
            "coincidono (mai solo il cognome: evita linee scambiate tipo Jalen/Jaylin Williams). "
            "Escludiamo anche chi risulta OUT/Doubtful sull’injury API e le linee **incoerenti** con la media "
            "stagionale/recente. Resta consigliata un’occhiata alla colonna **Su bookmaker** / **Verifica** e al "
            "**match** reale."
        )
        st.caption("Solo segnali OVER (compatibili con Eplay24). Under disabilitati.")
        st.caption(
            f"Quote calcolate in modalita': **{odds_mode_label}**"
            + (f" · filtro bookmaker: **{bookmaker_filter}**" if bookmaker_filter else "")
        )
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Eventi scansionati", int((qstats or {}).get("events_scanned", 0)))
        q2.metric("Player visti", int((qstats or {}).get("players_seen", 0)))
        q3.metric("Scarti injury", int((qstats or {}).get("players_injury_blocked", 0)))
        q4.metric("Scarti mismatch", int((qstats or {}).get("players_name_miss", 0))
                  + int((qstats or {}).get("players_team_miss", 0)))
        st.dataframe(df_auto, width="stretch", hide_index=True)

        top = df_auto.head(5)
        st.markdown("#### 🔥 Top 5 Pick reali")
        for _, r in top.iterrows():
            vz = str(r.get("Verifica", "") or "").strip()
            ext = f" ⚠️ {vz}" if vz else ""
            st.write(
                f"- **{r['Giocatore']} {r['Stat']} OVER {r['Linea']}** · "
                f"Quota {r['Quota Over']} ({r['Bookmaker']}) · Prob {r['Prob Over %']}% · "
                f"Edge {r['Edge %']}% · Kelly €{float(r['Kelly €']):.2f} · {r['Signal']} · {r['Match']}{ext}"
            )

        st.download_button(
            "⬇️ Esporta Alert Value (CSV)",
            data=df_to_csv(df_auto),
            file_name=f"alert_value_real_{datetime.date.today()}.csv",
            mime="text/csv",
        )
        _telegram_alert_block(df_auto, source="Auto · Odds API",
                              key_prefix="tg_auto", default_top=5)
        return

    # init default odds session keys
    if "alert_odd_pts" not in st.session_state:
        st.session_state["alert_odd_pts"] = 1.90
    if "alert_odd_reb" not in st.session_state:
        st.session_state["alert_odd_reb"] = 1.90
    if "alert_odd_ast" not in st.session_state:
        st.session_state["alert_odd_ast"] = 1.90

    auto_eplay = st.checkbox("Auto-sync quote da Eplay24 (beta)", value=True, key="auto_eplay_sync")
    sync_col1, sync_col2 = st.columns([1, 2])
    do_sync = sync_col1.button("🔄 Sync Eplay24")
    if auto_eplay and ("_eplay_synced_once" not in st.session_state):
        do_sync = True
        st.session_state["_eplay_synced_once"] = True
    if do_sync:
        odds_ref = fetch_eplay24_reference_odds()
        if odds_ref:
            st.session_state["alert_odd_pts"] = float(odds_ref["PTS"])
            st.session_state["alert_odd_reb"] = float(odds_ref["REB"])
            st.session_state["alert_odd_ast"] = float(odds_ref["AST"])
            sync_col2.success("Quote Eplay24 sincronizzate.")
        else:
            sync_col2.warning("Sync Eplay24 non disponibile ora. Uso quote manuali.")

    c1, c2, c3 = st.columns(3)
    odd_pts = c1.number_input("Quota target PTS", min_value=1.01, step=0.01, key="alert_odd_pts")
    odd_reb = c2.number_input("Quota target REB", min_value=1.01, step=0.01, key="alert_odd_reb")
    odd_ast = c3.number_input("Quota target AST", min_value=1.01, step=0.01, key="alert_odd_ast")
    f1, f2, f3 = st.columns(3)
    min_edge = f1.slider("Edge minimo (%)", -5, 20, 4, key="alert_min_edge")
    min_hit = f2.slider("Hit rate minimo (%)", 30, 90, 50, key="alert_min_hit")
    max_players = f3.slider("Max giocatori per team", 4, 15, 10, key="alert_max_players")
    m1, m2 = st.columns(2)
    scan_all_today = m1.checkbox("Scan all teams today", value=False, key="scan_all_teams_today")
    max_teams_today = m2.slider("Max team scan today", 2, 20, 10, key="max_teams_today")
    k1, k2 = st.columns(2)
    bankroll_for_kelly = k1.number_input("Bankroll riferimento (€)", min_value=10.0, value=1000.0, step=50.0, key="alert_bk_ref")
    kelly_fraction = k2.slider("Kelly frazionato (0-1)", 0.05, 1.0, 0.25, step=0.05, key="alert_kelly_frac")
    time_mode = st.selectbox(
        "Filtro orario partite",
        ["Nessun filtro", "Solo non iniziate", "Prossime 6h", "Prossime 12h", "Prossime 24h"],
        index=1,
        key="alert_time_mode",
    )

    if not st.button("🔎 Genera Alert Value"):
        st.info("Premi il pulsante per calcolare le migliori value bet della giornata.")
        return

    odds = {"PTS": odd_pts, "REB": odd_reb, "AST": odd_ast}
    with st.spinner("Analisi value in corso..."):
        team_ids_to_scan = []
        team_label_by_id = {}
        if scan_all_today:
            if time_mode == "Prossime 6h":
                games_today = fetch_games_window(6)
            elif time_mode == "Prossime 12h":
                games_today = fetch_games_window(12)
            elif time_mode == "Prossime 24h":
                games_today = fetch_games_window(24)
            else:
                today_iso = str(datetime.date.today())
                games_today = fetch_games_by_date(today_iso)
            ids = []
            for g in games_today:
                tm = g.get("teams", {}) or {}
                home = tm.get("home", {}) or {}
                vis = tm.get("visitors", {}) or {}
                is_finished, is_not_started, _ = _game_status_flags(g)
                # hard filter: escludi sempre partite finite nello scanner giornaliero
                if is_finished:
                    continue
                # se richiesto, considera solo non iniziate
                if time_mode == "Solo non iniziate" and not is_not_started:
                        continue
                hid = home.get("id")
                vid = vis.get("id")
                if hid:
                    ids.append(int(hid))
                    team_label_by_id[int(hid)] = home.get("name") or home.get("code") or f"ID {hid}"
                if vid:
                    ids.append(int(vid))
                    team_label_by_id[int(vid)] = vis.get("name") or vis.get("code") or f"ID {vid}"
            # dedup preservando ordine
            seen_ids = set()
            for tid in ids:
                if tid not in seen_ids:
                    seen_ids.add(tid)
                    team_ids_to_scan.append(tid)
            if not team_ids_to_scan:
                st.warning("Nessuna partita trovata nel filtro orario. Uso Team 1 + Team 2.")
                team_ids_to_scan = [int(team1_id), int(team2_id)]
            team_ids_to_scan = team_ids_to_scan[:max_teams_today]
        else:
            team_ids_to_scan = [int(team1_id), int(team2_id)]

        candidates = []
        for tid in team_ids_to_scan:
            roster = fetch_team_players(int(tid), SEASON)[:max_players]
            for p in roster:
                pid = p.get("id")
                name = p.get("name")
                if pid and name:
                    candidates.append((name, int(pid), tid))
        # dedup
        seen = set()
        unique_candidates = []
        for n, pid, tid in candidates:
            if pid not in seen:
                seen.add(pid)
                unique_candidates.append((n, pid, tid))

        rows = []
        for n, pid, tid in unique_candidates:
            player_rows = _evaluate_player_value_rows(
                n, pid, linee, odds, n_partite, phase_selected,
                expected_team_id=int(tid),
                bankroll=float(bankroll_for_kelly),
                kelly_frac=float(kelly_fraction),
            )
            team_name = team_label_by_id.get(tid, f"Team {tid}")
            for pr in player_rows:
                pr["Team"] = team_name
                rows.append(pr)

    if not rows:
        st.warning("Nessun alert disponibile: verifica roster/API o allarga i filtri.")
        return

    df_alert = pd.DataFrame(rows)
    df_alert = df_alert[(df_alert["Edge %"] >= min_edge) & (df_alert["Hit Rate %"] >= min_hit)]
    if df_alert.empty:
        st.warning("Nessuna value bet con i filtri correnti. Prova a ridurre le soglie.")
        return
    df_alert = df_alert.sort_values(["Edge %", "Prob Over %"], ascending=False).reset_index(drop=True)

    scope_lbl = "all teams today" if scan_all_today else f"{team1_label} + {team2_label}"
    st.success(f"Trovate {len(df_alert)} opportunità value ({scope_lbl}).")
    if scan_all_today:
        st.caption(f"Filtro orario attivo: {time_mode}")
    st.dataframe(df_alert, width="stretch", hide_index=True)

    top = df_alert.head(5)
    st.markdown("#### 🔥 Top 5 Alert")
    for _, r in top.iterrows():
        st.write(
            f"- **{r['Giocatore']} {r['Stat']} Over {r['Linea']}** · "
            f"Prob {r['Prob Over %']}% · Quota {r['Quota']} · Edge {r['Edge %']}% · "
            f"Kelly €{r.get('Kelly €', 0):.2f} · {r['Signal']}"
        )

    st.download_button(
        "⬇️ Esporta Alert Value (CSV)",
        data=df_to_csv(df_alert),
        file_name=f"alert_value_{datetime.date.today()}.csv",
        mime="text/csv",
    )
    _telegram_alert_block(df_alert, source="Manuale", key_prefix="tg_man", default_top=5)


def _telegram_alert_block(df_alert: pd.DataFrame, source: str = "Manuale",
                          key_prefix: str = "tg", default_top: int = 5):
    """Pannello riutilizzabile per inviare gli alert su Telegram."""
    if df_alert is None or df_alert.empty:
        return
    st.markdown("---")
    st.markdown("#### 📨 Notifica Telegram")
    _tk, _ch = _get_telegram_creds()
    has_creds = bool(_tk and _ch)
    if not has_creds:
        st.caption("Configura il bot in **🩺 Salute Dati → Telegram bot** "
                   "(o variabili env `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`).")
    cols = st.columns([1, 1, 2])
    top_n = cols[0].number_input("Top N", min_value=1, max_value=20,
                                 value=min(default_top, len(df_alert)),
                                 step=1, key=f"{key_prefix}_topn")
    min_edge_tg = cols[1].slider("Edge minimo (%) per Telegram", -5, 30, 4,
                                 key=f"{key_prefix}_min_edge")
    cols[2].caption("I messaggi arrivano in HTML al chat configurato. Usa l'edge per "
                    "filtrare solo le pick di qualità.")

    df_send = df_alert[df_alert["Edge %"] >= min_edge_tg].head(int(top_n))
    if df_send.empty:
        st.info("Nessuna pick supera la soglia di edge selezionata.")
        return

    msg = _format_alerts_for_telegram(df_send, max_rows=int(top_n),
                                      title="🚨 Value Alert NBA",
                                      source=source)
    with st.expander("Anteprima messaggio", expanded=False):
        st.code(msg, language="html")

    if st.button("📨 Invia su Telegram", key=f"{key_prefix}_send",
                 disabled=not has_creds):
        ok, info = send_telegram_message(msg)
        if ok:
            st.success(f"✅ Inviate {len(df_send)} pick su Telegram. {info}")
        else:
            st.error(f"❌ Invio fallito: {info}")


# ══════════════════════════════════════════════════════════════════════════════
#  HEALTH + DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def health_page():
    st.subheader("🩺 Salute Dati")
    st.caption("Diagnostica integrità API/dizionario player.")

    integ = player_integrity_report()
    teams_local = fetch_teams(SEASON)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Player DB locale", integ["players"])
    c2.metric("Anomalie ID", len(integ["collisions"]))
    c3.metric("Team caricati", len(teams_local))
    c4.metric("Stagione", SEASON)
    _tg_tok, _tg_chat = _get_telegram_creds()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("API NBA", "🟢 Configurata" if API_KEY else "🔴 Mancante")
    s2.metric("Odds API", "🟢 Configurata" if ODDS_API_KEY else "🔴 Mancante")
    s3.metric("Telegram", "🟢 Attivo" if (_tg_tok and _tg_chat) else "🔴 Off")
    s4.metric("Versione", VERSION)

    st.markdown("---")
    st.markdown("#### 🧪 Test endpoint API")
    test_cols = st.columns(3)
    if test_cols[0].button("Test /teams"):
        try:
            test_resp = _api_get("/teams", {"season": SEASON})
            st.success(f"/teams OK · status {test_resp.status_code} · "
                       f"{len(test_resp.json().get('response', []))} team")
        except Exception as exc:
            st.error(f"Errore: {exc}")
    if test_cols[1].button("Test /games (oggi)"):
        try:
            today_iso = str(datetime.date.today())
            games = fetch_games_by_date(today_iso)
            st.success(f"/games?date={today_iso} OK · {len(games)} game")
        except Exception as exc:
            st.error(f"Errore: {exc}")
    if test_cols[2].button("Test The Odds API"):
        try:
            evs = fetch_oddsapi_nba_events(ODDS_API_KEY)
            if evs:
                st.success(f"Odds API OK · {len(evs)} eventi NBA")
            else:
                st.warning("Odds API: nessun evento o key non valida.")
        except Exception as exc:
            st.error(f"Errore Odds API: {exc}")

    st.markdown("---")
    st.markdown("#### 🛡 Validatore roster vs API")
    teams_lookup = {t["label"]: t["id"] for t in teams_local}
    if not teams_lookup:
        st.warning("Nessun team disponibile. Fai prima sync da sidebar.")
    else:
        sel = st.selectbox("Squadra da validare", list(teams_lookup.keys()))
        if st.button("Verifica roster"):
            tid = teams_lookup[sel]
            roster = fetch_team_players(int(tid), SEASON)
            df_roster = pd.DataFrame([
                {"ID": p["id"], "Nome": p["name"], "Team ID": p["team_id"]} for p in roster
            ])
            if df_roster.empty:
                st.warning("Roster vuoto dall'API.")
            else:
                st.success(f"Roster OK · {len(df_roster)} giocatori.")
                st.dataframe(df_roster, width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("#### 🧹 Cache")
    cc1, cc2, cc3 = st.columns(3)
    if cc1.button("Pulisci cache dati"):
        try:
            st.cache_data.clear()
            st.success("Cache dati azzerata.")
        except Exception:
            st.warning("Cache non pulita.")
    if cc2.button("Reset team list"):
        try:
            fetch_teams.clear()
            st.success("Lista team ripulita.")
        except Exception:
            st.warning("Niente da ripulire.")
    if cc3.button("Reset The Odds API cache"):
        try:
            fetch_oddsapi_nba_events.clear()
            fetch_oddsapi_event_props.clear()
            st.success("Cache Odds API ripulita.")
        except Exception:
            st.warning("Niente da ripulire.")

    if integ["collisions"]:
        st.markdown("#### ⚠️ Collisioni Player ID")
        coll = pd.DataFrame(
            [{"ID": pid, "Nomi": ", ".join(names)}
             for pid, names in sorted(integ["collisions"].items())]
        )
        st.dataframe(coll, width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("#### 📨 Telegram bot")
    st.caption(
        "Configura il bot per ricevere notifiche delle value alert. "
        "Crea il bot con [@BotFather](https://t.me/BotFather) → ottieni il **token**. "
        "Apri una chat col bot, invia `/start`, poi visita "
        "`https://api.telegram.org/bot<TOKEN>/getUpdates` per leggere il **chat_id**."
    )
    tk_default, ch_default = _get_telegram_creds()
    tg_c1, tg_c2 = st.columns(2)
    new_token = tg_c1.text_input("Bot token", value=tk_default,
                                 type="password", key="tg_token_input")
    new_chat  = tg_c2.text_input("Chat ID", value=ch_default,
                                 key="tg_chat_input")
    save_col, test_col, clear_col = st.columns([1, 1, 1])
    if save_col.button("💾 Salva credenziali (sessione)"):
        st.session_state["tg_token_override"] = new_token.strip()
        st.session_state["tg_chat_override"]  = new_chat.strip()
        st.success("Credenziali salvate per questa sessione.")
    if test_col.button("📨 Invia messaggio test"):
        # usa quelle scritte ora (non solo session_state) per consentire test on-the-fly
        ok, info = send_telegram_message(
            f"✅ <b>NBA Whale Pro</b> · test connessione\n<i>{datetime.datetime.now():%d/%m/%Y %H:%M:%S}</i>",
            bot_token=new_token.strip(),
            chat_id=new_chat.strip(),
        )
        if ok:
            st.success(f"Messaggio test inviato. {info}")
        else:
            st.error(f"Invio fallito: {info}")
    if clear_col.button("🗑️ Cancella credenziali sessione"):
        for k in ("tg_token_override", "tg_chat_override"):
            if k in st.session_state:
                del st.session_state[k]
        st.info("Credenziali rimosse dalla sessione (restano eventuali env-var).")

    tk_active, ch_active = _get_telegram_creds()
    st.caption(
        f"Stato: {'🟢 attivo' if (tk_active and ch_active) else '🔴 non configurato'} · "
        f"Token: {'…' + tk_active[-4:] if tk_active else 'mancante'} · "
        f"Chat: {ch_active or 'mancante'}"
    )

    st.markdown("---")
    st.markdown("#### 📡 Stato configurazione")
    tk_cfg, ch_cfg = _get_telegram_creds()
    cfg = pd.DataFrame([
        {"Parametro": "BASE_URL", "Valore": BASE_URL},
        {"Parametro": "ODDS_API_BASE", "Valore": ODDS_API_BASE},
        {"Parametro": "TELEGRAM_API_BASE", "Valore": TELEGRAM_API_BASE},
        {"Parametro": "Telegram configurato", "Valore": "🟢 sì" if (tk_cfg and ch_cfg) else "🔴 no"},
        {"Parametro": "Bankroll file", "Valore": BANKROLL_FILE},
        {"Parametro": "REQ_TIMEOUT (s)", "Valore": REQ_TIMEOUT},
        {"Parametro": "MAX_RETRIES", "Valore": MAX_RETRIES},
        {"Parametro": "Stagione", "Valore": SEASON},
        {"Parametro": "Versione app", "Valore": VERSION},
    ])
    st.dataframe(cfg, width="stretch", hide_index=True)


def tipster_dashboard_page():
    st.subheader("📈 Dashboard Tipster Pro")
    st.caption("KPI globali sul registro scommesse.")
    init_bankroll()
    bets = st.session_state.get("bets", [])
    if not bets:
        st.info("Nessuna scommessa registrata. Vai a 💰 Bankroll per iniziare.")
        return
    df_bets = pd.DataFrame(bets)
    df_bets["Data"] = pd.to_datetime(df_bets["Data"], errors="coerce")
    chiuse = df_bets[df_bets["Risultato"] != "In attesa"].copy()
    pnl_tot = chiuse["P&L €"].sum() if not chiuse.empty else 0.0
    stake_tot = chiuse["Stake €"].sum() if not chiuse.empty else 0.0
    roi_global = (pnl_tot / stake_tot * 100) if stake_tot > 0 else 0.0
    wr_global = (chiuse["Risultato"] == "Vinto").mean() * 100 if not chiuse.empty else 0.0

    today = pd.Timestamp(datetime.date.today())
    last7 = chiuse[chiuse["Data"] >= today - pd.Timedelta(days=7)]
    last30 = chiuse[chiuse["Data"] >= today - pd.Timedelta(days=30)]
    pnl_7 = last7["P&L €"].sum() if not last7.empty else 0.0
    pnl_30 = last30["P&L €"].sum() if not last30.empty else 0.0
    roi_7 = (pnl_7 / last7["Stake €"].sum() * 100) if not last7.empty and last7["Stake €"].sum() > 0 else 0.0
    roi_30 = (pnl_30 / last30["Stake €"].sum() * 100) if not last30.empty and last30["Stake €"].sum() > 0 else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("ROI globale", f"{roi_global:.1f}%")
    k2.metric("Win Rate", f"{wr_global:.0f}%")
    k3.metric("ROI 7g", f"{roi_7:.1f}%", delta=f"{pnl_7:+.2f} €")
    k4.metric("ROI 30g", f"{roi_30:.1f}%", delta=f"{pnl_30:+.2f} €")
    k5.metric("Bankroll attuale", f"€{(st.session_state.bankroll_start + pnl_tot):.2f}")

    st.markdown("---")
    if not chiuse.empty:
        per_stat = chiuse.groupby("Stat").agg(
            n=("Risultato", "count"),
            wins=("Risultato", lambda s: (s == "Vinto").sum()),
            stake=("Stake €", "sum"),
            pnl=("P&L €", "sum"),
        ).reset_index()
        per_stat["Win%"] = (per_stat["wins"] / per_stat["n"] * 100).round(0)
        per_stat["ROI%"] = (per_stat["pnl"] / per_stat["stake"] * 100).round(1)
        st.markdown("#### Per tipologia")
        st.dataframe(per_stat, width="stretch", hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ABOUT PAGE
# ══════════════════════════════════════════════════════════════════════════════

def _navigate_to(target_page: str):
    """Callback per cambiare la pagina selezionata nel radio della sidebar.
    Va eseguita in un on_click (fra un rerun e l'altro) altrimenti Streamlit
    rifiuta la modifica di una key già usata da un widget."""
    st.session_state["nav_page"] = target_page


def render_line_inputs(expanded: bool = False) -> dict:
    """Mostra in pagina i 3 input per Linea PTS / REB / AST e ritorna `linee`.

    I valori sono persistenti tramite `st.session_state` (chiavi l_pts/l_reb/l_ast)
    e quindi condivisi automaticamente fra tutte le pagine che chiamano questa helper.
    """
    st.session_state.setdefault("l_pts", 22.5)
    st.session_state.setdefault("l_reb", 5.5)
    st.session_state.setdefault("l_ast", 4.5)

    with st.expander("⚙️ Linee Over/Under (modifica le linee del bookmaker)", expanded=expanded):
        st.caption(
            "Imposta qui le linee Over/Under del bookmaker. Tutti i calcoli (Hit Rate, "
            "probabilità Poisson, Z-score, ecc.) usano questi valori."
        )
        c1, c2, c3 = st.columns(3)
        c1.number_input("Punti",    step=0.5, key="l_pts")
        c2.number_input("Rimbalzi", step=0.5, key="l_reb")
        c3.number_input("Assist",   step=0.5, key="l_ast")

    return {
        "PTS": float(st.session_state["l_pts"]),
        "REB": float(st.session_state["l_reb"]),
        "AST": float(st.session_state["l_ast"]),
    }


def home_page():
    """Schermata principale: logo + grid di tutte le funzioni cliccabili."""
    if _ICON_192:
        icon_html = (
            f'<img src="data:image/png;base64,{_ICON_192}" '
            f'style="width:130px;height:130px;border-radius:28px;'
            f'box-shadow:0 8px 30px rgba(0,212,170,0.35);" />'
        )
    else:
        icon_html = '<span style="font-size:6rem;">🐋</span>'

    st.markdown(
        f"""
<div style="text-align:center;padding:24px 0 18px;">
    {icon_html}
    <h1 style="color:#00D4AA;margin:18px 0 4px 0;font-size:2.6rem;letter-spacing:0.5px;">
        NBA Whale Pro
    </h1>
    <p style="color:#E6EDF3;font-size:1.05rem;margin:0;">
        Analisi statistica NBA · Tipster intelligence
    </p>
    <p style="color:#8B949E;font-size:0.85rem;margin:4px 0 0 0;">
        v{VERSION} · Stagione 20{SEASON}-20{int(SEASON)+1} · Dati api-sports.io
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 🚀 Tutte le funzioni")
    st.caption("Clicca una card per aprire la sezione. Le impostazioni (linee, finestre, "
               "squadre) restano sempre nella **sidebar** a sinistra.")

    cards = [
        ("📊", "Analisi Singolo",
         "Studia un giocatore: stat, hit rate, trend per opponent, partite anomale.",
         "📊 Analisi Singolo"),
        ("⚔️", "Confronto Giocatori",
         "Confronta due giocatori metrica per metrica con verdetto vincitore.",
         "⚔️ Confronto"),
        ("🏀", "Confronto Squadre",
         "Compara due squadre: PF/PA, trend, attacco/difesa nei testa a testa.",
         "🏀 Squadre"),
        ("🚨", "Alert Value Giornata",
         "Scanner value-bet OVER con linee/quote reali da The Odds API + Telegram.",
         "🚨 Alert Value"),
        ("🧰", "Toolkit Pro",
         "100+ tool tipster: averages, hit rate, momentum, contesto e injury.",
         "🧰 Toolkit Pro"),
        ("📈", "Dashboard Tipster",
         "KPI globali e per periodo: ROI, win rate, P&L, drawdown.",
         "📈 Tipster Pro"),
        ("💰", "Bankroll Tracker",
         "Registra scommesse, monitora P&L, import/export CSV con persistenza.",
         "💰 Bankroll"),
        ("🩺", "Salute Dati",
         "Diagnostica API, validatore roster, gestione cache e bot Telegram.",
         "🩺 Salute Dati"),
        ("ℹ️", "Guida",
         "Documentazione, legenda acronimi e best practice di betting.",
         "ℹ️ Guida"),
    ]

    cols_per_row = 3
    for i in range(0, len(cards), cols_per_row):
        chunk = cards[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, (emoji, title, desc, target_page) in zip(cols, chunk):
            with col:
                st.markdown(
                    f"""
<div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
            padding:18px 16px 14px 16px;margin-bottom:10px;height:170px;
            display:flex;flex-direction:column;justify-content:flex-start;">
    <div style="font-size:2.2rem;line-height:1;margin-bottom:8px;">{emoji}</div>
    <div style="font-weight:600;color:#E6EDF3;font-size:1.02rem;margin-bottom:6px;">{title}</div>
    <div style="color:#8B949E;font-size:0.82rem;line-height:1.35;">{desc}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
                st.button(
                    "Apri →",
                    key=f"home_btn_{target_page}",
                    width="stretch",
                    on_click=_navigate_to,
                    args=(target_page,),
                )

    st.markdown("---")
    # Stato configurazione veloce
    _tk, _ch = _get_telegram_creds()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("API NBA",  "🟢 OK" if API_KEY else "🔴 Mancante")
    s2.metric("Odds API", "🟢 OK" if ODDS_API_KEY else "🔴 Off")
    s3.metric("Telegram", "🟢 OK" if (_tk and _ch) else "⚪ Off")
    bets_n = len(st.session_state.get("bets", []))
    s4.metric("Scommesse registrate", bets_n)
    st.caption("⚠️ NBA Whale Pro è uno strumento di analisi statistica. "
               "Non costituisce consulenza finanziaria. Gioca responsabilmente.")


def about_page():
    st.subheader("ℹ️ NBA Whale Pro — Guida & Metodologia")
    st.markdown(f"""
**Versione:** {VERSION} &nbsp;·&nbsp; **Stagione:** 20{SEASON}-20{int(SEASON)+1}
&nbsp;·&nbsp; **Fonte dati:** api-sports.io (NBA API v2)

---
#### 🔍 Come cercare un giocatore
Digita **nome, cognome o soprannome** nella barra di ricerca. Esempi funzionanti:
- `LeBron` · `lebron` · `bron` · `king james`
- `Curry` · `steph` · `Stephen Curry`
- `Jokic` · `Nikola Jokic`
- `SGA` · `shai` · `Shai Gilgeous-Alexander`
- `Giannis` · `Anthony Edwards` · `ant`

---
#### 🎯 Come funziona il Verdetto Scommessa

| Fattore | Peso | Descrizione |
|---|---|---|
| Distribuzione di Poisson | 40% | Probabilità matematica di superare la linea |
| Hit Rate storico | 40% | % partite in cui il giocatore ha superato la linea |
| Forma recente | 20% | Media ultimi 3 match vs media del periodo |

| Score | Verdetto |
|---|---|
| ≥ 68 | ✅ BET OVER |
| 57–67 | ⚡ OVER PROBABILE |
| 43–56 | ⚠️ SKIP |
| 32–42 | 🔻 UNDER PROBABILE |
| < 32  | ❌ BET UNDER |

---
#### 🔄 Contropronostici
Confronta media stagionale vs ultimi N match per rilevare slump e rimbalzi attesi.

---
#### ⚠️ Disclaimer
NBA Whale Pro è uno strumento di analisi statistica a scopo informativo.
Non costituisce consulenza finanziaria. Il gioco d'azzardo può causare dipendenza.

---
#### 📚 Legenda acronimi principali
- `PTS`: punti segnati
- `REB`: rimbalzi
- `AST`: assist
- `STL`: palle rubate
- `BLK`: stoppate
- `TOV`: palle perse
- `MIN`: minuti giocati
- `LOC`: casa/trasferta
- `PHASE`: fase della stagione
- `PF` / `PA`: punti fatti / punti subiti (sezione squadre)
""")


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR + ROUTING
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        '<div class="sb-card" style="text-align:center;">'
        '<span style="font-size:1.9rem;">🐋</span><br>'
        f'<strong style="color:#00D4AA;font-size:1.06rem;">NBA Whale Pro</strong>'
        f'<span class="badge">v{VERSION}</span><br>'
        f'<span class="sb-sub">Stagione 20{SEASON}-20{int(SEASON)+1}</span>'
        '</div>', unsafe_allow_html=True)

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "🏠 Home"

    st.markdown('<div class="sb-title">Menu principale</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.button("🏠 Home", on_click=_navigate_to, args=("🏠 Home",))
    m2.button("📊 Analisi", on_click=_navigate_to, args=("📊 Analisi Singolo",))
    m3, m4 = st.columns(2)
    m3.button("🚨 Alert", on_click=_navigate_to, args=("🚨 Alert Value",))
    m4.button("💰 Bankroll", on_click=_navigate_to, args=("💰 Bankroll",))

    with st.expander("🧩 Avanzate", expanded=False):
        extra = st.selectbox(
            "Apri sezione",
            ["—", "⚔️ Confronto", "🏀 Squadre", "🧰 Toolkit Pro", "📈 Tipster Pro", "🩺 Salute Dati", "ℹ️ Guida"],
            index=0,
            key="nav_extra_select",
        )
        if extra != "—":
            st.session_state["nav_page"] = extra
    pagina = st.session_state.get("nav_page", "🏠 Home")
    st.markdown("---")

    with st.expander("🏁 Contesto partite", expanded=True):
        phase_type = st.selectbox(
            "Competizione",
            ["Tutte", "Regular Season", "Play-In", "Playoff"],
            index=0,
            key="phase_type",
        )

    st.session_state.setdefault("l_pts", 22.5)
    st.session_state.setdefault("l_reb", 5.5)
    st.session_state.setdefault("l_ast", 4.5)
    linee = {
        "PTS": float(st.session_state["l_pts"]),
        "REB": float(st.session_state["l_reb"]),
        "AST": float(st.session_state["l_ast"]),
    }

    with st.expander("📅 Finestre analisi", expanded=True):
        n_partite = st.slider("Ultime gare",    5, 20, 10, key="n_gare")
        n_slump   = st.slider("Finestra slump", 3, 10,  5, key="n_slump")
        st.checkbox("Usa tutte le partite giocate", value=False, key="use_all_games")
    st.markdown("---")

    chip = '<span class="sb-chip sb-chip-ok">OK</span>' if API_KEY else '<span class="sb-chip sb-chip-off">Mancante</span>'
    st.markdown(
        f'<div class="sb-card"><div class="sb-title">Stato connessione</div>'
        f'<div class="sb-sub">API SPORTS {chip}</div></div>',
        unsafe_allow_html=True
    )
    with st.expander("📚 Legenda acronimi"):
        st.caption("PTS punti · REB rimbalzi · AST assist · STL rubate · BLK stoppate · TOV perse · MIN minuti · PF/PA punti fatti/subiti")
    integ = player_integrity_report()
    if integ["collisions"]:
        st.caption(f"⚠️ Anomalie DB player ID: {len(integ['collisions'])}")
        with st.expander("Dettaglio anomalie player ID"):
            for pid, names in sorted(integ["collisions"].items()):
                st.write(f"ID {pid}: {', '.join(names)}")
    st.caption("⚠️ Non è consulenza finanziaria.")

if not API_KEY and pagina not in ("🏠 Home", "ℹ️ Guida"):
    st.error("⚠️ Chiave api-sports.io non configurata. "
             "Imposta la variabile d'ambiente **API_SPORTS_KEY** "
             "(o aggiungi il segreto in Streamlit Cloud → Settings → Secrets).")
    st.stop()

if   pagina == "🏠 Home":            home_page()
elif pagina == "📊 Analisi Singolo": single_player_page(linee, n_partite, n_slump)
elif pagina == "⚔️ Confronto":       comparison_page(linee, n_partite, n_slump)
elif pagina == "🏀 Squadre":         team_stats_page(n_partite)
elif pagina == "🚨 Alert Value":     value_alerts_page(linee, n_partite)
elif pagina == "🧰 Toolkit Pro":     toolkit_pro_page(linee, n_partite)
elif pagina == "📈 Tipster Pro":     tipster_dashboard_page()
elif pagina == "🩺 Salute Dati":     health_page()
elif pagina == "💰 Bankroll":        bankroll_page()
elif pagina == "ℹ️ Guida":           about_page()

st.markdown(
    f'<div class="disclaimer">'
    f'NBA Whale Pro v{VERSION} · Stagione 20{SEASON}-20{int(SEASON)+1} · '
    f'Dati: api-sports.io · Gioca responsabilmente · Non è consulenza finanziaria'
    f'</div>', unsafe_allow_html=True)

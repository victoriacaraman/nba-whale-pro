import os
import io
import datetime
import difflib
import math
import re
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from scipy.stats import poisson

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="NBA Whale Pro", layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"About": "NBA Whale Pro · analisi statistica NBA"})

# ── PWA / Mobile (manifest inline + meta) ──────────────────────────────────
def _load_icon_b64(path: str):
    try:
        import base64
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return ""

_ICON_192 = _load_icon_b64(os.path.join(os.path.dirname(__file__), "icon-192.png")) if "__file__" in globals() else _load_icon_b64("icon-192.png")
_ICON_512 = _load_icon_b64(os.path.join(os.path.dirname(__file__), "icon-512.png")) if "__file__" in globals() else _load_icon_b64("icon-512.png")

_icon_entries = []
if _ICON_192:
    _icon_entries.append('{"src":"data:image/png;base64,' + _ICON_192 + '","sizes":"192x192","type":"image/png","purpose":"any maskable"}')
if _ICON_512:
    _icon_entries.append('{"src":"data:image/png;base64,' + _ICON_512 + '","sizes":"512x512","type":"image/png","purpose":"any maskable"}')

_PWA_MANIFEST = (
    '{'
    '"name":"NBA Whale Pro",'
    '"short_name":"NBA Whale",'
    '"start_url":".",'
    '"display":"standalone",'
    '"orientation":"portrait",'
    '"background_color":"#0E1117",'
    '"theme_color":"#00D4AA",'
    f'"icons":[{",".join(_icon_entries)}]'
    '}'
)

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

API_KEY     = os.environ.get("API_SPORTS_KEY", "d8c21a4004e1999c362481a3abb16260")
BASE_URL    = "https://v2.nba.api-sports.io"
SEASON      = "2025"
STAT_LABELS = {"PTS": "Punti", "REB": "Rimbalzi", "AST": "Assist"}
STAT_COLORS = {"PTS": "#00D4AA", "REB": "#3B9EFF", "AST": "#FF9F40"}
VERSION     = "3.0"
REQ_TIMEOUT = 15
MAX_RETRIES = 3
EPLAY24_BASE_URL = "https://www.eplay24.com"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "d0610cb7c6f61f3424a82d4d2e56c4e3")

st.markdown("""
<style>
:root {
    --bg:#0E1117;--card:#161B22;--border:#30363D;
    --accent:#00D4AA;--danger:#FF5252;--warn:#FFD600;
    --text:#E6EDF3;--muted:#8B949E;
}
html,body,[class*="css"]{background-color:var(--bg);color:var(--text);font-family:'Inter',sans-serif;}
section[data-testid="stSidebar"]{background-color:#0D1117;border-right:1px solid var(--border);}
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


@st.cache_data(ttl=21600)
def fetch_teams(season: str):
    teams_map = {}

    def _add_team(tid, name, code):
        if not tid or not name:
            return
        label = f"{name} ({code})" if code else str(name)
        teams_map[int(tid)] = {"id": int(tid), "name": str(name), "label": label}

    # Tentativo 1: endpoint teams con season
    try:
        r = _api_get("/teams", {"season": season})
        for t in r.json().get("response", []):
            _add_team(t.get("id"), t.get("name"), t.get("code") or "")
    except Exception:
        pass

    # Tentativo 2: endpoint teams senza season (alcuni piani/API lo richiedono)
    if len(teams_map) < 2:
        try:
            r = _api_get("/teams", {})
            for t in r.json().get("response", []):
                _add_team(t.get("id"), t.get("name"), t.get("code") or "")
        except Exception:
            pass

    # Tentativo 3 (fallback forte): ricava team da games della season
    if len(teams_map) < 2:
        try:
            r = _api_get("/games", {"season": season})
            for g in r.json().get("response", []):
                tm = g.get("teams", {}) or {}
                home = tm.get("home", {}) or {}
                vis = tm.get("visitors", {}) or {}
                _add_team(home.get("id"), home.get("name") or home.get("nickname"), home.get("code") or "")
                _add_team(vis.get("id"), vis.get("name") or vis.get("nickname"), vis.get("code") or "")
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
    v1.metric("Score",    f"{score:.0f}/100")
    v2.metric("Poisson",  f"{prob:.1f}%")
    v3.metric("Hit Rate", f"{hit:.0f}%")
    v4.metric("Forma",    f"{form:.0f}/100")

    st.markdown(
        f'<div class="verdict-box {css_class}">'
        f'{emo} <strong>{lbl}</strong> — Linea {linea} {stat_lbl}<br>'
        f'<span style="font-size:0.85rem;color:#8B949E">{desc}</span>'
        f'</div>', unsafe_allow_html=True)

    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={"text": f"Segnale {stat_lbl}", "font": {"size": 13}},
        number={"font": {"size": 26}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"size": 10}},
            "bar":  {"color": bar_color, "thickness": 0.25},
            "steps": [
                {"range": [0,  32], "color": "#2d0000"},
                {"range": [32, 43], "color": "#4a1a1a"},
                {"range": [43, 57], "color": "#2d2d00"},
                {"range": [57, 68], "color": "#0d3320"},
                {"range": [68,100], "color": "#062218"},
            ],
            "threshold": {"line": {"color": "white", "width": 2}, "value": 57},
        }
    ))
    fig.update_layout(height=220, template="plotly_dark",
                      margin=dict(t=36, b=4, l=8, r=8))
    st.plotly_chart(fig, width="stretch")
    st.caption("Score = 40% Poisson + 40% Hit Rate + 20% Forma. Non è consulenza finanziaria.")


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


def build_extra_10_tools(df_r: pd.DataFrame, df_all: pd.DataFrame, linee: dict):
    avg_pts = float(df_r["PTS"].mean()) if "PTS" in df_r.columns and not df_r.empty else 0.0
    extra = [
        ("E1", "Delta recente-stagionale PTS", _recent_vs_season_delta(df_r, df_all, "PTS")),
        ("E2", "Delta recente-stagionale REB", _recent_vs_season_delta(df_r, df_all, "REB")),
        ("E3", "Delta recente-stagionale AST", _recent_vs_season_delta(df_r, df_all, "AST")),
        ("E4", "Consistency Index PTS", _consistency_index(df_r, "PTS")),
        ("E5", "Ceiling Rate PTS %", _ceiling_rate(df_r, "PTS")),
        ("E6", "Floor Rate PTS %", _floor_rate(df_r, "PTS")),
        ("E7", "Momentum Index PTS", _momentum_index(df_r, "PTS")),
        ("E8", "Pressure Index (da TOV)", _pressure_index(df_r)),
        ("E9", "Two-Way Impact (STL+BLK-TOV)", _two_way_impact(df_r)),
        ("E10", "Line Gap PTS (media-linea)", _line_gap(avg_pts, linee.get("PTS", 0))),
    ]
    return pd.DataFrame(extra, columns=["#", "Tool", "Valore"])


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


def toolkit_pro_page(linee: dict, n_partite: int):
    st.subheader("🧰 Toolkit Tipster Pro")
    st.caption("Toolkit base (40) + toolkit contesto avanzato (50).")
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
    t_base, t_ctx, t_adv = st.tabs(["Toolkit Base (40)", "Toolkit Contesto (50)", "Toolkit Avanzato (20)"])
    with t_base:
        tools_df = build_40_tools(name, df_all, df_r, linee)
        st.dataframe(tools_df, width="stretch", hide_index=True)
        score_core = (
            float(tools_df.loc[tools_df["#"] == "13", "Valore"].iloc[0]) * 0.25
            + float(tools_df.loc[tools_df["#"] == "10", "Valore"].iloc[0]) * 0.25
            + max(0.0, float(tools_df.loc[tools_df["#"] == "40", "Valore"].iloc[0])) * 0.25
            + max(0.0, min(100.0, 50 + float(tools_df.loc[tools_df["#"] == "16", "Valore"].iloc[0]) * 5)) * 0.25
        )
        st.metric("Indice Pro Complessivo", f"{score_core:.1f}/100")
        st.download_button(
            "⬇️ Esporta Toolkit Base (CSV)",
            data=df_to_csv(tools_df),
            file_name=f"{name.replace(' ', '_')}_toolkit_base.csv",
            mime="text/csv",
        )

    with t_ctx:
        st.markdown("#### Input contesto partita")
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
                st.caption("Injury auto-detected da team selezionati in sidebar.")
                with st.expander("Dettaglio injury auto (beta)"):
                    st.write("Team selezionato:")
                    for note in auto_summary["team_notes"][:6]:
                        st.write(f"- {note}")
                    st.write("Avversario selezionato:")
                    for note in auto_summary["opp_notes"][:6]:
                        st.write(f"- {note}")
            else:
                st.caption("Per auto-injury, seleziona Team 1 e Team 2 in sidebar.")

        c1, c2, c3 = st.columns(3)
        teammate_out_count = c1.number_input(
            "Compagni OUT",
            min_value=0, max_value=12,
            value=int(auto_summary.get("teammate_out_count", 1)),
            step=1
        )
        opp_out_count = c2.number_input(
            "Avversari OUT",
            min_value=0, max_value=12,
            value=int(auto_summary.get("opp_out_count", 1)),
            step=1
        )
        b2b_flag = c3.checkbox("Back-to-back", value=False)
        c4, c5, c6 = st.columns(3)
        teammate_usage_loss = c4.slider(
            "Usage perso compagni %",
            0, 60, int(round(auto_summary.get("teammate_usage_loss", 12)))
        )
        opp_def_weakness = c5.slider(
            "Debolezza difesa avv. %",
            0, 60, int(round(auto_summary.get("opp_def_weakness", 10)))
        )
        expected_min_delta = c6.slider(
            "Delta minuti atteso",
            -8, 12, int(round(auto_summary.get("expected_min_delta", 2)))
        )
        market_odds = st.number_input("Quota mercato (es. 1.90)", min_value=1.01, value=1.90, step=0.01)
        st.caption("Inserisci assenze/contesto manualmente: il modello applica adjustment euristico.")

        ctx_df = build_50_context_tools(
            name=name,
            df_all=df_all,
            df_r=df_r,
            linee=linee,
            teammate_out_count=int(teammate_out_count),
            opp_out_count=int(opp_out_count),
            teammate_usage_loss=float(teammate_usage_loss),
            opp_def_weakness=float(opp_def_weakness),
            expected_min_delta=float(expected_min_delta),
            b2b_flag=bool(b2b_flag),
        )
        st.dataframe(ctx_df, width="stretch", hide_index=True)

        prob_adj_pts = float(ctx_df.loc[ctx_df["#"] == "22", "Valore"].iloc[0])
        implied_prob = 100 / market_odds if market_odds > 1 else 0.0
        edge = prob_adj_pts - implied_prob
        fair_odds = 100 / max(prob_adj_pts, 0.1)
        if edge >= 7:
            st.success(f"🟢 VALUE BET FORTE (PTS): edge +{edge:.1f}pp · fair odds ~ {fair_odds:.2f}")
        elif edge >= 3:
            st.info(f"🔵 VALUE BET MODERATA (PTS): edge +{edge:.1f}pp · fair odds ~ {fair_odds:.2f}")
        elif edge <= -7:
            st.error(f"🔴 NO BET (PTS): edge {edge:.1f}pp · quota non favorevole")
        else:
            st.warning(f"🟡 EDGE LIMITATA (PTS): edge {edge:.1f}pp")

        st.download_button(
            "⬇️ Esporta Toolkit Contesto (50) CSV",
            data=df_to_csv(ctx_df),
            file_name=f"{name.replace(' ', '_')}_toolkit_contesto_50.csv",
            mime="text/csv",
        )

    with t_adv:
        adv_df = build_advanced_20_tools(df_all, df_r, linee)
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

def init_bankroll():
    if "bankroll_start" not in st.session_state:
        st.session_state.bankroll_start = 1000.0
    if "bets" not in st.session_state:
        st.session_state.bets = []


def bankroll_page():
    init_bankroll()
    st.subheader("💰 Tracker Bankroll")
    st.caption("Registra le scommesse e monitora P&L, ROI e win rate in tempo reale.")

    with st.expander("⚙️ Bankroll iniziale", expanded=len(st.session_state.bets) == 0):
        new_start = st.number_input("Bankroll iniziale (€)",
                                    value=st.session_state.bankroll_start,
                                    min_value=1.0, step=50.0)
        if st.button("Aggiorna bankroll"):
            st.session_state.bankroll_start = new_start
            st.rerun()

    st.markdown("#### ➕ Registra Scommessa")
    with st.form("add_bet"):
        b1, b2, b3 = st.columns(3)
        giocatore = b1.text_input("Giocatore")
        stat_bet  = b2.selectbox("Stat", ["Punti", "Rimbalzi", "Assist"])
        esito     = b3.selectbox("Tipo", ["Over", "Under"])
        c1, c2, c3, c4 = st.columns(4)
        linea_b = c1.number_input("Linea", value=20.0, step=0.5)
        quota   = c2.number_input("Quota", value=1.90, step=0.05, min_value=1.01)
        stake   = c3.number_input("Stake (€)", value=20.0, step=5.0, min_value=1.0)
        vinto   = c4.selectbox("Risultato", ["In attesa", "Vinto", "Perso"])
        note    = st.text_input("Note (opzionale)")
        if st.form_submit_button("Aggiungi") and giocatore:
            profit = (round(stake * (quota - 1), 2) if vinto == "Vinto"
                      else (-stake if vinto == "Perso" else 0.0))
            st.session_state.bets.append({
                "Data": str(datetime.date.today()), "Giocatore": giocatore,
                "Stat": stat_bet, "Tipo": esito, "Linea": linea_b,
                "Quota": quota, "Stake €": stake, "Risultato": vinto,
                "P&L €": profit, "Note": note,
            })
            st.success(f"✅ Scommessa su {giocatore} registrata!")
            st.rerun()

    if not st.session_state.bets:
        st.info("Nessuna scommessa ancora. Usare il form sopra per iniziare.")
        return

    df_bets = pd.DataFrame(st.session_state.bets)
    chiuse  = df_bets[df_bets["Risultato"] != "In attesa"]
    pnl_tot  = chiuse["P&L €"].sum()     if not chiuse.empty else 0.0
    stake_tot= chiuse["Stake €"].sum()   if not chiuse.empty else 0.0
    roi      = (pnl_tot / stake_tot * 100) if stake_tot > 0 else 0.0
    bankroll = st.session_state.bankroll_start + pnl_tot
    vinte    = len(chiuse[chiuse["Risultato"] == "Vinto"])
    wr       = (vinte / len(chiuse) * 100) if len(chiuse) > 0 else 0.0

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Bankroll Attuale", f"€{bankroll:.2f}", delta=f"{pnl_tot:+.2f}")
    s2.metric("P&L Totale",      f"€{pnl_tot:.2f}")
    s3.metric("ROI",              f"{roi:.1f}%")
    s4.metric("Win Rate",         f"{wr:.0f}%")
    s5.metric("Scommesse totali", len(df_bets))
    st.markdown("---")

    if not chiuse.empty:
        chiuse_s = chiuse.copy()
        chiuse_s["Bankroll"] = st.session_state.bankroll_start + chiuse_s["P&L €"].cumsum()
        fig_bk = go.Figure()
        fig_bk.add_trace(go.Scatter(
            x=list(range(1, len(chiuse_s) + 1)), y=chiuse_s["Bankroll"],
            mode="lines+markers", line=dict(color="#00D4AA", width=2),
            fill="tozeroy", fillcolor="rgba(0,212,170,0.08)", name="Bankroll"))
        fig_bk.add_hline(y=st.session_state.bankroll_start, line_dash="dash",
                         line_color="#8B949E", annotation_text="Bankroll iniziale")
        fig_bk.update_layout(height=300, template="plotly_dark",
                             xaxis_title="Scommessa #", yaxis_title="€")
        st.plotly_chart(fig_bk, width="stretch")

    st.markdown("#### 📄 Storico")
    st.dataframe(df_bets, width="stretch", hide_index=True)
    col_del, col_exp = st.columns([1, 3])
    with col_del:
        if st.button("🗑️ Cancella tutto"):
            st.session_state.bets = []
            st.rerun()
    with col_exp:
        st.download_button("⬇️ Esporta CSV Scommesse", data=df_to_csv(df_bets),
                           file_name=f"bankroll_{datetime.date.today()}.csv",
                           mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  SINGLE PLAYER PAGE
# ══════════════════════════════════════════════════════════════════════════════

def single_player_page(linee: dict, n_partite: int, n_slump: int):
    use_sidebar_player = st.session_state.get("use_sidebar_player_sync", False)
    if use_sidebar_player and st.session_state.get("sidebar_player_pick"):
        st.session_state["sp_input"] = st.session_state["sidebar_player_pick"]
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

    st.subheader("📈 Andamento Prestazioni")
    tg1, tg2, tg3 = st.tabs(["Punti", "Rimbalzi", "Assist"])
    for tab, col, linea, color in [
        (tg1, "PTS", linee["PTS"], "#00D4AA"),
        (tg2, "REB", linee["REB"], "#3B9EFF"),
        (tg3, "AST", linee["AST"], "#FF9F40"),
    ]:
        with tab:
            if col in df_r.columns:
                avg_v = df_r[col].mean()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_r["GAME_DATE"], y=df_r[col],
                                         mode="lines+markers",
                                         line=dict(color=color, width=2.5),
                                         marker=dict(size=7),
                                         name=STAT_LABELS[col]))
                fig.add_hline(y=linea, line_dash="dash", line_color="#FF5252",
                              annotation_text=f"Linea {linea}")
                fig.add_hline(y=avg_v,  line_dash="dot",  line_color="#FFD600",
                              annotation_text=f"Media {avg_v:.1f}")
                fig.update_layout(height=360, template="plotly_dark",
                                  xaxis_title="Data", yaxis_title=STAT_LABELS[col])
                st.plotly_chart(fig, width="stretch")
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
    st.subheader("🧠 Extra 10 Tool")
    extra_df = build_extra_10_tools(df_r, df_all, linee)
    st.dataframe(extra_df, width="stretch", hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  COMPARISON PAGE
# ══════════════════════════════════════════════════════════════════════════════

def comparison_page(linee: dict, n_partite: int, n_slump: int):
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

    st.subheader("📈 Trend Diretto")
    gt1, gt2, gt3 = st.tabs(["Punti","Rimbalzi","Assist"])
    for tab, col, linea in [(gt1,"PTS",linee["PTS"]),(gt2,"REB",linee["REB"]),(gt3,"AST",linee["AST"])]:
        with tab:
            fig = go.Figure()
            for df_x, nm, cx in [(df1,n1,C1),(df2,n2,C2)]:
                if col in df_x.columns:
                    fig.add_trace(go.Scatter(x=df_x["GAME_DATE"], y=df_x[col],
                                             mode="lines+markers", name=nm,
                                             line=dict(color=cx, width=2.5),
                                             marker=dict(size=7)))
            fig.add_hline(y=linea, line_dash="dash", line_color="white",
                          annotation_text=f"Linea {linea}")
            fig.update_layout(height=360, template="plotly_dark",
                              xaxis_title="Data", yaxis_title=STAT_LABELS.get(col, col),
                              legend=dict(orientation="h", y=1.12))
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

    st.subheader("📋 Riepilogo Statistico")
    summary = pd.DataFrame({
        "Statistica": ["Media PTS","Prob. Over PTS %","Hit Rate PTS %",
                       "Media REB","Prob. Over REB %","Media AST","Prob. Over AST %",
                       "Max PTS","Min PTS"],
        n1: [f"{avg1_pts:.1f}", f"{prob1_pts:.1f}%", f"{hit1_pts:.0f}%",
             f"{avg1_reb:.1f}", f"{prob1_reb:.1f}%", f"{avg1_ast:.1f}", f"{prob1_ast:.1f}%",
             f"{df1['PTS'].max():.0f}" if "PTS" in df1.columns else "—",
             f"{df1['PTS'].min():.0f}" if "PTS" in df1.columns else "—"],
        n2: [f"{avg2_pts:.1f}", f"{prob2_pts:.1f}%", f"{hit2_pts:.0f}%",
             f"{avg2_reb:.1f}", f"{prob2_reb:.1f}%", f"{avg2_ast:.1f}", f"{prob2_ast:.1f}%",
             f"{df2['PTS'].max():.0f}" if "PTS" in df2.columns else "—",
             f"{df2['PTS'].min():.0f}" if "PTS" in df2.columns else "—"],
    })
    st.dataframe(summary, width="stretch", hide_index=True)


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
            home_score = _safe_float((scores.get("home") or {}).get("points"))
            vis_score = _safe_float((scores.get("visitors") or {}).get("points"))
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
            is_home = team_id == home.get("id")
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
            home_id = home.get("id")
            vis_id = vis.get("id")
            if {home_id, vis_id} != {team1_id, team2_id}:
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

            home_score = _safe_float((scores.get("home") or {}).get("points"))
            vis_score = _safe_float((scores.get("visitors") or {}).get("points"))
            date = ((g.get("date", {}) or {}).get("start", "") or "")[:10]

            if home_id == team1_id:
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
def fetch_oddsapi_event_props(api_key: str, event_id: str, regions: str = "us,eu,uk"):
    """
    Restituisce dict con linee/quote per player_points, player_rebounds, player_assists.
    Formato: { player_name: { 'PTS': {'line': X, 'over_odds': Y, 'under_odds': Z}, ... } }
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
    props = {}
    for bookmaker in payload.get("bookmakers", []) or []:
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
                slot = props.setdefault(player, {}).setdefault(stat_col, {
                    "line": float(line_val),
                    "over_odds": None,
                    "under_odds": None,
                    "bookmaker": bookmaker.get("title", ""),
                })
                if "over" in side:
                    if slot["over_odds"] is None or float(price) > slot["over_odds"]:
                        slot["over_odds"] = float(price)
                        slot["line"] = float(line_val)
                        slot["bookmaker"] = bookmaker.get("title", "")
                elif "under" in side:
                    if slot["under_odds"] is None or float(price) > slot["under_odds"]:
                        slot["under_odds"] = float(price)
                        slot["line"] = float(line_val)
                        slot["bookmaker"] = bookmaker.get("title", "")
    return props


def _normalize_player_key(name: str) -> str:
    s = (name or "").lower().strip()
    s = s.replace(".", "").replace("'", "").replace("-", " ")
    return " ".join(s.split())


def _match_player_props(target_name: str, props_dict: dict):
    target_key = _normalize_player_key(target_name)
    if target_key in {_normalize_player_key(k): k for k in props_dict.keys()}:
        # exact match
        for k in props_dict.keys():
            if _normalize_player_key(k) == target_key:
                return props_dict[k], k
    # partial fallback (cognome)
    last = target_key.split()[-1] if target_key else ""
    if last:
        for k in props_dict.keys():
            if last in _normalize_player_key(k):
                return props_dict[k], k
    return None, None


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


def teams_comparison_page(n_partite: int):
    st.subheader("🏀 Confronto Squadre")
    team1_id = st.session_state.get("team_1_id")
    team2_id = st.session_state.get("team_2_id")
    team1_label = st.session_state.get("team_1_label", "Team 1")
    team2_label = st.session_state.get("team_2_label", "Team 2")
    phase_selected = st.session_state.get("phase_type", "Tutte")

    if not team1_id or not team2_id:
        st.info("Seleziona due squadre dalla sidebar per avviare il confronto.")
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
    st.caption(f"Filtro partite: {phase_selected} · Ultime {n_partite} gare")

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


def _kelly_stake(prob_pct: float, odd: float, bankroll: float, fraction: float = 1.0) -> float:
    if odd <= 1 or prob_pct <= 0 or bankroll <= 0:
        return 0.0
    p = max(0.0, min(1.0, prob_pct / 100.0))
    b = odd - 1.0
    kelly = (b * p - (1 - p)) / b
    if kelly <= 0:
        return 0.0
    return round(bankroll * kelly * max(0.0, min(1.0, fraction)), 2)


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


def _scan_value_with_real_odds(api_key: str, n_partite: int, phase_selected: str, bankroll: float, kelly_frac: float, min_edge: float, min_hit: float, time_mode: str):
    """
    Modalità AUTO con linee/quote reali da The Odds API.
    """
    events = fetch_oddsapi_nba_events(api_key)
    if not events:
        return None, "Nessun evento NBA disponibile (verifica API key The Odds API)."

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
        return None, "Nessun evento NBA nel filtro orario richiesto."

    # mappa team API->roster locale
    teams_local = {t["id"]: t for t in fetch_teams(SEASON)}
    name_to_local_team = {}
    for t in teams_local.values():
        name_to_local_team[t["name"].lower()] = t

    rows = []
    debug_info = []
    for ev, ev_dt in filtered_events:
        event_id = ev.get("id")
        home_name = ev.get("home_team", "")
        away_name = ev.get("away_team", "")
        props = fetch_oddsapi_event_props(api_key, event_id)
        if not props:
            debug_info.append(f"{home_name} vs {away_name}: nessuna prop disponibile")
            continue

        # roster di entrambe le squadre dal nostro provider
        roster_players = []
        for tname in [home_name, away_name]:
            local_t = name_to_local_team.get(tname.lower())
            if not local_t:
                # match parziale (Lakers, Celtics ecc.)
                for cand in teams_local.values():
                    if tname.lower().split()[-1] in cand["name"].lower():
                        local_t = cand
                        break
            if local_t:
                roster_players.extend(fetch_team_players(int(local_t["id"]), SEASON))

        for p in roster_players:
            pid = p.get("id")
            pname = p.get("name")
            if not pid or not pname:
                continue
            matched_props, matched_key = _match_player_props(pname, props)
            if not matched_props:
                continue
            df_all = get_nba_data(int(pid), pname, SEASON, API_KEY, phase_selected)
            if isinstance(df_all, str) or df_all is None or df_all.empty:
                continue
            n_eff = len(df_all) if st.session_state.get("use_all_games", False) else n_partite
            df_r = df_all.head(max(1, n_eff)).copy()

            for stat_col, info in matched_props.items():
                line_val = float(info.get("line", 0))
                over_odd = info.get("over_odds")
                under_odd = info.get("under_odds")
                if stat_col not in df_r.columns or line_val <= 0:
                    continue
                avg = float(df_r[stat_col].mean())
                hit = float((df_r[stat_col] > line_val).mean() * 100)
                prob = float((1 - poisson.cdf(line_val, avg)) * 100 if avg > 0 else 0.0)

                # OVER only (Eplay24 supporta solo Over per player props)
                if over_odd:
                    implied = 100 / over_odd
                    edge = prob - implied
                    rows.append({
                        "Giocatore": pname,
                        "Stat": stat_col,
                        "Linea": line_val,
                        "Quota Over": round(float(over_odd), 2),
                        "Bookmaker": info.get("bookmaker", ""),
                        "Media": round(avg, 2),
                        "Prob Over %": round(prob, 1),
                        "Implied %": round(implied, 1),
                        "Edge %": round(edge, 1),
                        "Hit Rate %": round(hit, 1),
                        "Kelly €": _kelly_stake(prob, float(over_odd), bankroll, kelly_frac),
                        "Signal": _value_label(edge),
                        "Match": f"{away_name} @ {home_name}",
                    })

    if not rows:
        return None, "Nessuna prop incrociabile coi roster (prova ad aumentare le partite o a cambiare filtri)."

    df = pd.DataFrame(rows)
    df = df[(df["Edge %"] >= min_edge) & (df["Hit Rate %"] >= min_hit)]
    if df.empty:
        return None, "Nessuna value bet con i filtri correnti."
    df = df.sort_values(["Edge %", "Prob Over %"], ascending=False).reset_index(drop=True)
    return df, None


def value_alerts_page(linee: dict, n_partite: int):
    st.subheader("🚨 Alert Value Giornata")
    st.caption("Scanner value-bet con linee/quote reali da The Odds API + fallback manuale.")

    team1_id = st.session_state.get("team_1_id")
    team2_id = st.session_state.get("team_2_id")
    team1_label = st.session_state.get("team_1_label", "Team 1")
    team2_label = st.session_state.get("team_2_label", "Team 2")
    phase_selected = st.session_state.get("phase_type", "Tutte")

    if not team1_id or not team2_id:
        st.info("Seleziona Team 1 e Team 2 in sidebar.")
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
        st.caption("Free tier 500 req/mese. Registrati su https://the-odds-api.com per ottenere la chiave.")
        odds_key = st.text_input(
            "API key (oppure imposta env ODDS_API_KEY)",
            value=ODDS_API_KEY,
            type="password",
            key="oddsapi_key_input",
        )
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

        if not st.button("🔎 Scansiona linee reali"):
            st.info("Premi per scaricare linee/quote reali e generare alert.")
            return
        if not odds_key:
            st.error("Inserisci l'API key di The Odds API per la modalità auto.")
            return

        with st.spinner("Scarico eventi NBA, props e calcolo value..."):
            df_auto, err = _scan_value_with_real_odds(
                api_key=odds_key,
                n_partite=n_partite,
                phase_selected=phase_selected,
                bankroll=float(bankroll_for_kelly_a),
                kelly_frac=float(kelly_fraction_a),
                min_edge=float(min_edge_a),
                min_hit=float(min_hit_a),
                time_mode=time_mode_a,
            )
        if err:
            st.warning(err)
            return
        st.success(f"Trovate {len(df_auto)} value bet OVER reali (linee + quote da bookmakers).")
        st.caption("Solo segnali OVER (compatibili con Eplay24). Under disabilitati.")
        st.dataframe(df_auto, width="stretch", hide_index=True)

        top = df_auto.head(5)
        st.markdown("#### 🔥 Top 5 Pick reali")
        for _, r in top.iterrows():
            st.write(
                f"- **{r['Giocatore']} {r['Stat']} OVER {r['Linea']}** · "
                f"Quota {r['Quota Over']} ({r['Bookmaker']}) · Prob {r['Prob Over %']}% · "
                f"Edge {r['Edge %']}% · Kelly €{r['Kelly €']:.2f} · {r['Signal']} · {r['Match']}"
            )

        st.download_button(
            "⬇️ Esporta Alert Value (CSV)",
            data=df_to_csv(df_auto),
            file_name=f"alert_value_real_{datetime.date.today()}.csv",
            mime="text/csv",
        )
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
    s1, s2, s3 = st.columns(3)
    s1.metric("API NBA", "🟢 Configurata" if API_KEY else "🔴 Mancante")
    s2.metric("Odds API", "🟢 Configurata" if ODDS_API_KEY else "🔴 Mancante")
    s3.metric("Versione", VERSION)

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
    st.markdown("#### 📡 Stato configurazione")
    cfg = pd.DataFrame([
        {"Parametro": "BASE_URL", "Valore": BASE_URL},
        {"Parametro": "ODDS_API_BASE", "Valore": ODDS_API_BASE},
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
        '<div style="text-align:center;padding:12px 0 8px;">'
        '<span style="font-size:2rem;">🐋</span><br>'
        f'<strong style="color:#00D4AA;font-size:1.1rem;">NBA Whale Pro</strong>'
        f'<span class="badge">v{VERSION}</span><br>'
        f'<span style="color:#8B949E;font-size:0.75rem;">Stagione 20{SEASON}-20{int(SEASON)+1}</span>'
        '</div>', unsafe_allow_html=True)
    st.markdown("---")

    pagina = st.radio("Navigazione",
                      ["📊 Analisi Singolo","⚔️ Confronto","🏀 Squadre","🚨 Alert Value","🧰 Toolkit Pro","📈 Tipster Pro","🩺 Salute Dati","💰 Bankroll","ℹ️ Guida"],
                      label_visibility="collapsed")
    st.markdown("---")

    st.markdown("**🏁 Tipo partite**")
    phase_type = st.selectbox(
        "Competizione",
        ["Tutte", "Regular Season", "Play-In", "Playoff"],
        index=0,
        key="phase_type",
    )
    st.markdown("---")

    st.markdown("**⚙️ Linee Over/Under**")
    linea_pts = st.number_input("Punti",    value=22.5, step=0.5, key="l_pts")
    linea_reb = st.number_input("Rimbalzi", value=5.5,  step=0.5, key="l_reb")
    linea_ast = st.number_input("Assist",   value=4.5,  step=0.5, key="l_ast")
    linee = {"PTS": linea_pts, "REB": linea_reb, "AST": linea_ast}

    st.markdown("**📅 Finestre di analisi**")
    n_partite = st.slider("Ultime gare",    5, 20, 10, key="n_gare")
    n_slump   = st.slider("Finestra slump", 3, 10,  5, key="n_slump")
    st.checkbox("Usa tutte le partite giocate", value=False, key="use_all_games")
    st.markdown("---")

    st.markdown("**🏀 Confronto squadre**")
    teams_opts = fetch_teams(SEASON)
    if teams_opts:
        labels = [t["label"] for t in teams_opts]
        default_1 = labels.index("Los Angeles Lakers (LAL)") if "Los Angeles Lakers (LAL)" in labels else 0
        default_2 = labels.index("Boston Celtics (BOS)") if "Boston Celtics (BOS)" in labels else min(1, len(labels) - 1)
        t1_label = st.selectbox("Squadra 1", labels, index=default_1, key="team_1_label")
        t2_label = st.selectbox("Squadra 2", labels, index=default_2, key="team_2_label")
        lookup = {t["label"]: t["id"] for t in teams_opts}
        st.session_state.team_1_id = lookup.get(t1_label)
        st.session_state.team_2_id = lookup.get(t2_label)

        roster_team_label = st.selectbox("Roster da squadra", labels, index=default_1, key="roster_team_label")
        roster_team_id = lookup.get(roster_team_label)
        team_players = fetch_team_players(roster_team_id, SEASON) if roster_team_id else []
        if team_players:
            player_labels = [p["label"] for p in team_players]
            selected_label = st.selectbox("Giocatore (da roster)", player_labels, key="sidebar_player_pick_label")
            selected_map = {p["label"]: p["name"] for p in team_players}
            sidebar_player = selected_map.get(selected_label, "")
            st.session_state["sidebar_player_pick"] = sidebar_player
            st.checkbox("Usa giocatore roster in Analisi Singolo", value=False, key="use_sidebar_player_sync")
            st.caption(f"Selezionato: {sidebar_player}")
        else:
            st.caption("Roster non disponibile per la squadra selezionata.")
    else:
        st.caption("Team list non disponibile (API).")
        if st.button("🔄 Riprova caricamento team"):
            fetch_teams.clear()
            st.rerun()

    st.markdown("---")
    api_ok = "🟢 Configurata" if API_KEY else "🔴 Mancante"
    st.caption(f"API Key: {api_ok}")
    with st.expander("📚 Legenda veloce acronimi"):
        st.caption("PTS punti · REB rimbalzi · AST assist · STL rubate · BLK stoppate · TOV perse · MIN minuti · PF/PA punti fatti/subiti")
    integ = player_integrity_report()
    if integ["collisions"]:
        st.caption(f"⚠️ Anomalie DB player ID: {len(integ['collisions'])}")
        with st.expander("Dettaglio anomalie player ID"):
            for pid, names in sorted(integ["collisions"].items()):
                st.write(f"ID {pid}: {', '.join(names)}")
    st.caption("⚠️ Non è consulenza finanziaria.")

if not API_KEY and pagina != "ℹ️ Guida":
    st.error("⚠️ Chiave api-sports.io non configurata. "
             "Imposta la variabile d'ambiente **API_SPORTS_KEY**.")
    st.stop()

if   pagina == "📊 Analisi Singolo": single_player_page(linee, n_partite, n_slump)
elif pagina == "⚔️ Confronto":       comparison_page(linee, n_partite, n_slump)
elif pagina == "🏀 Squadre":         teams_comparison_page(n_partite)
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

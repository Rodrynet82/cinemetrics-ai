"""
app.py - CineMetrics AI · Box Office Dashboard (Neon Holographic · i18n)
=========================================================================
Rediseño con soporte multiidioma (ES / EN).
Ejecutar con: streamlit run app.py
"""

import logging
import sys
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CineMetrics AI · Box Office Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# TRANSLATIONS (i18n)
# ─────────────────────────────────────────────────────────────────────────────
TRANSLATIONS: dict[str, dict] = {
    "ES": {
        # Header
        "sys_subtitle":   "SISTEMA DE INTELIGENCIA TAQUILLERA · v2.0",
        "live_label":     "EN VIVO",
        "mode_demo":      "MODO DEMO",
        "mode_live":      "CLICKHOUSE LIVE",
        # Tabs
        "tab_dashboard":  "📊  DASHBOARD",
        "tab_ai":         "🤖  AI ANALYST",
        # KPI strip
        "kpi_box_office": "🌍 Taquilla Global",
        "kpi_tickets":    "🎟️ Entradas Q3",
        "kpi_sentiment":  "💬 Sent. Positivo",
        "kpi_films":      "🎞️ Películas Activas",
        "kpi_viewers":    "👁️ Viewers Live",
        # Card titles
        "c_box_office":   "📈 TAQUILLA GLOBAL · FIN DE SEMANA",
        "c_engagement":   "🎯 ENGAGEMENT DE AUDIENCIA",
        "c_sat_score":    "PUNTUACIÓN DE SATISFACCIÓN",
        "c_demo":         "👥 DEMOGRAFÍA",
        "c_traffic":      "👁️ TRÁFICO EN TIEMPO REAL",
        "c_viewers":      "Espectadores Actuales",
        "c_markets":      "MERCADOS",
        "c_avg":          "PROM. VIS.",
        "c_releases":     "🎬 PRÓXIMOS ESTRENOS",
        "c_regional":     "🌍 RENDIMIENTO REGIONAL",
        "c_sentiment":    "💬 SENTIMIENTO SOCIAL",
        "c_positive":     "POSITIVO 74%",
        "c_predict":      "🤖 PREDICCIONES IA",
        # Chart labels
        "weeks":          ["Sem 1","Sem 2","Sem 3","Sem 4","Sem 5"],
        "weeks_eng":      ["Sem 1","Sem 2","Sem 3","Sem 4","Sem 5","Sem 6","Sem 7","Sem 8","Sem 9","Sem 10","Sem 11","Sem 12"],
        "annot_peak":     "▲ 22%  Sem 3: $312M",
        "donut_center":   "88%\nSCORE",
        "hover_ticket":   "Sem %{x}: %{y}%",
        # Regional card numbers
        "reg_asia":  "$620M", "reg_us": "$450M", "reg_eu": "$380M",
        # Sentiment bars
        "sent_bars": [
            ("Hype",         74, "#BF00FF"),
            ("Obra Maestra", 68, "#00FF9F"),
            ("Anticipación", 81, "#00F5FF"),
            ("Buzz Crítica", 55, "#FF2D78"),
        ],
        # Sentiment chart labels
        "sent_hype":  "Hype",
        "sent_mast":  "Obra Maestra",
        # Upcoming releases
        "releases": [
            ("Galactic Odyssey 2",  "15 Sep 2026", "#00F5FF", "95%"),
            ("El Último Horizonte", "22 Sep 2026", "#BF00FF", "82%"),
            ("Thunder Squad 4",     "04 Oct 2026", "#FF2D78", "91%"),
            ("La Mansión",          "18 Oct 2026", "#00FF9F", "77%"),
        ],
        # AI Predictions
        "predictions": [
            ("Galactic Odyssey 2",
             "Proyección abre en $200M+. IMAX agotado en 12 mercados.",
             "CONF: 91%"),
            ("Campaña Digital MX",
             "ROI estimado 3.2x. Escalar presupuesto recomendado.",
             "CONF: 87%"),
            ("Alerta Sentiment Drop",
             "La Mansión: riesgo de caída post-premiere. Monitorear.",
             "CONF: 78%"),
        ],
        # Badges
        "badge_wknd":  "▲ 22% vs Ú4S",
        "best_week":   "Sem 3: $312M · Mejor semana del trimestre",
        "live_pct":    "▲ 8% EN VIVO",
        # AI Chat tab
        "chat_title":       "🤖 GEMINI AI ANALYST · CONSULTA EN LENGUAJE NATURAL",
        "ch_toggle":        "ClickHouse Real",
        "ch_help":          "Activa para conectar al servidor MCP de ClickHouse real",
        "clear_btn":        "🗑️ LIMPIAR",
        "send_btn":         "ENVIAR →",
        "chat_placeholder": "Ej: ¿Cuáles son los 5 mercados con mayor taquilla este trimestre?",
        "chat_empty_icon":  "💬",
        "chat_empty_text":  "ESPERANDO CONSULTA · ESCRIBE UNA PREGUNTA",
        "spinner_text":     "🎬 Analizando consulta con Gemini…",
        "data_expand":      "📊 DATOS · Resultado ClickHouse",
        "sql_expand":       "🔍 SQL GENERADO POR GEMINI",
        "mcp_tool":         "Herramienta MCP",
        "sdk_caption":      "Gemini genera SQL automáticamente · MCP ClickHouse · google-genai SDK",
        "examples": [
            "¿Cuántas entradas se vendieron en España?",
            "¿Top 5 películas por taquilla?",
            "¿Qué formato genera más ingresos: IMAX o 3D?",
            "¿ROI de campañas digitales vs TV?",
            "¿Público objetivo 18-34 por mercado?",
        ],
    },
    "EN": {
        # Header
        "sys_subtitle":   "BOX OFFICE INTELLIGENCE SYSTEM · v2.0",
        "live_label":     "LIVE",
        "mode_demo":      "DEMO MODE",
        "mode_live":      "CLICKHOUSE LIVE",
        # Tabs
        "tab_dashboard":  "📊  DASHBOARD",
        "tab_ai":         "🤖  AI ANALYST",
        # KPI strip
        "kpi_box_office": "🌍 Global Box Office",
        "kpi_tickets":    "🎟️ Tickets Q3",
        "kpi_sentiment":  "💬 Positive Sent.",
        "kpi_films":      "🎞️ Active Films",
        "kpi_viewers":    "👁️ Live Viewers",
        # Card titles
        "c_box_office":   "📈 GLOBAL BOX OFFICE · WEEKEND GROSS",
        "c_engagement":   "🎯 AUDIENCE ENGAGEMENT",
        "c_sat_score":    "SATISFACTION SCORE",
        "c_demo":         "👥 DEMOGRAPHICS",
        "c_traffic":      "👁️ REAL-TIME TRAFFIC",
        "c_viewers":      "Current Viewers",
        "c_markets":      "MARKETS",
        "c_avg":          "AVG VIEW",
        "c_releases":     "🎬 UPCOMING RELEASES",
        "c_regional":     "🌍 REGIONAL PERFORMANCE",
        "c_sentiment":    "💬 SOCIAL SENTIMENT",
        "c_positive":     "POSITIVE 74%",
        "c_predict":      "🤖 AI PREDICTIONS",
        # Chart labels
        "weeks":         ["Wk 1","Wk 2","Wk 3","Wk 4","Wk 5"],
        "weeks_eng":     ["Wk 1","Wk 2","Wk 3","Wk 4","Wk 5","Wk 6","Wk 7","Wk 8","Wk 9","Wk 10","Wk 11","Wk 12"],
        "annot_peak":    "▲ 22%  Wk 3: $312M",
        "donut_center":  "88%\nSCORE",
        "hover_ticket":  "Wk %{x}: %{y}%",
        # Regional card numbers
        "reg_asia": "$620M", "reg_us": "$450M", "reg_eu": "$380M",
        # Sentiment bars
        "sent_bars": [
            ("Hype",         74, "#BF00FF"),
            ("Masterpiece",  68, "#00FF9F"),
            ("Anticipation", 81, "#00F5FF"),
            ("Review Buzz",  55, "#FF2D78"),
        ],
        # Sentiment chart labels
        "sent_hype":  "Hype",
        "sent_mast":  "Masterpiece",
        # Upcoming releases
        "releases": [
            ("Galactic Odyssey 2",  "Sep 15, 2026", "#00F5FF", "95%"),
            ("El Último Horizonte", "Sep 22, 2026", "#BF00FF", "82%"),
            ("Thunder Squad 4",     "Oct 04, 2026", "#FF2D78", "91%"),
            ("La Mansión",          "Oct 18, 2026", "#00FF9F", "77%"),
        ],
        # AI Predictions
        "predictions": [
            ("Galactic Odyssey 2",
             "Projected opening $200M+. IMAX sold out in 12 markets.",
             "CONF: 91%"),
            ("Digital Campaign MX",
             "Estimated ROI 3.2x. Scaling budget recommended.",
             "CONF: 87%"),
            ("Sentiment Drop Alert",
             "La Mansión: post-premiere drop risk. Monitor closely.",
             "CONF: 78%"),
        ],
        # Badges
        "badge_wknd":  "▲ 22% vs L4W",
        "best_week":   "Wk 3: $312M · Best week of the quarter",
        "live_pct":    "▲ 8% LIVE",
        # AI Chat tab
        "chat_title":       "🤖 GEMINI AI ANALYST · NATURAL LANGUAGE QUERY",
        "ch_toggle":        "Real ClickHouse",
        "ch_help":          "Enable to connect to the real MCP ClickHouse server",
        "clear_btn":        "🗑️ CLEAR",
        "send_btn":         "SEND →",
        "chat_placeholder": "E.g.: What are the top 5 markets by box office this quarter?",
        "chat_empty_icon":  "💬",
        "chat_empty_text":  "AWAITING QUERY · TYPE A QUESTION BELOW",
        "spinner_text":     "🎬 Analyzing query with Gemini…",
        "data_expand":      "📊 DATA · ClickHouse Result",
        "sql_expand":       "🔍 SQL GENERATED BY GEMINI",
        "mcp_tool":         "MCP Tool",
        "sdk_caption":      "Gemini auto-generates SQL · MCP ClickHouse · google-genai SDK",
        "examples": [
            "How many tickets were sold in Spain?",
            "Top 5 films by box office?",
            "Which format earns more: IMAX or 3D?",
            "ROI of digital campaigns vs TV?",
            "Target audience 18-34 by market?",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');

:root {
    --neon-cyan:    #00F5FF;
    --neon-purple:  #BF00FF;
    --neon-pink:    #FF2D78;
    --neon-green:   #00FF9F;
    --neon-blue:    #0066FF;
    --bg-deep:      #020813;
    --bg-card:      #060D1F;
    --bg-card2:     #080E20;
    --border-dim:   rgba(0,245,255,0.2);
    --text-bright:  #E8F4FF;
    --text-dim:     #5A7A9A;
    --font-hud:     'Orbitron', monospace;
    --font-body:    'Rajdhani', sans-serif;
}
html, body, .stApp {
    background: var(--bg-deep) !important;
    background-image:
        radial-gradient(ellipse at 15% 0%,   rgba(0,102,255,0.12) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 100%, rgba(191,0,255,0.10) 0%, transparent 55%),
        radial-gradient(ellipse at 50% 50%,  rgba(0,245,255,0.03) 0%, transparent 70%) !important;
    font-family: var(--font-body) !important;
    color: var(--text-bright) !important;
}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
[data-testid="stSidebar"]{display:none!important}
.block-container{padding:1rem 1.5rem 2rem!important;max-width:100%!important}

/* Scanline */
.stApp::before{
    content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
    background:repeating-linear-gradient(0deg,rgba(0,245,255,0.015) 0px,transparent 1px,transparent 3px);
}

/* Header */
.hud-header{
    display:flex;align-items:center;justify-content:space-between;
    padding:12px 20px;
    background:linear-gradient(90deg,rgba(0,245,255,0.06) 0%,rgba(191,0,255,0.06) 100%);
    border:1px solid var(--border-dim);border-top:2px solid var(--neon-cyan);
    border-radius:4px 4px 0 0;margin-bottom:2px;
    box-shadow:0 0 30px rgba(0,245,255,0.08),inset 0 1px 0 rgba(0,245,255,0.3);
}
.hud-title{
    font-family:var(--font-hud);font-size:1.4rem;font-weight:900;
    letter-spacing:0.15em;text-transform:uppercase;
    color:var(--text-bright);
    text-shadow:0 0 10px var(--neon-cyan),0 0 30px rgba(0,245,255,0.4);
    margin:0;line-height:1.2;
}
.hud-title span{color:var(--neon-cyan);}
.hud-subtitle{font-family:var(--font-hud);font-size:.5rem;color:#2A4A6A;letter-spacing:.1em;margin:3px 0 0;}
.hud-meta{font-family:var(--font-hud);font-size:.62rem;color:var(--text-dim);letter-spacing:.1em;text-align:right;line-height:1.7;}
.hud-meta strong{color:var(--neon-cyan);}
.hud-dot{width:7px;height:7px;border-radius:50%;background:var(--neon-green);
    box-shadow:0 0 8px var(--neon-green),0 0 20px var(--neon-green);
    display:inline-block;margin-right:5px;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

/* Lang switcher */
.lang-btn-row{display:flex;gap:6px;align-items:center;margin-left:20px;}
.lang-pill{
    font-family:var(--font-hud);font-size:.6rem;letter-spacing:.1em;
    padding:4px 10px;border-radius:3px;cursor:pointer;border:1px solid;
    transition:all .2s;text-decoration:none;
}
.lang-active{
    background:rgba(0,245,255,.15);color:var(--neon-cyan);
    border-color:var(--neon-cyan);box-shadow:0 0 8px rgba(0,245,255,.3);
}
.lang-inactive{background:transparent;color:var(--text-dim);border-color:rgba(255,255,255,.1);}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{
    background:rgba(0,13,30,.95)!important;
    border-bottom:1px solid var(--border-dim)!important;
    gap:4px;padding:0 8px;
}
.stTabs [data-baseweb="tab"]{
    font-family:var(--font-hud)!important;font-size:.68rem!important;
    letter-spacing:.12em!important;color:var(--text-dim)!important;
    padding:10px 22px!important;border:none!important;background:transparent!important;
    border-bottom:2px solid transparent!important;transition:all .2s!important;
}
.stTabs [aria-selected="true"]{
    color:var(--neon-cyan)!important;border-bottom:2px solid var(--neon-cyan)!important;
    text-shadow:0 0 8px var(--neon-cyan)!important;background:rgba(0,245,255,.05)!important;
}
.stTabs [data-baseweb="tab-panel"]{background:transparent!important;padding:0!important;}

/* Neon card */
.neon-card{
    background:var(--bg-card);border:1px solid var(--border-dim);
    border-radius:6px;padding:16px;position:relative;overflow:hidden;
    box-shadow:0 0 20px rgba(0,245,255,.04),inset 0 1px 0 rgba(0,245,255,.12);
    margin-bottom:12px;
}
.neon-card::before{
    content:'';position:absolute;top:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,var(--neon-cyan),transparent);opacity:.5;
}
.neon-card.purple::before{background:linear-gradient(90deg,transparent,var(--neon-purple),transparent);}
.neon-card.pink::before{background:linear-gradient(90deg,transparent,var(--neon-pink),transparent);}
.neon-card.green::before{background:linear-gradient(90deg,transparent,var(--neon-green),transparent);}

/* Card title */
.card-title{font-family:var(--font-hud);font-size:.65rem;letter-spacing:.14em;
    text-transform:uppercase;color:var(--text-dim);margin-bottom:6px;}
.card-title.cyan  {color:var(--neon-cyan);  text-shadow:0 0 6px var(--neon-cyan);}
.card-title.purple{color:var(--neon-purple);text-shadow:0 0 6px var(--neon-purple);}
.card-title.pink  {color:var(--neon-pink);  text-shadow:0 0 6px var(--neon-pink);}
.card-title.green {color:var(--neon-green); text-shadow:0 0 6px var(--neon-green);}

/* Big metric */
.big-metric{
    font-family:var(--font-hud);font-size:2.4rem;font-weight:900;line-height:1;
    color:var(--neon-cyan);text-shadow:0 0 20px var(--neon-cyan),0 0 50px rgba(0,245,255,.4);
    margin:8px 0 4px;
}
.big-metric.purple{color:var(--neon-purple);text-shadow:0 0 20px var(--neon-purple),0 0 50px rgba(191,0,255,.4);}
.big-metric.green {color:var(--neon-green); text-shadow:0 0 20px var(--neon-green), 0 0 50px rgba(0,255,159,.4);}
.metric-sub{font-family:var(--font-body);font-size:.77rem;color:var(--text-dim);letter-spacing:.05em;}
.metric-badge{display:inline-block;padding:2px 8px;border-radius:3px;
    font-family:var(--font-hud);font-size:.58rem;font-weight:700;letter-spacing:.1em;}
.badge-up{background:rgba(0,255,159,.15);color:var(--neon-green);border:1px solid rgba(0,255,159,.3);}

/* Mini KPI */
.mini-kpi-row{display:flex;gap:8px;margin-bottom:12px;}
.mini-kpi{flex:1;background:rgba(0,245,255,.04);border:1px solid var(--border-dim);border-radius:4px;padding:10px 12px;text-align:center;}
.mini-kpi-val{font-family:var(--font-hud);font-size:1.05rem;font-weight:700;
    color:var(--neon-cyan);text-shadow:0 0 8px var(--neon-cyan);display:block;}
.mini-kpi-lbl{font-size:.6rem;color:var(--text-dim);letter-spacing:.08em;text-transform:uppercase;}

/* Releases */
.release-item{display:flex;align-items:center;gap:10px;padding:7px 10px;border-bottom:1px solid rgba(0,245,255,.06);}
.release-item:last-child{border-bottom:none;}
.release-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;}
.release-title{font-size:.8rem;font-weight:600;color:var(--text-bright);}
.release-meta{font-size:.67rem;color:var(--text-dim);margin-top:1px;}
.release-score{margin-left:auto;font-family:var(--font-hud);font-size:.68rem;font-weight:700;
    padding:2px 7px;border-radius:3px;white-space:nowrap;}

/* Predictions */
.prediction-item{padding:8px 10px;border-left:2px solid var(--neon-purple);margin-bottom:6px;
    background:rgba(191,0,255,.05);border-radius:0 4px 4px 0;}
.prediction-title{font-size:.79rem;font-weight:600;color:var(--text-bright);}
.prediction-desc{font-size:.67rem;color:var(--text-dim);margin-top:2px;}
.prediction-conf{font-family:var(--font-hud);font-size:.63rem;color:var(--neon-purple);margin-top:4px;}

/* Sentiment bars */
.sentiment-bar-wrap{margin:6px 0;}
.sentiment-label{display:flex;justify-content:space-between;font-size:.7rem;margin-bottom:3px;color:var(--text-dim);}
.sentiment-label span:last-child{color:var(--neon-cyan);font-family:var(--font-hud);}
.sentiment-bar-bg{background:rgba(0,245,255,.08);border-radius:2px;height:5px;overflow:hidden;}
.sentiment-bar-fill{height:100%;border-radius:2px;}

/* Chat */
.chat-user{
    background:rgba(191,0,255,.1);border:1px solid rgba(191,0,255,.3);
    border-radius:12px 12px 4px 12px;padding:12px 16px;margin:8px 0;
    max-width:72%;margin-left:auto;font-size:.9rem;color:var(--text-bright);
}
.chat-agent{
    background:var(--bg-card2);border:1px solid var(--border-dim);
    border-radius:12px 12px 12px 4px;padding:14px 18px;margin:8px 0;
    max-width:88%;font-size:.9rem;color:var(--text-bright);line-height:1.7;
    box-shadow:0 0 20px rgba(0,245,255,.04);
}

/* Inputs */
.stTextInput>div>div>input{
    background:rgba(0,13,30,.9)!important;border:1px solid var(--border-dim)!important;
    border-radius:4px!important;color:var(--text-bright)!important;
    font-family:var(--font-body)!important;font-size:.95rem!important;
}
.stTextInput>div>div>input:focus{
    border-color:var(--neon-cyan)!important;box-shadow:0 0 12px rgba(0,245,255,.2)!important;
}
.stButton>button{
    background:linear-gradient(135deg,rgba(0,245,255,.15),rgba(191,0,255,.15))!important;
    border:1px solid var(--neon-cyan)!important;color:var(--neon-cyan)!important;
    font-family:var(--font-hud)!important;font-size:.68rem!important;letter-spacing:.1em!important;
    border-radius:4px!important;transition:all .2s!important;
}
.stButton>button:hover{background:rgba(0,245,255,.2)!important;box-shadow:0 0 15px rgba(0,245,255,.3)!important;}

/* Misc */
[data-testid="stDataFrame"]{border-radius:6px;overflow:hidden;}
[data-testid="stExpander"]{background:var(--bg-card2)!important;border:1px solid var(--border-dim)!important;border-radius:4px!important;}
.stSpinner>div{border-top-color:var(--neon-cyan)!important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:var(--bg-deep);}
::-webkit-scrollbar-thumb{background:rgba(0,245,255,.3);border-radius:2px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG GUARD
# ─────────────────────────────────────────────────────────────────────────────
from config import get_settings_safe, ENV_FILE_PATH  # noqa: E402

_settings, _config_error = get_settings_safe()
if _config_error or _settings is None:
    st.markdown(f"""
    <div style="max-width:560px;margin:80px auto;padding:36px;
                background:#060D1F;border:1px solid rgba(0,245,255,.25);
                border-top:2px solid #00F5FF;border-radius:6px;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:14px">⚙️</div>
        <h2 style="font-family:'Orbitron',monospace;color:#E8F4FF;font-size:1rem;letter-spacing:.15em;">
            CONFIGURATION REQUIRED
        </h2>
        <p style="color:#5A7A9A;font-size:.85rem;margin-bottom:22px;">
            Set your <strong style="color:#00F5FF">GOOGLE_API_KEY</strong> to start the system.
        </p>
        <div style="background:#020813;border:1px solid #1A2A3A;border-radius:4px;
                    padding:16px;text-align:left;font-family:monospace;font-size:.8rem;
                    color:#58A6FF;margin-bottom:20px;">
            1. Copy <span style="color:#FFD700">.env.example</span> → <span style="color:#00FF9F">.env</span><br>
            2. Add: <span style="color:#FF2D78">GOOGLE_API_KEY=AIza...</span><br>
            3. Save and reload
        </div>
        <a href="https://aistudio.google.com/app/apikey" target="_blank"
           style="background:rgba(0,245,255,.15);border:1px solid #00F5FF;color:#00F5FF;
                  padding:8px 20px;border-radius:4px;text-decoration:none;
                  font-family:'Orbitron',monospace;font-size:.65rem;letter-spacing:.1em;">
            🔑 GET API KEY
        </a>
        <p style="color:#2A3A4A;font-size:.68rem;margin-top:16px;">{ENV_FILE_PATH}</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "messages":      [],
        "use_mock":      True,
        "total_queries": 0,
        "session_start": datetime.now().strftime("%H:%M"),
        "lang":          "ES",   # ← idioma activo
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# Shortcut cómodo al diccionario del idioma activo
t = TRANSLATIONS[st.session_state.lang]

# ─────────────────────────────────────────────────────────────────────────────
# CHART HELPERS  (reciben `t` para textos traducidos)
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Rajdhani, sans-serif", color="#5A7A9A", size=10),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(
        gridcolor="rgba(0,245,255,0.06)",
        zerolinecolor="rgba(0,245,255,0.1)",
        tickfont=dict(color="#5A7A9A", size=9),
        linecolor="rgba(0,245,255,0.1)",
    ),
    yaxis=dict(
        gridcolor="rgba(0,245,255,0.06)",
        zerolinecolor="rgba(0,245,255,0.1)",
        tickfont=dict(color="#5A7A9A", size=9),
        linecolor="rgba(0,245,255,0.1)",
    ),
)
CHART_CFG = {"displayModeBar": False, "responsive": True}

_Y_BASE = dict(
    gridcolor="rgba(0,245,255,0.06)",
    zerolinecolor="rgba(0,245,255,0.1)",
    tickfont=dict(color="#5A7A9A", size=9),
)


def chart_box_office(t: dict) -> go.Figure:
    gross = [148, 221, 312, 278, 355]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t["weeks"], y=gross, mode="lines+markers",
        fill="tozeroy", fillcolor="rgba(0,245,255,0.07)",
        line=dict(color="#00F5FF", width=2.5, shape="spline"),
        marker=dict(color="#00F5FF", size=6, line=dict(color="#001A2E", width=2)),
        name="Box Office", hovertemplate="%{y}M€<extra></extra>",
    ))
    fig.add_annotation(
        x=t["weeks"][2], y=312, text=t["annot_peak"],
        font=dict(color="#00FF9F", size=9, family="Orbitron"),
        showarrow=False, yshift=14,
        bgcolor="rgba(0,255,159,0.12)", bordercolor="rgba(0,255,159,0.4)",
        borderwidth=1, borderpad=4,
    )
    fig.update_layout(**PLOTLY_BASE)
    fig.update_layout(
        height=170,
        yaxis=dict(**_Y_BASE, tickprefix="$", ticksuffix="M", range=[0, 420]),
    )
    return fig


def chart_regional(t: dict) -> go.Figure:
    regions = ["US", "EU", "ASIA", "LATAM", "MEA"]
    values  = [450, 380, 620, 195, 142]
    colors  = ["#00F5FF", "#BF00FF", "#FF2D78", "#00FF9F", "#0066FF"]
    fig = go.Figure()
    for r, v, c in zip(regions, values, colors):
        fig.add_trace(go.Bar(
            x=[r], y=[v], name=r,
            marker=dict(
                color=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.5)",
                line=dict(color=c, width=1.5),
            ),
            hovertemplate=f"{r}: ${v}M<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_BASE)
    fig.update_layout(
        height=170, showlegend=False, barmode="group",
        yaxis=dict(**_Y_BASE, tickprefix="$", ticksuffix="M"),
    )
    return fig


def chart_demographics(t: dict) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=["18-34", "35-49", "50+"],
        values=[45, 30, 25], hole=0.62,
        marker=dict(colors=["#00F5FF", "#BF00FF", "#FF2D78"],
                    line=dict(color="#020813", width=3)),
        textfont=dict(size=9, color="#5A7A9A"),
        hovertemplate="%{label}: %{value}%<extra></extra>",
    ))
    fig.add_annotation(
        text=t["donut_center"], x=0.5, y=0.5, showarrow=False,
        font=dict(color="#00F5FF", size=12, family="Orbitron"),
    )
    fig.update_layout(**PLOTLY_BASE)
    fig.update_layout(
        height=160, showlegend=True,
        legend=dict(font=dict(size=9, color="#5A7A9A"), orientation="v", x=1.05, y=0.5),
        margin=dict(l=0, r=60, t=0, b=0),
    )
    return fig


def chart_engagement(t: dict) -> go.Figure:
    vals = [62, 71, 58, 88, 75, 90, 83, 95, 79, 88, 91, 97]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=t["weeks_eng"], y=vals,
        marker=dict(
            color=[f"rgba(0,245,255,{0.3 + 0.05*i})" for i in range(12)],
            line=dict(color="#00F5FF", width=0.5),
        ),
        hovertemplate=t["hover_ticket"] + "<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_BASE)
    fig.update_layout(
        height=130, showlegend=False,
        yaxis=dict(**_Y_BASE, range=[0, 110], ticksuffix="%"),
    )
    return fig


def chart_sentiment(t: dict) -> go.Figure:
    weeks = [t["sent_hype"], t["sent_hype"]+"+", "Reset", "Test", "Review", t["sent_hype"], "Boom"]
    hype  = [40, 65, 30, 50, 45, 80, 74]
    mast  = [20, 30, 45, 60, 70, 65, 80]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks, y=hype, mode="lines", name=t["sent_hype"],
        line=dict(color="#BF00FF", width=2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(191,0,255,0.06)",
        hovertemplate=t["sent_hype"]+": %{y}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=mast, mode="lines", name=t["sent_mast"],
        line=dict(color="#00FF9F", width=2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(0,255,159,0.06)",
        hovertemplate=t["sent_mast"]+": %{y}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_BASE)
    fig.update_layout(
        height=150, showlegend=True,
        legend=dict(font=dict(size=8, color="#5A7A9A"), orientation="h", x=0, y=1.15),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# HEADER  (con language switcher)
# ─────────────────────────────────────────────────────────────────────────────
now = datetime.now()
mode_lbl = t["mode_demo"] if st.session_state.use_mock else t["mode_live"]

# Renderizar header con columnas: título | lang switcher | meta
hdr_left, hdr_lang, hdr_right = st.columns([4, 1, 2])

with hdr_left:
    st.markdown(f"""
    <div style="padding:12px 0 8px;">
        <p class="hud-title">🎬 <span>CINE</span>METRICS · AI</p>
        <p class="hud-subtitle">{t["sys_subtitle"]}</p>
    </div>
    """, unsafe_allow_html=True)

with hdr_lang:
    # Botones de idioma
    st.markdown("<div style='padding-top:14px;'>", unsafe_allow_html=True)
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        es_style = "background:rgba(0,245,255,.15);border-color:#00F5FF;" if st.session_state.lang == "ES" else ""
        if st.button("🇪🇸 ES", key="btn_es", use_container_width=True):
            st.session_state.lang = "ES"
            st.rerun()
    with lang_col2:
        en_style = "background:rgba(0,245,255,.15);border-color:#00F5FF;" if st.session_state.lang == "EN" else ""
        if st.button("🇬🇧 EN", key="btn_en", use_container_width=True):
            st.session_state.lang = "EN"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with hdr_right:
    st.markdown(f"""
    <div style="text-align:right;padding:12px 0 8px;
                font-family:'Orbitron',monospace;font-size:.6rem;
                color:#5A7A9A;letter-spacing:.1em;line-height:1.8;">
        <span class="hud-dot"></span><strong style="color:#00F5FF">{t["live_label"]}</strong><br>
        {now.strftime('%Y-%m-%d · %H:%M:%S')}<br>
        {mode_lbl}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='border-top:1px solid rgba(0,245,255,.15);margin-bottom:10px;'></div>",
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_dash, tab_ai = st.tabs([t["tab_dashboard"], t["tab_ai"]])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 · DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
with tab_dash:

    # ── KPI STRIP ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="mini-kpi-row">
        <div class="mini-kpi">
            <span class="mini-kpi-val">$1.85B</span>
            <span class="mini-kpi-lbl">{t["kpi_box_office"]}</span>
        </div>
        <div class="mini-kpi" style="border-color:rgba(191,0,255,.3);">
            <span class="mini-kpi-val" style="color:#BF00FF;text-shadow:0 0 8px #BF00FF;">18.4M</span>
            <span class="mini-kpi-lbl">{t["kpi_tickets"]}</span>
        </div>
        <div class="mini-kpi" style="border-color:rgba(0,255,159,.3);">
            <span class="mini-kpi-val" style="color:#00FF9F;text-shadow:0 0 8px #00FF9F;">74%</span>
            <span class="mini-kpi-lbl">{t["kpi_sentiment"]}</span>
        </div>
        <div class="mini-kpi" style="border-color:rgba(255,45,120,.3);">
            <span class="mini-kpi-val" style="color:#FF2D78;text-shadow:0 0 8px #FF2D78;">183</span>
            <span class="mini-kpi-lbl">{t["kpi_films"]}</span>
        </div>
        <div class="mini-kpi">
            <span class="mini-kpi-val">21,450</span>
            <span class="mini-kpi-lbl">{t["kpi_viewers"]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FILA 1 ────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([2.2, 1.9, 1.5])

    with c1:
        st.markdown(f"""
        <div class="neon-card" style="margin-bottom:0">
            <div class="card-title cyan">{t["c_box_office"]}</div>
            <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:4px;">
                <span class="big-metric" style="font-size:1.8rem;">$1.85B</span>
                <span class="metric-badge badge-up">{t["badge_wknd"]}</span>
            </div>
            <div class="metric-sub">{t["best_week"]}</div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_box_office(t), use_container_width=True, config=CHART_CFG)

    with c2:
        st.markdown(f"""
        <div class="neon-card purple" style="margin-bottom:6px;">
            <div class="card-title purple">{t["c_engagement"]}</div>
            <div style="display:flex;align-items:baseline;gap:8px;">
                <span class="big-metric purple" style="font-size:1.5rem;">88%</span>
                <span class="metric-badge badge-up">{t["c_sat_score"]}</span>
            </div>
            <div class="metric-sub">↑ 3pts</div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_engagement(t), use_container_width=True, config=CHART_CFG)

        st.markdown(f"""
        <div class="neon-card" style="margin-bottom:0;padding:12px 16px;">
            <div class="card-title">{t["c_demo"]}</div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_demographics(t), use_container_width=True, config=CHART_CFG)

    with c3:
        st.markdown(f"""
        <div class="neon-card green" style="margin-bottom:6px;text-align:center;padding:18px;">
            <div class="card-title green">{t["c_traffic"]}</div>
            <div class="big-metric green" style="font-size:2.2rem;">21,450</div>
            <div class="metric-sub">{t["c_viewers"]}</div>
            <div style="margin-top:10px;">
                <span class="metric-badge badge-up">{t["live_pct"]}</span>
            </div>
            <div style="height:1px;background:rgba(0,255,159,.15);margin:12px 0;"></div>
            <div style="display:flex;justify-content:space-around;">
                <div>
                    <div style="font-family:'Orbitron',monospace;font-size:.9rem;
                                color:#00FF9F;text-shadow:0 0 6px #00FF9F;">47</div>
                    <div style="font-size:.6rem;color:#5A7A9A;">{t["c_markets"]}</div>
                </div>
                <div>
                    <div style="font-family:'Orbitron',monospace;font-size:.9rem;
                                color:#00F5FF;text-shadow:0 0 6px #00F5FF;">3.2s</div>
                    <div style="font-size:.6rem;color:#5A7A9A;">{t["c_avg"]}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Upcoming Releases
        items_html = "".join(f"""
        <div class="release-item">
            <div class="release-dot" style="background:{c};box-shadow:0 0 6px {c};"></div>
            <div>
                <div class="release-title">{title}</div>
                <div class="release-meta">{date}</div>
            </div>
            <span class="release-score"
                  style="background:rgba(0,245,255,.08);color:{c};border:1px solid rgba(0,245,255,.2);">
                {score}
            </span>
        </div>
        """ for title, date, c, score in t["releases"])

        st.markdown(f"""
        <div class="neon-card" style="padding:12px;">
            <div class="card-title cyan" style="margin-bottom:8px;">{t["c_releases"]}</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)

    # ── FILA 2 ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns([2.0, 2.2, 1.5])

    with c4:
        st.markdown(f"""
        <div class="neon-card pink" style="margin-bottom:0;">
            <div class="card-title pink">{t["c_regional"]}</div>
            <div style="display:flex;gap:14px;margin-bottom:4px;">
                <div>
                    <span style="font-family:'Orbitron',monospace;font-size:.85rem;color:#FF2D78;">
                        {t["reg_asia"]}</span>
                    <span style="font-size:.6rem;color:#5A7A9A;"> ASIA</span>
                </div>
                <div>
                    <span style="font-family:'Orbitron',monospace;font-size:.85rem;color:#00F5FF;">
                        {t["reg_us"]}</span>
                    <span style="font-size:.6rem;color:#5A7A9A;"> US</span>
                </div>
                <div>
                    <span style="font-family:'Orbitron',monospace;font-size:.85rem;color:#BF00FF;">
                        {t["reg_eu"]}</span>
                    <span style="font-size:.6rem;color:#5A7A9A;"> EU</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_regional(t), use_container_width=True, config=CHART_CFG)

    with c5:
        bars_html = "".join(f"""
        <div class="sentiment-bar-wrap">
            <div class="sentiment-label">
                <span>{label}</span><span>{val}%</span>
            </div>
            <div class="sentiment-bar-bg">
                <div class="sentiment-bar-fill"
                     style="width:{val}%;background:linear-gradient(90deg,{color}88,{color});
                            box-shadow:0 0 6px {color};"></div>
            </div>
        </div>
        """ for label, val, color in t["sent_bars"])

        st.markdown(f"""
        <div class="neon-card green">
            <div class="card-title green">
                {t["c_sentiment"]} · <span style="color:#00FF9F">{t["c_positive"]}</span>
            </div>
            {bars_html}
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_sentiment(t), use_container_width=True, config=CHART_CFG)

    with c6:
        preds_html = "".join(f"""
        <div class="prediction-item">
            <div class="prediction-title">{title}</div>
            <div class="prediction-desc">{desc}</div>
            <div class="prediction-conf">{conf}</div>
        </div>
        """ for title, desc, conf in t["predictions"])

        st.markdown(f"""
        <div class="neon-card purple">
            <div class="card-title purple">{t["c_predict"]}</div>
            {preds_html}
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 · AI ANALYST CHAT
# ═════════════════════════════════════════════════════════════════════════════
with tab_ai:

    s1, s2, s3 = st.columns([2, 1, 1])
    with s1:
        st.markdown(f"""
        <div style="font-family:'Orbitron',monospace;font-size:.68rem;
                    color:#00F5FF;letter-spacing:.12em;padding:12px 0 4px;">
            {t["chat_title"]}
        </div>
        """, unsafe_allow_html=True)
    with s2:
        use_real = st.toggle(t["ch_toggle"], value=not st.session_state.use_mock, help=t["ch_help"])
        st.session_state.use_mock = not use_real
    with s3:
        if st.button(t["clear_btn"], use_container_width=True):
            st.session_state.messages = []
            st.session_state.total_queries = 0
            st.rerun()

    # Example questions
    cols = st.columns(len(t["examples"]))
    for col, q in zip(cols, t["examples"]):
        with col:
            label = q[:28] + ("…" if len(q) > 28 else "")
            if st.button(label, key=f"ex_{q[:12]}", use_container_width=True):
                st.session_state["pending_q"] = q

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Chat history
    if not st.session_state.messages:
        st.markdown(f"""
        <div style="text-align:center;padding:40px 20px;color:#2A4A6A;">
            <div style="font-size:2rem;margin-bottom:10px;">{t["chat_empty_icon"]}</div>
            <p style="font-family:'Orbitron',monospace;font-size:.72rem;
                      letter-spacing:.12em;color:#2A4A6A;">
                {t["chat_empty_text"]}
            </p>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">👤 &nbsp;{msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-agent">🎬 &nbsp;{msg["content"]}</div>',
                        unsafe_allow_html=True)
            if msg.get("data"):
                with st.expander(t["data_expand"], expanded=True):
                    st.dataframe(pd.DataFrame(msg["data"]), use_container_width=True, hide_index=True)
            if msg.get("sql_query"):
                with st.expander(t["sql_expand"], expanded=False):
                    st.code(msg["sql_query"], language="sql")
                    if msg.get("tool_used"):
                        st.caption(f"{t['mcp_tool']}: `{msg['tool_used']}`  ·  Model: `{_settings.gemini_model}`")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── MCP Server availability guard ──────────────────────────────────────
    # Si el toggle está en "ClickHouse Real", verificar que el servidor MCP
    # está instalado antes de mostrar el input de chat.
    if not st.session_state.use_mock:
        import shutil
        from config import get_settings
        _s = get_settings()
        mcp_cmd = _s.mcp_server_command          # "uvx" o "mcp-clickhouse"
        mcp_exe_found = shutil.which(mcp_cmd) is not None

        if not mcp_exe_found:
            st.markdown(f"""
            <div style="background:#060D1F;border:1px solid rgba(255,45,120,.35);
                        border-left:3px solid #FF2D78;border-radius:6px;
                        padding:20px 24px;margin:12px 0;">
                <div style="font-family:'Orbitron',monospace;font-size:.75rem;
                            color:#FF2D78;letter-spacing:.12em;margin-bottom:10px;">
                    ⚠️ SERVIDOR MCP NO INSTALADO
                </div>
                <p style="color:#8A8A9A;font-size:.82rem;margin-bottom:14px;">
                    El ejecutable <code style="color:#FF2D78">{mcp_cmd}</code> no está
                    en el PATH. Instálalo con <strong style="color:#E8F4FF">una</strong>
                    de estas opciones y reinicia la app:
                </p>
                <div style="display:flex;gap:10px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:220px;background:#020813;border:1px solid #1A2A3A;
                                border-radius:4px;padding:14px;">
                        <div style="font-family:'Orbitron',monospace;font-size:.6rem;
                                    color:#00F5FF;margin-bottom:8px;">OPCIÓN A · pip directo</div>
                        <code style="color:#00FF9F;font-size:.78rem;display:block;line-height:1.8;">
                            .venv/Scripts/pip.exe install mcp-clickhouse
                        </code>
                        <div style="color:#5A7A9A;font-size:.68rem;margin-top:6px;">
                            Luego en .env:<br>
                            <code style="color:#58A6FF">MCP_SERVER_COMMAND=mcp-clickhouse<br>MCP_SERVER_ARGS=</code>
                        </div>
                    </div>
                    <div style="flex:1;min-width:220px;background:#020813;border:1px solid #1A2A3A;
                                border-radius:4px;padding:14px;">
                        <div style="font-family:'Orbitron',monospace;font-size:.6rem;
                                    color:#BF00FF;margin-bottom:8px;">OPCIÓN B · uv tool runner</div>
                        <code style="color:#00FF9F;font-size:.78rem;display:block;line-height:1.8;">
                            .venv/Scripts/pip.exe install uv
                        </code>
                        <div style="color:#5A7A9A;font-size:.68rem;margin-top:6px;">
                            .env por defecto ya usa uvx ✓
                        </div>
                    </div>
                </div>
                <div style="margin-top:14px;padding:10px 14px;background:rgba(0,255,159,.05);
                            border:1px solid rgba(0,255,159,.2);border-radius:4px;">
                    <span style="color:#00FF9F;font-size:.75rem;">
                        💡 O desactiva el toggle <strong>ClickHouse Real</strong>
                        para seguir en Modo Demo con datos simulados.
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # Deshabilitar el formulario cuando el servidor no está disponible
            st.stop()

    pending = st.session_state.pop("pending_q", None)

    with st.form("chat_form", clear_on_submit=True):
        ci, cb = st.columns([5, 1])
        with ci:
            user_input = st.text_input(
                "query", label_visibility="collapsed",
                placeholder=t["chat_placeholder"],
                value=pending or "",
            )
        with cb:
            submitted = st.form_submit_button(t["send_btn"], use_container_width=True)

    st.markdown(f'<p style="font-size:.67rem;color:#2A3A4A;letter-spacing:.05em;">{t["sdk_caption"]}</p>',
                unsafe_allow_html=True)

    # ── Process query ──────────────────────────────────────────────────────
    def process_query(query: str):
        from agent import run_agent_sync, AgentResponse
        from mcp_client import extract_clean_error_message

        st.session_state.messages.append({"role": "user", "content": query})
        st.session_state.total_queries += 1

        try:
            with st.spinner(t["spinner_text"]):
                response = run_agent_sync(query, use_mock=st.session_state.use_mock)
        except Exception as e:
            clean_err = extract_clean_error_message(e)
            response = AgentResponse(
                answer=(
                    f"⚠️ **Error al procesar la consulta**\n\n"
                    f"{clean_err}\n\n"
                    f"*Sugerencia:* Si no dispones de un servidor ClickHouse en tu máquina, "
                    f"desactiva la casilla **'ClickHouse Real'** para usar el Modo Demo."
                ),
                error=clean_err,
            )

        # Si el error es de servidor MCP no encontrado, revertir a modo demo
        if response.error and (
            "MCPServerNotFoundError" in response.error
            or "WinError 2" in response.error
            or "FileNotFoundError" in response.error
        ):
            st.session_state.use_mock = True
            answer = (
                "⚠️ **Servidor MCP no disponible** — revertido a Modo Demo automáticamente.\n\n"
                "El ejecutable del servidor MCP no fue encontrado en el sistema. "
                "Para conectarlo, asegúrate de tener `uv` o `mcp-clickhouse` instalado y reinicia la app."
            )
        else:
            answer = response.answer if response.answer else (f"⚠️ {response.error}" if response.error else "Sin respuesta.")

        st.session_state.messages.append({
            "role":      "assistant",
            "content":   answer,
            "data":      response.data,
            "sql_query": response.sql_query,
            "tool_used": response.tool_used,
        })
        st.rerun()

    if submitted and user_input.strip():
        process_query(user_input.strip())
    elif pending and pending.strip():
        process_query(pending.strip())



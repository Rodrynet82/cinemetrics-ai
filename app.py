"""
app.py - CineMetrics AI · Box Office Intelligence (Neon Holographic · 100% i18n · Full Suite v3.5)
==================================================================================================
Suite completa con soporte multiidioma total (ES / EN):
  - Tab 📊 DASHBOARD: Filtros interactivos reactivos (Género / Territorio / Período), KPIs dinámicos y Briefing Ejecutivo bilingüe descargable
  - Tab 🎮 WHAT-IF SIMULATOR: Simulador interactivo de estrenos con sliders, curvas de decaimiento y cálculo de ROI en tiempo real
  - Tab 📰 INDUSTRY NEWS: Radar de noticias bilingüe con enlaces directos clicables a fuentes líderes (Variety, Deadline, BoxOffice Pro), botón de actualización y evaluador de noticias personalizadas con Gemini
  - Tab 🤖 AI ANALYST: Chat en lenguaje natural con Gemini + servidor MCP ClickHouse (con esquemas de herramientas sanitizados)

Ejecutar con: streamlit run app.py
"""

import logging
import sys
import time
import json
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
    page_title="CineMetrics AI · Box Office Intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# TRANSLATIONS (100% i18n ES / EN)
# ─────────────────────────────────────────────────────────────────────────────
TRANSLATIONS: dict[str, dict] = {
    "ES": {
        # Header
        "sys_subtitle":       "SISTEMA DE INTELIGENCIA TAQUILLERA & MARKETING · v3.5",
        "live_label":         "EN VIVO",
        "mode_demo":          "MODO DEMO",
        "mode_live":          "CLICKHOUSE LIVE",
        # Tabs
        "tab_dashboard":      "📊  DASHBOARD",
        "tab_simulator":      "🎮  SIMULADOR WHAT-IF",
        "tab_news":           "📰  NOTICIAS & RADAR",
        "tab_ai":             "🤖  AI ANALYST",
        # Quick Filters
        "flt_genre":          "Género",
        "flt_territory":      "Territorio",
        "flt_period":         "Período",
        "all_genres":         ["Todos los Géneros", "Sci-Fi / Ficción", "Acción & Aventura", "Drama", "Terror / Horror", "Animación"],
        "all_territories":    ["Global", "Norteamérica (US/CA)", "Europa (EU)", "Asia-Pacífico", "Latinoamérica"],
        "all_periods":        ["Trimestre Actual (Q3)", "Últimos 12 Meses", "Proyección Q4", "Histórico 2025-2026"],
        "btn_export_brief":   "📄 Exportar Briefing Ejecutivo",
        # Briefing
        "brief_title":        "📄 INFORME EJECUTIVO DE ESTRATEGIA · DESCARGABLE",
        "brief_header":       "### 🎬 CINEMETRICS AI · INFORME ESTRATÉGICO EJECUTIVO",
        "brief_date_lbl":     "Fecha de Emisión",
        "brief_filters_lbl":  "Filtros Aplicados",
        "brief_sec1_title":   "#### 1. Rendimiento Global Consolidado",
        "brief_sec1_box":     "* **Volumen Total de Taquilla:**",
        "brief_sec1_tix":     "* **Volumen de Entradas Proyectado:**",
        "brief_sec1_csat":    "* **Índice de Retención & Satisfacción:** 88% (Puntuación Excelente).",
        "brief_sec2_title":   "#### 2. Hallazgos Clave de Exhibición y Marketing",
        "brief_sec2_imax":    "* **Prima de Gran Formato (IMAX / PLF):** +41.4% de recaudación comparado con salas estándar.",
        "brief_sec2_roi":     "* **Eficiencia de Campañas:** El canal Digital rinde a **3.80x ROI**, superando a la televisión tradicional (**2.20x ROI**).",
        "brief_sec2_geo":     "* **Foco Territorial:** Fuerte tracción en preventa en México, España y Norteamérica.",
        "brief_sec3_title":   "#### 3. Acciones Inmediatas Recomendadas",
        "brief_sec3_rec1":    "1. Escalar inversión en marketing digital y video vertical (TikTok/Instagram) para el target de 18-34 años.",
        "brief_sec3_rec2":    "2. Asegurar contratos de retención en salas IMAX para las semanas 2 y 3.",
        "brief_download_btn": "💾 Descargar Briefing (.md)",
        # KPI strip
        "kpi_box_office":     "🌍 Taquilla Global",
        "kpi_tickets":        "🎟️ Entradas Vendidas",
        "kpi_sentiment":      "💬 Sent. Positivo",
        "kpi_films":          "🎞️ Películas Activas",
        "kpi_viewers":        "👁️ Viewers Live",
        # Card titles
        "c_box_office":       "📈 EVOLUCIÓN TEMPORAL DE TAQUILLA",
        "c_engagement":       "🎯 ENGAGEMENT DE AUDIENCIA",
        "c_sat_score":        "PUNTUACIÓN DE SATISFACCIÓN",
        "c_sat_sub":          "↑ 3pts vs media histórica",
        "c_demo":             "👥 DEMOGRAFÍA & AUDIENCIA",
        "c_traffic":          "👁️ TRÁFICO EN TIEMPO REAL",
        "c_viewers":          "Espectadores Actuales",
        "c_markets":          "MERCADOS",
        "c_avg":              "PROM. VIS.",
        "c_releases":         "🎬 PRÓXIMOS ESTRENOS",
        "c_regional":         "🌍 RENDIMIENTO REGIONAL",
        "c_sentiment":        "💬 SENTIMIENTO SOCIAL",
        "c_positive":         "POSITIVO 74%",
        "c_predict":          "🤖 PREDICCIONES IA",
        # Sentiment bars
        "sent_bars": [
            ("Hype & Viralidad", 74, "#BF00FF"),
            ("Aclamación Crítica", 68, "#00FF9F"),
            ("Anticipación Preventa", 81, "#00F5FF"),
            ("Buzz en Redes", 55, "#FF2D78"),
        ],
        "sent_hype":          "Hype",
        "sent_mast":          "Aclamación",
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
             "Proyección abre en $200M+. IMAX agotado en 12 mercados clave.",
             "CONF: 91%"),
            ("Campaña Digital MX",
             "ROI estimado 3.8x. Recomendada escalación de presupuesto.",
             "CONF: 87%"),
            ("Alerta de Sostenibilidad",
             "La Mansión: riesgo de caída post-premiere (-58%). Reforzar social ads.",
             "CONF: 78%"),
        ],
        "weeks_eng":          ["Sem 1", "Sem 2", "Sem 3", "Sem 4", "Sem 5", "Sem 6", "Sem 7", "Sem 8", "Sem 9", "Sem 10", "Sem 11", "Sem 12"],
        "donut_center":       "88%\nSCORE",
        "hover_ticket":       "Período %{x}: %{y}%",
        "badge_wknd":         "▲ 22% vs Media",
        "best_week":          "Mejor semana del período",
        "live_pct":           "▲ 8% EN VIVO",
        # Simulator
        "sim_title":          "🎮 SIMULADOR DE LANZAMIENTOS & IMPACTO DE MARKETING",
        "sim_desc":           "Modela variables clave de marketing y exhibición para predecir la recaudación del fin de semana de apertura (Opening Weekend) y el ROI.",
        "sim_genres":         ["Sci-Fi / Blockbuster", "Acción & Franquicia", "Drama / Autor", "Terror / Suspenso"],
        "sim_budget_dig":     "Presupuesto Marketing Digital (€M)",
        "sim_budget_tv":      "Presupuesto Marketing TV (€M)",
        "sim_imax_share":     "Asignación de Pantallas IMAX / PLF (%)",
        "sim_release_win":    "Ventana de Exclusividad en Cines (Días)",
        "sim_genre_sel":      "Género Principal",
        "sim_proj_open":      "RECAUDACIÓN ESTIMADA OPENING",
        "sim_sub_open":       "Recaudación Fin de Semana de Apertura",
        "sim_proj_roi":       "ROI DE MARKETING ESPERADO",
        "sim_sub_roi":        "Ratio de Eficiencia de Campaña",
        "sim_imax_boost":     "IMPACTO PREMIUM IMAX",
        "sim_sub_boost":      "Prima de Gran Formato (PLF)",
        "sim_decay_curve":    "📈 CURVA DE DECAIMIENTO PROYECTADA (5 SEMANAS)",
        "sim_decay_weeks":    ["Sem 1 (Estreno)", "Sem 2", "Sem 3", "Sem 4", "Sem 5"],
        # News Radar
        "news_title":         "📰 RADAR DE NOTICIAS DE LA INDUSTRIA & ANÁLISIS DE IMPACTO IA",
        "news_desc":          "Monitor en tiempo real de eventos de Hollywood, exhibición y distribución con enlaces directos y evaluación de impacto financiero generada por Gemini.",
        "news_btn_refresh":   "🔄 Actualizar Radar de Noticias",
        "news_impact_tag":    "EVALUACIÓN DE IMPACTO IA:",
        "news_read_btn":      "🔗 Leer Noticia Completa en",
        "news_custom_title":  "💡 EVALUADOR DE NOTICIAS & RUMORES PERSONALIZADO",
        "news_custom_desc":   "Pega cualquier titular, anuncio o rumor cinematográfico para que Gemini analice su impacto financiero previsto:",
        "news_custom_btn":    "🚀 Analizar Impacto en Taquilla",
        "news_custom_ph":     "Ej: Warner Bros anuncia que rodará la secuela de Dune íntegramente en formato IMAX para Noviembre 2027...",
        "news_spinner":       "🧠 Gemini analizando impacto económico y taquillero...",
        "news_card_custom_lbl": "ANÁLISIS PERSONALIZADO GEMINI AI",
        # AI Chat tab
        "chat_title":         "🤖 GEMINI AI ANALYST · CONSULTA EN LENGUAJE NATURAL",
        "ch_toggle":          "ClickHouse Real",
        "ch_help":            "Activa para conectar al servidor MCP de ClickHouse real",
        "clear_btn":          "🗑️ LIMPIAR",
        "send_btn":           "ENVIAR →",
        "chat_placeholder":   "Ej: ¿Cuáles son los 5 mercados con mayor taquilla este trimestre?",
        "chat_empty_icon":    "💬",
        "chat_empty_text":    "ESPERANDO CONSULTA · ESCRIBE UNA PREGUNTA",
        "spinner_text":       "🎬 Analizando consulta con Gemini…",
        "data_expand":        "📊 DATOS · Resultado ClickHouse",
        "sql_expand":         "🔍 SQL GENERADO POR GEMINI",
        "mcp_tool":           "Herramienta MCP",
        "sdk_caption":        "Gemini genera SQL automáticamente · Protocolo MCP ClickHouse · Google GenAI SDK",
        "examples": [
            "¿Cuántas entradas se vendieron en España?",
            "¿Qué formato genera más ingresos: IMAX o 3D?",
            "¿ROI de campañas digitales vs TV?",
            "¿Top 5 películas por recaudación?",
            "¿Público objetivo 18-34 por mercado?",
        ],
    },
    "EN": {
        # Header
        "sys_subtitle":       "BOX OFFICE & MARKETING INTELLIGENCE SYSTEM · v3.5",
        "live_label":         "LIVE",
        "mode_demo":          "DEMO MODE",
        "mode_live":          "CLICKHOUSE LIVE",
        # Tabs
        "tab_dashboard":      "📊  DASHBOARD",
        "tab_simulator":      "🎮  WHAT-IF SIMULATOR",
        "tab_news":           "📰  NEWS & RADAR",
        "tab_ai":             "🤖  AI ANALYST",
        # Quick Filters
        "flt_genre":          "Genre",
        "flt_territory":      "Territory",
        "flt_period":         "Period",
        "all_genres":         ["All Genres", "Sci-Fi / Fiction", "Action & Adventure", "Drama", "Horror / Thriller", "Animation"],
        "all_territories":    ["Global", "North America (US/CA)", "Europe (EU)", "Asia-Pacific", "Latin America"],
        "all_periods":        ["Current Quarter (Q3)", "Last 12 Months", "Q4 Forecast", "Historical 2025-2026"],
        "btn_export_brief":   "📄 Export Executive Briefing",
        # Briefing
        "brief_title":        "📄 EXECUTIVE STRATEGY BRIEFING · DOWNLOADABLE",
        "brief_header":       "### 🎬 CINEMETRICS AI · EXECUTIVE STRATEGY BRIEFING",
        "brief_date_lbl":     "Issue Date",
        "brief_filters_lbl":  "Active Filters",
        "brief_sec1_title":   "#### 1. Consolidated Global Performance",
        "brief_sec1_box":     "* **Total Box Office Gross:**",
        "brief_sec1_tix":     "* **Projected Ticket Volume:**",
        "brief_sec1_csat":    "* **Audience Retention & CSAT Score:** 88% (Excellent Tier).",
        "brief_sec2_title":   "#### 2. Key Exhibition & Marketing Insights",
        "brief_sec2_imax":    "* **Premium Large Format (IMAX / PLF) Lift:** +41.4% gross revenue compared to standard auditoriums.",
        "brief_sec2_roi":     "* **Campaign Efficiency:** Digital channels deliver **3.80x ROI**, significantly outpacing linear TV (**2.20x ROI**).",
        "brief_sec2_geo":     "* **Territorial Focus:** Strong presale momentum in Mexico, Spain, and North America.",
        "brief_sec3_title":   "#### 3. Immediate Recommended Actions",
        "brief_sec3_rec1":    "1. Scale budget allocation toward vertical video social channels (TikTok/Instagram) for the 18-34 demo.",
        "brief_sec3_rec2":    "2. Secure extended 2nd and 3rd week theatrical holds in IMAX screens.",
        "brief_download_btn": "💾 Download Briefing (.md)",
        # KPI strip
        "kpi_box_office":     "🌍 Global Box Office",
        "kpi_tickets":        "🎟️ Total Tickets Sold",
        "kpi_sentiment":      "💬 Positive Sent.",
        "kpi_films":          "🎞️ Active Films",
        "kpi_viewers":        "👁️ Live Viewers",
        # Card titles
        "c_box_office":       "📈 BOX OFFICE TIMELINE & EVOLUTION",
        "c_engagement":       "🎯 AUDIENCE ENGAGEMENT",
        "c_sat_score":        "SATISFACTION SCORE",
        "c_sat_sub":          "↑ 3pts vs historical average",
        "c_demo":             "👥 DEMOGRAPHICS & AUDIENCE",
        "c_traffic":          "👁️ REAL-TIME TRAFFIC",
        "c_viewers":          "Current Viewers",
        "c_markets":          "MARKETS",
        "c_avg":              "AVG VIEW",
        "c_releases":         "🎬 UPCOMING RELEASES",
        "c_regional":         "🌍 REGIONAL PERFORMANCE",
        "c_sentiment":        "💬 SOCIAL SENTIMENT",
        "c_positive":         "POSITIVE 74%",
        "c_predict":          "🤖 AI PREDICTIONS",
        # Sentiment bars
        "sent_bars": [
            ("Hype & Virality", 74, "#BF00FF"),
            ("Critical Acclaim", 68, "#00FF9F"),
            ("Presale Anticipation", 81, "#00F5FF"),
            ("Social Buzz", 55, "#FF2D78"),
        ],
        "sent_hype":          "Hype",
        "sent_mast":          "Acclaim",
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
             "Opening projected $200M+. IMAX sold out in 12 key markets.",
             "CONF: 91%"),
            ("Digital Campaign MX",
             "Projected ROI 3.8x. Recommended budget expansion.",
             "CONF: 87%"),
            ("Sustainability Alert",
             "La Mansión: high post-premiere drop risk (-58%). Boost social ads.",
             "CONF: 78%"),
        ],
        "weeks_eng":          ["Wk 1", "Wk 2", "Wk 3", "Wk 4", "Wk 5", "Wk 6", "Wk 7", "Wk 8", "Wk 9", "Wk 10", "Wk 11", "Wk 12"],
        "donut_center":       "88%\nSCORE",
        "hover_ticket":       "Period %{x}: %{y}%",
        "badge_wknd":         "▲ 22% vs Avg",
        "best_week":          "Best week of the period",
        "live_pct":           "▲ 8% LIVE",
        # Simulator
        "sim_title":          "🎮 BOX OFFICE & MARKETING WHAT-IF SIMULATOR",
        "sim_desc":           "Model key marketing spend and exhibition variables to forecast opening weekend gross and promotional ROI in real time.",
        "sim_genres":         ["Sci-Fi / Blockbuster", "Action & Franchise", "Drama / Auteur", "Horror / Suspense"],
        "sim_budget_dig":     "Digital Marketing Budget ($M)",
        "sim_budget_tv":      "TV Marketing Budget ($M)",
        "sim_imax_share":     "IMAX / PLF Screen Allocation (%)",
        "sim_release_win":    "Theatrical Exclusivity Window (Days)",
        "sim_genre_sel":      "Primary Film Genre",
        "sim_proj_open":      "ESTIMATED OPENING WEEKEND",
        "sim_sub_open":       "Opening Weekend Projected Gross",
        "sim_proj_roi":       "EXPECTED CAMPAIGN ROI",
        "sim_sub_roi":        "Marketing Efficiency Ratio",
        "sim_imax_boost":     "PREMIUM FORMAT BOOST",
        "sim_sub_boost":      "PLF Premium Revenue Lift",
        "sim_decay_curve":    "📈 5-WEEK PROJECTED DECAY CURVE",
        "sim_decay_weeks":    ["Wk 1 (Opening)", "Wk 2", "Wk 3", "Wk 4", "Wk 5"],
        # News Radar
        "news_title":         "📰 INDUSTRY NEWS RADAR & AI IMPACT ASSESSMENT",
        "news_desc":          "Real-time tracking of Hollywood events, exhibition trends, and studio announcements with direct source links and financial impact analyses by Gemini.",
        "news_btn_refresh":   "🔄 Refresh News Radar",
        "news_impact_tag":    "AI IMPACT ASSESSMENT:",
        "news_read_btn":      "🔗 Read Full Article on",
        "news_custom_title":  "💡 CUSTOM FILM NEWS & RUMOR ANALYZER",
        "news_custom_desc":   "Paste any headline, studio announcement, or rumor to let Gemini evaluate its projected box office impact:",
        "news_custom_btn":    "🚀 Evaluate Box Office Impact",
        "news_custom_ph":     "E.g.: Warner Bros announces that Dune sequel will be shot entirely in 70mm IMAX for November 2027...",
        "news_spinner":       "🧠 Gemini analyzing box office and financial impact...",
        "news_card_custom_lbl": "CUSTOM GEMINI AI ANALYSIS",
        # AI Chat tab
        "chat_title":         "🤖 GEMINI AI ANALYST · NATURAL LANGUAGE QUERY",
        "ch_toggle":          "Real ClickHouse",
        "ch_help":            "Enable to connect to the real MCP ClickHouse server",
        "clear_btn":          "🗑️ CLEAR",
        "send_btn":           "SEND →",
        "chat_placeholder":   "E.g.: What are the top 5 markets by box office this quarter?",
        "chat_empty_icon":    "💬",
        "chat_empty_text":    "AWAITING QUERY · TYPE A QUESTION BELOW",
        "spinner_text":       "🎬 Analyzing query with Gemini…",
        "data_expand":        "📊 DATA · ClickHouse Result",
        "sql_expand":         "🔍 SQL GENERATED BY GEMINI",
        "mcp_tool":           "MCP Tool",
        "sdk_caption":        "Gemini auto-generates SQL · ClickHouse MCP Protocol · Google GenAI SDK",
        "examples": [
            "How many tickets were sold in Spain?",
            "Which format earns more revenue: IMAX or 3D?",
            "ROI of digital campaigns vs TV?",
            "Top 5 films by box office gross?",
            "Target audience 18-34 by market?",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# BILINGUAL NEWS FEEDS WITH DIRECT URLS
# ─────────────────────────────────────────────────────────────────────────────
NEWS_FEEDS: dict[str, dict[int, list[dict]]] = {
    "ES": {
        1: [
            {
                "id": "news_1",
                "source": "VARIETY · EXHIBITION RADAR",
                "source_name": "Variety",
                "url": "https://variety.com/v/film/box-office/",
                "headline": "IMAX expande su red global con 120 nuevas salas premium en Asia y Latinoamérica",
                "date": "Hace 15 min · Mercado Global",
                "body": "La compañía de gran formato anuncia acuerdos de expansión con cadenas de exhibición en Japón, Corea y México ante la demanda récord de entradas para franquicias de ciencia ficción.",
                "ai_impact": "📈 **Impacto Proyectado:** +18% en recaudación internacional para blockbusters en Q4. Se recomienda negociar ventanas extendidas de exclusividad PLF de al menos 3 semanas.",
            },
            {
                "id": "news_2",
                "source": "DEADLINE · MARKETING SHIFT",
                "source_name": "Deadline",
                "url": "https://deadline.com/v/box-office/",
                "headline": "Los estudios de Hollywood reducen un 30% el gasto en TV tradicional en favor de TikTok y streaming ads",
                "date": "Hace 1 hora · Estrategia",
                "body": "Nuevos reportes confirman que el costo por adquisición de audiencia juvenil (18-34 años) es 3.2 veces más eficiente en plataformas sociales que en televisión lineal abierta.",
                "ai_impact": "💡 **Acción Sugerida:** Reasignar presupuesto de campañas otoño/invierno hacia micro-influencers de cine y compra programática de video vertical para maximizar el ROI.",
            },
            {
                "id": "news_3",
                "source": "BOXOFFICE PRO · BOX OFFICE PULSE",
                "source_name": "BoxOffice Pro",
                "url": "https://www.boxofficepro.com/",
                "headline": "Las preventas de 'Galactic Odyssey 2' superan los 85M$ en su primera semana",
                "date": "Hace 3 horas · Taquilla",
                "body": "La secuela espacial apunta a un fin de semana de apertura global superior a los 220M$, impulsada por una retención del 95% en salas de gran formato.",
                "ai_impact": "🎯 **Proyección:** Probabilidad del 91% de superar el récord trimestral de taquilla. Riesgo bajo de canibalización con títulos competidores en su ventana de estreno.",
            },
        ],
        2: [
            {
                "id": "news_4",
                "source": "THE HOLLYWOOD REPORTER · TRENDS",
                "source_name": "The Hollywood Reporter",
                "url": "https://www.hollywoodreporter.com/c/movies/movie-news/",
                "headline": "El público post-pandemia consolida el hábito de acudir a salas solo para eventos cinematográficos masivos",
                "date": "Actualizado ahora · Tendencias",
                "body": "Un estudio revela que el 72% de los espectadores de entre 18 y 45 años reservan su entrada exclusivamente en formatos inmersivos (IMAX, 4DX, Dolby Cinema).",
                "ai_impact": "🔥 **Oportunidad:** Fortalecer el ticket medio con paquetes de preventa con merchandising exclusivo y pases de medianoche.",
            },
            {
                "id": "news_5",
                "source": "SCREEN DAILY · EUROPEAN BOX OFFICE",
                "source_name": "Screen Daily",
                "url": "https://www.screendaily.com/box-office",
                "headline": "España y Francia lideran el crecimiento de cuota de pantalla en Europa este trimestre (+14%)",
                "date": "Hace 45 min · Europa",
                "body": "Las campañas promocionales de Fiesta del Cine y las preventas escalonadas impulsan la afluencia en salas en el sur de Europa a máximos del año.",
                "ai_impact": "🇪🇸 **Estrategia Local:** Reforzar la distribución en copias dobladas y subtituladas en Cataluña, Madrid y Andalucía para capturar el pico de demanda de otoño.",
            },
        ]
    },
    "EN": {
        1: [
            {
                "id": "news_1",
                "source": "VARIETY · EXHIBITION RADAR",
                "source_name": "Variety",
                "url": "https://variety.com/v/film/box-office/",
                "headline": "IMAX Expands Global Footprint with 120 New Premium Auditoriums in Asia and Latin America",
                "date": "15 min ago · Global Market",
                "body": "The large-format giant announces major multi-territory pacts with leading theatrical circuits across Japan, South Korea, and Mexico following historic presale demand for sci-fi franchises.",
                "ai_impact": "📈 **Projected Impact:** +18% lift in international gross for Q4 blockbusters. Exhibitors are advised to lock in minimum 3-week PLF exclusive window holds.",
            },
            {
                "id": "news_2",
                "source": "DEADLINE · MARKETING SHIFT",
                "source_name": "Deadline",
                "url": "https://deadline.com/v/box-office/",
                "headline": "Hollywood Studios Shift 30% of Traditional Broadcast Ad Spend to TikTok & Vertical Video",
                "date": "1 hour ago · Marketing Strategy",
                "body": "Industry audits reveal customer acquisition costs for the 18-34 demographic are 3.2x more cost-effective across short-form video channels than linear network television.",
                "ai_impact": "💡 **Strategic Action:** Reallocate fall/winter campaign reserves into programmatic vertical video and creator networks to maximize promotional ROI.",
            },
            {
                "id": "news_3",
                "source": "BOXOFFICE PRO · BOX OFFICE PULSE",
                "source_name": "BoxOffice Pro",
                "url": "https://www.boxofficepro.com/",
                "headline": "'Galactic Odyssey 2' Advanced Presales Cross $85M in Opening Tracking Week",
                "date": "3 hours ago · Theatrical Tracking",
                "body": "The sci-fi tentpole is pacing toward a massive $220M+ worldwide launch, driven by a blistering 95% occupancy rate across premium large format screens.",
                "ai_impact": "🎯 **Forecast:** 91% probability of setting a new quarter record. Low counter-programming cannibalization risk within its primary theatrical corridor.",
            },
        ],
        2: [
            {
                "id": "news_4",
                "source": "THE HOLLYWOOD REPORTER · TRENDS",
                "source_name": "The Hollywood Reporter",
                "url": "https://www.hollywoodreporter.com/c/movies/movie-news/",
                "headline": "Theatrical Audiences Solidify Habit of Reserving Cinema Visits Strictly for Event Blockbusters",
                "date": "Just updated · Exhibition Trends",
                "body": "New survey data shows 72% of moviegoers aged 18-45 now reserve tickets exclusively for premium experiential formats (IMAX, 4DX, Dolby Cinema).",
                "ai_impact": "🔥 **Revenue Opportunity:** Bolster per-patron average spend through commemorative collectible tickets and premium midnight fan previews.",
            },
            {
                "id": "news_5",
                "source": "SCREEN DAILY · EUROPEAN BOX OFFICE",
                "source_name": "Screen Daily",
                "url": "https://www.screendaily.com/box-office",
                "headline": "Spain and France Propel European Box Office Growth This Quarter (+14% YoY)",
                "date": "45 min ago · European Market",
                "body": "National discount cinema festivals and coordinated multi-territory marketing initiatives push Southern European admissions to yearly highs.",
                "ai_impact": "🇪🇸 **Territory Playbook:** Reinforce targeted digital marketing and dubbing distribution across major metropolitan hubs to capture autumn momentum.",
            },
        ]
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# CSS · NEON HOLOGRAPHIC THEME
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
    --neon-gold:    #FFD700;
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
.block-container{padding:0.8rem 1.5rem 2rem!important;max-width:100%!important}

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
.hud-dot{width:7px;height:7px;border-radius:50%;background:var(--neon-green);
    box-shadow:0 0 8px var(--neon-green),0 0 20px var(--neon-green);
    display:inline-block;margin-right:5px;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{
    background:rgba(0,13,30,.95)!important;
    border-bottom:1px solid var(--border-dim)!important;
    gap:4px;padding:0 8px;
}
.stTabs [data-baseweb="tab"]{
    font-family:var(--font-hud)!important;font-size:.68rem!important;
    letter-spacing:.12em!important;color:var(--text-dim)!important;
    padding:10px 18px!important;border:none!important;background:transparent!important;
    border-bottom:2px solid transparent!important;transition:all .2s!important;
}
.stTabs [aria-selected="true"]{
    color:var(--neon-cyan)!important;border-bottom:2px solid var(--neon-cyan)!important;
    text-shadow:0 0 8px var(--neon-cyan)!important;background:rgba(0,245,255,.05)!important;
}
.stTabs [data-baseweb="tab-panel"]{background:transparent!important;padding:0!important;}

/* Neon Cards */
.neon-card{
    background:var(--bg-card);border:1px solid var(--border-dim);
    border-radius:6px;padding:14px;position:relative;overflow:hidden;
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
.neon-card.gold::before{background:linear-gradient(90deg,transparent,var(--neon-gold),transparent);}

/* Card title */
.card-title{font-family:var(--font-hud);font-size:.65rem;letter-spacing:.14em;
    text-transform:uppercase;color:var(--text-dim);margin-bottom:6px;}
.card-title.cyan  {color:var(--neon-cyan);  text-shadow:0 0 6px var(--neon-cyan);}
.card-title.purple{color:var(--neon-purple);text-shadow:0 0 6px var(--neon-purple);}
.card-title.pink  {color:var(--neon-pink);  text-shadow:0 0 6px var(--neon-pink);}
.card-title.green {color:var(--neon-green); text-shadow:0 0 6px var(--neon-green);}
.card-title.gold  {color:var(--neon-gold);  text-shadow:0 0 6px var(--neon-gold);}

/* Big metric */
.big-metric{
    font-family:var(--font-hud);font-size:2.3rem;font-weight:900;line-height:1;
    color:var(--neon-cyan);text-shadow:0 0 20px var(--neon-cyan),0 0 50px rgba(0,245,255,.4);
    margin:8px 0 4px;
}
.big-metric.purple{color:var(--neon-purple);text-shadow:0 0 20px var(--neon-purple),0 0 50px rgba(191,0,255,.4);}
.big-metric.green {color:var(--neon-green); text-shadow:0 0 20px var(--neon-green), 0 0 50px rgba(0,255,159,.4);}
.big-metric.pink  {color:var(--neon-pink);  text-shadow:0 0 20px var(--neon-pink), 0 0 50px rgba(255,45,120,.4);}
.big-metric.gold  {color:var(--neon-gold);  text-shadow:0 0 20px var(--neon-gold), 0 0 50px rgba(255,215,0,.4);}
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

/* News Cards & Links */
.news-card{
    background:var(--bg-card2);border:1px solid var(--border-dim);
    border-radius:6px;padding:16px;margin-bottom:14px;transition:all 0.2s;
    position:relative;
}
.news-card:hover{border-color:var(--neon-cyan);box-shadow:0 0 15px rgba(0,245,255,.12);}
.news-source{font-family:var(--font-hud);font-size:.62rem;color:var(--neon-cyan);letter-spacing:.1em;}
.news-headline{font-size:1rem;font-weight:700;color:var(--text-bright);margin:6px 0;}
.news-summary{font-size:.82rem;color:var(--text-dim);line-height:1.5;}
.news-impact-box{
    margin-top:12px;padding:12px 14px;background:rgba(191,0,255,.08);
    border-left:3px solid var(--neon-purple);border-radius:0 4px 4px 0;
    font-size:.82rem;color:#E9D5FF;line-height:1.6;
}
.news-link-btn{
    display:inline-flex;align-items:center;gap:6px;margin-top:10px;
    padding:5px 12px;background:rgba(0,245,255,.08);border:1px solid rgba(0,245,255,.3);
    border-radius:4px;color:#00F5FF!important;text-decoration:none!important;
    font-family:var(--font-hud);font-size:.62rem;letter-spacing:.08em;transition:all 0.2s;
}
.news-link-btn:hover{background:rgba(0,245,255,.2);box-shadow:0 0 10px rgba(0,245,255,.3);color:#fff!important;}

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

/* Form Inputs & Sliders */
.stSlider > div > div > div > div { background-color: var(--neon-cyan) !important; }
.stSelectbox > div > div { background-color: rgba(0,13,30,.9) !important; border-color: var(--border-dim) !important; }
.stTextInput>div>div>input{
    background:rgba(0,13,30,.9)!important;border:1px solid var(--border-dim)!important;
    border-radius:4px!important;color:var(--text-bright)!important;
    font-family:var(--font-body)!important;font-size:.95rem!important;
}
.stButton>button{
    background:linear-gradient(135deg,rgba(0,245,255,.15),rgba(191,0,255,.15))!important;
    border:1px solid var(--neon-cyan)!important;color:var(--neon-cyan)!important;
    font-family:var(--font-hud)!important;font-size:.68rem!important;letter-spacing:.1em!important;
    border-radius:4px!important;transition:all .2s!important;
}
.stButton>button:hover{background:rgba(0,245,255,.25)!important;box-shadow:0 0 15px rgba(0,245,255,.3)!important;}
[data-testid="stDataFrame"]{border-radius:6px;overflow:hidden;}
[data-testid="stExpander"]{background:var(--bg-card2)!important;border:1px solid var(--border-dim)!important;border-radius:4px!important;}
.stSpinner>div{border-top-color:var(--neon-cyan)!important;}
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
        "lang":          "ES",
        "news_feed_ver": 1,
        "custom_evals":  [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()
t = TRANSLATIONS[st.session_state.lang]

# ─────────────────────────────────────────────────────────────────────────────
# CHART HELPERS (DYNAMIC TIMELINE BASED ON PERIOD / GENRE / TERRITORY)
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
_Y_BASE = dict(gridcolor="rgba(0,245,255,0.06)", zerolinecolor="rgba(0,245,255,0.1)", tickfont=dict(color="#5A7A9A", size=9))


def get_timeline_data(period_sel: str, genre_mult: float, terr_mult: float, lang: str):
    """Calcula etiquetas temporales y valores en base al período seleccionado e idioma."""
    base_mult = genre_mult * terr_mult

    if "12 Meses" in period_sel or "12 Months" in period_sel:
        ticks = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"] if lang == "ES" else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        base_vals = [280, 310, 390, 420, 580, 690, 750, 620, 480, 510, 680, 890]
        peak_idx = 11
        peak_label = "Dic Peak" if lang == "ES" else "Dec Peak"
    elif "Q4" in period_sel or "Forecast" in period_sel:
        ticks = ["Sem 40", "Sem 41", "Sem 42", "Sem 43", "Sem 44", "Sem 45", "Navidad"] if lang == "ES" else ["Wk 40", "Wk 41", "Wk 42", "Wk 43", "Wk 44", "Wk 45", "Holidays"]
        base_vals = [190, 240, 290, 360, 410, 480, 620]
        peak_idx = 6
        peak_label = "Navidad Peak" if lang == "ES" else "Holiday Peak"
    elif "Histórico" in period_sel or "Historical" in period_sel:
        ticks = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26", "Q2'26", "Q3'26", "Q4'26"]
        base_vals = [1200, 1450, 1680, 2100, 1380, 1590, 1850, 2350]
        peak_idx = 7
        peak_label = "Q4'26 Proy." if lang == "ES" else "Q4'26 Proj."
    else:
        # Default Q3 (5 semanas)
        ticks = ["Sem 1", "Sem 2", "Sem 3", "Sem 4", "Sem 5"] if lang == "ES" else ["Wk 1", "Wk 2", "Wk 3", "Wk 4", "Wk 5"]
        base_vals = [148, 221, 312, 278, 355]
        peak_idx = 2
        peak_label = "Sem 3 Peak" if lang == "ES" else "Wk 3 Peak"

    vals = [round(v * base_mult, 1) for v in base_vals]
    return ticks, vals, peak_idx, peak_label


def chart_box_office_dynamic(ticks: list, vals: list, peak_idx: int, peak_label: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ticks, y=vals, mode="lines+markers",
        fill="tozeroy", fillcolor="rgba(0,245,255,0.07)",
        line=dict(color="#00F5FF", width=2.5, shape="spline"),
        marker=dict(color="#00F5FF", size=6, line=dict(color="#001A2E", width=2)),
        name="Box Office", hovertemplate="%{y}M$<extra></extra>",
    ))
    fig.add_annotation(
        x=ticks[peak_idx], y=vals[peak_idx], text=f"▲ {peak_label}: ${vals[peak_idx]}M",
        font=dict(color="#00FF9F", size=9, family="Orbitron"),
        showarrow=False, yshift=14,
        bgcolor="rgba(0,255,159,0.12)", bordercolor="rgba(0,255,159,0.4)",
        borderwidth=1, borderpad=4,
    )
    fig.update_layout(**PLOTLY_BASE)
    fig.update_layout(
        height=170,
        yaxis=dict(**_Y_BASE, tickprefix="$", ticksuffix="M", range=[0, max(vals) * 1.35]),
    )
    return fig


def chart_regional(t: dict, multiplier: float = 1.0) -> go.Figure:
    regions = ["US", "EU", "ASIA", "LATAM", "MEA"]
    values  = [round(450 * multiplier), round(380 * multiplier), round(620 * multiplier), round(195 * multiplier), round(142 * multiplier)]
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
        marker=dict(colors=["#00F5FF", "#BF00FF", "#FF2D78"], line=dict(color="#020813", width=3)),
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


def chart_engagement(t: dict, multiplier: float = 1.0) -> go.Figure:
    vals = [round(min(100, v * (0.85 + 0.15 * multiplier))) for v in [62, 71, 58, 88, 75, 90, 83, 95, 79, 88, 91, 97]]
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


def chart_simulator_decay(opening_m: float, week_labels: list) -> go.Figure:
    gross = [
        round(opening_m, 1),
        round(opening_m * 0.52, 1),
        round(opening_m * 0.31, 1),
        round(opening_m * 0.19, 1),
        round(opening_m * 0.12, 1),
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=week_labels, y=gross, mode="lines+markers+text",
        text=[f"${g}M" for g in gross], textposition="top center",
        textfont=dict(family="Orbitron", size=10, color="#00F5FF"),
        line=dict(color="#00F5FF", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(0,245,255,0.08)",
        marker=dict(size=8, color="#BF00FF", line=dict(color="#00F5FF", width=2)),
        hovertemplate="%{x}: $%{y}M<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_BASE)
    fig.update_layout(
        height=220,
        yaxis=dict(**_Y_BASE, tickprefix="$", ticksuffix="M", range=[0, max(gross) * 1.35]),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# HEADER & LANGUAGE SWITCHER
# ─────────────────────────────────────────────────────────────────────────────
now = datetime.now()
mode_lbl = t["mode_demo"] if st.session_state.use_mock else t["mode_live"]

hdr_left, hdr_lang, hdr_right = st.columns([4.2, 1.2, 1.8])

with hdr_left:
    st.markdown(f"""
    <div style="padding:10px 0 6px;">
        <p class="hud-title">🎬 <span>CINE</span>METRICS · AI</p>
        <p class="hud-subtitle">{t["sys_subtitle"]}</p>
    </div>
    """, unsafe_allow_html=True)

with hdr_lang:
    st.markdown("<div style='padding-top:12px;'>", unsafe_allow_html=True)
    l1, l2 = st.columns(2)
    with l1:
        if st.button("🇪🇸 ES", key="btn_es", use_container_width=True):
            st.session_state.lang = "ES"
            st.rerun()
    with l2:
        if st.button("🇬🇧 EN", key="btn_en", use_container_width=True):
            st.session_state.lang = "EN"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with hdr_right:
    st.markdown(f"""
    <div style="text-align:right;padding:10px 0 6px;
                font-family:'Orbitron',monospace;font-size:.6rem;
                color:#5A7A9A;letter-spacing:.1em;line-height:1.7;">
        <span class="hud-dot"></span><strong style="color:#00F5FF">{t["live_label"]}</strong><br>
        {now.strftime('%Y-%m-%d · %H:%M:%S')}<br>
        {mode_lbl}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='border-top:1px solid rgba(0,245,255,.15);margin-bottom:8px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_dash, tab_sim, tab_news, tab_ai = st.tabs([
    t["tab_dashboard"],
    t["tab_simulator"],
    t["tab_news"],
    t["tab_ai"],
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 · DASHBOARD (FILTROS REACTIVOS Y PROYECCIONES DINÁMICAS)
# ═════════════════════════════════════════════════════════════════════════════
with tab_dash:

    # ── FILTROS GLOBALES INTERACTIVOS ──────────────────────────────────────
    f1, f2, f3, f4 = st.columns([1.5, 1.5, 1.5, 1.5])
    with f1:
        sel_genre = st.selectbox("🎬 " + t["flt_genre"], t["all_genres"], key="sb_genre")
    with f2:
        sel_terr = st.selectbox("🌍 " + t["flt_territory"], t["all_territories"], key="sb_terr")
    with f3:
        sel_period = st.selectbox("📅 " + t["flt_period"], t["all_periods"], key="sb_period")
    with f4:
        st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
        if st.button("📥 " + t["btn_export_brief"], use_container_width=True):
            st.session_state["show_briefing_modal"] = True
        st.markdown("</div>", unsafe_allow_html=True)

    # ── FACTORES DE ESCALA DINÁMICOS POR FILTRO ────────────────────────────
    genre_mult = 1.35 if "Sci-Fi" in sel_genre else (1.20 if "Acción" in sel_genre or "Action" in sel_genre else (0.85 if "Terror" in sel_genre or "Horror" in sel_genre else 1.0))
    terr_mult = 0.55 if "Europe" in sel_terr or "Europa" in sel_terr else (0.75 if "Asia" in sel_terr else (0.40 if "Latino" in sel_terr or "Latin" in sel_terr else 1.0))

    # Factor de escala según período seleccionado
    if "12 Meses" in sel_period or "12 Months" in sel_period:
        period_factor = 2.6
        period_kpi_label = "$4.82B"
        tickets_kpi_label = "42.8M"
    elif "Q4" in sel_period or "Forecast" in sel_period:
        period_factor = 1.25
        period_kpi_label = "$2.31B"
        tickets_kpi_label = "21.6M"
    elif "Histórico" in sel_period or "Historical" in sel_period:
        period_factor = 5.2
        period_kpi_label = "$9.65B"
        tickets_kpi_label = "94.2M"
    else:
        # Q3 base
        period_factor = 1.0
        period_kpi_label = f"${round(1.85 * genre_mult * terr_mult, 2)}B"
        tickets_kpi_label = f"{round(18.4 * genre_mult * terr_mult, 1)}M"

    dyn_total_gross = f"${round(1.85 * genre_mult * terr_mult * (period_factor if period_factor <= 1.5 else 1.0), 2)}B"
    if period_factor > 1.5:
        dyn_total_gross = f"${round(float(period_kpi_label.replace('$','').replace('B','')) * genre_mult * terr_mult, 2)}B"

    dyn_ticks, dyn_vals, peak_idx, peak_label = get_timeline_data(sel_period, genre_mult, terr_mult, st.session_state.lang)

    # ── MODAL / EXPANDER DE BRIEFING EJECUTIVO (BILINGÜE) ─────────────────
    if st.session_state.get("show_briefing_modal", False):
        with st.expander(t["brief_title"], expanded=True):
            briefing_text = f"""{t["brief_header"]}
**{t["brief_date_lbl"]}:** {now.strftime('%d/%m/%Y %H:%M')} | **{t["brief_filters_lbl"]}:** {sel_genre} · {sel_terr} · {sel_period}

---
{t["brief_sec1_title"]}
{t["brief_sec1_box"]} {dyn_total_gross} ({sel_period}).
{t["brief_sec1_tix"]} {tickets_kpi_label} tickets.
{t["brief_sec1_csat"]}

{t["brief_sec2_title"]}
{t["brief_sec2_imax"]}
{t["brief_sec2_roi"]}
{t["brief_sec2_geo"]}

{t["brief_sec3_title"]}
{t["brief_sec3_rec1"]}
{t["brief_sec3_rec2"]}
"""
            st.markdown(briefing_text)
            st.download_button(
                t["brief_download_btn"],
                data=briefing_text,
                file_name=f"CineMetrics_Briefing_{now.strftime('%Y%m%d_%H%M')}_{st.session_state.lang}.md",
                mime="text/markdown",
            )

    # ── KPI STRIP DINÁMICO ─────────────────────────────────────────────────
    st.markdown(f"""
    <div class="mini-kpi-row">
        <div class="mini-kpi">
            <span class="mini-kpi-val">{dyn_total_gross}</span>
            <span class="mini-kpi-lbl">{t["kpi_box_office"]} ({sel_period[:10]})</span>
        </div>
        <div class="mini-kpi" style="border-color:rgba(191,0,255,.3);">
            <span class="mini-kpi-val" style="color:#BF00FF;text-shadow:0 0 8px #BF00FF;">{tickets_kpi_label}</span>
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
            <div class="card-title cyan">{t["c_box_office"]} · {sel_period.upper()}</div>
            <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:4px;">
                <span class="big-metric" style="font-size:1.8rem;">{dyn_total_gross}</span>
                <span class="metric-badge badge-up">{sel_genre}</span>
            </div>
            <div class="metric-sub">{peak_label}: ${dyn_vals[peak_idx]}M · {t["flt_territory"]}: {sel_terr}</div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_box_office_dynamic(dyn_ticks, dyn_vals, peak_idx, peak_label), use_container_width=True, config=CHART_CFG)

    with c2:
        st.markdown(f"""
        <div class="neon-card purple" style="margin-bottom:6px;">
            <div class="card-title purple">{t["c_engagement"]}</div>
            <div style="display:flex;align-items:baseline;gap:8px;">
                <span class="big-metric purple" style="font-size:1.5rem;">88%</span>
                <span class="metric-badge badge-up">{t["c_sat_score"]}</span>
            </div>
            <div class="metric-sub">{t["c_sat_sub"]}</div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_engagement(t, genre_mult), use_container_width=True, config=CHART_CFG)

        st.markdown(f"""
        <div class="neon-card" style="margin-bottom:0;padding:10px 14px;">
            <div class="card-title">{t["c_demo"]}</div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_demographics(t), use_container_width=True, config=CHART_CFG)

    with c3:
        st.markdown(f"""
        <div class="neon-card green" style="margin-bottom:6px;text-align:center;padding:16px;">
            <div class="card-title green">{t["c_traffic"]}</div>
            <div class="big-metric green" style="font-size:2.1rem;">21,450</div>
            <div class="metric-sub">{t["c_viewers"]}</div>
            <div style="margin-top:8px;">
                <span class="metric-badge badge-up">{t["live_pct"]}</span>
            </div>
            <div style="height:1px;background:rgba(0,255,159,.15);margin:10px 0;"></div>
            <div style="display:flex;justify-content:space-around;">
                <div>
                    <div style="font-family:'Orbitron',monospace;font-size:.85rem;color:#00FF9F;">47</div>
                    <div style="font-size:.6rem;color:#5A7A9A;">{t["c_markets"]}</div>
                </div>
                <div>
                    <div style="font-family:'Orbitron',monospace;font-size:.85rem;color:#00F5FF;">3.2s</div>
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
            <span class="release-score" style="background:rgba(0,245,255,.08);color:{c};border:1px solid rgba(0,245,255,.2);">
                {score}
            </span>
        </div>
        """ for title, date, c, score in t["releases"])

        st.markdown(f"""
        <div class="neon-card" style="padding:10px 12px;">
            <div class="card-title cyan" style="margin-bottom:6px;">{t["c_releases"]}</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)

    # ── FILA 2 ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns([2.0, 2.2, 1.5])

    with c4:
        st.markdown(f"""
        <div class="neon-card pink" style="margin-bottom:0;">
            <div class="card-title pink">{t["c_regional"]} · {sel_terr.upper()}</div>
            <div style="display:flex;gap:14px;margin-bottom:4px;">
                <div>
                    <span style="font-family:'Orbitron',monospace;font-size:.85rem;color:#FF2D78;">
                        ${round(620 * genre_mult * terr_mult)}M</span>
                    <span style="font-size:.6rem;color:#5A7A9A;"> ASIA</span>
                </div>
                <div>
                    <span style="font-family:'Orbitron',monospace;font-size:.85rem;color:#00F5FF;">
                        ${round(450 * genre_mult * terr_mult)}M</span>
                    <span style="font-size:.6rem;color:#5A7A9A;"> US</span>
                </div>
                <div>
                    <span style="font-family:'Orbitron',monospace;font-size:.85rem;color:#BF00FF;">
                        ${round(380 * genre_mult * terr_mult)}M</span>
                    <span style="font-size:.6rem;color:#5A7A9A;"> EU</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(chart_regional(t, genre_mult * terr_mult), use_container_width=True, config=CHART_CFG)

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
# TAB 2 · WHAT-IF SIMULATOR (100% BILINGÜE)
# ═════════════════════════════════════════════════════════════════════════════
with tab_sim:
    st.markdown(f"""
    <div style="padding:8px 0 14px;">
        <div style="font-family:'Orbitron',monospace;font-size:.85rem;color:#00F5FF;letter-spacing:.12em;">
            {t["sim_title"]}
        </div>
        <div style="color:#5A7A9A;font-size:.82rem;margin-top:4px;">
            {t["sim_desc"]}
        </div>
    </div>
    """, unsafe_allow_html=True)

    sim_c1, sim_c2 = st.columns([1.6, 2.4])

    with sim_c1:
        st.markdown('<div class="neon-card gold">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title gold">🎛️ {t["sim_title"]}</div>', unsafe_allow_html=True)

        sim_genre = st.selectbox(t["sim_genre_sel"], t["sim_genres"])
        sim_digital = st.slider(t["sim_budget_dig"], min_value=1.0, max_value=40.0, value=15.0, step=0.5)
        sim_tv = st.slider(t["sim_budget_tv"], min_value=1.0, max_value=50.0, value=20.0, step=0.5)
        sim_imax = st.slider(t["sim_imax_share"], min_value=5, max_value=60, value=30, step=5)
        sim_window = st.slider(t["sim_release_win"], min_value=30, max_value=120, value=45, step=5)
        st.markdown('</div>', unsafe_allow_html=True)

        # Cálculo del modelo predictivo en tiempo real
        genre_base = 45.0 if "Sci-Fi" in sim_genre else (38.0 if "Acción" in sim_genre or "Action" in sim_genre else 20.0)
        dig_impact = sim_digital * 3.8
        tv_impact  = sim_tv * 2.2
        imax_boost_val = (sim_imax / 100.0) * 0.42
        total_opening = (genre_base + (dig_impact + tv_impact) * 0.7) * (1.0 + imax_boost_val)
        total_spend = sim_digital + sim_tv
        predicted_roi = round(((dig_impact + tv_impact) / total_spend), 2)

    with sim_c2:
        # Scorecards proyectados
        st.markdown(f"""
        <div style="display:flex;gap:10px;margin-bottom:12px;">
            <div class="neon-card" style="flex:1;text-align:center;padding:16px;">
                <div class="card-title cyan">{t["sim_proj_open"]}</div>
                <div class="big-metric" style="font-size:2rem;">${round(total_opening, 1)}M</div>
                <div class="metric-sub">{t["sim_sub_open"]}</div>
            </div>
            <div class="neon-card green" style="flex:1;text-align:center;padding:16px;">
                <div class="card-title green">{t["sim_proj_roi"]}</div>
                <div class="big-metric green" style="font-size:2rem;">{predicted_roi}x</div>
                <div class="metric-sub">{t["sim_sub_roi"]}</div>
            </div>
            <div class="neon-card purple" style="flex:1;text-align:center;padding:16px;">
                <div class="card-title purple">{t["sim_imax_boost"]}</div>
                <div class="big-metric purple" style="font-size:2rem;">+{int(imax_boost_val * 100)}%</div>
                <div class="metric-sub">{t["sim_sub_boost"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="neon-card"><div class="card-title cyan">{t["sim_decay_curve"]}</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_simulator_decay(total_opening, t["sim_decay_weeks"]), use_container_width=True, config=CHART_CFG)
        st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 · INDUSTRY NEWS & RADAR (100% BILINGÜE CON LINKS CLICABLES)
# ═════════════════════════════════════════════════════════════════════════════
with tab_news:
    n_head_col, n_btn_col = st.columns([4, 1.5])
    with n_head_col:
        st.markdown(f"""
        <div style="padding:4px 0 10px;">
            <div style="font-family:'Orbitron',monospace;font-size:.85rem;color:#00F5FF;letter-spacing:.12em;">
                {t["news_title"]}
            </div>
            <div style="color:#5A7A9A;font-size:.82rem;margin-top:2px;">
                {t["news_desc"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with n_btn_col:
        st.markdown("<div style='padding-top:6px;'>", unsafe_allow_html=True)
        if st.button(t["news_btn_refresh"], use_container_width=True):
            st.session_state.news_feed_ver = (st.session_state.news_feed_ver % 2) + 1
            st.toast("✅ Radar de noticias sincronizado con el mercado.", icon="📡")
        st.markdown("</div>", unsafe_allow_html=True)

    lang_feed = NEWS_FEEDS.get(st.session_state.lang, NEWS_FEEDS["ES"])
    current_items = lang_feed.get(st.session_state.news_feed_ver, lang_feed[1])

    for item in current_items:
        st.markdown(f"""
        <div class="news-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="news-source">{item["source"]}</span>
                <span style="font-size:.68rem;color:#5A7A9A;">{item["date"]}</span>
            </div>
            <div class="news-headline">{item["headline"]}</div>
            <div class="news-summary">{item["body"]}</div>
            <div class="news-impact-box">
                <strong>{t["news_impact_tag"]}</strong><br>
                {item["ai_impact"]}
            </div>
            <div style="margin-top:10px;">
                <a class="news-link-btn" href="{item['url']}" target="_blank">
                    {t["news_read_btn"]} {item['source_name']} &nbsp;↗
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── EVALUADOR DE NOTICIAS PERSONALIZADAS ───────────────────────────────
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="neon-card purple">
        <div class="card-title purple">{t["news_custom_title"]}</div>
        <div style="font-size:.8rem;color:#5A7A9A;margin-bottom:10px;">{t["news_custom_desc"]}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("custom_news_form", clear_on_submit=False):
        custom_txt = st.text_input(
            "news_input", label_visibility="collapsed",
            placeholder=t["news_custom_ph"],
        )
        submit_custom = st.form_submit_button(t["news_custom_btn"], use_container_width=True)

    if submit_custom and custom_txt.strip():
        with st.spinner(t["news_spinner"]):
            try:
                import google.genai as genai
                client = genai.Client(api_key=_settings.google_api_key)
                prompt = (
                    f"Act as an expert box office financial analyst for CineMetrics AI. "
                    f"Analyze the following film industry news or rumor: '{custom_txt}'. "
                    f"In 2 or 3 concise paragraphs with bullet points and emojis: "
                    f"1. Estimate the projected financial impact on global box office ($ and % lift/risk). "
                    f"2. Identify target demographics and primary sensitive territories. "
                    f"3. Provide strategic marketing and exhibition recommendations. "
                    f"Respond entirely in the following language: {st.session_state.lang}."
                )
                res = client.models.generate_content(
                    model=_settings.gemini_model.removeprefix("models/"),
                    contents=prompt,
                )
                eval_text = res.text or "Sin respuesta / No response."
                st.session_state.custom_evals.insert(0, {"query": custom_txt, "response": eval_text})
            except Exception as e:
                st.error(f"Error evaluando noticia con Gemini: {e}")

    for ev in st.session_state.custom_evals:
        st.markdown(f"""
        <div class="news-card" style="border-left:3px solid #BF00FF;">
            <div style="font-family:'Orbitron',monospace;font-size:.65rem;color:#BF00FF;margin-bottom:4px;">
                {t["news_card_custom_lbl"]}
            </div>
            <div style="font-size:.88rem;font-weight:700;color:#E8F4FF;margin-bottom:8px;">
                "{ev["query"]}"
            </div>
            <div style="font-size:.82rem;color:#D8B4FE;line-height:1.6;">
                {ev["response"]}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 · AI ANALYST CHAT (MCP CLICKHOUSE)
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

    # Preguntas de ejemplo rápidas
    cols = st.columns(len(t["examples"]))
    for col, q in zip(cols, t["examples"]):
        with col:
            label = q[:28] + ("…" if len(q) > 28 else "")
            if st.button(label, key=f"ex_{q[:12]}", use_container_width=True):
                st.session_state["pending_q"] = q

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Historial de Chat
    if not st.session_state.messages:
        st.markdown(f"""
        <div style="text-align:center;padding:36px 20px;color:#2A4A6A;">
            <div style="font-size:2rem;margin-bottom:10px;">{t["chat_empty_icon"]}</div>
            <p style="font-family:'Orbitron',monospace;font-size:.72rem;letter-spacing:.12em;color:#2A4A6A;">
                {t["chat_empty_text"]}
            </p>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">👤 &nbsp;{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-agent">🎬 &nbsp;{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("data"):
                with st.expander(t["data_expand"], expanded=True):
                    st.dataframe(pd.DataFrame(msg["data"]), use_container_width=True, hide_index=True)
            if msg.get("sql_query"):
                with st.expander(t["sql_expand"], expanded=False):
                    st.code(msg["sql_query"], language="sql")
                    if msg.get("tool_used"):
                        st.caption(f"{t['mcp_tool']}: `{msg['tool_used']}`  ·  Model: `{_settings.gemini_model}`")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
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

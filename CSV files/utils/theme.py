"""
utils/theme.py
Shared design system - Dark premium with electric accents.
Call apply_theme() at the top of every page.
"""
import streamlit as st

_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700;900&family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {
    --bg: #0a0e17;
    --bg2: #111827;
    --ink: #e2e8f0;
    --ink-dim: #94a3b8;
    --accent: #06b6d4;
    --accent2: #8b5cf6;
    --danger: #ef4444;
    --warn: #f59e0b;
    --success: #10b981;
    --surface: #1e293b;
    --surface-hi: #334155;
    --border: #334155;
    --white: #f8fafc;
}

/* App shell */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    background: var(--bg) !important;
}
[data-testid="stHeader"] { background: var(--bg) !important; }
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }

/* Typography - only target specific Streamlit content containers */
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    font-family: 'Space Grotesk', sans-serif !important;
    text-transform: uppercase !important;
    letter-spacing: -0.01em !important;
    color: var(--white) !important;
}
[data-testid="stAppViewContainer"] .stMarkdown p,
[data-testid="stAppViewContainer"] .stMarkdown li,
[data-testid="stAppViewContainer"] .stCaption {
    font-family: 'Inter', sans-serif !important;
    color: var(--ink-dim) !important;
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.5) !important;
}

/* Inputs */
.stTextInput input, .stSelectbox [data-baseweb="select"] > div,
.stChatInput textarea, textarea, .stNumberInput input,
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
}
.stTextInput label, .stSelectbox label, .stMultiSelect label {
    color: var(--ink-dim) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
}
[data-testid="stMetricLabel"] { color: var(--ink-dim) !important; font-size: 0.8rem !important; }
[data-testid="stMetricValue"] { color: var(--white) !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 900 !important; }

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
}

/* Expanders */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    background: var(--surface) !important;
}
[data-testid="stExpander"] summary span {
    color: var(--ink) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 8px !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    color: var(--ink-dim) !important;
    border-radius: 6px !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: rgba(6, 182, 212, 0.15) !important;
    border-radius: 6px !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    border-radius: 12px !important;
}

/* Divider */
hr { border-top: 1px solid var(--border) !important; }

/* Info/Warning/Error boxes */
[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* ============================================================ */
/* Custom component classes                                      */
/* ============================================================ */

.bh-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid rgba(6, 182, 212, 0.3);
    border-radius: 16px;
    box-shadow: 0 0 40px rgba(6, 182, 212, 0.1), inset 0 1px 0 rgba(255,255,255,0.05);
    padding: 32px 36px; margin-bottom: 24px;
}
.bh-hero h1 {
    background: linear-gradient(135deg, #06b6d4, #8b5cf6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 10px 0; font-size: 2.2rem; font-weight: 900;
    font-family: 'Space Grotesk', sans-serif; text-transform: uppercase;
}
.bh-hero p { margin: 0; color: #94a3b8; font-size: 0.95rem; font-weight: 400; text-transform: none; }

.bh-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin: 8px 0 22px 0; }
.bh-tile {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    transition: all 0.2s ease;
}
.bh-tile:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); border-color: var(--accent); }
.bh-tile.t-accent { background: linear-gradient(135deg, rgba(6,182,212,0.15), rgba(139,92,246,0.1)); border-color: rgba(6,182,212,0.3); }
.bh-tile.t-warn { background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(245,158,11,0.05)); border-color: rgba(245,158,11,0.3); }
.bh-tile.t-danger { background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05)); border-color: rgba(239,68,68,0.3); }
.bh-tile-label { font-family: 'Space Grotesk', sans-serif; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-dim); margin-bottom: 8px; }
.bh-tile-value { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 900; letter-spacing: -0.02em; line-height: 1; color: var(--white); }
.bh-tile-sub { font-size: 0.76rem; font-weight: 500; margin-top: 8px; color: var(--ink-dim); }

.bh-section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 900; text-transform: uppercase; font-size: 1rem; letter-spacing: 0.05em;
    color: var(--accent);
    border-bottom: 2px solid var(--border); padding-bottom: 8px; margin: 24px 0 14px 0;
}

.bh-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px 22px; margin-bottom: 16px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}
.bh-card-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.1em; color: var(--accent); margin-bottom: 12px; }

.bh-nba {
    background: linear-gradient(135deg, #0f172a, #1e1b4b);
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 12px; box-shadow: 0 0 30px rgba(6,182,212,0.1);
    padding: 22px 24px; margin-bottom: 16px;
}
.bh-nba-label { font-family: 'Space Grotesk', sans-serif; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #06b6d4; }
.bh-nba-action { font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem; font-weight: 900; text-transform: uppercase; margin: 6px 0; color: #f8fafc; }
.bh-nba-detail { font-size: 0.86rem; color: #94a3b8; }

.bh-pill {
    display: inline-block; font-family: 'Space Grotesk', sans-serif;
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    padding: 4px 12px; margin-right: 6px; margin-bottom: 6px;
    border-radius: 6px; border: none;
}
.bh-p-urgent { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.bh-p-high { background: rgba(249,115,22,0.2); color: #f97316; border: 1px solid rgba(249,115,22,0.3); }
.bh-p-medium { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.bh-p-low { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.bh-p-info { background: rgba(6,182,212,0.2); color: #06b6d4; border: 1px solid rgba(6,182,212,0.3); }

.bh-gauge-wrap { margin: 10px 0; }
.bh-gauge-top { display: flex; justify-content: space-between; font-family: 'Space Grotesk', sans-serif; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; color: var(--ink-dim); }
.bh-gauge-track { height: 10px; border-radius: 5px; background: var(--surface-hi); overflow: hidden; }
.bh-gauge-fill { height: 100%; border-radius: 5px; }
.bh-g-good { background: linear-gradient(90deg, #10b981, #34d399); }
.bh-g-warn { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.bh-g-bad { background: linear-gradient(90deg, #ef4444, #f87171); }

.bh-kv { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.88rem; }
.bh-kv:last-child { border-bottom: none; }
.bh-kv-k { text-transform: uppercase; font-family: 'Space Grotesk', sans-serif; font-size: 0.72rem; font-weight: 700; color: var(--ink-dim); }
.bh-kv-v { font-weight: 700; color: var(--white); }

.rag-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 18px; margin-bottom: 12px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.ai-box {
    background: linear-gradient(135deg, rgba(6,182,212,0.08), rgba(139,92,246,0.08));
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 12px; padding: 18px; margin-top: 10px;
}

/* Badge overrides for existing pages */
.badge-Urgent { background: rgba(239,68,68,0.2); color: #ef4444; padding: 3px 12px; border-radius: 6px; font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.badge-High { background: rgba(249,115,22,0.2); color: #f97316; padding: 3px 12px; border-radius: 6px; font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.badge-Medium { background: rgba(245,158,11,0.2); color: #f59e0b; padding: 3px 12px; border-radius: 6px; font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.badge-Low { background: rgba(16,185,129,0.2); color: #10b981; padding: 3px 12px; border-radius: 6px; font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }

/* Old page classes compatibility */
.section-title { color: var(--accent) !important; font-family: 'Space Grotesk', sans-serif !important; font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
.nba-box { background: var(--surface) !important; border: 1px solid var(--accent) !important; border-radius: 12px !important; padding: 16px; }
.card { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; padding: 14px; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--surface-hi); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
"""

def apply_theme():
    st.html(_CSS)

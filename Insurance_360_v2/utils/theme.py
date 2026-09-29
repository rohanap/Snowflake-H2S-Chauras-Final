"""
utils/theme.py  --  BAUHAUS / NEO-BRUTALIST design system  (Insurance_360_v2)

Hand-translated from stitch_snowflake_streamlit_ui_redesign/ (Stitch export).

WHY HAND-TRANSLATED: the Stitch HTML loads Tailwind from cdn.tailwindcss.com,
Google Fonts, and the Material Symbols icon font. This runtime has no outbound
network access, so none of those would resolve. Every token from the export's
tailwind.config and every utility pattern it used is reproduced below as plain
CSS.

FONTS are self-hosted from static/ and declared in .streamlit/config.toml via
[[theme.fontFaces]] -- a CDN <link> fails silently here. Space Grotesk has no
offline source, so display type is Fira Sans.

ICONS are plain numerals and unicode glyphs. Material Symbols renders through
font ligatures, and that font does not load in this runtime, so passing
icon=":material/dashboard:" printed the literal word "DASHBOARD" on screen.

DESIGN LAWS (from bauhaus/DESIGN.md -- "Form Follows Function"):
  * Flat solid colour blocks. NO gradients on surfaces.
  * NO soft shadows, no glassmorphism. Depth = 3px solid borders + hard
    offset shadow blocks (4-6px down-right, #1a1a1a).
  * Radii ~0.
  * Oversized geometric display type against small functional body text.
  * Limited palette: black + ONE accent per section.
  * Buttons: solid fill, thick border, uppercase; hover = colour invert.
  * Inputs: thick bottom border only.
"""
from contextlib import contextmanager

import streamlit as st

# ── Palette (verbatim from the export's tailwind.config) ──────────────
INK = "#1a1a1a"          # primary / all borders / body text
PAPER = "#f5f0e8"        # surface  - warm off-white, "aged paper"
BRIGHT = "#faf7f2"       # surface-bright
CONTAINER = "#eee9e0"    # surface-container
CONTAINER_HI = "#e8e3da" # surface-container-high / surface-variant
CONTAINER_TOP = "#e2ddd4"  # surface-container-highest
DIM = "#d6d1c9"          # surface-dim
WHITE = "#ffffff"        # surface-container-lowest
MUTED = "#4a4a4a"        # on-surface-variant
HAIRLINE = "#d0cbc3"     # outline-variant

YELLOW = "#ffcc00"       # primary-container  - CTAs, active states
YELLOW_DIM = "#e6b800"
RED = "#e63b2e"          # secondary          - alerts, destructive
RED_SOFT = "#ffdad6"     # secondary-container
BLUE = "#0055ff"         # tertiary           - links, interactive
BLUE_SOFT = "#d6e3ff"    # tertiary-container
ERROR = "#cc0000"

# Priority colour map reused across pages
PRI_FILL = {"Urgent": RED_SOFT, "High": BRIGHT, "Medium": YELLOW, "Low": CONTAINER}
PRI_INK = {"Urgent": RED, "High": INK, "Medium": INK, "Low": MUTED}

# Fonts are self-hosted from static/ and declared in .streamlit/config.toml
# via [[theme.fontFaces]] -- this runtime has no outbound network access, so a
# Google Fonts <link> silently fails. Space Grotesk is not obtainable offline,
# so display type is Fira Sans (geometric, condensed) and the missing 900
# weight is faked with -webkit-text-stroke on oversized headings.
_FONT_DISPLAY = '"FiraSans","Archivo","Helvetica Neue",Arial,system-ui,sans-serif'
_FONT_BODY = '"Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'
_FONT_MONO = '"JetBrainsMono","SFMono-Regular",Menlo,Consolas,monospace'

FONT_DISPLAY = _FONT_DISPLAY
FONT_BODY = _FONT_BODY
FONT_MONO = _FONT_MONO

_CSS = """
<style>
:root {
    --ink: __INK__;
    --paper: __PAPER__;
    --bright: __BRIGHT__;
    --container: __CONTAINER__;
    --container-hi: __CONTAINER_HI__;
    --container-top: __CONTAINER_TOP__;
    --dim: __DIM__;
    --white: __WHITE__;
    --muted: __MUTED__;
    --hairline: __HAIRLINE__;
    --yellow: __YELLOW__;
    --yellow-dim: __YELLOW_DIM__;
    --red: __RED__;
    --red-soft: __RED_SOFT__;
    --blue: __BLUE__;
    --blue-soft: __BLUE_SOFT__;
    --error: __ERROR__;
    --font-display: __FONT_DISPLAY__;
    --font-body: __FONT_BODY__;
    --font-mono: __FONT_MONO__;
    /* Hard offset shadow blocks - the ONLY depth cue in this system */
    --drop-3: 3px 3px 0px 0px var(--ink);
    --drop-4: 4px 4px 0px 0px var(--ink);
    --drop-5: 5px 5px 0px 0px var(--ink);
    --drop-6: 6px 6px 0px 0px var(--ink);
    --bd: 3px solid var(--ink);
    --bd-2: 2px solid var(--ink);
}

/* ══════════════════════════════════════════════════════════════════
   APP SHELL
   ══════════════════════════════════════════════════════════════════ */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stMain"] {
    background: var(--paper) !important;
}
[data-testid="stHeader"] {
    background: var(--paper) !important;
    border-bottom: var(--bd-2) !important;
}
[data-testid="stAppViewBlockContainer"] {
    padding-top: 2.2rem !important;
    max-width: 100% !important;
}

/* Kill Streamlit's own page nav - we render a custom brutalist one */
[data-testid="stSidebarNav"] { display: none !important; }

/* Sidebar colours now come from [theme.sidebar] in .streamlit/config.toml.
   An earlier version used `[data-testid="stSidebar"] * { color: paper }`,
   which forced paper-white text onto the near-white Sync button and made its
   label invisible. Only specific text elements are targeted here. */
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1rem !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: var(--paper) !important;
}
/* Sidebar buttons: yellow on black, inverting to paper on hover. Explicit so
   they can never inherit an unreadable colour pair. */
[data-testid="stSidebar"] .stButton > button {
    background: var(--yellow) !important;
    color: var(--ink) !important;
    border: 3px solid var(--paper) !important;
    box-shadow: 4px 4px 0px 0px var(--paper) !important;
    font-family: var(--font-display) !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--paper) !important;
    color: var(--ink) !important;
    transform: translate(2px, 2px) !important;
    box-shadow: 2px 2px 0px 0px var(--paper) !important;
}
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] .stButton > button span {
    color: inherit !important;
}

/* ══════════════════════════════════════════════════════════════════
   TYPOGRAPHY - oversized geometric display vs small functional body
   ══════════════════════════════════════════════════════════════════ */
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    font-family: var(--font-display) !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: -0.03em !important;
    line-height: 0.95 !important;
    color: var(--ink) !important;
}
[data-testid="stAppViewContainer"] h1 { font-size: clamp(2rem, 4.4vw, 3.6rem) !important; }
[data-testid="stAppViewContainer"] .stMarkdown p,
[data-testid="stAppViewContainer"] .stMarkdown li {
    font-family: var(--font-body) !important;
    color: var(--muted) !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    font-family: var(--font-mono) !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--muted) !important;
}

/* ══════════════════════════════════════════════════════════════════
   WIDGETS - solid fill, thick border, uppercase, hover = invert
   ══════════════════════════════════════════════════════════════════ */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    background: var(--bright) !important;
    color: var(--ink) !important;
    border: var(--bd) !important;
    border-radius: 0 !important;
    box-shadow: var(--drop-4) !important;
    font-family: var(--font-display) !important;
    font-weight: 700 !important;
    font-size: 0.74rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 0.55rem 1rem !important;
    transition: none !important;
}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    background: var(--ink) !important;
    color: var(--paper) !important;
    transform: translate(2px, 2px) !important;
    box-shadow: var(--drop-2, 2px 2px 0px 0px var(--ink)) !important;
}
.stButton > button:active, .stFormSubmitButton > button:active {
    transform: translate(4px, 4px) !important;
    box-shadow: none !important;
}
/* Primary CTA = yellow fill */
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: var(--yellow) !important;
    color: var(--ink) !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: var(--ink) !important;
    color: var(--yellow) !important;
}
.stButton > button:disabled {
    background: var(--container-top) !important;
    color: var(--hairline) !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Inputs: thick BOTTOM border only, no radius */
.stTextInput input, .stNumberInput input, .stChatInput textarea, textarea {
    background: var(--bright) !important;
    border: none !important;
    border-bottom: var(--bd) !important;
    border-radius: 0 !important;
    color: var(--ink) !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
}
.stTextInput input:focus, textarea:focus {
    background: var(--yellow) !important;
    box-shadow: none !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--bright) !important;
    border: var(--bd-2) !important;
    border-radius: 0 !important;
    color: var(--ink) !important;
    font-weight: 600 !important;
}
[data-testid="stWidgetLabel"] label, .stTextInput label,
.stSelectbox label, .stMultiSelect label, .stRadio label {
    font-family: var(--font-display) !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    color: var(--ink) !important;
}
/* Multiselect tokens read as brutalist chips */
.stMultiSelect [data-baseweb="tag"] {
    background: var(--yellow) !important;
    border: var(--bd-2) !important;
    border-radius: 0 !important;
    color: var(--ink) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.66rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
}
.stMultiSelect [data-baseweb="tag"] span { color: var(--ink) !important; }

[data-testid="stForm"] {
    background: var(--container) !important;
    border: var(--bd) !important;
    border-radius: 0 !important;
    box-shadow: var(--drop-5) !important;
    padding: 1.1rem 1.2rem 0.6rem 1.2rem !important;
}

/* Segmented control = hard tab row */
[data-testid="stSegmentedControl"] { margin-bottom: 0.4rem !important; }
[data-testid="stSegmentedControl"] > div {
    gap: 0 !important;
    background: transparent !important;
}
[data-testid="stSegmentedControl"] button {
    background: var(--bright) !important;
    color: var(--ink) !important;
    border: var(--bd) !important;
    border-radius: 0 !important;
    margin-right: -3px !important;
    font-family: var(--font-display) !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    padding: 0.5rem 0.95rem !important;
}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[data-selected="true"] {
    background: var(--yellow) !important;
    color: var(--ink) !important;
    box-shadow: var(--drop-3) !important;
    z-index: 2 !important;
}

/* Metrics -> brutalist stat blocks */
[data-testid="stMetric"] {
    background: var(--bright) !important;
    border: var(--bd) !important;
    border-radius: 0 !important;
    box-shadow: var(--drop-5) !important;
    padding: 1rem 1.1rem !important;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
    font-family: var(--font-display) !important;
    font-size: 0.66rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--ink) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-weight: 700 !important;
    font-size: clamp(1.4rem, 2.6vw, 2.4rem) !important;
    letter-spacing: -0.03em !important;
    line-height: 1 !important;
    color: var(--ink) !important;
    overflow: visible !important;
    text-overflow: clip !important;
    white-space: nowrap !important;
}
[data-testid="stMetricValue"] > div { overflow: visible !important; }

/* Tables */
[data-testid="stDataFrame"] {
    border: var(--bd) !important;
    border-radius: 0 !important;
    box-shadow: var(--drop-5) !important;
}
[data-testid="stExpander"] {
    background: var(--bright) !important;
    border: var(--bd-2) !important;
    border-radius: 0 !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-display) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}
[data-testid="stExpander"] summary span, [data-testid="stExpander"] summary p {
    color: var(--ink) !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: transparent !important;
    border-bottom: var(--bd) !important;
}
.stTabs [data-baseweb="tab"] {
    background: var(--container) !important;
    border: var(--bd-2) !important;
    border-bottom: none !important;
    border-radius: 0 !important;
    margin-right: -2px !important;
    font-family: var(--font-display) !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: var(--yellow) !important;
    color: var(--ink) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

[data-testid="stChatMessage"] {
    background: var(--bright) !important;
    border: var(--bd-2) !important;
    border-radius: 0 !important;
    box-shadow: var(--drop-3) !important;
}
[data-testid="stAlert"] {
    border: var(--bd) !important;
    border-radius: 0 !important;
    box-shadow: var(--drop-4) !important;
    font-family: var(--font-body) !important;
}
hr { border-top: var(--bd-2) !important; }
code {
    background: var(--container-top) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
    color: var(--ink) !important;
    font-family: var(--font-mono) !important;
}
[data-testid="stCodeBlock"], pre {
    border: var(--bd-2) !important;
    border-radius: 0 !important;
    background: var(--container-top) !important;
}

/* ══════════════════════════════════════════════════════════════════
   LOADING - top scan bar + label. stStatusWidget exists only while the
   script runs, so restyling it gives a free page-load indicator.
   ══════════════════════════════════════════════════════════════════ */
[data-testid="stStatusWidget"] {
    position: fixed !important;
    top: 0 !important; left: 0 !important; right: 0 !important;
    width: 100vw !important; height: 6px !important;
    min-height: 6px !important; max-height: 6px !important;
    padding: 0 !important; margin: 0 !important;
    border: none !important; border-radius: 0 !important;
    background: repeating-linear-gradient(90deg,
        __INK__ 0 14px, __YELLOW__ 14px 28px) !important;
    background-size: 56px 100% !important;
    animation: bh-march 0.55s linear infinite !important;
    z-index: 999999 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}
[data-testid="stStatusWidget"] * {
    display: none !important; visibility: hidden !important;
}
@keyframes bh-march {
    from { background-position: 0 0; }
    to   { background-position: 56px 0; }
}
[data-testid="stSpinner"] {
    border: none !important;
    background: transparent !important;
    padding: 8px 0 !important;
}
[data-testid="stSpinner"] p,
[data-testid="stSpinner"] div[data-testid="stMarkdownContainer"] p {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--ink) !important;
    margin: 0 !important;
}

/* ══════════════════════════════════════════════════════════════════
   CUSTOM SIDEBAR  (brand block / nav / status card)
   ══════════════════════════════════════════════════════════════════ */
.bh-brand {
    border-bottom: 4px solid var(--paper);
    padding: 0 0 14px 0; margin-bottom: 16px;
}
.bh-brand-mark {
    display: flex; align-items: center; gap: 8px;
    font-family: var(--font-display); font-size: 1.18rem; font-weight: 700;
    letter-spacing: -0.02em; text-transform: uppercase; color: var(--paper);
}
.bh-brand-bar { width: 7px; height: 26px; background: var(--yellow); display: inline-block; }
.bh-brand-sub {
    font-family: var(--font-mono); font-size: 0.6rem; font-weight: 700;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--yellow); margin-top: 6px; padding-left: 15px;
}
.bh-navlabel {
    font-family: var(--font-mono); font-size: 0.58rem; font-weight: 700;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: #8a857c; margin: 4px 0 8px 0;
}
/* Sidebar page_link -> hard nav rows.
   Left-aligned with modest tracking: an earlier version centred the text and
   over-spaced it, which made rows collide. */
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    background: transparent !important;
    border: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: 7px 10px !important;
    margin-bottom: 2px !important;
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    gap: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a p,
[data-testid="stSidebar"] [data-testid="stPageLink"] a span,
[data-testid="stSidebar"] [data-testid="stPageLink"] a div {
    font-family: var(--font-display) !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.01em !important;
    color: var(--paper) !important;
    text-align: left !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    margin: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    background: var(--yellow) !important;
    border-color: var(--paper) !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover p,
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover span,
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover div {
    color: var(--ink) !important;
}
.bh-status {
    border: 2px solid var(--paper); padding: 11px 12px; margin-top: 14px;
    background: #262626;
}
.bh-status-top {
    display: flex; align-items: center; gap: 7px;
    font-family: var(--font-mono); font-size: 0.6rem; font-weight: 700;
    letter-spacing: 0.13em; text-transform: uppercase; color: var(--yellow);
}
.bh-dot {
    width: 8px; height: 8px; background: var(--yellow);
    display: inline-block; animation: bh-blink 1.3s steps(2) infinite;
}
@keyframes bh-blink { 50% { opacity: 0.15; } }
.bh-status-row {
    display: flex; justify-content: space-between;
    font-family: var(--font-mono); font-size: 0.62rem; font-weight: 600;
    color: var(--paper); margin-top: 7px;
}
.bh-status-row span:last-child { color: var(--yellow); font-weight: 700; }

/* ══════════════════════════════════════════════════════════════════
   TOP STATUS STRIP
   ══════════════════════════════════════════════════════════════════ */
.bh-topbar {
    display: flex; flex-wrap: wrap; align-items: center; gap: 0;
    border: var(--bd); background: var(--ink);
    margin-bottom: 20px; box-shadow: var(--drop-4);
}
.bh-topbar-cell {
    display: flex; align-items: baseline; gap: 7px;
    padding: 8px 14px; border-right: 2px solid #3d3d3d;
    font-family: var(--font-mono); font-size: 0.64rem; font-weight: 600;
    color: var(--dim);
}
.bh-topbar-cell b { color: var(--paper); font-weight: 700; letter-spacing: 0.03em; }
.bh-topbar-cell.k {
    font-size: 0.56rem; letter-spacing: 0.16em; text-transform: uppercase;
    color: #8a857c;
}
.bh-topbar-live {
    margin-left: auto; padding: 8px 14px; background: var(--yellow);
    border-left: 3px solid var(--ink);
    font-family: var(--font-mono); font-size: 0.62rem; font-weight: 700;
    letter-spacing: 0.13em; text-transform: uppercase; color: var(--ink);
    display: flex; align-items: center; gap: 7px;
}
.bh-topbar-live .d {
    width: 8px; height: 8px; background: var(--red); display: inline-block;
    animation: bh-blink 1.1s steps(2) infinite;
}

/* ══════════════════════════════════════════════════════════════════
   PAGE BANNER
   ══════════════════════════════════════════════════════════════════ */
.bh-banner { border-bottom: var(--bd); padding-bottom: 18px; margin-bottom: 24px; }
.bh-eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 4px 9px; margin-bottom: 12px;
    background: var(--ink); color: var(--paper);
    border: var(--bd-2); box-shadow: var(--drop-3);
    font-family: var(--font-mono); font-size: 0.62rem; font-weight: 700;
    letter-spacing: 0.13em; text-transform: uppercase;
}
.bh-eyebrow .p {
    width: 8px; height: 8px; background: var(--red); display: inline-block;
    animation: bh-blink 1.1s steps(2) infinite;
}
.bh-title {
    font-family: var(--font-display); font-weight: 700;
    font-size: clamp(2rem, 5vw, 3.75rem); line-height: 0.9;
    letter-spacing: -0.045em; text-transform: uppercase; color: var(--ink);
    margin: 0;
    /* Bundled Fira Sans tops out at 700, but Bauhaus wants 900. Stroking the
       glyphs in their own colour thickens them to read as a heavier cut. */
    -webkit-text-stroke: 0.7px var(--ink);
    paint-order: stroke fill;
}
.bh-sub {
    margin: 14px 0 0 0; padding-left: 12px;
    border-left: 5px solid var(--red);
    font-family: var(--font-body); font-size: 0.86rem; font-weight: 500;
    color: var(--muted); max-width: 78ch;
}
.bh-sub b { color: var(--ink); font-weight: 700; }

/* ══════════════════════════════════════════════════════════════════
   CORE BLOCKS
   ══════════════════════════════════════════════════════════════════ */
.bh-box {
    background: var(--bright); border: var(--bd);
    box-shadow: var(--drop-5); padding: 18px 20px; margin-bottom: 20px;
}
.bh-box.tight { padding: 14px 16px; }
.bh-box.paper { background: var(--container); }
.bh-box.yellow { background: var(--yellow); }
.bh-box.red { background: var(--red-soft); }
.bh-box.blue { background: var(--blue-soft); }
.bh-box.dark { background: var(--ink); }
.bh-box.dark, .bh-box.dark * { color: var(--paper); }
.bh-box.dark .bh-box-title { color: var(--yellow); }

.bh-box-title {
    display: flex; align-items: center; justify-content: space-between;
    gap: 10px; font-family: var(--font-display); font-size: 0.72rem;
    font-weight: 700; letter-spacing: 0.11em; text-transform: uppercase;
    color: var(--ink); border-bottom: var(--bd-2);
    padding-bottom: 9px; margin-bottom: 13px;
}
.bh-section {
    display: flex; align-items: center; gap: 11px;
    font-family: var(--font-display); font-weight: 700; font-size: 1.05rem;
    letter-spacing: -0.01em; text-transform: uppercase; color: var(--ink);
    border-bottom: var(--bd); padding-bottom: 9px; margin: 30px 0 16px 0;
}
.bh-section .n {
    background: var(--yellow); border: var(--bd-2); padding: 1px 8px;
    font-family: var(--font-mono); font-size: 0.7rem; font-weight: 700;
}

/* KPI bento */
.bh-bento {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
    gap: 16px; margin-bottom: 24px;
}
.bh-kpi {
    background: var(--bright); border: var(--bd); box-shadow: var(--drop-5);
    padding: 17px 18px; display: flex; flex-direction: column;
    justify-content: space-between; min-height: 150px;
}
.bh-kpi.red { background: var(--red-soft); }
.bh-kpi.yellow { background: var(--yellow); }
.bh-kpi.paper { background: var(--container); }
.bh-kpi.blue { background: var(--blue-soft); }
.bh-kpi.dark { background: var(--ink); }
.bh-kpi.dark .bh-kpi-k { color: var(--yellow); }
.bh-kpi.dark .bh-kpi-v { color: var(--yellow); }
.bh-kpi.dark .bh-kpi-s { color: var(--dim); }
.bh-kpi-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.bh-kpi-k {
    font-family: var(--font-display); font-size: 0.66rem; font-weight: 700;
    letter-spacing: 0.11em; text-transform: uppercase; color: var(--ink);
}
.bh-kpi-i { font-size: 1.05rem; line-height: 1; }
.bh-kpi-v {
    font-family: var(--font-display); font-weight: 700;
    font-size: clamp(1.7rem, 3.1vw, 2.85rem); letter-spacing: -0.04em;
    line-height: 0.95; color: var(--ink); margin: 14px 0 3px 0;
    -webkit-text-stroke: 0.5px currentColor; paint-order: stroke fill;
}
.bh-kpi-s {
    font-family: var(--font-mono); font-size: 0.6rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted);
}
.bh-kpi-bar {
    height: 9px; background: var(--container-top);
    border: 2px solid var(--ink); margin-top: 13px; overflow: hidden;
}
.bh-kpi-bar > i { display: block; height: 100%; background: var(--ink); }

/* Chips / pills */
.bh-chip {
    display: inline-block; padding: 3px 9px; margin: 0 5px 5px 0;
    background: var(--bright); border: var(--bd-2);
    font-family: var(--font-mono); font-size: 0.62rem; font-weight: 700;
    letter-spacing: 0.05em; text-transform: uppercase; color: var(--ink);
}
.bh-chip.on { background: var(--yellow); box-shadow: 2px 2px 0 0 var(--ink); }
.bh-chip.red { background: var(--red); color: var(--paper); }
.bh-chip.redsoft { background: var(--red-soft); color: var(--red); }
.bh-chip.yellow { background: var(--yellow); }
.bh-chip.blue { background: var(--blue); color: var(--paper); }
.bh-chip.bluesoft { background: var(--blue-soft); color: var(--blue); }
.bh-chip.dark { background: var(--ink); color: var(--paper); }
.bh-chip.ghost { background: transparent; }

/* Execution queue row */
.bh-row {
    display: grid;
    grid-template-columns: 46px minmax(190px, 2.3fr) repeat(4, minmax(74px, 1fr));
    align-items: center; gap: 12px;
    background: var(--bright); border: var(--bd); box-shadow: var(--drop-4);
    padding: 13px 15px; margin-bottom: 12px;
}
.bh-row.urgent { background: var(--red-soft); }
.bh-row.high { background: var(--bright); }
.bh-row.medium { background: #fdf6dc; }
.bh-row.low { background: var(--container); }
.bh-row-n {
    font-family: var(--font-display); font-weight: 700; font-size: 1.35rem;
    color: var(--ink); border-right: var(--bd-2); padding-right: 11px;
    line-height: 1; text-align: center;
}
.bh-row-name {
    font-family: var(--font-display); font-weight: 700; font-size: 1rem;
    letter-spacing: -0.015em; text-transform: uppercase; color: var(--ink);
    line-height: 1.1;
}
.bh-row-meta {
    font-family: var(--font-mono); font-size: 0.6rem; font-weight: 600;
    text-transform: uppercase; color: var(--muted); margin-top: 4px;
}
.bh-cell { text-align: center; }
.bh-cell-v {
    font-family: var(--font-display); font-weight: 700; font-size: 1.05rem;
    letter-spacing: -0.02em; line-height: 1; color: var(--ink);
}
.bh-cell-k {
    font-family: var(--font-mono); font-size: 0.53rem; font-weight: 700;
    letter-spacing: 0.09em; text-transform: uppercase;
    color: var(--muted); margin-top: 3px;
}
.bh-nba-strip {
    grid-column: 1 / -1; border-top: var(--bd-2); margin-top: 11px;
    padding-top: 10px; display: flex; flex-wrap: wrap; align-items: baseline;
    gap: 9px; font-family: var(--font-body); font-size: 0.78rem;
    color: var(--muted);
}
.bh-nba-strip b {
    font-family: var(--font-display); font-size: 0.82rem; font-weight: 700;
    text-transform: uppercase; color: var(--ink);
}

/* Key/value ledger */
.bh-kv {
    display: flex; justify-content: space-between; gap: 12px;
    padding: 7px 0; border-bottom: 1px dashed var(--hairline);
    font-family: var(--font-mono); font-size: 0.72rem;
}
.bh-kv:last-child { border-bottom: none; }
.bh-kv-k {
    font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase;
    color: var(--muted);
}
.bh-kv-v { font-weight: 700; color: var(--ink); text-align: right; }

/* Fact grid */
.bh-facts {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(125px, 1fr));
    gap: 0; border-top: var(--bd-2);
}
.bh-fact {
    padding: 11px 13px; border-right: 2px solid var(--ink);
    border-bottom: 2px solid var(--ink);
}
.bh-fact:last-child { border-right: none; }
.bh-fact-k {
    font-family: var(--font-mono); font-size: 0.55rem; font-weight: 700;
    letter-spacing: 0.13em; text-transform: uppercase; color: var(--muted);
}
.bh-fact-v {
    font-family: var(--font-display); font-weight: 700; font-size: 1.02rem;
    letter-spacing: -0.02em; color: var(--ink); margin-top: 4px;
    line-height: 1.1;
}

/* Gauge / meter */
.bh-meter {
    height: 22px; background: var(--container-top); border: var(--bd-2);
    overflow: hidden; position: relative;
}
.bh-meter > i {
    display: block; height: 100%;
    background: repeating-linear-gradient(45deg,
        var(--ink) 0 6px, transparent 6px 12px), var(--yellow);
}
.bh-meter.red > i {
    background: repeating-linear-gradient(45deg,
        var(--ink) 0 6px, transparent 6px 12px), var(--red);
}
.bh-meter-scale {
    display: flex; justify-content: space-between;
    font-family: var(--font-mono); font-size: 0.55rem; font-weight: 700;
    color: var(--muted); margin-top: 4px;
}

/* Numbered signal card */
.bh-signal {
    background: var(--bright); border: var(--bd); box-shadow: var(--drop-4);
    padding: 0; overflow: hidden;
}
.bh-signal-h {
    display: flex; align-items: center; gap: 10px;
    background: var(--ink); padding: 9px 13px;
}
.bh-signal-n {
    font-family: var(--font-mono); font-size: 0.72rem; font-weight: 700;
    background: var(--yellow); color: var(--ink); padding: 1px 7px;
    border: 2px solid var(--paper);
}
.bh-signal-t {
    font-family: var(--font-display); font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.11em; text-transform: uppercase; color: var(--paper);
}
.bh-signal-b { padding: 11px 14px; }
.bh-signal.alert .bh-signal-h { background: var(--red); }
.bh-signal.ok .bh-signal-h { background: var(--ink); }

/* Monospace output block (AI script preview / raw values) */
.bh-mono {
    background: var(--container-top); border: var(--bd-2);
    padding: 14px 16px; font-family: var(--font-mono);
    font-size: 0.78rem; line-height: 1.65; color: var(--ink);
    white-space: pre-wrap; word-break: break-word;
}
.bh-mono.dark { background: var(--ink); color: var(--paper); }

/* Ledger table (hand-rolled, for brutalist rows) */
.bh-ledger { width: 100%; border-collapse: collapse; font-family: var(--font-mono); }
.bh-ledger th {
    background: var(--ink); color: var(--paper); text-align: left;
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; padding: 8px 11px; border: 2px solid var(--ink);
}
.bh-ledger td {
    background: var(--bright); font-size: 0.72rem; font-weight: 600;
    color: var(--ink); padding: 8px 11px; border: 2px solid var(--ink);
}
.bh-ledger tr.sel td { background: var(--yellow); }
.bh-ledger td.num { text-align: right; }

/* Bar list (right-rail breakdowns) */
.bh-bars { display: flex; flex-direction: column; gap: 10px; }
.bh-bar-l {
    display: flex; justify-content: space-between;
    font-family: var(--font-mono); font-size: 0.63rem; font-weight: 700;
    text-transform: uppercase; color: var(--ink); margin-bottom: 3px;
}
.bh-bar-t { height: 15px; background: var(--container-top); border: 2px solid var(--ink); }
.bh-bar-t > i { display: block; height: 100%; }

/* ══════════════════════════════════════════════════════════════════
   RESPONSIVE
   ══════════════════════════════════════════════════════════════════ */
@media (max-width: 1200px) {
    .bh-bento { grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
    .bh-row { grid-template-columns: 40px minmax(160px, 2fr) repeat(4, minmax(62px, 1fr)); }
}
@media (max-width: 900px) {
    .bh-title { font-size: clamp(1.6rem, 7vw, 2.3rem); }
    .bh-row { grid-template-columns: 40px 1fr 1fr; row-gap: 12px; }
    .bh-row-nw { grid-column: 2 / -1; }
    .bh-topbar-cell { padding: 6px 10px; }
    .bh-topbar-live { margin-left: 0; width: 100%; border-left: none; border-top: 3px solid var(--ink); }
    .bh-facts { grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); }
}
@media (max-width: 640px) {
    .bh-bento { grid-template-columns: 1fr 1fr; gap: 10px; }
    .bh-kpi { min-height: 120px; padding: 13px; }
    .bh-row { grid-template-columns: 1fr 1fr; }
    .bh-row-n { display: none; }
    .bh-kv { flex-direction: column; gap: 2px; }
    .bh-kv-v { text-align: left; }
}
</style>
"""

for _k, _v in [
    ("__INK__", INK), ("__PAPER__", PAPER), ("__BRIGHT__", BRIGHT),
    ("__CONTAINER_HI__", CONTAINER_HI), ("__CONTAINER_TOP__", CONTAINER_TOP),
    ("__CONTAINER__", CONTAINER), ("__DIM__", DIM), ("__WHITE__", WHITE),
    ("__MUTED__", MUTED), ("__HAIRLINE__", HAIRLINE),
    ("__YELLOW_DIM__", YELLOW_DIM), ("__YELLOW__", YELLOW),
    ("__RED_SOFT__", RED_SOFT), ("__RED__", RED),
    ("__BLUE_SOFT__", BLUE_SOFT), ("__BLUE__", BLUE), ("__ERROR__", ERROR),
    ("__FONT_DISPLAY__", FONT_DISPLAY), ("__FONT_BODY__", FONT_BODY),
    ("__FONT_MONO__", FONT_MONO),
]:
    _CSS = _CSS.replace(_k, _v)


# ── Public API ────────────────────────────────────────────────────────

# Numbered labels, NOT Material icons. Material Symbols renders via font
# ligatures, and that font does not load in this runtime -- passing
# icon=":material/dashboard:" showed the literal word "DASHBOARD" overlapping
# the label. Numbers are font-independent and fit the brutalist grid.
NAV = [
    ("streamlit_app.py", "01  Command Center"),
    ("pages/1_Customer_360.py", "02  Customer 360"),
    ("pages/2_NBA_Dashboard.py", "03  NBA Priority"),
    ("pages/3_Segment_Analytics.py", "04  Segment Analytics"),
    ("pages/4_Transcript_Explorer.py", "05  Transcript RAG"),
    ("pages/5_Ask_Your_Data.py", "06  Ask Your Data"),
    ("pages/6_Document_AI.py", "07  Document AI"),
    ("pages/7_Ops_Monitor.py", "08  Ops Monitor"),
]


def apply_theme() -> None:
    """Inject the Bauhaus stylesheet. First UI call on every page."""
    st.html(_CSS)


def sidebar(warehouse: str = "COMPUTE_WH", size: str = "X-SMALL") -> None:
    """Custom brutalist sidebar: brand block, nav, warehouse status card.

    Streamlit's own nav is hidden by CSS; this replaces it so the extra
    'Command Center' entry and the status card from the mockup can exist.
    """
    with st.sidebar:
        st.html("""
        <div class="bh-brand">
            <div class="bh-brand-mark"><span class="bh-brand-bar"></span>INSURANCE_TWIN</div>
            <div class="bh-brand-sub">Cortex Edition</div>
        </div>
        <div class="bh-navlabel">// Modules</div>""")

        for path, label in NAV:
            st.page_link(path, label=label, use_container_width=True)

        st.html(f"""
        <div class="bh-status">
            <div class="bh-status-top"><span class="bh-dot"></span>Warehouse Active</div>
            <div class="bh-status-row"><span>NAME</span><span>{warehouse}</span></div>
            <div class="bh-status-row"><span>SIZE</span><span>{size}</span></div>
            <div class="bh-status-row"><span>ROLE</span><span>ACCOUNTADMIN</span></div>
        </div>""")


def topbar(records: str = "-", latency: str = "-",
           db: str = "INSURANCE_C360", schema: str = "GOLD") -> None:
    """Top system status strip from the mockups."""
    st.html(f"""
    <div class="bh-topbar">
        <div class="bh-topbar-cell k">DB / SCHEMA</div>
        <div class="bh-topbar-cell"><b>{db}.{schema}</b></div>
        <div class="bh-topbar-cell k">RECORDS</div>
        <div class="bh-topbar-cell"><b>{records}</b></div>
        <div class="bh-topbar-cell k">LATENCY</div>
        <div class="bh-topbar-cell"><b>{latency}</b></div>
        <div class="bh-topbar-live"><span class="d"></span>Cortex Engine Ready</div>
    </div>""")


def banner(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    """Oversized page banner."""
    eb = (f'<div class="bh-eyebrow"><span class="p"></span>{eyebrow}</div>'
          if eyebrow else "")
    sub = f'<p class="bh-sub">{subtitle}</p>' if subtitle else ""
    st.html(f'<div class="bh-banner">{eb}<h1 class="bh-title">{title}</h1>{sub}</div>')


def section(title: str, number: str = "") -> None:
    """Section rule with an optional numbered tag."""
    n = f'<span class="n">{number}</span>' if number else ""
    st.html(f'<div class="bh-section">{n}<span>{title}</span></div>')


def kpi(label: str, value: str, sub: str = "", tone: str = "",
        icon: str = "", bar_pct: int = None, bar_color: str = None) -> str:
    """One KPI bento tile. Returns HTML - join several inside bento()."""
    ic = f'<span class="bh-kpi-i">{icon}</span>' if icon else ""
    bar = ""
    if bar_pct is not None:
        col = bar_color or INK
        bar = (f'<div class="bh-kpi-bar"><i style="width:{max(2, min(100, bar_pct))}%;'
               f'background:{col}"></i></div>')
    tail = f'<div class="bh-kpi-s">{sub}</div>' if sub else ""
    return (f'<div class="bh-kpi {tone}"><div class="bh-kpi-top">'
            f'<span class="bh-kpi-k">{label}</span>{ic}</div>'
            f'<div class="bh-kpi-v">{value}</div>{tail}{bar}</div>')


def bento(tiles: list) -> None:
    """Render a KPI grid from kpi() fragments."""
    st.html(f'<div class="bh-bento">{"".join(tiles)}</div>')


def inr(value, compact: bool = False) -> str:
    """Format rupees. compact=True for narrow slots (uses Cr / L / K)."""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return "₹0"
    if not compact:
        return f"₹{v:,.0f}"
    if abs(v) >= 1e7:
        return f"₹{v / 1e7:.2f} Cr"
    if abs(v) >= 1e5:
        return f"₹{v / 1e5:.2f} L"
    if abs(v) >= 1e3:
        return f"₹{v / 1e3:.1f}K"
    return f"₹{v:,.0f}"


@contextmanager
def loading(message: str = "Executing"):
    """Spinner for slow call sites. Wrap the CALL, not the function body."""
    with st.spinner(message):
        yield

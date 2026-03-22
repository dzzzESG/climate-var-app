"""
TC Energy — Climate Risk Stress Testing Terminal  v3.2
Real TC Energy 2024 public disclosure data · No Mapbox token needed (Scattergeo)
Install: pip install streamlit plotly pandas numpy yfinance
Run:     streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import date
import textwrap  # 引入 textwrap 彻底解决 HTML 缩进渲染 Bug

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TRP Climate Stress Terminal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main  { background: #F4F6F9; }
.block-container { padding: 1.8rem 2.4rem 2rem; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #0D2137 !important; }
section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider   label,
section[data-testid="stSidebar"] .stNumberInput label {
  color: #94A3B8 !important; font-size: .71rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .07em;
}
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08) !important; }
section[data-testid="stSidebar"] .stSelectbox > div > div {
  background: #1E3A5F !important; border-color: #2D5A8C !important; color: #E2E8F0 !important;
}

/* Page header */
.page-hdr h1 { font-size: 1.6rem; font-weight: 700; color: #0D2137; margin: 0 0 .2rem; letter-spacing: -.4px; }
.page-hdr p  { font-size: .88rem; color: #64748B; margin: 0; }
.hdr-rule    { border: none; border-top: 2px solid #0D2137; margin: .8rem 0 1.5rem; }

/* Sidebar section label */
.sb-lbl {
  font-size: .67rem; font-weight: 700; color: #475569;
  text-transform: uppercase; letter-spacing: .1em;
  border-top: 1px solid rgba(255,255,255,.06);
  padding-top: 1rem; margin: 1rem 0 .3rem;
}

/* KPI cards */
.kpi { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: .95rem 1.2rem; }
.kpi-dark { background: #0D2137; border-radius: 10px; padding: .95rem 1.2rem; }
.kpi-lbl  { font-size: .66rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 5px; }
.kpi-val  { font-size: 1.45rem; font-weight: 700; color: #0D2137; line-height: 1.1; }
.kpi-sub  { font-size: .73rem; color: #94A3B8; margin-top: 3px; }
.kpi-dark .kpi-lbl { color: #475569; }
.kpi-dark .kpi-val { color: #F1F5F9; }
.kpi-dark .kpi-sub { color: #334155; }
.kpi-neg  { border-left: 3px solid #EF4444; }
.kpi-warn { border-left: 3px solid #F59E0B; }
.kpi-pos  { border-left: 3px solid #22C55E; }
.kpi-inf  { border-left: 3px solid #3B82F6; }

/* Section title */
.sec { font-size: .98rem; font-weight: 600; color: #0D2137;
       border-bottom: 2px solid #E2E8F0; padding-bottom: .55rem; margin-bottom: 1.15rem; }

/* Info tiles */
.itile { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: .85rem 1.05rem; }
.itile .il { font-size: .65rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 4px; }
.itile .iv { font-size: 1.25rem; font-weight: 700; color: #0D2137; }
.itile .is { font-size: .72rem; color: #94A3B8; margin-top: 2px; }

/* Asset card */
.a-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;
           padding: .6rem .9rem; margin-bottom: .45rem; }
.a-card.sel { background: #EFF6FF; border-color: #0D2137; border-width: 2px; }
.a-name { font-size: .79rem; font-weight: 600; color: #0D2137; margin-bottom: 2px; }
.a-meta { display: flex; gap: 14px; font-size: .7rem; color: #64748B; }

/* Note box */
.note { background: #F0F9FF; border-left: 3px solid #0EA5E9; border-radius: 0 6px 6px 0;
        padding: .65rem 1rem; font-size: .8rem; color: #0C4A6E; margin-top: .6rem; }
.note b { color: #0369A1; }

/* Method box */
.mbox { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;
        padding: .75rem 1rem; font-size: .78rem; color: #374151; margin-top: .5rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #E8EDF2; border-radius: 9px; padding: 4px; gap: 3px; }
.stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 7px 18px; font-size: .85rem; font-weight: 500; color: #64748B; }
.stTabs [aria-selected="true"] { background: white !important; color: #0D2137 !important; box-shadow: 0 1px 3px rgba(0,0,0,.1); }

/* Download */
.stDownloadButton button { background: #0D2137 !important; color: #F1F5F9 !important;
  border: none !important; border-radius: 6px !important; font-weight: 600 !important;
  font-size: .82rem !important; }
.stDownloadButton button:hover { background: #1E3A5F !important; }

/* Formal report */
.rpt { background:#FFFFFF; padding:44px 52px; border:1px solid #D1D5DB; border-radius:8px;
       box-shadow:0 2px 8px rgba(0,0,0,.05); font-family:'Georgia',serif; color:#111827; }
.rpt h2 { color:#0D2137; font-size:21px; text-transform:uppercase; letter-spacing:.4px; margin:0 0 5px; }
.rpt h3 { color:#0D2137; font-size:15px; border-bottom:1px solid #0D2137;
         padding-bottom:4px; margin:26px 0 9px; }
.rpt p, .rpt li { font-size:13.5px; line-height:1.75; color:#1F2937; }
.rpt .rec { background:#F3F4F6; border-left:4px solid #0D2137; padding:14px 18px 14px 22px; }
.rpt .ftr { font-size:11px; color:#9CA3AF; margin-top:36px; padding-top:12px;
            border-top:1px solid #D1D5DB; text-align:justify; }
</style>
""", unsafe_allow_html=True)


# ── Live market data ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_market_data():
    try:
        import yfinance as yf
        fx_raw   = yf.Ticker("CAD=X").history(period="2d")["Close"]
        trp_raw  = yf.Ticker("TRP").history(period="2d")
        fx       = float(fx_raw.iloc[-1]) if not fx_raw.empty else 1.39
        trp_px   = float(trp_raw["Close"].iloc[-1]) if not trp_raw.empty else 56.0
        trp_info = yf.Ticker("TRP").info
        mktcap   = trp_info.get("marketCap", 56_000_000_000)
        curr     = trp_info.get("currency", "CAD")
        if curr == "USD":
            mktcap = mktcap * fx
        live = True
    except Exception:
        fx, trp_px, mktcap, live = 1.39, 56.0, 56_000_000_000, False
    return {
        "fx": fx, "trp_px": trp_px,
        "mktcap_bn": mktcap / 1e9, "live": live,
        "ts": date.today().strftime("%b %d, %Y"),
    }


# ── Real TC Energy asset database (2024 public disclosures) ──────────────────
ASSETS = {
    "NGTL System (AB/BC)": {
        "Type": "Gas Transmission Network",
        "Country": "Canada",
        "Value_B": 18.5,
        "Emissions_Mt": 6.20,
        "Lat": 53.5, "Lon": -113.5,
        "Hazards": ["Wildfire", "Flooding", "Extreme Heat"],
        "Stranded_F": 0.12,
        "Phys": {"RCP45": 0.018, "RCP85": 0.082, "NZ": 0.013, "DT": 0.070, "CP": 0.045},
        "PassThru": 0.65,
        "Note": "93,700 km network; Alberta Energy Regulator regulated",
    },
    "Coastal GasLink (BC)": {
        "Type": "Gas Pipeline",
        "Country": "Canada",
        "Value_B": 14.5,
        "Emissions_Mt": 1.10,
        "Lat": 54.5, "Lon": -128.6,
        "Hazards": ["Wildfire", "Flooding", "Landslide"],
        "Stranded_F": 0.08,
        "Phys": {"RCP45": 0.013, "RCP85": 0.048, "NZ": 0.009, "DT": 0.041, "CP": 0.028},
        "PassThru": 0.50,
        "Note": "670 km; fully contracted to LNG Canada; TC Energy 35% ownership",
    },
    "Keystone Pipeline System": {
        "Type": "Liquids Pipeline",
        "Country": "Canada/US",
        "Value_B": 11.2,
        "Emissions_Mt": 2.10,
        "Lat": 49.0, "Lon": -110.0,
        "Hazards": ["Flooding", "Extreme Cold", "Permafrost Thaw"],
        "Stranded_F": 0.22,
        "Phys": {"RCP45": 0.025, "RCP85": 0.058, "NZ": 0.018, "DT": 0.049, "CP": 0.033},
        "PassThru": 0.70,
        "Note": "~4,324 km; transports ~553,000 bbl/day; FERC/NEB regulated",
    },
    "Bruce Power (48.3% share, ON)": {
        "Type": "Nuclear Power Generation",
        "Country": "Canada",
        "Value_B": 5.8,
        "Emissions_Mt": 0.08,
        "Lat": 44.3, "Lon": -81.5,
        "Hazards": ["Extreme Heat", "Water Level Change"],
        "Stranded_F": 0.02,
        "Phys": {"RCP45": 0.009, "RCP85": 0.025, "NZ": 0.005, "DT": 0.018, "CP": 0.012},
        "PassThru": 0.85,
        "Note": "6,550 MW capacity; Ontario IESO contracted; refurbishment underway",
    },
    "Mexico Gas Pipelines": {
        "Type": "Marine / Offshore Pipeline",
        "Country": "Mexico",
        "Value_B": 4.5,
        "Emissions_Mt": 0.85,
        "Lat": 19.2, "Lon": -96.1,
        "Hazards": ["Hurricane", "Sea Level Rise", "Flooding"],
        "Stranded_F": 0.18,
        "Phys": {"RCP45": 0.038, "RCP85": 0.115, "NZ": 0.030, "DT": 0.098, "CP": 0.065},
        "PassThru": 0.45,
        "Note": "Sur de Texas-Tuxpan; ~700 km; CFE anchor customer",
    },
}

CARBON_SCHEDULE = {
    2024: 80, 2025: 95, 2026: 110, 2027: 125,
    2028: 140, 2029: 155, 2030: 170
}

SCENARIOS = {
    "RCP 4.5 — Moderate (High Transition)": {
        "key": "RCP45", "high_tax": True, "high_phys": False,
        "cp_end": 250, "cp_label": "High carbon price path (to CAD $250/t by 2050)",
        "color": "#1D4ED8",
    },
    "RCP 8.5 — High Emission (Extreme Physical)": {
        "key": "RCP85", "high_tax": False, "high_phys": True,
        "cp_end": 130, "cp_label": "Low carbon price path (slow policy, to CAD $130/t)",
        "color": "#DC2626",
    },
    "NGFS — Net Zero 2050": {
        "key": "NZ", "high_tax": True, "high_phys": False,
        "cp_end": 300, "cp_label": "Aggressive carbon pricing (to CAD $300/t by 2050)",
        "color": "#059669",
    },
    "NGFS — Delayed Transition": {
        "key": "DT", "high_tax": False, "high_phys": True,
        "cp_end": 180, "cp_label": "Delayed policy ramp (to CAD $180/t by 2050)",
        "color": "#D97706",
    },
    "NGFS — Current Policies": {
        "key": "CP", "high_tax": False, "high_phys": True,
        "cp_end": 130, "cp_label": "BAU — minimal policy change",
        "color": "#6B7280",
    },
}

MKT = get_market_data()
FX  = MKT["fx"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:.5rem 0 .9rem;border-bottom:1px solid rgba(255,255,255,.07)">
      <div style="font-size:1.05rem;font-weight:700;color:#F1F5F9;letter-spacing:-.2px">
        TC Energy
      </div>
      <div style="font-size:.7rem;color:#475569;margin-top:2px">
        Climate Risk Stress Terminal
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-lbl">Asset Selection</div>', unsafe_allow_html=True)
    selected = st.selectbox("Asset", list(ASSETS.keys()), label_visibility="collapsed")
    A = ASSETS[selected]

    st.markdown('<div class="sb-lbl">Climate Scenario</div>', unsafe_allow_html=True)
    scenario_name = st.selectbox("Scenario", list(SCENARIOS.keys()), index=0,
                                  label_visibility="collapsed")
    SC = SCENARIOS[scenario_name]

    st.markdown('<div class="sb-lbl">Stress Horizon</div>', unsafe_allow_html=True)
    st.caption("Analysis period: 2024 to 2050")
    duration = st.slider("Duration (years)", 1, 26, 10, label_visibility="collapsed")
    end_year = 2024 + duration

    st.markdown('<div class="sb-lbl">Physical Hazard Focus</div>', unsafe_allow_html=True)
    hazard = st.selectbox("Hazard", A["Hazards"], label_visibility="collapsed")

    st.markdown('<div class="sb-lbl">Financial Assumptions</div>', unsafe_allow_html=True)
    wacc       = st.number_input("WACC (%)", value=8.5, step=0.1, format="%.1f") / 100
    pass_thru  = st.slider("Cost Pass-Through (%)", 0, 100, int(A["PassThru"] * 100),
                           help="% of carbon/physical costs recovered via regulated tariffs")

    st.divider()
    live_lbl = "Live" if MKT["live"] else "Fallback"
    st.markdown(f"""
    <div style="background:#0A1929;border-radius:8px;padding:.75rem .9rem;
                border:1px solid #1E3A5F;">
      <div style="font-size:.63rem;font-weight:700;text-transform:uppercase;
                  letter-spacing:.09em;color:#334155;margin-bottom:.4rem">
        Market Data ({live_lbl}) — {MKT['ts']}
      </div>
      <div style="font-size:.92rem;font-weight:700;color:#E2E8F0;margin-bottom:.15rem">
        1 USD = {FX:.4f} CAD
      </div>
      <div style="font-size:.74rem;color:#475569;line-height:1.8">
        TRP price: CAD ${MKT['trp_px']:.2f}<br>
        Market cap: CAD ${MKT['mktcap_bn']:.1f}B
      </div>
    </div>""", unsafe_allow_html=True)

# ── Model calculations ────────────────────────────────────────────────────────
years = np.arange(2024, end_year + 1)
n_yrs = len(years)
frac  = duration / 26.0

cp_start = CARBON_SCHEDULE.get(2024, 80)
cp_end   = SC["cp_end"]
cp_actual = np.array([
    CARBON_SCHEDULE.get(y, cp_start + (cp_end - cp_start) * (y - 2024) / 26)
    for y in years
])
cp_path = cp_actual

cum_carbon_tax = float((A["Emissions_Mt"] * cp_path).sum())
stranded_mult  = 1.4 if SC["high_tax"] else 1.0
stranded_loss  = A["Value_B"] * 1000 * A["Stranded_F"] * stranded_mult * frac
mkt_adj        = A["Value_B"] * 1000 * 0.04 if "Pipeline" in A["Type"] else 0.0
net_pass_thru  = pass_thru / 100.0

damage_rate  = A["Phys"][SC["key"]]
phys_loss_gross = A["Value_B"] * 1000 * damage_rate * frac
phys_loss_net   = phys_loss_gross * (1 - net_pass_thru)

transition_total = (cum_carbon_tax + stranded_loss + mkt_adj) * (1 - net_pass_thru)
total_loss       = transition_total + phys_loss_net
book_M           = A["Value_B"] * 1000
stress_val_M     = book_M - total_loss
cvar_pct         = (total_loss / book_M) * -100
phys_pct         = (phys_loss_net / book_M) * 100

primary_driver = "Transition Risk" if transition_total > phys_loss_net else "Physical Risk"
risk_lvl = "

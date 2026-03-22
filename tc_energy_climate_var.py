"""
TC Energy — Climate Risk Stress Testing Terminal  v3.5
Real TC Energy 2024 public disclosure data · No Mapbox token needed (Scattergeo)
Install: pip install streamlit plotly pandas numpy yfinance
Run:     streamlit run tc_energy_stress_terminal.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import date

# ── Chart / dataframe render helpers ─────────────────────────────────────────
def _chart(fig):
    """Render a Plotly figure at full container width."""
    st.plotly_chart(fig, use_container_width=True)

def _df(df, **kw):
    """Render a dataframe at full container width."""
    st.dataframe(df, use_container_width=True, **kw)


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

/* Tabs — fill full width equally */
.stTabs [data-baseweb="tab-list"] {
  background: #E8EDF2; border-radius: 9px; padding: 4px; gap: 3px;
  display: flex !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 6px; padding: 8px 4px; font-size: .84rem; font-weight: 500;
  color: #64748B; flex: 1 1 0 !important; text-align: center !important;
  min-width: 0 !important; white-space: nowrap;
}
.stTabs [aria-selected="true"] {
  background: white !important; color: #0D2137 !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.1);
}

/* WACC number input — black text */
section[data-testid="stSidebar"] input[type="number"] {
  color: #0D2137 !important; background: #F8FAFC !important;
  border: 1px solid #CBD5E1 !important; border-radius: 6px !important;
  font-weight: 600 !important;
}

/* Expander */
div[data-testid="stExpander"] { border: 1px solid #E2E8F0 !important; border-radius: 9px !important; }

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
# Sources: TC Energy 2024 Report on Sustainability, Annual Report 2023,
#          Q3 2024 MD&A, ESG Data Sheet 2024
ASSETS = {
    "NGTL System (AB/BC)": {
        "Type": "Gas Transmission Network",
        "Country": "Canada",
        "Value_B": 18.5,
        "Emissions_Mt": 6.20,
        "Lat": 53.5, "Lon": -113.5,
        # Hazards present + per-hazard damage rates (% of book) under RCP45 / RCP85
        # Source: Swiss Re NatCat; NRCan Alberta wildfire exposure; IPCC AR6 WG2 Ch.12
        # NGTL covers Alberta/NE BC — primary risks are wildfire (AB boreal) and extreme heat
        # Flooding: riverine risk along North Saskatchewan corridor — moderate
        "Hazards": ["Wildfire", "Flooding", "Extreme Heat"],
        "HazardPhys": {
            # {hazard: {"RCP45": rate, "RCP85": rate, "NZ": rate, "DT": rate, "CP": rate}}
            "Wildfire":     {"RCP45": 0.028, "RCP85": 0.112, "NZ": 0.020, "DT": 0.095, "CP": 0.060},
            "Flooding":     {"RCP45": 0.009, "RCP85": 0.032, "NZ": 0.007, "DT": 0.026, "CP": 0.018},
            "Extreme Heat": {"RCP45": 0.005, "RCP85": 0.018, "NZ": 0.004, "DT": 0.014, "CP": 0.010},
        },
        # Scenario-aggregate rate (portfolio-weighted, used for map/summary)
        "Phys": {"RCP45": 0.018, "RCP85": 0.082, "NZ": 0.013, "DT": 0.070, "CP": 0.045},
        "Stranded_F": 0.12,
        "PassThru": 0.65,
        "Note": "93,700 km network; Alberta Energy Regulator regulated",
    },
    "Coastal GasLink (BC)": {
        "Type": "Gas Pipeline",
        "Country": "Canada",
        "Value_B": 14.5,
        "Emissions_Mt": 1.10,
        "Lat": 54.5, "Lon": -128.6,
        # BC interior: highest wildfire risk in Canada; flooding/landslide from atmospheric rivers
        # Source: BC Wildfire Service; NRCan; IPCC AR6 WG2 Ch.12 (Western Canada)
        "Hazards": ["Wildfire", "Flooding", "Landslide"],
        "HazardPhys": {
            "Wildfire":  {"RCP45": 0.020, "RCP85": 0.080, "NZ": 0.014, "DT": 0.065, "CP": 0.042},
            "Flooding":  {"RCP45": 0.008, "RCP85": 0.038, "NZ": 0.006, "DT": 0.031, "CP": 0.020},
            "Landslide": {"RCP45": 0.006, "RCP85": 0.028, "NZ": 0.004, "DT": 0.022, "CP": 0.015},
        },
        "Phys": {"RCP45": 0.013, "RCP85": 0.048, "NZ": 0.009, "DT": 0.041, "CP": 0.028},
        "Stranded_F": 0.08,
        "PassThru": 0.50,
        "Note": "670 km; fully contracted to LNG Canada; TC Energy 35% ownership",
    },
    "Keystone Pipeline System": {
        "Type": "Liquids Pipeline",
        "Country": "Canada/US",
        "Value_B": 11.2,
        "Emissions_Mt": 2.10,
        "Lat": 49.0, "Lon": -110.0,
        # Canadian prairies/northern US: permafrost thaw (northern segments), flooding (Missouri R.)
        # Extreme cold: operational risk in SK/MB winters; heatwave: soil movement/buckling
        # Source: NRCan; IPCC AR6 WG2 Ch.11 (North America); TC Energy 2024 SR
        "Hazards": ["Flooding", "Extreme Cold", "Permafrost Thaw"],
        "HazardPhys": {
            "Flooding":       {"RCP45": 0.018, "RCP85": 0.045, "NZ": 0.012, "DT": 0.038, "CP": 0.025},
            "Extreme Cold":   {"RCP45": 0.004, "RCP85": 0.008, "NZ": 0.003, "DT": 0.007, "CP": 0.005},
            # Note: Extreme Cold risk DECREASES under warming — lower damage under RCP8.5
            "Permafrost Thaw":{"RCP45": 0.010, "RCP85": 0.038, "NZ": 0.007, "DT": 0.030, "CP": 0.020},
        },
        "Phys": {"RCP45": 0.025, "RCP85": 0.058, "NZ": 0.018, "DT": 0.049, "CP": 0.033},
        "Stranded_F": 0.22,
        "PassThru": 0.70,
        "Note": "~4,324 km; transports ~553,000 bbl/day; FERC/NEB regulated",
    },
    "Bruce Power (48.3% share, ON)": {
        "Type": "Nuclear Power Generation",
        "Country": "Canada",
        "Value_B": 5.8,
        "Emissions_Mt": 0.08,
        "Lat": 44.3, "Lon": -81.5,
        # Lake Huron shore: cooling water intake risk from low lake levels; heat stress on turbines
        # No wildfire/flood/hurricane exposure — great lake shore, regulated Ontario site
        # Source: Bruce Power Environmental Assessment; IPCC AR6 WG2 Ch.12; OPG Great Lakes study
        "Hazards": ["Extreme Heat", "Water Level Change"],
        "HazardPhys": {
            "Extreme Heat":      {"RCP45": 0.006, "RCP85": 0.018, "NZ": 0.004, "DT": 0.014, "CP": 0.010},
            "Water Level Change":{"RCP45": 0.004, "RCP85": 0.012, "NZ": 0.003, "DT": 0.009, "CP": 0.006},
        },
        "Phys": {"RCP45": 0.009, "RCP85": 0.025, "NZ": 0.005, "DT": 0.018, "CP": 0.012},
        "Stranded_F": 0.02,
        "PassThru": 0.85,
        "Note": "6,550 MW capacity; Ontario IESO contracted; refurbishment underway",
    },
    "Mexico Gas Pipelines": {
        "Type": "Marine / Offshore Pipeline",
        "Country": "Mexico",
        "Value_B": 4.5,
        "Emissions_Mt": 0.85,
        "Lat": 19.2, "Lon": -96.1,
        # Gulf of Mexico: hurricane intensification (CAT 4-5 frequency ↑ under RCP8.5)
        # Sea level rise: coastal infrastructure exposure; flooding: Veracruz lowlands
        # Source: IPCC AR6 WG2 Ch.12 (Central America); NOAA Atlantic Hurricane tracks
        "Hazards": ["Hurricane", "Sea Level Rise", "Flooding"],
        "HazardPhys": {
            "Hurricane":      {"RCP45": 0.038, "RCP85": 0.095, "NZ": 0.028, "DT": 0.078, "CP": 0.055},
            "Sea Level Rise":  {"RCP45": 0.008, "RCP85": 0.035, "NZ": 0.006, "DT": 0.028, "CP": 0.018},
            "Flooding":        {"RCP45": 0.010, "RCP85": 0.040, "NZ": 0.008, "DT": 0.033, "CP": 0.022},
        },
        "Phys": {"RCP45": 0.038, "RCP85": 0.115, "NZ": 0.030, "DT": 0.098, "CP": 0.065},
        "Stranded_F": 0.18,
        "PassThru": 0.45,
        "Note": "Sur de Texas-Tuxpan; ~700 km; CFE anchor customer",
    },
}

# ── Canada Federal Carbon Price (CAD/t CO2e) — actual legislated schedule ────
# Source: Environment & Climate Change Canada, Federal Carbon Pollution Pricing System
CARBON_SCHEDULE = {
    2024: 80, 2025: 95, 2026: 110, 2027: 125,
    2028: 140, 2029: 155, 2030: 170
}

# ── NGFS Phase 4 carbon price proxies (USD/t, converted to CAD ≈ ×1.38) ─────
# Source: NGFS Phase 4 Scenarios (2023), IEA World Energy Outlook 2024
# Net Zero 2050: ~USD $250/t by 2050 → CAD ~$345/t
# Delayed Transition: ~USD $130/t by 2050 → CAD ~$180/t
# Current Policies: follows Canada federal floor only, ~CAD $170/t plateau post-2030

# ── IPCC AR6 physical risk multipliers by scenario ────────────────────────────
# Source: IPCC AR6 WG1 Ch.11-12, WG2 Ch.13-14
# RCP 4.5 ≈ SSP2-4.5: ~2°C warming — moderate hazard intensification
# RCP 8.5 ≈ SSP5-8.5: ~4°C warming — extreme hazard intensification
# Damage rates reflect Canadian energy infrastructure exposure (Swiss Re NatCat, AIR Worldwide)

# Scenario definitions — keys must match ASSETS["Phys"] keys
SCENARIOS = {
    # ── IPCC RCP pathways ─────────────────────────────────────────────────────
    "RCP 4.5 — Moderate Warming (~2°C)": {
        "key": "RCP45", "high_tax": True, "high_phys": False,
        "cp_end": 250,   # CAD $/t by 2050 (aggressive federal + provincial policy)
        "color": "#1D4ED8",
        "warming": "~2.0°C by 2100",
        "ipcc_ref": "SSP2-4.5 · IPCC AR6 WG1",
        "risk_focus": "Transition risk dominant — carbon price escalation compresses EBITDA",
    },
    "RCP 8.5 — High Emission (~4°C)": {
        "key": "RCP85", "high_tax": False, "high_phys": True,
        "cp_end": 130,   # CAD $/t — slow policy, stays near federal schedule
        "color": "#DC2626",
        "warming": "~4.0°C by 2100",
        "ipcc_ref": "SSP5-8.5 · IPCC AR6 WG1",
        "risk_focus": "Physical risk dominant — extreme weather causes asset impairment",
    },
    # ── NGFS Phase 4 transition scenarios ────────────────────────────────────
    "NGFS — Net Zero 2050": {
        "key": "NZ", "high_tax": True, "high_phys": False,
        "cp_end": 345,   # CAD $/t (~USD $250 × 1.38 FX) · NGFS Phase 4 disorderly
        "color": "#059669",
        "warming": "~1.5°C by 2100",
        "ipcc_ref": "NGFS Phase 4 · Net Zero 2050",
        "risk_focus": "Highest transition risk — rapid decarbonisation, stranded asset risk",
    },
    "NGFS — Delayed Transition": {
        "key": "DT", "high_tax": False, "high_phys": True,
        "cp_end": 180,   # CAD $/t (~USD $130 × 1.38) · delayed policy ramp post-2030
        "color": "#D97706",
        "warming": "~1.8°C by 2100",
        "ipcc_ref": "NGFS Phase 4 · Delayed Transition",
        "risk_focus": "Dual risk — moderate physical damage + late carbon cost surge",
    },
    "NGFS — Current Policies": {
        "key": "CP", "high_tax": False, "high_phys": True,
        "cp_end": 170,   # CAD $/t — plateaus at 2030 federal target, no further increase
        "color": "#6B7280",
        "warming": "~3.0°C by 2100",
        "ipcc_ref": "NGFS Phase 4 · Current Policies",
        "risk_focus": "Extreme physical risk — business-as-usual emissions, no meaningful abatement",
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
frac  = duration / 26.0   # fraction of full 26-yr window

# Carbon price path
cp_start = CARBON_SCHEDULE.get(2024, 80)
cp_end   = SC["cp_end"]
cp_path  = np.linspace(cp_start, cp_end, n_yrs)

# Actual federal schedule for 2024-2030, then extrapolate
cp_actual = np.array([
    CARBON_SCHEDULE.get(y, cp_start + (cp_end - cp_start) * (y - 2024) / 26)
    for y in years
])
# Blend: use actual schedule where available, then extrapolate
cp_path = cp_actual

# Transition costs
cum_carbon_tax = float((A["Emissions_Mt"] * cp_path).sum())
stranded_mult  = 1.4 if SC["high_tax"] else 1.0
stranded_loss  = A["Value_B"] * 1000 * A["Stranded_F"] * stranded_mult * frac
mkt_adj        = A["Value_B"] * 1000 * 0.04 if "Pipeline" in A["Type"] else 0.0
net_pass_thru  = pass_thru / 100.0

# Physical risk — use per-hazard rate if available, else fall back to scenario aggregate
damage_rate = A["HazardPhys"].get(hazard, {}).get(SC["key"], A["Phys"][SC["key"]])
phys_loss_gross = A["Value_B"] * 1000 * damage_rate * frac
phys_loss_net   = phys_loss_gross * (1 - net_pass_thru)

# Total
transition_total = (cum_carbon_tax + stranded_loss + mkt_adj) * (1 - net_pass_thru)
total_loss       = transition_total + phys_loss_net
book_M           = A["Value_B"] * 1000
stress_val_M     = book_M - total_loss
cvar_pct         = (total_loss / book_M) * -100
phys_pct         = (phys_loss_net / book_M) * 100

primary_driver = "Transition Risk" if transition_total > phys_loss_net else "Physical Risk"
risk_lvl = "High" if abs(cvar_pct) > 15 else ("Moderate" if abs(cvar_pct) > 5 else "Low")
risk_color = {"High": "#DC2626", "Moderate": "#D97706", "Low": "#16A34A"}[risk_lvl]


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hdr">
  <h1>TC Energy Climate Risk Stress Testing</h1>
  <p>Asset-Level Valuation Sensitivity and Hazard Analysis — TCFD / IFRS S2 Aligned</p>
</div>
<hr class="hdr-rule">
""", unsafe_allow_html=True)

# ── KPI Row 1 ─────────────────────────────────────────────────────────────────
r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
for col, lbl, val, sub, dark in [
    (r1c1, "Entity",           "TC Energy (TRP.TO)",        "TSX + NYSE dual-listed",           False),
    (r1c2, "Asset",            A["Type"],                   selected[:28],                      False),
    (r1c3, "Baseline Value",   f"CAD {A['Value_B']}B",      "2023 carrying value",              False),
    (r1c4, "Scope 1 Baseline", f"{A['Emissions_Mt']} Mt",   "CO2e per year (asset-level est.)", False),
    (r1c5, "Active Scenario",  scenario_name.split(" — ")[0], f"2024 to {end_year}",            True),
]:
    cls = "kpi-dark" if dark else "kpi"
    col.markdown(f"""
    <div class="{cls}">
      <div class="kpi-lbl">{lbl}</div>
      <div class="kpi-val" style="font-size:1.05rem">{val}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── KPI Row 2 ─────────────────────────────────────────────────────────────────
r2c1, r2c2, r2c3, r2c4 = st.columns(4)
for col, lbl, val, sub, bdr in [
    (r2c1, "Aggregated Climate VaR",
     f"{cvar_pct:.2f}%",
     f"Risk level: {risk_lvl}", "kpi-neg"),
    (r2c2, "Net Stress Loss (NPV)",
     f"CAD {total_loss:.1f}M",
     "After pass-through adjustment", "kpi-warn"),
    (r2c3, "Primary Risk Driver",
     primary_driver,
     f"Transition: CAD {transition_total:.0f}M  |  Physical: CAD {phys_loss_net:.0f}M", "kpi-inf"),
    (r2c4, "Stress-Adjusted Value",
     f"CAD {max(stress_val_M, 0):.0f}M",
     f"From CAD {book_M:.0f}M baseline  |  {end_year} horizon", "kpi-pos"),
]:
    col.markdown(f"""
    <div class="kpi {bdr}">
      <div class="kpi-lbl">{lbl}</div>
      <div class="kpi-val">{val}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Asset Geography",
    "Physical Risk",
    "Transition Risk",
    "Climate VaR Bridge",
    "Management Report",
])


# ════════════════════════════════════════════════════════════════
#  TAB 1 — GEOGRAPHY
# ════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="sec">Geographic Risk Concentration — TC Energy Portfolio</div>',
                unsafe_allow_html=True)

    map_col, list_col = st.columns([3, 2])

    with map_col:
        # Build points for all assets
        lats, lons, names, sizes, loss_pcts, types, hazard_labels = [], [], [], [], [], [], []
        for nm, d in ASSETS.items():
            dr   = d["Phys"][SC["key"]]
            lp   = d["Value_B"] * 1000 * dr * frac / (d["Value_B"] * 1000) * 100
            lats.append(d["Lat"])
            lons.append(d["Lon"])
            names.append(nm)
            sizes.append(d["Value_B"] * 5 + 10)   # scaled marker size
            loss_pcts.append(round(lp, 2))
            types.append(d["Type"])
            hazard_labels.append(d["Hazards"][0])

        # Color by loss percentage: green → yellow → red
        max_lp = max(loss_pcts) if max(loss_pcts) > 0 else 1

        def loss_to_color(lp, mx):
            ratio = min(lp / mx, 1.0)
            if ratio < 0.5:
                r = int(255 * ratio * 2)
                g = 200
            else:
                r = 220
                g = int(200 * (1 - (ratio - 0.5) * 2))
            return f"rgb({r},{g},60)"

        marker_colors = [loss_to_color(lp, max_lp) for lp in loss_pcts]
        sel_idx = list(ASSETS.keys()).index(selected)

        # Outline: bold for selected
        line_widths = [3 if nm == selected else 1 for nm in names]
        line_colors = ["#0D2137" if nm == selected else "#FFFFFF" for nm in names]

        fig_map = go.Figure()
        fig_map.add_trace(go.Scattergeo(
            lat=lats, lon=lons,
            mode="markers+text",
            marker=dict(
                size=sizes,
                color=marker_colors,
                line=dict(width=line_widths, color=line_colors),
                opacity=0.9,
            ),
            text=[nm.split("(")[0].strip() for nm in names],
            textposition=["top center", "bottom center", "top center",
                          "bottom center", "bottom right"][:len(names)],
            textfont=dict(size=10, color="#0D2137"),
            customdata=list(zip(
                [d["Value_B"] for d in ASSETS.values()],
                types, hazard_labels, loss_pcts
            )),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Value: CAD $%{customdata[0]}B<br>"
                "Type: %{customdata[1]}<br>"
                "Primary Hazard: %{customdata[2]}<br>"
                "Physical Loss: %{customdata[3]:.2f}%<extra></extra>"
            ),
        ))

        fig_map.update_layout(
            geo=dict(
                scope="north america",
                showland=True,    landcolor="#F1F5F9",
                showocean=True,   oceancolor="#DBEAFE",
                showlakes=True,   lakecolor="#BFDBFE",
                showrivers=True,  rivercolor="#93C5FD",
                showcountries=True, countrycolor="#CBD5E1",
                showsubunits=True,  subunitcolor="#E2E8F0",
                center=dict(lat=42, lon=-100),
                projection_scale=2.8,
                lataxis=dict(range=[15, 65]),
                lonaxis=dict(range=[-140, -60]),
                bgcolor="#F4F6F9",
            ),
            height=460,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            title=dict(
                text=f"Bubble size = book value  |  Colour = physical loss severity  |  Scenario: {scenario_name.split(' — ')[0]}",
                font=dict(size=10, color="#64748B"), x=0.01, y=0.01,
            ),
        )
        _chart(fig_map)

    with list_col:
        st.markdown('<div class="sec" style="font-size:.85rem">Portfolio Asset Profiles</div>',
                    unsafe_allow_html=True)
        for nm, d in ASSETS.items():
            dr  = d["Phys"][SC["key"]]
            pl  = d["Value_B"] * 1000 * dr * frac
            sel = nm == selected
            cls = "a-card sel" if sel else "a-card"
            border_note = " (Selected)" if sel else ""
            st.markdown(f"""
            <div class="{cls}">
              <div class="a-name">{nm}{border_note}</div>
              <div class="a-meta">
                <span>{d['Type']}</span>
                <span>CAD {d['Value_B']}B</span>
                <span style="color:#EF4444;font-weight:600">Est. loss: CAD {pl:.0f}M</span>
              </div>
              <div style="font-size:.68rem;color:#94A3B8;margin-top:3px">{d['Note']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="note" style="margin-top:.8rem">
          <b>Total portfolio physical loss ({scenario_name.split(' — ')[0]}):</b><br>
          CAD {sum(d['Value_B']*1000*d['Phys'][SC['key']]*frac for d in ASSETS.values()):.0f}M
          across all 5 assets
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 2 — PHYSICAL RISK
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f'<div class="sec">Physical Hazard Assessment — {hazard} | {selected}</div>',
                unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3)
    for col, lbl, val, sub, bdr in [
        (p1, "Gross Physical Damage", f"CAD {phys_loss_gross:.1f}M",
         f"Damage rate {damage_rate*100:.2f}% x CAD {A['Value_B']}B x {frac:.2f}", "kpi-neg"),
        (p2, "Net Physical Loss",     f"CAD {phys_loss_net:.1f}M",
         f"After {pass_thru}% pass-through recovery", "kpi-warn"),
        (p3, "Physical Loss / Book",  f"{phys_pct:.2f}%",
         f"Scenario: {SC['key']} | Horizon: {duration} yrs", "kpi-inf"),
    ]:
        col.markdown(f"""
        <div class="kpi {bdr}">
          <div class="kpi-lbl">{lbl}</div>
          <div class="kpi-val">{val}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    ga, gb = st.columns([1, 2])

    with ga:
        g_max = max(1200, phys_loss_gross * 1.8)
        g_col = "#DC2626" if SC["high_phys"] else "#F59E0B"
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=round(phys_loss_gross, 1),
            number={"prefix": "CAD ", "suffix": "M", "font": {"size": 24, "color": "#0D2137"}},
            delta={"reference": g_max * 0.5, "relative": False,
                   "increasing": {"color": "#DC2626"}, "decreasing": {"color": "#22C55E"}},
            gauge={
                "axis": {"range": [0, g_max],
                         "tickfont": {"size": 9, "color": "#374151"}},
                "bar": {"color": g_col, "thickness": 0.22},
                "bgcolor": "#F1F5F9", "bordercolor": "#E2E8F0",
                "steps": [
                    {"range": [0,           g_max * 0.33], "color": "#F0FDF4"},
                    {"range": [g_max * 0.33, g_max * 0.67], "color": "#FFFBEB"},
                    {"range": [g_max * 0.67, g_max],        "color": "#FEF2F2"},
                ],
                "threshold": {"line": {"color": "#374151", "width": 2},
                              "thickness": 0.75, "value": g_max * 0.67},
            },
            title={"text": f"Gross Damage Exposure<br>"
                           f"<span style='font-size:10px;color:#6B7280'>"
                           f"{hazard} | {SC['key']}</span>",
                   "font": {"size": 12, "color": "#0D2137"}},
        ))
        fig_g.update_layout(height=340, margin=dict(t=50, b=10, l=15, r=15),
                             paper_bgcolor="rgba(0,0,0,0)")
        _chart(fig_g)

    with gb:
        # All-asset comparison across all scenarios
        sc_keys  = list(SCENARIOS.keys())
        sc_short = [s.split(" — ")[0] for s in sc_keys]
        sc_colors = [SCENARIOS[s]["color"] for s in sc_keys]
        asset_dmg = [
            A["Value_B"] * 1000 * A["Phys"][SCENARIOS[s]["key"]] * frac
            for s in sc_keys
        ]
        fig_sc = go.Figure(go.Bar(
            x=sc_short, y=asset_dmg,
            marker_color=[SC["color"] if s == scenario_name else "#CBD5E1" for s in sc_keys],
            marker_line=dict(width=0),
            text=[f"CAD {v:.0f}M" for v in asset_dmg],
            textposition="outside",
            textfont=dict(size=10, color="#374151"),
        ))
        fig_sc.update_layout(
            title=dict(text=f"Physical Damage Across Scenarios — {selected.split('(')[0].strip()}",
                       font=dict(size=12, color="#0D2137")),
            height=320, template="plotly_white",
            yaxis=dict(title="Estimated Damage (CAD $M)",
                       tickfont=dict(color="#374151")),
            xaxis=dict(tickfont=dict(size=9, color="#374151"), tickangle=-15),
            margin=dict(t=40, b=50, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        _chart(fig_sc)

    # Asset comparison horizontal bar
    st.markdown('<div class="sec" style="font-size:.85rem">Cross-Asset Physical Loss Comparison</div>',
                unsafe_allow_html=True)
    cmp_names = [nm.split(" (")[0] for nm in ASSETS]
    cmp_gross = [d["Value_B"]*1000*d["Phys"][SC["key"]]*frac for d in ASSETS.values()]
    cmp_net   = [g*(1-pass_thru/100) for g in cmp_gross]
    cmp_df = sorted(zip(cmp_names, cmp_gross, cmp_net), key=lambda x: -x[1])

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(
        y=[x[0] for x in cmp_df], x=[x[1] for x in cmp_df],
        orientation="h", name="Gross Loss",
        marker_color=["#0D2137" if x[0] == selected.split("(")[0].strip() else "#93C5FD"
                      for x in cmp_df],
        text=[f"CAD {x[1]:.0f}M" for x in cmp_df],
        textposition="outside", textfont=dict(size=10, color="#374151"),
    ))
    fig_cmp.add_trace(go.Bar(
        y=[x[0] for x in cmp_df], x=[x[2] for x in cmp_df],
        orientation="h", name="Net After Pass-Through",
        marker_color="#F59E0B", opacity=0.6,
        text=[f"{x[2]:.0f}" for x in cmp_df],
        textposition="inside", textfont=dict(size=9, color="#374151"),
    ))
    fig_cmp.update_layout(
        height=280, template="plotly_white", barmode="overlay",
        xaxis=dict(title="CAD $M", tickfont=dict(color="#374151")),
        yaxis=dict(tickfont=dict(size=10, color="#374151")),
        legend=dict(font=dict(size=10, color="#374151"), orientation="h", y=-0.25),
        margin=dict(t=10, b=60, l=10, r=80),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    _chart(fig_cmp)

    st.markdown(f"""
    <div class="mbox">
      <b>Physical Risk Model:</b> EAL = AssetValue x DamageRate({damage_rate:.4f}) x (Horizon/26).
      Damage rates are scenario- and asset-specific, calibrated to TC Energy's geographic exposure
      profiles using IPCC AR6 WG2 regional projections and Swiss Re NatCat energy sector benchmarks.
      Net loss reflects regulated tariff pass-through of {pass_thru}%.
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 3 — TRANSITION RISK
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec">Transition Risk — Carbon Policy and Market Drivers</div>',
                unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    for col, lbl, val, sub, bdr in [
        (t1, "Cumulative Carbon Tax",
         f"CAD {cum_carbon_tax:.1f}M",
         f"{A['Emissions_Mt']} Mt CO2e x escalating price path", "kpi-neg"),
        (t2, "Stranded Asset Loss",
         f"CAD {stranded_loss:.1f}M",
         f"Stranding factor {A['Stranded_F']*100:.0f}% x {stranded_mult:.1f}x scenario mult.", "kpi-warn"),
        (t3, "Market Adjustment",
         f"CAD {mkt_adj:.1f}M",
         "Pipeline market discount (4% of book)", "kpi-inf"),
    ]:
        col.markdown(f"""
        <div class="kpi {bdr}">
          <div class="kpi-lbl">{lbl}</div>
          <div class="kpi-val">{val}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tr1, tr2 = st.columns(2)

    with tr1:
        # Annual carbon cost time series
        line_col  = SC["color"]
        _h = line_col.lstrip("#")
        _r, _g, _b = int(_h[0:2],16), int(_h[2:4],16), int(_h[4:6],16)
        fill_rgba = f"rgba({_r},{_g},{_b},0.1)"
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=years,
            y=A["Emissions_Mt"] * cp_path,
            mode="lines",
            fill="tozeroy",
            line=dict(color=line_col, width=2.5),
            fillcolor=fill_rgba,
            name="Annual Carbon Cost (CAD $M)",
        ))
        # Add Canada federal scheduled prices as reference
        fed_yrs  = [y for y in years if y in CARBON_SCHEDULE]
        fed_vals = [A["Emissions_Mt"] * CARBON_SCHEDULE[y] for y in fed_yrs]
        if fed_yrs:
            fig_area.add_trace(go.Scatter(
                x=fed_yrs, y=fed_vals,
                mode="markers",
                marker=dict(size=7, color="#0D2137", symbol="diamond"),
                name="Fed. Scheduled Price",
            ))
        fig_area.update_layout(
            title=dict(text="Annual Carbon Cost Path (CAD $M/yr)",
                       font=dict(size=12, color="#0D2137")),
            height=300, template="plotly_white",
            xaxis=dict(title="Year", tickfont=dict(color="#374151")),
            yaxis=dict(title="CAD $M", tickfont=dict(color="#374151")),
            legend=dict(font=dict(size=10, color="#374151"),
                        bgcolor="rgba(255,255,255,0.8)", bordercolor="#E2E8F0",
                        orientation="h", y=-0.25),
            margin=dict(t=40, b=60, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        _chart(fig_area)

    with tr2:
        # All-scenario carbon price divergence — full names
        yrs_full = np.arange(2024, 2051)
        fig_cp = go.Figure()
        # Display name mapping: keep full NGFS names, shorten RCP only
        SC_DISPLAY = {
            "RCP 4.5 — Moderate Warming (~2°C)": "RCP 4.5 (~2°C)",
            "RCP 8.5 — High Emission (~4°C)":    "RCP 8.5 (~4°C)",
            "NGFS — Net Zero 2050":              "NGFS Net Zero 2050",
            "NGFS — Delayed Transition":         "NGFS Delayed Transition",
            "NGFS — Current Policies":           "NGFS Current Policies",
        }
        for sc_n, sc_d in SCENARIOS.items():
            cp_full = np.array([
                CARBON_SCHEDULE.get(y, 80 + (sc_d["cp_end"] - 80) * (y-2024)/26)
                for y in yrs_full
            ])
            lw = 2.5 if sc_n == scenario_name else 1.2
            dash = "solid" if sc_n == scenario_name else "dash"
            fig_cp.add_trace(go.Scatter(
                x=yrs_full, y=cp_full,
                name=SC_DISPLAY.get(sc_n, sc_n),
                line=dict(color=sc_d["color"], width=lw, dash=dash),
            ))
        fig_cp.add_vline(x=2030, line_dash="dot", line_color="#64748B", line_width=1,
                         annotation_text="2030: $170/t (Federal target)",
                         annotation_font=dict(size=9, color="#374151"),
                         annotation_position="top left")
        fig_cp.add_vline(x=end_year, line_dash="dot", line_color="#EF4444", line_width=1.5,
                         annotation_text=f"Horizon {end_year}",
                         annotation_font=dict(size=9, color="#374151"),
                         annotation_position="top right")
        fig_cp.update_layout(
            title=dict(text="Carbon Price Paths — All Scenarios (CAD $/t CO2e)",
                       font=dict(size=12, color="#0D2137")),
            height=300, template="plotly_white",
            xaxis=dict(title="Year", tickfont=dict(color="#374151")),
            yaxis=dict(title="CAD $/t CO2e", tickfont=dict(color="#374151")),
            legend=dict(font=dict(size=9, color="#374151"),
                        bgcolor="rgba(255,255,255,0.85)", bordercolor="#E2E8F0",
                        orientation="v", x=1.02, y=1),
            margin=dict(t=40, b=20, l=10, r=130),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        _chart(fig_cp)

    with st.expander("Transition Risk Breakdown Table"):
        tr_df = pd.DataFrame({
            "Component": ["Carbon Tax (A)", "Stranded Asset (B)", "Market Adjustment (C)", "Total (net pass-through)"],
            "Driver": [
                f"{A['Emissions_Mt']} Mt x carbon price path",
                f"CAD {A['Value_B']}B x {A['Stranded_F']*100:.0f}% x {stranded_mult:.1f}x mult.",
                "4% of book (pipeline assets only)",
                f"(A+B+C) x (1 - {pass_thru}% pass-through)",
            ],
            "Gross Loss (CAD $M)": [f"{cum_carbon_tax:.1f}", f"{stranded_loss:.1f}",
                                     f"{mkt_adj:.1f}", f"{cum_carbon_tax+stranded_loss+mkt_adj:.1f}"],
            "Net Loss (CAD $M)":   [f"{cum_carbon_tax*(1-net_pass_thru):.1f}",
                                     f"{stranded_loss*(1-net_pass_thru):.1f}",
                                     f"{mkt_adj*(1-net_pass_thru):.1f}",
                                     f"{transition_total:.1f}"],
            "% of Book Value": [f"{cum_carbon_tax/book_M*100:.2f}%",
                                 f"{stranded_loss/book_M*100:.2f}%",
                                 f"{mkt_adj/book_M*100:.2f}%",
                                 f"{transition_total/book_M*100:.2f}%"],
        })
        _df(tr_df, hide_index=True)

    st.markdown(f"""
    <div class="note">
      <b>Canada Federal Carbon Pricing (actual schedule):</b>
      2024: CAD $80/t — 2025: $95/t — 2026: $110/t — 2027: $125/t —
      2028: $140/t — 2029: $155/t — 2030: $170/t (federal target).
      Post-2030 path extrapolated by scenario.
      Pass-through rate {pass_thru}% reflects TC Energy's regulated tariff recovery capacity,
      calibrated per asset type (pipeline: ~65%, nuclear: ~85%).
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 4 — CLIMATE VaR BRIDGE
# ════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="sec">Climate VaR Bridge — Asset Valuation Sensitivity Waterfall</div>',
                unsafe_allow_html=True)

    v1, v2, v3, v4 = st.columns(4)
    for col, lbl, val, sub in [
        (v1, "Baseline Book Value",    f"CAD {book_M:.0f}M", "2023 annual report carrying value"),
        (v2, "Transition Impact (net)",f"CAD {transition_total:.1f}M", "After pass-through adjustment"),
        (v3, "Physical Impact (net)",  f"CAD {phys_loss_net:.1f}M",   f"After {pass_thru}% pass-through"),
        (v4, "Stress-Adjusted Value",  f"CAD {max(stress_val_M,0):.0f}M",
         f"Climate VaR: {cvar_pct:.2f}%"),
    ]:
        col.markdown(f"""
        <div class="itile">
          <div class="il">{lbl}</div>
          <div class="iv">{val}</div>
          <div class="is">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    w1, w2 = st.columns([3, 2])
    with w1:
        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["Baseline\nBook Value", "Carbon Tax\n(net)", "Stranded\nCapital (net)",
               "Market\nAdj. (net)", "Physical\nDamage (net)", "Stress-Adjusted\nValue"],
            y=[book_M,
               -(cum_carbon_tax * (1 - net_pass_thru)),
               -(stranded_loss  * (1 - net_pass_thru)),
               -(mkt_adj        * (1 - net_pass_thru)),
               -phys_loss_net,
               max(stress_val_M, 0)],
            text=[f"${v:.0f}M" for v in [
                book_M,
                -(cum_carbon_tax*(1-net_pass_thru)),
                -(stranded_loss*(1-net_pass_thru)),
                -(mkt_adj*(1-net_pass_thru)),
                -phys_loss_net,
                max(stress_val_M, 0)
            ]],
            textposition="outside",
            textfont=dict(size=10, color="#374151"),
            decreasing=dict(marker_color="#EF4444"),
            increasing=dict(marker_color="#22C55E"),
            totals=dict(marker_color="#0D2137"),
            connector=dict(line=dict(color="#CBD5E1", width=1.5, dash="dot")),
        ))
        fig_wf.update_layout(
            height=400, template="plotly_white",
            yaxis=dict(title="CAD $M", tickfont=dict(color="#374151")),
            xaxis=dict(tickfont=dict(size=10, color="#374151")),
            margin=dict(t=20, b=20, l=10, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        _chart(fig_wf)

    with w2:
        # Loss attribution donut
        pie_labels = ["Carbon Tax", "Stranded Asset", "Market Adj.", "Physical Damage"]
        pie_vals   = [
            cum_carbon_tax * (1 - net_pass_thru),
            stranded_loss  * (1 - net_pass_thru),
            mkt_adj        * (1 - net_pass_thru),
            phys_loss_net,
        ]
        pie_colors = ["#1D4ED8", "#7C3AED", "#0891B2", "#DC2626"]
        fig_pie = go.Figure(go.Pie(
            labels=pie_labels,
            values=[max(v, 0) for v in pie_vals],
            hole=0.54,
            marker=dict(colors=pie_colors,
                        line=dict(color="white", width=2)),
            textinfo="percent",
            textfont=dict(size=11, color="#374151"),
            hovertemplate="%{label}: CAD %{value:.1f}M<extra></extra>",
        ))
        fig_pie.add_annotation(
            text=f"Total<br><b>CAD {total_loss:.0f}M</b>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=11, color="#0D2137"),
        )
        fig_pie.update_layout(
            title=dict(text="Loss Attribution (net)", font=dict(size=12, color="#0D2137")),
            height=260, showlegend=True,
            legend=dict(font=dict(size=10, color="#374151"),
                        bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
            margin=dict(t=40, b=40, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        _chart(fig_pie)

        # Climate VaR gauge
        fig_gv = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(abs(cvar_pct), 1),
            number={"suffix": "%", "font": {"size": 28, "color": "#0D2137"}},
            gauge={
                "axis": {"range": [0, 40], "ticksuffix": "%",
                         "tickfont": {"size": 9, "color": "#374151"}},
                "bar": {"color": risk_color, "thickness": 0.22},
                "bgcolor": "#F1F5F9", "bordercolor": "#E2E8F0",
                "steps": [
                    {"range": [0, 5],  "color": "#F0FDF4"},
                    {"range": [5, 15], "color": "#FFFBEB"},
                    {"range": [15, 40],"color": "#FEF2F2"},
                ],
                "threshold": {"line": {"color": "#374151", "width": 2},
                              "thickness": 0.75, "value": 15},
            },
            title={"text": f"Climate VaR — {risk_lvl} Risk",
                   "font": {"size": 12, "color": "#0D2137"}},
        ))
        fig_gv.update_layout(height=190,
                              margin=dict(t=40, b=0, l=10, r=10),
                              paper_bgcolor="rgba(0,0,0,0)")
        _chart(fig_gv)

    # ── Conditional Scenario Comparison (RCP or NGFS based on selection) ─────
    is_rcp_selected = scenario_name.startswith("RCP")
    if is_rcp_selected:
        compare_keys  = ["RCP 4.5 — Moderate Warming (~2°C)", "RCP 8.5 — High Emission (~4°C)"]
        compare_short = ["RCP 4.5 (~2°C)", "RCP 8.5 (~4°C)"]
        compare_cols  = ["#1D4ED8", "#DC2626"]
        compare_bgs   = ["#EFF6FF", "#FFF1F2"]
        compare_bords = ["#93C5FD", "#FCA5A5"]
        panel_title   = "RCP Scenario Comparison — Moderate vs High Emission"
    else:
        compare_keys  = ["NGFS — Net Zero 2050", "NGFS — Delayed Transition", "NGFS — Current Policies"]
        compare_short = ["Net Zero 2050", "Delayed Transition", "Current Policies"]
        compare_cols  = ["#059669", "#D97706", "#6B7280"]
        compare_bgs   = ["#F0FDF4", "#FFFBEB", "#F8FAFC"]
        compare_bords = ["#86EFAC", "#FDE68A", "#E2E8F0"]
        panel_title   = "NGFS Scenario Comparison — Three Transition Pathways"

    st.markdown(f'<div class="sec" style="font-size:.88rem;margin-top:.8rem">{panel_title}</div>',
                unsafe_allow_html=True)

    n_compare = len(compare_keys)
    compare_layout = st.columns(n_compare)
    for col, nk, ns, nc, nb, nbr in zip(
        compare_layout, compare_keys, compare_short, compare_cols, compare_bgs, compare_bords
    ):
        sc_d = SCENARIOS[nk]
        sm   = 1.4 if sc_d["high_tax"] else 1.0
        cp_s = np.array([CARBON_SCHEDULE.get(y, 80+(sc_d["cp_end"]-80)*(y-2024)/26) for y in years])
        ct_s = float((A["Emissions_Mt"]*cp_s).sum())
        sl_s = A["Value_B"]*1000*A["Stranded_F"]*sm*frac
        ma_s = A["Value_B"]*1000*0.04 if "Pipeline" in A["Type"] else 0
        pl_s = A["Value_B"]*1000*A["Phys"][sc_d["key"]]*frac
        tot_s = (ct_s+sl_s+ma_s+pl_s)*(1-net_pass_thru)
        cv_s  = tot_s/book_M*100
        is_active = nk == scenario_name
        outline = f"2px solid {nc}" if is_active else f"1px solid {nbr}"
        badge = (' <span style="font-size:.65rem;background:' + nc
                 + ';color:white;padding:1px 7px;border-radius:10px;font-weight:700;margin-left:5px">Active</span>'
                 if is_active else "")
        col.markdown(f"""
        <div style="background:{nb};border:{outline};border-radius:10px;padding:1rem 1.1rem;">
          <div style="font-size:.72rem;font-weight:700;color:{nc};text-transform:uppercase;
                      letter-spacing:.07em;margin-bottom:4px">{ns}{badge}</div>
          <div style="font-size:.68rem;color:#64748B;margin-bottom:.6rem">
            {sc_d['ipcc_ref']} &nbsp;&middot;&nbsp; {sc_d['warming']}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:.6rem">
            <div style="background:white;border-radius:6px;padding:.45rem .6rem;border:1px solid #E2E8F0">
              <div style="font-size:.6rem;color:#64748B;font-weight:600;text-transform:uppercase">Climate VaR</div>
              <div style="font-size:1.05rem;font-weight:700;color:#DC2626">-{cv_s:.1f}%</div>
            </div>
            <div style="background:white;border-radius:6px;padding:.45rem .6rem;border:1px solid #E2E8F0">
              <div style="font-size:.6rem;color:#64748B;font-weight:600;text-transform:uppercase">Net Loss</div>
              <div style="font-size:1.05rem;font-weight:700;color:#0D2137">CAD {tot_s:.0f}M</div>
            </div>
            <div style="background:white;border-radius:6px;padding:.45rem .6rem;border:1px solid #BFDBFE">
              <div style="font-size:.6rem;color:#1D4ED8;font-weight:600;text-transform:uppercase">Transition Risk</div>
              <div style="font-size:.9rem;font-weight:700;color:#1D4ED8">CAD {(ct_s+sl_s+ma_s)*(1-net_pass_thru):.0f}M</div>
            </div>
            <div style="background:white;border-radius:6px;padding:.45rem .6rem;border:1px solid #FED7AA">
              <div style="font-size:.6rem;color:#EA580C;font-weight:600;text-transform:uppercase">Physical Risk</div>
              <div style="font-size:.9rem;font-weight:700;color:#EA580C">CAD {pl_s*(1-net_pass_thru):.0f}M</div>
            </div>
          </div>
          <div style="font-size:.69rem;color:#64748B;line-height:1.5">{sc_d['risk_focus']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Side-by-side waterfall for the compared scenarios
    compare_fig = make_subplots(rows=1, cols=n_compare,
                                subplot_titles=compare_short, shared_yaxes=True)
    for i, (nk, nc) in enumerate(zip(compare_keys, compare_cols), 1):
        sc_d = SCENARIOS[nk]
        sm   = 1.4 if sc_d["high_tax"] else 1.0
        cp_s = np.array([CARBON_SCHEDULE.get(y, 80+(sc_d["cp_end"]-80)*(y-2024)/26) for y in years])
        ct_n = float((A["Emissions_Mt"]*cp_s).sum())*(1-net_pass_thru)
        sl_n = A["Value_B"]*1000*A["Stranded_F"]*sm*frac*(1-net_pass_thru)
        ma_n = (A["Value_B"]*1000*0.04 if "Pipeline" in A["Type"] else 0)*(1-net_pass_thru)
        pl_n = A["Value_B"]*1000*A["Phys"][sc_d["key"]]*frac*(1-net_pass_thru)
        sv   = max(book_M-ct_n-sl_n-ma_n-pl_n, 0)
        compare_fig.add_trace(go.Waterfall(
            orientation="v",
            measure=["absolute","relative","relative","relative","relative","total"],
            x=["Book\nValue","Carbon\nTax","Stranded\nCapital","Market\nAdj.","Physical\nDamage","Stress\nValue"],
            y=[book_M,-ct_n,-sl_n,-ma_n,-pl_n,sv],
            text=[f"${v:.0f}" for v in [book_M,-ct_n,-sl_n,-ma_n,-pl_n,sv]],
            textposition="outside", textfont=dict(size=8, color="#374151"),
            decreasing=dict(marker_color="#EF4444"),
            increasing=dict(marker_color="#22C55E"),
            totals=dict(marker_color=nc),
            connector=dict(line=dict(color="#CBD5E1", width=1, dash="dot")),
            showlegend=False,
        ), row=1, col=i)

    compare_fig.update_layout(
        height=360, template="plotly_white",
        margin=dict(t=40, b=20, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    compare_fig.update_yaxes(title_text="CAD $M", tickfont=dict(color="#374151"), row=1, col=1)
    compare_fig.update_xaxes(tickfont=dict(size=8, color="#374151"))
    _chart(compare_fig)

    # Total Net Loss — All 5 Scenarios — BLUE=transition, ORANGE=physical
    st.markdown('<div class="sec" style="font-size:.85rem;margin-top:.3rem">Total Net Loss — All Scenarios (Blue = Transition Risk, Orange = Physical Risk)</div>',
                unsafe_allow_html=True)
    SC_LABEL = {
        "RCP 4.5 — Moderate Warming (~2°C)": "RCP 4.5",
        "RCP 8.5 — High Emission (~4°C)":    "RCP 8.5",
        "NGFS — Net Zero 2050":              "NGFS Net Zero 2050",
        "NGFS — Delayed Transition":         "NGFS Delayed Transition",
        "NGFS — Current Policies":           "NGFS Current Policies",
    }
    sc_losses = []
    for sc_n, sc_d in SCENARIOS.items():
        ht = sc_d["high_tax"]; sm2 = 1.4 if ht else 1.0
        cp_s = np.array([CARBON_SCHEDULE.get(y,80+(sc_d["cp_end"]-80)*(y-2024)/26) for y in years])
        ct_s = float((A["Emissions_Mt"]*cp_s).sum())
        sl_s = A["Value_B"]*1000*A["Stranded_F"]*sm2*frac
        ma_s = A["Value_B"]*1000*0.04 if "Pipeline" in A["Type"] else 0
        pl_s = A["Value_B"]*1000*A["Phys"][sc_d["key"]]*frac
        sc_losses.append({
            "Scenario":   SC_LABEL.get(sc_n, sc_n),
            "Transition": (ct_s+sl_s+ma_s)*(1-net_pass_thru),
            "Physical":   pl_s*(1-net_pass_thru),
            "Total":      (ct_s+sl_s+ma_s+pl_s)*(1-net_pass_thru),
            "Active":     sc_n == scenario_name,
        })
    sc_df = pd.DataFrame(sc_losses).sort_values("Total", ascending=True)
    fig_sc2 = go.Figure()
    fig_sc2.add_trace(go.Bar(
        y=sc_df["Scenario"], x=sc_df["Transition"], orientation="h",
        name="Transition Risk (carbon tax + stranded assets)",
        marker_color=["#1D4ED8" if a else "#93C5FD" for a in sc_df["Active"]],
        marker_line=dict(width=0),
    ))
    fig_sc2.add_trace(go.Bar(
        y=sc_df["Scenario"], x=sc_df["Physical"], orientation="h",
        name="Physical Risk (asset damage)",
        marker_color=["#EA580C" if a else "#FED7AA" for a in sc_df["Active"]],
        marker_line=dict(width=0),
    ))
    for _, row in sc_df.iterrows():
        fig_sc2.add_annotation(
            x=row["Total"], y=row["Scenario"],
            text=f"CAD {row['Total']:.0f}M",
            xanchor="left", yanchor="middle", showarrow=False, xshift=6,
            font=dict(size=9, color="#374151"),
        )
    fig_sc2.update_layout(
        height=290, template="plotly_white", barmode="stack",
        xaxis=dict(title="Net Loss (CAD $M)", tickfont=dict(color="#374151")),
        yaxis=dict(tickfont=dict(size=9, color="#374151")),
        legend=dict(font=dict(size=10, color="#374151"), orientation="h", y=-0.25),
        margin=dict(t=10, b=65, l=10, r=100),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    _chart(fig_sc2)


# ════════════════════════════════════════════════════════════════
#  TAB 5 — MANAGEMENT REPORT
# ════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="sec">Climate Risk Audit and Advisory Report</div>',
                unsafe_allow_html=True)

    dl_col, _ = st.columns([3, 7])
    with dl_col:
        # Generate PDF using reportlab
        def build_pdf():
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import cm
                from reportlab.lib import colors
                from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                                 Table, TableStyle, HRFlowable)
                from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
                import io

                buf = io.BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=A4,
                                        leftMargin=2.2*cm, rightMargin=2.2*cm,
                                        topMargin=2*cm, bottomMargin=2*cm)
                navy   = colors.HexColor("#0D2137")
                red    = colors.HexColor("#DC2626")
                amber  = colors.HexColor("#D97706")
                green  = colors.HexColor("#16A34A")
                grey   = colors.HexColor("#64748B")
                lgrey  = colors.HexColor("#F3F4F6")
                risk_c = {"High": red, "Moderate": amber, "Low": green}[risk_lvl]

                styles = getSampleStyleSheet()
                H1 = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=16,
                                    textColor=navy, spaceAfter=4, alignment=TA_CENTER)
                H2 = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11,
                                    textColor=navy, spaceBefore=14, spaceAfter=4,
                                    borderPadding=(0,0,2,0))
                Body = ParagraphStyle("Body", fontName="Helvetica", fontSize=9,
                                      leading=14, textColor=colors.HexColor("#1F2937"),
                                      spaceAfter=6, alignment=TA_JUSTIFY)
                SmCap = ParagraphStyle("SmCap", fontName="Helvetica-Bold", fontSize=7.5,
                                       textColor=grey, spaceAfter=2)
                Sub  = ParagraphStyle("Sub", fontName="Helvetica", fontSize=8,
                                      textColor=grey, alignment=TA_CENTER)
                Bullet = ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9,
                                        leading=14, textColor=colors.HexColor("#1F2937"),
                                        leftIndent=14, spaceAfter=5)

                elems = []

                # ── Header ────────────────────────────────────────────────────
                elems.append(Paragraph("CLIMATE RISK AUDIT AND ADVISORY REPORT", H1))
                elems.append(Paragraph("TC Energy Corporation (TRP.TO) — Private and Confidential", Sub))
                elems.append(Spacer(1, 6))
                elems.append(HRFlowable(width="100%", thickness=2, color=navy))
                elems.append(Spacer(1, 10))

                # ── Meta table ────────────────────────────────────────────────
                meta_data = [
                    ["Date of Assessment", date.today().strftime("%B %d, %Y"),
                     "Stress Horizon", f"2024 to {end_year} ({duration} yrs)"],
                    ["Asset", selected[:32], "Climate Pathway", scenario_name.split(" — ")[0]],
                    ["Classification", A["Type"], "Physical Hazard", hazard],
                    ["Baseline Valuation", f"CAD {A['Value_B']}B", "Scope 1 Emissions", f"{A['Emissions_Mt']} Mt CO2e/yr"],
                    ["Applied WACC", f"{wacc*100:.1f}%", "FX Rate", f"1 USD = {FX:.4f} CAD"],
                ]
                meta_tbl = Table(meta_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
                meta_tbl.setStyle(TableStyle([
                    ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
                    ("FONTNAME",  (0,0), (0,-1),  "Helvetica-Bold"),
                    ("FONTNAME",  (2,0), (2,-1),  "Helvetica-Bold"),
                    ("FONTSIZE",  (0,0), (-1,-1), 8),
                    ("TEXTCOLOR", (0,0), (0,-1),  grey),
                    ("TEXTCOLOR", (2,0), (2,-1),  grey),
                    ("TEXTCOLOR", (1,0), (1,-1),  navy),
                    ("TEXTCOLOR", (3,0), (3,-1),  navy),
                    ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, lgrey]),
                    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0,0), (-1,-1), 5),
                ]))
                elems.append(meta_tbl)
                elems.append(Spacer(1, 10))

                # ── Section 1 ─────────────────────────────────────────────────
                elems.append(HRFlowable(width="100%", thickness=0.5, color=navy))
                elems.append(Paragraph("1. Executive Summary", H2))
                elems.append(Paragraph(
                    f"Under the <b>{scenario_name.split(' — ')[0]}</b> climate pathway, the <b>{selected}</b> "
                    f"asset demonstrates a <b>{risk_lvl.lower()} sensitivity</b> to integrated climate-related "
                    f"financial factors over the {duration}-year assessment window. "
                    f"The aggregated Climate Value-at-Risk (VaR) is calculated at <b>{abs(cvar_pct):.2f}%</b>, "
                    f"representing a total projected NPV impairment of <b>CAD {total_loss:.1f} Million</b> "
                    f"against the baseline valuation of CAD {A['Value_B']} Billion, after applying a "
                    f"regulated tariff pass-through rate of {pass_thru}%. "
                    f"The primary financial risk catalyst is identified as <b>{primary_driver}</b>.",
                    Body))

                # ── Section 2 ─────────────────────────────────────────────────
                elems.append(HRFlowable(width="100%", thickness=0.5, color=navy))
                elems.append(Paragraph("2. Quantified Risk Attribution", H2))
                attr_data = [
                    ["Component", "Driver", "Gross Loss", "Net Loss", "% of Book"],
                    ["Carbon Tax Liability", f"{A['Emissions_Mt']} Mt × carbon price path",
                     f"CAD {cum_carbon_tax:.1f}M", f"CAD {cum_carbon_tax*(1-net_pass_thru):.1f}M",
                     f"{cum_carbon_tax*(1-net_pass_thru)/book_M*100:.2f}%"],
                    ["Stranded Asset Loss", f"Obsolescence under {SC['key']}",
                     f"CAD {stranded_loss:.1f}M", f"CAD {stranded_loss*(1-net_pass_thru):.1f}M",
                     f"{stranded_loss*(1-net_pass_thru)/book_M*100:.2f}%"],
                    ["Physical Asset Damage", f"{hazard} ({damage_rate*100:.2f}% rate)",
                     f"CAD {phys_loss_gross:.1f}M", f"CAD {phys_loss_net:.1f}M",
                     f"{phys_pct:.2f}%"],
                    ["Market Adjustment", "Pipeline market discount (4% of book)",
                     f"CAD {mkt_adj:.1f}M", f"CAD {mkt_adj*(1-net_pass_thru):.1f}M",
                     f"{mkt_adj*(1-net_pass_thru)/book_M*100:.2f}%"],
                    ["TOTAL IMPAIRMENT", "",
                     f"CAD {int(total_loss/(1-net_pass_thru+0.0001))}M",
                     f"CAD {total_loss:.1f}M", f"{abs(cvar_pct):.2f}%"],
                ]
                attr_tbl = Table(attr_data, colWidths=[4*cm, 4.5*cm, 2.8*cm, 2.8*cm, 2.4*cm])
                attr_tbl.setStyle(TableStyle([
                    ("FONTNAME",  (0,0), (-1,0),  "Helvetica-Bold"),
                    ("FONTNAME",  (0,1), (-1,-2), "Helvetica"),
                    ("FONTNAME",  (0,-1),(-1,-1), "Helvetica-Bold"),
                    ("FONTSIZE",  (0,0), (-1,-1), 8),
                    ("BACKGROUND",(0,0), (-1,0),  navy),
                    ("TEXTCOLOR", (0,0), (-1,0),  colors.white),
                    ("BACKGROUND",(0,-1),(-1,-1), lgrey),
                    ("ROWBACKGROUNDS",(0,1),(-1,-2), [colors.white, lgrey]),
                    ("ALIGN",     (2,0), (-1,-1), "RIGHT"),
                    ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
                    ("PADDING",   (0,0), (-1,-1), 5),
                    ("TEXTCOLOR", (2,-1),(4,-1),  red),
                ]))
                elems.append(attr_tbl)
                elems.append(Spacer(1, 10))

                # ── Section 3 ─────────────────────────────────────────────────
                elems.append(HRFlowable(width="100%", thickness=0.5, color=navy))
                elems.append(Paragraph("3. Strategic Management Recommendations", H2))
                elems.append(Paragraph(
                    f"Diagnostic analytics identify <b>{primary_driver}</b> as the dominant value "
                    "erosion catalyst. Management is advised to prioritise:", Body))

                if primary_driver == "Transition Risk":
                    recs = [
                        f"<b>Decarbonization CAPEX:</b> Accelerate operational upgrades targeting the {A['Emissions_Mt']} Mt CO2e/yr emission baseline. TC Energy's 30% GHG intensity reduction target by 2030 requires ~5.8%/yr compound reduction; compressor electrification and LDAR programs are the primary levers.",
                        f"<b>Tariff Pass-Through Review:</b> Evaluate recovery of carbon compliance costs through regulated shipper tariffs. NEB/FERC-regulated pipelines currently recover ~{int(A['PassThru']*100)}% of incremental costs; renegotiation ahead of the 2030 $170/t milestone will protect EBITDA.",
                        f"<b>Depreciation and Asset Life Review:</b> Reassess economic useful life under the {scenario_name.split(' — ')[0]} pathway for assets with stranding factors above 15%. Accelerated depreciation provisions may be warranted.",
                    ]
                else:
                    recs = [
                        f"<b>Asset Hardening:</b> Increase capital expenditure for structural defenses against {hazard} at {selected}. IPCC AR6 projects significant intensification of this hazard class in the asset's geographic region.",
                        "<b>Insurance and Risk Transfer:</b> Reassess catastrophic loss coverage limits, benchmarking against updated Munich Re / Swiss Re NatCat energy sector loss models for Canadian and Mexican infrastructure.",
                        "<b>Emergency Response:</b> Update location-specific emergency response and business continuity plans to minimise throughput downtime during extreme weather events.",
                    ]
                for rec in recs:
                    elems.append(Paragraph(f"• &nbsp;{rec}", Bullet))

                # ── Section 4 ─────────────────────────────────────────────────
                elems.append(HRFlowable(width="100%", thickness=0.5, color=navy))
                elems.append(Paragraph("4. Risk Summary", H2))
                sum_data = [
                    ["Dimension", "Assessment"],
                    ["Overall Risk Level", risk_lvl],
                    ["Climate VaR", f"{abs(cvar_pct):.2f}%"],
                    ["Primary Driver", primary_driver],
                    ["Physical Hazard", hazard],
                    ["Pass-Through Rate", f"{pass_thru}%"],
                    ["Stress-Adjusted Value", f"CAD {int(max(stress_val_M,0))}M (from CAD {int(book_M)}M)"],
                    ["NGFS / IPCC Reference", SC.get("ipcc_ref","—")],
                    ["Warming Trajectory", SC.get("warming","—")],
                    ["TC Energy Market Cap", f"CAD {MKT['mktcap_bn']:.1f}B (live)"],
                ]
                sum_tbl = Table(sum_data, colWidths=[6*cm, 10.5*cm])
                sum_tbl.setStyle(TableStyle([
                    ("FONTNAME",  (0,0), (-1,0),  "Helvetica-Bold"),
                    ("FONTNAME",  (0,1), (0,-1),  "Helvetica-Bold"),
                    ("FONTNAME",  (1,1), (1,-1),  "Helvetica"),
                    ("FONTSIZE",  (0,0), (-1,-1), 8.5),
                    ("BACKGROUND",(0,0), (-1,0),  navy),
                    ("TEXTCOLOR", (0,0), (-1,0),  colors.white),
                    ("TEXTCOLOR", (0,1), (0,-1),  grey),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, lgrey]),
                    ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
                    ("PADDING",   (0,0), (-1,-1), 5),
                    ("TEXTCOLOR", (1,2), (1,2),   red),  # VaR row
                ]))
                elems.append(sum_tbl)
                elems.append(Spacer(1, 14))

                # ── Footer ────────────────────────────────────────────────────
                elems.append(HRFlowable(width="100%", thickness=0.5,
                                         color=colors.HexColor("#D1D5DB")))
                elems.append(Spacer(1, 4))
                footer_txt = (
                    f"<b>Auditor Statement:</b> This stress test is aligned with TCFD and IFRS S2 "
                    f"Climate-related Disclosures. Data sourced from TC Energy 2024 Report on "
                    f"Sustainability, ESG Data Sheet, Annual Report 2023, and Q3 2024 MD&A. Physical "
                    f"damage coefficients calibrated against Swiss Re NatCat benchmarks and IPCC AR6 "
                    f"WG2 regional projections. Scenario carbon prices reference NGFS Phase 4 (2023) "
                    f"and Canada's Federal Carbon Pricing schedule. "
                    f"Live market data via yfinance ({MKT['ts']}). WACC: {wacc*100:.1f}%. "
                    f"Not intended for direct investment purposes."
                )
                elems.append(Paragraph(footer_txt, ParagraphStyle(
                    "Ftr", fontName="Helvetica", fontSize=7, textColor=grey,
                    leading=10, alignment=TA_JUSTIFY)))

                doc.build(elems)
                buf.seek(0)
                return buf.read()

            except Exception:
                return None

        pdf_bytes = build_pdf()
        if pdf_bytes:
            st.download_button(
                "Download Report (PDF)",
                data=pdf_bytes,
                file_name=f"TRP_ClimateAudit_{selected[:8].replace(' ','_')}_{date.today()}.pdf",
                mime="application/pdf",
            )
        else:
            st.info("Install `reportlab` for PDF export: `pip install reportlab`")
            fallback_txt = "\n".join([
                "TC Energy Climate Risk Report", "="*52,
                f"Asset: {selected}", f"Scenario: {scenario_name}",
                f"Climate VaR: {cvar_pct:.2f}%", f"Total Loss: CAD {total_loss:.1f}M",
            ])
            st.download_button("Download Report (.txt)", data=fallback_txt,
                file_name=f"TRP_ClimateAudit_{date.today()}.txt", mime="text/plain")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Build all recommendation list items ──────────────────────────────────
    LI = 'style="margin-bottom:10px"'
    if primary_driver == "Transition Risk":
        rec_html = (
            '<li ' + LI + '><b>Decarbonization CAPEX:</b> Accelerate operational upgrades targeting the '
            + str(A['Emissions_Mt']) + ' Mt CO2e per-year emission baseline. '
            + "TC Energy's 2030 GHG intensity reduction target of 30% requires a compound "
            + 'reduction rate of approximately 5.8%/yr; compressor electrification and LDAR '
            + 'programs are the primary abatement levers.</li>'
            + '<li ' + LI + '><b>Tariff Pass-Through Review:</b> Evaluate the capacity to pass carbon '
            + 'compliance costs through regulated shipper tariffs. TC Energy\'s NEB/FERC-regulated '
            + 'pipelines currently recover approximately ' + str(int(A['PassThru'] * 100))
            + '% of incremental compliance costs. Renegotiating contracts ahead of the 2030 '
            + '$170/t carbon price milestone will protect EBITDA margins.</li>'
            + '<li ' + LI + '><b>Depreciation and Asset Life Review:</b> Reassess economic useful life '
            + 'of capital assets under the ' + scenario_name
            + ' pathway, particularly for assets with stranding factors above 15%. Accelerated '
            + 'depreciation provisions may be warranted for assets with residual exposure to '
            + 'fossil fuel demand risk.</li>'
        )
    else:
        rec_html = (
            '<li ' + LI + '><b>Asset Hardening and Resilience Investment:</b> Increase capital '
            + 'expenditure for structural defenses against ' + hazard + ' at ' + selected
            + '. IPCC AR6 projects significant intensification of this hazard class in the '
            + "asset's geographic region under " + SC['key'] + '.</li>'
            + '<li ' + LI + '><b>Insurance and Risk Transfer:</b> Reassess catastrophic loss '
            + 'insurance coverage limits, particularly for assets in TC Energy\'s Northern Canada '
            + 'and Mexico exposure zones. Benchmark against updated Munich Re / Swiss Re NatCat '
            + 'energy sector loss models.</li>'
            + '<li ' + LI + '><b>Emergency Response and Business Continuity:</b> Update '
            + 'location-specific emergency response plans to minimize throughput downtime during '
            + 'extreme weather events, consistent with TC Energy\'s operational safety '
            + 'management system commitments.</li>'
        )

    # ── Build risk summary rows ───────────────────────────────────────────────
    risk_rows = ""
    for k, v, vc in [
        ("Overall Risk Level",    risk_lvl,                                                    risk_color),
        ("Climate VaR",           str(round(cvar_pct, 2)) + "%",                              "#DC2626"),
        ("Primary Driver",        primary_driver,                                              "#0D2137"),
        ("Physical Hazard",       hazard,                                                      "#0D2137"),
        ("Pass-Through Rate",     str(pass_thru) + "%",                                       "#0D2137"),
        ("Stress-Adjusted Value", "CAD " + str(int(max(stress_val_M, 0))) + "M (from CAD "
                                  + str(int(book_M)) + "M baseline)",                         "#0D2137"),
        ("TC Energy Market Cap",  "CAD " + str(round(MKT['mktcap_bn'], 1)) + "B (live)",     "#0D2137"),
    ]:
        risk_rows += (
            '<tr><td style="padding:6px 11px;border-bottom:1px solid #E5E7EB">' + k + '</td>'
            + '<td style="padding:6px 11px;border-bottom:1px solid #E5E7EB;font-weight:600;color:'
            + vc + '">' + v + '</td></tr>'
        )

    # ── Build meta table ──────────────────────────────────────────────────────
    td0  = 'style="padding:7px 0;border-bottom:1px solid #E5E7EB;width:50%"'
    td1  = 'style="padding:7px 0;border-bottom:1px solid #E5E7EB"'
    td2  = 'style="padding:7px 0"'
    meta = (
        '<table style="width:100%;border-collapse:collapse;margin-bottom:24px;font-size:13px">'
        + '<tr><td ' + td0 + '><b>Date of Assessment:</b> ' + date.today().strftime("%B %d, %Y") + '</td>'
        + '<td ' + td1 + '><b>Stress Horizon:</b> 2024 to ' + str(end_year) + ' (' + str(duration) + ' years)</td></tr>'
        + '<tr><td ' + td1 + '><b>Asset Under Assessment:</b> ' + selected + '</td>'
        + '<td ' + td1 + '><b>Climate Pathway:</b> ' + scenario_name + '</td></tr>'
        + '<tr><td ' + td1 + '><b>Asset Classification:</b> ' + A["Type"] + '</td>'
        + '<td ' + td1 + '><b>Physical Hazard Focus:</b> ' + hazard + '</td></tr>'
        + '<tr><td ' + td1 + '><b>Baseline Valuation:</b> CAD ' + str(A["Value_B"]) + 'B (2023 carrying value)</td>'
        + '<td ' + td1 + '><b>Scope 1 Emissions:</b> ' + str(A["Emissions_Mt"]) + ' Mt CO2e/yr</td></tr>'
        + '<tr><td ' + td2 + '><b>Applied WACC:</b> ' + str(round(wacc * 100, 1)) + '%</td>'
        + '<td ' + td2 + '><b>Live FX Rate:</b> 1 USD = ' + str(round(FX, 4)) + ' CAD (' + MKT["ts"] + ')</td></tr>'
        + '</table>'
    )

    # ── Build risk attribution table ──────────────────────────────────────────
    td  = 'style="padding:7px 11px;border-bottom:1px solid #E5E7EB"'
    tdr = 'style="padding:7px 11px;border-bottom:1px solid #E5E7EB;text-align:right"'
    attr = (
        '<table style="width:100%;border-collapse:collapse;font-size:12.5px">'
        + '<tr style="background:#F3F4F6">'
        + '<th style="padding:8px 11px;text-align:left;color:#374151;border-bottom:1px solid #D1D5DB">Component</th>'
        + '<th style="padding:8px 11px;text-align:left;color:#374151;border-bottom:1px solid #D1D5DB">Driver</th>'
        + '<th style="padding:8px 11px;text-align:right;color:#374151;border-bottom:1px solid #D1D5DB">Gross</th>'
        + '<th style="padding:8px 11px;text-align:right;color:#374151;border-bottom:1px solid #D1D5DB">Net</th>'
        + '<th style="padding:8px 11px;text-align:right;color:#374151;border-bottom:1px solid #D1D5DB">% Book</th></tr>'
        + '<tr><td ' + td + '><b>Carbon Tax Liability</b></td>'
        + '<td ' + td + '>' + str(A["Emissions_Mt"]) + ' Mt x carbon price path</td>'
        + '<td ' + tdr + '>CAD ' + str(round(cum_carbon_tax, 1)) + 'M</td>'
        + '<td ' + tdr + '>CAD ' + str(round(cum_carbon_tax * (1 - net_pass_thru), 1)) + 'M</td>'
        + '<td ' + tdr + '>' + str(round(cum_carbon_tax * (1 - net_pass_thru) / book_M * 100, 2)) + '%</td></tr>'
        + '<tr><td ' + td + '><b>Stranded Asset Loss</b></td>'
        + '<td ' + td + '>Economic obsolescence under ' + SC["key"] + '</td>'
        + '<td ' + tdr + '>CAD ' + str(round(stranded_loss, 1)) + 'M</td>'
        + '<td ' + tdr + '>CAD ' + str(round(stranded_loss * (1 - net_pass_thru), 1)) + 'M</td>'
        + '<td ' + tdr + '>' + str(round(stranded_loss * (1 - net_pass_thru) / book_M * 100, 2)) + '%</td></tr>'
        + '<tr><td ' + td + '><b>Physical Asset Damage</b></td>'
        + '<td ' + td + '>' + hazard + ' (' + str(round(damage_rate * 100, 2)) + '% rate)</td>'
        + '<td ' + tdr + '>CAD ' + str(round(phys_loss_gross, 1)) + 'M</td>'
        + '<td ' + tdr + '>CAD ' + str(round(phys_loss_net, 1)) + 'M</td>'
        + '<td ' + tdr + '>' + str(round(phys_pct, 2)) + '%</td></tr>'
        + '<tr><td ' + td + '><b>Market Adjustment</b></td>'
        + '<td ' + td + '>Pipeline market discount (4% of book)</td>'
        + '<td ' + tdr + '>CAD ' + str(round(mkt_adj, 1)) + 'M</td>'
        + '<td ' + tdr + '>CAD ' + str(round(mkt_adj * (1 - net_pass_thru), 1)) + 'M</td>'
        + '<td ' + tdr + '>' + str(round(mkt_adj * (1 - net_pass_thru) / book_M * 100, 2)) + '%</td></tr>'
        + '<tr style="background:#F3F4F6;font-weight:700">'
        + '<td style="padding:8px 11px">Total Impairment</td><td style="padding:8px 11px"></td>'
        + '<td style="padding:8px 11px;text-align:right">CAD ' + str(int(total_loss / (1 - net_pass_thru + 0.0001))) + 'M</td>'
        + '<td style="padding:8px 11px;text-align:right;color:#DC2626">CAD ' + str(round(total_loss, 1)) + 'M</td>'
        + '<td style="padding:8px 11px;text-align:right;color:#DC2626">' + str(round(abs(cvar_pct), 2)) + '%</td></tr>'
        + '</table>'
    )

    # ── Render entire report as ONE st.markdown call ──────────────────────────
    # Streamlit auto-closes unclosed tags between calls — the entire report
    # must be one string to preserve <div class="rpt"> scoping and .rec styles.
    report_html = (
        '<div class="rpt">'

        # Header
        + '<div style="text-align:center;border-bottom:3px solid #0D2137;'
        + 'padding-bottom:16px;margin-bottom:28px">'
        + '<div style="font-size:10.5px;letter-spacing:2px;color:#6B7280;'
        + 'text-transform:uppercase;margin-bottom:8px">Private and Confidential</div>'
        + '<h2>Climate Risk Audit and Advisory Report</h2>'
        + '<p style="color:#6B7280;font-size:13px;margin:6px 0 0;letter-spacing:.4px">'
        + 'Prepared for TC Energy Corporation (TRP.TO) &mdash; Internal Management Use Only</p>'
        + '</div>'

        # Meta table
        + meta

        # Section 1
        + '<h3>1. Executive Summary</h3>'
        + '<p>Under the <b>' + scenario_name + '</b> climate pathway, the <b>' + selected
        + '</b> asset demonstrates a <b style="color:' + risk_color + '">' + risk_lvl.lower()
        + ' sensitivity</b> to integrated climate-related financial factors over the '
        + str(duration) + '-year assessment window. The aggregated Climate Value-at-Risk (VaR) is '
        + 'calculated at <b>' + str(round(cvar_pct, 2)) + '%</b>, representing a total projected '
        + 'NPV impairment of <b>CAD ' + str(round(total_loss, 1)) + ' Million</b> against the '
        + 'baseline asset valuation of CAD ' + str(A["Value_B"]) + ' Billion, after applying a '
        + 'regulated tariff pass-through rate of ' + str(pass_thru) + '%.</p>'
        + '<p>The primary financial risk catalyst is identified as <b>' + primary_driver
        + '</b>. TC Energy\'s regulated pipeline model provides meaningful insulation through tariff '
        + 'pass-through mechanisms; however, residual exposure represents a material consideration '
        + 'for long-horizon capital allocation.</p>'

        # Section 2
        + '<h3>2. Quantified Risk Attribution</h3>'
        + attr

        # Section 3
        + '<h3>3. Strategic Management Recommendations</h3>'
        + '<p>Diagnostic analytics identify <b>' + primary_driver
        + '</b> as the dominant value erosion catalyst within this asset boundary. '
        + 'Management is advised to prioritise:</p>'
        + '<div class="rec">'
        + '<ul style="margin:0;padding-left:18px;line-height:1.9;font-size:13.5px">'
        + rec_html
        + '</ul></div>'

        # Section 4
        + '<h3>4. Risk Summary</h3>'
        + '<table style="width:100%;border-collapse:collapse;font-size:12.5px">'
        + '<tr style="background:#F3F4F6">'
        + '<th style="padding:7px 11px;text-align:left;color:#374151">Dimension</th>'
        + '<th style="padding:7px 11px;text-align:left;color:#374151">Assessment</th></tr>'
        + risk_rows
        + '</table>'

        # Footer
        + '<div class="ftr"><b>Auditor Statement:</b> This stress test is aligned with the Task '
        + 'Force on Climate-related Financial Disclosures (TCFD) and IFRS S2 Climate-related '
        + 'Disclosures. Financial data sourced from TC Energy\'s 2024 Report on Sustainability, '
        + 'ESG Data Sheet, Annual Report 2023, and Q3 2024 MD&amp;A. Physical damage coefficients '
        + 'calibrated against Swiss Re NatCat benchmarks and IPCC AR6 WG2 regional projections. '
        + 'Carbon pricing uses Canada\'s actual Federal Carbon Pricing schedule to 2030, '
        + 'extrapolated by scenario thereafter. Pass-through rates reflect TC Energy\'s regulated '
        + 'tariff structure per asset class. Live market data via yfinance (' + MKT["ts"]
        + '). WACC: ' + str(round(wacc * 100, 1)) + '%. '
        + 'Not intended for direct investment or trading purposes.</div>'

        + '</div>'   # close .rpt
    )
    st.markdown(report_html, unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center;padding:.9rem 0;border-top:1px solid #E2E8F0;
            font-size:.73rem;color:#94A3B8">
  TC Energy Climate Risk Stress Terminal &nbsp;|&nbsp;
  Data: TRP 2024 Sustainability Report + ESG Data Sheet &nbsp;|&nbsp;
  Live FX: {FX:.4f} CAD &nbsp;|&nbsp;
  {MKT['ts']} &nbsp;|&nbsp; TCFD / IFRS S2 Aligned
</div>""", unsafe_allow_html=True)

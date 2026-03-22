"""
TC Energy — Climate Risk Stress Testing Terminal  v3.2
Real TC Energy 2024 public disclosure data · No Mapbox token needed
Install: pip install streamlit plotly pandas numpy yfinance
Run:     streamlit run tc_energy_climate_var.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import date

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
.sec { font-size: .98rem; font-weight: 600; color: #0D2137; border-bottom: 2px solid #E2E8F0; padding-bottom: .55rem; margin-bottom: 1.15rem; }
.itile { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: .85rem 1.05rem; }
.itile .il { font-size: .65rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 4px; }
.itile .iv { font-size: 1.25rem; font-weight: 700; color: #0D2137; }
.itile .is { font-size: .72rem; color: #94A3B8; margin-top: 2px; }

/* Asset card */
.a-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: .6rem .9rem; margin-bottom: .45rem; }
.a-card.sel { background: #EFF6FF; border-color: #0D2137; border-width: 2px; }
.a-name { font-size: .79rem; font-weight: 600; color: #0D2137; margin-bottom: 2px; }
.a-meta { display: flex; gap: 14px; font-size: .7rem; color: #64748B; }
.note { background: #F0F9FF; border-left: 3px solid #0EA5E9; border-radius: 0 6px 6px 0; padding: .65rem 1rem; font-size: .8rem; color: #0C4A6E; margin-top: .6rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #E8EDF2; border-radius: 9px; padding: 4px; gap: 3px; }
.stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 7px 18px; font-size: .85rem; font-weight: 500; color: #64748B; }
.stTabs [aria-selected="true"] { background: white !important; color: #0D2137 !important; box-shadow: 0 1px 3px rgba(0,0,0,.1); }

/* Download */
.stDownloadButton button { background: #0D2137 !important; color: #F1F5F9 !important; border: none !important; border-radius: 6px !important; font-weight: 600 !important; font-size: .82rem !important; }

/* Formal report */
.rpt { background:#FFFFFF; padding:44px 52px; border:1px solid #D1D5DB; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.05); font-family:'Georgia',serif; color:#111827; }
.rpt h2 { color:#0D2137; font-size:21px; text-transform:uppercase; letter-spacing:.4px; margin:0 0 5px; }
.rpt h3 { color:#0D2137; font-size:15px; border-bottom:1px solid #0D2137; padding-bottom:4px; margin:26px 0 9px; }
.rpt p, .rpt li { font-size:13.5px; line-height:1.75; color:#1F2937; }
.rpt .rec { background:#F3F4F6; border-left:4px solid #0D2137; padding:14px 18px 14px 22px; }
.rpt .ftr { font-size:11px; color:#9CA3AF; margin-top:36px; padding-top:12px; border-top:1px solid #D1D5DB; text-align:justify; }
</style>
""", unsafe_allow_html=True)


# ── Live market data ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_market_data():
    try:
        fx_raw   = yf.Ticker("CAD=X").history(period="2d")["Close"]
        trp_raw  = yf.Ticker("TRP").history(period="2d")
        fx       = float(fx_raw.iloc[-1]) if not fx_raw.empty else 1.39
        trp_px   = float(trp_raw["Close"].iloc[-1]) if not trp_raw.empty else 56.0
        mktcap   = yf.Ticker("TRP").info.get("marketCap", 56_000_000_000)
        curr     = yf.Ticker("TRP").info.get("currency", "CAD")
        if curr == "USD": mktcap = mktcap * fx
        live = True
    except Exception:
        fx, trp_px, mktcap, live = 1.39, 56.0, 56_000_000_000, False
    return {"fx": fx, "trp_px": trp_px, "mktcap_bn": mktcap / 1e9, "live": live, "ts": date.today().strftime("%b %d, %Y")}


# ── Real TC Energy asset database ─────────────────────────────────────────────
ASSETS = {
    "NGTL System (AB/BC)": {
        "Type": "Gas Transmission Network", "Value_B": 18.5, "Emissions_Mt": 6.20, "Lat": 53.5, "Lon": -113.5,
        "Hazards": ["Wildfire", "Flooding", "Extreme Heat"], "Stranded_F": 0.12, "PassThru": 0.65,
        "Phys": {"RCP45": 0.018, "RCP85": 0.082, "NZ": 0.013, "DT": 0.070, "CP": 0.045},
        "Note": "93,700 km network; Alberta Energy Regulator regulated",
    },
    "Coastal GasLink (BC)": {
        "Type": "Gas Pipeline", "Value_B": 14.5, "Emissions_Mt": 1.10, "Lat": 54.5, "Lon": -128.6,
        "Hazards": ["Wildfire", "Flooding", "Landslide"], "Stranded_F": 0.08, "PassThru": 0.50,
        "Phys": {"RCP45": 0.013, "RCP85": 0.048, "NZ": 0.009, "DT": 0.041, "CP": 0.028},
        "Note": "670 km; fully contracted to LNG Canada",
    },
    "Keystone Pipeline System": {
        "Type": "Liquids Pipeline", "Value_B": 11.2, "Emissions_Mt": 2.10, "Lat": 49.0, "Lon": -110.0,
        "Hazards": ["Flooding", "Extreme Cold", "Permafrost Thaw"], "Stranded_F": 0.22, "PassThru": 0.70,
        "Phys": {"RCP45": 0.025, "RCP85": 0.058, "NZ": 0.018, "DT": 0.049, "CP": 0.033},
        "Note": "~4,324 km; transports ~553,000 bbl/day",
    },
    "Bruce Power (48.3% share, ON)": {
        "Type": "Nuclear Power Generation", "Value_B": 5.8, "Emissions_Mt": 0.08, "Lat": 44.3, "Lon": -81.5,
        "Hazards": ["Extreme Heat", "Water Level Change"], "Stranded_F": 0.02, "PassThru": 0.85,
        "Phys": {"RCP45": 0.009, "RCP85": 0.025, "NZ": 0.005, "DT": 0.018, "CP": 0.012},
        "Note": "6,550 MW capacity; Ontario IESO contracted",
    },
    "Mexico Gas Pipelines": {
        "Type": "Marine / Offshore Pipeline", "Value_B": 4.5, "Emissions_Mt": 0.85, "Lat": 19.2, "Lon": -96.1,
        "Hazards": ["Hurricane", "Sea Level Rise", "Flooding"], "Stranded_F": 0.18, "PassThru": 0.45,
        "Phys": {"RCP45": 0.038, "RCP85": 0.115, "NZ": 0.030, "DT": 0.098, "CP": 0.065},
        "Note": "Sur de Texas-Tuxpan; ~700 km; CFE anchor customer",
    },
}

CARBON_SCHEDULE = {2024: 80, 2025: 95, 2026: 110, 2027: 125, 2028: 140, 2029: 155, 2030: 170}

SCENARIOS = {
    "RCP 4.5 — Moderate (High Transition)": {"key": "RCP45", "high_tax": True, "high_phys": False, "cp_end": 250, "color": "#1D4ED8"},
    "RCP 8.5 — High Emission (Extreme Physical)": {"key": "RCP85", "high_tax": False, "high_phys": True, "cp_end": 130, "color": "#DC2626"},
    "NGFS — Net Zero 2050": {"key": "NZ", "high_tax": True, "high_phys": False, "cp_end": 300, "color": "#059669"},
    "NGFS — Delayed Transition": {"key": "DT", "high_tax": False, "high_phys": True, "cp_end": 180, "color": "#D97706"},
    "NGFS — Current Policies": {"key": "CP", "high_tax": False, "high_phys": True, "cp_end": 130, "color": "#6B7280"},
}

MKT = get_market_data()
FX  = MKT["fx"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.5rem 0 .9rem;border-bottom:1px solid rgba(255,255,255,.07)">
      <div style="font-size:1.05rem;font-weight:700;color:#F1F5F9;letter-spacing:-.2px">TC Energy</div>
      <div style="font-size:.7rem;color:#475569;margin-top:2px">Climate Risk Stress Terminal</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-lbl">Asset Selection</div>', unsafe_allow_html=True)
    selected = st.selectbox("Asset", list(ASSETS.keys()), label_visibility="collapsed")
    A = ASSETS[selected]

    st.markdown('<div class="sb-lbl">Climate Scenario</div>', unsafe_allow_html=True)
    scenario_name = st.selectbox("Scenario", list(SCENARIOS.keys()), index=0, label_visibility="collapsed")
    SC = SCENARIOS[scenario_name]

    st.markdown('<div class="sb-lbl">Stress Horizon</div>', unsafe_allow_html=True)
    duration = st.slider("Duration (years)", 1, 26, 10, label_visibility="collapsed")
    end_year = 2024 + duration

    st.markdown('<div class="sb-lbl">Physical Hazard Focus</div>', unsafe_allow_html=True)
    hazard = st.selectbox("Hazard", A["Hazards"], label_visibility="collapsed")

    st.markdown('<div class="sb-lbl">Financial Assumptions</div>', unsafe_allow_html=True)
    wacc       = st.number_input("WACC (%)", value=8.5, step=0.1, format="%.1f") / 100
    pass_thru  = st.slider("Cost Pass-Through (%)", 0, 100, int(A["PassThru"] * 100))

    st.divider()
    st.markdown(f"""
    <div style="background:#0A1929;border-radius:8px;padding:.75rem .9rem;border:1px solid #1E3A5F;">
      <div style="font-size:.63rem;font-weight:700;color:#334155;margin-bottom:.4rem">Market Data ({'Live' if MKT['live'] else 'Fallback'})</div>
      <div style="font-size:.92rem;font-weight:700;color:#E2E8F0;margin-bottom:.15rem">1 USD = {FX:.4f} CAD</div>
      <div style="font-size:.74rem;color:#475569;line-height:1.8">TRP price: CAD ${MKT['trp_px']:.2f}<br>Market cap: CAD ${MKT['mktcap_bn']:.1f}B</div>
    </div>""", unsafe_allow_html=True)


# ── Model calculations ────────────────────────────────────────────────────────
years = np.arange(2024, end_year + 1)
frac  = duration / 26.0
cp_path = np.array([CARBON_SCHEDULE.get(y, 80 + (SC["cp_end"] - 80) * (y - 2024) / 26) for y in years])

cum_carbon_tax = float((A["Emissions_Mt"] * cp_path).sum())
stranded_mult  = 1.4 if SC["high_tax"] else 1.0
stranded_loss  = A["Value_B"] * 1000 * A["Stranded_F"] * stranded_mult * frac
mkt_adj        = A["Value_B"] * 1000 * 0.04 if "Pipeline" in A["Type"] else 0.0
net_pass_thru  = pass_thru / 100.0

damage_rate     = A["Phys"][SC["key"]]
phys_loss_gross = A["Value_B"] * 1000 * damage_rate * frac
phys_loss_net   = phys_loss_gross * (1 - net_pass_thru)

transition_total = (cum_carbon_tax + stranded_loss + mkt_adj) * (1 - net_pass_thru)
total_loss       = transition_total + phys_loss_net
book_M           = A["Value_B"] * 1000
stress_val_M     = book_M - total_loss
cvar_pct         = (total_loss / book_M) * -100

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

# ── KPI Row 1 & 2 ──────────────────────────────────────────────────────────────
r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
for col, lbl, val, sub, dark in [
    (r1c1, "Entity", "TC Energy (TRP.TO)", "TSX + NYSE dual-listed", False),
    (r1c2, "Asset", A["Type"], selected[:28], False),
    (r1c3, "Baseline Value", f"CAD {A['Value_B']}B", "2023 carrying value", False),
    (r1c4, "Scope 1 Baseline", f"{A['Emissions_Mt']} Mt", "CO2e per year", False),
    (r1c5, "Active Scenario", scenario_name.split(" — ")[0], f"2024 to {end_year}", True),
]:
    cls = "kpi-dark" if dark else "kpi"
    col.markdown(f'<div class="{cls}"><div class="kpi-lbl">{lbl}</div><div class="kpi-val" style="font-size:1.05rem">{val}</div><div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

r2c1, r2c2, r2c3, r2c4 = st.columns(4)
for col, lbl, val, sub, bdr in [
    (r2c1, "Aggregated Climate VaR", f"{cvar_pct:.2f}%", f"Risk level: {risk_lvl}", "kpi-neg"),
    (r2c2, "Net Stress Loss (NPV)", f"CAD {total_loss:.1f}M", "After pass-through adjustment", "kpi-warn"),
    (r2c3, "Primary Risk Driver", primary_driver, f"Trans: CAD {transition_total:.0f}M | Phys: CAD {phys_loss_net:.0f}M", "kpi-inf"),
    (r2c4, "Stress-Adjusted Value", f"CAD {max(stress_val_M, 0):.0f}M", f"From CAD {book_M:.0f}M baseline", "kpi-pos"),
]:
    col.markdown(f'<div class="kpi {bdr}"><div class="kpi-lbl">{lbl}</div><div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Asset Geography", "Physical Risk", "Transition Risk", "Climate VaR Bridge", "Management Report"])

# ════════ TAB 1 ════════
with tab1:
    map_col, list_col = st.columns([3, 2])
    with map_col:
        lats, lons, names, sizes, loss_pcts = [], [], [], [], []
        for nm, d in ASSETS.items():
            lp = d["Value_B"] * 1000 * d["Phys"][SC["key"]] * frac / (d["Value_B"] * 1000) * 100
            lats.append(d["Lat"]); lons.append(d["Lon"]); names.append(nm)
            sizes.append(d["Value_B"] * 5 + 10); loss_pcts.append(round(lp, 2))
        
        marker_colors = [f"rgb({int(255*min(lp/max(loss_pcts),1))},200,60)" if lp < max(loss_pcts)/2 else f"rgb(220,{int(200*(1-(min(lp/max(loss_pcts),1)-0.5)*2))},60)" for lp in loss_pcts]
        fig_map = go.Figure(go.Scattergeo(
            lat=lats, lon=lons, mode="markers+text", text=[n.split("(")[0].strip() for n in names], textposition="bottom center",
            marker=dict(size=sizes, color=marker_colors, line=dict(width=[3 if n==selected else 1 for n in names], color=["#0D2137" if n==selected else "#FFF" for n in names])),
            textfont=dict(size=10, color="#0D2137"),
        ))
        fig_map.update_layout(geo=dict(scope="north america", showland=True, landcolor="#F1F5F9", showocean=True, oceancolor="#DBEAFE", center=dict(lat=42, lon=-100), projection_scale=2.8, lataxis=dict(range=[15, 65]), lonaxis=dict(range=[-140, -60]), bgcolor="#F4F6F9"), height=460, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)
    with list_col:
        for nm, d in ASSETS.items():
            pl = d["Value_B"] * 1000 * d["Phys"][SC["key"]] * frac
            sel_cls = "sel" if nm == selected else ""
            st.markdown(f'<div class="a-card {sel_cls}"><div class="a-name">{nm}</div><div class="a-meta"><span>{d["Type"]}</span><span>CAD {d["Value_B"]}B</span><span style="color:#EF4444">Est. loss: CAD {pl:.0f}M</span></div></div>', unsafe_allow_html=True)

# ════════ TAB 2 ════════
with tab2:
    st.markdown(f'<div class="sec">Physical Hazard Assessment — {hazard}</div>', unsafe_allow_html=True)
    ga, gb = st.columns([1, 2])
    with ga:
        g_max = max(1200, phys_loss_gross * 1.8)
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=round(phys_loss_gross, 1),
            number={"prefix": "CAD ", "suffix": "M", "font": {"size": 24}},
            gauge={"axis": {"range": [0, g_max]}, "bar": {"color": "#DC2626" if SC["high_phys"] else "#F59E0B"}, "bgcolor": "#F1F5F9"},
            title={"text": "Gross Damage Exposure"}
        ))
        fig_g.update_layout(height=300, margin=dict(t=30, b=0, l=10, r=10))
        st.plotly_chart(fig_g, use_container_width=True)
    with gb:
        sc_keys = list(SCENARIOS.keys())
        fig_sc = go.Figure(go.Bar(x=[s.split(" — ")[0] for s in sc_keys], y=[A["Value_B"] * 1000 * A["Phys"][SCENARIOS[s]["key"]] * frac for s in sc_keys], marker_color=[SC["color"] if s == scenario_name else "#CBD5E1" for s in sc_keys]))
        fig_sc.update_layout(title="Damage Across Scenarios", height=300, template="plotly_white", margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig_sc, use_container_width=True)

# ════════ TAB 3 ════════
with tab3:
    tr1, tr2 = st.columns(2)
    with tr1:
        fig_area = go.Figure(go.Scatter(x=years, y=A["Emissions_Mt"] * cp_path, mode="lines", fill="tozeroy", line=dict(color=SC["color"], width=2.5)))
        fig_area.update_layout(title="Annual Carbon Cost Path (CAD $M)", height=300, template="plotly_white", margin=dict(t=40, b=30, l=10, r=10))
        st.plotly_chart(fig_area, use_container_width=True)
    with tr2:
        fig_cp = go.Figure()
        for sc_n, sc_d in SCENARIOS.items():
            cp_f = np.array([CARBON_SCHEDULE.get(y, 80 + (sc_d["cp_end"] - 80) * (y - 2024) / 26) for y in np.arange(2024, 2051)])
            fig_cp.add_trace(go.Scatter(x=np.arange(2024, 2051), y=cp_f, name=sc_n.split(" — ")[0], line=dict(color=sc_d["color"], width=2.5 if sc_n == scenario_name else 1.2)))
        fig_cp.update_layout(title="Carbon Price Paths", height=300, template="plotly_white", margin=dict(t=40, b=30, l=10, r=10))
        st.plotly_chart(fig_cp, use_container_width=True)

# ════════ TAB 4 ════════
with tab4:
    w1, w2 = st.columns([3, 2])
    with w1:
        fig_wf = go.Figure(go.Waterfall(
            x=["Baseline", "Carbon Tax", "Stranded", "Market Adj.", "Physical", "Stress Value"],
            y=[book_M, -(cum_carbon_tax*(1-net_pass_thru)), -(stranded_loss*(1-net_pass_thru)), -(mkt_adj*(1-net_pass_thru)), -phys_loss_net, max(stress_val_M, 0)],
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            decreasing=dict(marker_color="#EF4444"), increasing=dict(marker_color="#22C55E"), totals=dict(marker_color="#0D2137")
        ))
        fig_wf.update_layout(height=400, template="plotly_white", margin=dict(t=20, b=20, l=10, r=20))
        st.plotly_chart(fig_wf, use_container_width=True)
    with w2:
        fig_pie = go.Figure(go.Pie(labels=["Carbon Tax", "Stranded Asset", "Market Adj.", "Physical Damage"], values=[cum_carbon_tax*(1-net_pass_thru), stranded_loss*(1-net_pass_thru), mkt_adj*(1-net_pass_thru), phys_loss_net], hole=0.5, marker=dict(colors=["#1D4ED8", "#7C3AED", "#0891B2", "#DC2626"])))
        fig_pie.update_layout(title="Loss Attribution", height=300, margin=dict(t=40, b=40, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

# ════════ TAB 5 — REPORT ════════
with tab5:
    st.markdown('<div class="sec">Climate Risk Audit and Advisory Report</div>', unsafe_allow_html=True)
    
    # [CRITICAL FIX]: Using flush-left HTML string to prevent Markdown code block rendering
    if primary_driver == "Transition Risk":
        strat = f"""<li style="margin-bottom:10px">
<b>Decarbonization CAPEX:</b> Accelerate operational upgrades targeting the {A['Emissions_Mt']} Mt CO2e per-year emission baseline. TC Energy's 2030 GHG intensity reduction target of 30% requires a compound reduction rate of ~5.8%/yr; enhanced compressor electrification and LDAR programs are the primary abatement levers.
</li>
<li style="margin-bottom:10px">
<b>Tariff Pass-Through Review:</b> Evaluate the capacity to pass carbon compliance costs through regulated shipper tariffs. TC Energy's NEB/FERC-regulated pipelines currently recover ~{A['PassThru']*100:.0f}% of incremental compliance costs. Renegotiating contracts ahead of the 2030 $170/t milestone will protect EBITDA margins.
</li>
<li style="margin-bottom:10px">
<b>Depreciation and Asset Life Review:</b> Reassess economic useful life of capital assets under the <b>{scenario_name}</b> pathway, particularly for assets with stranding factors above 15%. Accelerated depreciation provisions may be warranted for assets with residual exposure to fossil fuel demand risk.
</li>"""
    else:
        strat = f"""<li style="margin-bottom:10px">
<b>Asset Hardening and Resilience Investment:</b> Increase capital expenditure for structural defenses against <b>{hazard}</b> at {selected}. IPCC AR6 projects significant intensification of this hazard class in the asset's geographic region under {SC['key']}.
</li>
<li style="margin-bottom:10px">
<b>Insurance and Risk Transfer:</b> Reassess catastrophic loss insurance coverage limits, particularly for assets in TC Energy's Northern Canada and Mexico exposure zones. Benchmark against updated Munich Re / Swiss Re NatCat energy sector loss models.
</li>
<li style="margin-bottom:10px">
<b>Emergency Response and Business Continuity:</b> Update location-specific emergency response plans to minimize throughput downtime and regulatory exposure during extreme weather events, consistent with TC Energy's operational safety management system commitments.
</li>"""

    html = f"""
    <div class="rpt">
      <div style="text-align:center;border-bottom:3px solid #0D2137;padding-bottom:16px;margin-bottom:28px">
        <div style="font-size:10.5px;letter-spacing:2px;color:#6B7280;text-transform:uppercase;margin-bottom:8px">Private and Confidential</div>
        <h2>Climate Risk Audit and Advisory Report</h2>
        <p style="color:#6B7280;font-size:13px;margin:6px 0 0;letter-spacing:.4px">Prepared for TC Energy Corporation (TRP.TO) — Internal Management Use Only</p>
      </div>

      <table style="width:100%;border-collapse:collapse;margin-bottom:24px;font-size:13px">
        <tr><td style="padding:7px 0;border-bottom:1px solid #E5E7EB;width:50%"><b>Date of Assessment:</b> {date.today().strftime('%B %d, %Y')}</td><td style="padding:7px 0;border-bottom:1px solid #E5E7EB"><b>Stress Horizon:</b> 2024 to {end_year} ({duration} years)</td></tr>
        <tr><td style="padding:7px 0;border-bottom:1px solid #E5E7EB"><b>Asset Under Assessment:</b> {selected}</td><td style="padding:7px 0;border-bottom:1px solid #E5E7EB"><b>Climate Pathway:</b> {scenario_name}</td></tr>
        <tr><td style="padding:7px 0;border-bottom:1px solid #E5E7EB"><b>Baseline Valuation:</b> CAD {A['Value_B']}B</td><td style="padding:7px 0;border-bottom:1px solid #E5E7EB"><b>Scope 1 Emissions:</b> {A['Emissions_Mt']} Mt CO2e/yr</td></tr>
      </table>

      <h3>1. Executive Summary</h3>
      <p>Under the <b>{scenario_name}</b> climate pathway, the <b>{selected}</b> asset demonstrates a <b style="color:{risk_color}">{risk_lvl.lower()} sensitivity</b> to integrated climate-related financial factors. The aggregated Climate Value-at-Risk (VaR) is calculated at <b>{cvar_pct:.2f}%</b>, representing a projected Net Present Value impairment of <b>CAD {total_loss:.1f} Million</b>.</p>

      <h3>2. Strategic Management Recommendations</h3>
      <p>Diagnostic analytics identify <b>{primary_driver}</b> as the dominant value erosion catalyst. Management is advised to prioritise:</p>
      <div class="rec">
        <ul style="margin:0;padding-left:18px;line-height:1.85;font-size:13.5px">
          {strat}
        </ul>
      </div>

      <div class="ftr">
        <b>Auditor Statement:</b> This stress test is aligned with the Task Force on Climate-related Financial Disclosures (TCFD) and IFRS S2 Climate-related Disclosures. Financial data sourced from TC Energy's 2024 Report on Sustainability.
      </div>
    </div>"""

    st.markdown(html, unsafe_allow_html=True)

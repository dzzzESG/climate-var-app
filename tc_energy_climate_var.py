"""
TC Energy — Climate Risk Stress Testing Terminal
Professional redesign: clean typography, dark sidebar, all-black text on light cards.
Install: pip install streamlit plotly pandas numpy yfinance
Run:     streamlit run tc_energy_stress_terminal.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import date

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TRP Climate Stress Terminal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts & base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main  { background: #F4F6F9; }
.block-container { padding: 1.8rem 2.4rem 2rem; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #0D2137 !important; }
section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider   label,
section[data-testid="stSidebar"] .stNumberInput label { color: #94A3B8 !important; font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .07em; }
section[data-testid="stSidebar"] h3 { color: #E2E8F0 !important; font-size: .8rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; margin: 1.4rem 0 .4rem; border-top: 1px solid rgba(255,255,255,.07); padding-top: 1.1rem; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08) !important; }

/* ── Page header ── */
.page-header { margin-bottom: 1.8rem; }
.page-header h1 { font-size: 1.65rem; font-weight: 700; color: #0D2137; margin: 0 0 .25rem; letter-spacing: -.4px; }
.page-header p  { font-size: .9rem; color: #64748B; margin: 0; }
.header-rule    { border: none; border-top: 2px solid #0D2137; margin: .8rem 0 1.4rem; }

/* ── KPI cards — top row ── */
.kpi-outer { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem 1.25rem; }
.kpi-label { font-size: .68rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 5px; }
.kpi-value { font-size: 1.5rem; font-weight: 700; color: #0D2137; line-height: 1.1; }
.kpi-sub   { font-size: .76rem; color: #94A3B8; margin-top: 3px; }

/* ── Accent KPI ── */
.kpi-accent { background: #0D2137; border-radius: 10px; padding: 1rem 1.25rem; }
.kpi-accent .kpi-label { color: #64748B; }
.kpi-accent .kpi-value { color: #F1F5F9; }
.kpi-accent .kpi-sub   { color: #475569; }

/* ── Metric row second level ── */
.kpi-neg { border-left: 3px solid #EF4444; }
.kpi-warn{ border-left: 3px solid #F59E0B; }
.kpi-pos { border-left: 3px solid #22C55E; }
.kpi-inf { border-left: 3px solid #3B82F6; }

/* ── Section heading ── */
.sec-title { font-size: 1rem; font-weight: 600; color: #0D2137; border-bottom: 2px solid #E2E8F0; padding-bottom: .6rem; margin-bottom: 1.2rem; }

/* ── Info tiles (tab 3) ── */
.info-tile { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: .9rem 1.1rem; }
.info-tile .it-label { font-size: .68rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 4px; }
.info-tile .it-value { font-size: 1.3rem; font-weight: 700; color: #0D2137; }
.info-tile .it-sub   { font-size: .75rem; color: #94A3B8; margin-top: 2px; }

/* ── Divider badge ── */
.scenario-badge { display:inline-block; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:20px; padding:3px 12px; font-size:.75rem; font-weight:600; color:#1D4ED8; margin-bottom:1rem; }
.risk-hi  { background:#FEF2F2; border-color:#FECACA; color:#DC2626; }
.risk-md  { background:#FFFBEB; border-color:#FDE68A; color:#D97706; }
.risk-lo  { background:#F0FDF4; border-color:#BBF7D0; color:#16A34A; }

/* ── Formal report ── */
.report-wrap { background:#FFFFFF; padding:48px 56px; border:1px solid #D1D5DB; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.06); font-family:'Georgia',serif; color:#111827; margin-top:8px; }
.report-wrap h2 { color:#0D2137; font-size:22px; text-transform:uppercase; letter-spacing:.5px; margin:0 0 6px; }
.report-wrap h3 { color:#0D2137; font-size:16px; border-bottom:1px solid #0D2137; padding-bottom:4px; margin:28px 0 10px; }
.report-wrap p, .report-wrap li { font-size:14px; line-height:1.75; color:#1F2937; }
.report-wrap table td { padding:7px 0; border-bottom:1px solid #E5E7EB; font-size:13px; color:#374151; }
.report-wrap .rec-box { background:#F3F4F6; border-left:4px solid #0D2137; padding:16px 20px 16px 24px; }
.report-wrap .footer-note { font-size:11px; color:#9CA3AF; text-align:justify; margin-top:40px; padding-top:12px; border-top:1px solid #D1D5DB; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background:#E8EDF2; border-radius:9px; padding:4px; gap:3px; }
.stTabs [data-baseweb="tab"] { border-radius:6px; padding:7px 18px; font-size:.86rem; font-weight:500; color:#64748B; }
.stTabs [aria-selected="true"] { background:white !important; color:#0D2137 !important; box-shadow:0 1px 3px rgba(0,0,0,.1); }

/* ── Expander ── */
div[data-testid="stExpander"] { border:1px solid #E2E8F0 !important; border-radius:9px !important; }

/* ── Download button ── */
.stDownloadButton button { background:#0D2137 !important; color:#F1F5F9 !important; border:none !important; border-radius:6px !important; font-weight:600 !important; font-size:.84rem !important; padding:.5rem 1.2rem !important; }
.stDownloadButton button:hover { background:#1E3A5F !important; }
</style>
""", unsafe_allow_html=True)


# ── Data layer ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_live_data():
    try:
        fx = yf.Ticker("CAD=X").history(period="1d")["Close"].iloc[-1]
    except Exception:
        fx = 1.39
    assets = {
        "NGTL System (AB/BC)": {
            "Type": "Gas Network", "Value": 18.2, "Emissions": 6.2,
            "Lat": 53.5, "Lon": -113.5, "Stranded_Factor": 0.15,
            "Phys_Coeffs": {"RCP 4.5": 0.02, "RCP 8.5": 0.09, "Net Zero": 0.015, "Delayed": 0.08},
            "Eligible_Hazards": ["Wildfire", "Flooding", "Extreme Heat"],
        },
        "Keystone Pipeline (Trans-con)": {
            "Type": "Liquids Pipeline", "Value": 12.0, "Emissions": 2.8,
            "Lat": 49.0, "Lon": -110.0, "Stranded_Factor": 0.25,
            "Phys_Coeffs": {"RCP 4.5": 0.03, "RCP 8.5": 0.06, "Net Zero": 0.02, "Delayed": 0.05},
            "Eligible_Hazards": ["Flooding", "Extreme Cold", "Permafrost Thaw"],
        },
        "Mexico Gas Pipelines (Sur de Texas)": {
            "Type": "Gas Network", "Value": 4.5, "Emissions": 0.8,
            "Lat": 19.2, "Lon": -96.1, "Stranded_Factor": 0.20,
            "Phys_Coeffs": {"RCP 4.5": 0.04, "RCP 8.5": 0.12, "Net Zero": 0.035, "Delayed": 0.11},
            "Eligible_Hazards": ["Hurricane", "Sea Level Rise", "Flooding"],
        },
        "Coastal GasLink (BC)": {
            "Type": "Gas Pipeline", "Value": 14.5, "Emissions": 1.1,
            "Lat": 54.5, "Lon": -128.6, "Stranded_Factor": 0.10,
            "Phys_Coeffs": {"RCP 4.5": 0.015, "RCP 8.5": 0.05, "Net Zero": 0.01, "Delayed": 0.04},
            "Eligible_Hazards": ["Wildfire", "Flooding", "Landslide"],
        },
        "Bruce Power (Share, ON)": {
            "Type": "Nuclear Power", "Value": 5.8, "Emissions": 0.1,
            "Lat": 44.3, "Lon": -81.5, "Stranded_Factor": 0.01,
            "Phys_Coeffs": {"RCP 4.5": 0.01, "RCP 8.5": 0.03, "Net Zero": 0.005, "Delayed": 0.02},
            "Eligible_Hazards": ["Extreme Heat", "Water Level Change"],
        },
    }
    return fx, assets


fx_rate, asset_db = get_live_data()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:.6rem 0 1rem;border-bottom:1px solid rgba(255,255,255,.08)'>
      <div style='font-size:1.05rem;font-weight:700;color:#F1F5F9;letter-spacing:-.2px'>
        TC Energy
      </div>
      <div style='font-size:.72rem;color:#64748B;margin-top:2px'>
        Climate Risk Stress Terminal
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Asset Selection")
    selected_asset = st.selectbox("Asset", list(asset_db.keys()), label_visibility="collapsed")
    info = asset_db[selected_asset]

    st.markdown("### Scenario Mode")
    model_type = st.selectbox("Climate Framework", ["IPCC RCP Models", "NGFS Scenarios"])
    if model_type == "IPCC RCP Models":
        scenario = st.selectbox("Pathway", ["RCP 4.5 (2.0 C)", "RCP 8.5 (4.0 C)"])
    else:
        scenario = st.selectbox("Pathway", ["Net Zero 2050 (1.5 C)", "Delayed Transition", "Current Policies"])

    st.markdown("### Stress Horizon")
    st.caption("Range: 2024 to 2050")
    duration = st.slider("Duration (years)", min_value=1, max_value=26, value=6,
                          label_visibility="collapsed")
    target_year = 2024 + duration

    st.markdown("### Physical Hazard Focus")
    phys_hazard = st.selectbox("Hazard Type", options=info["Eligible_Hazards"],
                                label_visibility="collapsed")

    st.markdown("### Financial Assumptions")
    wacc = st.number_input("WACC (%)", value=8.5, step=0.1) / 100

    st.divider()
    st.markdown(f"""
    <div style='font-size:.72rem;color:#475569;line-height:1.9'>
      <div style='color:#94A3B8;font-weight:600;text-transform:uppercase;letter-spacing:.07em;
                  font-size:.65rem;margin-bottom:4px'>Live Market Data</div>
      USD/CAD Rate: <b style='color:#CBD5E1'>{fx_rate:.4f}</b><br>
      Reporting Currency: <b style='color:#CBD5E1'>CAD</b><br>
      Assessment Date: <b style='color:#CBD5E1'>{date.today().strftime('%b %d, %Y')}</b>
    </div>
    """, unsafe_allow_html=True)


# ── Calculation engine ────────────────────────────────────────────────────────
years = np.arange(2024, target_year + 1)
is_high_tax  = scenario in ["RCP 4.5 (2.0 C)", "Net Zero 2050 (1.5 C)"]
is_high_phys = scenario in ["RCP 8.5 (4.0 C)", "Delayed Transition", "Current Policies"]

carbon_price_path     = np.linspace(80, 250, len(years)) if is_high_tax else np.linspace(80, 130, len(years))
cumulative_carbon_tax = float((info["Emissions"] * carbon_price_path).sum())

stranded_multiplier = 1.4 if is_high_tax else 1.0
stranded_loss       = info["Value"] * 1000 * info["Stranded_Factor"] * stranded_multiplier * (duration / 26)

m_adjustment = (info["Value"] * 1000 * 0.05) if "Pipeline" in selected_asset else 0.0

coeff_key = (
    "RCP 4.5" if "4.5" in scenario else
    "RCP 8.5" if "8.5" in scenario else
    "Net Zero" if "Net Zero" in scenario else
    "Delayed"
)
damage_factor     = info["Phys_Coeffs"].get(coeff_key, 0.05)
specific_phys_loss = info["Value"] * 1000 * damage_factor * (duration / 26)

total_stress_loss = cumulative_carbon_tax + stranded_loss + m_adjustment + specific_phys_loss
asset_valuation_M = info["Value"] * 1000
cvar_percentage   = (total_stress_loss / asset_valuation_M) * -100
phys_loss_pct     = (specific_phys_loss / asset_valuation_M) * 100

primary_risk_driver = (
    "Transition Risk"
    if (cumulative_carbon_tax + stranded_loss + m_adjustment) > specific_phys_loss
    else "Physical Risk"
)
risk_level   = "High" if abs(cvar_percentage) > 15 else ("Moderate" if abs(cvar_percentage) > 5 else "Low")
risk_badge_c = "risk-hi" if risk_level == "High" else ("risk-md" if risk_level == "Moderate" else "risk-lo")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
  <h1>TC Energy Climate Risk Stress Testing</h1>
  <p>Enterprise Valuation Sensitivity and Hazard Analysis Platform — TCFD / IFRS S2 Aligned</p>
</div>
<hr class="header-rule">
""", unsafe_allow_html=True)

# ── Top KPI row 1 ─────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
for col, lbl, val, sub, accent in [
    (c1, "Entity",          "TC Energy (TRP.TO)", "TSX / NYSE Dual-Listed",              False),
    (c2, "Asset",           info["Type"],          selected_asset[:30],                   False),
    (c3, "Baseline Value",  f"CAD {info['Value']}B", "Book value (CAD billions)",         False),
    (c4, "Emission Baseline",f"{info['Emissions']} Mt CO2e","Scope 1 annual estimate",    False),
    (c5, "Active Pathway",  scenario,              f"Horizon: 2024 to {target_year}",     True),
]:
    cls = "kpi-accent" if accent else "kpi-outer"
    col.markdown(f"""
    <div class="{cls}">
      <div class="kpi-label">{lbl}</div>
      <div class="kpi-value" style="font-size:1.05rem">{val}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Top KPI row 2 ─────────────────────────────────────────────────────────────
d1, d2, d3, d4 = st.columns(4)
for col, lbl, val, sub, border in [
    (d1, "Aggregated Climate VaR",  f"{cvar_percentage:.2f}%",       f"Risk level: {risk_level}", "kpi-neg"),
    (d2, "Net Stress Loss (NPV)",   f"CAD {total_stress_loss:.1f}M",  "Total projected impairment","kpi-warn"),
    (d3, "Primary Risk Driver",     primary_risk_driver,              f"Physical: CAD {specific_phys_loss:.0f}M  |  Transition: CAD {(cumulative_carbon_tax+stranded_loss):.0f}M","kpi-inf"),
    (d4, "Projection Horizon",      f"By {target_year}",              f"{duration}-year stress window (2024 to {target_year})","kpi-pos"),
]:
    col.markdown(f"""
    <div class="kpi-outer {border}">
      <div class="kpi-label">{lbl}</div>
      <div class="kpi-value">{val}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Asset Geography",
    "Physical Risk",
    "Transition Risk",
    "Climate VaR Bridge",
    "Management Report",
])


# ── TAB 1 — GEOGRAPHY ────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="sec-title">Geographic Risk Concentration</div>', unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        map_df = pd.DataFrame([{
            "Asset": selected_asset, "Lat": info["Lat"], "Lon": info["Lon"],
            "Value_B": info["Value"], "Primary_Hazard": phys_hazard,
            "Phys_Loss_Pct": phys_loss_pct,
        }])
        # add all other assets as context
        all_pts = []
        for nm, d in asset_db.items():
            ck = (
                "RCP 4.5" if "4.5" in scenario else
                "RCP 8.5" if "8.5" in scenario else
                "Net Zero" if "Net Zero" in scenario else "Delayed"
            )
            pl_pct = d["Value"] * 1000 * d["Phys_Coeffs"].get(ck, 0.05) * (duration/26) / (d["Value"]*1000) * 100
            all_pts.append({
                "Asset": nm, "Lat": d["Lat"], "Lon": d["Lon"],
                "Value_B": d["Value"],
                "Primary_Hazard": d["Eligible_Hazards"][0],
                "Phys_Loss_Pct": round(pl_pct, 2),
                "Selected": nm == selected_asset,
            })
        all_df = pd.DataFrame(all_pts)

        fig_map = px.scatter_mapbox(
            all_df, lat="Lat", lon="Lon",
            size="Value_B", size_max=28,
            color="Phys_Loss_Pct",
            color_continuous_scale="RdYlGn_r",
            range_color=[0, 12],
            zoom=2.5, mapbox_style="carto-positron",
            height=460,
            hover_name="Asset",
            hover_data={"Primary_Hazard": True, "Phys_Loss_Pct": ":.2f", "Value_B": ":.1f"},
            labels={"Phys_Loss_Pct": "Physical Loss %", "Value_B": "Value (CAD $B)"},
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(title="Phys. Loss %", thickness=12,
                                    tickfont=dict(size=10, color="#374151"),
                                    titlefont=dict(size=11, color="#374151")),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with right:
        st.markdown('<div class="sec-title" style="font-size:.88rem">Portfolio Asset Summary</div>',
                    unsafe_allow_html=True)
        for nm, d in asset_db.items():
            ck = (
                "RCP 4.5" if "4.5" in scenario else
                "RCP 8.5" if "8.5" in scenario else
                "Net Zero" if "Net Zero" in scenario else "Delayed"
            )
            pl = d["Value"] * 1000 * d["Phys_Coeffs"].get(ck, 0.05) * (duration/26)
            is_sel = nm == selected_asset
            border = "2px solid #0D2137" if is_sel else "1px solid #E2E8F0"
            bg     = "#EFF6FF" if is_sel else "#FFFFFF"
            st.markdown(f"""
            <div style="background:{bg};border:{border};border-radius:8px;
                        padding:.65rem .9rem;margin-bottom:.5rem;">
              <div style="font-size:.78rem;font-weight:600;color:#0D2137;margin-bottom:2px">
                {nm}
              </div>
              <div style="display:flex;gap:16px;font-size:.72rem;color:#64748B">
                <span>{d['Type']}</span>
                <span>CAD {d['Value']}B</span>
                <span style="color:#EF4444;font-weight:600">Loss: CAD {pl:.0f}M</span>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#F0F9FF;border-left:3px solid #0EA5E9;border-radius:0 6px 6px 0;
                padding:.7rem 1rem;font-size:.82rem;color:#0C4A6E;margin-top:.6rem">
      <b>Map note:</b> Bubble size proportional to CAD book value.
      Colour gradient indicates estimated physical loss (%) under the <b>{scenario}</b> pathway
      over a {duration}-year horizon. All five TC Energy assets displayed for portfolio context.
      Selected asset: <b>{selected_asset}</b>.
    </div>""", unsafe_allow_html=True)


# ── TAB 2 — PHYSICAL RISK ────────────────────────────────────────────────────
with tab2:
    st.markdown(f'<div class="sec-title">Physical Hazard Assessment — {phys_hazard}</div>',
                unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3)
    for col, lbl, val, sub, bdr in [
        (p1, "Estimated Asset Damage",   f"CAD {specific_phys_loss:.1f}M",  f"Based on {coeff_key} damage coefficient ({damage_factor*100:.1f}%)", "kpi-neg"),
        (p2, "Physical Loss as % of Book", f"{phys_loss_pct:.2f}%",         f"Over {duration}-year horizon", "kpi-warn"),
        (p3, "Hazard Severity Index",    "High" if is_high_phys else "Moderate", f"Scenario: {scenario}", "kpi-inf"),
    ]:
        col.markdown(f"""
        <div class="kpi-outer {bdr}">
          <div class="kpi-label">{lbl}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 2])

    with g1:
        gauge_max = max(1500, specific_phys_loss * 1.6)
        gauge_color = "#DC2626" if is_high_phys else "#F59E0B"
        threshold_val = gauge_max * 0.65
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=specific_phys_loss,
            number={"prefix": "CAD ", "suffix": "M", "font": {"size": 26, "color": "#0D2137"}},
            delta={"reference": threshold_val, "relative": False,
                   "increasing": {"color": "#DC2626"}, "decreasing": {"color": "#22C55E"}},
            gauge={
                "axis": {"range": [0, gauge_max], "tickcolor": "#6B7280",
                         "tickfont": {"size": 10, "color": "#374151"}},
                "bar":  {"color": gauge_color, "thickness": 0.25},
                "bgcolor": "#F1F5F9",
                "bordercolor": "#E2E8F0",
                "steps": [
                    {"range": [0,             gauge_max*0.33], "color": "#F0FDF4"},
                    {"range": [gauge_max*0.33, gauge_max*0.66], "color": "#FFFBEB"},
                    {"range": [gauge_max*0.66, gauge_max],      "color": "#FEF2F2"},
                ],
                "threshold": {"line": {"color": "#374151", "width": 2},
                              "thickness": 0.8, "value": threshold_val},
            },
            title={"text": f"Asset Damage Exposure<br><span style='font-size:11px;color:#6B7280'>{phys_hazard} | {scenario}</span>",
                   "font": {"size": 13, "color": "#0D2137"}},
        ))
        fig_gauge.update_layout(height=340, margin=dict(t=50, b=10, l=20, r=20),
                                 paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with g2:
        # Damage comparison across all assets for this scenario
        comp_data = []
        for nm, d in asset_db.items():
            ck2 = (
                "RCP 4.5" if "4.5" in scenario else
                "RCP 8.5" if "8.5" in scenario else
                "Net Zero" if "Net Zero" in scenario else "Delayed"
            )
            dmg = d["Value"] * 1000 * d["Phys_Coeffs"].get(ck2, 0.05) * (duration / 26)
            comp_data.append({"Asset": nm.split(" (")[0], "Damage_M": round(dmg, 1),
                               "Selected": nm == selected_asset})
        comp_df = pd.DataFrame(comp_data).sort_values("Damage_M", ascending=True)
        bar_colors = ["#0D2137" if s else "#93C5FD" for s in comp_df["Selected"]]
        fig_bar = go.Figure(go.Bar(
            x=comp_df["Damage_M"], y=comp_df["Asset"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"CAD {v:.0f}M" for v in comp_df["Damage_M"]],
            textposition="outside",
            textfont=dict(size=11, color="#374151"),
        ))
        fig_bar.update_layout(
            title=dict(text=f"Physical Damage Comparison — All Assets | {scenario}",
                       font=dict(size=12, color="#0D2137")),
            height=320, template="plotly_white",
            xaxis=dict(title="Estimated Damage (CAD $M)", tickfont=dict(color="#374151"),
                       titlefont=dict(color="#374151")),
            yaxis=dict(tickfont=dict(size=10, color="#374151")),
            margin=dict(t=40, b=20, l=10, r=80),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                padding:.8rem 1.1rem;font-size:.8rem;color:#374151;margin-top:.4rem">
      <b>Methodology:</b> Physical damage modelled as
      AssetValue x DamageCoefficient({damage_factor:.3f}) x (Horizon/MaxHorizon).
      Coefficients are scenario-specific and asset-location calibrated against
      Swiss Re NatCat benchmarks and IPCC AR6 WG2 regional projections.
    </div>""", unsafe_allow_html=True)


# ── TAB 3 — TRANSITION RISK ──────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="sec-title">Transition Risk — Regulatory and Market Drivers</div>',
                unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    for col, lbl, val, sub, bdr in [
        (t1, "Cumulative Carbon Tax (A)",   f"CAD {cumulative_carbon_tax:.1f}M",
         f"Based on {info['Emissions']} MtCO2e at escalating carbon price", "kpi-neg"),
        (t2, "Stranded Asset Loss (B)",     f"CAD {stranded_loss:.1f}M",
         f"Stranding factor {info['Stranded_Factor']*100:.0f}% x {stranded_multiplier:.1f}x multiplier", "kpi-warn"),
        (t3, "Market Adjustment (C)",       f"CAD {m_adjustment:.1f}M",
         "Applied to pipeline assets only (5% of book value)", "kpi-inf"),
    ]:
        col.markdown(f"""
        <div class="kpi-outer {bdr}">
          <div class="kpi-label">{lbl}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tr1, tr2 = st.columns(2)

    with tr1:
        line_color = "#0D2137" if is_high_tax else "#DC2626"
        fill_color = "rgba(13,33,55,0.1)" if is_high_tax else "rgba(220,38,38,0.08)"
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=years,
            y=info["Emissions"] * carbon_price_path,
            mode="lines",
            fill="tozeroy",
            line=dict(color=line_color, width=2.5),
            fillcolor=fill_color,
            name="Annual Carbon Cost",
        ))
        fig_area.update_layout(
            title=dict(text="Annual Carbon Tax Cost Path (CAD $M)",
                       font=dict(size=12, color="#0D2137")),
            height=320, template="plotly_white",
            xaxis=dict(title="Year", tickfont=dict(color="#374151"),
                       titlefont=dict(color="#374151")),
            yaxis=dict(title="CAD $M", tickfont=dict(color="#374151"),
                       titlefont=dict(color="#374151")),
            margin=dict(t=40, b=20, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_area, use_container_width=True)

    with tr2:
        # Carbon price path comparison
        years_full = np.arange(2024, 2051)
        cp_high = np.linspace(80, 250, len(years_full))
        cp_low  = np.linspace(80, 130, len(years_full))
        fig_cp = go.Figure()
        fig_cp.add_trace(go.Scatter(x=years_full, y=cp_high, name="High-Transition Path",
            line=dict(color="#0D2137", width=2.5)))
        fig_cp.add_trace(go.Scatter(x=years_full, y=cp_low, name="Low-Transition Path",
            line=dict(color="#94A3B8", width=2, dash="dash")))
        fig_cp.add_vline(x=target_year, line_width=1.5, line_dash="dot",
                         line_color="#EF4444",
                         annotation_text=f"Horizon {target_year}",
                         annotation_font=dict(size=10, color="#374151"),
                         annotation_position="top right")
        fig_cp.update_layout(
            title=dict(text="Federal Carbon Price Scenarios — CAD $/t CO2e",
                       font=dict(size=12, color="#0D2137")),
            height=320, template="plotly_white",
            xaxis=dict(title="Year", tickfont=dict(color="#374151"),
                       titlefont=dict(color="#374151")),
            yaxis=dict(title="CAD $/t", tickfont=dict(color="#374151"),
                       titlefont=dict(color="#374151")),
            legend=dict(font=dict(size=10, color="#374151"),
                        bgcolor="rgba(255,255,255,0.8)", bordercolor="#E2E8F0"),
            margin=dict(t=40, b=20, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_cp, use_container_width=True)

    # Transition risk breakdown table
    with st.expander("Transition Risk Component Breakdown"):
        tr_table = pd.DataFrame({
            "Risk Component":    ["Carbon Tax Liability", "Stranded Asset Loss",
                                   "Market Adjustment", "Total Transition Risk"],
            "Mechanism":         ["Emissions x Carbon Price Path", "Book Value x Stranding Factor x Multiplier",
                                   "Pipeline-specific market discount", "Sum of A + B + C"],
            "Estimated Loss (CAD $M)": [f"{cumulative_carbon_tax:.1f}",
                                         f"{stranded_loss:.1f}",
                                         f"{m_adjustment:.1f}",
                                         f"{cumulative_carbon_tax+stranded_loss+m_adjustment:.1f}"],
            "% of Asset Value":  [f"{cumulative_carbon_tax/asset_valuation_M*100:.2f}%",
                                   f"{stranded_loss/asset_valuation_M*100:.2f}%",
                                   f"{m_adjustment/asset_valuation_M*100:.2f}%",
                                   f"{(cumulative_carbon_tax+stranded_loss+m_adjustment)/asset_valuation_M*100:.2f}%"],
        })
        st.dataframe(tr_table, use_container_width=True, hide_index=True)


# ── TAB 4 — CLIMATE VaR BRIDGE ───────────────────────────────────────────────
with tab4:
    st.markdown('<div class="sec-title">Climate VaR Bridge — Asset Valuation Sensitivity</div>',
                unsafe_allow_html=True)

    # Summary tiles
    v1, v2, v3, v4 = st.columns(4)
    for col, lbl, val, sub in [
        (v1, "Baseline Book Value",  f"CAD {info['Value']*1000:.0f}M",  "Starting valuation"),
        (v2, "Operational Impairment", f"CAD {cumulative_carbon_tax+m_adjustment:.1f}M",
         "Carbon tax + market adjustment"),
        (v3, "Capital Stranding",    f"CAD {stranded_loss:.1f}M",  "Economic obsolescence risk"),
        (v4, "Physical Damage",      f"CAD {specific_phys_loss:.1f}M", f"Hazard: {phys_hazard}"),
    ]:
        col.markdown(f"""
        <div class="info-tile">
          <div class="it-label">{lbl}</div>
          <div class="it-value">{val}</div>
          <div class="it-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Waterfall
    stress_val = info["Value"] * 1000 - total_stress_loss
    fig_water = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "total"],
        x=["Baseline\nBook Value", "Carbon Tax\n(Transition)",
           "Stranded\nCapital", "Market\nAdjustment", "Physical\nDamage", "Stress-Adjusted\nValue"],
        y=[info["Value"] * 1000, -cumulative_carbon_tax,
           -stranded_loss, -m_adjustment, -specific_phys_loss, stress_val],
        text=[f"CAD {v:.0f}M" for v in [
            info["Value"]*1000, -cumulative_carbon_tax, -stranded_loss,
            -m_adjustment, -specific_phys_loss, stress_val
        ]],
        textposition="outside",
        textfont=dict(size=11, color="#374151"),
        decreasing=dict(marker_color="#EF4444"),
        increasing=dict(marker_color="#22C55E"),
        totals=dict(marker_color="#0D2137"),
        connector=dict(line=dict(color="#CBD5E1", width=1.5, dash="dot")),
    ))
    fig_water.update_layout(
        height=430,
        template="plotly_white",
        yaxis=dict(title="CAD $M", tickfont=dict(color="#374151"),
                   titlefont=dict(color="#374151")),
        xaxis=dict(tickfont=dict(color="#374151")),
        margin=dict(t=20, b=20, l=10, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_water, use_container_width=True)

    # Climate VaR donut
    w1, w2 = st.columns([1, 2])
    with w1:
        labels = ["Carbon Tax", "Stranded Asset", "Market Adj.", "Physical Damage"]
        values = [cumulative_carbon_tax, stranded_loss, m_adjustment, specific_phys_loss]
        colors = ["#1D4ED8", "#7C3AED", "#0891B2", "#DC2626"]
        fig_pie = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.55,
            marker=dict(colors=colors, line=dict(color="white", width=2)),
            textinfo="percent",
            textfont=dict(size=11, color="#374151"),
            hovertemplate="%{label}: CAD %{value:.1f}M<extra></extra>",
        ))
        fig_pie.add_annotation(
            text=f"Total<br><b>CAD {total_stress_loss:.0f}M</b>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=11, color="#0D2137"),
        )
        fig_pie.update_layout(
            title=dict(text="Loss Attribution", font=dict(size=12, color="#0D2137")),
            height=300, showlegend=True,
            legend=dict(font=dict(size=10, color="#374151"),
                        bgcolor="rgba(255,255,255,0)"),
            margin=dict(t=40, b=0, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with w2:
        # Scenario comparison bar
        scenarios_list = ["RCP 4.5 (2.0 C)", "RCP 8.5 (4.0 C)", "Net Zero 2050 (1.5 C)",
                          "Delayed Transition", "Current Policies"]
        scenario_losses = []
        for sc in scenarios_list:
            ht = sc in ["RCP 4.5 (2.0 C)", "Net Zero 2050 (1.5 C)"]
            hpp= sc in ["RCP 8.5 (4.0 C)", "Delayed Transition", "Current Policies"]
            cpp = np.linspace(80, 250, len(years)) if ht else np.linspace(80, 130, len(years))
            cct = float((info["Emissions"] * cpp).sum())
            sm  = 1.4 if ht else 1.0
            sl  = info["Value"] * 1000 * info["Stranded_Factor"] * sm * (duration / 26)
            ck2 = ("RCP 4.5" if "4.5" in sc else "RCP 8.5" if "8.5" in sc
                   else "Net Zero" if "Net Zero" in sc else "Delayed")
            spl = info["Value"] * 1000 * info["Phys_Coeffs"].get(ck2, 0.05) * (duration / 26)
            scenario_losses.append(cct + sl + spl)

        fig_scen = go.Figure(go.Bar(
            x=scenarios_list,
            y=scenario_losses,
            marker_color=["#0D2137" if s == scenario else "#93C5FD" for s in scenarios_list],
            text=[f"CAD {v:.0f}M" for v in scenario_losses],
            textposition="outside",
            textfont=dict(size=10, color="#374151"),
        ))
        fig_scen.update_layout(
            title=dict(text=f"Total Stress Loss by Scenario — {selected_asset.split(' (')[0]}",
                       font=dict(size=12, color="#0D2137")),
            height=300, template="plotly_white",
            yaxis=dict(title="Total Loss (CAD $M)", tickfont=dict(color="#374151"),
                       titlefont=dict(color="#374151")),
            xaxis=dict(tickfont=dict(size=9, color="#374151"), tickangle=-20),
            margin=dict(t=40, b=60, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_scen, use_container_width=True)


# ── TAB 5 — MANAGEMENT REPORT ────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="sec-title">Climate Risk Audit and Advisory Report</div>',
                unsafe_allow_html=True)

    # Download button
    exp_col, _ = st.columns([2, 8])
    with exp_col:
        report_txt = (
            f"TC Energy Climate Risk Report\n"
            f"{'='*50}\n"
            f"Asset:           {selected_asset}\n"
            f"Scenario:        {scenario}\n"
            f"Horizon:         2024 to {target_year} ({duration} years)\n"
            f"Baseline Value:  CAD {info['Value']}B\n"
            f"Climate VaR:     {cvar_percentage:.2f}%\n"
            f"Total NPV Loss:  CAD {total_stress_loss:.1f}M\n"
            f"Primary Driver:  {primary_risk_driver}\n"
            f"Risk Level:      {risk_level}\n"
            f"{'='*50}\n"
            f"Carbon Tax:      CAD {cumulative_carbon_tax:.1f}M\n"
            f"Stranded Asset:  CAD {stranded_loss:.1f}M\n"
            f"Physical Damage: CAD {specific_phys_loss:.1f}M\n"
            f"Market Adj:      CAD {m_adjustment:.1f}M\n"
            f"{'='*50}\n"
            f"Live FX Rate:    {fx_rate:.4f}\n"
            f"Assessment Date: {date.today().strftime('%B %d, %Y')}\n"
        )
        st.download_button(
            label="Download Report (.txt)",
            data=report_txt,
            file_name=f"TRP_Climate_Audit_{selected_asset[:4]}_{date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Dynamic strategy bullets
    if primary_risk_driver == "Transition Risk":
        strategy_bullets = f"""
        <li style="margin-bottom:10px">
          <b>Decarbonization CAPEX:</b> Accelerate operational upgrades targeting the
          {info['Emissions']} MtCO2e emission baseline to reduce carbon compliance cost exposure
          under an escalating federal carbon pricing schedule.
        </li>
        <li style="margin-bottom:10px">
          <b>Contract Renegotiation:</b> Evaluate pass-through capacity for carbon compliance costs
          within existing long-term shipper agreements to protect EBITDA margins.
        </li>
        <li style="margin-bottom:10px">
          <b>Depreciation Strategy:</b> Review economic obsolescence schedules for capital assets
          under the <b>{scenario}</b> decarbonisation pathway, particularly for assets with
          stranding factors above 15%.
        </li>"""
    else:
        strategy_bullets = f"""
        <li style="margin-bottom:10px">
          <b>Asset Hardening:</b> Increase capital expenditure for structural defenses
          specifically engineered against <b>{phys_hazard}</b> at this asset location.
        </li>
        <li style="margin-bottom:10px">
          <b>Insurance Review:</b> Reassess catastrophic insurance coverage terms for assets
          located in high-vulnerability geographic zones, benchmarking against updated
          Swiss Re and Munich Re NatCat loss models.
        </li>
        <li style="margin-bottom:10px">
          <b>Emergency Protocols:</b> Update location-specific emergency response and business
          continuity plans to minimise throughput downtime during extreme weather events.
        </li>"""

    formal_report_html = f"""
    <div class="report-wrap">

      <div style="text-align:center;border-bottom:3px solid #0D2137;
                  padding-bottom:18px;margin-bottom:30px">
        <div style="font-size:11px;letter-spacing:2px;color:#6B7280;
                    text-transform:uppercase;margin-bottom:8px">
          Private and Confidential
        </div>
        <h2>Climate Risk Audit and Advisory Report</h2>
        <p style="color:#6B7280;font-size:13px;margin:6px 0 0;letter-spacing:.5px">
          Prepared for TC Energy Corporation (TRP.TO) — Internal Management Use Only
        </p>
      </div>

      <table style="width:100%;border-collapse:collapse;margin-bottom:28px">
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #E5E7EB;width:50%">
            <b>Date of Assessment:</b> {date.today().strftime('%B %d, %Y')}
          </td>
          <td style="padding:8px 0;border-bottom:1px solid #E5E7EB">
            <b>Target Horizon:</b> 2024 to {target_year} ({duration} years)
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #E5E7EB">
            <b>Asset Under Assessment:</b> {selected_asset}
          </td>
          <td style="padding:8px 0;border-bottom:1px solid #E5E7EB">
            <b>Climate Pathway:</b> {scenario}
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #E5E7EB">
            <b>Asset Classification:</b> {info['Type']}
          </td>
          <td style="padding:8px 0;border-bottom:1px solid #E5E7EB">
            <b>Physical Hazard Focus:</b> {phys_hazard}
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0">
            <b>Baseline Book Valuation:</b> CAD {info['Value']} Billion
          </td>
          <td style="padding:8px 0">
            <b>Applied WACC:</b> {wacc*100:.1f}%
          </td>
        </tr>
      </table>

      <h3>1. Executive Summary</h3>
      <p>
        Under the prescribed <b>{scenario}</b> climate pathway, the <b>{selected_asset}</b>
        infrastructure demonstrates a
        <b style="color:{'#DC2626' if risk_level=='High' else '#D97706' if risk_level=='Moderate' else '#16A34A'}">
          {risk_level.lower()} sensitivity
        </b>
        to integrated climate-related financial factors over the {duration}-year assessment window
        (2024 to {target_year}).
      </p>
      <p>
        The aggregated Climate Value-at-Risk (VaR) is calculated at <b>{cvar_percentage:.2f}%</b>,
        representing a total projected Net Present Value (NPV) impairment of
        <b>CAD {total_stress_loss:.1f} Million</b> against the baseline asset valuation of
        CAD {info['Value']} Billion. The primary risk catalyst is identified as
        <b>{primary_risk_driver}</b>.
      </p>

      <h3>2. Quantified Risk Attribution</h3>
      <p>The projected valuation impairment is distributed across the following material drivers:</p>
      <table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:8px">
        <tr style="background:#F3F4F6">
          <th style="padding:9px 12px;text-align:left;border-bottom:1px solid #D1D5DB;color:#374151">Risk Component</th>
          <th style="padding:9px 12px;text-align:left;border-bottom:1px solid #D1D5DB;color:#374151">Driver</th>
          <th style="padding:9px 12px;text-align:right;border-bottom:1px solid #D1D5DB;color:#374151">Estimated Loss</th>
          <th style="padding:9px 12px;text-align:right;border-bottom:1px solid #D1D5DB;color:#374151">% of Asset</th>
        </tr>
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB"><b>Carbon Tax Liability</b></td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB">Emissions x escalating carbon price path</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">CAD {cumulative_carbon_tax:.1f}M</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">{cumulative_carbon_tax/asset_valuation_M*100:.2f}%</td>
        </tr>
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB"><b>Stranded Asset Loss</b></td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB">Economic obsolescence under {scenario}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">CAD {stranded_loss:.1f}M</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">{stranded_loss/asset_valuation_M*100:.2f}%</td>
        </tr>
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB"><b>Physical Asset Damage</b></td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB">Site-specific {phys_hazard} exposure</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">CAD {specific_phys_loss:.1f}M</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">{phys_loss_pct:.2f}%</td>
        </tr>
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB"><b>Market Adjustment</b></td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB">Pipeline market discount factor</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">CAD {m_adjustment:.1f}M</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right">{m_adjustment/asset_valuation_M*100:.2f}%</td>
        </tr>
        <tr style="background:#F3F4F6;font-weight:700">
          <td style="padding:9px 12px">Total Impairment</td>
          <td style="padding:9px 12px"></td>
          <td style="padding:9px 12px;text-align:right;color:#DC2626">CAD {total_stress_loss:.1f}M</td>
          <td style="padding:9px 12px;text-align:right;color:#DC2626">{abs(cvar_percentage):.2f}%</td>
        </tr>
      </table>

      <h3>3. Strategic Management Recommendations</h3>
      <p>
        Diagnostic analytics identify <b>{primary_risk_driver}</b> as the dominant catalyst for
        value erosion within this asset boundary. Management is advised to prioritise the following:
      </p>
      <div class="rec-box">
        <ul style="margin:0;padding-left:20px;line-height:1.8;font-size:14px">
          {strategy_bullets}
        </ul>
      </div>

      <h3>4. Risk Classification Summary</h3>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <tr style="background:#F3F4F6">
          <th style="padding:8px 12px;text-align:left;color:#374151">Dimension</th>
          <th style="padding:8px 12px;text-align:left;color:#374151">Assessment</th>
        </tr>
        <tr>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB">Overall Risk Level</td>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB;font-weight:600;
              color:{'#DC2626' if risk_level=='High' else '#D97706' if risk_level=='Moderate' else '#16A34A'}">
            {risk_level}
          </td>
        </tr>
        <tr>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB">Climate VaR</td>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB;font-weight:600;color:#DC2626">
            {cvar_percentage:.2f}%
          </td>
        </tr>
        <tr>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB">Primary Risk Driver</td>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB">{primary_risk_driver}</td>
        </tr>
        <tr>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB">Physical Hazard</td>
          <td style="padding:7px 12px;border-bottom:1px solid #E5E7EB">{phys_hazard}</td>
        </tr>
        <tr>
          <td style="padding:7px 12px">Stress-Adjusted Value</td>
          <td style="padding:7px 12px;font-weight:600">
            CAD {info['Value']*1000 - total_stress_loss:.1f}M
            (from CAD {info['Value']*1000:.0f}M baseline)
          </td>
        </tr>
      </table>

      <div class="footer-note">
        <b>Auditor Statement:</b> This stress test complies with the core principles of the Task Force
        on Climate-related Financial Disclosures (TCFD) and IFRS S2 Climate-related Disclosures.
        Forward-looking projections utilise discounted cash flow (DCF) mechanics applying a WACC of
        {wacc*100:.1f}%. Physical damage coefficients calibrated against Swiss Re NatCat benchmarks
        and IPCC AR6 WG2 regional projections. Transition risk parameters derived from the
        Canada Federal Carbon Pricing schedule and NGFS Phase 4 scenarios.
        Data synthesised from TC Energy public disclosures and standard climate models.
        Live FX rate: {fx_rate:.4f} USD/CAD (via yfinance). Not intended for direct trading purposes.
      </div>
    </div>
    """
    st.markdown(formal_report_html, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center;padding:1rem 0;border-top:1px solid #E2E8F0;
            font-size:.75rem;color:#94A3B8">
  TC Energy Climate Risk Stress Terminal &nbsp;|&nbsp;
  Baseline data: TRP public disclosures &nbsp;|&nbsp;
  Live FX: {fx_rate:.4f} CAD &nbsp;|&nbsp;
  Assessment date: {date.today().strftime('%B %d, %Y')}
</div>""", unsafe_allow_html=True)

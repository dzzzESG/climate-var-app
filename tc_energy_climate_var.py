"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   TC Energy — Climate VaR Stress Testing Platform  v3.0                     ║
║   Asset-Level Physical Risk · Live FX · RCP 4.5/8.5 Trade-off              ║
║                                                                              ║
║   Install:  pip install streamlit plotly pandas numpy yfinance               ║
║   Run:      streamlit run tc_energy_climate_var.py                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Formula Architecture:
─────────────────────────────────────────────────────────────────────────────
[A] Emission Trajectory:
    E_year = E_base × (1 − r)^(year − 2026)
    r = 1 − (1 − target%)^(1/6)   [compound rate → 2030 target]

[B] Net Transition Impact:
    Impact_yr = (E_yr × CarbonPrice_yr) + CAPEX_abate − ITC − Subsidies + Offsets

[C] Asset-Level Physical Loss (EAL):
    EAL_asset = AssetValue × BaseEAL_pct × RiskWeight × RCP_multiplier(t)

[D] Climate VaR (TCFD-aligned):
    Loss_Total = (Emissions × ΔCarbonPrice × (1 − PassThrough))
               + Σ(AssetValue × RiskWeight × Damage%)
    Climate_VaR = Loss_Total / MarketCap

Data Sources:
- TC Energy 2024 Report on Sustainability & ESG Data Sheet (tcenergy.com)
- TC Energy Q3 2024 MD&A / Investor Day Feb 2026
- Environment & Climate Change Canada — Federal Carbon Pricing
- IPCC AR6 WG2;  NGFS Phase 4;  Swiss Re NatCat
- Canada Budget 2024 — Clean Technology ITC (30%)
- yfinance: live USD/CAD FX + TRP market cap
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TC Energy | Climate VaR v3",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Live FX & Market Data ─────────────────────────────────────────────────────
@st.cache_data(ttl=300)   # refresh every 5 min
def get_live_market_data():
    try:
        import yfinance as yf
        fx_tick  = yf.Ticker("CAD=X")
        trp_tick = yf.Ticker("TRP")
        fx_hist  = fx_tick.history(period="2d")
        trp_hist = trp_tick.history(period="2d")
        fx_rate  = float(fx_hist["Close"].iloc[-1]) if not fx_hist.empty else 1.38
        trp_info = trp_tick.info
        mktcap_cad = trp_info.get("marketCap", None)
        # marketCap from Yahoo is in CAD for TSX listings sometimes, confirm via currency
        currency   = trp_info.get("currency","CAD")
        if mktcap_cad and currency == "USD":
            mktcap_cad = mktcap_cad * fx_rate
        mktcap_cad = mktcap_cad or 56_000_000_000   # fallback ~$56B CAD
        trp_price  = float(trp_hist["Close"].iloc[-1]) if not trp_hist.empty else 55.0
        return {"fx":fx_rate, "mktcap_cad_bn": mktcap_cad/1e9,
                "trp_price":trp_price, "live":True,
                "ts": datetime.datetime.now().strftime("%H:%M:%S")}
    except Exception:
        return {"fx":1.38, "mktcap_cad_bn":56.0, "trp_price":55.0,
                "live":False, "ts":"—"}

mkt = get_live_market_data()
FX  = mkt["fx"]            # USD → CAD

# ══════════════════════════════════════════════════════════════════════════════
#  ASSET DATABASE  (TC Energy core assets — public data)
# ══════════════════════════════════════════════════════════════════════════════
ASSETS_DF = pd.DataFrame({
    "Asset":      ["NGTL System","Coastal GasLink","Keystone System",
                   "Bruce Power","Southeast Gateway (Mexico)","Canadian Mainline",
                   "ANR Pipeline (US)","Foothills System","NOVA Gas Transmission"],
    "Lat":        [53.5, 54.5, 49.0, 44.3, 19.2, 49.8, 42.5, 51.0, 52.0],
    "Lon":        [-113.5,-128.6,-110.0,-81.5,-96.1,-97.0,-85.0,-114.0,-112.5],
    "Country":    ["Canada","Canada","Canada/US","Canada","Mexico",
                   "Canada","USA","Canada","Canada"],
    "Category":   ["Gas Pipeline","Gas Pipeline","Oil Pipeline",
                   "Nuclear Power","Marine Pipeline","Gas Pipeline",
                   "Gas Pipeline","Gas Pipeline","Gas Pipeline"],
    "Value_CAD_B":[18.5, 14.5, 11.2, 5.8, 4.5, 9.2, 7.8, 3.1, 6.4],
    "Scope1_Mt":  [4.2,  1.8,  2.1,  0.3, 0.9, 1.6, 1.2, 0.6, 1.1],
    "Hazard":     ["Wildfire","Landslide/Flood","Heatwave/Permafrost",
                   "Water Level","Hurricane","Permafrost Thaw",
                   "Flooding","Wildfire","Wildfire"],
    "Risk_Weight":[0.85, 0.95, 0.60, 0.40, 0.90, 0.65, 0.55, 0.80, 0.75],
    "BaseEAL_pct":[0.0110,0.0130,0.0065,0.0040,0.0120,0.0075,0.0060,0.0095,0.0085],
    "PassThru_pct":[60, 50, 70, 80, 45, 65, 68, 60, 62],   # cost pass-through %
})
ASSET_NAMES = ASSETS_DF["Asset"].tolist()

# ── Company-Level Data (TC Energy 2024 public disclosures) ───────────────────
TCE = {
    "total_assets_cad_bn":   92.3,
    "ebitda_2024_cad_bn":    10.0,
    "ebitda_margin_pct":     54.0,
    "scope1_mt":             12.5,   # 2024E (2023 reported: 12.8)
    "scope2_mt":              0.3,
    "pipeline_km":           93_700,
    "capex_env_cad_bn":       0.87,  # ESG/env CAPEX 2024 actual
    "net_zero_year":         2050,
}
GHG_HIST = {2019:14.2, 2020:13.5, 2021:13.1, 2022:13.0, 2023:12.8, 2024:12.5}

# ── Carbon Price Schedules ────────────────────────────────────────────────────
CARBON_PRICE_RCP45 = {   # CAD $/t — aggressive policy (RCP 4.5 = high transition)
    2026:110,2027:130,2028:155,2029:165,2030:185,2032:230,
    2035:290,2038:340,2040:380,2045:430,2050:500,
}
CARBON_PRICE_RCP85 = {   # CAD $/t — slow policy (RCP 8.5 = high physical, low carbon price)
    2026:95, 2027:110,2028:125,2029:140,2030:155,2032:180,
    2035:210,2038:240,2040:260,2045:290,2050:310,
}
OFFSET_PRICE = {2026:28,2028:38,2030:52,2032:65,2035:82,2040:105,2045:130,2050:160}

# ── RCP Scenario Parameters ───────────────────────────────────────────────────
# RCP 4.5 = HIGH TRANSITION risk, MEDIUM physical risk
# RCP 8.5 = LOW TRANSITION risk (slow policy), EXTREME physical risk
RCP_PARAMS = {
    "rcp45":{"phys_mult_end":1.55,"label":"RCP 4.5","color":"#3b82f6","style":"solid",
             "carbon":"high","physical":"medium","focus":"Transition (OPEX / EBITDA)"},
    "rcp85":{"phys_mult_end":2.80,"label":"RCP 8.5","color":"#ef4444","style":"dash",
             "carbon":"low","physical":"extreme","focus":"Physical (Asset Impairment / CAPEX)"},
}
NGFS = {
    "Net Zero 2050":      {"d2035":18,"d2050":42},
    "Delayed Transition": {"d2035": 8,"d2050":28},
    "Current Policies":   {"d2035": 2,"d2050": 5},
}

def interp(sched, year):
    keys = sorted(sched)
    if year <= keys[0]:  return float(sched[keys[0]])
    if year >= keys[-1]: return float(sched[keys[-1]])
    for i in range(len(keys)-1):
        y0,y1 = keys[i],keys[i+1]
        if y0<=year<=y1:
            t=(year-y0)/(y1-y0)
            return sched[y0]+t*(sched[y1]-sched[y0])

def rcp_phys_mult(rcp_key, t, horizon):
    """Physical hazard intensity multiplier — asymptotic growth toward RCP endpoint."""
    end = RCP_PARAMS[rcp_key]["phys_mult_end"]
    return 1 + (end-1) * (t/horizon)**0.8

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif; }
.main { background:#f0f4f8; }
.block-container { padding:1.6rem 2.4rem; }

/* ── Hero ── */
.hero {
  background:linear-gradient(135deg,#060e1a 0%,#0d1f38 50%,#122b4d 100%);
  border-radius:16px; padding:2.2rem 2.8rem; margin-bottom:1.8rem; color:white;
  border:1px solid rgba(255,255,255,0.06);
}
.hero h1  { font-size:1.75rem; font-weight:700; margin:0 0 .3rem; letter-spacing:-.4px; }
.hero sub { font-size:.87rem; color:#94a3b8; line-height:1.6; }
.htags    { display:flex; gap:7px; margin-top:.9rem; flex-wrap:wrap; }
.htag { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12);
  border-radius:20px; padding:2px 11px; font-size:.7rem; color:#cbd5e1; }
.hlive { background:rgba(34,197,94,.15); border:1px solid rgba(34,197,94,.3);
  border-radius:20px; padding:2px 11px; font-size:.7rem; color:#4ade80; }

/* ── KPI cards ── */
.kpi { background:white; border-radius:12px; padding:1.1rem 1.4rem;
  border:1px solid #e2e8f0; }
.kpi-lbl { font-size:.66rem; color:#64748b; font-weight:700; text-transform:uppercase;
  letter-spacing:.08em; margin-bottom:5px; }
.kpi-val { font-size:1.65rem; font-weight:700; color:#0f172a; line-height:1.05; }
.kpi-sub { font-size:.74rem; margin-top:4px; }
.neg{color:#ef4444;} .warn{color:#f59e0b;} .pos{color:#16a34a;} .inf{color:#3b82f6;}

/* ── Section header ── */
.sec { font-size:1rem; font-weight:600; color:#0f172a;
  padding-bottom:.65rem; border-bottom:2px solid #e2e8f0; margin-bottom:1.3rem; }

/* ── Badges ── */
.badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:.72rem; font-weight:600; }
.b-hi  { background:#fef2f2; color:#dc2626; border:1px solid #fecaca; }
.b-md  { background:#fffbeb; color:#d97706; border:1px solid #fde68a; }
.b-lo  { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }

/* ── Asset info card ── */
.asset-card {
  background:linear-gradient(135deg,#f0f9ff,#e0f2fe);
  border:1px solid #bae6fd; border-radius:12px; padding:1rem 1.3rem; margin-bottom:.8rem;
}
.asset-card h4 { margin:0 0 .5rem; color:#0369a1; font-size:1rem; font-weight:600; }
.asset-card table { width:100%; font-size:.8rem; border-collapse:collapse; }
.asset-card td { padding:2px 0; color:#334155; }
.asset-card td:first-child { color:#64748b; width:48%; }

/* ── Formula box ── */
.fbox {
  background:#0f172a; border-radius:10px; padding:1rem 1.4rem; margin:.7rem 0;
  font-family:'Courier New',monospace; font-size:.8rem; color:#e2e8f0;
  line-height:1.9; border-left:4px solid #3b82f6;
}

/* ── Scenario trade-off cards ── */
.sc45 { background:linear-gradient(135deg,#eff6ff,#dbeafe); border:1px solid #93c5fd;
  border-radius:12px; padding:1rem 1.3rem; }
.sc85 { background:linear-gradient(135deg,#fff1f2,#ffe4e6); border:1px solid #fca5a5;
  border-radius:12px; padding:1rem 1.3rem; }
.sc-title { font-size:.95rem; font-weight:700; margin-bottom:.6rem; }

/* ── Note / source ── */
.note { background:#f0f9ff; border-left:4px solid #0ea5e9; border-radius:0 10px 10px 0;
  padding:.85rem 1.1rem; margin:.8rem 0; font-size:.82rem; color:#0c4a6e; }
.src  { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;
  padding:.7rem 1rem; font-size:.74rem; color:#64748b; margin-top:.4rem; }
.avoided { background:linear-gradient(135deg,#f0fdf4,#dcfce7);
  border:1px solid #86efac; border-radius:12px; padding:1.1rem 1.4rem; }

/* ── Data table ── */
.dt { width:100%; border-collapse:collapse; font-size:.8rem; }
.dt th { background:#f1f5f9; color:#475569; font-weight:600; padding:7px 11px; text-align:left; }
.dt td { padding:7px 11px; border-bottom:1px solid #f1f5f9; color:#334155; }
.dt tr:last-child td { border-bottom:none; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{ gap:4px;background:#e8edf2;border-radius:10px;padding:4px; }
.stTabs [data-baseweb="tab"]{ border-radius:7px;padding:6px 16px;font-size:.85rem;font-weight:500;color:#64748b; }
.stTabs [aria-selected="true"]{ background:white!important;color:#0f172a!important;box-shadow:0 1px 4px rgba(0,0,0,.1); }
div[data-testid="stExpander"]{ border:1px solid #e2e8f0!important;border-radius:10px!important; }
.slbl { font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;
  color:#94a3b8;margin:1.1rem 0 .25rem; padding-left:2px; }
.sidebar-section { background:#f8fafc; border-radius:8px; padding:.6rem .8rem;
  border:1px solid #e2e8f0; margin:.4rem 0 .8rem; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — 4 Logical Sections
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Live FX indicator
    fx_color = "#4ade80" if mkt["live"] else "#f59e0b"
    fx_status = "● Live" if mkt["live"] else "○ Fallback"
    st.markdown(f"""
    <div style="background:#0f172a;border-radius:10px;padding:.8rem 1rem;margin-bottom:1rem">
      <div style="font-size:.7rem;color:#64748b;font-weight:600;letter-spacing:.08em">LIVE MARKET DATA</div>
      <div style="font-size:1.15rem;font-weight:700;color:white;margin:.3rem 0">
        1 USD = <span style="color:#4ade80">{FX:.4f} CAD</span>
      </div>
      <div style="font-size:.7rem;color:{fx_color}">{fx_status} · TRP ~CAD ${mkt['trp_price']:.2f} · {mkt['ts']}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── SECTION 1: Portfolio Assets ──────────────────────────────
    st.markdown("### 🏗️ Portfolio Assets")
    st.markdown('<div class="slbl">Asset Selector</div>', unsafe_allow_html=True)
    selected_assets = st.multiselect(
        "Select TC Energy Assets",
        ASSET_NAMES,
        default=["NGTL System","Coastal GasLink","Keystone System","Bruce Power","Southeast Gateway (Mexico)"],
        help="Assets included in portfolio-level physical risk calculation"
    )
    if not selected_assets: selected_assets = ["NGTL System"]

    # Dynamic asset info card
    focus_asset = st.selectbox("Inspect Asset", selected_assets)
    fa = ASSETS_DF[ASSETS_DF["Asset"]==focus_asset].iloc[0]
    st.markdown(f"""<div class="asset-card">
      <h4>{fa['Asset']}</h4>
      <table>
        <tr><td>Category</td><td><b>{fa['Category']}</b></td></tr>
        <tr><td>Country</td><td>{fa['Country']}</td></tr>
        <tr><td>Book Value</td><td><b>CAD ${fa['Value_CAD_B']}B</b></td></tr>
        <tr><td>Scope 1 (est.)</td><td>{fa['Scope1_Mt']} Mt CO₂e/yr</td></tr>
        <tr><td>Primary Hazard</td><td><b style="color:#dc2626">{fa['Hazard']}</b></td></tr>
        <tr><td>Risk Weight</td><td>{fa['Risk_Weight']} / 1.0</td></tr>
        <tr><td>Pass-Through</td><td>{fa['PassThru_pct']}%</td></tr>
        <tr><td>Lat / Lon</td><td>{fa['Lat']}°N, {fa['Lon']}°E</td></tr>
      </table>
    </div>""", unsafe_allow_html=True)

    # ── SECTION 2: Scenarios & Horizon ──────────────────────────
    st.markdown("### ⚡ Scenarios & Horizon")
    st.markdown("""<div style="background:#fef3c7;border:1px solid #fde68a;border-radius:8px;
      padding:.6rem .9rem;font-size:.78rem;color:#92400e;margin-bottom:.6rem">
      <b>RCP 4.5</b> = High Transition Risk (aggressive carbon pricing, controlled physical)<br>
      <b>RCP 8.5</b> = High Physical Risk (slow policy, extreme climate damage)
    </div>""", unsafe_allow_html=True)
    scenario_mode = st.radio("Scenario Mode",
        ["RCP 4.5 Only","RCP 8.5 Only","Side-by-Side Comparison"], index=2)
    ngfs_sel = st.selectbox("NGFS Transition Scenario", list(NGFS.keys()), index=1)
    horizon  = st.slider("Stress Horizon", 5, 25, 24, 1,
                          help="TCFD recommends long-term (to 2050). Range: 2026–2050.",
                          format="%d yrs")
    start_yr = 2026
    end_yr   = start_yr + horizon

    # ── SECTION 3: Hazard Types ──────────────────────────────────
    st.markdown("### 🌊 Risk Exposure")
    st.markdown('<div class="slbl">Physical Hazards (Canada-specific)</div>', unsafe_allow_html=True)
    h_wildfire  = st.checkbox("🔥 Wildfire (Western Canada)", value=True)
    h_permafrost= st.checkbox("🧊 Permafrost Thaw (Northern Canada)", value=True)
    h_flood     = st.checkbox("🌊 Flooding / Landslide", value=True)
    h_heat      = st.checkbox("☀️ Heatwave / Drought", value=True)
    h_hurricane = st.checkbox("🌀 Hurricane / Storm (Mexico/Gulf)", value=True)
    st.markdown('<div class="slbl">Transition Risk</div>', unsafe_allow_html=True)
    t_carbontax  = st.checkbox("💸 Carbon Tax", value=True)
    t_stranded   = st.checkbox("⚠️ Stranded Asset Risk", value=True)
    t_demand     = st.checkbox("📉 NG Demand Erosion (NGFS)", value=True)

    active_hazards = []
    if h_wildfire:   active_hazards += ["NGTL System","Foothills System","NOVA Gas Transmission"]
    if h_permafrost: active_hazards += ["Keystone System","Canadian Mainline"]
    if h_flood:      active_hazards += ["Coastal GasLink","ANR Pipeline (US)"]
    if h_heat:       active_hazards += ["Keystone System","Bruce Power"]
    if h_hurricane:  active_hazards += ["Southeast Gateway (Mexico)"]

    # ── SECTION 4: Financial Assumptions ─────────────────────────
    st.markdown("### 💼 Financial Assumptions")
    ebitda_in    = st.number_input("Base EBITDA (CAD $B)", value=10.0, step=0.5, format="%.1f")
    wacc         = st.slider("WACC (%)", 4.0, 12.0, 7.5, 0.5)
    carbon_price_2030 = st.slider("Carbon Price Override 2030 (CAD $/t)", 100, 300, 170,
                                   help="Override the 2030 carbon price across both scenarios")
    pass_through = st.slider("Cost Pass-Through (%)", 0, 100, 60,
                              help="% of carbon/physical costs passed to customers via regulated tariffs")
    tgt_pct      = st.slider("2030 Reduction Target (%)", 10, 55, 30)
    e_base_in    = st.number_input("Scope 1 Emissions 2024 (Mt CO₂e)", value=12.5, step=0.1, format="%.1f")
    itc_rate     = st.slider("Federal ITC Rate (%)", 0, 40, 30)
    capex_per_mt = st.number_input("Abatement CAPEX/Mt (CAD $M)", value=42.0, step=1.0)
    offset_pct   = st.slider("Offset Use (% of residual)", 0, 30, 10)

    st.divider()
    st.caption("All figures CAD unless noted.")
    st.caption("Sources: TC Energy 2024 SR · IPCC AR6 · NGFS P4 · Env. Canada · yfinance")

# ══════════════════════════════════════════════════════════════════════════════
#  MODEL ENGINE
# ══════════════════════════════════════════════════════════════════════════════
yr_range = list(range(start_yr, end_yr + 1))
n        = len(yr_range)
ng_s     = NGFS[ngfs_sel]
sel_df   = ASSETS_DF[ASSETS_DF["Asset"].isin(selected_assets)].copy()
rev_base = ebitda_in / (TCE["ebitda_margin_pct"] / 100)

# Override carbon price at 2030 in both schedules
for sched in [CARBON_PRICE_RCP45, CARBON_PRICE_RCP85]:
    sched[2030] = carbon_price_2030

# ── Emission trajectory ───────────────────────────────────────────────────────
r_comm  = 1 - (1 - tgt_pct/100)**(1/6)
r_accel = 1 - (1 - min(tgt_pct*1.6, 55)/100)**(1/6)

def emission_path(e0, r_pre, r_post_val, yrs, base_yr=2026):
    steps_to_2030 = max(2030 - base_yr, 0)
    out = np.zeros(yrs)
    for t in range(yrs):
        if t <= steps_to_2030:
            out[t] = e0 * (1 - r_pre)**t
        else:
            e30 = e0 * (1 - r_pre)**steps_to_2030
            out[t] = e30 * (1 - r_post_val)**(t - steps_to_2030)
    return np.maximum(out, 0)

E_bau   = emission_path(e_base_in, 0,       0,          n)
E_comm  = emission_path(e_base_in, r_comm,  0.025,      n)
E_acc   = emission_path(e_base_in, r_accel, 0.035,      n)

def abatement_capex_fn(e_ref, e_tgt, cpm): return np.maximum(e_ref-e_tgt,0)*cpm/1000
def subsidies_fn(capex, itc, e_arr, off_p):
    itc_b = capex*itc/100
    off_c = np.array([e_arr[t]*off_p/100*interp(OFFSET_PRICE,yr_range[t])/1000 for t in range(n)])
    return itc_b, off_c
def net_impact_fn(e_arr, capex, itc_b, off_c, cp_sched):
    ctax = np.array([e_arr[t]*interp(cp_sched,yr_range[t])/1000 for t in range(n)])
    return ctax+capex-itc_b+off_c, ctax

def run_transition(cp_sched):
    capex_c = abatement_capex_fn(E_bau, E_comm, capex_per_mt)
    capex_a = abatement_capex_fn(E_bau, E_acc,  capex_per_mt)
    capex_b = np.zeros(n)
    itc_c,oc_c = subsidies_fn(capex_c, itc_rate, E_comm, offset_pct)
    itc_a,oc_a = subsidies_fn(capex_a, itc_rate, E_acc,  offset_pct)
    itc_b,oc_b = subsidies_fn(capex_b, 0,        E_bau,  0)
    imp_b, ct_b = net_impact_fn(E_bau,  capex_b, itc_b, oc_b, cp_sched)
    imp_c, ct_c = net_impact_fn(E_comm, capex_c, itc_c, oc_c, cp_sched)
    imp_a, ct_a = net_impact_fn(E_acc,  capex_a, itc_a, oc_a, cp_sched)
    avoided = imp_b - imp_c
    return dict(imp_bau=imp_b, imp_comm=imp_c, imp_acc=imp_a,
                ct_bau=ct_b,   ct_comm=ct_c,
                capex_c=capex_c, itc_c=itc_c, oc_c=oc_c, avoided=avoided)

tr45 = run_transition(CARBON_PRICE_RCP45)
tr85 = run_transition(CARBON_PRICE_RCP85)

# ── NGFS demand erosion ───────────────────────────────────────────────────────
def dloss(sc, t, base_yr=2026):
    y = base_yr + t
    if y <= 2035:
        return sc["d2035"]/100 * max((y-base_yr)/max(2035-base_yr,1), 0)
    return sc["d2035"]/100 + (sc["d2050"]/100-sc["d2035"]/100)*min((y-2035)/15,1)

rev_erosion = np.array([rev_base*dloss(ng_s,t) for t in range(n)]) if t_demand else np.zeros(n)

def ebitda_adj_fn(tr):
    return np.array([ebitda_in*(1-dloss(ng_s,t))-tr["imp_comm"][t] for t in range(n)])

ebitda_adj45 = ebitda_adj_fn(tr45)
ebitda_adj85 = ebitda_adj_fn(tr85)

# ── Asset-level Physical Risk (EAL) ──────────────────────────────────────────
def asset_eal(df, rcp_key, yrs):
    """
    EAL_asset = AssetValue × BaseEAL_pct × RiskWeight × RCP_multiplier(t)
    Only include assets whose hazard type matches active hazard checkboxes.
    """
    total = np.zeros(yrs)
    breakdown = {}
    hazard_map = {
        "Wildfire":            h_wildfire,
        "Landslide/Flood":     h_flood,
        "Heatwave/Permafrost": h_heat or h_permafrost,
        "Water Level":         h_flood,
        "Hurricane":           h_hurricane,
        "Permafrost Thaw":     h_permafrost,
        "Flooding":            h_flood,
    }
    for _, row in df.iterrows():
        hazard_active = hazard_map.get(row["Hazard"], True)
        if not hazard_active:
            breakdown[row["Asset"]] = np.zeros(yrs)
            continue
        series = np.array([
            row["Value_CAD_B"] * row["BaseEAL_pct"] * row["Risk_Weight"]
            * rcp_phys_mult(rcp_key, t, yrs)
            for t in range(yrs)
        ])
        total += series
        breakdown[row["Asset"]] = series
    return total, breakdown

eal45, eal_bd45 = asset_eal(sel_df, "rcp45", n)
eal85, eal_bd85 = asset_eal(sel_df, "rcp85", n)

# ── Stranded asset risk (at-risk book value under high physical scenario) ─────
def stranded_risk(df, rcp_key, yrs):
    """Fraction of asset value at risk of stranding — grows with RCP intensity."""
    mult = rcp_phys_mult(rcp_key, yrs-1, yrs)
    at_risk = sum(row["Value_CAD_B"] * row["Risk_Weight"] * 0.05 * (mult-1)
                  for _,row in df.iterrows())
    return at_risk if t_stranded else 0

stranded45 = stranded_risk(sel_df,"rcp45",n)
stranded85 = stranded_risk(sel_df,"rcp85",n)

# ── DCF Climate VaR ──────────────────────────────────────────────────────────
disc   = np.array([(1/(1+wacc/100))**t for t in range(n)])
base_fcf = np.full(n, ebitda_in)

def climate_var_dcf(ebitda_arr, eal_arr, stranded_val, tr, pass_thru_pct):
    """
    Loss_Total = (Emissions × ΔCarbonPrice × (1−PassThrough))
               + Σ(AssetValue × RiskWeight × Damage%)
    Climate_VaR = Loss_Total / MarketCap
    """
    adj_fcf = ebitda_arr - eal_arr*(1-pass_thru_pct/100)
    b_npv   = float(np.sum(base_fcf * disc))
    a_npv   = float(np.sum(adj_fcf  * disc))
    cvar    = b_npv - a_npv + stranded_val
    cvar_pct= cvar/b_npv*100 if b_npv else 0
    cvar_mktcap = cvar/mkt["mktcap_cad_bn"]*100
    pv_phy  = float(np.sum(eal_arr*(1-pass_thru_pct/100)*disc))
    pv_tran = float(np.sum(tr["imp_comm"]*disc))
    pv_dem  = float(np.sum(rev_erosion*(TCE["ebitda_margin_pct"]/100)*disc))
    return dict(b_npv=b_npv, a_npv=a_npv, cvar=cvar, cvar_pct=cvar_pct,
                cvar_mktcap=cvar_mktcap, pv_phy=pv_phy, pv_tran=pv_tran,
                pv_dem=pv_dem, adj_fcf=adj_fcf)

cv45 = climate_var_dcf(ebitda_adj45, eal45, stranded45, tr45, pass_through)
cv85 = climate_var_dcf(ebitda_adj85, eal85, stranded85, tr85, pass_through)

# Primary displayed scenario
show45 = scenario_mode != "RCP 8.5 Only"
show85 = scenario_mode != "RCP 4.5 Only"
cv_primary = cv85 if scenario_mode == "RCP 8.5 Only" else cv45

rl = "HIGH" if cv_primary["cvar_pct"]>25 else ("MED" if cv_primary["cvar_pct"]>10 else "LOW")
rc = {"HIGH":"b-hi","MED":"b-md","LOW":"b-lo"}[rl]
rn = {"HIGH":"High Risk ▲","MED":"Medium Risk ◆","LOW":"Low Risk ●"}[rl]
e2030 = e_base_in*(1-r_comm)**max(2030-start_yr,0)

# ══════════════════════════════════════════════════════════════════════════════
#  HERO BANNER
# ══════════════════════════════════════════════════════════════════════════════
live_tag = "hlive" if mkt["live"] else "htag"
st.markdown(f"""
<div class="hero">
  <h1>🛢️ TC Energy — Climate VaR Stress Test <span style="font-size:.9rem;font-weight:400;color:#475569">v3.0</span></h1>
  <sub>Asset-Level Physical Risk Mapping · Emission Path Differential · RCP 4.5/8.5 Trade-off · TCFD-aligned DCF<br>
  93,700 km Pipeline Network · Canada · United States · Mexico</sub>
  <div class="htags">
    <span class="{live_tag}">📊 1 USD = {FX:.4f} CAD {'(Live)' if mkt['live'] else '(Fallback)'}</span>
    <span class="htag">🏗 {len(selected_assets)} Assets Selected  |  CAD ${sel_df['Value_CAD_B'].sum():.1f}B</span>
    <span class="htag">📅 {start_yr} – {end_yr}  ({horizon}yr horizon)</span>
    <span class="htag">{'⚡ Side-by-Side' if 'Side' in scenario_mode else scenario_mode}</span>
    <span class="htag">NGFS: {ngfs_sel}</span>
    <span class="htag">r = {r_comm*100:.2f}%/yr → −{tgt_pct}% by 2030</span>
    <span class="htag">Mkt Cap CAD ${mkt['mktcap_cad_bn']:.1f}B</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TOP METRICS BAR
# ══════════════════════════════════════════════════════════════════════════════
m1,m2,m3,m4,m5,m6 = st.columns(6)
with m1:
    st.markdown(f"""<div class="kpi"><div class="kpi-lbl">Market Cap (Live)</div>
      <div class="kpi-val inf">CAD ${mkt['mktcap_cad_bn']:.1f}B</div>
      <div class="kpi-sub inf">TRP ~${mkt['trp_price']:.2f} / share</div>
    </div>""", unsafe_allow_html=True)
with m2:
    total_scope12 = TCE["scope1_mt"] + TCE["scope2_mt"]
    st.markdown(f"""<div class="kpi"><div class="kpi-lbl">Total Scope 1+2</div>
      <div class="kpi-val warn">{total_scope12:.1f} Mt</div>
      <div class="kpi-sub warn">CO₂e / yr  (2024E)</div>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="kpi"><div class="kpi-lbl">Climate VaR (Primary)</div>
      <div class="kpi-val neg">CAD ${cv_primary['cvar']:.1f}B</div>
      <div class="kpi-sub neg">{cv_primary['cvar_pct']:.1f}% of NPV
        &nbsp;<span class="badge {rc}">{rn}</span></div>
    </div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="kpi"><div class="kpi-lbl">VaR / Market Cap</div>
      <div class="kpi-val neg">{cv_primary['cvar_mktcap']:.1f}%</div>
      <div class="kpi-sub neg">Loss_{'{Total}'} / Mkt Cap formula</div>
    </div>""", unsafe_allow_html=True)
with m5:
    st.markdown(f"""<div class="kpi"><div class="kpi-lbl">Portfolio Asset Value</div>
      <div class="kpi-val inf">CAD ${sel_df['Value_CAD_B'].sum():.1f}B</div>
      <div class="kpi-sub inf">{len(selected_assets)} assets selected</div>
    </div>""", unsafe_allow_html=True)
with m6:
    avoid_pv = float(np.sum((tr45["avoided"] if show45 else tr85["avoided"]) * disc))
    st.markdown(f"""<div class="kpi"><div class="kpi-lbl">Avoided Cost PV</div>
      <div class="kpi-val pos">CAD ${avoid_pv:.2f}B</div>
      <div class="kpi-sub pos">Financial value of −{tgt_pct}% target</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════
tMap, tRCP, tTR, tCV, tRpt = st.tabs([
    "🗺️  Asset Risk Map",
    "⚡  RCP 4.5 vs 8.5",
    "🏭  Transition Risk",
    "📊  Climate VaR",
    "📋  Full Report",
])

# ════════════════════════════════════════════════════════════════
#  TAB 1 — ASSET RISK MAP
# ════════════════════════════════════════════════════════════════
with tMap:
    st.markdown('<div class="sec">Asset-Level Physical Risk Map — TC Energy Core Infrastructure</div>', unsafe_allow_html=True)

    rcp_for_map = "rcp85" if scenario_mode == "RCP 8.5 Only" else "rcp45"

    col_map, col_tbl = st.columns([3,2])
    with col_map:
        # Build bubble map
        map_df = ASSETS_DF.copy()
        map_df["eal_terminal"] = [
            row["Value_CAD_B"] * row["BaseEAL_pct"] * row["Risk_Weight"]
            * rcp_phys_mult(rcp_for_map, n-1, n)
            for _, row in map_df.iterrows()
        ]
        map_df["selected"] = map_df["Asset"].isin(selected_assets)
        map_df["opacity"]  = map_df["selected"].map({True:0.9, False:0.35})
        map_df["border"]   = map_df["selected"].map({True:2.5, False:0.5})

        color_map = {
            "Gas Pipeline":"#3b82f6","Oil Pipeline":"#f59e0b","Nuclear Power":"#22c55e",
            "Marine Pipeline":"#8b5cf6"
        }
        risk_color = {"Wildfire":"#ef4444","Landslide/Flood":"#3b82f6","Heatwave/Permafrost":"#f59e0b",
                      "Water Level":"#22c55e","Hurricane":"#8b5cf6","Permafrost Thaw":"#f59e0b",
                      "Flooding":"#3b82f6"}

        fig_map = go.Figure()
        for cat, grp in map_df.groupby("Category"):
            col = color_map.get(cat,"#94a3b8")
            fig_map.add_trace(go.Scattergeo(
                lat=grp["Lat"], lon=grp["Lon"],
                mode="markers+text",
                marker=dict(
                    size=grp["Value_CAD_B"].values * 2.2 + 8,
                    color=[risk_color.get(h,"#94a3b8") for h in grp["Hazard"]],
                    opacity=grp["opacity"].values,
                    line=dict(color="white", width=grp["border"].values),
                ),
                text=grp["Asset"],
                textposition="top center",
                textfont=dict(size=9, color="#0f172a"),
                name=cat,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Value: CAD $%{customdata[0]:.1f}B<br>"
                    "Hazard: %{customdata[1]}<br>"
                    "Risk Weight: %{customdata[2]}<br>"
                    "Terminal EAL: $%{customdata[3]:.3f}B/yr<extra></extra>"
                ),
                customdata=grp[["Value_CAD_B","Hazard","Risk_Weight","eal_terminal"]].values,
            ))

        fig_map.update_layout(
            geo=dict(
                scope="north america",
                showland=True, landcolor="#f1f5f9",
                showocean=True, oceancolor="#dbeafe",
                showlakes=True, lakecolor="#bfdbfe",
                showrivers=True, rivercolor="#93c5fd",
                showcountries=True, countrycolor="#cbd5e1",
                showsubunits=True, subunitcolor="#e2e8f0",
                center=dict(lat=48, lon=-100),
                projection_scale=2.5,
                lataxis=dict(range=[15,65]),
                lonaxis=dict(range=[-140,-60]),
            ),
            height=480,
            margin=dict(t=10,b=0,l=0,r=0),
            legend=dict(x=0.01,y=0.98,bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="#e2e8f0",borderwidth=1,font=dict(size=11)),
            paper_bgcolor="rgba(0,0,0,0)",
            title=dict(text=f"Bubble size = Asset value · Colour = Primary hazard type · Opacity = {'Selected' if True else 'Unselected'}",
                       font=dict(size=11,color="#64748b"),x=0.01,y=0.02)
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_tbl:
        st.markdown("**Selected Asset Portfolio — Physical Risk Profile**")
        disp = sel_df[["Asset","Category","Value_CAD_B","Hazard","Risk_Weight","PassThru_pct"]].copy()
        disp.columns = ["Asset","Type","Value $B","Primary Hazard","Risk Wt.","Pass-Thru %"]
        disp["Terminal EAL $B"] = [
            f"{row['Value_CAD_B']*row['BaseEAL_pct']*row['Risk_Weight']*rcp_phys_mult(rcp_for_map,n-1,n):.3f}"
            for _,row in sel_df.iterrows()
        ]
        st.dataframe(disp, use_container_width=True, hide_index=True)

        # Risk heatmap by asset
        st.markdown("**Risk Weight × Hazard Intensity Heat Map**")
        heat_assets = sel_df["Asset"].tolist()
        heat_years  = list(range(start_yr, end_yr+1, max(horizon//5,1)))
        heat_z = []
        for _,row in sel_df.iterrows():
            r_row=[]
            for y in heat_years:
                t = y-start_yr
                eal = row["Value_CAD_B"]*row["BaseEAL_pct"]*row["Risk_Weight"]*rcp_phys_mult(rcp_for_map,t,n)
                r_row.append(round(eal*1000,1))  # CAD $M
            heat_z.append(r_row)

        fig_heat = go.Figure(go.Heatmap(
            z=heat_z, x=[str(y) for y in heat_years], y=heat_assets,
            colorscale=[[0,"#f0fdf4"],[0.3,"#fef9c3"],[0.6,"#fed7aa"],[0.85,"#fca5a5"],[1,"#7f1d1d"]],
            text=[[f"${v}M" for v in row] for row in heat_z],
            texttemplate="%{text}", textfont=dict(size=10),
            showscale=True, colorbar=dict(title="EAL CAD $M",thickness=12),
        ))
        fig_heat.update_layout(height=260, margin=dict(t=10,b=20,l=10,r=60),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_heat, use_container_width=True)

    # EAL time series all assets stacked
    st.markdown(f"**Portfolio EAL Time Series — {'RCP 4.5' if rcp_for_map=='rcp45' else 'RCP 8.5'} (CAD $B/yr)**")
    eal_bd = eal_bd45 if rcp_for_map=="rcp45" else eal_bd85
    colors_list = ["#3b82f6","#ef4444","#f59e0b","#22c55e","#8b5cf6","#06b6d4","#f97316","#84cc16","#ec4899"]
    figEAL = go.Figure()
    for i,(a_name, series) in enumerate(eal_bd.items()):
        figEAL.add_trace(go.Scatter(x=yr_range, y=series,
            name=a_name, stackgroup="one", line=dict(width=0.5),
            fillcolor=colors_list[i % len(colors_list)]))
    figEAL.update_layout(height=280, template="plotly_white",
        yaxis_title="EAL (CAD $B/yr)", xaxis_title="Year",
        legend=dict(orientation="h",y=-0.3,font=dict(size=10)),
        margin=dict(t=10,b=80,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figEAL, use_container_width=True)

    st.markdown(f"""
    <div class="note"><b>Asset-Level Model:</b>
    EAL_asset = AssetValue × BaseEAL% × RiskWeight × RCP_multiplier(t).
    Bubble radius proportional to CAD book value. Colour encodes primary climate hazard.
    Pass-through % reflects regulated tariff recovery capacity per asset.
    Terminal portfolio EAL ({end_yr}): <b>CAD ${(eal45 if rcp_for_map=='rcp45' else eal85)[-1]:.3f}B/yr</b>.
    </div>
    <div class="src">TC Energy 2024 SR (asset locations/values) · Swiss Re NatCat · IPCC AR6 WG2
    · NRCan Climate Infrastructure Risk Atlas</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 2 — RCP 4.5 vs 8.5 TRADE-OFF
# ════════════════════════════════════════════════════════════════
with tRCP:
    st.markdown('<div class="sec">RCP 4.5 vs RCP 8.5 — Risk Trade-off Analysis (2026–{})'.format(end_yr) + '</div>', unsafe_allow_html=True)

    # Trade-off explainer cards
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(f"""<div class="sc45">
          <div class="sc-title" style="color:#1d4ed8">🟦 RCP 4.5 — High Transition · Medium Physical</div>
          <table style="width:100%;font-size:.82rem;border-collapse:collapse">
            <tr><td style="color:#475569;padding:3px 0">Policy / Carbon Price</td>
                <td style="font-weight:600;color:#dc2626">HIGH (aggressive)</td></tr>
            <tr><td style="color:#475569;padding:3px 0">2030 Carbon Price</td>
                <td style="font-weight:600">{carbon_price_2030} → ${interp(CARBON_PRICE_RCP45,end_yr):.0f}/t ({end_yr})</td></tr>
            <tr><td style="color:#475569;padding:3px 0">Physical Hazard Intensity</td>
                <td style="font-weight:600;color:#d97706">MEDIUM ({rcp_phys_mult('rcp45',n-1,n):.2f}× base)</td></tr>
            <tr><td style="color:#475569;padding:3px 0">Primary Financial Impact</td>
                <td style="font-weight:600">OPEX pressure · EBITDA margin erosion</td></tr>
            <tr><td style="color:#475569;padding:3px 0">Climate VaR</td>
                <td style="font-weight:600;color:#dc2626">CAD ${cv45['cvar']:.1f}B ({cv45['cvar_pct']:.1f}% NPV)</td></tr>
            <tr><td style="color:#475569;padding:3px 0">VaR / Mkt Cap</td>
                <td style="font-weight:600">{cv45['cvar_mktcap']:.1f}%</td></tr>
          </table>
        </div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div class="sc85">
          <div class="sc-title" style="color:#dc2626">🟥 RCP 8.5 — Low Transition · Extreme Physical</div>
          <table style="width:100%;font-size:.82rem;border-collapse:collapse">
            <tr><td style="color:#475569;padding:3px 0">Policy / Carbon Price</td>
                <td style="font-weight:600;color:#16a34a">LOW (slow policy)</td></tr>
            <tr><td style="color:#475569;padding:3px 0">2030 Carbon Price</td>
                <td style="font-weight:600">{CARBON_PRICE_RCP85[2030]} → ${interp(CARBON_PRICE_RCP85,end_yr):.0f}/t ({end_yr})</td></tr>
            <tr><td style="color:#475569;padding:3px 0">Physical Hazard Intensity</td>
                <td style="font-weight:600;color:#dc2626">EXTREME ({rcp_phys_mult('rcp85',n-1,n):.2f}× base)</td></tr>
            <tr><td style="color:#475569;padding:3px 0">Primary Financial Impact</td>
                <td style="font-weight:600">Asset impairment · CAPEX repair surge</td></tr>
            <tr><td style="color:#475569;padding:3px 0">Climate VaR</td>
                <td style="font-weight:600;color:#dc2626">CAD ${cv85['cvar']:.1f}B ({cv85['cvar_pct']:.1f}% NPV)</td></tr>
            <tr><td style="color:#475569;padding:3px 0">VaR / Mkt Cap</td>
                <td style="font-weight:600">{cv85['cvar_mktcap']:.1f}%</td></tr>
          </table>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Side-by-side EAL ─────────────────────────────────────────
    figRCP = make_subplots(rows=1,cols=2,subplot_titles=[
        f"Physical EAL — RCP 4.5 (CAD $B/yr)",
        f"Physical EAL — RCP 8.5 (CAD $B/yr)"
    ])
    figRCP.add_trace(go.Scatter(x=yr_range,y=eal45,name="EAL RCP 4.5",
        line=dict(color="#3b82f6",width=2.5),fill="tozeroy",fillcolor="rgba(59,130,246,0.08)"),row=1,col=1)
    figRCP.add_trace(go.Scatter(x=yr_range,y=eal85,name="EAL RCP 8.5",
        line=dict(color="#ef4444",width=2.5),fill="tozeroy",fillcolor="rgba(239,68,68,0.08)"),row=1,col=2)
    figRCP.update_layout(height=300,template="plotly_white",showlegend=False,
        margin=dict(t=40,b=20,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figRCP, use_container_width=True)

    # ── Carbon price divergence ───────────────────────────────────
    figCP = go.Figure()
    figCP.add_trace(go.Scatter(x=yr_range,y=[interp(CARBON_PRICE_RCP45,y) for y in yr_range],
        name="Carbon Price — RCP 4.5 (High Transition)",
        line=dict(color="#3b82f6",width=2.5),fill="tozeroy",fillcolor="rgba(59,130,246,0.07)"))
    figCP.add_trace(go.Scatter(x=yr_range,y=[interp(CARBON_PRICE_RCP85,y) for y in yr_range],
        name="Carbon Price — RCP 8.5 (Slow Policy)",
        line=dict(color="#ef4444",width=2,dash="dash"),fill="tozeroy",fillcolor="rgba(239,68,68,0.05)"))
    figCP.add_vline(x=2030,line_width=1,line_dash="dot",line_color="#94a3b8",
        annotation_text=f"2030: ${carbon_price_2030}/t (RCP 4.5) vs ${CARBON_PRICE_RCP85[2030]}/t (RCP 8.5)",
        annotation_position="top right",annotation_font_size=10)
    figCP.update_layout(title="Carbon Price Path Divergence — Key Driver of Scenario Risk Trade-off",
        height=280,template="plotly_white",yaxis_title="CAD $/t CO₂e",
        legend=dict(orientation="h",y=-0.22),margin=dict(t=40,b=60,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figCP, use_container_width=True)

    # ── Radar chart: risk dimensions ─────────────────────────────
    categories = ["Carbon Tax\nExposure","Physical\nEAL","Demand\nErosion",
                  "Asset\nImpairment","EBITDA\nErosion"]
    def normalise(v, vmax): return min(v/vmax*10, 10)
    vmax_ct  = max(float(np.sum(tr45["imp_comm"])), float(np.sum(tr85["imp_comm"])), 1)
    vmax_eal = max(float(np.sum(eal45)), float(np.sum(eal85)), 1)
    vmax_dem = float(np.sum(rev_erosion)) + 0.001
    vals45 = [normalise(float(np.sum(tr45["ct_comm"])),vmax_ct),
              normalise(float(np.sum(eal45)),vmax_eal),
              normalise(float(np.sum(rev_erosion))*0.6,vmax_dem*0.8),
              normalise(stranded45,max(stranded45,stranded85,0.001)),
              normalise(float(np.sum(tr45["imp_comm"])),vmax_ct)]
    vals85 = [normalise(float(np.sum(tr85["ct_comm"])),vmax_ct),
              normalise(float(np.sum(eal85)),vmax_eal),
              normalise(float(np.sum(rev_erosion))*0.3,vmax_dem*0.8),
              normalise(stranded85,max(stranded45,stranded85,0.001)),
              normalise(float(np.sum(tr85["imp_comm"])),vmax_ct)]
    figR = go.Figure()
    for vals, col, name in [(vals45,"#3b82f6","RCP 4.5"),(vals85,"#ef4444","RCP 8.5")]:
        figR.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=categories+[categories[0]],
            fill="toself", name=name,
            line=dict(color=col,width=2), fillcolor=col.replace("#","rgba(").replace(
                "rgba(","rgba(") + ",0.12)" if False else col+"26"))
    figR.update_layout(title="Risk Dimension Radar — RCP 4.5 vs RCP 8.5 (score 0–10)",
        polar=dict(radialaxis=dict(visible=True,range=[0,10])),
        height=360, showlegend=True,
        legend=dict(orientation="h",y=-0.08),
        margin=dict(t=50,b=40,l=20,r=20),
        paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figR, use_container_width=True)

    st.markdown("""
    <div class="note"><b>Risk Trade-off Insight:</b>
    Under RCP 4.5, aggressive carbon policy drives transition risk —
    higher carbon taxes compress EBITDA margins and create strong incentives for decarbonisation.
    Under RCP 8.5, slow policy reduces carbon cost exposure but allows physical climate damage to
    compound dramatically, ultimately causing greater asset impairment and emergency CAPEX.
    TC Energy's regulated pipeline model (take-or-pay) provides significant insulation from transition
    risk through cost pass-through, but physical damage to remote pipeline corridors is harder to recover.
    </div>
    <div class="src">IPCC AR6 · NGFS Phase 4 · TC Energy 2024 Sustainability Report · Swiss Re NatCat 2024</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 3 — TRANSITION RISK
# ════════════════════════════════════════════════════════════════
with tTR:
    st.markdown('<div class="sec">Module B · Transition Risk — Emission Path Differential & Net Financial Impact</div>', unsafe_allow_html=True)

    # Formula display
    cf1,cf2,cf3 = st.columns(3)
    with cf1:
        st.markdown(f"""<div class="fbox" style="border-left-color:#f59e0b">
<span style="color:#fbbf24">A. Emission Trajectory</span>

E_year = E_base × (1 − r)^(yr−{start_yr})

r = 1−(1−{tgt_pct}%)<sup>1/6</sup> = <b style="color:#4ade80">{r_comm*100:.3f}%/yr</b>

E_{2030} = {e_base_in}×(1−{r_comm:.4f})^{max(2030-start_yr,0)}
     = <b style="color:#4ade80">{e2030:.2f} Mt CO₂e</b>
</div>""", unsafe_allow_html=True)
    with cf2:
        st.markdown(f"""<div class="fbox" style="border-left-color:#ef4444">
<span style="color:#fca5a5">B. Net Financial Impact</span>

Impact_yr =
  (E_yr × CarbonPrice_yr)
  + CAPEX_abate
  − ITC_{itc_rate}%
  + Offset_purch

<span style="color:#64748b">CAPEX = ΔE × ${capex_per_mt:.0f}M/Mt
ITC   = {itc_rate}% × CAPEX
Offsets= {offset_pct}% residual × mkt price</span>
</div>""", unsafe_allow_html=True)
    with cf3:
        cum_avoid = float(np.sum(tr45["avoided"] if show45 else tr85["avoided"]))
        net_capex = float(np.sum(tr45["capex_c"]-tr45["itc_c"]))
        roi = cum_avoid/net_capex if net_capex>0 else 0
        st.markdown(f"""<div class="fbox" style="border-left-color:#22c55e">
<span style="color:#4ade80">C. Path Differential</span>

ΔImpact_yr = Impact_BAU − Impact_Comm

<span style="color:#64748b">Cumulative:
  CAD <b style="color:#4ade80">${cum_avoid:.2f}B</b>

PV (@{wacc}% WACC):
  CAD <b style="color:#4ade80">${avoid_pv:.2f}B</b>

Abatement ROI:
  <b style="color:#4ade80">{roi:.1f}×</b></span>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Emission trajectories
    st.markdown("**Emission Trajectory Pathways (Mt CO₂e/yr)**")
    figE = go.Figure()
    hist_x = list(GHG_HIST.keys())
    hist_y = list(GHG_HIST.values())
    figE.add_trace(go.Scatter(x=hist_x,y=hist_y,name="Historical Reported",
        mode="markers+lines",marker=dict(size=7,color="#1e40af"),line=dict(color="#1e40af",width=2.5)))
    for e_arr,col,dash,lname in [
        (E_bau,"#ef4444","dash","BAU (r=0)"),
        (E_comm,"#f59e0b","solid",f"Committed r={r_comm*100:.2f}%/yr → −{tgt_pct}% by 2030"),
        (E_acc,"#22c55e","dot",f"Accelerated r={r_accel*100:.2f}%/yr"),
    ]:
        figE.add_trace(go.Scatter(x=yr_range,y=e_arr,name=lname,
            line=dict(color=col,width=2.5 if col=="#f59e0b" else 2,dash=dash)))
    figE.add_annotation(x=2030,y=e2030,text=f"⬤ {e2030:.1f} Mt<br>{2030} Target",
        showarrow=True,arrowhead=2,arrowcolor="#f59e0b",font=dict(size=10,color="#92400e"),
        bgcolor="#fef9c3",bordercolor="#fde68a")
    figE.add_vline(x=2030,line_width=1,line_dash="dot",line_color="#94a3b8")
    figE.update_layout(height=340,template="plotly_white",xaxis_title="Year",yaxis_title="Mt CO₂e/yr",
        legend=dict(orientation="h",y=-0.22),margin=dict(t=10,b=70,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figE, use_container_width=True)

    # Net impact decomposition
    tr_show = tr45 if show45 else tr85
    cp_lbl  = "RCP 4.5" if show45 else "RCP 8.5"
    st.markdown(f"**Net Financial Impact Decomposition — {cp_lbl} Committed Pathway (CAD $B/yr)**")
    figNFI = make_subplots(specs=[[{"secondary_y":True}]])
    figNFI.add_trace(go.Bar(x=yr_range,y=tr_show["ct_comm"],name="Carbon Tax",marker_color="#f87171",opacity=0.85),secondary_y=False)
    figNFI.add_trace(go.Bar(x=yr_range,y=tr_show["capex_c"],name="Abatement CAPEX",marker_color="#fb923c",opacity=0.85),secondary_y=False)
    figNFI.add_trace(go.Bar(x=yr_range,y=-tr_show["itc_c"],name=f"ITC −{itc_rate}%",marker_color="#4ade80",opacity=0.85),secondary_y=False)
    figNFI.add_trace(go.Bar(x=yr_range,y=tr_show["oc_c"],name="Offset Purchases",marker_color="#c084fc",opacity=0.85),secondary_y=False)
    figNFI.add_trace(go.Scatter(x=yr_range,y=tr_show["imp_comm"],name="Net Impact",line=dict(color="#0f172a",width=2.5)),secondary_y=True)
    figNFI.add_trace(go.Scatter(x=yr_range,y=tr_show["imp_bau"],name="BAU (ref.)",line=dict(color="#ef4444",width=1.5,dash="dash")),secondary_y=True)
    figNFI.update_layout(height=330,template="plotly_white",barmode="relative",
        legend=dict(orientation="h",y=-0.28),margin=dict(t=10,b=80,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    figNFI.update_yaxes(title_text="Components (CAD $B/yr)",secondary_y=False)
    figNFI.update_yaxes(title_text="Net Total (CAD $B/yr)",secondary_y=True)
    st.plotly_chart(figNFI, use_container_width=True)

    # Path differential
    st.markdown("**ΔImpact — Annual Avoided Cost vs BAU (CAD $B/yr)**")
    avoided = tr_show["avoided"]
    figD = make_subplots(specs=[[{"secondary_y":True}]])
    figD.add_trace(go.Bar(x=yr_range,y=avoided,name="Committed vs BAU",
        marker_color=["#22c55e" if v>=0 else "#ef4444" for v in avoided],opacity=0.8),secondary_y=False)
    figD.add_trace(go.Scatter(x=yr_range,y=np.cumsum(avoided),name="Cumulative Savings",
        line=dict(color="#0ea5e9",width=2.5)),secondary_y=True)
    figD.update_layout(height=280,template="plotly_white",barmode="group",
        legend=dict(orientation="h",y=-0.25),margin=dict(t=10,b=70,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    figD.update_yaxes(title_text="Annual ΔImpact (CAD $B/yr)",secondary_y=False)
    figD.update_yaxes(title_text="Cumulative (CAD $B)",secondary_y=True)
    st.plotly_chart(figD, use_container_width=True)

    # Avoided cost cards
    a1,a2,a3 = st.columns(3)
    with a1:
        st.markdown(f"""<div class="avoided">
          <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;color:#15803d;letter-spacing:.07em;margin-bottom:3px">Cumulative Avoided vs BAU</div>
          <div style="font-size:1.5rem;font-weight:700;color:#15803d">CAD ${cum_avoid:.2f}B</div>
          <div style="font-size:.76rem;color:#166534;margin-top:3px">{start_yr}–{end_yr}</div>
        </div>""", unsafe_allow_html=True)
    with a2:
        st.markdown(f"""<div class="avoided">
          <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;color:#92400e;letter-spacing:.07em;margin-bottom:3px">Net Abatement Cost</div>
          <div style="font-size:1.5rem;font-weight:700;color:#d97706">CAD ${net_capex:.2f}B</div>
          <div style="font-size:.76rem;color:#92400e;margin-top:3px">CAPEX − {itc_rate}% ITC benefit</div>
        </div>""", unsafe_allow_html=True)
    with a3:
        st.markdown(f"""<div class="avoided">
          <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;color:#15803d;letter-spacing:.07em;margin-bottom:3px">Abatement ROI</div>
          <div style="font-size:1.5rem;font-weight:700;color:#15803d">{roi:.1f}×</div>
          <div style="font-size:.76rem;color:#166534;margin-top:3px">Avoided cost ÷ Net CAPEX</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="src">Canada Budget 2024 — Federal Clean Technology ITC (30%) ·
    TC Energy 2024 SR (ESG CAPEX ~$870M) · Environment Canada Federal Carbon Pricing ·
    NGFS Phase 4 · Canada Carbon Offset Credit System (COCES)</div>
    """, unsafe_allow_html=True)

    with st.expander("📄 Full Transition Risk Data Table"):
        tr_disp = tr45 if show45 else tr85
        df_t = pd.DataFrame({
            "Year": yr_range,
            "Carbon Price CAD$/t": [round(interp(CARBON_PRICE_RCP45 if show45 else CARBON_PRICE_RCP85,y),0) for y in yr_range],
            "E_BAU (Mt)": E_bau.round(3),"E_Committed (Mt)": E_comm.round(3),
            "Carbon Tax Committed ($B)": tr_disp["ct_comm"].round(3),
            "CAPEX ($B)": tr_disp["capex_c"].round(3), "ITC ($B)": tr_disp["itc_c"].round(3),
            "Offset ($B)": tr_disp["oc_c"].round(3),
            "Net Impact ($B)": tr_disp["imp_comm"].round(3),
            "BAU Impact ($B)": tr_disp["imp_bau"].round(3),
            "ΔImpact Avoided ($B)": tr_disp["avoided"].round(3),
            "Cumul. Avoided ($B)": np.cumsum(tr_disp["avoided"]).round(3),
        })
        st.dataframe(df_t, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
#  TAB 4 — CLIMATE VAR
# ════════════════════════════════════════════════════════════════
with tCV:
    st.markdown('<div class="sec">Module C · Climate VaR — DCF Waterfall, Sensitivity & Formula Decomposition</div>', unsafe_allow_html=True)

    st.markdown(f"""<div class="fbox" style="border-left-color:#8b5cf6;font-size:.78rem">
<span style="color:#c4b5fd">Climate VaR Master Formula (TCFD-aligned)</span>

<b>Loss_Total</b> = (Emissions × ΔCarbonPrice × (1 − PassThrough%))
            + Σ(AssetValue × RiskWeight × Damage%)

<b>Climate_VaR</b> = Loss_Total / MarketCap

<span style="color:#64748b">PassThrough = {pass_through}%  (regulated tariff recovery)
Total Asset Value = CAD ${sel_df['Value_CAD_B'].sum():.1f}B  ({len(selected_assets)} assets)
Market Cap = CAD ${mkt['mktcap_cad_bn']:.1f}B  (live: {'yes' if mkt['live'] else 'fallback'})
WACC = {wacc}%  |  Horizon = {start_yr}–{end_yr}</span>
</div>""", unsafe_allow_html=True)

    # Waterfall side by side
    wf1, wf2 = st.columns(2) if "Side" in scenario_mode else (st.columns([1,1]) if show45 else st.columns([1,1]))
    def waterfall_fig(cv, title, color):
        wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute","relative","relative","relative","total"],
            x=["Base NPV","Physical EAL\n(net pass-thru PV)","Net Transition\nPV","Demand\nErosion PV","Climate-adj.\nNPV"],
            y=[cv["b_npv"],-cv["pv_phy"],-cv["pv_tran"],-cv["pv_dem"],cv["a_npv"]],
            text=[f"${v:.1f}B" for v in [cv["b_npv"],-cv["pv_phy"],-cv["pv_tran"],-cv["pv_dem"],cv["a_npv"]]],
            textposition="outside",textfont=dict(size=10),
            decreasing=dict(marker_color="#ef4444"),increasing=dict(marker_color="#22c55e"),
            totals=dict(marker_color=color),
            connector=dict(line=dict(color="#cbd5e1",width=1.5,dash="dot"))))
        wf.update_layout(title=dict(text=title,font=dict(size=12)),height=380,template="plotly_white",
            yaxis_title="CAD $B",margin=dict(t=40,b=10,l=10,r=10),
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        return wf

    with wf1:
        if show45:
            st.plotly_chart(waterfall_fig(cv45,f"RCP 4.5 — WACC {wacc}% (CAD $B)","#3b82f6"), use_container_width=True)
    with wf2:
        if show85:
            st.plotly_chart(waterfall_fig(cv85,f"RCP 8.5 — WACC {wacc}% (CAD $B)","#ef4444"), use_container_width=True)

    # Gauge + summary table
    gA, gB = st.columns([1,1])
    with gA:
        cv_show = cv45 if show45 else cv85
        rcp_show_lbl = "RCP 4.5" if show45 else "RCP 8.5"
        figG = go.Figure(go.Indicator(
            mode="gauge+number+delta",value=round(cv_show["cvar_pct"],1),
            number={"suffix":"%","font":{"size":32}},
            delta={"reference":10,"suffix":"%","prefix":"Threshold 10%","increasing":{"color":"#ef4444"}},
            gauge={"axis":{"range":[0,60],"ticksuffix":"%"},
                   "bar":{"color":"#ef4444" if cv_show["cvar_pct"]>25 else ("#f59e0b" if cv_show["cvar_pct"]>10 else "#22c55e")},
                   "steps":[{"range":[0,10],"color":"#f0fdf4"},{"range":[10,25],"color":"#fffbeb"},{"range":[25,60],"color":"#fef2f2"}],
                   "threshold":{"line":{"color":"#dc2626","width":3},"value":25}},
            title={"text":f"Climate VaR / NPV<br>({rcp_show_lbl} primary)","font":{"size":12}}))
        figG.update_layout(height=240,margin=dict(t=20,b=0,l=10,r=10),paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(figG, use_container_width=True)

    with gB:
        def row_html(label, v45, v85, unit=""):
            return f"<tr><td style='color:#64748b;padding:5px 8px'>{label}</td><td style='padding:5px 8px;color:#1d4ed8;font-weight:600'>{v45}{unit}</td><td style='padding:5px 8px;color:#dc2626;font-weight:600'>{v85}{unit}</td></tr>"
        st.markdown(f"""<table class="dt">
          <tr><th>Metric</th><th style="color:#1d4ed8">RCP 4.5</th><th style="color:#dc2626">RCP 8.5</th></tr>
          {row_html("Base NPV", f"${cv45['b_npv']:.1f}B", f"${cv85['b_npv']:.1f}B")}
          {row_html("Physical EAL PV", f"-${cv45['pv_phy']:.2f}B", f"-${cv85['pv_phy']:.2f}B")}
          {row_html("Transition PV", f"-${cv45['pv_tran']:.2f}B", f"-${cv85['pv_tran']:.2f}B")}
          {row_html("Demand Erosion PV", f"-${cv45['pv_dem']:.2f}B", f"-${cv85['pv_dem']:.2f}B")}
          {row_html("Climate-adj. NPV", f"${cv45['a_npv']:.1f}B", f"${cv85['a_npv']:.1f}B")}
          {row_html("Climate VaR", f"${cv45['cvar']:.1f}B ({cv45['cvar_pct']:.1f}%)", f"${cv85['cvar']:.1f}B ({cv85['cvar_pct']:.1f}%)")}
          {row_html("VaR / Mkt Cap", f"{cv45['cvar_mktcap']:.1f}%", f"{cv85['cvar_mktcap']:.1f}%")}
          {row_html("Stranded Risk", f"${stranded45:.2f}B", f"${stranded85:.2f}B")}
        </table>""", unsafe_allow_html=True)

    # Sensitivity heatmap
    st.markdown("**Sensitivity — Climate VaR% vs WACC × 2030 Reduction Target (Primary Scenario)**")
    wacc_rng = [5,6,7,8,9,10,11]; tgt_rng = [10,15,20,25,30,40,50]
    cv_show_key = "rcp45" if show45 else "rcp85"
    cp_show = CARBON_PRICE_RCP45 if show45 else CARBON_PRICE_RCP85
    eal_show = eal45 if show45 else eal85
    heat_z=[]
    for w in wacc_rng:
        row=[]
        for tg in tgt_rng:
            rt=1-(1-tg/100)**(1/6)
            et=emission_path(e_base_in,rt,0.025,n)
            ct=abatement_capex_fn(E_bau,et,capex_per_mt)
            ib,oc=subsidies_fn(ct,itc_rate,et,offset_pct)
            it,_=net_impact_fn(et,ct,ib,oc,cp_show)
            ea=np.array([ebitda_in*(1-dloss(ng_s,t))-it[t] for t in range(n)])
            dis=np.array([(1/(1+w/100))**t for t in range(n)])
            bn=float(np.sum(base_fcf*dis)); an=float(np.sum((ea-eal_show*(1-pass_through/100))*dis))
            row.append(round((bn-an)/bn*100,1) if bn else 0)
        heat_z.append(row)
    figH=go.Figure(go.Heatmap(z=heat_z,x=[f"−{t}%" for t in tgt_rng],y=[f"{w}%" for w in wacc_rng],
        colorscale=[[0,"#f0fdf4"],[0.2,"#fef9c3"],[0.5,"#fed7aa"],[0.75,"#fca5a5"],[1,"#7f1d1d"]],
        text=[[f"{v:.1f}%" for v in row] for row in heat_z],
        texttemplate="%{text}",textfont=dict(size=11),showscale=True,colorbar=dict(title="VaR %",thickness=12)))
    cwi=min(range(len(wacc_rng)),key=lambda i:abs(wacc_rng[i]-wacc))
    cti=min(range(len(tgt_rng)),key=lambda i:abs(tgt_rng[i]-tgt_pct))
    figH.add_shape(type="rect",x0=cti-.5,x1=cti+.5,y0=cwi-.5,y1=cwi+.5,line=dict(color="#0ea5e9",width=3))
    figH.update_layout(height=295,template="plotly_white",xaxis_title="2030 Reduction Target",
        yaxis_title="WACC",margin=dict(t=10,b=20,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figH, use_container_width=True)


# ════════════════════════════════════════════════════════════════
#  TAB 5 — FULL REPORT
# ════════════════════════════════════════════════════════════════
with tRpt:
    st.markdown('<div class="sec">📋 TC Energy — Integrated Climate Risk Stress Test Report (v3.0)</div>', unsafe_allow_html=True)

    st.markdown(f"""
    #### Executive Summary
    TCFD-aligned stress test of **TC Energy Corporation (TSX/NYSE: TRP)** over **{horizon} years ({start_yr}–{end_yr})**.

    **v3.0 Upgrades:** Asset-level physical risk geo-modelling for {len(selected_assets)} assets across
    Canada/US/Mexico · Live USD/CAD FX via yfinance (1 USD = {FX:.4f} CAD) · RCP 4.5 vs 8.5 risk trade-off
    (transition-heavy vs physically-driven) · Loss_Total / MarketCap formula · 4-section professional sidebar.

    **Active:** {'RCP 4.5 + 8.5 Side-by-Side' if 'Side' in scenario_mode else scenario_mode} ·
    {ngfs_sel} NGFS · r = {r_comm*100:.2f}%/yr → E₂₀₃₀ = {e2030:.1f} Mt CO₂e · Pass-Through {pass_through}%
    ---
    """)

    re1,re2,re3,re4 = st.columns(4)
    for col, lbl, body in [
        (re1,"A · Physical Risk",
         f"• Assets: {', '.join(selected_assets[:2])} ...<br>"
         f"• Portfolio value: CAD ${sel_df['Value_CAD_B'].sum():.1f}B<br>"
         f"• Terminal EAL (RCP 4.5): ${eal45[-1]:.3f}B/yr<br>"
         f"• Terminal EAL (RCP 8.5): ${eal85[-1]:.3f}B/yr<br>"
         f"• Stranded risk (8.5): ${stranded85:.2f}B"),
        (re2,"B · Transition Risk",
         f"• E₂₀₃₀ (committed): {e2030:.1f} Mt CO₂e<br>"
         f"• r = {r_comm*100:.2f}%/yr compound rate<br>"
         f"• Net impact (RCP 4.5): ${float(np.sum(tr45['imp_comm'])):.2f}B cumul.<br>"
         f"• Avoided vs BAU: ${cum_avoid:.2f}B cumul.<br>"
         f"• Abatement ROI: {roi:.1f}×"),
        (re3,"C · Climate VaR",
         f"• RCP 4.5 VaR: ${cv45['cvar']:.1f}B ({cv45['cvar_pct']:.1f}%)<br>"
         f"• RCP 8.5 VaR: ${cv85['cvar']:.1f}B ({cv85['cvar_pct']:.1f}%)<br>"
         f"• VaR/Mkt Cap (4.5): {cv45['cvar_mktcap']:.1f}%<br>"
         f"• VaR/Mkt Cap (8.5): {cv85['cvar_mktcap']:.1f}%<br>"
         f"• Risk: <span class='badge {rc}'>{rn}</span>"),
        (re4,"Market Data",
         f"• Live FX: 1 USD = {FX:.4f} CAD<br>"
         f"• TRP Price: ~CAD ${mkt['trp_price']:.2f}<br>"
         f"• Mkt Cap: CAD ${mkt['mktcap_cad_bn']:.1f}B<br>"
         f"• Data: {'Live yfinance' if mkt['live'] else 'Fallback values'}<br>"
         f"• As of: {mkt['ts']}"),
    ]:
        col.markdown(f"""<div class="kpi"><div class="kpi-lbl">{lbl}</div>
          <div style="font-size:.78rem;color:#475569;line-height:1.9;margin-top:.4rem">{body}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>**6-Scenario Matrix**")
    def full_var(rcp_k,ngfs_k):
        cp_s = CARBON_PRICE_RCP45 if rcp_k=="rcp45" else CARBON_PRICE_RCP85
        el_f = eal45 if rcp_k=="rcp45" else eal85
        tr_f = run_transition(cp_s)
        ea = np.array([ebitda_in*(1-dloss(NGFS[ngfs_k],t))-tr_f["imp_comm"][t] for t in range(n)])
        dis = np.array([(1/(1+wacc/100))**t for t in range(n)])
        bn=float(np.sum(base_fcf*dis)); an=float(np.sum((ea-el_f*(1-pass_through/100))*dis))
        cv=bn-an; cvp=cv/bn*100 if bn else 0
        rlv="🔴 High" if cvp>25 else ("🟡 Medium" if cvp>10 else "🟢 Low")
        return round(bn,1),round(an,1),round(cv,1),round(cvp,1),rlv
    mat=[]
    for rk,rl2 in [("rcp45","RCP 4.5"),("rcp85","RCP 8.5")]:
        for nk in NGFS:
            bn,an,cv2,cvp2,rlv2=full_var(rk,nk)
            mat.append({"Scenario":f"{rl2} · {nk}","Base NPV($B)":bn,"Adj.NPV($B)":an,
                        "Climate VaR($B)":cv2,"VaR/NPV(%)":cvp2,"Risk":rlv2})
    st.dataframe(pd.DataFrame(mat),use_container_width=True,hide_index=True)

    st.markdown("#### Asset Portfolio Summary")
    asum = sel_df[["Asset","Category","Country","Value_CAD_B","Hazard","Risk_Weight","PassThru_pct","Scope1_Mt"]].copy()
    asum.columns = ["Asset","Type","Country","Value $B","Hazard","Risk Wt","Pass-Thru%","Scope1 Mt"]
    st.dataframe(asum, use_container_width=True, hide_index=True)

    st.markdown("#### Formula & Assumptions")
    st.markdown(f"""<table class="dt">
      <tr><th>Formula</th><th>Expression</th><th>Current Value</th><th>Source</th></tr>
      <tr><td>Emission trajectory</td><td>E_yr = {e_base_in}×(1−{r_comm:.4f})^(yr−{start_yr})</td>
          <td>E₂₀₃₀ = <b>{e2030:.2f} Mt</b></td><td>TC Energy 2024 Sustainability Report</td></tr>
      <tr><td>Compound reduction rate</td><td>r = 1−(1−{tgt_pct}%)<sup>1/6</sup></td>
          <td><b>{r_comm*100:.4f}%/yr</b></td><td>Derived from TC Energy 2030 target</td></tr>
      <tr><td>Asset EAL</td><td>AssetVal × BaseEAL% × RiskWt × RCP_mult(t)</td>
          <td>Portfolio terminal: ${(eal45 if show45 else eal85)[-1]:.3f}B/yr</td><td>Swiss Re NatCat · IPCC AR6</td></tr>
      <tr><td>Net Impact</td><td>(E×CPrice) + CAPEX − ITC + Offsets</td>
          <td>2030: ${(tr45 if show45 else tr85)["imp_comm"][min(2030-start_yr,n-1)]:.3f}B/yr</td><td>TCFD Transition Risk Framework</td></tr>
      <tr><td>Climate VaR</td><td>Loss_Total / MarketCap</td>
          <td>RCP 4.5: {cv45['cvar_mktcap']:.1f}% | RCP 8.5: {cv85['cvar_mktcap']:.1f}%</td><td>TCFD · NGFS</td></tr>
      <tr><td>Federal ITC</td><td>{itc_rate}% × Abatement CAPEX</td>
          <td>Cumul. benefit ${float(np.sum(tr45['itc_c'])):.2f}B</td><td>Canada Budget 2024</td></tr>
      <tr><td>Pass-Through</td><td>{pass_through}% of carbon/physical costs recovered</td>
          <td>Applied to EAL in DCF</td><td>TC Energy regulated pipeline tariffs</td></tr>
      <tr><td>Live FX</td><td>USD × {FX:.4f} = CAD</td><td>{'Live yfinance' if mkt['live'] else 'Fallback'}</td><td>yfinance CAD=X</td></tr>
      <tr><td>Market Cap</td><td>TRP TSX/NYSE</td><td>CAD ${mkt['mktcap_cad_bn']:.1f}B</td><td>yfinance TRP</td></tr>
    </table>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="note" style="margin-top:1rem">
      <b>⚠️ Disclaimer:</b> This is a portfolio-level climate stress testing demonstration model.
      Financial and ESG data sourced from TC Energy's publicly available 2024 Report on Sustainability,
      ESG Data Sheet, and Q3 2024 MD&A. Asset coordinates are representative centroids of operating regions.
      Physical risk EAL rates calibrated to Swiss Re NatCat benchmarks for North American energy infrastructure.
      Live market data via yfinance with 5-minute cache. This output does not constitute investment advice.
    </div>""", unsafe_allow_html=True)

    # Full CSV download
    tr_dl = tr45 if show45 else tr85
    csv = pd.DataFrame({
        "Year":yr_range, "E_BAU(Mt)":E_bau.round(4), "E_Committed(Mt)":E_comm.round(4),
        "CarbonPrice_RCP45($/t)":[round(interp(CARBON_PRICE_RCP45,y),0) for y in yr_range],
        "CarbonPrice_RCP85($/t)":[round(interp(CARBON_PRICE_RCP85,y),0) for y in yr_range],
        "EAL_RCP45($B)":eal45.round(4), "EAL_RCP85($B)":eal85.round(4),
        "CarbonTax_Comm($B)":tr_dl["ct_comm"].round(4),
        "AbateCAPEX($B)":tr_dl["capex_c"].round(4), "ITC($B)":tr_dl["itc_c"].round(4),
        "NetImpact_Comm($B)":tr_dl["imp_comm"].round(4),
        "NetImpact_BAU($B)":tr_dl["imp_bau"].round(4),
        "Avoided($B)":tr_dl["avoided"].round(4),
        "Adj_EBITDA_RCP45($B)":ebitda_adj45.round(4),
        "Adj_EBITDA_RCP85($B)":ebitda_adj85.round(4),
        "VaR_RCP45_pct":[round(cv45["cvar_pct"],2)]*n,
        "VaR_RCP85_pct":[round(cv85["cvar_pct"],2)]*n,
        "FX_USD_CAD":[round(FX,4)]*n,
    }).to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download Full Dataset (CSV)", data=csv,
        file_name=f"TCE_ClimVaR_v3_{end_yr}.csv", mime="text/csv")

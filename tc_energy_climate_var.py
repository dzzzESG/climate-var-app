import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

# --- 1. UI THEME & TEXT COLOR CONFIG (FORCING BLACK TEXT) ---
st.set_page_config(page_title="TC Energy Climate Stress Platform", layout="wide")

st.markdown("""
    <style>
    /* Global black text for professional corporate look */
    * { color: #000000 !important; }
    .stMetric { color: #000000 !important; border: 1px solid #f0f2f6; padding: 15px; border-radius: 5px; background-color: #fcfcfc; }
    .stSelectbox div div { color: #000000 !important; }
    .stSlider div { color: #000000 !important; }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .main { background-color: #FFFFFF; }
    /* Fix slider labels visibility */
    .stSlider label { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA SOURCE & REAL-TIME FX ENGINE ---
@st.cache_data(ttl=3600)
def get_live_context():
    # Fetch Live USD/CAD FX
    try:
        ticker = yf.Ticker("CAD=X")
        fx = ticker.history(period="1d")['Close'].iloc[-1]
    except Exception:
        fx = 1.39 # Conservative fallback
    
    # TC Energy Core Asset Database (Aggregated from 2024 Sustainability Report & Financials)
    # Values in CAD Billions, Emissions in MtCO2e
    assets = {
        'NGTL System': {
            'Type': 'Natural Gas Network', 'Value': 18.2, 'Emissions': 6.2, 'Lat': 53.5, 'Lon': -113.5, 
            'Stranded_Factor': 0.15, 
            'Phys_Hazards': ['Wildfire', 'Flooding', 'Extreme Heat'],
            'Trans_Risks': ['Carbon Taxation', 'Methane Regulation']
        },
        'Coastal GasLink': {
            'Type': 'Natural Gas Pipeline', 'Value': 14.5, 'Emissions': 1.1, 'Lat': 54.5, 'Lon': -128.6, 
            'Stranded_Factor': 0.10, 
            'Phys_Hazards': ['Flooding', 'Landslide', 'Wildfire'],
            'Trans_Risks': ['Methane Regulation', 'Stranded Asset Risk']
        },
        'Keystone Pipeline': {
            'Type': 'Liquids Pipeline', 'Value': 12.0, 'Emissions': 2.8, 'Lat': 49.0, 'Lon': -110.0, 
            'Stranded_Factor': 0.25, 
            'Phys_Hazards': ['Permafrost Thaw', 'Wildfire', 'Flooding'],
            'Trans_Risks': ['Stranded Asset Risk', 'Market Shift']
        },
        'Mexico Gas Pipelines': {
            'Type': 'Natural Gas Network', 'Value': 4.5, 'Emissions': 0.8, 'Lat': 19.2, 'Lon': -96.1, 
            'Stranded_Factor': 0.20, 
            'Phys_Hazards': ['Hurricane', 'Sea Level Rise', 'Flooding'],
            'Trans_Risks': ['Regulatory Change', 'Market Shift']
        },
        'Bruce Power (Share)': {
            'Type': 'Nuclear Power', 'Value': 5.8, 'Emissions': 0.1, 'Lat': 44.3, 'Lon': -81.5, 
            'Stranded_Factor': 0.02, 
            'Phys_Hazards': ['Water Level Change', 'Extreme Heat', 'Flooding'],
            'Trans_Risks': ['Market Shift', 'Carbon Taxation (Benefit)']
        }
    }
    return fx, assets

fx_rate, asset_db = get_live_context()

# --- 3. SIDEBAR: PROFESSIONAL CONFIGURATION PORTAL ---
with st.sidebar:
    st.title("Configuration Portal")
    
    # Section 1: Asset Master
    st.header("Asset Selection")
    selected_asset = st.selectbox("Select Asset", list(asset_db.keys()))
    info = asset_db[selected_asset]
    
    # Section 2: Scenario Mode
    st.header("Scenario Mode")
    model_type = st.selectbox("Climate Model", ["IPCC RCP Models", "NGFS Scenarios"])
    if model_type == "IPCC RCP Models":
        scenario = st.selectbox("Pathway Selection", ["RCP 4.5", "RCP 8.5"])
    else:
        scenario = st.selectbox("Pathway Selection", ["Net Zero 2050", "Delayed Transition", "Current Policies"])
    
    # Section 3: Stress Horizon (2024-2050 Dynamic)
    st.header("Stress Horizon")
    st.write("Baseline: 2024 | Range: 2050")
    duration = st.slider("Simulation Duration (Years)", min_value=1, max_value=26, value=6)
    target_year = 2024 + duration
    st.write(f"Projection Period: 2024 - {target_year}")

    # Section 4: Risk Exposure (Dual Dynamic Filtering)
    st.header("Risk Exposure (Linked)")
    p_risk = st.selectbox("Physical Hazard", options=info['Phys_Hazards'])
    t_risk = st.selectbox("Transition Driver", options=info['Trans_Risks'])

    # Section 5: Financial Assumptions
    st.header("Financial Assumptions")
    wacc = st.number_input("WACC (%)", value=8.5, step=0.1) / 100
    ebitda_margin = st.slider("EBITDA Margin (%)", 20, 60, 42) / 100
    
    st.divider()
    st.write(f"Live FX: 1 USD = {fx_rate:.4f} CAD")

# --- 4. CORE CALCULATION LOGIC ---
# Severity mapping
is_stress_scenario = scenario in ["RCP 8.5", "Delayed Transition", "Current Policies"]
sev_index = 0.08 if is_stress_scenario else 0.03

# A. Carbon Tax Calculation (Transition)
sim_years = np.arange(2024, target_year + 1)
is_high_policy = scenario in ["RCP 4.5", "Net Zero 2050"]
price_path = np.linspace(80, 250, len(sim_years)) if is_high_policy else np.linspace(80, 130, len(sim_years))
cum_carbon_tax = (info['Emissions'] * price_path).sum()

# B. Stranded Asset Loss
stranded_loss = info['Value'] * 1000 * info['Stranded_Factor'] * (duration / 26)
if is_high_policy: stranded_loss *= 1.4

# C. Market Shift Impact
m_adjustment = (info['Value'] * 1000 * 0.05) if "Market" in t_risk else 0

# Physical Risk Calculation
phys_loss = info['Value'] * 1000 * sev_index * (duration / 26)

# Final Metrics
total_stress_loss = cum_carbon_tax + stranded_loss + m_adjustment + phys_loss
cvar_pct = (total_stress_loss / (info['Value'] * 1000)) * -100

# --- 5. MAIN INTERFACE ---
# --- Entity Header Section ---
header_container = st.container()
with header_container:
    st.title("TC Energy Climate Risk Stress Test")
    
    # Asset Specific Fundamentals
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    col_a1.metric("Selected Entity", "TC Energy (TRP)")
    col_a2.metric("Asset Classification", info['Type'])
    col_a3.metric("Baseline Valuation", f"C${info['Value']}B")
    col_a4.metric("Emission Intensity", f"{info['Emissions']} MtCO2e")
    
    # Stress Summary Dashboard
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    col_b1.metric("Active Pathway", scenario)
    col_b2.metric("Aggregated Climate VaR", f"{cvar_pct:.2f}%", delta_color="inverse")
    col_b3.metric("Net Stress Loss (NPV)", f"C${total_stress_loss:.1f}M")
    col_b4.metric("Projection Horizon", f"By {target_year}")
    
    st.markdown("---")

# --- Analytics Modules (Tabs) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Asset Geography", "Physical Risk", "Transition Risk", "Climate VaR", "Full Report"
])

# Tab 1: Geography (Risk Heatmap)
with tab1:
    st.subheader("Geographic Risk Concentration Map")
    risk_score = (phys_loss / (info['Value']*1000)) * 10
    map_df = pd.DataFrame([{
        'Asset': selected_asset, 'Lat': info['Lat'], 'Lon': info['Lon'], 
        'Val_B': info['Value'], 'Hazard': p_risk, 'Risk_Level': risk_score
    }])
    fig_map = px.scatter_mapbox(
        map_df, lat="Lat", lon="Lon", size="Val_B", color="Risk_Level",
        color_continuous_scale=["#2D6A4F", "#FFB703", "#D00000"], range_color=[0, 1],
        zoom=3, mapbox_style="carto-positron", height=500,
        hover_data={"Hazard": True, "Risk_Level": False}
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.info(f"Visualizing Risk Level for {p_risk}. Color intensity represents financial vulnerability relative to asset value.")

# Tab 2: Physical Risk
with tab2:
    st.subheader(f"Physical Hazard Assessment: {p_risk}")
    st.metric("Estimated Asset Damage", f"CAD {phys_loss:.2f} Million")
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = phys_loss,
        gauge = {'axis': {'range': [None, 1500]}, 'bar': {'color': "#D00000" if is_stress_scenario else "#FB8500"}}
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)

# Tab 3: Transition Risk (A/B/C Quantification)
with tab3:
    st.subheader(f"Transition Risk Driver: {t_risk}")
    
    t_col1, t_col2, t_col3 = st.columns(3)
    t_col1.metric("A. Carbon Tax Liability", f"CAD {cum_carbon_tax:.1f}M")
    t_col2.metric("B. Stranded Asset Risk", f"CAD {stranded_loss:.1f}M")
    t_col3.metric("C. Market Shift Impact", f"CAD {m_adjustment:.1f}M")
    
    # Line chart color based on model
    line_color = "#D00000" if "8.5" in scenario else "#023E8A"
    fig_trend = px.area(x=sim_years, y=info['Emissions'] * price_path, 
                       title=f"Carbon Cost Projection under {scenario} (CAD M)",
                       color_discrete_sequence=[line_color])
    st.plotly_chart(fig_trend, use_container_width=True)

# Tab 4: Climate VaR Bridge
with tab4:
    st.subheader("Asset Valuation Sensitivity Bridge")
    
    # Detailed financial component layout
    f1, f2, f3 = st.columns(3)
    f1.info(f"**Transition Component**\n\nCAD {cum_carbon_tax + stranded_loss + m_adjustment:.1f}M")
    f2.info(f"**Physical Component**\n\nCAD {phys_loss:.1f}M")
    f3.info(f"**Aggregated Exposure**\n\nCAD {total_stress_loss:.1f}M")
    
    fig_water = go.Figure(go.Waterfall(
        x = ["Market Value", "Carbon Tax", "Stranded", "Market Adj", "Physical", "Stress Value"],
        y = [info['Value']*1000, -cum_carbon_tax, -stranded_loss, -m_adjustment, -phys_loss, 0],
        measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
    ))
    st.plotly_chart(fig_water, use_container_width=True)

# Tab 5: Full Report
with tab5:
    st.subheader("Integrated Stress Test Audit Report")
    
    primary_risk = "Transition" if (cum_carbon_tax + stranded_loss) > phys_loss else "Physical"
    
    report_text = f"""
STRESS TEST AUDIT SUMMARY: {selected_asset}
---------------------------------------------------------------------------
ENTITY: TC ENERGY (TRP)
PATHWAY: {scenario} ({model_type})
PERIOD: 2024 TO {target_year}
---------------------------------------------------------------------------

1. FINANCIAL QUANTIFICATION:
   - Aggregated Climate VaR: {cvar_pct:.2f}%
   - Net Present Value (NPV) Loss: CAD {total_stress_loss:.2f} Million

2. RISK ATTRIBUTION:
   - Transition Exposure: Carbon Taxation (CAD {cum_carbon_tax:.1f}M) and Stranded Asset Risk (CAD {stranded_loss:.1f}M).
   - Physical Exposure: {p_risk} damage estimated at CAD {phys_loss:.1f}M.

3. MANAGEMENT MITIGATION STRATEGY:
   Given that {primary_risk} is the dominant driver of value erosion:
   - If Transition-heavy: Prioritize decarbonization CAPEX and carbon cost pass-through optimization.
   - If Physical-heavy: Enhance asset hardening infrastructure and review catastrophic insurance coverage.

4. AUDIT STATEMENT:
This analysis integrates historical TRP emission profiles with IPCC/NGFS forward-looking climate pathways. 
The findings should be incorporated into the Enterprise Risk Management (ERM) framework.
---------------------------------------------------------------------------
    """
    st.text_area("Audit-Ready Summary", value=report_text, height=450)

st.divider()
st.caption(f"Proprietary Portfolio Work | Baseline Data: TC Energy Sustainability Report 2024 | FX Refresh: {fx_rate:.4f}")

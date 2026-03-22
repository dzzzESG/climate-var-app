import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import date

# --- 1. UI THEME & PROFESSIONAL COLOR PALETTE (CSS INJECTION) ---
st.set_page_config(page_title="TRP Climate Stress Terminal", layout="wide")

st.markdown("""
    <style>
    /* Main Background and text color */
    .main { background-color: #F8F9FA; color: #000000; }
    * { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    
    /* Metrics styling - Colorful and bordered */
    .stMetric { 
        color: #000000 !important; 
        border: 1px solid #DEE2E6; 
        padding: 15px; 
        border-radius: 5px; 
        background-color: #FFFFFF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .stMetric label { color: #495057 !important; font-weight: 600; font-size: 0.9rem; }
    .stMetric [data-testid="stMetricValue"] { color: #0F4C81 !important; font-size: 1.8rem; font-weight: 700; }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 5px; padding: 5px; }
    .stTabs [data-baseweb="tab-list"] button { color: #495057 !important; font-weight: bold; font-size: 1rem; padding: 10px 20px; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { background-color: #FFFFFF !important; color: #0F4C81 !important; border-bottom: 2px solid #0F4C81;}

    /* Sidebar styling */
    .css-163utfM { background-color: #0F4C81; color: #FFFFFF; }
    .css-163utfM .stSelectbox div div, .css-163utfM .stSlider div { color: #FFFFFF !important; }
    .stSlider label { color: #FFFFFF !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ASSET DATABASE WITH SYNTHESIZED, LOCATION-SPECIFIC RISK DATA ---
@st.cache_data(ttl=3600)
def get_live_data():
    try:
        fx = yf.Ticker("CAD=X").history(period="1d")['Close'].iloc[-1]
    except Exception:
        fx = 1.39 
    
    assets = {
        'NGTL System (AB/BC)': {
            'Type': 'Gas Network', 'Value': 18.2, 'Emissions': 6.2, 'Lat': 53.5, 'Lon': -113.5, 
            'Stranded_Factor': 0.15,
            'Phys_Coeffs': {'RCP 4.5': 0.02, 'RCP 8.5': 0.09, 'Net Zero': 0.015, 'Delayed': 0.08},
            'Eligible_Hazards': ['Wildfire', 'Flooding', 'Extreme Heat']
        },
        'Keystone Pipeline (Trans-con)': {
            'Type': 'Liquids Pipeline', 'Value': 12.0, 'Emissions': 2.8, 'Lat': 49.0, 'Lon': -110.0, 
            'Stranded_Factor': 0.25, 
            'Phys_Coeffs': {'RCP 4.5': 0.03, 'RCP 8.5': 0.06, 'Net Zero': 0.02, 'Delayed': 0.05},
            'Eligible_Hazards': ['Flooding', 'Extreme Cold', 'Permafrost Thaw']
        },
        'Mexico Gas Pipelines (Sur de Texas)': {
            'Type': 'Gas Network', 'Value': 4.5, 'Emissions': 0.8, 'Lat': 19.2, 'Lon': -96.1, 
            'Stranded_Factor': 0.20,
            'Phys_Coeffs': {'RCP 4.5': 0.04, 'RCP 8.5': 0.12, 'Net Zero': 0.035, 'Delayed': 0.11}, 
            'Eligible_Hazards': ['Hurricane', 'Sea Level Rise', 'Flooding']
        },
        'Coastal GasLink (BC)': {
            'Type': 'Gas Pipeline', 'Value': 14.5, 'Emissions': 1.1, 'Lat': 54.5, 'Lon': -128.6, 
            'Stranded_Factor': 0.10,
            'Phys_Coeffs': {'RCP 4.5': 0.015, 'RCP 8.5': 0.05, 'Net Zero': 0.01, 'Delayed': 0.04}, 
            'Eligible_Hazards': ['Wildfire', 'Flooding', 'Landslide']
        },
        'Bruce Power (Share, ON)': {
            'Type': 'Nuclear Power', 'Value': 5.8, 'Emissions': 0.1, 'Lat': 44.3, 'Lon': -81.5, 
            'Stranded_Factor': 0.01, 
            'Phys_Coeffs': {'RCP 4.5': 0.01, 'RCP 8.5': 0.03, 'Net Zero': 0.005, 'Delayed': 0.02}, 
            'Eligible_Hazards': ['Extreme Heat', 'Water Level Change']
        }
    }
    return fx, assets

fx_rate, asset_db = get_live_data()

# --- 3. SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("<h2 style='color:#FFFFFF;'>Configuration Portal</h2>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='color:#FFFFFF;'>Asset Selection</h4>", unsafe_allow_html=True)
    selected_asset = st.selectbox("Select Asset", list(asset_db.keys()), label_visibility="collapsed")
    info = asset_db[selected_asset]
    
    st.markdown("<h4 style='color:#FFFFFF;'>Scenario Mode</h4>", unsafe_allow_html=True)
    model_type = st.selectbox("Climate Model", ["IPCC RCP Models", "NGFS Scenarios"])
    if model_type == "IPCC RCP Models":
        scenario = st.selectbox("Pathway Selection", ["RCP 4.5 (2.0°C)", "RCP 8.5 (4.0°C)"])
    else:
        scenario = st.selectbox("Pathway Selection", ["Net Zero 2050 (1.5°C)", "Delayed Transition", "Current Policies"])
    
    st.markdown("<h4 style='color:#FFFFFF;'>Stress Horizon</h4>", unsafe_allow_html=True)
    st.write("Range: 2024 - 2050")
    duration = st.slider("Simulation Duration (Years)", min_value=1, max_value=26, value=6, label_visibility="collapsed")
    target_year = 2024 + duration

    st.markdown("<h4 style='color:#FFFFFF;'>Risk Hazard (Location-Specific)</h4>", unsafe_allow_html=True)
    phys_hazard = st.selectbox("Physical Hazard Focus", options=info['Eligible_Hazards'], label_visibility="collapsed")

    st.markdown("<h4 style='color:#FFFFFF;'>Financial Assumptions</h4>", unsafe_allow_html=True)
    wacc = st.number_input("WACC (%)", value=8.5, step=0.1) / 100
    
    st.divider()
    st.write(f"Live USD/CAD Rate: {fx_rate:.4f}")
    st.write("Reporting Currency: CAD")

# --- 4. CORE CALCULATION ENGINE ---
years = np.arange(2024, target_year + 1)
is_high_tax_scenario = scenario in ["RCP 4.5 (2.0°C)", "Net Zero 2050 (1.5°C)"]
carbon_price_path = np.linspace(80, 250, len(years)) if is_high_tax_scenario else np.linspace(80, 130, len(years))
cumulative_carbon_tax = (info['Emissions'] * carbon_price_path).sum()

stranded_multiplier = 1.4 if is_high_tax_scenario else 1.0
stranded_loss = info['Value'] * 1000 * info['Stranded_Factor'] * stranded_multiplier * (duration / 26)

m_adjustment = (info['Value'] * 1000 * 0.05) if "Pipeline" in selected_asset else 0

coeff_key = "RCP 4.5" if "4.5" in scenario else "RCP 8.5" if "8.5" in scenario else "Net Zero" if "Net Zero" in scenario else "Delayed"
damage_factor = info['Phys_Coeffs'].get(coeff_key, 0.05)
specific_phys_loss = info['Value'] * 1000 * damage_factor * (duration / 26)

total_stress_loss = cumulative_carbon_tax + stranded_loss + m_adjustment + specific_phys_loss
asset_valuation_M = info['Value'] * 1000
cvar_percentage = (total_stress_loss / asset_valuation_M) * -100

phys_loss_pct = (specific_phys_loss / asset_valuation_M) * 100

# --- 5. MAIN DASHBOARD TERMINAL ---
header_container = st.container()
with header_container:
    st.markdown("<h1 style='color: #0F4C81; margin-bottom: 0px;'>TC Energy Climate Risk Stress Testing</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6C757D; font-size: 1.1rem; margin-top: 0px;'>Enterprise Valuation Sensitivity & Hazard Analysis Platform</p>", unsafe_allow_html=True)
    
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    col_a1.metric("Selected Entity", "TC Energy (TRP.TO)")
    col_a2.metric("Asset Classification", info['Type'])
    col_a3.metric("Baseline Valuation", f"C${info['Value']} Billion")
    col_a4.metric("Emission Baseline", f"{info['Emissions']} MtCO2e")
    
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    col_b1.metric("Active Pathway", scenario)
    col_b2.metric("Aggregated Climate VaR", f"{cvar_percentage:.2f}%")
    col_b3.metric("Net Stress Loss (NPV)", f"C${total_stress_loss:.1f}M")
    col_b4.metric("Projection Horizon", f"By {target_year}")
    
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5 Modules (Tabs) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Asset Geography", "Physical Risk", "Transition Risk", "Climate VaR Bridge", "Full Management Report"
])

with tab1:
    st.markdown("### Geographic Risk Concentration Map")
    map_df = pd.DataFrame([{'Asset': selected_asset, 'Lat': info['Lat'], 'Lon': info['Lon'], 'Value_B': info['Value'], 'Primary_Hazard': phys_hazard, 'Phys_Loss_Pct': phys_loss_pct}])
    fig_map = px.scatter_mapbox(map_df, lat="Lat", lon="Lon", size="Value_B", size_max=25, color="Phys_Loss_Pct", color_continuous_scale="RdYlGn_r", range_color=[0, 10], zoom=3, mapbox_style="carto-positron", height=500, hover_name="Asset", hover_data={"Primary_Hazard": True, "Phys_Loss_Pct": ":.1f"})
    st.plotly_chart(fig_map, use_container_width=True)

with tab2:
    st.markdown(f"### Physical Hazard Assessment: {phys_hazard}")
    st.metric("Estimated Asset Damage", f"CAD {specific_phys_loss:.2f} Million")
    is_stress_scenario = scenario in ["RCP 8.5 (4.0°C)", "Delayed Transition", "Current Policies"]
    fig_gauge = go.Figure(go.Indicator(mode = "gauge+number", value = specific_phys_loss, gauge = {'axis': {'range': [None, 1500]}, 'bar': {'color': "#D00000" if is_stress_scenario else "#F5A623"}}))
    fig_gauge.update_layout(height=400)
    st.plotly_chart(fig_gauge, use_container_width=True)

with tab3:
    st.markdown("### Transition Risk: Regulatory & Market Drivers")
    t1, t2, t3 = st.columns(3)
    t1.metric("Cum. Carbon Tax (A)", f"CAD {cumulative_carbon_tax:.1f}M")
    t2.metric("Stranded Asset Loss (B)", f"CAD {stranded_loss:.1f}M")
    t3.metric("Market Adj (C)", f"CAD {m_adjustment:.1f}M")

    line_color = "#0F4C81" if "Net Zero" in scenario or "4.5" in scenario else "#D00000"
    fig_area = px.area(x=years, y=info['Emissions'] * carbon_price_path, labels={'x':'Year', 'y':'Annual Cost (CAD M)'}, color_discrete_sequence=[line_color])
    fig_area.update_layout(height=400, template="plotly_white", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_area, use_container_width=True)

with tab4:
    st.markdown("### Asset Valuation Sensitivity Bridge")
    f_c1, f_c2, f_c3 = st.columns(3)
    f_c1.info(f"**Operational Impairment**\n\nCAD {cumulative_carbon_tax + m_adjustment:.1f}M")
    f_c2.info(f"**Stranded Capital**\n\nCAD {stranded_loss:.1f}M")
    f_c3.info(f"**Physical Damage**\n\nCAD {specific_phys_loss:.1f}M")
    
    fig_water = go.Figure(go.Waterfall(x = ["Baseline Book Value", "Carbon Tax", "Stranded Capital", "Market Adj", "Physical Damage", "Stress Value"], y = [info['Value']*1000, -cumulative_carbon_tax, -stranded_loss, -m_adjustment, -specific_phys_loss, 0], measure = ["absolute", "relative", "relative", "relative", "relative", "total"]))
    fig_water.update_layout(height=450, template="plotly_white")
    st.plotly_chart(fig_water, use_container_width=True)

# --- TAB 5: FORMAL PDF-STYLE REPORT ---
with tab5:
    # Action Button for Download
    col_export1, col_export2 = st.columns([8, 2])
    with col_export2:
        report_txt = f"TC Energy Climate Risk Report\nAsset: {selected_asset}\nScenario: {scenario}\nClimate VaR: {cvar_percentage:.2f}%\nTotal NPV Loss: CAD {total_stress_loss:.1f}M"
        st.download_button(label="📥 Download Formal Report (.txt)", data=report_txt, file_name=f"TRP_Climate_Audit_{selected_asset[:4]}.txt", mime="text/plain", use_container_width=True)

    # Dynamic Strategy Logic
    primary_risk_driver = "Transition Risk" if (cumulative_carbon_tax + stranded_loss + m_adjustment) > specific_phys_loss else "Physical Risk"
    risk_level = "High" if abs(cvar_percentage) > 15 else "Moderate" if abs(cvar_percentage) > 5 else "Low"
    
    if primary_risk_driver == "Transition Risk":
        strategy_bullets = f"""
        <li style="margin-bottom: 8px;"><b>Decarbonization CAPEX:</b> Accelerate operational upgrades to reduce the {info['Emissions']} MtCO2e baseline emission intensity.</li>
        <li style="margin-bottom: 8px;"><b>Contract Renegotiation:</b> Evaluate the pass-through capacity of carbon compliance costs in existing long-term shipper contracts.</li>
        <li style="margin-bottom: 8px;"><b>Depreciation Strategy:</b> Review economic obsolescence timelines for capital assets under the aggressive <b>{scenario}</b> pathway.</li>
        """
    else:
        strategy_bullets = f"""
        <li style="margin-bottom: 8px;"><b>Asset Hardening:</b> Increase capital expenditure for specific structural defenses against <b>{phys_hazard}</b>.</li>
        <li style="margin-bottom: 8px;"><b>Insurance Review:</b> Reassess catastrophic insurance coverage terms for assets located in highly vulnerable geographic zones.</li>
        <li style="margin-bottom: 8px;"><b>Emergency Protocols:</b> Update location-specific emergency response plans to minimize downtime during extreme weather events.</li>
        """

    # Formal HTML Report Template
    formal_report_html = f"""
    <div style="background-color: #FFFFFF; padding: 50px; border: 1px solid #D1D5DB; box-shadow: 0 4px 6px rgba(0,0,0,0.05); font-family: 'Georgia', serif; color: #000000; margin-top: 10px;">
        
        <div style="text-align: center; border-bottom: 3px solid #0F4C81; padding-bottom: 15px; margin-bottom: 30px;">
            <h2 style="color: #0F4C81; margin: 0; font-family: 'Georgia', serif; font-size: 28px; text-transform: uppercase;">Climate Risk Audit & Advisory Report</h2>
            <p style="color: #6B7280; font-size: 14px; margin: 10px 0 0 0; letter-spacing: 1px;">PRIVATE & CONFIDENTIAL | PREPARED FOR TC ENERGY (TRP.TO) MANAGEMENT</p>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 14px;">
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #E5E7EB;"><b>Date of Assessment:</b> {date.today().strftime('%B %d, %Y')}</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #E5E7EB;"><b>Target Horizon:</b> 2024 - {target_year} ({duration} Years)</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #E5E7EB;"><b>Asset Evaluated:</b> {selected_asset}</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #E5E7EB;"><b>Climate Pathway:</b> {scenario}</td>
            </tr>
        </table>

        <h3 style="color: #0F4C81; border-bottom: 1px solid #0F4C81; padding-bottom: 5px; font-size: 18px; margin-top: 30px;">1. EXECUTIVE SUMMARY</h3>
        <p style="line-height: 1.6; font-size: 15px;">
            Under the prescribed <b>{scenario}</b> pathway, the <b>{selected_asset}</b> infrastructure demonstrates a <b>{risk_level.lower()}</b> sensitivity to integrated climate factors. 
            The aggregated Climate Value-at-Risk (VaR) is calculated at <b>{cvar_percentage:.2f}%</b>, representing a total projected Net Present Value (NPV) impairment of <b>CAD {total_stress_loss:.1f} Million</b> against the baseline asset valuation of CAD {info['Value']} Billion.
        </p>

        <h3 style="color: #0F4C81; border-bottom: 1px solid #0F4C81; padding-bottom: 5px; font-size: 18px; margin-top: 30px;">2. QUANTIFIED RISK ATTRIBUTION</h3>
        <p style="line-height: 1.6; font-size: 15px;">The projected valuation impairment is distributed across the following material drivers:</p>
        <ul style="line-height: 1.8; font-size: 15px;">
            <li><b>Regulatory & Tax Liability (Transition):</b> Cumulative carbon compliance costs estimated at <b>CAD {cumulative_carbon_tax:.1f} Million</b>.</li>
            <li><b>Capital Stranding (Transition):</b> Economic obsolescence risk resulting in a potential impairment of <b>CAD {stranded_loss:.1f} Million</b>.</li>
            <li><b>Asset Damage (Physical):</b> Site-specific vulnerability to <b>{phys_hazard}</b> requiring estimated resilience/repair capital of <b>CAD {specific_phys_loss:.1f} Million</b>.</li>
        </ul>

        <h3 style="color: #0F4C81; border-bottom: 1px solid #0F4C81; padding-bottom: 5px; font-size: 18px; margin-top: 30px;">3. STRATEGIC MANAGEMENT RECOMMENDATIONS</h3>
        <p style="line-height: 1.6; font-size: 15px;">Diagnostic analytics identify <b>{primary_risk_driver}</b> as the dominant catalyst for value erosion within this asset boundary. Management is advised to prioritize the following initiatives:</p>
        <ul style="line-height: 1.8; font-size: 15px; background-color: #F3F4F6; padding: 20px 20px 20px 40px; border-left: 4px solid #0F4C81;">
            {strategy_bullets}
        </ul>

        <div style="margin-top: 50px; border-top: 1px solid #D1D5DB; padding-top: 15px; font-size: 12px; color: #9CA3AF; text-align: justify;">
            <b>Auditor Statement:</b> This stress test complies with the core principles of the Task Force on Climate-related Financial Disclosures (TCFD) and IFRS S2. Forward-looking projections utilize discounted cash flow (DCF) mechanics applying a WACC of {wacc*100}%. Data synthesized from public disclosures and standard climate models. Not intended for direct trading purposes.
        </div>
    </div>
    """
    
    st.markdown(formal_report_html, unsafe_allow_html=True)

# Footer
st.divider()
st.markdown(f"<p style='text-align: center; color: #6C757D; font-size: 12px;'>Proprietary Advisory Tool | Baseline Data: TRP Disclosure | Live FX: {fx_rate:.4f} CAD</p>", unsafe_allow_html=True)

"""
╔══════════════════════════════════════════════════════════════════════╗
║          Climate VaR 气候风险压力测试平台                              ║
║          IPCC RCP 4.5 / 8.5 Aligned Stress Testing Tool             ║
║                                                                      ║
║  安装依赖:  pip install streamlit plotly pandas numpy                 ║
║  运行方式:  streamlit run climate_var_app.py                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
#  Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Climate VaR | 气候风险压力测试",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  Global CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.main                        { background: #f8fafc; }
.block-container             { padding: 1.8rem 2.5rem; }

/* ── Hero Banner ── */
.hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2d42 55%, #243b53 100%);
    border-radius: 16px; padding: 2.4rem 3rem; margin-bottom: 2rem; color: white;
}
.hero h1 { font-size: 1.85rem; font-weight: 700; margin: 0 0 .4rem; letter-spacing: -.5px; }
.hero p  { font-size: .95rem; color: #94a3b8; margin: 0; }
.hero-tags { display: flex; gap: 8px; margin-top: 1.2rem; flex-wrap: wrap; }
.tag {
    background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.14);
    border-radius: 20px; padding: 3px 13px; font-size: .75rem; color: #cbd5e1;
}

/* ── Metric Cards ── */
.kpi { background: white; border-radius: 12px; padding: 1.3rem 1.5rem;
       border: 1px solid #e2e8f0; height: 100%; }
.kpi-label { font-size: .72rem; color: #64748b; font-weight: 600;
             text-transform: uppercase; letter-spacing: .07em; margin-bottom: 6px; }
.kpi-value { font-size: 1.85rem; font-weight: 700; color: #0f172a; line-height: 1.05; }
.kpi-sub   { font-size: .8rem; margin-top: 5px; }
.neg  { color: #ef4444; } .warn { color: #f59e0b; } .pos { color: #22c55e; }

/* ── Section Headers ── */
.sec-hdr {
    font-size: 1.05rem; font-weight: 600; color: #0f172a;
    padding-bottom: .7rem; border-bottom: 2px solid #e2e8f0; margin-bottom: 1.4rem;
}

/* ── Risk Badges ── */
.badge { display: inline-block; padding: 2px 11px; border-radius: 20px; font-size: .75rem; font-weight: 600; }
.b-hi  { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.b-md  { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.b-lo  { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

/* ── Insight Box ── */
.insight {
    background: #f0f9ff; border-left: 4px solid #0ea5e9;
    border-radius: 0 10px 10px 0; padding: 1rem 1.2rem; margin: 1rem 0;
}
.insight strong { color: #0369a1; }

/* ── Assumption Table ── */
.assume-table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.assume-table th { background: #f1f5f9; color: #475569; font-weight: 600;
                   padding: 8px 12px; text-align: left; }
.assume-table td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.assume-table tr:last-child td { border-bottom: none; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #f1f5f9; border-radius: 10px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px; padding: 7px 18px; font-size: .88rem;
    font-weight: 500; color: #64748b;
}
.stTabs [aria-selected="true"] {
    background: white !important; color: #0f172a !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.1);
}

div[data-testid="stExpander"] { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }
.sidebar-lbl { font-size: .7rem; font-weight: 700; text-transform: uppercase;
               letter-spacing: .09em; color: #94a3b8; margin: 1.2rem 0 .3rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Constants & Model Data
# ─────────────────────────────────────────────
HAZARD_PARAMS = {
    "洪涝 Flood":    {"base_eal": .013, "rcp45": 1.40, "rcp85": 1.90},
    "野火 Wildfire": {"base_eal": .009, "rcp45": 1.60, "rcp85": 2.50},
    "热浪 Heat":     {"base_eal": .005, "rcp45": 1.25, "rcp85": 1.75},
    "风暴 Storm":    {"base_eal": .010, "rcp45": 1.30, "rcp85": 1.80},
    "干旱 Drought":  {"base_eal": .006, "rcp45": 1.20, "rcp85": 1.65},
}

CARBON_PRICE = {  # USD/tonne CO₂
    2024: 65,  2025: 80,  2026: 95,  2027: 110,
    2028: 130, 2029: 150, 2030: 170, 2032: 195,
    2035: 230, 2038: 270, 2040: 310, 2045: 380, 2050: 450,
}

def rcp_multiplier(rcp: str, t: int) -> float:
    """Hazard intensity multiplier at year t (t=0 → 2024)."""
    if rcp == "rcp45":
        return 1 + 0.020 * t + 0.0008 * t ** 1.6
    else:
        return 1 + 0.035 * t + 0.0018 * t ** 2.0

def interpolated_carbon_price(year: int) -> float:
    keys = sorted(CARBON_PRICE)
    if year <= keys[0]:  return CARBON_PRICE[keys[0]]
    if year >= keys[-1]: return CARBON_PRICE[keys[-1]]
    for i in range(len(keys) - 1):
        y0, y1 = keys[i], keys[i+1]
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0)
            return CARBON_PRICE[y0] + t * (CARBON_PRICE[y1] - CARBON_PRICE[y0])

# ─────────────────────────────────────────────
#  Sidebar Inputs
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 参数配置")
    st.caption("Climate VaR Stress Testing Platform")
    st.divider()

    st.markdown('<div class="sidebar-lbl">📌 资产信息</div>', unsafe_allow_html=True)
    asset_name    = st.text_input("资产名称", "示范工业园区 A")
    asset_type    = st.selectbox("资产类型", ["工业厂房", "商业办公楼", "数据中心", "仓储物流", "零售商业"])
    replace_cost  = st.number_input("资产重置成本（万元）", 500, 200000, 8000, 500)
    lat           = st.number_input("纬度", value=43.70, format="%.2f")
    lon           = st.number_input("经度", value=-79.42, format="%.2f")

    st.markdown('<div class="sidebar-lbl">⚡ 气候情景</div>', unsafe_allow_html=True)
    scenario_opt  = st.radio("IPCC 情景路径", ["RCP 4.5（温和）", "RCP 8.5（高排放）", "双情景对比"])
    horizon       = st.slider("压力测试期限（年）", 5, 30, 20, 5)
    hazard_sel    = st.multiselect(
        "暴露风险类型", list(HAZARD_PARAMS.keys()),
        default=["洪涝 Flood", "热浪 Heat"]
    )
    if not hazard_sel:
        hazard_sel = ["洪涝 Flood"]

    st.markdown('<div class="sidebar-lbl">💼 企业财务</div>', unsafe_allow_html=True)
    revenue       = st.number_input("年营收（万元）", 1000, 500000, 25000, 1000)
    ebitda_margin = st.slider("当前 EBITDA 利润率 %", 5, 60, 28)
    co2_tonnes    = st.number_input("年碳排放（吨 CO₂）", 100, 500000, 12000, 500)
    wacc          = st.slider("WACC 折现率 %", 3.0, 15.0, 8.5, 0.5)
    usd_rmb       = st.number_input("汇率 USD/CNY", 6.0, 8.5, 7.25, 0.05)

# ─────────────────────────────────────────────
#  Core Model Functions
# ─────────────────────────────────────────────
def run_physical_risk(rcp: str, hazards: list, yrs: int, rc_wan: float):
    rc = rc_wan  # 万元
    year_range = list(range(2024, 2024 + yrs + 1))
    total = np.zeros(yrs + 1)
    breakdown = {}
    for h in hazards:
        p = HAZARD_PARAMS[h]
        series = np.array([
            p["base_eal"] * (p[rcp] if rcp == "rcp45" else p["rcp85"]) * rcp_multiplier(rcp, t) * rc
            for t in range(yrs + 1)
        ])
        total += series
        breakdown[h] = series
    return total, year_range, breakdown


def run_transition_risk(yrs: int, co2: float, rev: float, margin: float):
    year_range = list(range(2024, 2024 + yrs + 1))
    base_ebitda = rev * margin / 100
    carbon_cost = np.array([
        interpolated_carbon_price(2024 + t) * co2 / 10000 * usd_rmb  # CNY 万元
        for t in range(yrs + 1)
    ])
    adj_margin  = np.array([
        margin - (carbon_cost[t] / rev * 100)
        for t in range(yrs + 1)
    ])
    return carbon_cost, base_ebitda, adj_margin, year_range


def run_climate_var(phys_loss, carbon_loss, yrs: int, rev: float, margin: float):
    base_fcf  = rev * margin / 100
    discount  = np.array([(1 / (1 + wacc / 100)) ** t for t in range(yrs + 1)])
    base_npv  = float(np.sum(base_fcf * discount))
    adj_fcf   = base_fcf - phys_loss - carbon_loss
    adj_npv   = float(np.sum(adj_fcf * discount))
    cvar      = base_npv - adj_npv
    cvar_pct  = cvar / base_npv * 100 if base_npv else 0
    return base_npv, adj_npv, cvar, cvar_pct, adj_fcf, base_fcf * np.ones(yrs + 1)


# ─── Run models ───────────────────────────────
use85   = "8.5" in scenario_opt
both    = "双" in scenario_opt
rcp_key = "rcp85" if use85 else "rcp45"

phys45, yr_range, bd45 = run_physical_risk("rcp45", hazard_sel, horizon, replace_cost)
phys85, _,        bd85 = run_physical_risk("rcp85", hazard_sel, horizon, replace_cost)
phys_main = phys85 if use85 else phys45

carbon, base_ebitda, adj_margins, _ = run_transition_risk(horizon, co2_tonnes, revenue, ebitda_margin)
base_npv, adj_npv, cvar, cvar_pct, adj_fcf, base_fcf_arr = run_climate_var(
    phys_main, carbon, horizon, revenue, ebitda_margin
)

cum_phys   = float(np.sum(phys_main))
cum_carbon = float(np.sum(carbon))
eal_final  = phys_main[-1] / replace_cost * 100
margin_hit = ebitda_margin - adj_margins[-1]

risk_lvl  = "HIGH" if cvar_pct > 20 else ("MED" if cvar_pct > 8 else "LOW")
risk_cls  = {"HIGH": "b-hi", "MED": "b-md", "LOW": "b-lo"}[risk_lvl]
risk_lbl  = {"HIGH": "高风险 ▲", "MED": "中风险 ◆", "LOW": "低风险 ●"}[risk_lvl]

# ─────────────────────────────────────────────
#  Hero Banner
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <h1>🌍 Climate VaR 压力测试平台</h1>
  <p>基于 IPCC RCP 路径的气候风险量化工具 &nbsp;—&nbsp; <strong style="color:#e2e8f0">{asset_name}</strong></p>
  <div class="hero-tags">
    <span class="tag">📍 {lat:.2f}°N, {lon:.2f}°E</span>
    <span class="tag">🏗 {asset_type}</span>
    <span class="tag">📅 2024 – {2024+horizon}</span>
    <span class="tag">{'⚡ RCP 4.5 + 8.5 双情景' if both else ('🔴 RCP 8.5 高排放' if use85 else '🟡 RCP 4.5 温和')}</span>
    <span class="tag">WACC {wacc}%</span>
    <span class="tag">CO₂ {co2_tonnes:,} t/yr</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  KPI Row
# ─────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi">
      <div class="kpi-label">🎯 Climate VaR（现值损失）</div>
      <div class="kpi-value">¥{cvar/10000:.2f}亿</div>
      <div class="kpi-sub neg">▼ 占基准 NPV {cvar_pct:.1f}%
        &nbsp;<span class="badge {risk_cls}">{risk_lbl}</span></div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi">
      <div class="kpi-label">🌊 累计物理损失</div>
      <div class="kpi-value">¥{cum_phys/10000:.2f}亿</div>
      <div class="kpi-sub neg">终期 EAL {eal_final:.2f}% / 年</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi">
      <div class="kpi-label">🏭 累计碳税成本</div>
      <div class="kpi-value">¥{cum_carbon/10000:.2f}亿</div>
      <div class="kpi-sub warn">碳价 ${interpolated_carbon_price(2024+horizon):.0f}/吨（{2024+horizon}年）</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi">
      <div class="kpi-label">📉 EBITDA 利润率侵蚀</div>
      <div class="kpi-value">{margin_hit:.1f} pp</div>
      <div class="kpi-sub neg">{ebitda_margin}% → {adj_margins[-1]:.1f}%（{2024+horizon}年）</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Tabs
# ─────────────────────────────────────────────
tabA, tabB, tabC, tabD = st.tabs([
    "🌊  A · 物理风险建模",
    "🏭  B · 转型风险建模",
    "📊  C · Climate VaR 估值",
    "📋  综合压测报告",
])

# ════════════════════════════════════════════
#  TAB A — Physical Risk
# ════════════════════════════════════════════
with tabA:
    st.markdown('<div class="sec-hdr">物理风险（Physical Risk）— 预期年化损失 EAL 建模</div>', unsafe_allow_html=True)

    col_chart, col_info = st.columns([3, 1])

    with col_chart:
        fig = go.Figure()
        colors = {"rcp45": "#3b82f6", "rcp85": "#ef4444"}

        if both or not use85:
            fig.add_trace(go.Scatter(
                x=yr_range, y=phys45,
                name="RCP 4.5 温和",
                line=dict(color=colors["rcp45"], width=2.5),
                fill="tozeroy", fillcolor="rgba(59,130,246,0.08)"
            ))
        if both or use85:
            fig.add_trace(go.Scatter(
                x=yr_range, y=phys85,
                name="RCP 8.5 高排放",
                line=dict(color=colors["rcp85"], width=2.5, dash="solid" if use85 else "dash"),
                fill="tozeroy", fillcolor="rgba(239,68,68,0.06)"
            ))
        if both:
            diff = phys85 - phys45
            fig.add_trace(go.Scatter(
                x=yr_range, y=diff,
                name="情景差值",
                line=dict(color="#f59e0b", width=1.5, dash="dot"),
            ))

        fig.update_layout(
            title="预期年化损失（EAL）时序 — 万元/年",
            xaxis_title="年份", yaxis_title="EAL（万元/年）",
            height=380, template="plotly_white",
            legend=dict(orientation="h", y=-0.18),
            margin=dict(t=40, b=60, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.markdown("**各风险敞口分解（终期）**")
        bd = bd85 if (use85 and not both) else bd45
        hz_data = [(h, round(bd[h][-1], 1)) for h in hazard_sel]
        hz_data.sort(key=lambda x: -x[1])
        for h, v in hz_data:
            pct = v / (sum(x[1] for x in hz_data) + 0.001) * 100
            st.markdown(f"**{h}**")
            st.progress(int(pct))
            st.caption(f"¥{v:.1f} 万/年 ({pct:.0f}%)")
            st.markdown("")

    # Stacked area by hazard
    st.markdown("**风险类型叠加贡献图**")
    bd_use = bd85 if use85 else bd45
    fig2 = go.Figure()
    palette = ["#3b82f6", "#ef4444", "#f59e0b", "#22c55e", "#8b5cf6"]
    for i, h in enumerate(hazard_sel):
        fig2.add_trace(go.Scatter(
            x=yr_range, y=bd_use[h],
            name=h, stackgroup="one",
            fillcolor=palette[i % len(palette)].replace("#", "rgba(").replace(
                "rgba(", "rgba(") + ",0.7)" if False else palette[i % len(palette)],
            line=dict(width=0.5),
        ))
    fig2.update_layout(
        height=280, template="plotly_white",
        yaxis_title="EAL 万元/年", xaxis_title="年份",
        legend=dict(orientation="h", y=-0.22),
        margin=dict(t=20, b=60, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(f"""
    <div class="insight">
      <strong>📌 分析师注释：</strong> 在 {'RCP 8.5' if use85 else 'RCP 4.5'} 情景下，
      至 {2024+horizon} 年，{asset_name} 的综合 EAL 将从当前
      <strong>¥{phys_main[0]:.1f} 万/年</strong> 上升至
      <strong>¥{phys_main[-1]:.1f} 万/年</strong>，增幅
      <strong>{(phys_main[-1]/phys_main[0]-1)*100:.0f}%</strong>。
      主导风险为 <strong>{hz_data[0][0] if hz_data else '—'}</strong>。
    </div>
    """, unsafe_allow_html=True)

    # Data table
    with st.expander("📄 查看原始数据"):
        df_phys = pd.DataFrame({
            "年份": yr_range,
            "EAL RCP 4.5（万元/年）": phys45.round(2),
            "EAL RCP 8.5（万元/年）": phys85.round(2),
        })
        st.dataframe(df_phys, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════
#  TAB B — Transition Risk
# ════════════════════════════════════════════
with tabB:
    st.markdown('<div class="sec-hdr">转型风险（Transition Risk）— 碳税冲击与 EBITDA 侵蚀</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Carbon price path
        carbon_prices_plot = [interpolated_carbon_price(y) for y in yr_range]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=yr_range, y=carbon_prices_plot,
            name="碳价路径", line=dict(color="#f59e0b", width=3),
            fill="tozeroy", fillcolor="rgba(245,158,11,0.1)"
        ))
        # Mark key milestone
        fig3.add_vline(x=2030, line_width=1.5, line_dash="dash", line_color="#dc2626",
                       annotation_text="2030目标 $170/t", annotation_position="top right")
        fig3.update_layout(
            title="加拿大碳税路径（USD/吨 CO₂）",
            height=320, template="plotly_white",
            xaxis_title="年份", yaxis_title="碳价 USD/t",
            margin=dict(t=40, b=20, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        # EBITDA margin erosion
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=yr_range, y=[ebitda_margin] * len(yr_range),
            name="基准利润率", line=dict(color="#94a3b8", width=1.5, dash="dash")
        ))
        fig4.add_trace(go.Scatter(
            x=yr_range, y=adj_margins,
            name="气候调整后利润率",
            line=dict(color="#8b5cf6", width=2.5),
            fill="tonexty", fillcolor="rgba(239,68,68,0.08)"
        ))
        fig4.add_hline(y=0, line_color="#ef4444", line_dash="dot",
                       annotation_text="利润率=0", annotation_position="right")
        fig4.update_layout(
            title="EBITDA 利润率侵蚀路径 (%)",
            height=320, template="plotly_white",
            xaxis_title="年份", yaxis_title="EBITDA 利润率 %",
            legend=dict(orientation="h", y=-0.22),
            margin=dict(t=40, b=60, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Carbon cost bar chart
    st.markdown("**年度碳税绝对成本（万元）**")
    bar_years = yr_range[::max(1, horizon // 8)]
    bar_vals  = [carbon[yr_range.index(y)] for y in bar_years]

    fig5 = go.Figure(go.Bar(
        x=bar_years, y=bar_vals,
        marker_color=[
            "#fbbf24" if v < carbon[-1] * 0.5 else
            ("#f97316" if v < carbon[-1] * 0.8 else "#ef4444")
            for v in bar_vals
        ],
        text=[f"¥{v:.0f}" for v in bar_vals],
        textposition="outside", textfont=dict(size=11),
    ))
    fig5.update_layout(
        height=280, template="plotly_white",
        xaxis_title="年份", yaxis_title="碳税成本（万元）",
        margin=dict(t=20, b=20, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown(f"""
    <div class="insight">
      <strong>📌 分析师注释：</strong>
      当碳价在 {2024+horizon} 年达到
      <strong>${interpolated_carbon_price(2024+horizon):.0f}/吨</strong> 时，
      企业年碳税支出将达 <strong>¥{carbon[-1]:.0f} 万</strong>，
      相当于当期营收的 <strong>{carbon[-1]/revenue*100:.2f}%</strong>，
      EBITDA 利润率从基准 <strong>{ebitda_margin}%</strong> 压缩至
      <strong>{adj_margins[-1]:.1f}%</strong>，
      侵蚀 <strong>{margin_hit:.1f} 个百分点</strong>。
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📄 碳税情景数据表"):
        df_trans = pd.DataFrame({
            "年份": yr_range,
            "碳价（USD/t）": [round(interpolated_carbon_price(y), 0) for y in yr_range],
            "碳税成本（万元）": carbon.round(1),
            "营收占比（%）": (carbon / revenue * 100).round(3),
            "调整后EBITDA率（%）": adj_margins.round(2),
        })
        st.dataframe(df_trans, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════
#  TAB C — Climate VaR Valuation
# ════════════════════════════════════════════
with tabC:
    st.markdown('<div class="sec-hdr">气候敏感型估值（Climate-adjusted Valuation）— DCF + Climate VaR</div>', unsafe_allow_html=True)

    # Waterfall
    col_wf, col_gauge = st.columns([2, 1])

    with col_wf:
        wf_labels = ["基准 NPV", "物理风险损失", "转型风险损失", "Climate-adjusted NPV"]
        wf_base = base_npv / 10000
        wf_phys = -float(np.sum(phys_main * np.array([(1/(1+wacc/100))**t for t in range(horizon+1)]))) / 10000
        wf_carb = -float(np.sum(carbon * np.array([(1/(1+wacc/100))**t for t in range(horizon+1)]))) / 10000
        wf_adj  = adj_npv / 10000

        fig6 = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=wf_labels,
            y=[wf_base, wf_phys, wf_carb, wf_adj],
            text=[f"¥{wf_base:.1f}亿", f"¥{wf_phys:.1f}亿",
                  f"¥{wf_carb:.1f}亿", f"¥{wf_adj:.1f}亿"],
            textposition="outside",
            decreasing=dict(marker_color="#ef4444"),
            increasing=dict(marker_color="#22c55e"),
            totals=dict(marker_color="#3b82f6"),
            connector=dict(line=dict(color="#cbd5e1", width=1.5, dash="dot")),
        ))
        fig6.update_layout(
            title="DCF 瀑布图 — 气候风险对估值的逐层冲击（亿元）",
            height=380, template="plotly_white",
            margin=dict(t=40, b=20, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig6, use_container_width=True)

    with col_gauge:
        st.markdown("**Climate VaR 风险指示器**")
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=round(cvar_pct, 1),
            number={"suffix": "%", "font": {"size": 36}},
            delta={"reference": 8, "suffix": "%", "prefix": "基准 8%"},
            gauge={
                "axis": {"range": [0, 50], "ticksuffix": "%"},
                "bar": {"color": "#ef4444" if cvar_pct > 20 else ("#f59e0b" if cvar_pct > 8 else "#22c55e")},
                "steps": [
                    {"range": [0, 8],  "color": "#f0fdf4"},
                    {"range": [8, 20], "color": "#fffbeb"},
                    {"range": [20, 50],"color": "#fef2f2"},
                ],
                "threshold": {"line": {"color": "#dc2626", "width": 3}, "value": 20},
            },
            title={"text": "Climate VaR<br>占基准 NPV"},
        ))
        fig_g.update_layout(
            height=300,
            margin=dict(t=20, b=0, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_g, use_container_width=True)

        # Summary metrics
        st.markdown(f"""
        <table class="assume-table">
          <tr><th>指标</th><th>数值</th></tr>
          <tr><td>基准 NPV</td><td><b>¥{base_npv/10000:.2f}亿</b></td></tr>
          <tr><td>调整后 NPV</td><td><b>¥{adj_npv/10000:.2f}亿</b></td></tr>
          <tr><td>Climate VaR</td><td style="color:#ef4444"><b>¥{cvar/10000:.2f}亿</b></td></tr>
          <tr><td>VaR / NPV</td><td style="color:#ef4444"><b>{cvar_pct:.1f}%</b></td></tr>
          <tr><td>风险等级</td><td><span class="badge {risk_cls}">{risk_lbl}</span></td></tr>
        </table>
        """, unsafe_allow_html=True)

    # FCF comparison chart
    st.markdown("**自由现金流对比：基准 vs 气候调整（万元/年）**")
    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(
        x=yr_range, y=base_fcf_arr,
        name="基准 FCF", line=dict(color="#94a3b8", width=2, dash="dash"),
    ))
    fig7.add_trace(go.Scatter(
        x=yr_range, y=adj_fcf,
        name="气候调整 FCF", line=dict(color="#3b82f6", width=2.5),
        fill="tonexty", fillcolor="rgba(239,68,68,0.07)",
    ))
    fig7.add_hline(y=0, line_dash="dot", line_color="#ef4444", line_width=1)
    fig7.update_layout(
        height=300, template="plotly_white",
        xaxis_title="年份", yaxis_title="FCF（万元/年）",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=20, b=50, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig7, use_container_width=True)

    # Sensitivity heatmap
    st.markdown("**敏感性分析：Climate VaR% vs WACC × 碳排放量**")
    wacc_range    = [5, 6, 7, 8, 9, 10, 11, 12]
    co2_range     = [int(co2_tonnes * r) for r in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]]
    heat_z = []
    for w in wacc_range:
        row = []
        for c in co2_range:
            c_cost_s, _, _, _ = run_transition_risk(horizon, c, revenue, ebitda_margin)
            disc = np.array([(1/(1+w/100))**t for t in range(horizon+1)])
            b_npv = float(np.sum(base_fcf_arr * disc))
            a_npv = float(np.sum((base_fcf_arr - phys_main - c_cost_s) * disc))
            row.append(round((b_npv - a_npv) / b_npv * 100, 1) if b_npv else 0)
        heat_z.append(row)

    fig8 = go.Figure(go.Heatmap(
        z=heat_z,
        x=[f"{c//1000}k t" for c in co2_range],
        y=[f"{w}%" for w in wacc_range],
        colorscale=[
            [0.0, "#f0fdf4"], [0.15, "#fef9c3"],
            [0.4, "#fed7aa"], [0.7, "#fca5a5"], [1.0, "#7f1d1d"]
        ],
        text=[[f"{v:.1f}%" for v in row] for row in heat_z],
        texttemplate="%{text}", textfont=dict(size=11),
        showscale=True,
        colorbar=dict(title="Climate VaR %"),
    ))
    fig8.update_layout(
        height=320, template="plotly_white",
        xaxis_title="年碳排放量", yaxis_title="WACC",
        margin=dict(t=20, b=20, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig8, use_container_width=True)


# ════════════════════════════════════════════
#  TAB D — Summary Report
# ════════════════════════════════════════════
with tabD:
    st.markdown('<div class="sec-hdr">📋 气候 VaR 压力测试综合报告</div>', unsafe_allow_html=True)

    # Executive summary
    st.markdown("#### 执行摘要 Executive Summary")
    st.markdown(f"""
    本报告基于 **IPCC {'RCP 4.5 温和情景' if not use85 else 'RCP 8.5 高排放情景'}**，
    对资产 **{asset_name}** 在 **{2024}–{2024+horizon}** 年期间的综合气候风险进行量化分析。

    评估范围涵盖：(A) 物理风险所致的资产损耗与维修成本增加；
    (B) 碳税政策转型对营运利润的直接侵蚀；
    (C) 上述两类风险通过折现现金流模型转化为估值损失（Climate VaR）。
    """)

    # Three module summary
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-label">模块 A｜物理风险</div>
          <div style="font-size:1.1rem;font-weight:600;color:#0f172a;margin:.5rem 0">
            累计 EAL ¥{cum_phys:.0f}万
          </div>
          <div style="font-size:.83rem;color:#475569;line-height:1.7">
            • 风险类型：{', '.join(hazard_sel)}<br>
            • 终期 EAL：¥{phys_main[-1]:.1f} 万/年<br>
            • 较基期增幅：{(phys_main[-1]/phys_main[0]-1)*100:.0f}%<br>
            • 占重置成本：{phys_main[-1]/replace_cost*100:.2f}%/年
          </div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-label">模块 B｜转型风险</div>
          <div style="font-size:1.1rem;font-weight:600;color:#0f172a;margin:.5rem 0">
            累计碳税 ¥{cum_carbon:.0f}万
          </div>
          <div style="font-size:.83rem;color:#475569;line-height:1.7">
            • 2030碳价：$170/t（已锁定）<br>
            • 终期碳税：¥{carbon[-1]:.0f} 万/年<br>
            • EBITDA 侵蚀：{margin_hit:.1f} pp<br>
            • 调整后利润率：{adj_margins[-1]:.1f}%
          </div>
        </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-label">模块 C｜Climate VaR</div>
          <div style="font-size:1.1rem;font-weight:600;color:#ef4444;margin:.5rem 0">
            ¥{cvar/10000:.2f}亿 损失
          </div>
          <div style="font-size:.83rem;color:#475569;line-height:1.7">
            • 基准 NPV：¥{base_npv/10000:.2f} 亿<br>
            • 调整后 NPV：¥{adj_npv/10000:.2f} 亿<br>
            • VaR / NPV：{cvar_pct:.1f}%<br>
            • 风险评级：<span class="badge {risk_cls}">{risk_lbl}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Scenario comparison
    st.markdown("#### 情景对比总览")
    df_compare = pd.DataFrame({
        "指标": [
            "终期 EAL（万元/年）",
            "累计物理损失（万元）",
            "物理损失现值（万元）",
            "碳税现值（万元）",
            "Climate VaR（万元）",
            "VaR / 基准NPV（%）",
            "调整后EBITDA率（%）",
        ],
        "RCP 4.5（温和）": [
            round(phys45[-1], 1),
            round(float(np.sum(phys45)), 1),
            round(float(np.sum(phys45 * [(1/(1+wacc/100))**t for t in range(horizon+1)])), 1),
            round(float(np.sum(carbon * [(1/(1+wacc/100))**t for t in range(horizon+1)])), 1),
            round(base_npv - float(np.sum((base_fcf_arr - phys45 - carbon) * [(1/(1+wacc/100))**t for t in range(horizon+1)])), 1),
            round((base_npv - float(np.sum((base_fcf_arr - phys45 - carbon) * [(1/(1+wacc/100))**t for t in range(horizon+1)]))) / base_npv * 100, 1),
            round(adj_margins[-1], 1),
        ],
        "RCP 8.5（高排放）": [
            round(phys85[-1], 1),
            round(float(np.sum(phys85)), 1),
            round(float(np.sum(phys85 * [(1/(1+wacc/100))**t for t in range(horizon+1)])), 1),
            round(float(np.sum(carbon * [(1/(1+wacc/100))**t for t in range(horizon+1)])), 1),
            round(base_npv - float(np.sum((base_fcf_arr - phys85 - carbon) * [(1/(1+wacc/100))**t for t in range(horizon+1)])), 1),
            round((base_npv - float(np.sum((base_fcf_arr - phys85 - carbon) * [(1/(1+wacc/100))**t for t in range(horizon+1)]))) / base_npv * 100, 1),
            round(adj_margins[-1], 1),
        ],
    })
    st.dataframe(df_compare, use_container_width=True, hide_index=True)

    # Model assumptions
    st.markdown("#### 模型假设与参数")
    st.markdown(f"""
    <table class="assume-table">
      <tr><th>参数类别</th><th>参数名称</th><th>数值</th><th>数据来源</th></tr>
      <tr><td>物理风险</td><td>基期 EAL 比率（洪涝）</td><td>1.3% / 年</td><td>Swiss Re NatCat</td></tr>
      <tr><td>物理风险</td><td>RCP 8.5 强化因子</td><td>1.9×（2050）</td><td>IPCC AR6 WG2</td></tr>
      <tr><td>转型风险</td><td>2030 碳价目标</td><td>$170/吨</td><td>加拿大联邦政府</td></tr>
      <tr><td>转型风险</td><td>2050 碳价预测</td><td>$450/吨</td><td>NGFS Net Zero 2050</td></tr>
      <tr><td>估值</td><td>WACC</td><td>{wacc}%</td><td>用户输入</td></tr>
      <tr><td>估值</td><td>测试期限</td><td>{horizon} 年（至 {2024+horizon}）</td><td>用户输入</td></tr>
      <tr><td>汇率</td><td>USD/CNY</td><td>{usd_rmb}</td><td>用户输入</td></tr>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="insight">
      <strong>⚠️ 免责声明：</strong>
      本工具为投资组合气候压力测试示范模型，所有参数基于公开 IPCC、NGFS 及加拿大政府政策数据。
      实际风险评估需结合高精度地理空间数据（如 RMS、AIR）、企业碳足迹审计及法律合规意见。
      本输出不构成任何投资建议。
    </div>
    """, unsafe_allow_html=True)

    # Download button
    csv = pd.DataFrame({
        "年份": yr_range,
        "EAL_RCP45（万元）": phys45.round(2),
        "EAL_RCP85（万元）": phys85.round(2),
        "碳税成本（万元）": carbon.round(2),
        "调整后EBITDA率(%)": adj_margins.round(3),
        "基准FCF（万元）": base_fcf_arr.round(2),
        "调整后FCF（万元）": adj_fcf.round(2),
    }).to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇ 下载完整数据（CSV）",
        data=csv,
        file_name=f"climate_var_{asset_name}_{2024+horizon}.csv",
        mime="text/csv",
    )

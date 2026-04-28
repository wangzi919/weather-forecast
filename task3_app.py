"""
Task 3: Interactive Streamlit Web App with Folium Map
Reads ONLY from data.db.  Run with:  streamlit run task3_app.py
"""

import sqlite3
import os

import pandas as pd
import streamlit as st
import folium
import altair as alt
from streamlit_folium import st_folium

# ── Constants ─────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# Geographic coordinates for each region label stored in the DB
REGION_COORDS = {
    "北部地區":   [25.05, 121.55],
    "中部地區":   [24.10, 120.70],
    "南部地區":   [22.99, 120.22],
    "東北部地區": [24.70, 121.75],
    "東部地區":   [23.99, 121.60],
    "東南部地區": [22.75, 121.15],
}

# Region emoji icons for KPI cards
REGION_ICON = {
    "北部地區":   "🏙️",
    "中部地區":   "🏔️",
    "南部地區":   "🌴",
    "東北部地區": "🌊",
    "東部地區":   "🌿",
    "東南部地區": "☀️",
}


# ── Temperature helpers ───────────────────────────────────────────────────────

def temp_color(avg_temp: float) -> str:
    """CSS hex colour based on average temperature band."""
    if avg_temp < 20:
        return "#60a5fa"   # sky blue
    elif avg_temp < 25:
        return "#34d399"   # emerald
    elif avg_temp < 30:
        return "#fbbf24"   # amber
    else:
        return "#f87171"   # rose-red


def temp_color_dark(avg_temp: float) -> str:
    """Darker tint of temp_color for gradient backgrounds."""
    if avg_temp < 20:
        return "#1d4ed8"
    elif avg_temp < 25:
        return "#059669"
    elif avg_temp < 30:
        return "#d97706"
    else:
        return "#dc2626"


def temp_label(avg_temp: float) -> str:
    """平均氣溫區間標籤。"""
    if avg_temp < 20:
        return "偏涼"
    elif avg_temp < 25:
        return "舒適"
    elif avg_temp < 30:
        return "偏熱"
    else:
        return "高溫"


# ── Page configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="臺灣七日天氣預報",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Premium CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* ── Fonts ──────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], .stMarkdown, .stSelectbox, .stDataFrame {
        font-family: 'Noto Sans TC', 'Inter', sans-serif;
    }

    /* ── App background ─────────────────────────────────────── */
    .stApp {
        background: #080e1a;
        color: #e2e8f0;
    }

    /* Remove default top padding */
    .block-container { padding-top: 1.2rem !important; }

    /* ── Animated hero header ───────────────────────────────── */
    .hero-wrap {
        text-align: center;
        padding: 2.2rem 0 0.6rem;
        position: relative;
    }
    .hero-badge {
        display: inline-block;
        padding: 0.22rem 1rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        background: rgba(56,189,248,0.12);
        border: 1px solid rgba(56,189,248,0.3);
        color: #38bdf8;
        margin-bottom: 0.9rem;
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(120deg, #e0f2fe 0%, #38bdf8 40%, #818cf8 70%, #c084fc 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 4s linear infinite;
        margin-bottom: 0.45rem;
    }
    @keyframes shine {
        to { background-position: 200% center; }
    }
    .hero-sub {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 400;
        letter-spacing: 0.02em;
        margin-bottom: 0;
    }

    /* ── Divider ─────────────────────────────────────────────── */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(56,189,248,0.25), rgba(129,140,248,0.25), transparent);
        border: none;
        margin: 1.2rem 0;
    }

    /* ── KPI strip ───────────────────────────────────────────── */
    .kpi-card {
        border-radius: 18px;
        padding: 1rem 1.1rem 0.9rem;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: default;
        border: 1px solid rgba(255,255,255,0.07);
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.4);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 60%);
        pointer-events: none;
    }
    .kpi-icon   { font-size: 1.5rem; margin-bottom: 0.35rem; }
    .kpi-region { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em; opacity: 0.75; margin-bottom: 0.25rem; }
    .kpi-temp   { font-size: 1.55rem; font-weight: 700; letter-spacing: -0.03em; color: #f1f5f9; line-height: 1.1; }
    .kpi-label  { font-size: 0.68rem; font-weight: 600; margin-top: 0.45rem; padding: 0.15rem 0.55rem; border-radius: 999px; display: inline-block; }
    .kpi-date   { font-size: 0.65rem; color: rgba(255,255,255,0.35); margin-top: 0.3rem; }

    /* ── Section header ──────────────────────────────────────── */
    .sec-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.8rem;
    }
    .sec-icon {
        width: 30px; height: 30px;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
        background: rgba(56,189,248,0.15);
        border: 1px solid rgba(56,189,248,0.25);
        flex-shrink: 0;
    }
    .sec-title {
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #94a3b8;
    }

    /* ── Map hint card ────────────────────────────────────────── */
    .map-hint {
        background: rgba(56,189,248,0.06);
        border: 1px solid rgba(56,189,248,0.15);
        border-radius: 12px;
        padding: 0.65rem 1rem;
        font-size: 0.82rem;
        color: #7dd3fc;
        margin-bottom: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Dropdown override ────────────────────────────────────── */
    .stSelectbox > div > div {
        background: rgba(15,23,42,0.8) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-size: 0.92rem !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
    }
    label { color: #94a3b8 !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: 0.06em !important; }

    /* ── Stat pills ───────────────────────────────────────────── */
    .pills-row  { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; margin: 0.5rem 0 0.8rem; }
    .spill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.32rem 0.9rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .spill-cold { background: rgba(96,165,250,0.15); color: #93c5fd; border: 1px solid rgba(96,165,250,0.3); }
    .spill-hot  { background: rgba(248,113,113,0.15); color: #fca5a5; border: 1px solid rgba(248,113,113,0.3); }
    .spill-date { background: rgba(255,255,255,0.05); color: #64748b; border: 1px solid rgba(255,255,255,0.06);
                  font-size: 0.75rem; font-weight: 400; }

    /* ── Chart label ─────────────────────────────────────────── */
    .chart-label {
        font-size: 0.72rem; color: #475569; margin-bottom: 0.2rem; letter-spacing: 0.04em;
    }

    /* ── DataFrame ────────────────────────────────────────────── */
    .stDataFrame { border-radius: 14px !important; overflow: hidden !important; }
    .stDataFrame [data-testid="stDataFrameResizable"] { border-radius: 14px !important; }

    /* ── Footer ───────────────────────────────────────────────── */
    .footer {
        text-align: center;
        padding: 1.4rem 0 1rem;
        color: #334155;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
    }
    .footer a { color: #475569; text-decoration: none; }

    /* Hide Streamlit default header decorations */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_all_data() -> pd.DataFrame:
    """Load all rows from data.db into a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(
        "SELECT regionName, dataDate, mint, maxt "
        "FROM TemperatureForecasts ORDER BY regionName, dataDate",
        conn,
    )
    conn.close()
    df["dataDate"] = pd.to_datetime(df["dataDate"])
    return df


@st.cache_data(show_spinner=False)
def load_latest_per_region() -> dict[str, dict]:
    """Return {regionName: {mint, maxt, date}} for the most recent date per region."""
    conn = sqlite3.connect(DB_PATH)
    sql  = """
        SELECT regionName, dataDate, mint, maxt
        FROM   TemperatureForecasts
        WHERE  (regionName, dataDate) IN (
            SELECT regionName, MAX(dataDate) FROM TemperatureForecasts GROUP BY regionName
        )
    """
    df = pd.read_sql_query(sql, conn)
    conn.close()
    result = {}
    for _, row in df.iterrows():
        result[row["regionName"]] = {
            "mint": row["mint"],
            "maxt": row["maxt"],
            "date": row["dataDate"],
        }
    return result


# ── Map builder ───────────────────────────────────────────────────────────────

def build_taiwan_map(latest: dict[str, dict]) -> folium.Map:
    """
    Folium map on CartoDB dark tiles.
    Marker colour = temp_color(avg) so it follows the band rules:
      blue < 20°C | green 20-25 | yellow 25-30 | red ≥ 30
    """
    m = folium.Map(location=[23.8, 121.0], zoom_start=7, tiles="CartoDB dark_matter")

    # In-map legend
    legend_html = """
    <div style="position:fixed;bottom:18px;left:18px;z-index:9999;
                background:rgba(8,14,26,0.92);
                border:1px solid rgba(255,255,255,0.1);
                border-radius:14px;padding:12px 16px;
                font-family:'Noto Sans TC','Inter',sans-serif;
                font-size:11.5px;color:#cbd5e1;line-height:2;
                box-shadow:0 4px 20px rgba(0,0,0,0.5);">
      <div style="font-weight:700;font-size:12px;color:#e2e8f0;margin-bottom:2px">
        平均氣溫 色碼說明
      </div>
      <div style="height:1px;background:rgba(255,255,255,0.08);margin:6px 0 8px"></div>
      <span style="color:#60a5fa">&#9679;</span>&nbsp;&lt; 20°C 偏涼 &nbsp;
      <span style="color:#34d399">&#9679;</span>&nbsp;20–25°C 舒適<br>
      <span style="color:#fbbf24">&#9679;</span>&nbsp;25–30°C 偏熱 &nbsp;
      <span style="color:#f87171">&#9679;</span>&nbsp;&gt; 30°C 高溫
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    for region, coords in REGION_COORDS.items():
        info = latest.get(region, {})
        mint = info.get("mint", None)
        maxt = info.get("maxt", None)
        date = info.get("date", "")

        if mint is not None and maxt is not None:
            avg      = (mint + maxt) / 2
            color    = temp_color(avg)
            dark     = temp_color_dark(avg)
            band     = temp_label(avg)
            mint_str = f"{mint}°C"
            maxt_str = f"{maxt}°C"
            avg_str  = f"{avg:.1f}°C"
        else:
            color = dark = "#475569"
            band  = band = "—"
            mint_str = maxt_str = avg_str = "N/A"

        popup_html = f"""
        <div style="font-family:'Noto Sans TC','Inter',sans-serif;
                    min-width:190px;padding:10px 12px;
                    background:#0f172a;border-radius:12px;
                    border:1px solid rgba(255,255,255,0.1);">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            <div style="width:10px;height:10px;border-radius:50%;
                        background:{color};flex-shrink:0;
                        box-shadow:0 0 6px {color}88"></div>
            <b style="font-size:13px;color:{color}">{region}</b>
          </div>
          <div style="font-size:10px;color:#475569;margin-bottom:8px">{date}</div>
          <table style="width:100%;border-collapse:collapse;font-size:12px;color:#cbd5e1">
            <tr>
              <td style="padding:3px 0;color:#64748b">最低氣溫</td>
              <td style="text-align:right;font-weight:700;color:#60a5fa">{mint_str}</td>
            </tr>
            <tr>
              <td style="padding:3px 0;color:#64748b">最高氣溫</td>
              <td style="text-align:right;font-weight:700;color:#f87171">{maxt_str}</td>
            </tr>
            <tr style="border-top:1px solid rgba(255,255,255,0.06)">
              <td style="padding:5px 0 2px;color:#64748b">平均氣溫</td>
              <td style="text-align:right;font-weight:700;color:{color};padding-top:5px">{avg_str}</td>
            </tr>
          </table>
          <div style="margin-top:8px;padding:3px 8px;border-radius:6px;
                      background:{color}22;border:1px solid {color}44;
                      font-size:10px;font-weight:600;color:{color};
                      display:inline-block">{band}</div>
        </div>
        """

        # Circular DivIcon with glow border
        div_icon = folium.DivIcon(
            html=f"""
            <div style="
                width:32px; height:32px;
                background: radial-gradient(circle at 35% 35%, {color}, {dark});
                border: 2.5px solid rgba(255,255,255,0.7);
                border-radius: 50%;
                box-shadow: 0 0 10px {color}88, 0 3px 10px rgba(0,0,0,0.6);
                display: flex; align-items: center; justify-content: center;
                font-size: 14px; line-height: 1; cursor: pointer;
                transition: transform 0.15s;
            ">☁</div>
            """,
            icon_size=(32, 32),
            icon_anchor=(16, 16),
        )

        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"<b>{region}</b> &nbsp;|&nbsp; 均溫 {avg_str} &nbsp;({band})",
            icon=div_icon,
        ).add_to(m)

    return m


# ── Chart builder ─────────────────────────────────────────────────────────────

def build_altair_chart(df_region: pd.DataFrame) -> alt.Chart:
    """Build a premium dark-themed Altair line chart."""
    df_chart = df_region.copy()
    df_chart["dataDate"] = pd.to_datetime(df_chart["dataDate"])
    
    # Melt dataframe for Altair
    df_melt = pd.melt(
        df_chart, 
        id_vars=["dataDate"], 
        value_vars=["mint", "maxt"],
        var_name="Type", 
        value_name="Temperature"
    )
    
    # Map types to Chinese labels
    df_melt["Type"] = df_melt["Type"].map({"mint": "最低氣溫", "maxt": "最高氣溫"})

    # Create Altair chart with dark theme configuration
    chart = alt.Chart(df_melt).mark_line(point=alt.OverlayMarkDef(size=60, filled=True)).encode(
        x=alt.X('dataDate:T', title='日期', axis=alt.Axis(grid=False, labelColor='#94a3b8', titleColor='#94a3b8')),
        y=alt.Y('Temperature:Q', title='氣溫 (°C)', scale=alt.Scale(zero=False), axis=alt.Axis(gridColor='rgba(255,255,255,0.1)', labelColor='#94a3b8', titleColor='#94a3b8')),
        color=alt.Color('Type:N', scale=alt.Scale(domain=['最低氣溫', '最高氣溫'], range=['#60a5fa', '#f87171']), legend=alt.Legend(title=None, labelColor='#e2e8f0', orient='top')),
        tooltip=[
            alt.Tooltip('dataDate:T', title='日期', format='%Y-%m-%d'),
            alt.Tooltip('Type:N', title='類型'),
            alt.Tooltip('Temperature:Q', title='氣溫 (°C)')
        ]
    ).properties(
        height=280
    ).configure(
        background='transparent'
    ).configure_view(
        strokeWidth=0
    )
    
    return chart


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

def main():

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-wrap">
          <div class="hero-badge">🛰 中央氣象署開放資料 · CWA Open Data</div>
          <div class="hero-title">臺灣七日天氣預報</div>
          <div class="hero-sub">互動式地區氣溫探索儀表板 · 資料每日更新</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load data ─────────────────────────────────────────────────────────────
    if not os.path.exists(DB_PATH):
        st.error(f"⚠️ 找不到資料庫 `{DB_PATH}`，請先執行 **task2_store_db.py**。")
        st.stop()

    with st.spinner("正在從資料庫載入天氣資料 …"):
        df     = load_all_data()
        latest = load_latest_per_region()

    if df.empty:
        st.warning("資料庫為空，請先執行 task2_store_db.py 取得資料。")
        st.stop()

    all_regions = sorted(df["regionName"].unique().tolist())

    # ── KPI strip ─────────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    cols_kpi = st.columns(len(all_regions), gap="small")
    for i, region in enumerate(all_regions):
        info  = latest.get(region, {})
        mint  = info.get("mint", None)
        maxt  = info.get("maxt", None)
        date  = info.get("date", "—")
        icon  = REGION_ICON.get(region, "🌡️")

        if mint is not None and maxt is not None:
            avg   = (mint + maxt) / 2
            color = temp_color(avg)
            dark  = temp_color_dark(avg)
            band  = temp_label(avg)
            temp_display = f"{mint}° / {maxt}°"
        else:
            color = dark = "#475569"
            band  = "—"
            temp_display = "—"

        bg   = f"linear-gradient(135deg, {dark}33 0%, rgba(15,23,42,0.85) 100%)"
        bdr  = f"1px solid {color}44"
        with cols_kpi[i]:
            st.markdown(
                f"""
                <div class="kpi-card" style="background:{bg};border:{bdr};">
                  <div class="kpi-icon">{icon}</div>
                  <div class="kpi-region">{region}</div>
                  <div class="kpi-temp">{temp_display}</div>
                  <div class="kpi-label"
                       style="background:{color}22;color:{color};border:1px solid {color}44">
                    {band}
                  </div>
                  <div class="kpi-date">{date}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Main two-column layout ─────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    # ═══════════════════════
    # LEFT — Folium map
    # ═══════════════════════
    with left_col:
        st.markdown(
            '<div class="sec-header">'
            '<div class="sec-icon">📍</div>'
            '<span class="sec-title">互動式臺灣地圖</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="map-hint">💡 點擊地圖標記，查看該地區的詳細氣溫資訊</div>',
            unsafe_allow_html=True,
        )
        taiwan_map = build_taiwan_map(latest)
        with st.container():
            st_folium(taiwan_map, width="100%", height=490, returned_objects=[])

    # ═══════════════════════
    # RIGHT — Controls + chart + table
    # ═══════════════════════
    with right_col:
        st.markdown(
            '<div class="sec-header">'
            '<div class="sec-icon">📊</div>'
            '<span class="sec-title">地區七日氣溫趨勢</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Dropdown
        selected_region = st.selectbox(
            "選擇查詢地區",
            options=all_regions,
            index=0,
            label_visibility="visible",
        )

        df_region = df[df["regionName"] == selected_region].copy()
        info      = latest.get(selected_region, {})
        mint_v    = info.get("mint", None)
        maxt_v    = info.get("maxt", None)
        date_v    = info.get("date", "—")

        avg_v     = (mint_v + maxt_v) / 2 if (mint_v is not None and maxt_v is not None) else None
        color_v   = temp_color(avg_v) if avg_v is not None else "#64748b"
        band_v    = temp_label(avg_v) if avg_v is not None else "—"

        # Stat pills
        st.markdown(
            f"""
            <div class="pills-row">
              <span class="spill spill-cold">🧊 最低 &nbsp;<b>{mint_v if mint_v is not None else "—"}°C</b></span>
              <span class="spill spill-hot"> 🔥 最高 &nbsp;<b>{maxt_v if maxt_v is not None else "—"}°C</b></span>
              <span class="spill spill-date">📅 {date_v}</span>
              <span class="spill" style="background:{color_v}18;color:{color_v};border:1px solid {color_v}44;font-size:0.8rem">
                {band_v}
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Chart
        st.markdown(
            '<div class="chart-label">七日最低 / 最高氣溫走勢（°C）</div>',
            unsafe_allow_html=True,
        )
        
        # Use premium Altair chart to ensure dark theme and transparency
        chart = build_altair_chart(df_region)
        st.altair_chart(chart, use_container_width=True)

        # Data table
        st.markdown(
            '<div class="sec-header" style="margin-top:1.1rem">'
            '<div class="sec-icon" style="font-size:0.9rem">📋</div>'
            '<span class="sec-title">詳細資料表</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        display_df = df_region[["dataDate", "mint", "maxt"]].copy()
        display_df["dataDate"] = display_df["dataDate"].dt.strftime("%Y-%m-%d")
        display_df.columns = ["日期", "最低氣溫 (°C)", "最高氣溫 (°C)"]
        st.dataframe(
            display_df.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="footer">'
        '資料來源：中央氣象署（CWA）開放資料平臺 &nbsp;·&nbsp; '
        '以 Streamlit 與 Folium 建置 &nbsp;·&nbsp; 僅供學術用途'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

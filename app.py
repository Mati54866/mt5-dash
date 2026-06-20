"""
MetaTrader Trading Analysis Dashboard
A professional Streamlit app for analyzing MT4/MT5 backtest & forward trading data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
from dataclasses import dataclass
from typing import Optional, Tuple

# ─── Page Config ───
st.set_page_config(
    page_title="MT Trading Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
code, .stMetric .metric-value, .mono {
    font-family: 'JetBrains Mono', monospace;
}

/* Dark trading terminal aesthetic */
.stApp {
    background: #0a0e17;
}
section[data-testid="stSidebar"] {
    background: #0f1521;
    border-right: 1px solid #1a2332;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #111827 0%, #0f1521 100%);
    border: 1px solid #1e2d3d;
    border-radius: 12px;
    padding: 16px 20px;
    transition: border-color 0.2s;
}
div[data-testid="stMetric"]:hover {
    border-color: #3b82f6;
}
div[data-testid="stMetric"] label {
    color: #64748b !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background: #111827;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #1e2d3d;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94a3b8;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: #1e293b !important;
    color: #3b82f6 !important;
}

/* Headers */
h1, h2, h3 {
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
h1 { font-weight: 700 !important; letter-spacing: -0.02em; }

/* Upload area */
[data-testid="stFileUploader"] {
    border: 2px dashed #1e2d3d !important;
    border-radius: 12px;
    padding: 12px;
}
[data-testid="stFileUploader"]:hover {
    border-color: #3b82f6 !important;
}

/* Dataframes */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* Positive/Negative colors */
.positive { color: #22c55e; }
.negative { color: #ef4444; }

/* Score badge */
.score-badge {
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem; font-weight: 700;
    width: 90px; height: 90px; border-radius: 50%;
    border: 3px solid;
}
.score-excellent { background: #052e16; border-color: #22c55e; color: #22c55e; }
.score-good { background: #172554; border-color: #3b82f6; color: #3b82f6; }
.score-warning { background: #422006; border-color: #f59e0b; color: #f59e0b; }
.score-poor { background: #450a0a; border-color: #ef4444; color: #ef4444; }

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #1e2d3d, transparent);
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════
# DATA PARSING & PROCESSING
# ════════════════════════════════════════════════

def detect_and_parse_csv(uploaded_file) -> Optional[pd.DataFrame]:
    """Auto-detect MT4/MT5 CSV format and parse into standardized DataFrame."""
    try:
        content = uploaded_file.getvalue().decode("utf-8", errors="replace")
        lines = content.strip().split("\n")

        # Try different separators
        for sep in ["\t", ",", ";"]:
            try:
                df = pd.read_csv(io.StringIO(content), sep=sep, engine="python")
                if len(df.columns) >= 4:
                    break
            except Exception:
                continue
        else:
            st.error("Could not parse CSV. Check format.")
            return None

        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Rename common MT5 columns
        col_map = {
            "time": "open_time", "open_time": "open_time",
            "deal": "ticket", "ticket": "ticket", "order": "ticket",
            "symbol": "symbol",
            "type": "type", "direction": "type",
            "volume": "lots", "lots": "lots", "size": "lots",
            "price": "open_price", "open_price": "open_price",
            "s/l": "sl", "sl": "sl", "stop_loss": "sl",
            "t/p": "tp", "tp": "tp", "take_profit": "tp",
            "profit": "profit", "net_profit": "profit",
            "balance": "balance",
            "close_time": "close_time",
            "close_price": "close_price",
            "commission": "commission",
            "swap": "swap",
        }

        renamed = {}
        for col in df.columns:
            for key, val in col_map.items():
                if key in col and val not in renamed.values():
                    renamed[col] = val
                    break
        df = df.rename(columns=renamed)

        # Filter to trade rows (buy/sell)
        if "type" in df.columns:
            df["type"] = df["type"].astype(str).str.strip().str.lower()
            trade_mask = df["type"].str.contains("buy|sell", case=False, na=False)
            if trade_mask.any():
                df = df[trade_mask].copy()

        # Parse dates
        for dcol in ["open_time", "close_time"]:
            if dcol in df.columns:
                df[dcol] = pd.to_datetime(df[dcol], errors="coerce", dayfirst=False)

        # Ensure numeric columns
        for ncol in ["profit", "lots", "balance", "commission", "swap", "open_price", "close_price", "sl", "tp"]:
            if ncol in df.columns:
                df[ncol] = pd.to_numeric(df[ncol], errors="coerce")

        # Reconstruct balance if missing
        if "balance" not in df.columns and "profit" in df.columns:
            df["balance"] = df["profit"].cumsum()

        return df.reset_index(drop=True)

    except Exception as e:
        st.error(f"Parse error: {e}")
        return None


def compute_stats(df: pd.DataFrame) -> dict:
    """Compute comprehensive trading statistics."""
    if df is None or df.empty or "profit" not in df.columns:
        return {}

    profits = df["profit"].dropna()
    wins = profits[profits > 0]
    losses = profits[profits < 0]

    total_trades = len(profits)
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
    expectancy = profits.mean() if total_trades > 0 else 0
    profit_factor = wins.sum() / abs(losses.sum()) if len(losses) > 0 and losses.sum() != 0 else float("inf")

    # Equity curve & drawdown
    equity = profits.cumsum()
    running_max = equity.cummax()
    drawdown = equity - running_max
    max_dd = drawdown.min()
    peak_at_dd = running_max[drawdown.idxmin()] if len(drawdown) > 0 else 0
    relative_dd = (max_dd / peak_at_dd * 100) if peak_at_dd > 0 else 0

    # Sharpe-like ratio (daily returns proxy)
    if len(profits) > 1:
        sharpe = (profits.mean() / profits.std()) * np.sqrt(252) if profits.std() > 0 else 0
    else:
        sharpe = 0

    # Monthly stats
    monthly = {}
    if "close_time" in df.columns:
        df_with_time = df.dropna(subset=["close_time"])
        if not df_with_time.empty:
            df_with_time = df_with_time.copy()
            df_with_time["month"] = df_with_time["close_time"].dt.to_period("M")
            monthly = df_with_time.groupby("month")["profit"].sum().to_dict()

    return {
        "total_trades": total_trades,
        "net_profit": profits.sum(),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "relative_drawdown": relative_dd,
        "sharpe_ratio": sharpe,
        "best_trade": profits.max(),
        "worst_trade": profits.min(),
        "consecutive_wins": max_consecutive(profits > 0),
        "consecutive_losses": max_consecutive(profits < 0),
        "monthly": monthly,
        "equity_curve": equity.values,
        "drawdown_curve": drawdown.values,
    }


def max_consecutive(series: pd.Series) -> int:
    groups = series.ne(series.shift()).cumsum()
    counts = series.groupby(groups).sum()
    return int(counts.max()) if len(counts) > 0 else 0


def compute_robustness_score(bt_stats: dict, fw_stats: dict) -> dict:
    """Compare backtest vs forward and generate a robustness score."""
    scores = {}

    # Win rate deviation (weight: 20%)
    bt_wr, fw_wr = bt_stats.get("win_rate", 0), fw_stats.get("win_rate", 0)
    wr_dev = abs(bt_wr - fw_wr)
    scores["win_rate"] = {"score": max(0, 100 - wr_dev * 3), "weight": 0.20, "bt": bt_wr, "fw": fw_wr, "dev": wr_dev}

    # Profit factor deviation (weight: 20%)
    bt_pf = min(bt_stats.get("profit_factor", 0), 10)
    fw_pf = min(fw_stats.get("profit_factor", 0), 10)
    pf_dev = abs(bt_pf - fw_pf)
    scores["profit_factor"] = {"score": max(0, 100 - pf_dev * 15), "weight": 0.20, "bt": bt_pf, "fw": fw_pf, "dev": pf_dev}

    # Expectancy deviation (weight: 20%)
    bt_exp, fw_exp = bt_stats.get("expectancy", 0), fw_stats.get("expectancy", 0)
    exp_dev = abs(bt_exp - fw_exp) / max(abs(bt_exp), 1)
    scores["expectancy"] = {"score": max(0, 100 - exp_dev * 50), "weight": 0.20, "bt": bt_exp, "fw": fw_exp, "dev": exp_dev * 100}

    # Drawdown comparison (weight: 20%)
    bt_dd, fw_dd = abs(bt_stats.get("relative_drawdown", 0)), abs(fw_stats.get("relative_drawdown", 0))
    dd_dev = max(0, fw_dd - bt_dd)
    scores["drawdown"] = {"score": max(0, 100 - dd_dev * 3), "weight": 0.20, "bt": bt_dd, "fw": fw_dd, "dev": dd_dev}

    # Trade frequency consistency (weight: 20%)
    bt_trades, fw_trades = bt_stats.get("total_trades", 0), fw_stats.get("total_trades", 0)
    if bt_trades > 0:
        freq_ratio = fw_trades / bt_trades
        freq_score = max(0, 100 - abs(1 - freq_ratio) * 100)
    else:
        freq_score = 0
    scores["trade_frequency"] = {"score": freq_score, "weight": 0.20, "bt": bt_trades, "fw": fw_trades, "dev": abs(bt_trades - fw_trades)}

    total = sum(s["score"] * s["weight"] for s in scores.values())
    return {"total": round(total, 1), "details": scores}


def get_score_class(score):
    if score >= 80: return "score-excellent"
    if score >= 60: return "score-good"
    if score >= 40: return "score-warning"
    return "score-poor"


# ════════════════════════════════════════════════
# UI COMPONENTS
# ════════════════════════════════════════════════

def render_header():
    st.markdown("""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:8px;">
        <div style="font-size:2.2rem;">📊</div>
        <div>
            <h1 style="margin:0; font-size:1.8rem; line-height:1.2;">MT Trading Analyzer</h1>
            <p style="margin:0; color:#64748b; font-size:0.9rem;">MetaTrader Backtest & Forward Performance Dashboard</p>
        </div>
    </div>
    <div class="divider"></div>
    """, unsafe_allow_html=True)


def render_metrics_row(stats: dict, label: str = ""):
    if not stats:
        return
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Net Profit", f"${stats['net_profit']:,.2f}")
    c2.metric("Win Rate", f"{stats['win_rate']:.1f}%")
    c3.metric("Profit Factor", f"{stats['profit_factor']:.2f}" if stats['profit_factor'] < 100 else "∞")
    c4.metric("Expectancy", f"${stats['expectancy']:,.2f}")
    c5.metric("Max Drawdown", f"${stats['max_drawdown']:,.2f}")
    c6.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")


def render_equity_chart(stats: dict, label: str):
    if "equity_curve" not in stats or len(stats["equity_curve"]) == 0:
        return
    eq_df = pd.DataFrame({
        "Trade #": range(1, len(stats["equity_curve"]) + 1),
        "Equity": stats["equity_curve"],
        "Drawdown": stats["drawdown_curve"],
    })
    st.markdown(f"##### 📈 Equity Curve — {label}")
    st.area_chart(eq_df, x="Trade #", y="Equity", color="#3b82f6", use_container_width=True)
    st.markdown(f"##### 📉 Drawdown — {label}")
    st.area_chart(eq_df, x="Trade #", y="Drawdown", color="#ef4444", use_container_width=True)


def render_monthly_table(stats: dict):
    monthly = stats.get("monthly", {})
    if not monthly:
        st.info("No monthly data available (ensure close_time column exists).")
        return
    mdf = pd.DataFrame([
        {"Month": str(k), "Profit": round(v, 2)} for k, v in monthly.items()
    ])
    mdf["Cumulative"] = mdf["Profit"].cumsum().round(2)
    st.dataframe(mdf, use_container_width=True, hide_index=True)


def render_detailed_stats(stats: dict):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Trade Breakdown**")
        rows = {
            "Total Trades": stats["total_trades"],
            "Avg Win": f"${stats['avg_win']:,.2f}",
            "Avg Loss": f"${stats['avg_loss']:,.2f}",
            "Best Trade": f"${stats['best_trade']:,.2f}",
            "Worst Trade": f"${stats['worst_trade']:,.2f}",
        }
        st.dataframe(pd.DataFrame(rows.items(), columns=["Metric", "Value"]), hide_index=True, use_container_width=True)
    with c2:
        st.markdown("**Streaks & Risk**")
        rows2 = {
            "Max Consec. Wins": stats["consecutive_wins"],
            "Max Consec. Losses": stats["consecutive_losses"],
            "Relative Drawdown": f"{stats['relative_drawdown']:.2f}%",
            "Sharpe Ratio": f"{stats['sharpe_ratio']:.2f}",
            "Profit Factor": f"{stats['profit_factor']:.2f}" if stats['profit_factor'] < 100 else "∞",
        }
        st.dataframe(pd.DataFrame(rows2.items(), columns=["Metric", "Value"]), hide_index=True, use_container_width=True)


def render_robustness(rob: dict):
    total = rob["total"]
    cls = get_score_class(total)
    st.markdown(f"""
    <div style="text-align:center; margin:1rem 0;">
        <div class="score-badge {cls}">{total}</div>
        <p style="color:#94a3b8; margin-top:8px; font-size:0.85rem;">Robustness Score (0–100)</p>
    </div>
    """, unsafe_allow_html=True)

    details = rob["details"]
    rows = []
    for key, d in details.items():
        rows.append({
            "Metric": key.replace("_", " ").title(),
            "Backtest": f"{d['bt']:.2f}",
            "Forward": f"{d['fw']:.2f}",
            "Deviation": f"{d['dev']:.2f}",
            "Score": f"{d['score']:.0f}/100",
            "Weight": f"{d['weight']*100:.0f}%",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def generate_pdf_report(bt_stats, fw_stats, rob) -> bytes:
    """Generate a simple text-based PDF report using only standard library."""
    lines = []
    lines.append("=" * 60)
    lines.append("   MT TRADING ANALYSIS REPORT")
    lines.append(f"   Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)

    for label, stats in [("BACKTEST", bt_stats), ("FORWARD", fw_stats)]:
        if not stats:
            continue
        lines.append(f"\n{'─' * 40}")
        lines.append(f"  {label} PERFORMANCE")
        lines.append(f"{'─' * 40}")
        lines.append(f"  Net Profit:       ${stats['net_profit']:>12,.2f}")
        lines.append(f"  Win Rate:         {stats['win_rate']:>12.1f}%")
        lines.append(f"  Profit Factor:    {stats['profit_factor']:>12.2f}")
        lines.append(f"  Expectancy:       ${stats['expectancy']:>12,.2f}")
        lines.append(f"  Max Drawdown:     ${stats['max_drawdown']:>12,.2f}")
        lines.append(f"  Relative DD:      {stats['relative_drawdown']:>12.2f}%")
        lines.append(f"  Sharpe Ratio:     {stats['sharpe_ratio']:>12.2f}")
        lines.append(f"  Total Trades:     {stats['total_trades']:>12}")
        lines.append(f"  Best Trade:       ${stats['best_trade']:>12,.2f}")
        lines.append(f"  Worst Trade:      ${stats['worst_trade']:>12,.2f}")

    if rob:
        lines.append(f"\n{'─' * 40}")
        lines.append(f"  ROBUSTNESS SCORE: {rob['total']}/100")
        lines.append(f"{'─' * 40}")
        for key, d in rob["details"].items():
            lines.append(f"  {key.replace('_',' ').title():20s}  BT={d['bt']:.2f}  FW={d['fw']:.2f}  Score={d['score']:.0f}")

    lines.append(f"\n{'=' * 60}")
    lines.append("  End of Report")
    lines.append("=" * 60)

    return "\n".join(lines).encode("utf-8")


# ════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════

def main():
    render_header()

    # ─── Sidebar ───
    with st.sidebar:
        st.markdown("### 📁 Upload Data")
        st.markdown('<p style="color:#64748b;font-size:0.8rem;">Upload MT4/MT5 Strategy Tester CSV exports</p>', unsafe_allow_html=True)

        bt_file = st.file_uploader("Backtest CSV", type=["csv", "txt", "tsv"], key="bt")
        fw_file = st.file_uploader("Forward / Demo CSV", type=["csv", "txt", "tsv"], key="fw")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### ⚙️ Settings")
        initial_balance = st.number_input("Initial Balance ($)", value=10000.0, step=1000.0)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="color:#475569; font-size:0.75rem; line-height:1.5;">
            <b>Supported formats:</b><br>
            • MT5 Strategy Tester CSV<br>
            • MT4 Report exports<br>
            • Tab/comma/semicolon separated<br>
            <br>
            Columns auto-detected:<br>
            time, ticket, symbol, type, lots, profit, balance, etc.
        </div>
        """, unsafe_allow_html=True)

    # ─── Parse data ───
    bt_df = detect_and_parse_csv(bt_file) if bt_file else None
    fw_df = detect_and_parse_csv(fw_file) if fw_file else None

    if bt_df is not None and "balance" in bt_df.columns:
        bt_df["balance"] = bt_df["balance"] + initial_balance

    if fw_df is not None and "balance" in fw_df.columns:
        fw_df["balance"] = fw_df["balance"] + initial_balance

    bt_stats = compute_stats(bt_df) if bt_df is not None else {}
    fw_stats = compute_stats(fw_df) if fw_df is not None else {}

    # ─── No data state ───
    if bt_df is None and fw_df is None:
        st.markdown("""
        <div style="text-align:center; padding:80px 20px; color:#64748b;">
            <div style="font-size:4rem; margin-bottom:16px;">📂</div>
            <h2 style="color:#94a3b8 !important; margin-bottom:8px;">Upload Your Trading Data</h2>
            <p>Use the sidebar to upload MT4/MT5 backtest or forward test CSV files.<br>
            The app will automatically detect the format and generate your analysis.</p>
            <div style="margin-top:32px; display:flex; gap:24px; justify-content:center; flex-wrap:wrap;">
                <div style="background:#111827; border:1px solid #1e2d3d; border-radius:12px; padding:20px 28px; max-width:200px;">
                    <div style="font-size:1.5rem;">📈</div>
                    <p style="font-size:0.85rem; margin-top:8px;">Equity & drawdown curves</p>
                </div>
                <div style="background:#111827; border:1px solid #1e2d3d; border-radius:12px; padding:20px 28px; max-width:200px;">
                    <div style="font-size:1.5rem;">🔍</div>
                    <p style="font-size:0.85rem; margin-top:8px;">Backtest vs Forward comparison</p>
                </div>
                <div style="background:#111827; border:1px solid #1e2d3d; border-radius:12px; padding:20px 28px; max-width:200px;">
                    <div style="font-size:1.5rem;">🏆</div>
                    <p style="font-size:0.85rem; margin-top:8px;">Robustness scoring</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ─── Main Tabs ───
    tabs = st.tabs(["📊 Overview", "📈 Backtest", "🔄 Forward", "⚖️ Comparison", "📋 Raw Data"])

    # ─── OVERVIEW TAB ───
    with tabs[0]:
        if bt_stats:
            st.markdown("### Backtest Performance")
            render_metrics_row(bt_stats)
        if fw_stats:
            st.markdown("### Forward Performance")
            render_metrics_row(fw_stats)

        if bt_stats and fw_stats:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### 🏆 Robustness Score")
            rob = compute_robustness_score(bt_stats, fw_stats)
            render_robustness(rob)

            # PDF export
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            report_bytes = generate_pdf_report(bt_stats, fw_stats, rob)
            st.download_button(
                "📥 Download Report (TXT)",
                data=report_bytes,
                file_name=f"trading_report_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
            )

    # ─── BACKTEST TAB ───
    with tabs[1]:
        if bt_stats:
            render_metrics_row(bt_stats)
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            render_equity_chart(bt_stats, "Backtest")
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            render_detailed_stats(bt_stats)
            st.markdown("##### 📅 Monthly Breakdown")
            render_monthly_table(bt_stats)
        else:
            st.info("Upload a backtest CSV to see analysis.")

    # ─── FORWARD TAB ───
    with tabs[2]:
        if fw_stats:
            render_metrics_row(fw_stats)
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            render_equity_chart(fw_stats, "Forward")
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            render_detailed_stats(fw_stats)
            st.markdown("##### 📅 Monthly Breakdown")
            render_monthly_table(fw_stats)
        else:
            st.info("Upload a forward/demo CSV to see analysis.")

    # ─── COMPARISON TAB ───
    with tabs[3]:
        if bt_stats and fw_stats:
            st.markdown("### ⚖️ Backtest vs Forward Comparison")

            comp_data = {
                "Metric": ["Net Profit", "Win Rate", "Profit Factor", "Expectancy", "Max Drawdown", "Rel. Drawdown", "Sharpe", "Total Trades"],
                "Backtest": [
                    f"${bt_stats['net_profit']:,.2f}", f"{bt_stats['win_rate']:.1f}%",
                    f"{bt_stats['profit_factor']:.2f}", f"${bt_stats['expectancy']:,.2f}",
                    f"${bt_stats['max_drawdown']:,.2f}", f"{bt_stats['relative_drawdown']:.2f}%",
                    f"{bt_stats['sharpe_ratio']:.2f}", bt_stats['total_trades'],
                ],
                "Forward": [
                    f"${fw_stats['net_profit']:,.2f}", f"{fw_stats['win_rate']:.1f}%",
                    f"{fw_stats['profit_factor']:.2f}", f"${fw_stats['expectancy']:,.2f}",
                    f"${fw_stats['max_drawdown']:,.2f}", f"{fw_stats['relative_drawdown']:.2f}%",
                    f"{fw_stats['sharpe_ratio']:.2f}", fw_stats['total_trades'],
                ],
            }
            st.dataframe(pd.DataFrame(comp_data), hide_index=True, use_container_width=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

            # Side-by-side equity
            col1, col2 = st.columns(2)
            with col1:
                render_equity_chart(bt_stats, "Backtest")
            with col2:
                render_equity_chart(fw_stats, "Forward")

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### 🏆 Robustness Analysis")
            rob = compute_robustness_score(bt_stats, fw_stats)
            render_robustness(rob)
        else:
            st.info("Upload both backtest AND forward CSVs to see comparison.")

    # ─── RAW DATA TAB ───
    with tabs[4]:
        if bt_df is not None:
            st.markdown("##### Backtest Raw Data")
            st.dataframe(bt_df, use_container_width=True, height=300)
        if fw_df is not None:
            st.markdown("##### Forward Raw Data")
            st.dataframe(fw_df, use_container_width=True, height=300)


if __name__ == "__main__":
    main()
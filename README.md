# MT Trading Analyzer — Streamlit Dashboard

A professional MetaTrader (MT4/MT5) trading analysis dashboard built with Streamlit.

## Features

- **CSV Auto-Detection**: Handles MT4/MT5 Strategy Tester exports (tab, comma, semicolon separated)
- **Equity & Drawdown Curves**: Reconstructed from trade profit data
- **True Relative Drawdown**: Peak-to-trough calculation on equity curve
- **Monthly/Yearly Breakdown**: Profit aggregated by calendar month
- **Backtest vs Forward Comparison**: Side-by-side metric comparison
- **Robustness Score**: Weighted composite score (0–100) across 5 dimensions:
  - Win rate deviation (20%)
  - Profit factor deviation (20%)
  - Expectancy deviation (20%)
  - Drawdown comparison (20%)
  - Trade frequency consistency (20%)
- **Report Export**: Download a text summary of all stats

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

## CSV Format

The app auto-detects columns. Your CSV should include some of these:

| Column | Aliases Recognized |
|--------|-------------------|
| Time/Date | `time`, `open_time`, `close_time` |
| Ticket | `deal`, `ticket`, `order` |
| Type | `type`, `direction` (must contain "buy" or "sell") |
| Volume | `volume`, `lots`, `size` |
| Profit | `profit`, `net_profit` |
| Balance | `balance` (auto-reconstructed if missing) |
| Symbol | `symbol` |

## Usage

1. Export your MT5 backtest report as CSV from Strategy Tester
2. Export your forward/demo trade history as CSV
3. Upload both files via the sidebar
4. Explore the tabs: Overview, Backtest, Forward, Comparison, Raw Data
<!-- updated: 2026-06-06 -->

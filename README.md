# MT Trading Analyzer — Streamlit Dashboard 📊

A professional MetaTrader (MT4/MT5) trading analysis dashboard built with Streamlit.

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Quick Start](#quick-start)
5. [CSV Format](#csv-format)
6. [Usage](#usage)
7. [Project Structure](#project-structure)
8. [Author](#author)

## <a name="introduction">🤖 Introduction</a>

MT Trading Analyzer is a powerful Streamlit dashboard designed for MetaTrader traders to analyze their backtest and forward trading performance. It provides comprehensive metrics, visualizations, and comparison tools to evaluate trading strategies.

## <a name="features">🔋 Features</a>

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

## <a name="tech-stack">⚙️ Tech Stack</a>

- **Streamlit** - Dashboard framework
- **Python** - Core language
- **Pandas** - Data manipulation
- **Plotly** - Interactive visualizations
- **NumPy** - Numerical computations

## <a name="quick-start">🤸 Quick Start</a>

### Prerequisites

Make sure you have the following installed:
- [Python](https://www.python.org/) (3.8 or higher)
- [pip](https://pip.pypa.io/) (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/Mati54866/mt-trading-analyzer.git
cd mt-trading-analyzer

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="ETF Performance Analyzer", layout="wide")

# Custom styling
st.markdown("""
<style>
    .metric {font-size: 1.2rem !important;}
    .stDataFrame {font-size: 14px;}
    .highlight {background-color: #fffacd; padding: 8px; border-radius: 5px;}
    .positive {color: #008000;}
    .negative {color: #FF0000;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 ETF Performance Analyzer")

# Load ETF list
etf_list = [
    "MAFANG.NS", "FMCGIETF.NS", "MOGSEC.NS", "TATAGOLD.NS", "GOLDIETF.NS",
    "GOLDCASE.NS", "HDFCGOLD.NS", "GOLD1.NS", "AXISGOLD.NS", "GOLD360.NS",
    # ... (add all your ETFs here)
    "IT.NS", "ITETFADD.NS", "HDFCPVTBAN.NS", "HDFCQUAL.NS", "MONQ50.NS"
]

# Date range selection
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365*3))
with col2:
    end_date = st.date_input("End Date", datetime.now())

# Analysis parameters
st.sidebar.header("Analysis Parameters")
benchmark = st.sidebar.selectbox("Benchmark Index", ["^NSEI", "^NSEMDCP50", "NIFTY_BANK.NS"])
risk_free_rate = st.sidebar.slider("Risk-Free Rate (% p.a.)", 0.0, 10.0, 5.0, 0.1)
min_trading_days = st.sidebar.slider("Minimum Trading Days", 50, 500, 200, 10)

# Function to fetch data
@st.cache_data(ttl=3600)
def get_etf_data(etfs, start, end):
    data = yf.download(etfs, start=start, end=end, group_by='ticker')
    return data

# Function to calculate metrics
def calculate_metrics(price_data):
    returns = price_data.pct_change().dropna()
    cum_returns = (1 + returns).cumprod() - 1
    
    # Annualized returns
    annual_returns = (1 + returns.mean())**252 - 1
    
    # Risk metrics
    annual_volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = (annual_returns - risk_free_rate/100) / annual_volatility
    
    # Max drawdown
    rolling_max = price_data.cummax()
    daily_drawdown = price_data / rolling_max - 1
    max_drawdown = daily_drawdown.cummin()
    
    return {
        'Annual Return': annual_returns,
        'Annual Volatility': annual_volatility,
        'Sharpe Ratio': sharpe_ratio,
        'Max Drawdown': max_drawdown.iloc[-1],
        'CAGR': (price_data.iloc[-1]/price_data.iloc[0])**(252/len(price_data)) - 1
    }

try:
    # Fetch data
    with st.spinner("Fetching ETF data from Yahoo Finance..."):
        etf_data = get_etf_data(etf_list, start_date, end_date)
    
    # Process data
    performance_data = []
    valid_etfs = []
    
    for etf in etf_list:
        try:
            if etf in etf_data:
                closes = etf_data[etf]['Close']
                if len(closes) > min_trading_days:
                    metrics = calculate_metrics(closes)
                    metrics['ETF'] = etf
                    performance_data.append(metrics)
                    valid_etfs.append(etf)
        except Exception as e:
            st.warning(f"Couldn't process {etf}: {str(e)}")
    
    if not performance_data:
        st.error("No valid ETF data found for the selected period.")
        st.stop()
    
    # Create performance DataFrame
    perf_df = pd.DataFrame(performance_data)
    perf_df.set_index('ETF', inplace=True)
    
    # Add benchmark data
    benchmark_data = yf.download(benchmark, start=start_date, end=end_date)['Close']
    bench_metrics = calculate_metrics(benchmark_data)
    bench_metrics['ETF'] = benchmark
    bench_df = pd.DataFrame([bench_metrics]).set_index('ETF')
    perf_df = pd.concat([perf_df, bench_df])
    
    # Display results
    st.subheader("📈 Performance Metrics")
    
    # Top performers selection
    metric_options = ['CAGR', 'Sharpe Ratio', 'Annual Volatility', 'Max Drawdown']
    sort_metric = st.selectbox("Sort by metric", metric_options, index=0)
    top_n = st.slider("Number of ETFs to display", 5, 50, 20)
    
    # Sort and display
    sorted_df = perf_df.sort_values(by=sort_metric, ascending=False if sort_metric != 'Max Drawdown' else True)
    display_df = sorted_df.head(top_n)
    
    # Formatting
    format_dict = {
        'Annual Return': '{:.1%}',
        'Annual Volatility': '{:.1%}',
        'Sharpe Ratio': '{:.2f}',
        'Max Drawdown': '{:.1%}',
        'CAGR': '{:.1%}'
    }
    
    st.dataframe(display_df.style.format(format_dict).applymap(
        lambda x: 'color: green' if isinstance(x, (int, float)) and x > 0 else 'color: red', 
        subset=['Annual Return', 'CAGR', 'Sharpe Ratio']))
    
    # Visualizations
    st.subheader("📊 Performance Comparison")
    
    # Select ETFs to compare
    selected_etfs = st.multiselect(
        "Select ETFs for detailed comparison",
        valid_etfs,
        default=valid_etfs[:3] if len(valid_etfs) >= 3 else valid_etfs
    )
    
    if selected_etfs:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Normalized price chart
        for etf in selected_etfs + [benchmark]:
            if etf in etf_data:
                prices = etf_data[etf]['Close'] if etf != benchmark else benchmark_data
                norm_prices = prices / prices.iloc[0]
                ax1.plot(norm_prices, label=etf)
        
        ax1.set_title("Normalized Price Comparison")
        ax1.set_ylabel("Growth (1 = Initial Investment)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Drawdown chart
        for etf in selected_etfs:
            if etf in etf_data:
                prices = etf_data[etf]['Close']
                rolling_max = prices.cummax()
                drawdown = (prices / rolling_max) - 1
                ax2.plot(drawdown, label=etf)
        
        ax2.set_title("Drawdown Analysis")
        ax2.set_ylabel("Drawdown from Peak")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        st.pyplot(fig)
    
    # Correlation matrix
    st.subheader("🧩 Correlation Matrix")
    
    # Create returns DataFrame
    returns_df = pd.DataFrame()
    for etf in selected_etfs:
        if etf in etf_data:
            returns_df[etf] = etf_data[etf]['Close'].pct_change().dropna()
    
    if not returns_df.empty:
        corr_matrix = returns_df.corr()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        cax = ax.matshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
        fig.colorbar(cax)
        
        ax.set_xticks(np.arange(len(corr_matrix.columns)))
        ax.set_yticks(np.arange(len(corr_matrix.columns)))
        ax.set_xticklabels(corr_matrix.columns, rotation=90)
        ax.set_yticklabels(corr_matrix.columns)
        
        st.pyplot(fig)
    
    # Recommendations
    st.subheader("💡 ETF Recommendations")
    
    # Best by category
    categories = {
        "Best Returns": "CAGR",
        "Best Risk-Adjusted": "Sharpe Ratio",
        "Lowest Volatility": "Annual Volatility",
        "Best Drawdown Recovery": "Max Drawdown"
    }
    
    cols = st.columns(len(categories))
    for i, (title, metric) in enumerate(categories.items()):
        ascending = metric in ["Annual Volatility", "Max Drawdown"]
        best = perf_df[perf_df.index != benchmark].sort_values(metric, ascending=ascending).head(1)
        
        with cols[i]:
            st.metric(
                label=title,
                value=best.index[0],
                delta=f"{best[metric].values[0]:.1%}" if '%' in format_dict[metric] else f"{best[metric].values[0]:.2f}"
            )
    
    # Detailed analysis
    with st.expander("🔍 Analysis Methodology"):
        st.markdown("""
        **Metrics Calculated:**
        1. **CAGR**: Compound Annual Growth Rate
        2. **Annualized Volatility**: Standard deviation of daily returns × √252
        3. **Sharpe Ratio**: (Return - Risk-Free Rate) / Volatility
        4. **Max Drawdown**: Largest peak-to-trough decline
        
        **Recommendation Logic:**
        - Top performers selected based on each metric
        - Benchmark comparison helps identify relative performance
        - Correlation matrix helps identify diversification opportunities
        """)
    
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.stop()

# Additional analysis
st.markdown("""
<div class="highlight">
<strong>📌 ETF Selection Tips:</strong>
1. <strong>Diversify</strong> across uncorrelated ETFs (check correlation matrix)
2. Consider <strong>risk-adjusted returns</strong> (Sharpe Ratio) not just absolute returns
3. Check <strong>drawdowns</strong> to understand worst-case scenarios
4. Compare to <strong>benchmark</strong> to evaluate relative performance
5. Look for <strong>consistent performers</strong> across multiple metrics
</div>
""", unsafe_allow_html=True)

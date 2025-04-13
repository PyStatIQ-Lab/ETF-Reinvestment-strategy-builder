import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="ETF Compounding Simulator", layout="wide")

# Custom styling
st.markdown("""
<style>
    .metric {font-size: 1.2rem !important;}
    .stSlider>div>div>div>div {background: #4f8bf9;}
    .stDataFrame {font-size: 14px;}
    .highlight {background-color: #fffacd; padding: 8px; border-radius: 5px;}
    .tax-box {border-left: 4px solid #4f8bf9; padding-left: 1rem; margin: 1rem 0;}
    .etf-card {border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🚀 ETF Compounding Strategy Simulator")

# List of ETFs
etf_list = [
    "MAFANG.NS", "FMCGIETF.NS", "MOGSEC.NS", "TATAGOLD.NS", "GOLDIETF.NS",
    "GOLDCASE.NS", "HDFCGOLD.NS", "GOLD1.NS", "AXISGOLD.NS", "GOLD360.NS",
    "ABGSEC.NS", "SETFGOLD.NS", "GOLDBEES.NS", "LICMFGOLD.NS", "QGOLDHALF.NS",
    "GSEC5IETF.NS", "IVZINGOLD.NS", "GOLDSHARE.NS", "BSLGOLDETF.NS", "LICNFNHGP.NS",
    "GOLDETFADD.NS", "UNIONGOLD.NS", "CONSUMBEES.NS", "SDL26BEES.NS", "AXISCETF.NS",
    "GROWWGOLD.NS", "GOLDETF.NS", "MASPTOP50.NS", "SETF10GILT.NS", "EBBETF0433.NS",
    "NV20BEES.NS", "BBNPPGOLD.NS", "CONSUMIETF.NS", "AUTOBEES.NS", "BSLSENETFG.NS",
    "LTGILTBEES.NS", "AUTOIETF.NS", "AXISBPSETF.NS", "GILT5YBEES.NS", "LIQUIDCASE.NS",
    "GROWWLIQID.NS", "GSEC10YEAR.NS", "LIQUIDBETF.NS", "LIQUIDADD.NS", "LIQUID1.NS",
    "HDFCLIQUID.NS", "MOLOWVOL.NS", "AONELIQUID.NS", "CASHIETF.NS", "LIQUIDPLUS.NS",
    "LIQUIDSHRI.NS", "ABSLLIQUID.NS", "LIQUIDETF.NS", "CONS.NS", "LIQUIDSBI.NS",
    "LIQUID.NS", "EGOLD.NS", "BBNPNBETF.NS", "LIQUIDIETF.NS", "IVZINNIFTY.NS",
    "GSEC10ABSL.NS", "LIQUIDBEES.NS", "EBBETF0430.NS", "SBIETFCON.NS", "MON100.NS",
    "LICNETFGSC.NS", "GSEC10IETF.NS", "QUAL30IETF.NS", "SILVRETF.NS", "LICNETFSEN.NS",
    "HDFCLOWVOL.NS", "EBANKNIFTY.NS", "LOWVOLIETF.NS", "EBBETF0431.NS", "TOP100CASE.NS",
    "NIFTYQLITY.NS", "HDFCGROWTH.NS", "SHARIABEES.NS", "BBETF0432.NS"
]

# Input parameters
with st.sidebar:
    st.header("💰 Investment Parameters")
    initial = st.number_input("Initial Capital (₹)", 100000, 10000000, 100000, 10000)
    months = st.slider("Investment Tenure (Months)", 1, 120, 60, 1)
    monthly_investment = st.number_input("Monthly SIP Amount (₹)", 0, 100000, 0, 1000)
    
    st.header("📈 ETF Selection")
    analysis_period = st.slider("Historical Analysis Period (Years)", 1, 10, 5)
    risk_appetite = st.select_slider("Risk Appetite", ["Low", "Medium", "High"])
    
    st.header("🧾 Tax Parameters")
    investor_type = st.selectbox("Investor Type", [
        "Individual (Equity: 10% LTCG, Debt: Slab)", 
        "Pvt Ltd (25% flat)", 
        "Custom"
    ])
    
    if investor_type == "Custom":
        equity_tax = st.slider("Equity LTCG Tax (%)", 0.0, 30.0, 10.0, 0.1)
        debt_tax = st.slider("Debt LTCG Tax (%)", 0.0, 30.0, 20.0, 0.1)
    else:
        equity_tax = 10.0 if "Individual" in investor_type else 25.0
        debt_tax = 20.0 if "Individual" in investor_type else 25.0

# Function to analyze ETF performance
def analyze_etf(etf_symbol, years):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*years)
        
        data = yf.download(etf_symbol, start=start_date, end=end_date)
        if len(data) < 10:  # Minimum data points
            return None
            
        data['Daily_Return'] = data['Adj Close'].pct_change()
        annual_return = data['Daily_Return'].mean() * 252 * 100
        annual_volatility = data['Daily_Return'].std() * np.sqrt(252) * 100
        sharpe_ratio = annual_return / annual_volatility if annual_volatility != 0 else 0
        
        return {
            'Symbol': etf_symbol,
            'Annual Return (%)': annual_return,
            'Volatility (%)': annual_volatility,
            'Sharpe Ratio': sharpe_ratio,
            'Last Price': data['Adj Close'].iloc[-1]
        }
    except:
        return None

# Analyze ETFs
st.subheader("🔍 Analyzing ETFs...")
with st.spinner("Fetching historical data and calculating performance metrics..."):
    etf_data = []
    for etf in etf_list:
        result = analyze_etf(etf, analysis_period)
        if result:
            etf_data.append(result)
    
    if not etf_data:
        st.error("No ETF data could be fetched. Please try again later.")
        st.stop()
    
    etf_df = pd.DataFrame(etf_data)
    
    # Filter based on risk appetite
    if risk_appetite == "Low":
        etf_df = etf_df[etf_df['Volatility (%)'] < 15].sort_values('Sharpe Ratio', ascending=False)
    elif risk_appetite == "Medium":
        etf_df = etf_df[(etf_df['Volatility (%)'] >= 15) & (etf_df['Volatility (%)'] < 25)].sort_values('Sharpe Ratio', ascending=False)
    else:
        etf_df = etf_df[etf_df['Volatility (%)'] >= 25].sort_values('Sharpe Ratio', ascending=False)
    
    top_etfs = etf_df.head(5)

# Display recommended ETFs
st.subheader("🏆 Top Recommended ETFs")
cols = st.columns(len(top_etfs))
for idx, (_, row) in enumerate(top_etfs.iterrows()):
    with cols[idx]:
        st.markdown(f"""
        <div class="etf-card">
            <h4>{row['Symbol']}</h4>
            <p>Return: {row['Annual Return (%)']:.1f}%</p>
            <p>Volatility: {row['Volatility (%)']:.1f}%</p>
            <p>Sharpe: {row['Sharpe Ratio']:.2f}</p>
            <p>Price: ₹{row['Last Price']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

# Let user select ETF or use top performer
selected_etf = st.selectbox("Select ETF for simulation", top_etfs['Symbol'], index=0)
selected_data = top_etfs[top_etfs['Symbol'] == selected_etf].iloc[0]

# Get full historical data for simulation
@st.cache_data
def get_full_history(etf_symbol):
    data = yf.download(etf_symbol)
    return data['Adj Close']

try:
    etf_prices = get_full_history(selected_etf)
    if len(etf_prices) < 30:  # At least 1 month of data
        raise ValueError("Insufficient data")
except:
    st.error(f"Could not fetch sufficient historical data for {selected_etf}")
    st.stop()

# Calculate monthly returns
monthly_prices = etf_prices.resample('M').last()
monthly_returns = monthly_prices.pct_change().dropna()

# Simulation function
def run_simulation(initial, monthly_investment, months, monthly_returns):
    investment_values = []
    current_value = initial
    dividends = 0
    
    for i in range(min(months, len(monthly_returns))):
        monthly_return = monthly_returns.iloc[i]
        current_value *= (1 + monthly_return)
        current_value += monthly_investment
        investment_values.append(current_value)
        
        # Simulate dividend (1% annual yield paid quarterly)
        if i % 3 == 0:
            dividend = current_value * 0.0025  # 1%/4
            dividends += dividend
            current_value += dividend
    
    final_value = current_value
    total_invested = initial + (monthly_investment * months)
    capital_gain = final_value - total_invested - dividends
    return investment_values, final_value, total_invested, capital_gain, dividends

# Run simulation
investment_values, final_value, total_invested, capital_gain, dividends = run_simulation(
    initial, monthly_investment, months, monthly_returns
)

# Tax Calculation
holding_years = months / 12
is_equity = True  # Assuming all these ETFs are equity-oriented

if is_equity:
    if holding_years >= 1:
        tax_rate = equity_tax  # LTCG
    else:
        tax_rate = 15.0 if "Individual" in investor_type else 25.0  # STCG
else:
    if holding_years >= 3:
        tax_rate = debt_tax  # LTCG with indexation
    else:
        tax_rate = (30.0 if "Individual" in investor_type else 25.0)  # STCG as per slab

capital_gain_tax = capital_gain * (tax_rate / 100)
dividend_tax = dividends * (10/100)  # Dividend distribution tax (simplified)
total_tax = capital_gain_tax + dividend_tax

# Final Returns
net_value = final_value - total_tax
net_gain = net_value - total_invested
annualized_return = ((net_value / total_invested) ** (12/months) - 1) * 100

# Display results
st.subheader("📊 Investment Simulation Results")
col1, col2, col3 = st.columns(3)
col1.metric("Total Invested", f"₹{total_invested:,.0f}")
col2.metric("Final Portfolio Value", f"₹{final_value:,.0f}")
col3.metric("Net Gain Before Tax", f"₹{final_value - total_invested:,.0f}")

st.subheader("🧾 Tax Liability")
with st.container():
    col1, col2 = st.columns(2)
    col1.markdown(f"""
    <div class="tax-box">
        <h4>Capital Gains Tax</h4>
        <p>Gain: ₹{capital_gain:,.0f}<br>
        Holding: {holding_years:.1f} years<br>
        Tax Rate: {tax_rate}%<br>
        <strong>Tax: ₹{capital_gain_tax:,.0f}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
    <div class="tax-box">
        <h4>Dividend Tax</h4>
        <p>Dividends: ₹{dividends:,.0f}<br>
        Tax Rate: 10%<br>
        <strong>Tax: ₹{dividend_tax:,.0f}</strong></p>
    </div>
    """, unsafe_allow_html=True)

st.subheader("💸 Final Returns")
col1, col2, col3 = st.columns(3)
col1.metric("Total Value", f"₹{final_value:,.0f}")
col2.metric("Net After Tax", f"₹{net_value:,.0f}")
col3.metric("Annualized Return", f"{annualized_return:.1f}%")

# Visualizations
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(range(1, len(investment_values)+1), investment_values, label="Portfolio Value", color='green')
ax.set_title(f"{selected_etf} Investment Growth")
ax.set_xlabel("Months")
ax.set_ylabel("Portfolio Value (₹)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# Detailed Breakdown
with st.expander("📝 Detailed Calculation Methodology"):
    st.markdown(f"""
    **ETF Growth Calculation:**
    - Initial Investment: ₹{initial:,.0f}
    - Monthly SIP: ₹{monthly_investment:,.0f}
    - Total Invested: ₹{total_invested:,.0f}
    - Historical Annual Return: {selected_data['Annual Return (%)']:.1f}%
    - Final Value after {months} months: ₹{final_value:,.0f}
    
    **Tax Treatment:**
    - ETF Type: {'Equity' if is_equity else 'Debt'}
    - Holding Period: {holding_years:.1f} years
    - Capital Gains Tax: {tax_rate}% on ₹{capital_gain:,.0f} = ₹{capital_gain_tax:,.0f}
    - Dividend Tax: 10% on ₹{dividends:,.0f} = ₹{dividend_tax:,.0f}
    
    **Net Position:**
    - Final Portfolio Value: ₹{final_value:,.0f}
    - Less: Taxes ₹{total_tax:,.0f}
    - Net Value: ₹{net_value:,.0f}
    - Annualized Return: {annualized_return:.1f}%
    """)

st.markdown(f"""
<div class="highlight">
<strong>💡 Key Strategy Benefits:</strong>
1. <strong>Compounding Magic:</strong> Reinvesting dividends and regular SIPs accelerate growth
2. <strong>Tax Efficiency:</strong> ETFs generally have lower expense ratios and tax benefits
3. <strong>Diversification:</strong> Single ETF can provide exposure to entire sector/index
4. <strong>Automatic Rebalancing:</strong> Index ETFs automatically maintain optimal allocations

<strong>⚠️ Risk Factors:</strong>
1. Past performance doesn't guarantee future returns
2. Market volatility can affect portfolio value
3. Tax laws may change affecting LTCG benefits
4. Dividend yields may vary from projections
</div>
""", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from numpy_financial import pmt, ipmt, ppmt

# Set page config
st.set_page_config(page_title="ETF Leveraged Compounding Simulator", layout="wide")

# Custom styling
st.markdown("""
<style>
    .metric {font-size: 1.2rem !important;}
    .stSlider>div>div>div>div {background: #4f8bf9;}
    .stDataFrame {font-size: 14px;}
    .highlight {background-color: #fffacd; padding: 8px; border-radius: 5px;}
    .tax-box {border-left: 4px solid #4f8bf9; padding-left: 1rem; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🚀 ETF Leveraged Compounding Strategy Simulator")

# Input parameters
with st.sidebar:
    st.header("💰 Investment Parameters")
    initial = st.number_input("Initial Capital (₹)", 100000, 10000000, 100000, 10000)
    leverage = st.slider("Leverage Ratio", 1.0, 3.0, 1.0, 0.1)
    loan_rate = st.slider("Loan Interest Rate (% p.a.)", 1.0, 20.0, 10.0, 0.1)
    months = st.slider("Investment Tenure (Months)", 1, 120, 60, 1)
    
    st.header("📈 ETF Parameters")
    etf_type = st.selectbox("ETF Type", [
        "Equity ETF (12% avg return)", 
        "Debt ETF (8% avg return)", 
        "Hybrid ETF (10% avg return)",
        "Custom"
    ])
    
    if etf_type == "Custom":
        etf_return = st.slider("Expected ETF Return (% p.a.)", 1.0, 30.0, 12.0, 0.1)
    else:
        etf_return = 12.0 if "Equity" in etf_type else (8.0 if "Debt" in etf_type else 10.0)
    
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

# Calculations
borrowed = initial * (leverage - 1) if leverage > 1 else 0
total_investment = initial + borrowed

# Loan EMI Calculation (if applicable)
if borrowed > 0:
    rate_per_period = loan_rate / 12 / 100
    emi = -pmt(rate_per_period, months, borrowed)
    
    # Generate loan amortization schedule
    loan_schedule = []
    remaining_principal = borrowed
    for month in range(1, months + 1):
        interest_payment = -ipmt(rate_per_period, month, months, borrowed)
        principal_payment = -ppmt(rate_per_period, month, months, borrowed)
        remaining_principal -= principal_payment
        loan_schedule.append({
            "Month": month,
            "EMI": emi,
            "Principal": principal_payment,
            "Interest": interest_payment,
            "Remaining Principal": remaining_principal
        })
    loan_df = pd.DataFrame(loan_schedule)
    total_loan_interest = loan_df["Interest"].sum()
else:
    loan_df = pd.DataFrame()
    total_loan_interest = 0

# ETF Growth Calculation
monthly_return = etf_return / 12 / 100
etf_values = []
dividends_received = 0

for month in range(1, months + 1):
    if month == 1:
        current_value = total_investment * (1 + monthly_return)
    else:
        current_value = etf_values[-1] * (1 + monthly_return)
    
    # Simulate quarterly dividend (1% of current value every 3 months)
    if month % 3 == 0:
        dividend = current_value * 0.01
        dividends_received += dividend
        current_value += dividend  # Reinvest dividend
    
    etf_values.append(current_value)

final_etf_value = etf_values[-1]
capital_gain = final_etf_value - total_investment - dividends_received

# Tax Calculation
holding_years = months / 12
is_equity = "Equity" in etf_type or etf_return >= 10  # Arbitrary threshold for equity-like returns

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
dividend_tax = dividends_received * (10/100)  # Dividend distribution tax (simplified)

if "Pvt Ltd" in investor_type:
    loan_interest_deduction = total_loan_interest * 0.25
else:
    loan_interest_deduction = 0

total_tax = capital_gain_tax + dividend_tax - loan_interest_deduction

# Final Returns
net_value = final_etf_value - (borrowed + total_loan_interest if borrowed > 0 else 0) - total_tax
net_gain = net_value - initial
annualized_return = ((net_value / initial) ** (12/months) - 1) * 100

# Display results
st.subheader("📊 Investment Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Invested", f"₹{total_investment:,.0f}", 
            f"Leverage: {leverage}x" if leverage > 1 else "No leverage")
col2.metric("Final ETF Value", f"₹{final_etf_value:,.0f}", 
            f"{etf_return}% p.a.")
col3.metric("Capital Gain", f"₹{capital_gain:,.0f}", 
            f"{dividends_received:,.0f} dividends")

if borrowed > 0:
    st.subheader("🏦 Loan Details")
    col1, col2, col3 = st.columns(3)
    col1.metric("Loan Amount", f"₹{borrowed:,.0f}")
    col2.metric("Total Interest Paid", f"₹{total_loan_interest:,.0f}", 
                f"{loan_rate}% p.a.")
    col3.metric("Effective Cost", f"₹{borrowed + total_loan_interest:,.0f}")

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
        <p>Dividends: ₹{dividends_received:,.0f}<br>
        Tax Rate: 10%<br>
        <strong>Tax: ₹{dividend_tax:,.0f}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    if "Pvt Ltd" in investor_type:
        st.markdown(f"""
        <div class="tax-box">
            <h4>Loan Interest Deduction</h4>
            <p>Interest Paid: ₹{total_loan_interest:,.0f}<br>
            Deduction @25%<br>
            <strong>Tax Saved: ₹{loan_interest_deduction:,.0f}</strong></p>
        </div>
        """, unsafe_allow_html=True)

st.subheader("💸 Final Returns")
col1, col2, col3 = st.columns(3)
col1.metric("Total Value", f"₹{final_etf_value:,.0f}")
col2.metric("Net After Loan & Tax", f"₹{net_value:,.0f}")
col3.metric("Annualized Return", f"{annualized_return:.1f}%")

# Visualizations
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(range(1, months+1), etf_values, label="ETF Portfolio Value", color='green')
if borrowed > 0:
    ax.plot(loan_df["Month"], loan_df["Remaining Principal"], 
            label="Loan Outstanding", color='red', linestyle='--')
ax.set_title("ETF Growth vs Loan Repayment")
ax.set_xlabel("Months")
ax.set_ylabel("Amount (₹)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# Detailed Breakdown
with st.expander("📝 Detailed Calculation Methodology"):
    st.markdown(f"""
    **ETF Growth Calculation:**
    - Initial Investment: ₹{initial:,.0f}
    - Leveraged Amount: ₹{borrowed:,.0f} (Total: ₹{total_investment:,.0f})
    - Monthly Return: {etf_return}/12 = {monthly_return*100:.2f}%
    - Dividend Reinvestment: 1% of portfolio value quarterly
    - Final Value after {months} months: ₹{final_etf_value:,.0f}
    
    **Tax Treatment:**
    - ETF Type: {'Equity' if is_equity else 'Debt'}
    - Holding Period: {holding_years:.1f} years
    - Capital Gains Tax: {tax_rate}% on ₹{capital_gain:,.0f} = ₹{capital_gain_tax:,.0f}
    - Dividend Tax: 10% on ₹{dividends_received:,.0f} = ₹{dividend_tax:,.0f}
    {"- Loan Interest Deduction: 25% of ₹" + f"{total_loan_interest:,.0f} = ₹{loan_interest_deduction:,.0f}" if "Pvt Ltd" in investor_type else ""}
    
    **Net Position:**
    - Final ETF Value: ₹{final_etf_value:,.0f}
    - Less: Loan Repayment ₹{borrowed + total_loan_interest:,.0f}
    - Less: Taxes ₹{total_tax:,.0f}
    - Net Value: ₹{net_value:,.0f}
    - Annualized Return: {annualized_return:.1f}%
    """)

st.markdown(f"""
<div class="highlight">
<strong>💡 Key Strategy Benefits:</strong>
1. <strong>Compounding Magic:</strong> Reinvesting dividends accelerates growth exponentially
2. <strong>Tax Efficiency:</strong> ETFs generally have lower expense ratios and tax benefits vs mutual funds
3. <strong>Leverage Boost:</strong> {leverage}x leverage can magnify returns (but increases risk)
4. <strong>Automatic Rebalancing:</strong> Index ETFs automatically maintain optimal allocations

<strong>⚠️ Risk Factors:</strong>
1. Market volatility can erode leveraged positions
2. Interest rate changes affect loan costs
3. Tax laws may change affecting LTCG benefits
4. Dividend yields may vary from projections
</div>
""", unsafe_allow_html=True)

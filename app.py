import streamlit as st

import datetime
import yfinance as yf
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


def get_yoy_price_data(ticker: str) :
    dataframe = yf.Ticker(ticker)
    df = dataframe.history(period="1y")
    
    low = df['High'].max()
    high= df['Low'].min()
    
    last_yr = datetime.date.today() - datetime.timedelta(days=365)

    # last_year_price = yf.download("AAPL", start=last_yr, end=last_yr+datetime.timedelta(days=7))
    last_year_price = dataframe.history(start=last_yr, end=last_yr+datetime.timedelta(days=7))
    yoy = (get_last_price(ticker) - last_year_price.iloc[0]['Close']) / last_year_price.iloc[0]['Close']
    return low, high, yoy, last_year_price.iloc[0]['Close']

def get_last_price(ticker: str):
    session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND*5)),  # max 2 requests per 5 seconds
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)
    ticker = yf.Ticker(ticker, session=session)
    session.close()
    return ticker.history(period='1d')['Close'][0]

st.title('Options Annualized Yield Calculator')

strategy = st.selectbox('Select Strategy', ['Covered Call', 'Cash-Secured Put'])

ticker = st.text_input('Ticker', 'AAPL')
col1, col2, col3, col4 = st.columns(4)
low, high, yoy, last_year_price = get_yoy_price_data(ticker)
with col1:
    st.metric("Last Price", f"${get_last_price(ticker):.2f}")
with col2:
    st.metric("Price Difference (YoY)", f"${(get_last_price(ticker)-last_year_price):.2f}", f"{yoy*100:+.2f}%")
with col3:
    st.metric("52-Week High", f"${low:.2f}")
with col4:
    st.metric("52-Week Low", f"${high:.2f}")

col1, col2 = st.columns(2)

with col1:
    enter_price = st.number_input('Entered Position Stock Price', min_value=0.00, value=100.00, step=0.01)
    strike_price = st.number_input('Strike Price', min_value=0.00, value=100.00, step=0.01)
    yr_out = datetime.datetime.now() + datetime.timedelta(days=7)
    expiration_date = st.date_input("Expiration Date", value=(yr_out))

with col2:
    premium = st.number_input('Option Premium', min_value=0.00, value=5.00, step=0.01)
    shares = st.number_input('Number of Contracts', min_value=1, value=1, step=1)

d = str(expiration_date)
print(d)
days_to_exp = datetime.datetime(int(d[:4]),int(d[5:7]),int(d[8:10])) - datetime.datetime.now() + datetime.timedelta(days=1)
print(days_to_exp)
yield_to_expiration=0
annualized_yield=0

if strategy == "Covered Call":
    yield_to_expiration = round((premium * 100) / enter_price, 2)
    annualized_yield = round((yield_to_expiration / days_to_exp.days) * 365, 2)  
else:
    yield_to_expiration = round((premium * 100) / strike_price, 2)
    annualized_yield = round((yield_to_expiration / days_to_exp.days) * 365, 2)

col5, col6 = st.columns(2)

with col5:
    st.metric("Yield to Expiration", f"{yield_to_expiration}%")
with col6:
    st.metric("Annualized Yield", f"{annualized_yield}%")



# fig, ax = plt.subplots(figsize=(10, 6))
# ax.plot(price_range, profit)
# ax.axhline(y=0, color='r', linestyle='--')
# ax.axvline(x=current_price, color='g', linestyle='--', label='Current Price')
# ax.axvline(x=strike_price, color='b', linestyle='--', label='Strike Price')
# ax.set_xlabel('Stock Price')
# ax.set_ylabel('Profit/Loss ($)')
# ax.set_title(f'{strategy} Profit/Loss Diagram')
# ax.legend()
# ax.grid(True)

# st.pyplot(fig)

# st.write(f'Maximum Profit: ${max_profit:.2f}')
# st.write(f'Maximum Loss: ${max_loss:.2f}')

# breakeven = strike_price - premium if strategy == 'Covered Call' else strike_price - premium
# st.write(f'Breakeven Price: ${breakeven:.2f}')
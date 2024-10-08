import hashlib
import pyotp
from avanza import Avanza, TimePeriod
import json
import pandas as pd
# from pandas.json import json_normalize  
from sklearn import preprocessing


def generateTOTP(totp_secret):
    totp = pyotp.TOTP(totp_secret, digest=hashlib.sha1)
    totp_code = totp.now()
    # print(totp_code)
    return totp_code

totp_code = generateTOTP('your secret')

avanza = Avanza({
    'username': 'your user id',
    'password': 'your password',
    'totpSecret': 'your secret'
})

def pp_json(json_dict):
    print(json.dumps(json_dict, indent=2))

# overview = avanza.get_overview()
# pp_json(overview)

def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return ((current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return float('inf')

def get_orderbooks_by_name(data, name_key):
    for item in data:
        if item['name'] == name_key:
            return item['orderbooks']
    return None

def extract_selected_values(data):
    # Use json_normalize to flatten the JSON object
    df = pd.json_normalize(data)
    
    # Select the specific columns: 'name', 
    selected_columns = ['listing.shortName', 'keyIndicators.marketCapital.value', 'quote.totalVolumeTraded', 'quote.totalValueTraded', 'keyIndicators.netMargin', 'keyIndicators.priceEarningsRatio', 'keyIndicators.returnOnEquity', 'keyIndicators.earningsPerShare.value', 'keyIndicators.numberOfOwners', 'historicalClosingPrices.oneDay', 'historicalClosingPrices.startOfYear', 'historicalClosingPrices.oneYear', 'historicalClosingPrices.threeYears', 'historicalClosingPrices.fiveYears']
    
    # Extract the selected columns into a new DataFrame
    result_df = df[selected_columns]
    
    # Rename columns
    result_df = result_df.rename(columns={
        'listing.shortName': 'Code',
        'keyIndicators.marketCapital.value': 'MCap (M)',
        'quote.totalVolumeTraded': 'Vol (K)',
        'quote.totalValueTraded': 'SEK (K)',
        'historicalClosingPrices.oneDay': 'Close',
        'historicalClosingPrices.startOfYear': 'Perf YTD', 
        'historicalClosingPrices.oneYear': 'Perf 1Y', 
        'historicalClosingPrices.threeYears': 'Perf 3Y', 
        'historicalClosingPrices.fiveYears': 'Perf 5Y',
        'keyIndicators.netMargin': 'Margin %',
        'keyIndicators.priceEarningsRatio': 'P/E',
        'keyIndicators.returnOnEquity': 'ROE',
        'keyIndicators.earningsPerShare.value': 'EPS',
        'keyIndicators.numberOfOwners': 'Owners'
    })
    result_df.insert(loc=4, column='R Vol', value=[0.0 for i in range(df.shape[0])])

    # Process columns
    result_df['R Vol'] = result_df['Vol (K)'] * result_df['SEK (K)'] / result_df['MCap (M)']
    result_df['Perf YTD'] = result_df[['Close', 'Perf YTD']].apply(lambda x: get_change(*x), axis=1)
    result_df['Perf 1Y'] = result_df[['Close', 'Perf 1Y']].apply(lambda x: get_change(*x), axis=1)
    result_df['Perf 3Y'] = result_df[['Close', 'Perf 3Y']].apply(lambda x: get_change(*x), axis=1)
    result_df['Perf 5Y'] = result_df[['Close', 'Perf 5Y']].apply(lambda x: get_change(*x), axis=1)
    
    # Format columns
    result_df['MCap (M)'] = result_df['MCap (M)'] / 1000000
    result_df['MCap (M)'] = result_df['MCap (M)'].map("{:.0f}".format)

    result_df['Vol (K)'] = result_df['Vol (K)'].apply(lambda x: f"{x / 1000:.0f}")
    result_df['SEK (K)'] = result_df['SEK (K)'].apply(lambda x: f"{x / 1000:.0f}")
    result_df['R Vol'] = result_df['R Vol'].apply(lambda x: f"{x:.0f}")

    result_df['Margin %'] = result_df['Margin %'].apply(lambda x: f"{x * 100:.0f}")

    result_df['ROE'] = result_df['ROE'].apply(lambda x: f"{x * 100:.0f}")

    result_df['Owners'] = result_df['Owners'].apply(lambda x: f"{x / 1000:.0f}")

    result_df['Perf YTD'] = result_df['Perf YTD'].map("{:,.0f}".format)
    result_df['Perf 1Y'] = result_df['Perf 1Y'].map("{:,.0f}".format)
    result_df['Perf 3Y'] = result_df['Perf 3Y'].map("{:,.0f}".format)
    result_df['Perf 5Y'] = result_df['Perf 5Y'].map("{:,.0f}".format)

  

    # Print the resulting DataFrame
    return result_df

# Sort columns and normalize rank (normalize) data
def normalize_basic(df):

    cols = df.columns[df.columns != 'Code']

    x = df[cols].values #returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    df[cols] = pd.DataFrame(x_scaled)

    df["Score"] = df[cols].sum(axis=1)

    return df

watchlist = avanza.get_watchlists()
wl = "High interested"
stock_ids = get_orderbooks_by_name(watchlist, wl)
# print(stock_ids) # For debugging

# Initialize an empty DataFrame
final_df = pd.DataFrame()

# For loop to process each JSON object and append the resulting DataFrame
for stock_id in stock_ids:

    index_info = avanza.get_index_info(index_id=stock_id)

    df = extract_selected_values(index_info)
    
    final_df = pd.concat([final_df, pd.DataFrame(df)], ignore_index=True)

final_df = normalize_basic(final_df)

# print(final_df) # For debugging
final_df.to_csv(wl+'-omx.analysis.csv', sep=';', index=False)

# @TODO: HAndle potential non-existing columns

import hashlib
import pyotp
from avanza import Avanza, ChannelType, TimePeriod
import json
import pandas as pd
from sklearn import preprocessing
import numpy as np
import configparser


def generateTOTP(totp_secret):
    totp = pyotp.TOTP(totp_secret, digest=hashlib.sha1)
    totp_code = totp.now()
    return totp_code

<<<<<<< HEAD
def authenticate():

    # totp_code = generateTOTP(totp_secret)

    # Read credentials from config file
    config = configparser.ConfigParser()
    config.read('stock.conf')

    username = config.get('credentials', 'username')
    password = config.get('credentials', 'password')
    totp_secret = config.get('credentials', 'totpSecret')

    avanza = Avanza({
        'username': username,
        'password': password,
        'totpSecret': totp_secret
    })

    return avanza
=======
totp_code = generateTOTP('yourcode')

avanza = Avanza({
    'username': 'yourusername',
    'password': 'yourpassword',
    'totpSecret': 'yoursecret'
})
>>>>>>> 923cf94bbe49ce479ba904981e21e895d67ecebc

def pp_json(json_dict):
    print(json.dumps(json_dict, indent=2))

def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return ((current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0

def get_orderbooks_by_name(data, name_key):
    for item in data:
        if item['name'] == name_key:
            return item['orderbookIds']
    return None

def extract_selected_values(data):
    # Use json_normalize to flatten the JSON object
    df = pd.json_normalize(data)
    
    # Select the specific columns: 'listing.shortName', 
    selected_columns = ['listing.shortName', 'keyIndicators.marketCapital.value', 'quote.totalVolumeTraded', 'quote.totalValueTraded', 'keyIndicators.netMargin', 'keyIndicators.priceEarningsRatio', 'keyIndicators.returnOnEquity', 'keyIndicators.earningsPerShare.value', 'keyIndicators.numberOfOwners', 'historicalClosingPrices.oneDay', 'historicalClosingPrices.startOfYear', 'historicalClosingPrices.oneYear', 'historicalClosingPrices.threeYears', 'historicalClosingPrices.fiveYears']
    
    # Handle non-existing columns (For example: threeYears data is not exist for 1 year old stock)
    for col in selected_columns:
        if col not in df.columns:
            #df.insert(0, col, 1)
            #df = df.assign(col=0)
            df[col] = 0
    # df.replace([np.inf, -np.inf], -1, inplace=True)

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

    # @TODO: P/E normailization should be in the reverse order

    x = df[cols].values #returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    df[cols] = pd.DataFrame(x_scaled)

    df["Score"] = df[cols].sum(axis=1)

    return df

def analysis(avanza):
    
    watchlist = avanza.get_watchlists()
    wl = "0 US stocks"
    wl = "1 EU stocks"
    wl = "2 SE high interest"
    # wl = "3 SE good performance"
    # wl = "5 SE low interest"
    
    stock_ids = get_orderbooks_by_name(watchlist, wl)
    # print(stock_ids) # For debugging

    # Initialize an empty DataFrame
    final_df = pd.DataFrame()

    # For loop to process each JSON object and append the resulting DataFrame
    for stock_id in stock_ids:

        index_info = avanza.get_index_info(index_id=stock_id)

        df = extract_selected_values(index_info)
        
        final_df = pd.concat([final_df, pd.DataFrame(df)], ignore_index=True)

    # If you want to have an overall ranking score
    # final_df = normalize_basic(final_df)

    # print(final_df) # For debugging
    final_df.to_csv(wl+'-omx.analysis.csv', sep=',', index=False)



import asyncio

def callback(data):
    # Do something with the quotes data here
    print(data)

async def subscribe_to_channel(avanza: Avanza):
    await avanza.subscribe_to_id(
        ChannelType.QUOTES,
        "19002", # OMX Stockholm 30
        callback
    )

def main():
    
    avanza = authenticate()
    # Analysis
    # analysis(avanza)

    # Real time data
    asyncio.get_event_loop().run_until_complete(
        subscribe_to_channel(avanza)
    )
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
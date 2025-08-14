#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
import os

CSV_FILE = "../data/transaktioner_2025-01-01_2025-08-14.csv"
STATIC_STARTING_BALANCE = 51971.58

def get_starting_balance(filename, default_balance):
    """
    Gets the starting balance from the filename if the part before the first
    underscore is an integer. Otherwise, returns the default balance.
    """
    basename = os.path.basename(filename)
    name_without_ext, _ = os.path.splitext(basename)
    first_part = name_without_ext.split('_')[0]
    if first_part.isdigit():
        return float(first_part)
    return default_balance

STARTING_BALANCE = get_starting_balance(CSV_FILE, STATIC_STARTING_BALANCE)


def load_data(filepath):
    return pd.read_csv(filepath, sep=";", decimal=",")

def parse_top_ups(df, starting_balance):
    top_ups = df[df["Typ av transaktion"] == "Insättning"].copy()
    top_ups["Datum"] = pd.to_datetime(top_ups["Datum"], format="%Y-%m-%d", errors="coerce")
    today = pd.to_datetime("today").normalize()
    top_ups["days_in_account"] = (today - top_ups["Datum"]).dt.days
    start_of_year = pd.to_datetime(f"{today.year}-01-01")
    starting_row = pd.DataFrame({
        "Datum": [start_of_year],
        "Belopp": [starting_balance],
        "days_in_account": [(today - start_of_year).days]
    })
    top_ups = pd.concat([top_ups, starting_row], ignore_index=True)
    weighted_sum = (top_ups["Belopp"].apply(lambda x: float(str(x).replace(",", "."))) * top_ups["days_in_account"]).sum()
    total_days = starting_row["days_in_account"].iloc[0]
    avg_balance = round(weighted_sum / total_days, 2) if total_days > 0 else 0
    total_top_ups = top_ups["Belopp"].apply(lambda x: float(str(x).replace(",", "."))).sum()
    return total_top_ups, avg_balance

def get_trade_stats(trades):
    total_trades = len(trades)
    total_buy = len(trades[trades["Typ av transaktion"] == "Köp"])
    total_sell = len(trades[trades["Typ av transaktion"] == "Sälj"])
    
    unique_names = trades["Värdepapper/beskrivning"].dropna().unique()
    total_shares = [str(name)[:3].strip().upper() for name in unique_names]

    distinct_shares = trades.apply(
        lambda row: row["ISIN"] if pd.notna(row["ISIN"]) else str(row["Värdepapper/beskrivning"]).strip().lower(),
        axis=1
    ).nunique()
    usd_shares = trades[trades["Instrumentvaluta"] == "USD"].apply(
        lambda row: row["ISIN"] if pd.notna(row["ISIN"]) else str(row["Värdepapper/beskrivning"]).strip().lower(),
        axis=1
    ).nunique()
    sek_shares = trades[trades["Instrumentvaluta"] == "SEK"].apply(
        lambda row: row["ISIN"] if pd.notna(row["ISIN"]) else str(row["Värdepapper/beskrivning"]).strip().lower(),
        axis=1
    ).nunique()
    return total_trades, total_buy, total_sell, total_shares, distinct_shares, usd_shares, sek_shares

def count_open_positions(trades):
    def get_id(row):
        return row["ISIN"] if pd.notna(row["ISIN"]) else str(row["Värdepapper/beskrivning"]).strip().lower()
    trades = trades.copy()
    trades["id"] = trades.apply(get_id, axis=1)
    open_count = 0
    for _, group in trades.groupby("id"):
        net_qty = 0
        for _, row in group.iterrows():
            qty = float(str(row["Antal"]).replace(",", "."))
            if row["Typ av transaktion"] == "Köp":
                net_qty += qty
            elif row["Typ av transaktion"] == "Sälj":
                net_qty += qty
        if net_qty > 0:
            open_count += 1
    return open_count

def get_closed_trades(trades):
    return trades[trades["Resultat"].notna()]

def get_gain_percentages(closed_trades_df):
    gain_percentages = []
    for _, row in closed_trades_df.iterrows():
        try:
            resultat = float(str(row["Resultat"]).replace(",", "."))
            belopp = abs(float(str(row["Belopp"]).replace(",", ".")))
            gain_pct = round((resultat / belopp) * 100, 2) if belopp != 0 else 0
            gain_percentages.append(gain_pct)
        except Exception:
            continue
    return gain_percentages

def get_commission_stats(trades):
    trades = trades.copy()
    trades["Courtage"] = trades["Courtage"].apply(lambda x: float(str(x).replace(",", ".")) if pd.notna(x) else 0)
    total_commission = trades["Courtage"].sum()
    max_commission = trades["Courtage"].max()
    min_commission = trades["Courtage"].min()
    avg_commission = round(trades["Courtage"].mean(), 2)
    return total_commission, max_commission, min_commission, avg_commission

def get_commission_by_currency(trades, currencies):
    stats = {}
    for currency in currencies:
        cur_trades = trades[trades["Instrumentvaluta"] == currency]
        cur_total = cur_trades["Courtage"].sum()
        cur_max = cur_trades["Courtage"].max() if not cur_trades.empty else 0
        cur_min = cur_trades["Courtage"].min() if not cur_trades.empty else 0
        cur_avg = cur_trades["Courtage"].mean() if not cur_trades.empty else 0
        stats[currency] = {
            "Min": cur_min,
            "Max": cur_max,
            "Avg": cur_avg,
            "Total": cur_total
        }
    return stats

def logic_df(df):
    
    total_top_ups, avg_balance = parse_top_ups(df, STARTING_BALANCE)
    trades = df[df["Typ av transaktion"].isin(["Köp", "Sälj"])]
    total_trades, total_buy, total_sell, total_shares, distinct_shares, usd_shares, sek_shares = get_trade_stats(trades)
    closed_trades_df = get_closed_trades(trades)
    closed_trades = len(closed_trades_df)
    open_trades = count_open_positions(trades)
    gain_percentages = get_gain_percentages(closed_trades_df)
    top5_profits = sorted(gain_percentages, reverse=True)[:5]
    top5_losses = sorted([g for g in gain_percentages if g < 0])[:5]
    num_gains = sum(1 for g in gain_percentages if g > 0)
    num_losses = sum(1 for g in gain_percentages if g < 0)
    total_gains_losses = num_gains + num_losses
    gain_ratio = round((num_gains / total_gains_losses * 100) if total_gains_losses > 0 else 0, 2)
    total_commission, max_commission, min_commission, avg_commission = get_commission_stats(trades)
    total_profit = round(closed_trades_df["Resultat"].apply(lambda x: float(str(x).replace(",", ".")) if pd.notna(x) else 0).sum(), 2)
    total_profit_avg_balance_ratio = round((total_profit / avg_balance * 100) if avg_balance > 0 else None, 2)
    
    if avg_balance > 0:
        commission_ratio = round((total_commission / avg_balance) * 100, 2)
    else:
        commission_ratio = None
    
    if total_profit != 0:
        commission_to_profit = round((total_commission / abs(total_profit)) * 100, 2)
    else:
        commission_to_profit = None

    currencies = ["SEK", "USD", "EUR", "DKK", "NOK"]
    commission_stats = get_commission_by_currency(trades, currencies)

    results = {
        "Starting balance": [STARTING_BALANCE],
        "Total top ups": [total_top_ups],
        "AVG balance": [avg_balance],
        "Total shares traded": [distinct_shares],
        "USD shares": [usd_shares],
        "SEK shares": [sek_shares],
        "Shares traded": [total_shares],
        "Total trades": [total_trades],
        "BUY": [total_buy],
        "SELL": [total_sell],
        "OPEN": [open_trades],
        "CLOSED": [closed_trades],
        "Total profit (SEK)": [total_profit],
        "Profit / AVG Balance (%)": [total_profit_avg_balance_ratio],
        "Top 5 Wins (%)": [top5_profits],
        "Top 5 Losses (%)": [top5_losses],
        "Wins": [num_gains],
        "Losses": [num_losses],
        "Win Ratio (%)": [gain_ratio],
        "Total commission (SEK)": [total_commission],
        "Max commission (SEK)": [max_commission],
        "Min commission (SEK)": [min_commission],
        "Avg commission (SEK)": [avg_commission],
        "Comm. / AVG Balance (%)": [commission_ratio],
        "Comm. / Profit (%)": [commission_to_profit]
    }
    # pd.options.display.precision = 2  # Set display precision for all
    report_df = pd.DataFrame(results)
    
    return report_df

def logic_print(df):
    
    total_top_ups, avg_balance = parse_top_ups(df, STARTING_BALANCE)
    trades = df[df["Typ av transaktion"].isin(["Köp", "Sälj"])]
    total_trades, total_buy, total_sell, total_shares, distinct_shares, usd_shares, sek_shares = get_trade_stats(trades)
    closed_trades_df = get_closed_trades(trades)
    closed_trades = len(closed_trades_df)
    open_trades = count_open_positions(trades)
    gain_percentages = get_gain_percentages(closed_trades_df)
    max_gain = max(gain_percentages) if gain_percentages else 0
    max_loss = min(gain_percentages) if gain_percentages else 0
    top5_profits = sorted(gain_percentages, reverse=True)[:5]
    top5_losses = sorted([g for g in gain_percentages if g < 0])[:5]
    num_gains = sum(1 for g in gain_percentages if g > 0)
    num_losses = sum(1 for g in gain_percentages if g < 0)
    total_gains_losses = num_gains + num_losses
    gain_ratio = (num_gains / total_gains_losses * 100) if total_gains_losses > 0 else 0
    total_commission, max_commission, min_commission, avg_commission = get_commission_stats(trades)
    total_profit = closed_trades_df["Resultat"].apply(lambda x: float(str(x).replace(",", ".")) if pd.notna(x) else 0).sum()
    currencies = ["SEK", "USD", "EUR", "DKK", "NOK"]
    commission_stats = get_commission_by_currency(trades, currencies)

    print("\n=== Avanza Trade Performance and Commission Report ===")
    print("Developer: Emre Süren - https://github.com/beyefendi/sverigeshub/tree/main/stocksearch")
    print("-" * 50)
    print("This script processes transaction CSV files from the Avanza transactions section.")
    print("Go to https://www.avanza.se/min-ekonomi/transaktioner.html, set date, and click 'Exportera transaktioner'.")
    print("Rename your filename as setting your initial balance in the filename: the integer before the first underscore is your balance.")
    print("Example: '50000_transaktioner.csv'")
    print("-" * 50)

    print(f"Starting balance\t: {STARTING_BALANCE:.2f}")
    print(f"Total top ups\t\t: {total_top_ups:.2f}")
    print(f"AVG balance (weighted)\t: {avg_balance:.2f}")
    print("-" * 50)
    print(f"Total shares traded\t: {distinct_shares}")
    print(f"USD shares\t\t: {usd_shares}")
    print(f"SEK shares\t\t: {sek_shares}")
    print(f"Shares traded\t\t: {', '.join(total_shares)}")
    print("-" * 50)
    print(f"Total trades\t\t: {total_trades}")
    print(f"BUY\t\t: {total_buy}")
    print(f"SELL\t\t: {total_sell}")
    print(f"OPEN\t\t: {open_trades}")
    print(f"CLOSED\t\t: {closed_trades}")
    print("-" * 50)
    print("!!! Profits and losses contain overheads (commission and currency conversion spread (at least 0.25%)) !!!")
    print(f"Total profit\t\t: {total_profit:.2f} SEK") # from closed trades
    if avg_balance > 0:
        profit_ratio = (total_profit / avg_balance) * 100
        print(f"Profit / AVG Balance\t: {profit_ratio:.2f}%")
    else:
        print("Profit / AVG Balance: N/A (average balance is zero)")
    print(f"Top 5 Wins (%)\t\t:", ", ".join(f"{g:.2f}" for g in top5_profits))
    print(f"Top 5 Losses (%)\t:", ", ".join(f"{l:.2f}" for l in top5_losses))
    print(f"Wins\t\t: {num_gains}")
    print(f"Losses\t: {num_losses}")
    print(f"Win Ratio\t: {gain_ratio:.2f}%")
    print("-" * 50)
    print("!!! Commission does not contain currency conversion spread (at least 0.25%) !!!")
    print(f"Total commission\t: {total_commission:.2f} SEK")
    print(f"MAX commission\t\t: {max_commission:.2f} SEK")
    print(f"MIN commission\t\t: {min_commission:.2f} SEK")
    print(f"AVG commission\t\t: {avg_commission:.2f} SEK")
    if avg_balance > 0:
        commission_ratio = (total_commission / avg_balance) * 100
        print(f"Commission / AVG Balance: {commission_ratio:.2f}%")
    else:
        print("Commission / AVG Balance: N/A (average balance is zero)")
    if total_profit != 0:
        commission_to_profit = (total_commission / abs(total_profit)) * 100
        print(f"Commission / Profit\t: {commission_to_profit:.2f}%")
    else:
        print(f"Commission / Profit\t: N/A (total profit is zero)")
    print("-" * 50)
    print(f"Commission by currency\t")
    print("{:<8}".format("") + "".join("{:>12}".format(cur) for cur in currencies))
    for stat in ["Min", "Max", "Avg", "Total"]:
        print("{:<8}".format(stat) + "".join("{:>12.2f}".format(commission_stats[cur][stat]) for cur in currencies))

if __name__ == "__main__":
    df = load_data(CSV_FILE)
    logic_print(df)

"""
def test_profit_calculation():
    buy_price = 93.17
    sell_price = 94.01
    size = 100
    paid_including_courtage = 9356
    get_including_courtage = 9362

    # Profit including courtage
    profit_including_courtage = get_including_courtage - paid_including_courtage
    profit_pct_including_courtage = (profit_including_courtage / paid_including_courtage) * 100

    # Profit excluding courtage
    profit_excluding_courtage = (sell_price - buy_price) * size
    profit_pct_excluding_courtage = (profit_excluding_courtage / (buy_price * size)) * 100

    # Calculate courtage
    courtage = (paid_including_courtage + sell_price * size) - (buy_price * size + get_including_courtage) 
    courtage = abs(courtage)  # Ensure positive value

    # Courtage as percentage of profit excluding courtage
    if profit_excluding_courtage != 0:
        courtage_pct_of_profit = (courtage / profit_excluding_courtage) * 100
    else:
        courtage_pct_of_profit = 0

    print(f"Profit including courtage: {profit_including_courtage:.2f} ({profit_pct_including_courtage:.2f}%)")
    print(f"Profit excluding courtage: {profit_excluding_courtage:.2f} ({profit_pct_excluding_courtage:.2f}%)")
    print(f"Courtage: {courtage:.2f} ({courtage_pct_of_profit:.2f}% of profit {profit_excluding_courtage:.2f})")
"""

"""
def test_calculate_spread():
    size = 20

    buy_price = 51
    sell_price = 56,06

    buy_exchange_rate = 9,750616
    sell_exchange_rate = 9,650349

    buy_including_courtage = 10004,13
    sell_including_courtage = 10792,92

    buy_courtage = 58,5	
    sell_courtage = 27,05
"""

"""
def test_calculate_spread():
    print("-" * 50)
    # Given exchange rates
    real_exchange = 9.7242 # Does not given in the transaction list
    customer_exchange = 9.7506
    minimum_spread = 0.25

    # Calculate the absolute difference
    difference = customer_exchange - real_exchange

    # Calculate the percentage difference
    percentage_difference = (difference / real_exchange) * 100

    # Display the results
    print(f"Real Exchange Rate: {real_exchange}")
    print(f"Customer Exchange Rate: {customer_exchange}")
    print(f"\nAbsolute Difference: {difference:.4f} {percentage_difference:.4f}%")
"""

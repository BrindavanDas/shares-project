# starting the code

import tkinter as tk
from tkinter import filedialog
import yfinance as yf
import pandas as pd
import numpy as np
import DatabaseUpdater
from dateutil.relativedelta import relativedelta

headers = {
    "Date": "date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
    "Ticker": "ticker",
    "Gain": "gain",
    "Loss": "loss",
    "Average Gain": "average_gain",
    "Average Loss": "average_loss",
    "RS": "rs",
    "RSI": "rsi",
    "Moving Average 20 Days": "moving_average_20_days",
    "Moving Average 100 Days": "moving_average_100_days",
    "Moving Average 200 Days": "moving_average_200_days",
    "MACD": "macd",
    "Signal Line": "signal_line",
    "MACD Histogram": "macd_histogram",
}


class Path:
    """all the paths access
    file access are done here"""

    def __init__(self):
        """Initiation for empty dataframe"""
        self.df = []

    def path(self):
        """To get the file"""
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        self.file = filedialog.askopenfilename()
        if self.file:
            print("Selected file:", self.file)

    def read_excel(self):
        """reads the excel file and saved the dataframe"""
        self.df = pd.read_excel(self.file)
        return self.df


class DataFromYahoo(Path):
    """Pull prices from yahoo finance"""

    def prices_extract(self, shares, start_date, end_date):
        """extracts prices from yahoo for my shares"""
        db_updater = DatabaseUpdater.Database()
        self.all_stock_data = []

        for share in shares:
            df = db_updater.read_from_postgres("data_feed")
            if share in df["Code"].values:
                stock_data = (
                    yf.download(
                        share, start=start_date - relativedelta(years=1), end=end_date
                    )
                    .sort_index()
                    .reset_index()
                )
            else:
                stock_data = (
                    yf.download(
                        share, start=start_date - relativedelta(years=3), end=end_date
                    )
                    .sort_index()
                    .reset_index()
                )

            if stock_data.empty:
                print(f"No data found for {share}")
                continue

            stock_data["Code"] = share  # Add 'Code' column
            stock_data["Date"] = stock_data["Date"].dt.date

            # Calculate RSI for this share
            stock_data["Gain"] = np.where(
                stock_data["Close"] > stock_data["Close"].shift(1),
                stock_data["Close"] - stock_data["Close"].shift(1),
                0,
            )
            stock_data["Loss"] = np.where(
                stock_data["Close"] < stock_data["Close"].shift(1),
                stock_data["Close"].shift(1) - stock_data["Close"],
                0,
            )
            if len(stock_data) >= 15:
                stock_data.loc[14, "Average Gain"] = (
                    stock_data["Gain"].iloc[1:15].mean()
                )
                stock_data.loc[14, "Average Loss"] = (
                    stock_data["Loss"].iloc[1:15].mean()
                )

                for i in range(15, len(stock_data)):
                    prev_avg_gain = stock_data.at[i - 1, "Average Gain"]
                    prev_avg_loss = stock_data.at[i - 1, "Average Loss"]
                    current_gain = stock_data.at[i, "Gain"]
                    current_loss = stock_data.at[i, "Loss"]
                    stock_data.at[i, "Average Gain"] = (
                        prev_avg_gain * 13 + current_gain
                    ) / 14
                    stock_data.at[i, "Average Loss"] = (
                        prev_avg_loss * 13 + current_loss
                    ) / 14
                stock_data["RS"] = (
                    stock_data["Average Gain"] / stock_data["Average Loss"]
                )
                stock_data["RSI"] = 100 - (100 / (1 + stock_data["RS"]))
            else:
                stock_data["Average Gain"] = None
                stock_data["Average Loss"] = None

            stock_data["Moving Average 20 Days"] = (
                stock_data["Close"].rolling(window=20).mean()
            )
            stock_data["Moving Average 100 Days"] = (
                stock_data["Close"].rolling(window=100).mean()
            )
            stock_data["Moving Average 200 Days"] = (
                stock_data["Close"].rolling(window=200).mean()
            )

            # Calculate the MACD Line
            stock_data["MACD"] = (
                stock_data["Close"].ewm(span=12, adjust=False).mean()
                - stock_data["Close"].ewm(span=26, adjust=False).mean()
            )

            # Calculate the Signal Line
            stock_data["Signal Line"] = (
                stock_data["MACD"].ewm(span=9, adjust=False).mean()
            )

            # Calculate the MACD Histogram
            stock_data["MACD Histogram"] = (
                stock_data["MACD"] - stock_data["Signal Line"]
            )
            stock_data.reset_index(drop=True, inplace=True)  # Reset index
            self.all_stock_data.append(stock_data)

        # Concatenate all DataFrames into a single DataFrame
        if self.all_stock_data:
            self.df_combined = pd.concat(
                self.all_stock_data
            )  # ignore_index=True to reset index

            self.df_combined.rename(columns=headers, inplace=True)

            return self.df_combined
        else:
            print("No data to concatenate")
            return pd.DataFrame()  # Return an empty DataFrame if no data was collected

    def save_to_excel(self):
        """Save df_combined to Excel file"""

        excel_file_path = "data_feed.xlsx"

        # Save combined DataFrame to Excel file
        self.df_combined.to_excel(excel_file_path, index=False)

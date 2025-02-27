# -*- coding: utf-8 -*-
"""Primetrade.ai.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_SkkEr3REQ1f52e6cuCcnSXIcJuueNv_

#Importing Libraries
"""

import requests
from pathlib import Path
from scipy.stats import zscore
from scipy.stats.mstats import winsorize

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import json
import ast

"""# Creating folder to store data"""

data_dir = Path("./Data")
trade_csv = data_dir/"trade.csv"

if data_dir.is_dir():
  print(f"{data_dir} path already exist!!")
else:
  print(f"{data_dir} path doesn't exist, creating the {data_dir} path......")
  Path.mkdir(data_dir)
  print(f"{data_dir} path created!!!!")

"""#Downloading data from Google Drive"""

with open(trade_csv,"wb") as f:
  response = requests.get("https://drive.google.com/uc?export=download&id=1E3T8i1akfm6NnT42AWEE6U1t7uvwreYK")
  f.write(response.content)

trade_df = pd.read_csv(trade_csv)
trade_df.head()

trade_df.head(1)

"""#Formating The Data into meaning full Data

##Parsing the json data and converting it to dataframe formate
"""

def parse_trade_history(trade_data):
    """Convert stringified trade history into a proper list of dictionaries."""
    try:
        if isinstance(trade_data, list):
            return trade_data  # Already a list, no need to parse
        elif isinstance(trade_data, str):
            # Replace single quotes with double quotes
            trade_data = trade_data.replace("'", '"')
            # Convert Python-style booleans and None to JSON format
            trade_data = trade_data.replace("True", "true").replace("False", "false").replace("None", "null")
            return json.loads(trade_data)  # Parse as JSON
        else:
            return None  # If unknown format, return None
    except json.JSONDecodeError as e:
        print("Error parsing trade history:", e)
        return None  # Handle parsing errors gracefully

# Apply the function to the Trade_History column
trade_df['Trade_History'] = trade_df['Trade_History'].apply(parse_trade_history)

# Explode the trade history into separate rows
df_exploded = trade_df.explode("Trade_History").reset_index(drop=True)
df_exploded.head()

# Convert the dictionary into a structured DataFrame
df_normalized = pd.json_normalize(df_exploded["Trade_History"]).reset_index(drop=True)
df_normalized.head()

# Merge with Port_IDs
df_final = pd.concat([df_exploded.drop(columns=["Trade_History"], errors="ignore"), df_normalized], axis=1)

# Save the structured trade data
df_final.to_csv(trade_csv, index=False)

df = pd.read_csv(trade_csv)
df.head()

"""#EDA(Explority Data Analysis)"""

df.info()

df.describe().T

"""##Adjusting the the time feature into proper formate"""

df["time"] = pd.to_datetime(df["time"], unit="ms")

df.head(3)

"""## Handling null Values for the continous data"""

df = df.fillna(method='ffill')

df.info()

"""##Handling Outliers"""

# Apply Winsorization (Cap extreme values at 1st & 99th percentile)
df["price"] = winsorize(df["price"], limits=[0.01, 0.01])
df["quantity"] = winsorize(df["quantity"], limits=[0.01, 0.01])
df["realizedProfit"] = winsorize(df["realizedProfit"], limits=[0.01, 0.01])

df.describe().T

# Calculate rolling mean and standard deviation for realizedProfit
rolling_mean = df["realizedProfit"].rolling(window=50, min_periods=1).mean()
rolling_std = df["realizedProfit"].rolling(window=50, min_periods=1).std()

# Compute the Rolling Z-score
df["Rolling_Zscore"] = (df["realizedProfit"] - rolling_mean) / rolling_std

# Fill NaN values (caused by std=0 at the beginning)
df["Rolling_Zscore"] = df["Rolling_Zscore"].fillna(0)

# Replace extreme values with median (keeps ranking stable)
df.loc[df["Rolling_Zscore"].abs() > 1, "realizedProfit"] = df["realizedProfit"].median()
df.loc[df["Rolling_Zscore"].abs() > 1, "quantity"] = df["quantity"].median()
df.loc[df["Rolling_Zscore"].abs() > 1, "price"] = df["price"].median()

df.describe().T

# Plot distribution of price, quantity, and realized profit
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

sns.histplot(df["price"], bins=50, ax=axes[0], kde=True)
axes[0].set_title("Price Distribution")

sns.histplot(df["quantity"], bins=50, ax=axes[1], kde=True)
axes[1].set_title("Quantity Distribution")

sns.histplot(df["realizedProfit"], bins=50, ax=axes[2], kde=True)
axes[2].set_title("Realized Profit Distribution")

plt.show()

# Boxplots to detect remaining outliers
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

sns.boxplot(y=df["price"], ax=axes[0])
axes[0].set_title("Price Boxplot")

sns.boxplot(y=df["quantity"], ax=axes[1])
axes[1].set_title("Quantity Boxplot")

sns.boxplot(y=df["realizedProfit"], ax=axes[2])
axes[2].set_title("Realized Profit Boxplot")

plt.show()

"""#Calculating Different Matrics
- ROI (Return on Investment)
- PnL (Profit and Loss)
- Sharpe Ratio
- MDD (Maximum Drawdown)
- Win Rate
- Win Positions
- Total Positions

In the below sessions we're going to calculate the desired matrics as instructed
"""

# Group by Port_IDs and sum up relevant columns
df_grouped = df.groupby("Port_IDs").agg({
  "quantity": "sum",          # Total money invested per account
  "realizedProfit": "sum",    # Total profit per account
  "fee": "sum",               # Total fees per account
  "qty": "sum",               # Total coin quantity per account
  "time": ["min", "max"],     # Get first and last trade timestamps
  "symbol": "nunique",        # Count number of unique traded assets
  "side": "count"             # Total trade count (Total Positions)
}).reset_index()

# Rename columns for clarity
df_grouped.columns = ["Port_IDs", "Total_Quantity", "Total_Realized_Profit", "Total_Fee",
                      "Total_Qty", "First_Trade", "Last_Trade", "Unique_Assets", "Total_Positions"]
df_grouped.head()

# Calculate trading duration (in hours)
df_grouped["Trading_Duration_Hours"] = (df_grouped["Last_Trade"] - df_grouped["First_Trade"]).dt.total_seconds() / 3600

# Calculate average trade frequency (trades per hour)
df_grouped["Avg_Trades_per_Hour"] = df_grouped["Total_Positions"] / df_grouped["Trading_Duration_Hours"]

df_grouped.head()

len(df_grouped)

"""##ROI(Return on Investment)
ROI can we calculate by:
### ROI (Return on Investment)
**Formula:**

ROI=(
Total Quantity Invested/Total Realized Profit
​
 )×100

- **Total Realized Profit** = Sum of `realizedProfit`
- **Total Quantity Invested** = Sum of `quantity` for **BUY** trades

"""

df_grouped.columns

# Define a small epsilon to replace zeroes
epsilon = 1e-6  # Small value to avoid divide-by-zero errors

# Replace 0 in PnL with epsilon before calculating ROI
df_grouped["Total_Realized_Profit"] = df_grouped["Total_Realized_Profit"].replace(0, epsilon)

df_grouped["ROI"] = (df_grouped["Total_Quantity"]/df_grouped["Total_Realized_Profit"])*100
df_grouped["ROI"].head(10)

df_grouped.tail(2)["Total_Realized_Profit"]

"""##PnL(Profit and Loss)
Pnl can be calculated by:

### PnL (Profit and Loss)
**Formula:**

PnL=∑(realizedProfit)


- Sum of all realized profits/losses from trades.
- Positive = profit, Negative = loss.

"""

df_grouped.columns

df_grouped.rename(columns={"Total_Realized_Profit":"PnL"},inplace=True)

df_grouped["PnL"]

"""##Sharpe Ratio
We can calculate Sharpe Ratio using:
Formula:

Sharpe Ratio = (𝐸[𝑟−𝑅𝑓])/𝜎𝑟

Where:

- r = Returns from trades (percentage change per trade)

- 𝑅𝑓 = Risk-free rate (assume 0% if unavailable)

- 𝜎𝑟 = Standard deviation of returns

How to Calculate:

Calculate percentage return per trade:

𝑟 = (realizedProfit)/quantity

- Compute average return 𝐸[𝑟]

- Compute standard deviation 𝜎𝑟

- Plug into formula
"""

# Assumption: Risk-free rate (Rf) = 0%
df_grouped["Mean_Return"] = df_grouped["PnL"] / df_grouped["Total_Quantity"]
df_grouped["Std_Dev_Return"] = df_grouped["Mean_Return"].std()  # Standard deviation of returns
df_grouped["Sharpe_Ratio"] = df_grouped["Mean_Return"] / df_grouped["Std_Dev_Return"]

"""##MDD(Maxium Drawdown)
We can calculate MDD by:

Formula:

𝑀𝐷𝐷 = [(max⁡(Cumulative Equity) − min⁡(Cumulative Equity))/max(Cumulative Equity)]*100

How to Calculate:

- Compute cumulative profit/loss per trade
- Track max equity value at any point
- Find largest drop from peak to low
"""

df_grouped["Sharpe_Ratio"]

# Calculate cumulative profit
df_grouped["Cumulative_Profit"] = df_grouped["PnL"].cumsum()

# Calculate Maximum Drawdown
df_grouped["Max_Cumulative_Profit"] = df_grouped["Cumulative_Profit"].cummax()
df_grouped["Drawdown"] = df_grouped["Max_Cumulative_Profit"] - df_grouped["Cumulative_Profit"]
df_grouped["Max_Drawdown (%)"] = (df_grouped["Drawdown"] / df_grouped["Max_Cumulative_Profit"]) * 100

df_grouped.columns

"""##Win Rate and Positions
Formula:
Formula:

Win Rate = (Win Positions/Total Positions)*100

How to Calculate:

- Win Positions = Count of trades where realizedProfit > 0
- Total Positions = Total number of trades

Win Positions = ∑1(realizedProfit>0)

How to Calculate:

- Count the number of trades where realizedProfit > 0
"""

df.groupby("Port_IDs")["realizedProfit"].apply(lambda x: (x > 0).sum()).reset_index()["realizedProfit"]

# Win Positions & Win Rate Calculation
df_grouped["Win_Positions"] = df.groupby("Port_IDs")["realizedProfit"].apply(lambda x: (x > 0).sum()).reset_index()["realizedProfit"]
df_grouped["Win_Rate (%)"] = (df_grouped["Win_Positions"] / df_grouped["Total_Positions"]) * 100

df_grouped.loc[:,["Win_Positions","Win_Rate (%)"]]

"""##Total Position
Formula:

Total Positions = Count of All trades

How to Calculate:

- Count total number of trades
"""

df.groupby(["Port_IDs", "side"])["side"].count().unstack(fill_value=0).reset_index()["BUY"]

# Count total trades per Port_IDs (Total Positions)
df_grouped["Total_Positions"] = df.groupby("Port_IDs")["side"].count().reset_index()["side"]
df_grouped["Total_Buy_Positions"] = df.groupby(["Port_IDs", "side"])["side"].count().unstack(fill_value=0).reset_index()["BUY"]
df_grouped["Total_Sell_Positions"] = df.groupby(["Port_IDs", "side"])["side"].count().unstack(fill_value=0).reset_index()["SELL"]
df_grouped["Net_Positions"] = df_grouped["Total_Buy_Positions"] - df_grouped["Total_Sell_Positions"]

df_grouped[["Total_Positions","Total_Buy_Positions","Total_Sell_Positions","Net_Positions"]]

"""##Saving The Metrics DataFrame to CSV"""

#Path to Metric DataFrame
metrics_csv = data_dir/"Metrics_DataFrame.csv"
#Saving the dataframe to the path
df_grouped.to_csv(metrics_csv)

"""#Ranking Trades
Now we're going to rank the trades from top best trades to worst trade using 3 different methodology.
1. Weight Score Method
2. Z-Score Normalization Method
3. Machine Learning Approach

##Weight Score Method
This is a multi-metric ranking approach that assigns weights to different parameters and calculates a final score for each trader.

Formula for Ranking Score

    Trade Score = (𝑤1 × 𝑅𝑂𝐼)+(𝑤2 × 𝑃𝑛𝐿)+(𝑤3 × 𝑆ℎ𝑎𝑟𝑝𝑒𝑅𝑎𝑡𝑖𝑜)+(𝑤4 × 𝑊𝑖𝑛𝑅𝑎𝑡𝑒)+(𝑤5 × 𝑇𝑟𝑎𝑑𝑒𝐴𝑐𝑡𝑖𝑣𝑖𝑡𝑦)

Where:

- 𝑤1, 𝑤2, 𝑤3, 𝑤4, 𝑤5 are weights assigned to each metric.
- Higher weights mean that metric is more important.
- The sum of all weights should be 1.0 (100%).
"""

df_grouped.columns

# Define Weights for Ranking (adjust based on importance)
weights = {
    "ROI": 0.2,            # Profitability
    "PnL": 0.2,            # Overall profit/loss
    "Sharpe_Ratio": 0.2,   # Risk-adjusted returns
    "Win_Rate": 0.2,       # Consistency
    "Total_Positions": 0.1, # Activity level
    "Net_Positions": 0.1
}

# Normalize Metrics (convert to range 0-1 for fair comparison)
df_grouped["ROI_Norm"] = df_grouped["ROI"] / df_grouped["ROI"].max()
df_grouped["PnL_Norm"] = df_grouped["PnL"] / df_grouped["PnL"].max()
df_grouped["Sharpe_Norm"] = df_grouped["Sharpe_Ratio"] / df_grouped["Sharpe_Ratio"].max()
df_grouped["WinRate_Norm"] = df_grouped["Win_Rate (%)"] / df_grouped["Win_Rate (%)"].max()
df_grouped["Positions_Norm"] = df_grouped["Total_Positions"] / df_grouped["Total_Positions"].max()
df_grouped["Net_Positions_Norm"] = df_grouped["Net_Positions"] / df_grouped["Net_Positions"].max()


# Calculate Final Trade Score
df_grouped["Trade_Weight_Score"] = (
    weights["ROI"] * df_grouped["ROI_Norm"] +
    weights["PnL"] * df_grouped["PnL_Norm"] +
    weights["Sharpe_Ratio"] * df_grouped["Sharpe_Norm"] +
    weights["Win_Rate"] * df_grouped["WinRate_Norm"] +
    weights["Total_Positions"] * df_grouped["Positions_Norm"] +
    weights["Net_Positions"] * df_grouped["Net_Positions_Norm"]
)

# Rank Traders Based on Trade Score
df_grouped = df_grouped.sort_values(by="Trade_Weight_Score", ascending=False).reset_index(drop=True)

Weight_Score = [list(df_grouped.head(20)["Port_IDs"]),list(df_grouped.head(20)["Trade_Weight_Score"])]
Weight_Score

"""##Z-Score Method
Instead of scaling from 0-1, normalize using Z-Score:

    𝑍 = (𝑋 − 𝜇)/𝜎

where μ is the mean and 𝜎 is the standard deviation.
"""

# Apply Z-Score Normalization to all ranking metrics
df_grouped["ROI_Z"] = zscore(df_grouped["ROI"])
df_grouped["PnL_Z"] = zscore(df_grouped["PnL"])
df_grouped["Sharpe_Z"] = zscore(df_grouped["Sharpe_Ratio"])
df_grouped["WinRate_Z"] = zscore(df_grouped["Win_Rate (%)"])
df_grouped["Positions_Z"] = zscore(df_grouped["Total_Positions"])
df_grouped["Net_Positions_Z"] = zscore(df_grouped["Net_Positions"])

# Define Weights for Ranking
weights = {
    "ROI_Z": 0.2,
    "PnL_Z": 0.2,
    "Sharpe_Z": 0.2,
    "WinRate_Z": 0.2,
    "Positions_Z": 0.1,
    "Net_Positions_Z" : 0.1
}

# Compute Trade Score using Weighted Z-Scores
df_grouped["Trade_Z_Score"] = (
    weights["ROI_Z"] * df_grouped["ROI_Z"] +
    weights["PnL_Z"] * df_grouped["PnL_Z"] +
    weights["Sharpe_Z"] * df_grouped["Sharpe_Z"] +
    weights["WinRate_Z"] * df_grouped["WinRate_Z"] +
    weights["Positions_Z"] * df_grouped["Positions_Z"] +
    weights["Net_Positions_Z"] * df_grouped["Net_Positions_Z"]
)

# Rank Traders Based on Trade Score
df_grouped = df_grouped.sort_values(by="Trade_Z_Score", ascending=False).reset_index(drop=True)

Z_Score = [list(df_grouped.head(20)["Port_IDs"]),list(df_grouped.head(20)["Trade_Z_Score"])]
Z_Score

"""##Machine Learning Apporach"""

import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from sklearn.neural_network import MLPRegressor

df_grouped.describe().T

"""###Splitting the data"""

# Define Features (X) and Target (y)
features = [
    'Total_Quantity', 'PnL', 'Total_Fee', 'Total_Qty', 'Unique_Assets',
    'Total_Positions', 'ROI', 'Mean_Return', 'Std_Dev_Return', 'Sharpe_Ratio',
    'Cumulative_Profit', 'Max_Cumulative_Profit', 'Drawdown', 'Max_Drawdown (%)',
    'Win_Positions', 'Win_Rate (%)', 'Total_Buy_Positions', 'Total_Sell_Positions',
    'Net_Positions', 'ROI_Norm', 'PnL_Norm', 'Sharpe_Norm', 'WinRate_Norm',
    'Positions_Norm', 'Net_Positions_Norm', 'Trade_Weight_Score', 'ROI_Z',
    'PnL_Z', 'Sharpe_Z', 'WinRate_Z', 'Positions_Z', 'Net_Positions_Z',
    'Trade_Z_Score'
]

X = df_grouped[features]
y = df_grouped["Trade_Weight_Score"]  # Target variable

# Handle missing values (replace NaN with 0)
X.fillna(0, inplace=True)
y.fillna(0, inplace=True)

# Split into train and test sets (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features for better ML performance
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

"""###RandomForest MODEL"""

# Train Random Forest Model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_scaled, y_train)

# Predict on test set
y_pred_rf = rf_model.predict(X_test_scaled)
y_pred_rf

r2_score(y_test, y_pred_rf), mean_absolute_error(y_test, y_pred_rf)

df_grouped["Trade_ML_Score"] = rf_model.predict(X)
df_grouped = df_grouped.sort_values(by="Trade_ML_Score", ascending=False).reset_index(drop=True)

ML_Score = [list(df_grouped.head(20)["Port_IDs"]),list(df_grouped.head(20)["Trade_ML_Score"])]
ML_Score

"""##Results
Now we will build up a result dataframe from the different results we got from the different approach we followed:

1. Weight Score Approach
2. Z-Score Approach
3. Machine Learning Approach
"""

#Results Dictionary
results = {
    "Rank": range(1,21),
    "WS_Ranking": Weight_Score[0],
    "Weight_Score": Weight_Score[1],
    "ZS_Ranking":Z_Score[0],
    "Z-Score":Z_Score[1],
    "ML_Ranking":ML_Score[0],
    "Machine_Learning":ML_Score[1]
}

results_df = pd.DataFrame.from_dict(results).set_index("Rank")
results_df.head(20)


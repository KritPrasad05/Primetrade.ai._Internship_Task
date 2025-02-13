# Primetrade.ai._Internship_Task
# Trade Ranking System

## 📌 Project Overview
This project aims to develop a **robust trade ranking system** using three distinct methodologies:
1. **Weighted Score Method** – Assigning predefined weights to key financial metrics.
2. **Z-Score Normalization Method** – Standardizing metrics for fair ranking.
3. **Machine Learning Approach (RandomForest Regressor)** – Predicting trade rankings based on historical data.

The dataset consists of trading history, including **buy/sell transactions, profit/loss, risk-adjusted returns, and trade activity**. This project is developed for **PrimeTrade.ai** to enhance trade evaluation and decision-making.

---

## 🔧 Installation Guide
### **Step 1: Clone the Repository**
To download and run this project locally, use:
```bash
git clone <GitHub_Repository_URL>
cd Trade_Ranking_System
```

### **Step 2: Create a Virtual Environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Download Trade Data (Automatically Handled in Code)**
The dataset is downloaded and stored automatically in the `Data/` folder.

---

## 📊 Methodologies Used

### **1️⃣ Weighted Score Method**
A scoring system assigns weights to:
- **PnL (40%)** – Profit & Loss.
- **ROI (25%)** – Return on Investment.
- **Sharpe Ratio (15%)** – Risk-adjusted returns.
- **Win Rate (10%)** – Consistency in profitable trades.
- **Net Positions (10%)** – Trading balance (Buy vs. Sell).

#### **Formula:**
```python
Trade_Score = (0.4 * PnL_Norm) + (0.25 * ROI_Norm) + (0.15 * Sharpe_Norm) + (0.1 * WinRate_Norm) + (0.1 * NetPositions_Norm)
```

### **2️⃣ Z-Score Normalization Method**
Z-score transformation ensures fair ranking by standardizing each metric:
```python
Z = (X - mean) / std_dev
```
All key metrics are transformed into Z-Scores and summed to create a final ranking score.

### **3️⃣ Machine Learning Approach (Random Forest)**
A **RandomForest Regressor** is trained on:
- **Financial Metrics**: `PnL`, `ROI`, `Sharpe_Ratio`, `Win Rate (%)`, etc.
- **Trade Behavior**: `Net Positions`, `Total Buy/Sell Positions`.
- **Normalization & Z-Scores** for standardization.

Trained on historical data, the model predicts rankings based on learned patterns.

---

## 🚀 How to Run the Code

### **Step 1: Run the Python Script**
```bash
python primetrade_ai.py
```
Or, if using Jupyter Notebook:
```bash
jupyter notebook
# Open Primetrade_ai.ipynb and run cells sequentially.
```

### **Step 2: View Rankings**
After execution, ranked results will be stored in:
- **`ranked_trades.csv`** (Weighted Score, Z-Score, ML rankings)
- **Visualizations for trade performance**

---

## 🛠️ Key Code Explanations
### **1. Parsing Trade History**
```python
def parse_trade_history(trade_data):
    """Convert trade history from JSON format into a structured DataFrame."""
    try:
        if isinstance(trade_data, list):
            return trade_data
        elif isinstance(trade_data, str):
            trade_data = trade_data.replace("'", '"')
            trade_data = trade_data.replace("True", "true").replace("False", "false").replace("None", "null")
            return json.loads(trade_data)
    except json.JSONDecodeError:
        return None
```
✅ **Why?** Converts trade history from JSON strings into structured tabular format.

### **2. Handling Outliers Using Winsorization**
```python
df["price"] = winsorize(df["price"], limits=[0.01, 0.01])
df["quantity"] = winsorize(df["quantity"], limits=[0.01, 0.01])
df["realizedProfit"] = winsorize(df["realizedProfit"], limits=[0.01, 0.01])
```
✅ **Why?** Caps extreme values (1st & 99th percentile) to prevent skewing rankings.

### **3. Computing Machine Learning Predictions**
```python
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)
```
✅ **Why?** Trains a RandomForest model to predict rankings based on historical performance.

---

## 📜 Acknowledgment
This project was **assigned by PrimeTrade.ai**, and we appreciate their support in building a robust trade ranking system. Special thanks to the data science team for their insights and collaboration.

---

## 🏆 Future Enhancements
- **Hyperparameter tuning** to improve model accuracy.
- **Integration with XGBoost & Neural Networks**.
- **Real-time ranking updates based on live trading data.**

---

## 🔗 Contact & Contributions
Feel free to contribute by submitting **pull requests** or **issues** to enhance functionality!

📩 **Contact:** [kritrp05@gmail.com](kritrp05@gmail.com)

---

🚀 **Now, you're ready to analyze & rank traders efficiently! Happy Trading!** 🎯


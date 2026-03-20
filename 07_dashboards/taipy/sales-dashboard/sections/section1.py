from taipy.gui import Gui
import pandas as pd
import datetime

# Load CSV data
csv_file_path = "data/sales_data.csv"

try:
    raw_data = pd.read_csv(
        csv_file_path,
        parse_dates=["order_date"],
        low_memory=False  # Suppress dtype warning
    )
    if "revenue" not in raw_data.columns:
        raw_data["revenue"] = raw_data["quantity"] * raw_data["price"]
    print(f"Data loaded successfully: {raw_data.shape[0]} rows")
except Exception as e:
    print(f"Error loading CSV: {e}")
    raw_data = pd.DataFrame()

categories = ["All Categories"] + sorted(raw_data['categories'].dropna().unique().tolist())

# Define the visualization options as a proper list
chart_options = ["Revenue Over Time", "Revenue by Category", "Top Products"]

section_1 = """
## Section 1

Data loaded: <|{raw_data.shape[0]}|> rows
"""
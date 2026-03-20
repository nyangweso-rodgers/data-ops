from sections.section1 import section_1, raw_data, categories, chart_options
import pandas as pd
import datetime

start_date = raw_data["order_date"].min().date() if not raw_data.empty else datetime.date(2020, 1, 1)
end_date = raw_data["order_date"].max().date() if not raw_data.empty else datetime.date(2023, 12, 31)
selected_category = "All Categories"
selected_tab = "Revenue Over Time"  # Set default selected tab
total_revenue = "$0.00"
total_orders = 0
avg_order_value = "$0.00"
top_category = "N/A"
revenue_data = pd.DataFrame(columns=["order_date", "revenue"])
category_data = pd.DataFrame(columns=["categories", "revenue"])
top_products_data = pd.DataFrame(columns=["product_names", "revenue"])

def apply_changes(state):
    filtered_data = raw_data[
        (raw_data["order_date"] >= pd.to_datetime(state.start_date)) &
        (raw_data["order_date"] <= pd.to_datetime(state.end_date))
    ]
    if state.selected_category != "All Categories":
        filtered_data = filtered_data[filtered_data["categories"] == state.selected_category]

    state.revenue_data = filtered_data.groupby("order_date")["revenue"].sum().reset_index()
    state.revenue_data.columns = ["order_date", "revenue"]
    print("Revenue Data:")
    print(state.revenue_data.head())

    state.category_data = filtered_data.groupby("categories")["revenue"].sum().reset_index()
    state.category_data.columns = ["categories", "revenue"]
    print("Category Data:")
    print(state.category_data.head())

    state.top_products_data = (
        filtered_data.groupby("product_names")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    state.top_products_data.columns = ["product_names", "revenue"]
    print("Top Products Data:")
    print(state.top_products_data.head())

    state.raw_data = filtered_data
    state.total_revenue = f"${filtered_data['revenue'].sum():,.2f}"
    state.total_orders = filtered_data["order_id"].nunique()
    state.avg_order_value = f"${filtered_data['revenue'].sum() / max(filtered_data['order_id'].nunique(), 1):,.2f}"
    state.top_category = (
        filtered_data.groupby("categories")["revenue"].sum().idxmax()
        if not filtered_data.empty else "N/A"
    )

def on_change(state, var_name, var_value):
    if var_name in {"start_date", "end_date", "selected_category", "selected_tab"}:
        print(f"State change detected: {var_name} = {var_value}")  # Debugging
        apply_changes(state)

def on_init(state):
    apply_changes(state)

import taipy.gui.builder as tgb

def get_partial_visibility(tab_name, selected_tab):
    return "block" if tab_name == selected_tab else "none"

section_2 = """
## Section 2: Interactive Sales Dashboard

<|layout|columns=1 1|gap=20px|>

<|part|>
<|{start_date}|date|label=Start Date|on_change=on_change|>  
<|{end_date}|date|label=End Date|on_change=on_change|>

<|{selected_category}|selector|lov={categories}|on_change=on_change|dropdown|label=Select Category|>

<|{chart_options}|toggle|bind=selected_tab|on_change=on_change|label=Select Chart|>

**Total Revenue:** <|{total_revenue}|>  
**Total Orders:** <|{total_orders}|>  
**Average Order Value:** <|{avg_order_value}|>  
**Top Category:** <|{top_category}|>

<|{revenue_data}|chart|type=line|x=order_date|y=revenue|visible={get_partial_visibility('Revenue Over Time', selected_tab)}|>

<|{category_data}|chart|type=bar|x=categories|y=revenue|visible={get_partial_visibility('Revenue by Category', selected_tab)}|>

<|{top_products_data}|chart|type=bar|x=product_names|y=revenue|visible={get_partial_visibility('Top Products', selected_tab)}|>
<|endpart|>

<|end|>
"""
from sections.section1 import raw_data, categories
from sections.section2 import (
    start_date, end_date, selected_category, selected_tab,
    total_revenue, total_orders, avg_order_value, top_category,
    revenue_data, category_data, top_products_data,
    on_change
)
import taipy.gui.builder as tgb

def create_section3_page():
    with tgb.Page() as page:
        tgb.text("# Sales Performance Dashboard", mode="md")
        
        # Filters section
        with tgb.part(class_name="card"):
            with tgb.layout(columns="1 1 2"):  # Arrange elements in 3 columns
                with tgb.part():
                    tgb.text("Filter From:")
                    tgb.date("{start_date}", on_change=on_change)
                with tgb.part():
                    tgb.text("To:")
                    tgb.date("{end_date}", on_change=on_change)
                with tgb.part():
                    tgb.text("Filter by Category:")
                    tgb.selector(
                        value="{selected_category}",
                        lov=categories,
                        dropdown=True,
                        width="300px",
                        on_change=on_change
                    )
       
        # Metrics section
        tgb.text("## Key Metrics", mode="md")
        with tgb.layout(columns="1 1 1 1"):
            with tgb.part(class_name="metric-card"):
                tgb.text("### Total Revenue", mode="md")
                tgb.text("{total_revenue}")
            with tgb.part(class_name="metric-card"):
                tgb.text("### Total Orders", mode="md")
                tgb.text("{total_orders}")
            with tgb.part(class_name="metric-card"):
                tgb.text("### Average Order Value", mode="md")
                tgb.text("{avg_order_value}")
            with tgb.part(class_name="metric-card"):
                tgb.text("### Top Category", mode="md")
                tgb.text("{top_category}")

        tgb.text("## Visualizations", mode="md")
        # Selector for visualizations with reduced width
        with tgb.part(style="width: 50%;"):  # Reduce width of the dropdown
            tgb.selector(
                value="{selected_tab}",
                lov=["Revenue Over Time", "Revenue by Category", "Top Products"],
                dropdown=True,
                width="360px",  # Reduce width of the dropdown
                on_change=on_change
            )

        # Conditional rendering of charts based on selected_tab
        with tgb.part(render="{selected_tab == 'Revenue Over Time'}"):
            tgb.chart(
                data="{revenue_data}",
                x="order_date",
                y="revenue",
                type="line",
                title="Revenue Over Time",
            )

        with tgb.part(render="{selected_tab == 'Revenue by Category'}"):
            tgb.chart(
                data="{category_data}",
                x="categories",
                y="revenue",
                type="bar",
                title="Revenue by Category",
            )

        with tgb.part(render="{selected_tab == 'Top Products'}"):
            tgb.chart(
                data="{top_products_data}",
                x="product_names",
                y="revenue",
                type="bar",
                title="Top Products",
            )

        # Raw Data Table
        tgb.text("## Raw Data", mode="md")
        tgb.table(data="{raw_data}")
    
    return page

# Create the section3 page
section_3_page = create_section3_page()
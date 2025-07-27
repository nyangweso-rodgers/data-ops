from taipy.gui import Gui
from sections.section1 import section_1, raw_data, categories, chart_options
from sections.section2 import (
    section_2,
    start_date, end_date, selected_category, selected_tab,
    total_revenue, total_orders, avg_order_value, top_category,
    revenue_data, category_data, top_products_data,
    apply_changes, on_change, on_init, get_partial_visibility
)
from sections.section3 import section_3_page

# Define scope with all variables and functions
scope = {
    "raw_data": raw_data,
    "categories": categories,
    "chart_options": chart_options,
    
    "start_date": start_date,
    "end_date": end_date,
    "selected_category": selected_category,
    "selected_tab": selected_tab,
    
    "total_revenue": total_revenue,
    "total_orders": total_orders,
    "avg_order_value": avg_order_value,
    "top_category": top_category,
    
    "revenue_data": revenue_data,
    "category_data": category_data,
    "top_products_data": top_products_data,
    
    "apply_changes": apply_changes,
    "on_change": on_change,
    "on_init": on_init,
    "get_partial_visibility": get_partial_visibility
}

# Option 1: Use individual sections (current approach)
# page_sections = """
# # Dashboard
# 
# """ + section_1 + section_2

# Option 2: Use the TGB-built page (new approach)
# Uncomment this to use section3 instead:
page_sections = section_3_page

# You can also create multiple pages for navigation
pages = {
    "Dashboard_Sections": page_sections,
    "Dashboard_TGB": section_3_page
}

if __name__ == "__main__":
    try:
        # Custom CSS file for styling
        gui = Gui(page=page_sections, css_file="./static/style.css")

        # Detect if running in Docker or locally
        import os
        is_docker = os.path.exists('/.dockerenv')
        
        if is_docker:
            host = "0.0.0.0"
            run_browser = False
            print("Running in Docker container")
            print("Open your browser and go to: http://localhost:5000")
        else:
            host = "127.0.0.1"
            run_browser = True
            print("Running locally")
            print("Open your browser and go to: http://127.0.0.1:5000")
        
        print("Starting Taipy application...")
        
        gui.run(
            host=host,
            port=5000,
            debug=True,
            run_browser=run_browser
        )
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
# Grafana

## Grafana API

- **Grafana API** is a RESTful interface that lets you programmatically control nearly every aspect of your Grafana instance.
- 3 Authentication Options to Get API Key

  1. **API Keys** – Simple but being deprecated in newer versions
  2. **Service Accounts**:

     - The recommended approach for automation
     - For most automation tasks, service accounts are the best bet.
     - Here's how to set up:
       - Navigate to **Administration** → **Service Accounts**
       - Create a new service account
       - Assign appropriate permissions (**Viewer**, **Editor**, or **Admin**)
       - Generate and securely store your token

  3. **Basic Auth** – For when you're testing or in a pinch

- **Sampl API Calls**

  1. Checking Health Of Grafana Instance
     ```sh
        curl -H "Authorization: Bearer your-token-here" https://your-grafana-instance/api/health
     ```

- **3 Essential Grafana API Endpoints for Everyday Use**:

  1. **Dashboard Management**

     - Creating and managing dashboards is where the API really shines. Here's how to get all dashboards:
       ```sh
        curl -H "Authorization: Bearer your-token-here" https://your-grafana-instance/api/search
       ```
     - To grab a specific dashboard:
       ```sh
        curl -H "Authorization: Bearer your-token-here" https://your-grafana-instance/api/dashboards/uid/your-dashboard-uid
       ```
     - For creating a dashboard:
       ```sh
        curl -X POST \
            -H "Authorization: Bearer your-token-here" \
            -H "Content-Type: application/json" \
            -d '{"dashboard": {"title": "API Created Dashboard", "panels": [...]}, "overwrite": true, "message": "Created via API"}' \
            https://your-grafana-instance/api/dashboards/db
       ```

  2. **Data Source Operations**

     - Data sources are essential for Grafana dashboards, as they provide the metrics and logs that power your visualizations. The Grafana API allows you to manage data sources programmatically instead of configuring them manually through the UI.
     - Listing All Data Sources
       ```sh
        curl -H "Authorization: Bearer your-token-here" https://your-grafana-instance/api/datasources
       ```
     - **Creating a New Prometheus Data Source**
       ```sh
        curl -X POST \
            -H "Authorization: Bearer your-token-here" \
            -H "Content-Type: application/json" \
            -d '{"name":"My Prometheus","type":"prometheus","url":"http://prometheus:9090","access":"proxy"}' \
            https://your-grafana-instance/api/datasources
       ```

  3. **User and Team Management**
     - List all users
       ```sh
        curl -H "Authorization: Bearer your-token-here" https://your-grafana-instance/api/users
       ```
     - Create a new team
       ```sh
        curl -X POST \
            -H "Authorization: Bearer your-token-here" \
            -H "Content-Type: application/json" \
            -d '{"name":"DevOps Team"}' \
            https://your-grafana-instance/api/teams
       ```

## How to Automate Dashboard Creation with Python

- Instead of relying on Bash scripts for simple API calls, Python provides more flexibility and scalability. The `requests` library makes it easy to interact with Grafana’s API and automate dashboard creation.
- Step 1: Setting Up API Credentials

  - Setup API Credentials

    ```py
        import requests
        import json

        GRAFANA_URL = "https://your-grafana-instance"
        API_TOKEN = "your-token-here"
        HEADERS = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
    ```

  - Imports `requests` and `json` to handle API calls and data processing.
  - Defines the `GRAFANA_URL` (your Grafana instance URL) and `API_TOKEN` (your API key for authentication).
  - Sets up the `HEADERS`, which include authorization and content type (JSON).

- **Step 2**: **Loading a Dashboard Template**

  - Loading a Dashboard Template
    ```py
        # Load dashboard template from file
        with open('dashboard_template.json', 'r') as f:
            dashboard = json.load(f)
    ```
  - Reads a dashboard template JSON file, which contains the structure of a Grafana dashboard.
  - Loads the JSON data into the `dashboard` variable for further modifications.

- **Step 3**: **Customizing the Dashboard for Each Service**

  - Customizing the Dashboard for Each Service

    ```py
        services = ["auth", "payments", "inventory", "shipping"]

        for service in services:
            # Customize dashboard for this service
            dashboard["dashboard"]["title"] = f"{service.capitalize()} Service Dashboard"
    ```

  - Defines a list of services (auth, payments, inventory, shipping).
  - Loops through each service and updates the dashboard title to match the service name.

- **Step 4**: **Updating Dashboard Panels with Service-Specific Metrics**

  - Updating Dashboard Panels with Service-Specific Metrics
    ```py
        # Update variables and panel targets
        for panel in dashboard["dashboard"]["panels"]:
            panel["targets"][0]["expr"] = panel["targets"][0]["expr"].replace("${service}", service)
    ```
  - Loops through the panels in the dashboard and updates the PromQL expressions to reflect the specific service.
  - Uses `.replace("${service}", service)` to dynamically modify queries.

- **Step 5**: **Sending the Dashboard to Grafana**

  - Sending the Dashboard to **Grafana**
    ```py
        # Create the dashboard
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            headers=HEADERS,
            json={
                "dashboard": dashboard["dashboard"],
                "overwrite": True,
                "message": f"Updated {service} dashboard via API"
            }
        )
    ```
  - Makes a `POST` request to the Grafana API (`/api/dashboards/db`) to create or update the dashboard.
  - Includes:`"dashboard": dashboard["dashboard"]` → The modified dashboard `JSON."overwrite": True` → Ensures existing dashboards with the same name are updated."message" → Adds a commit-style message for tracking changes.

- **Step 6**: **Handling the API Response**
  - Handling the API Response
    ```py
        if response.status_code == 200:
            print(f"Successfully created dashboard for {service}")
        else:
            print(f"Failed to create dashboard for {service}: {response.text}")
    ```
  - Checks the HTTP status code to determine if the request was successful.
  - If `200 OK`, prints a success message; otherwise, prints the error response.

# Resources and Further Reading

1. [Last9 - Getting Started with the Grafana API: Practical Use Cases](https://last9.io/blog/getting-started-with-the-grafana-api/?ref=dailydev)

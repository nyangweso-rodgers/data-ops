# flows/test_flow.py - Updated for Prefect 3
from prefect import flow, task
import pandas as pd

@task
def process_data():
    df = pd.DataFrame({"column": [1, 2, 3]})
    return df.sum().sum()

@flow(name="Test Flow")
def test_flow():
    result = process_data()
    print(f"Sum: {result}")

# For development/testing only
if __name__ == "__main__":
    # Option 1: Just run the flow locally
    # test_flow()
    
    # Option 2: Deploy and serve the flow (Prefect 3 way)
    test_flow.serve(
        name="test-flow-deployment",
        tags=["production", "test"],
        description="Test flow deployment"
    )
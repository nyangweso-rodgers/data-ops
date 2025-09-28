# deployments/deploy.py - Using serve() method
import sys
import os
sys.path.append('/app')

from flows.test_flow import test_flow

def deploy_all_flows():
    """Deploy all flows using serve() method"""
    
    print("Deploying flows using Prefect 3 serve() method...")
    
    # Use serve() method which is simpler for same-environment deployments
    test_flow.serve(
        name="test-flow-deployment",
        tags=["production", "test"],
        description="Test flow deployment using serve method",
        interval=None  # Manual runs only, or set to seconds for scheduled runs
    )

if __name__ == "__main__":
    deploy_all_flows()
"""
This file has been generated from dag_runner.j2
"""
from airflow import DAG
from openmetadata_managed_apis.workflows import workflow_factory

workflow = workflow_factory.WorkflowFactory.create("/opt/airflow/dag_generated_configs/c40f0f3c-57d0-4879-8eef-c35e25e04b47.json")
workflow.generate_dag(globals())
dag = workflow.get_dag()
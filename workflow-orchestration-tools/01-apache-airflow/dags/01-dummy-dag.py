import requests
from datetime import datetime

from airflow import DAG

# allows you to execute a Python function as a task in the workflow.
from airflow.operators.python_operator import PythonOperator

# A utility for date manipulation
from airflow.utils.dates import days_ago

# Python functions that will do some job.
def print_greeting():
    print("Hello, Airflow enthusiasts!")
    
def print_current_date():
    print("The time is now: {}".format(datetime.now()))
    
def print_random_quote():
    response = requests.get("https://api.quotable.io/random")
    data = response.json()
    print("Quote:",data["content"])
    
# The DAG object
dag = DAG(
    'dummy_dag', # unique identifier
    default_args={'start_date': days_ago(1)}, # sets the start date to one day before the current date.
    schedule_interval='*/5 * * * *', # Sets the DAG to run once a day at 13:00 (1 PM). 
    catchup=False # Prevents Airflow from running past executions that haven't been run yet since the last execution, when the DAG is activated.
)

# These are used to define tasks that execute Python functions:

print_greeting_task = PythonOperator(
    task_id='print_greeting',
    python_callable=print_greeting,
    dag=dag
)

print_current_date_task = PythonOperator(
    task_id='print_current_date',
    python_callable=print_current_date,
    dag=dag
)

print_random_quote_task = PythonOperator(
    task_id='print_random_quote',
    python_callable=print_random_quote,
    dag=dag
)

# Task Dependency: sets the execution order of the tasks
print_greeting_task >> print_current_date_task >> print_random_quote_task
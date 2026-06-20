# Building a Real-time Dashboard with FastAPI and Svelte

## Table of Contents

# Objective

- Build a real-time analytics dashboard using **FastAPI** and **Svelte**.

## Install Required Dependencies

```sh
    (venv)$ pip install fastapi==0.115.11 uvicorn==0.34.0 sse-starlette==2.2.1
```

## Start the Server

```sh
    (venv)$ python main.py
```

- Your API should now be running at http://localhost:8000. You can check the API documentation at http://localhost:8000/docs. After visiting the http://localhost:8000 you should see the following output:

```sh
    {
        "message": "Welcome to the Sensor Dashboard API"
        }
```

## Start the Svelte Development Server

- With the backend running in one terminal window, start the Svelte development server:

  ```sh
      $ npm run dev
  ```

- Your dashboard should now be accessible at http://localhost:5173, showing real-time sensor data updates!

# Resources and Further Reading

1. [testdriven.io - Building a Real-time Dashboard with FastAPI and Svelte](https://testdriven.io/blog/fastapi-svelte/)

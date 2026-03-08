# Diabetest Predictor Model Using Random Forest

# About the Dataset

- The diabetes dataset is a collection of 442 patient records with 10 physiological features. The target is a quantitative measure of disease progression one year after baseline: higher numbers indicate more advanced progression.

# Training the Model

# Testing the API Locally

- Run the following command from the project's root directory:
  ```sh
    uvicorn app:main:app --reload --port 8000
  ```
- Open the browswer to http://localhost:8000/ and you’ll see the FastAPI app running. Try making a prediction with the example data.
- You can also test with curl:
  ```sh
    curl -X POST "http://localhost:8000/predict" \
    -H "Content-Type: application/json" \
    -d '{
        "age": 0.05,
        "sex": 0.05,
        "bmi": 0.06,
        "bp": 0.02,
        "s1": -0.04,
        "s2": -0.04,
        "s3": -0.02,
        "s4": -0.01,
        "s5": 0.01,
        "s6": 0.02
    }'
  ```
- Sample output:
  ```sh
    {"predicted_progression_score":213.34,
    "interpretation":"Above average progression"}
  ```

# Containerizing with Docker

- Create a requirements.txt with:

  ```txt
    fastapi==0.115.12
    uvicorn==0.34.2
    scikit-learn==1.6.1
    pandas==2.2.3
    numpy==2.2.6
  ```

- Create Dockerfile:

  ```Dockerfile
    # Use Python 3.11 slim image
    FROM python:3.11-slim

    # Set working directory
    WORKDIR /app

    # Install system dependencies (if needed)
    RUN apt-get update && apt-get install -y \
        && rm -rf /var/lib/apt/lists/*

    # Copy requirements and install Python dependencies
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # Copy application code
    COPY app/ ./app/
    COPY models/ ./models/

    # Expose port
    EXPOSE 8000

    # Run the application
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- **Remarks**:

  - The slim image keeps our container small, and `--no-cache-dir` prevents pip from storing cached packages, further reducing size.

- Build Docker image by:

  ```sh
    docker build -t diabetes-predictor .
  ```

- Run the container from your built image:

  ```sh
    docker run -d -p 8000:8000 --name diabetes-container diabetes-predictor
  ```

- Test the API:
  ```sh
    curl http://localhost:8000
  ```

# Optional: Create a docker-compose.yml

- If you want easier management, create docker-compose.yml:

  ```yml
  services:
  api:
    build: .
    ports:
      - "8000:8000"
    container_name: diabetes-container
    restart: unless-stopped
  ```

- Then, run:
  ```sh
    docker-compose up -d    # Start
    docker-compose down     # Stop
    docker-compose logs -f  # View logs
  ```

# Test FastAPI Endpoint

## (Option 1) Use FastAPI's Built-in Interactive Docs

- Open your browser and go to: http://localhost:8000/docs. This gives you a beautiful interactive UI where you can:
  - See all your endpoints
  - Click "**Try it out**" on the `/predict` endpoint
  - Fill in the patient data
  - Click "**Execute**" to test

## (Option 2): Use curl (Command Line)

- Health check:

  ```sh
    curl http://localhost:8000/
  ```

- Make a prediction:
  ```sh
    curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{
        "age": 0.05,
        "sex": 0.05,
        "bmi": 0.06,
        "bp": 0.02,
        "s1": -0.04,
        "s2": -0.04,
        "s3": -0.02,
        "s4": -0.01,
        "s5": 0.01,
        "s6": 0.02
    }'
  ```

## (Option 3): Use Python requests

- Use python requests:

  ```py
    import requests

    # Health check
    response = requests.get("http://localhost:8000/")
    print(response.json())

    # Make prediction
    patient_data = {
        "age": 0.05,
        "sex": 0.05,
        "bmi": 0.06,
        "bp": 0.02,
        "s1": -0.04,
        "s2": -0.04,
        "s3": -0.02,
        "s4": -0.01,
        "s5": 0.01,
        "s6": 0.02
    }

    response = requests.post("http://localhost:8000/predict", json=patient_data)
    print(response.json())
  ```

## (Option 4): Use Postman or Insomnia (GUI tools)

- Create a POST request to http://localhost:8000/predict
- Set header: Content-Type: application/json
- Add the JSON body with patient data

# Publishing to Docker Hub

- Tagging docker Image

  - Before pushing, we need to tag the image with your Docker Hub username. Docker uses a specific naming convention:
    ```sh
        $ docker tag diabetes-predictor your-username/diabetes-predictor:v1.0
    ```
  - The v1.0 is a version tag. It’s good practice to version your images so you can track changes and roll back if needed.
  - Let’s also create a latest tag, which many deployment platforms use by default:
    ```sh
        $ docker tag diabetes-predictor your-username/diabetes-predictor:latest
    ```
  - Check your tagged images:
    ```sh
        docker images | grep diabetes-predictor
    ```

- Pushing to Docker Hub:
  - Push the image to docker hub by:
    ```sh
        $ docker push your-username/diabetes-predictor:v1.0
        $ docker push your-username/diabetes-predictor:latest
    ```

# Resources and Further Reading

1. [Machine Learning Mastery - Step-by-Step Guide to Deploying Machine Learning Models with FastAPI and Docker](https://machinelearningmastery.com/step-by-step-guide-to-deploying-machine-learning-models-with-fastapi-and-docker/?ref=dailydev)

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
# Use an official Python runtime as the base image
# FROM python:3.11-slim
FROM python:3.12.0

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
#COPY requirements.txt .

# Install any needed packages specified in requirements.txt
#RUN pip install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 3005

# Command to run your script
CMD ["python", "app.py"]
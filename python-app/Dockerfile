# Use an official Python runtime as the base image
FROM python:3.12.0

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Define the default command to run when the container starts
CMD ["python", "app.py"]
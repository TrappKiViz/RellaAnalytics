# Dockerfile for Rella Analytics Backend

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
COPY . .

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variables (optional)
# ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_RUN_PORT=5001

# Command to run the application using Flask's built-in server (for development)
# For production, use a proper WSGI server like Gunicorn:
# CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
CMD ["python", "app.py"] 
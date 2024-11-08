# app/Dockerfile
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt requirements.txt

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the application code
COPY ./app/main.py main.py

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
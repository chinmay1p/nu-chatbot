# Use the official Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your application files (including app.py and the data/vectorstore folder)
COPY . .

# Command to run the application using Gunicorn
# Gunicorn is used as the production WSGI server. 
# Render automatically injects the $PORT environment variable.
# Format: gunicorn --bind 0.0.0.0:$PORT <module_name>:<flask_app_instance_name>
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
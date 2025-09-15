# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]

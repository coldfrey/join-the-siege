# Use the official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set the working directory
WORKDIR /app

# Install system dependencies needed by OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Set the PYTHONPATH to include the /app and /app/src directories
ENV PYTHONPATH="/app:/app/src"

# Expose the port the app runs on
EXPOSE 8080

# Run the Flask app from the src directory
CMD ["python", "src/app.py", "--host=0.0.0.0", "--port=$PORT"]


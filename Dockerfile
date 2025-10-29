# Use Python 3.11 (avoid 3.13 because of audioop issue)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose port for Flask keep-alive
EXPOSE 8080

# Run your app
CMD ["python", "main.py"]

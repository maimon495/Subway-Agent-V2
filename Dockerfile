FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn jinja2

# Copy application
COPY . .

# Run the web server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

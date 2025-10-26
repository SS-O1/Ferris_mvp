# Multi-stage build for Ferris on Hugging Face Spaces
FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY requirements.txt package.json ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
RUN npm install

# Copy application code
COPY . .

# Expose ports
EXPOSE 7860 3000

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Node.js server in background\n\
node server.js &\n\
# Start FastAPI server on port 7860 (HF Spaces default)\n\
uvicorn app.main:app --host 0.0.0.0 --port 7860\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]

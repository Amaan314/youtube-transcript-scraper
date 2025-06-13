# Use a slim Python image, it's generally smaller
FROM python:3.12.7-slim

# Set working directory inside the container for initial root operations
WORKDIR /app

# Install system dependencies required for Playwright browsers (as root)
RUN apt-get update && apt-get install -y \
    libnss3 \
    libxss1 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libasound2 \
    fonts-liberation \
    ca-certificates \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user (as root)
RUN useradd -m user

# Set environment variables for the user's home and path.
# Crucially, set PLAYWRIGHT_BROWSERS_PATH before installing them.
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/home/user/.cache/ms-playwright/

# Switch to the non-root user *before* installing Python packages and Playwright browsers
USER user

# Set the working directory to your application's home for the non-root user
WORKDIR /home/user/app

# Copy requirements.txt and install Python dependencies (as 'user')
COPY --chown=user ./requirements.txt /home/user/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /home/user/app/requirements.txt

# --- IMPORTANT CHANGE HERE ---
# Install Playwright browser binaries (as 'user')
# REMOVE --with-deps because system dependencies were already installed as root
RUN playwright install chromium firefox webkit

# Copy your application code into the container (as 'user')
COPY --chown=user . /home/user/app

# Expose the port FastAPI will run on
EXPOSE 7860

# Command to run your FastAPI application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info", "--proxy-headers"]

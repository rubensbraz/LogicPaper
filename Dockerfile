# Use Python on Alpine Linux for minimal footprint
FROM python:3.11-alpine

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Ensures python output is sent straight to terminal (logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# Create directory for the application
WORKDIR $APP_HOME

# Install System Dependencies
# 1. libreoffice: The core engine for PDF conversion
# 2. openjdk11-jre: Java Runtime is REQUIRED for LibreOffice to run properly
# 3. ttf-dejavu, ttf-liberation, ttf-freefont: Essential fonts to prevent rendering glitches
# 4. tzdata: Timezone support
# 5. build-base, libffi-dev, musl-dev: Compilers for Python C-extensions (Pandas/Numpy)
# 6. jpeg-dev, zlib-dev: For Pillow (Image processing)
RUN apk add --no-cache \
    libreoffice \
    openjdk11-jre \
    font-noto \
    ttf-dejavu \
    ttf-liberation \
    ttf-freefont \
    tzdata \
    build-base \
    libffi-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libxml2-dev \
    libxslt-dev

# Upgrade pip
RUN pip install --upgrade pip

# Install Python Dependencies
# We copy requirements first to leverage Docker cache layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories for data handling
RUN mkdir -p /data/temp

# Copy the Application Code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
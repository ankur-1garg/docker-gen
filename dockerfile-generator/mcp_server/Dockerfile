# mcp_server/Dockerfile

# ---- Base Stage ----
# Use an official Python runtime as a parent image
# Choose a version compatible with your dependencies (e.g., 3.11 used in examples)
# Using 'slim' reduces image size
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., for libraries with C extensions)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*
# For now, we likely don't need extra system packages.

# ---- Builder Stage (for dependencies) ----
# This stage installs dependencies, allowing better caching
FROM base as builder
WORKDIR /app
# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .
# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

    # ---- Final Stage ----
        FROM base as final

        # Create non-root user
        ARG USER=appuser
        ARG UID=1001
        ARG GID=1001
        RUN groupadd -g $GID $USER && \
            useradd -u $UID -g $GID -ms /bin/sh $USER
    
        WORKDIR /app
    
        # Copy installed dependencies from the builder stage's site-packages
        # Adjust python3.11 path if using a different Python version
        COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
        COPY --from=builder /usr/local/bin /usr/local/bin 
        # Copy executables like uvicorn
    
        # Copy the application code AND config file
        COPY ./app ./app
        COPY harbor_mapping.yaml .
    
        # Change ownership to the non-root user AFTER copying everything
        RUN chown -R $USER:$USER /app
    
        USER $USER
    
        EXPOSE 8000
        CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Stage 1: Build the frontend
FROM node:7.8 AS frontend-build

WORKDIR /app

# Copy all files (backend and frontend)
COPY . .

# Install dependencies and build the frontend
RUN rm -f /usr/local/bin/yarn /usr/local/bin/yarnpkg && \
    npm install -g yarn && \
    yarn && \
    yarn build:dev

# Stage 2: Set up the backend
FROM python:3.9

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libhdf5-dev postgresql-client

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools

# Copy all files (backend and frontend builds)
COPY . .

# Copy the frontend build files into the appropriate static directory
COPY --from=frontend-build /app/client/dist/ /app/client/dist/

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose the necessary port
EXPOSE 8000

# Copy the post-backend script and make it executable
COPY post-backend.sh /app/post-backend.sh
RUN chmod +x /app/post-backend.sh

# Define the entry point for the container
# ENTRYPOINT ["./post-backend.sh", "prod"]

#!/bin/bash

# Shutting down services just to confirm they are down
docker-compose down

# Check if the first parameter is passed
if [ -z "$1" ]; then
  echo "No environment specified. Please use 'dev' or 'prod'."
  exit 1
fi

# Set the environment file based on the parameter
if [ "$1" == "dev" ]; then
  ENV_FILE="dev.env"
elif [ "$1" == "prod" ]; then
  ENV_FILE="prod.env"
else
  echo "Invalid environment specified. Please use 'dev' or 'prod'."
  exit 1
fi

# Run docker-compose with the appropriate environment file
echo "Using $ENV_FILE"
docker-compose --env-file $ENV_FILE up

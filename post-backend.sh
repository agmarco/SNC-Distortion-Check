#!/bin/bash

# Install required packages (already done in the Dockerfile)
# apt-get update && apt-get install -y libhdf5-dev postgresql-client

# Upgrade pip and setuptools (already done in the Dockerfile)
# pip install --upgrade pip setuptools

# Install Python dependencies (already done in the Dockerfile)
# pip install -r requirements.txt

# Set the environment file based on the parameter
if [ "$1" == "dev" ]; then
  ENV_FILE="dev.env"
elif [ "$1" == "prod" ]; then
  ENV_FILE="prod.env"
else
  echo "Invalid environment specified. Please use 'dev' or 'prod'."
  exit 1
fi

echo "Using $ENV_FILE"

# Load environment variables from the selected file
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' $ENV_FILE | xargs)
else
  echo "Environment file $ENV_FILE not found!"
  exit 1
fi

# Parse the DATABASE_URL environment variable
DATABASE_URL=${DATABASE_URL:-}
DB_USER=$(echo $DATABASE_URL | sed -n 's|.*//\([^:]*\):.*|\1|p')
DB_PASSWORD=$(echo $DATABASE_URL | sed -n 's|.*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\(.*\)/.*|\1|p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's|.*\/\(.*\)|\1|p')

echo "DATABASE_URL: $DATABASE_URL"

echo "Connecting to:"
echo "DB_HOST: $DB_HOST"
echo "DB_USER: $DB_USER"
echo "PGPORT: 5432"
echo "DB_NAME: $DB_NAME"
echo "DB_PASSWORD: $DB_PASSWORD"

export PGHOST=$DB_HOST
export PGUSER=$DB_USER
export PGPORT=5432
export PGDATABASE=$DB_NAME
export PGPASSWORD=$DB_PASSWORD

# Wait until the database is ready
until pg_isready -h cirstesting.postgres.database.azure.com -p 5432 -U cirs; do
  echo "Waiting for database $DB_NAME to be ready..."
  sleep 2
done

echo "Database $DB_NAME is ready."

# Check if migrations have already been applied
export PGPASSWORD="$DB_PASSWORD"
MIGRATION_CHECK=$(psql -h cirstesting.postgres.database.azure.com -p 5432 -U cirs postgres -tAc "SELECT 1 FROM django_migrations LIMIT 1;")

if [ "$MIGRATION_CHECK" = "1" ]; then
  echo "Migrations are already applied. Skipping migrations and demo data generation."
else
  echo "No migrations found. Applying migrations and generating demo data."
  
  # Run Django commands
  python /app/server/manage.py migrate
  python /app/server/manage.py generate_demo_data
fi

# Run the server
python /app/server/manage.py runserver 0.0.0.0:8000

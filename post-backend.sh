#!/bin/bash
  
# Install required packages
apt-get update && apt-get install -y libhdf5-dev postgresql-client

# Upgrade pip and setuptools
pip install --upgrade pip setuptools

# Install Python dependencies
pip install -r requirements.txt

# Parse the DATABASE_URL environment variable
DATABASE_URL=${DATABASE_URL:-}
DB_USER=$(echo $DATABASE_URL | sed -n 's|.*//\([^:]*\):.*|\1|p')
DB_PASSWORD=$(echo $DATABASE_URL | sed -n 's|.*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\(.*\)/.*|\1|p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's|.*\/\(.*\)|\1|p')

# Wait until the database is ready
until pg_isready -h "$DB_HOST" -U "$DB_USER"; do
  echo "Waiting for database $DB_NAME to be ready..."
  sleep 2
done

echo "Database $DB_NAME is ready."

# Check if migrations have already been applied
export PGPASSWORD="$DB_PASSWORD"
MIGRATION_CHECK=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1 FROM django_migrations LIMIT 1;")

if [ "$MIGRATION_CHECK" = "1" ]; then
  echo "Migrations are already applied. Skipping migrations and demo data generation."
else
  echo "No migrations found. Applying migrations and generating demo data."
  

  # Run Django commands
  python server/manage.py migrate
  python server/manage.py generate_demo_data
fi

# Run the server
python server/manage.py runserver 0.0.0.0:8000

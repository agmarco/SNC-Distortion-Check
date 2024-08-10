FROM node:7.8 AS client-build

WORKDIR /app

RUN rm -f /usr/local/bin/yarn /usr/local/bin/yarnpkg && npm install -g yarn

COPY . /app
RUN yarn 

RUN yarn build:dev

FROM python:3.9 AS backend-build

COPY --from=client-build /app /app

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql postgresql-contrib \
    libhdf5-dev && rm -rf /var/lib/apt/lists/*

# Modify PostgreSQL configuration for password authentication
RUN sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/15/main/postgresql.conf && \
    echo "host all all 127.0.0.1/32 md5" >> /etc/postgresql/15/main/pg_hba.conf && \
    echo "host all all ::1/128 md5" >> /etc/postgresql/15/main/pg_hba.conf

RUN service postgresql start

# Install Python dependencies
RUN pip install --upgrade pip setuptools

RUN pip install -r requirements.txt

# Expose the port
EXPOSE 8000

# Set the working directory to the server


# # Run the Django development server
CMD ["python", "/server/manage.py", "runserver", "0.0.0.0:8000"]
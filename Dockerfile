FROM node:7.8 AS client-build

WORKDIR /app

RUN rm -f /usr/local/bin/yarn /usr/local/bin/yarnpkg && npm install -g yarn

COPY . /app
RUN yarn 

RUN yarn build:dev

FROM python:3.9 AS backend-build

COPY --from=client-build /app /app

WORKDIR /app

COPY dev.env /app/.env

# Install Python dependencies
RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt
# run db migration 
RUN  python server/manage.py migrate
RUN python server/manage.py generate_demo_data
# Expose the port
EXPOSE 8000

# Set the working directory to the server
WORKDIR /app/server
# # Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
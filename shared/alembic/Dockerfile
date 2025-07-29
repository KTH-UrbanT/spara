FROM python:3.10-slim

WORKDIR /app

# Install Alembic and PostgreSQL adapter
RUN pip install alembic psycopg2-binary

# Copy migration files
COPY migrations/ ./migrations/

# Set up Alembic configuration
COPY alembic.ini ./alembic.ini

#CMD alembic upgrade head
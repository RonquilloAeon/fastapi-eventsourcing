FROM python:3.13-slim

WORKDIR /app

# Install poetry
RUN pip install poetry==1.7.1

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Run as non-root user for better security
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
USER appuser

# Copy the rest of the application
COPY src /app/src/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
ENTRYPOINT ["uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

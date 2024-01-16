# Use an official Python runtime as a parent image
# modify to python 3.9
 FROM python:3.9-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory content to /app in the container
ADD . /app

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Add the current directory contents into the container at /app
ADD . /app

# Switch to root user
USER root

# Train the Rasa NLU model
RUN rasa train 


# Download spacy language model
RUN python -m spacy download en_core_web_md
RUN python -m spacy link en_core_web_md en
# Use an official Python runtime as a parent image
FROM python:3.7-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory content to /app in the container
ADD . /app

# Install Rasa and Rasa[spacy]
RUN pip install rasa[spacy]

# Download spacy language model
RUN python -m spacy download en_core_web_md
RUN python -m spacy link en_core_web_md en

# Initialize a new Rasa project
RUN rasa init --no-prompt
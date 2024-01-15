version: '3.0'
services:
  rasa:
    image: rasa/rasa:latest-full
    ports:
      - 5005:5005
    volumes:
      - ./:/app
    environment:
      RASA_DUCKLING_HTTP_URL: http://rasa-duckling:8000
    command: run --model models/dialogue --endpoints endpoints.yml
  rasa-actions:
    build:
      context: .
    ports:
      - 5055:5055
  rasa-duckling:
    image: rasa/duckling
    ports:
      - 8000:8000
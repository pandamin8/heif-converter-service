FROM python:3.10.5-slim-buster

WORKDIR /converter

RUN pip install Pillow flask pyheif python-dotenv waitress

COPY . .

CMD ["python", "converter.py"]
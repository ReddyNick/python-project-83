PORT ?= 8000

install:
	poetry install

build:
	./build.sh

dev:
	poetry run flask --app page_analyzer:app run --debug

lint:
	poetry run flake8 page_analyzer

start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
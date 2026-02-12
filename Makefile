.PHONY: run install migrate

run:
	python -m bot.main

install:
	pip install -r requirements.txt

migrate:
	python -m bot.db --init

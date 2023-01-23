update-precommit:
	pre-commit autoupdate

create-venv:
	python3 -m venv .venv

run:
	export FLASK_APP=app && export FLASK_DEBUG=True && python3 app.py

lint:
	pre-commit install && pre-commit run -a -v

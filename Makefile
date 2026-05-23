.PHONY: install test run demo docker lint clean

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest

run:
	uvicorn ey_audit_ai.main:app --reload --host 0.0.0.0 --port 8000

demo:
	python -m ey_audit_ai.cli run-demo

docker:
	docker compose up --build

clean:
	rm -rf outputs .pytest_cache **/__pycache__

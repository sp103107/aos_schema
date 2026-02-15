.PHONY: install test run-foreman run-sorcerer

install:
	pip install -r requirements.txt

test:
	python -m unittest discover -s tests -p "test_*.py"

run-foreman:
	python -m aos_runtime.cli examples/envelopes/foreman_task.json

run-sorcerer:
	python -m aos_runtime.cli examples/envelopes/sorcerer_task.json

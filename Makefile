.PHONY: run setup clean install

setup:
	pip install .

clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/ .coverage htmlcov/

run:
	streamlit run app.py --server.port 8501

dev:
	streamlit run app.py --server.port 8501 --server.headless true 
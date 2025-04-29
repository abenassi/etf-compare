.PHONY: run setup

setup:
	pip install -r requirements.txt

run:
	streamlit run app.py --server.port 8501 
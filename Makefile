run_api:
	uvicorn api.fast:app --reload --port 8000

run_streamlit:
	streamlit run streamlit/app.py

deploy:
	gcloud run deploy fake-news-detector --source . --region europe-west1 --allow-unauthenticated --memory 4Gi

logs:
	gcloud run services logs read fake-news-detector --region=europe-west1 --limit=50

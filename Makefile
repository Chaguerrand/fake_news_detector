run_api:
	uvicorn api.fast:app --reload --port 8000

run_streamlit:
	streamlit run streamlit/app.py

deploy:
	gcloud run deploy fake-news-detector --source . --region europe-west1 --allow-unauthenticated --memory 4Gi --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,TAVILY_API_KEY=TAVILY_API_KEY:latest,GCP_SERVICE_ACCOUNT=GCP_SERVICE_ACCOUNT:latest

logs:
	gcloud run services logs read fake-news-detector --region=europe-west1 --limit=50

pip_req:
	pip install -r requirements.txt

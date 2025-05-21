import requests

def start_prediction(prompt):
    url = "http://localhost:5002/predictions"
    data = {
        "input": {"prompt": prompt},
        "webhook": "http://host.docker.internal:8000/webhook/prediction",
        "webhook_events_filter": ["output", "completed"]
    }
    headers = {
        "Content-Type": "application/json",
        "Prefer": "respond-async"
    }
    resp = requests.post(url, json=data, headers=headers)
    print("Prediction started:", resp.json())

if __name__ == "__main__":
    start_prediction("The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog")
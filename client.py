import requests
import json
import sseclient

# Start a prediction
response = requests.post(
    "http://localhost:8000/api/predict",
    json={"prompt": "The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog"}
)
prediction_id = response.json()["prediction_id"]
print(f"Started prediction: {prediction_id}")

# Stream the results using SSE
url = f"http://localhost:8000/api/stream/{prediction_id}"

# Create a new SSE client with the URL string, not the response object
client = sseclient.SSEClient(url)

# Process the events
for event in client:
    data = json.loads(event.data)
    if "token" in data:
        print(data["token"], end="", flush=True)
    elif data.get("status") == "complete":
        print("\nGeneration complete!")
        break
    elif data.get("status") == "error":
        print(f"\nError: {data.get('error')}")
        break
from flask import Flask, request
import sys

app = Flask(__name__)

@app.route("/webhook/prediction", methods=["POST"])
def prediction_webhook():
    data = request.get_json()
    event = data.get("event", "output")
    output = data.get("output")
    status = data.get("status")
    print(f"[Webhook] Event: {event}, Status: {status}, Output: {output}", flush=True)
    print("\n\n")
    print(data)
    print("\n\n")
    sys.stdout.flush()
    return "", 200

if __name__ == "__main__":
    app.run(port=8000)
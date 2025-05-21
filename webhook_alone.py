from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import threading
import queue
import json
import time
import uuid

app = Flask(__name__)

# Dictionary to track active predictions and their token queues
active_predictions = {}

class PredictionManager:
    def __init__(self):
        self.predictions = {}  # Maps prediction_ids to token queues and metadata
    
    def create_prediction(self):
        prediction_id = str(uuid.uuid4())
        self.predictions[prediction_id] = {
            "queue": queue.Queue(),
            "complete": False,
            "error": None
        }
        return prediction_id
    
    def add_tokens(self, cog_id, tokens):
        for pred_id, pred_data in self.predictions.items():
            if pred_data.get("cog_id") == cog_id:
                for token in tokens:
                    pred_data["queue"].put(token)
                return True
        return False
    
    def mark_complete(self, cog_id, error=None):
        for pred_id, pred_data in self.predictions.items():
            if pred_data.get("cog_id") == cog_id:
                pred_data["complete"] = True
                pred_data["error"] = error
                # Add None as sentinel to indicate completion
                pred_data["queue"].put(None)
                return True
        return False
    
    def get_prediction(self, prediction_id):
        return self.predictions.get(prediction_id)
    
    def cleanup(self, prediction_id, timeout=300):
        """Clean up prediction data after timeout seconds"""
        def _cleanup():
            time.sleep(timeout)
            if prediction_id in self.predictions:
                del self.predictions[prediction_id]
        
        t = threading.Thread(target=_cleanup)
        t.daemon = True
        t.start()

# Global prediction manager
prediction_manager = PredictionManager()

@app.route('/webhook/prediction', methods=['POST'])
def webhook_handler():
    data = request.json
    cog_id = data.get('started_at')
    
    # Process the output tokens
    if 'output' in data and data['output']:
        current_tokens = data['output']
        
        # Get the previous tokens count for this prediction
        previous_count = getattr(webhook_handler, f'prev_count_{cog_id}', 0)
        
        # Extract only new tokens
        if previous_count < len(current_tokens):
            new_tokens = current_tokens[previous_count:]
            setattr(webhook_handler, f'prev_count_{cog_id}', len(current_tokens))
            
            # Add tokens to all predictions tracking this cog_id
            prediction_manager.add_tokens(cog_id, new_tokens)
    
    # Check if prediction is complete
    if data.get('status') == 'succeeded':
        prediction_manager.mark_complete(cog_id)
    elif data.get('status') in ['failed', 'canceled']:
        prediction_manager.mark_complete(cog_id, error=data.get('error', 'Prediction failed'))
    
    return jsonify({"status": "received"}), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        request_data = request.json
        prompt = request_data.get('prompt')
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        # Create a new prediction ID for this request
        prediction_id = prediction_manager.create_prediction()
        
        # Start the cog prediction asynchronously
        threading.Thread(
            target=start_cog_prediction,
            args=(prompt, prediction_id)
        ).start()
        
        # Return the prediction ID so the client can stream results
        return jsonify({"prediction_id": prediction_id})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_cog_prediction(prompt, prediction_id):
    try:
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
        response_data = resp.json()
        
        # Store the cog_id (started_at timestamp) for this prediction
        pred_data = prediction_manager.get_prediction(prediction_id)
        if pred_data:
            pred_data["cog_id"] = response_data.get('started_at')
        
        # Schedule cleanup of this prediction data
        prediction_manager.cleanup(prediction_id)
        
    except Exception as e:
        prediction_manager.mark_complete(prediction_id, error=str(e))

@app.route('/api/stream/<prediction_id>', methods=['GET'])
def stream_prediction(prediction_id):
    prediction_data = prediction_manager.get_prediction(prediction_id)
    
    if not prediction_data:
        return jsonify({"error": "Prediction not found"}), 404
    
    def generate():
        token_queue = prediction_data["queue"]
        
        # Send event stream header
        yield "data: {\"status\": \"started\"}\n\n"
        
        while True:
            try:
                # Get token from queue with timeout
                token = token_queue.get(timeout=60)
                
                # None is our sentinel value for completion
                if token is None:
                    if prediction_data["error"]:
                        yield f"data: {{\"status\": \"error\", \"error\": \"{prediction_data['error']}\"}}\n\n"
                    else:
                        yield "data: {\"status\": \"complete\"}\n\n"
                    break
                
                # Send the token as an event
                yield f"data: {{\"token\": {json.dumps(token)}}}\n\n"
                
            except queue.Empty:
                # Send a keep-alive message
                yield "data: {\"status\": \"processing\"}\n\n"
                
                # If prediction is marked complete but queue is empty, we're done
                if prediction_data["complete"]:
                    yield "data: {\"status\": \"complete\"}\n\n"
                    break
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, threaded=True)
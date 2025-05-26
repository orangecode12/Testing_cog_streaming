from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import queue
import json
import uuid
import threading

app = Flask(__name__)

# Simple dictionary to store predictions
predictions = {}  # prediction_id -> {queue, complete, error}

@app.route('/webhook/prediction', methods=['POST'])
def webhook_handler():
    data = request.json
    prediction_id = data.get('id')
    
    if prediction_id not in predictions:
        return jsonify({"error": "Prediction not found"}), 404
    
    # Handle output tokens
    if 'output' in data and data['output']:
        current_tokens = data['output']
        # Get the previous tokens count for this prediction
        previous_count = predictions[prediction_id].get('token_count', 0)
        
        # Extract only new tokens
        if previous_count < len(current_tokens):
            new_tokens = current_tokens[previous_count:]
            predictions[prediction_id]['token_count'] = len(current_tokens)
            
            # Add new tokens to queue
            for token in new_tokens:
                predictions[prediction_id]['queue'].put(token)
    
    # Handle completion
    if data.get('status') in ['succeeded', 'failed', 'canceled']:
        predictions[prediction_id]['complete'] = True
        predictions[prediction_id]['error'] = data.get('error')
        predictions[prediction_id]['queue'].put(None)  # Completion signal
    
    return jsonify({"status": "received"}), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        prompt = request.json.get('prompt')
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        # Create new prediction entry
        prediction_id = str(uuid.uuid4())
        predictions[prediction_id] = {
            'queue': queue.Queue(),
            'complete': False,
            'error': None,
            'token_count': 0
        }
        
        # Start prediction in background thread
        def start_prediction():
            try:
                url = "http://localhost:5002/predictions"
                data = {
                    "input": {"prompt": prompt},
                    "webhook": "http://host.docker.internal:8000/webhook/prediction",
                    "webhook_events_filter": ["output", "completed"],
                    "id": prediction_id
                }
                
                requests.post(
                    url,
                    json=data,
                    headers={
                        "Content-Type": "application/json",
                        "Prefer": "respond-async"
                    }
                )
            except Exception as e:
                predictions[prediction_id]['error'] = str(e)
                predictions[prediction_id]['complete'] = True
                predictions[prediction_id]['queue'].put(None)
        
        threading.Thread(target=start_prediction, daemon=True).start()
        return jsonify({"prediction_id": prediction_id})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stream/<prediction_id>', methods=['GET'])
def stream_prediction(prediction_id):
    if prediction_id not in predictions:
        return jsonify({"error": "Prediction not found"}), 404
    
    def generate():
        pred = predictions[prediction_id]
        
        # Send initial status
        yield "data: {\"status\": \"started\"}\n\n"
        
        while True:
            try:
                token = pred['queue'].get(timeout=30)
                if token is None:  # Completion signal
                    if pred['error']:
                        yield f"data: {{\"status\": \"error\", \"error\": \"{pred['error']}\"}}\n\n"
                    else:
                        yield "data: {\"status\": \"complete\"}\n\n"
                    break
                yield f"data: {{\"token\": {json.dumps(token)}}}\n\n"
            except queue.Empty:
                if pred['complete']:
                    if pred['error']:
                        yield f"data: {{\"status\": \"error\", \"error\": \"{pred['error']}\"}}\n\n"
                    else:
                        yield "data: {\"status\": \"complete\"}\n\n"
                    break
                yield "data: {\"status\": \"processing\"}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*'
        }
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, threaded=True)
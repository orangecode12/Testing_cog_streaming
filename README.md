**Note:**  
- If running Cog in Docker, use `host.docker.internal` as the webhook host so the container can reach your local machine.
- If running everything natively, you can use `http://localhost:8000/webhook/prediction`.

---

## 5. How to run

1. **Start the webhook server:**
   ```bash
   python webhook_server.py
   ```

2. **Start Cog server:**
   ```bash
   cog build
   cog serve
   # or: docker run -p 5000:5000 my-image
   ```

3. **Start the client:**
   ```bash
   python client.py
   ```

---

## 6. What you’ll see

As the prediction runs, the webhook server will print output like:

```
[Webhook] Event: output, Status: processing, Output: ['The ']
127.0.0.1 - - [20/May/2025 13:01:43] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ']
127.0.0.1 - - [20/May/2025 13:01:44] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ', 'brown ']
127.0.0.1 - - [20/May/2025 13:01:45] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ', 'brown ', 'fox ']
127.0.0.1 - - [20/May/2025 13:01:46] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ', 'brown ', 'fox ', 'jumps ']
127.0.0.1 - - [20/May/2025 13:01:47] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ', 'brown ', 'fox ', 'jumps ', 'over ']
127.0.0.1 - - [20/May/2025 13:01:48] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ', 'brown ', 'fox ', 'jumps ', 'over ', 'the ']
127.0.0.1 - - [20/May/2025 13:01:49] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ', 'brown ', 'fox ', 'jumps ', 'over ', 'the ', 'lazy ']
127.0.0.1 - - [20/May/2025 13:01:50] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: processing, Output: ['The ', 'quick ', 'brown ', 'fox ', 'jumps ', 'over ', 'the ', 'lazy ', 'dog ']
127.0.0.1 - - [20/May/2025 13:01:51] "POST /webhook/prediction HTTP/1.1" 200 -
[Webhook] Event: output, Status: succeeded, Output: ['The ', 'quick ', 'brown ', 'fox ', 'jumps ', 'over ', 'the ', 'lazy ', 'dog ']

```

The client_flask.py will print output like:

```
python client_flask.py
Prediction started: {'input': {'prompt': 'The quick brown fox jumps over the lazy dog'}, 'output': None, 'id': None, 'version': None, 'created_at': None, 'started_at': '2025-05-20T09:01:42.274963+00:00', 'completed_at': None, 'logs': '', 'error': None, 'status': 'processing', 'metrics': None}

```

---

**That’s a complete, minimal Cog streaming + webhook example!**  
Let me know if you want a version that streams characters, or if you have any questions about deployment or networking.

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import threading
import queue
import json
import os
from agent import run_agent
from config import HOST, PORT

app = Flask(__name__, static_folder="static")
CORS(app)

# Stockage des tâches en cours
tasks = {}

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/run", methods=["POST"])
def run_task():
    data = request.json
    task = data.get("task", "").strip()

    if not task:
        return jsonify({"error": "Tâche vide"}), 400

    task_id = str(len(tasks) + 1)
    q = queue.Queue()
    tasks[task_id] = {"queue": q, "status": "running"}

    def execute():
        def callback(entry):
            q.put(entry)

        result = run_agent(task, callback=callback)
        tasks[task_id]["status"] = "done"
        tasks[task_id]["result"] = result
        q.put({"type": "end", "content": result})

    thread = threading.Thread(target=execute, daemon=True)
    thread.start()

    return jsonify({"task_id": task_id})

@app.route("/api/stream/<task_id>")
def stream(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Tâche introuvable"}), 404

    q = tasks[task_id]["queue"]

    def generate():
        while True:
            try:
                entry = q.get(timeout=60)
                yield f"data: {json.dumps(entry)}\n\n"
                if entry.get("type") == "end":
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/api/status/<task_id>")
def status(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Tâche introuvable"}), 404
    task = tasks[task_id]
    return jsonify({
        "status": task["status"],
        "result": task.get("result")
    })

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host=HOST, port=PORT, debug=False, threaded=True)

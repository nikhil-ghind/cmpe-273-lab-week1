import os
import time
import logging
from flask import Flask, request, jsonify, g

app = Flask(__name__)

# Configuration from environment variables
SERVICE_NAME = os.environ.get("SERVICE_NAME", "service-a")
PORT = int(os.environ.get("PORT", 8080))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@app.before_request
def before_request():
    """Store request start time for latency calculation."""
    g.start_time = time.time()


@app.after_request
def after_request(response):
    """Log request details with latency."""
    latency_ms = int((time.time() - g.start_time) * 1000)
    logger.info(
        f"service={SERVICE_NAME} method={request.method} "
        f"path={request.full_path.rstrip('?')} status={response.status_code} "
        f"latencyMs={latency_ms}"
    )
    return response


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.route("/echo", methods=["GET"])
def echo():
    """Echo endpoint - returns the msg query parameter."""
    msg = request.args.get("msg", "")

    if not msg:
        return jsonify({"error": "msg query param is required"}), 400

    return jsonify({"echo": msg})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

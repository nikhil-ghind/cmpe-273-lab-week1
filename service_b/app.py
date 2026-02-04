import os
import time
import logging
from flask import Flask, request, jsonify, g
import requests

app = Flask(__name__)

# Configuration from environment variables
SERVICE_NAME = os.environ.get("SERVICE_NAME", "service-b")
PORT = int(os.environ.get("PORT", 8081))
ECHO_BASE_URL = os.environ.get("ECHO_BASE_URL", "http://localhost:8080")
ECHO_TIMEOUT_SECONDS = float(os.environ.get("ECHO_TIMEOUT_SECONDS", 1.0))

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


@app.route("/call-echo", methods=["GET"])
def call_echo():
    """Call Service A's echo endpoint."""
    msg = request.args.get("msg", "")

    if not msg:
        return jsonify({"error": "msg query param is required"}), 400

    try:
        response = requests.get(
            f"{ECHO_BASE_URL}/echo",
            params={"msg": msg},
            timeout=ECHO_TIMEOUT_SECONDS
        )

        if response.status_code != 200:
            logger.error(
                f"service={SERVICE_NAME} action=call-echo "
                f'error="Echo service unavailable" cause=Non200Response'
            )
            return jsonify({"error": "Echo service unavailable"}), 503

        return jsonify({
            "serviceB": "ok",
            "echoServiceResponse": response.json()
        })

    except requests.Timeout:
        logger.error(
            f"service={SERVICE_NAME} action=call-echo "
            f'error="Echo service unavailable" cause=Timeout'
        )
        return jsonify({"error": "Echo service unavailable"}), 503

    except requests.ConnectionError:
        logger.error(
            f"service={SERVICE_NAME} action=call-echo "
            f'error="Echo service unavailable" cause=ConnectionError'
        )
        return jsonify({"error": "Echo service unavailable"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

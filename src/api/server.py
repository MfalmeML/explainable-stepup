from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
from src.api.handlers import APIHandlers
from src.api.step_up_handler import StepUpHandler
from src.api.validation_handler import ValidationHandler
from src.ui.investigator_view import InvestigatorView

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize handlers with store path
STORE_PATH = "outcome_store.json"
api_handlers = APIHandlers(STORE_PATH)
step_up_handler = StepUpHandler(STORE_PATH)
validation_handler = ValidationHandler(STORE_PATH)
investigator_view = InvestigatorView(STORE_PATH)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "explainable-decisioning"
    })

@app.route('/explanation/<transaction_id>', methods=['GET'])
def get_explanation(transaction_id):
    result = api_handlers.handle_get_case(transaction_id)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result), 200

@app.route('/reason-agreement', methods=['POST'])
def record_agreement():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Missing payload"}), 400
    result = api_handlers.handle_post_agreement(payload)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 200

@app.route('/reason-agreement/sample', methods=['GET'])
def get_sample():
    sample_size = request.args.get('size', default=10, type=int)
    result = api_handlers.handle_get_sample(sample_size)
    return jsonify(result), 200

@app.route('/step-up-outcome', methods=['POST'])
def record_step_up():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Missing payload"}), 400
    result = step_up_handler.handle_step_up_capture(payload)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 200

@app.route('/validation/step-up-completion', methods=['GET'])
def get_completion_rates():
    source = request.args.get('source')
    min_cases = request.args.get('min_cases', default=5, type=int)
    result = validation_handler.handle_validation_stats(source, min_cases)
    return jsonify(result), 200

@app.route('/validation/dashboard', methods=['GET'])
def get_dashboard():
    source = request.args.get('source')
    min_cases = request.args.get('min_cases', default=5, type=int)
    days = request.args.get('days', default=7, type=int)
    result = validation_handler.handle_dashboard_stats(source, min_cases, days)
    return jsonify(result), 200

@app.route('/validation/drift', methods=['GET'])
def get_drift():
    threshold = request.args.get('threshold', default=0.15, type=float)
    result = validation_handler.handle_drift_check(threshold)
    return jsonify(result), 200

@app.route('/metrics/coverage', methods=['GET'])
def get_coverage():
    from src.mlops.monitoring import MLOpsMonitor
    monitor = MLOpsMonitor(STORE_PATH)
    result = monitor.get_explanation_coverage()
    return jsonify(result), 200

@app.route('/metrics/reason-distribution', methods=['GET'])
def get_reason_distribution():
    from src.mlops.monitoring import MLOpsMonitor
    days = request.args.get('days', default=7, type=int)
    monitor = MLOpsMonitor(STORE_PATH)
    result = monitor.get_reason_distribution(days)
    return jsonify(result), 200

@app.route('/metrics/dashboard', methods=['GET'])
def get_metrics_dashboard():
    from src.mlops.monitoring import MLOpsMonitor
    monitor = MLOpsMonitor(STORE_PATH)
    result = monitor.get_mlops_dashboard()
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
mport os
import uuid
import pandas as pd
import numpy as np
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort

# --- App and Logger Configuration ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_key_that_is_long_and_secure')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)>
logger = logging.getLogger(__name__)

# --- Bot Instance Management ---
from bots.binance_bot import BinanceBot
bots = {}

def get_bot_for_session():
    """Retrieves or creates a BinanceBot instance for the current user session."""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    user_id = session['user_id']
    if user_id not in bots:
        logger.info(f"Creating new BinanceBot instance for user_id: {user_id}")
        bots[user_id] = BinanceBot()
    return bots[user_id]

# --- SECURITY HARDENING: Block common vulnerability scans ---
FORBIDDEN_PATHS = [
    '/.env', '/.git/config', '/info.php', '/server-status', '/config.json',
    '/actuator', '/actuator/gateway/routes', '/wp-login.php', '/.vscode/sftp.json',
    '/@vite/env', '/actuator/env', '/server', '/debug/default/view', '/v2/_catalog',
    '/ecp/Current/exporttool/microsoft.exchange.ediscovery.exporttool.application',
    '/_all_dbs', '/.DS_Store', '/telescope/requests'
]

@app.before_request
def block_suspicious_requests():
    """Intercepts and blocks requests for known sensitive or malicious paths."""
    # Check for exact path matches
    if request.path in FORBIDDEN_PATHS:
        logger.warning(f"Blocked suspicious request for exact path: {request.path} from IP: {reques>
        abort(404)
    # Check for partial path matches for more dynamic routes
    if any(forbidden in request.path for forbidden in ['/s/0373e22323e2033323e2735313', '/?rest_rou>
        logger.warning(f"Blocked suspicious request for partial path: {request.path} from IP: {requ>
        abort(404)


# --- ERROR HANDLING: Custom pages for common HTTP errors ---
@app.errorhandler(400)
def handle_bad_request(e):
    """Handles 400 Bad Request errors gracefully."""
    logger.warning(f"Bad Request (400) from IP: {request.remote_addr} for path: {request.path}")
    return render_template('error.html', error_code=400, error_message="Bad Request"), 400

@app.errorhandler(404)
def handle_not_found(e):
    """Handles 404 Not Found errors gracefully."""
    return render_template('error.html', error_code=404, error_message="Page Not Found"), 404

@app.errorhandler(500)
def handle_internal_server_error(e):
    """Handles 500 Internal Server Error errors gracefully."""
    logger.error(f"Internal Server Error (500): {e}", exc_info=True)
    return render_template('error.html', error_code=500, error_message="Internal Server Error"), 500


# --- Main Application Flow Routes ---

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        return redirect(url_for('platform_selection'))
    return render_template('signup.html')

@app.route('/platform-selection')
def platform_selection():
    return render_template('platform_selection.html')

@app.route('/select-platform', methods=['POST'])
def select_platform():
    platform = request.form.get('platform')
    if platform == 'binance':
        return redirect(url_for('connect_binance'))
    elif platform in ['alpaca', 'oanda', 'mt4', 'mt5']:
        return render_template('coming_soon.html', platform=platform.capitalize())
    else:
        abort(400) # Invalid platform
# --- Binance Specific Routes ---

@app.route('/connect-binance', methods=['GET', 'POST'])
def connect_binance():
    if request.method == 'POST':
        bin_bot = get_bot_for_session()
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        testnet = 'testnet' in request.form

        if not api_key or not api_secret:
            return render_template('connect_binance.html', error="API Key and Secret are required.")

        if bin_bot.connect(api_key, api_secret, testnet):
            session['binance_connected'] = True
            session['testnet'] = testnet
            return redirect(url_for('binance_dashboard'))
        else:
            session.clear()
            return render_template('connect_binance.html', error="Connection failed. Please check y>
    
    return render_template('connect_binance.html')

@app.route('/binance-dashboard')
def binance_dashboard():
    if not session.get('binance_connected'):
        return redirect(url_for('connect_binance'))
# --- Run Server ---
if __name__ == '__main__':
    # For production, use a proper WSGI server like Gunicorn or Waitress.
    # The 'debug=True' mode should be turned OFF in a production environment.
    app.run(host='0.0.0.0', port=5000, debug=False)

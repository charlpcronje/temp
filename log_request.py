#!/usr/bin/env python

import json
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/map', methods=['POST'])
def handle_map():
    """Log the request and return a success response."""
    try:
        # Get the request data
        data = request.json
        
        # Log the request data
        logger.info(f"Received request: {json.dumps(data, indent=2)}")
        
        # Return a success response
        return jsonify({"success": True, "mapped_fields": data})
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

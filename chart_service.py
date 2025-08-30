#!/usr/bin/env python3
"""
GPL Chart Service - HTTP wrapper around Kerykeion chart generation
Copyright (C) 2024 Lucy Bot Chart Service

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This service is licensed under GPL v3+ to comply with Kerykeion's licensing requirements.
"""

from flask import Flask, request, jsonify
import json
import sys
import traceback
from kerykeion_chart_generator import generate_chart

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "chart-generator"})

@app.route('/generate-chart', methods=['POST'])
def generate_chart_endpoint():
    try:
        # Get JSON input data
        input_data = request.get_json()
        
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400
        
        # Debug log
        is_transit = input_data.get('is_transit', False)
        chart_name = input_data.get('chart_data', {}).get('name', 'Unknown')
        import logging
        logging.warning(f"Flask: Generating chart for {chart_name}, is_transit={is_transit}")
        print(f"Flask: Generating chart for {chart_name}, is_transit={is_transit}")
        
        # Generate chart using existing Kerykeion code
        svg_content = generate_chart(input_data)
        
        return jsonify({
            "success": True,
            "svg_content": svg_content
        })
        
    except Exception as e:
        # Log error details
        print(f"Chart generation error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # Return error response
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
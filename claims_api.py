#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import time
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Figma plugin

@app.route('/generate-claims', methods=['POST'])
def generate_claims():
    """Generate claims using the existing Python system"""
    try:
        data = request.json
        brand_file = data.get('brandFile', 'metra')
        claim_count = data.get('claimCount', 8)
        claim_style = data.get('claimStyle', 'balanced')
        
        print(f"🎯 Generating claims for {brand_file}, count: {claim_count}, style: {claim_style}")
        
        # Run the claims generation system
        result = subprocess.run(
            ['python3', 'orchestrator/main.py'],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env={**os.environ, 'PYTHONPATH': os.getcwd()}
        )
        
        if result.returncode != 0:
            print(f"❌ Claims generation failed: {result.stderr}")
            return jsonify({
                'success': False,
                'error': f'Claims generation failed: {result.stderr}'
            }), 500
        
        print(f"✅ Claims generated successfully: {result.stdout}")
        
        # Look for generated job files
        job_files = list(Path('.').glob('job_*.json'))
        if not job_files:
            return jsonify({
                'success': False,
                'error': 'No job files generated'
            }), 500
        
        # Get the most recent job file
        latest_job = max(job_files, key=os.path.getctime)
        
        # Read the job file to get claims
        with open(latest_job, 'r') as f:
            job_data = json.load(f)
        
        # Extract claims from the job data
        claims = []
        if 'claims' in job_data:
            for angle_id, angle_claims in job_data['claims'].items():
                for claim in angle_claims:
                    claims.append({
                        'text': claim.get('text', ''),
                        'style': claim.get('style', ''),
                        'angle': angle_id
                    })
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(claims)} claims for {brand_file}',
            'claims': claims,
            'job_file': str(latest_job),
            'total_claims': len(claims)
        })
        
    except Exception as e:
        print(f"❌ Error generating claims: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Claims API is running'})

if __name__ == '__main__':
    print("🚀 Starting Claims API server...")
    print("   - POST /generate-claims - Generate new claims")
    print("   - GET  /health - Health check")
    print("   - Server will run on http://localhost:8002")
    app.run(host='0.0.0.0', port=8002, debug=True)

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
        
        # Look for generated job files in the out/ directory
        job_files = list(Path('out').glob('*.json'))
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
        if 'variants' in job_data and job_data['variants']:
            for variant in job_data['variants']:
                if 'claim' in variant:
                    claims.append({
                        'text': variant['claim'],
                        'style': 'balanced',  # Default style since it's not in the variant
                        'angle': 'general'    # Default angle since it's not in the variant
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

@app.route('/brands', methods=['GET'])
def discover_brands():
    """Discover all brands and their status"""
    try:
        brands = []
        inputs_dir = Path('inputs')
        
        if not inputs_dir.exists():
            return jsonify({'brands': []})
        
        # Scan for brand folders
        for brand_folder in inputs_dir.iterdir():
            if brand_folder.is_dir() and brand_folder.name not in ['BRAND_TEMPLATE']:
                brand_name = brand_folder.name
                brand_info = {
                    'name': brand_name,
                    'folder': str(brand_folder),
                    'status': 'incomplete',
                    'has_docs': False,
                    'has_json': False,
                    'has_config': False
                }
                
                # Check for brand_docs subfolder
                brand_docs = brand_folder / 'brand_docs'
                if brand_docs.exists() and brand_docs.is_dir():
                    brand_info['has_docs'] = True
                    # Check if there are actual documents
                    docs = list(brand_docs.glob('*'))
                    if docs:
                        brand_info['status'] = 'ready'
                
                # Check for enhanced JSON
                json_files = list(brand_folder.glob(f'{brand_name.lower()}_enhanced.json'))
                if json_files:
                    brand_info['has_json'] = True
                    brand_info['status'] = 'complete'
                
                # Check for brand config
                config_file = brand_folder / 'brand_config.json'
                if config_file.exists():
                    brand_info['has_config'] = True
                
                brands.append(brand_info)
        
        return jsonify({
            'success': True,
            'brands': brands
        })
        
    except Exception as e:
        print(f"❌ Error discovering brands: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/process-documents', methods=['POST'])
def process_documents():
    """Process documents for a specific brand to generate enhanced JSON"""
    try:
        data = request.json
        brand_name = data.get('brandName')
        
        if not brand_name:
            return jsonify({
                'success': False,
                'error': 'Brand name is required'
            }), 400
        
        print(f"🔄 Processing documents for brand: {brand_name}")
        
        # Run the document processor
        result = subprocess.run(
            ['python3', 'document_processor.py'],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env={**os.environ, 'PYTHONPATH': os.getcwd()}
        )
        
        if result.returncode != 0:
            print(f"❌ Document processing failed: {result.stderr}")
            return jsonify({
                'success': False,
                'error': f'Document processing failed: {result.stderr}'
            }), 500
        
        print(f"✅ Documents processed successfully: {result.stdout}")
        
        # Check if the enhanced JSON was created
        enhanced_json_path = f"inputs/{brand_name}/{brand_name.lower()}_enhanced.json"
        if os.path.exists(enhanced_json_path):
            return jsonify({
                'success': True,
                'message': f'Documents processed successfully for {brand_name}',
                'enhanced_json': enhanced_json_path
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Enhanced JSON not found at {enhanced_json_path}'
            }), 500
        
    except Exception as e:
        print(f"❌ Error processing documents: {str(e)}")
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
    print("   - GET  /brands - Discover brands and their status")
    print("   - POST /process-documents - Process documents for a brand")
    print("   - GET  /health - Health check")
    print("   - Server will run on http://localhost:8002")
    app.run(host='0.0.0.0', port=8002, debug=True)

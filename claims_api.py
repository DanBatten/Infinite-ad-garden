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
        claim_style = data.get('claimStyle', 'mixed-styles')
        template_name = data.get('templateName')  # New: template-specific claims
        template_variation = data.get('templateVariation', '01')  # Default to version 01 if not specified
        
        print(f"🎯 Generating claims for {brand_file}, count: {claim_count}, style: {claim_style}")
        if template_name:
            print(f"📋 Using template: {template_name}")
        if template_variation:
            print(f"🔄 Using variation: {template_variation}")
        
        # Pass parameters to the orchestrator via environment variables
        env_vars = {
            **os.environ, 
            'PYTHONPATH': os.getcwd(),
            'CLAIM_COUNT': str(claim_count),
            'CLAIM_STYLE': claim_style,
            'BRAND_FILE': brand_file
        }
        
        # Add template information if provided
        if template_name:
            env_vars['TEMPLATE_NAME'] = template_name
        if template_variation:
            env_vars['TEMPLATE_VARIATION'] = template_variation
        
        # Run the claims generation system
        result = subprocess.run(
            ['python3', 'orchestrator/main.py'],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env=env_vars
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
        
        # Extract job ID from filename (e.g., "out/abc123.json" -> "abc123")
        job_id = latest_job.stem  # This gets the filename without extension
        
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
                        'style': claim_style,  # Use the actual requested style
                        'angle': 'general'    # Default angle since it's not in the variant
                    })
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(claims)} claims for {brand_file}',
            'claims': claims,
            'job_id': job_id,  # Send the actual job ID
            'job_file': str(latest_job),
            'total_claims': len(claims)
        })
        
    except Exception as e:
        print(f"❌ Error generating claims: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/templates', methods=['GET'])
def list_templates():
    """List all available templates"""
    try:
        from orchestrator.templates import template_manager
        
        templates = template_manager.list_templates()
        return jsonify({
            'success': True,
            'templates': templates,
            'total': len(templates)
        })
        
    except Exception as e:
        print(f"❌ Error listing templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/templates/<template_name>', methods=['GET'])
def get_template(template_name):
    """Get details for a specific template"""
    try:
        from orchestrator.templates import template_manager
        
        template = template_manager.get_template(template_name)
        if not template:
            return jsonify({
                'success': False,
                'error': f'Template {template_name} not found'
            }), 404
        
        # Get template requirements
        requirements = template_manager.get_claims_requirements(template_name)
        
        return jsonify({
            'success': True,
            'template': {
                'name': template.name,
                'base_name': template.base_name,
                'category': template.category,
                'description': template.description,
                'variations': [
                    {
                        'name': v.name,
                        'aspect_ratio': v.aspect_ratio,
                        'dimensions': v.dimensions,
                        'elements_count': len(v.elements)
                    } for v in template.variations
                ],
                'requirements': requirements
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting template {template_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/templates/<template_name>/variations', methods=['GET'])
def get_template_variations(template_name):
    """Get version numbers for a specific template (e.g., ['01', '02'])"""
    try:
        from orchestrator.templates import template_manager
        
        versions = template_manager.get_template_variations(template_name)
        if not versions:
            return jsonify({
                'success': False,
                'error': f'No versions found for template {template_name}'
            }), 404
        
        return jsonify({
            'success': True,
            'template_name': template_name,
            'versions': versions,
            'note': 'These are version numbers. Each version will generate both portrait and square variants.'
        })
        
    except Exception as e:
        print(f"❌ Error getting versions for template {template_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/templates/<template_name>/requirements', methods=['GET'])
def get_template_requirements(template_name):
    """Get claims requirements for a specific template and variation"""
    try:
        from orchestrator.templates import template_manager
        
        variation_name = request.args.get('variation')
        requirements = template_manager.get_claims_requirements(template_name, variation_name)
        
        if not requirements:
            return jsonify({
                'success': False,
                'error': f'Requirements not found for template {template_name}'
            }), 404
        
        return jsonify({
            'success': True,
            'requirements': requirements
        })
        
    except Exception as e:
        print(f"❌ Error getting requirements for template {template_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/templates/refresh', methods=['POST'])
def refresh_templates():
    """Refresh template cache and scan for updates"""
    try:
        from orchestrator.templates import template_manager
        
        # Get template data from request body (sent by Figma plugin)
        data = request.get_json() or {}
        figma_templates = data.get('templates', [])
        template_requirements = data.get('templateRequirements', {})
        
        if figma_templates:
            # Use the new scanning method to update templates with requirements
            template_manager.scan_and_update_templates(figma_templates, template_requirements)
        else:
            # Fallback to just reloading cached templates
            template_manager.load_cached_templates()
        
        templates = template_manager.list_templates()
        return jsonify({
            'success': True,
            'message': f'Refreshed {len(templates)} templates',
            'templates': templates,
            'total': len(templates)
        })
        
    except Exception as e:
        print(f"❌ Error refreshing templates: {str(e)}")
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
        
        # Run the document processor with the specific brand name
        result = subprocess.run(
            ['python3', 'document_processor.py', brand_name],
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
    print("   - GET  /templates - List all templates")
    print("   - GET  /templates/<name> - Get template details")
    print("   - GET  /templates/<name>/variations - Get template variations")
    print("   - GET  /templates/<name>/requirements - Get template requirements")
    print("   - POST /templates/refresh - Refresh template cache")
    print("   - GET  /health - Health check")
    print("   - Server will run on http://localhost:8002")
    app.run(host='0.0.0.0', port=8002, debug=True)

# orchestrator/templates.py
"""
Template Management System for Infinite Ad Garden
Handles scanning Figma files for templates, parsing requirements, and managing variations
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TemplateElement:
    """Represents a text element in a template"""
    name: str
    max_chars: int
    description: str
    required: bool = True

@dataclass
class TemplateVariation:
    """Represents a variation of a template"""
    name: str
    aspect_ratio: str
    dimensions: Dict[str, int]
    elements: List[TemplateElement]

@dataclass
class Template:
    """Represents a complete template"""
    name: str
    base_name: str
    category: str
    description: str
    variations: List[TemplateVariation]
    image_weights: str
    metadata: Dict[str, Any]

class TemplateManager:
    """Manages templates and their requirements"""
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self.template_cache_file = "orchestrator/template_cache.json"
        self.load_cached_templates()
    
    def load_cached_templates(self):
        """Load templates from cache file"""
        try:
            if Path(self.template_cache_file).exists():
                with open(self.template_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    for template_data in cache_data.get('templates', []):
                        template = self._deserialize_template(template_data)
                        self.templates[template.name] = template
                print(f"✅ Loaded {len(self.templates)} cached templates")
            else:
                print("📁 No template cache file found, creating default templates")
                self._create_default_templates()
        except Exception as e:
            print(f"⚠️ Failed to load template cache: {e}")
            print("📁 Creating default templates as fallback")
            self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default templates if none exist"""
        try:
            # Create Value Prop Tick template
            value_prop_tick = Template(
                name="Template-Value_Prop_Tick",
                base_name="Template-Value_Prop_Tick",
                category="value_prop",
                description="Template for Value Proposition with tick marks",
                variations=[
                    TemplateVariation(
                        name="01-portrait",
                        aspect_ratio="9:16",
                        dimensions={"width": 1080, "height": 1440},
                        elements=[
                            TemplateElement("headline", 70, "Main headline text"),
                            TemplateElement("value_props", 200, "Value proposition text"),
                            TemplateElement("cta", 30, "Call to action")
                        ]
                    ),
                    TemplateVariation(
                        name="01-square",
                        aspect_ratio="1:1",
                        dimensions={"width": 1080, "height": 1080},
                        elements=[
                            TemplateElement("headline", 70, "Main headline text"),
                            TemplateElement("value_props", 200, "Value proposition text"),
                            TemplateElement("cta", 30, "Call to action")
                        ]
                    )
                ],
                image_weights="value_prop",
                metadata={"source": "default"}
            )
            
            # Create Problem Solution template
            problem_solution = Template(
                name="Template-Problem_Solution",
                base_name="Template-Problem_Solution",
                category="problem_solution",
                description="Template for Problem-Solution messaging",
                variations=[
                    TemplateVariation(
                        name="01-portrait",
                        aspect_ratio="9:16",
                        dimensions={"width": 1080, "height": 1440},
                        elements=[
                            TemplateElement("headline", 70, "Main headline text"),
                            TemplateElement("problem", 150, "Problem description"),
                            TemplateElement("solution", 150, "Solution description"),
                            TemplateElement("cta", 30, "Call to action")
                        ]
                    ),
                    TemplateVariation(
                        name="01-square",
                        aspect_ratio="1:1",
                        dimensions={"width": 1080, "height": 1080},
                        elements=[
                            TemplateElement("headline", 70, "Main headline text"),
                            TemplateElement("problem", 150, "Problem description"),
                            TemplateElement("solution", 150, "Solution description"),
                            TemplateElement("cta", 30, "Call to action")
                        ]
                    )
                ],
                image_weights="problem_solution",
                metadata={"source": "default"}
            )
            
            # Add to templates
            self.templates[value_prop_tick.name] = value_prop_tick
            self.templates[problem_solution.name] = problem_solution
            print(f"✅ Created {len(self.templates)} default templates")
            
            # Save to cache
            self.save_template_cache()
            
        except Exception as e:
            print(f"❌ Error creating default templates: {e}")
    
    def save_template_cache(self):
        """Save templates to cache file"""
        try:
            cache_data = {
                'templates': [self._serialize_template(t) for t in self.templates.values()],
                'last_updated': str(Path().cwd())
            }
            with open(self.template_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            print(f"✅ Saved {len(self.templates)} templates to cache")
        except Exception as e:
            print(f"⚠️ Failed to save template cache: {e}")
    
    def _serialize_template(self, template: Template) -> Dict[str, Any]:
        """Convert template to serializable format"""
        return {
            'name': template.name,
            'base_name': template.base_name,
            'category': template.category,
            'description': template.description,
            'variations': [
                {
                    'name': v.name,
                    'aspect_ratio': v.aspect_ratio,
                    'dimensions': v.dimensions,
                    'elements': [
                        {
                            'name': e.name,
                            'max_chars': e.max_chars,
                            'description': e.description,
                            'required': e.required
                        } for e in v.elements
                    ]
                } for v in template.variations
            ],
            'image_weights': template.image_weights,
            'metadata': template.metadata
        }
    
    def _deserialize_template(self, data: Dict[str, Any]) -> Template:
        """Convert serialized data back to Template object"""
        variations = [
            TemplateVariation(
                name=v['name'],
                aspect_ratio=v['aspect_ratio'],
                dimensions=v['dimensions'],
                elements=[
                    TemplateElement(
                        name=e['name'],
                        max_chars=e['max_chars'],
                        description=e['description'],
                        required=e['required']
                    ) for e in v['elements']
                ]
            ) for v in data['variations']
        ]
        
        return Template(
            name=data['name'],
            base_name=data['base_name'],
            category=data['category'],
            description=data['description'],
            variations=variations,
            image_weights=data['image_weights'],
            metadata=data['metadata']
        )
    
    def parse_template_guide(self, guide_text: str) -> Dict[str, Any]:
        """Parse template guide text to extract requirements"""
        try:
            # Extract text elements
            text_elements = {}
            elements_match = re.search(r'Text Elements:(.*?)(?=Text Character Max|Image weights:|$)', guide_text, re.DOTALL | re.IGNORECASE)
            if elements_match:
                elements_text = elements_match.group(1).strip()
                for line in elements_text.split('\n'):
                    line = line.strip()
                    if line.startswith('#') and ':' in line:
                        element_name = line.split(':')[0].strip()
                        text_elements[element_name] = {
                            'name': element_name,
                            'description': line.split(':')[1].strip() if ':' in line else ''
                        }
            
            # Extract character limits
            char_limits = {}
            char_match = re.search(r'Text Character Max(.*?)(?=Image weights:|$)', guide_text, re.DOTALL | re.IGNORECASE)
            if char_match:
                char_text = char_match.group(1).strip()
                for line in char_text.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        element_name = line.split(':')[0].strip()
                        try:
                            max_chars = int(line.split(':')[1].strip())
                            char_limits[element_name] = max_chars
                        except ValueError:
                            pass
            
            # Extract image weights
            image_weights = ""
            weights_match = re.search(r'Image weights:(.*?)$', guide_text, re.DOTALL | re.IGNORECASE)
            if weights_match:
                image_weights = weights_match.group(1).strip()
            
            return {
                'text_elements': text_elements,
                'char_limits': char_limits,
                'image_weights': image_weights
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing template guide: {e}")
            return {}
    
    def _determine_category(self, base_name: str) -> str:
        """Determine template category based on base name"""
        base_lower = base_name.lower()
        
        if 'value' in base_lower and 'prop' in base_lower:
            return 'value_proposition'
        elif 'problem' in base_lower and 'solution' in base_lower:
            return 'problem_solution'
        elif 'benefit' in base_lower:
            return 'benefit_focused'
        elif 'social' in base_lower and 'proof' in base_lower:
            return 'social_proof'
        elif 'urgency' in base_lower:
            return 'urgency_driven'
        elif 'story' in base_lower or 'narrative' in base_lower:
            return 'storytelling'
        else:
            return 'general'
    
    def add_template(self, template: Template):
        """Add or update a template"""
        self.templates[template.name] = template
        self.save_template_cache()
        print(f"✅ Added/updated template: {template.name}")
    
    def get_template(self, template_name: str) -> Optional[Template]:
        """Get a template by name"""
        return self.templates.get(template_name)
    
    def get_templates_by_category(self, category: str) -> List[Template]:
        """Get all templates in a category"""
        return [t for t in self.templates.values() if t.category == category]
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates with summary information"""
        return [
            {
                'name': t.name,
                'base_name': t.base_name,
                'category': t.category,
                'description': t.description,
                'variations_count': len(t.variations),
                'elements_count': len(t.variations[0].elements) if t.variations else 0
            }
            for t in self.templates.values()
        ]
    
    def get_template_variations(self, template_name: str) -> List[str]:
        """Get version numbers for a specific template (e.g., ['01', '02'])"""
        template = self.get_template(template_name)
        if not template:
            return []
        
        # Extract unique version numbers from variation names
        versions = set()
        for variation in template.variations:
            # Extract version number from names like "01-portrait", "02-square", etc.
            version_match = re.search(r'(\d+)', variation.name)
            if version_match:
                versions.add(version_match.group(1))
        
        # Return sorted version numbers
        return sorted(list(versions), key=lambda x: int(x))
    
    def get_variations_by_version(self, template_name: str, version: str) -> List[TemplateVariation]:
        """Get all variations (portrait, square) for a specific version number"""
        template = self.get_template(template_name)
        if not template:
            return []
        
        # Find variations that match the version number
        matching_variations = []
        for variation in template.variations:
            if variation.name.startswith(f"{version}-"):
                matching_variations.append(variation)
        
        return matching_variations
    
    def get_claims_requirements(self, template_name: str, variation_name: str = None) -> Dict[str, Any]:
        """Get claims requirements for a specific template and variation"""
        template = self.get_template(template_name)
        if not template:
            return {}
        
        # Use first variation if none specified
        variation = None
        if variation_name:
            variation = next((v for v in template.variations if v.name == variation_name), None)
        if not variation:
            variation = template.variations[0] if template.variations else None
        
        if not variation:
            return {}
        
        return {
            'template_name': template.name,
            'variation_name': variation.name,
            'category': template.category,
            'elements': [
                {
                    'name': e.name,
                    'max_chars': e.max_chars,
                    'description': e.description,
                    'required': e.required
                } for e in variation.elements
            ],
            'image_weights': template.image_weights,
            'total_elements': len(variation.elements),
            'metadata': template.metadata
        }
    
    def get_all_variations_for_template(self, template_name: str) -> List[Dict[str, Any]]:
        """Get all variations for a template with their requirements"""
        template = self.get_template(template_name)
        if not template:
            return []
        
        variations = []
        for variation in template.variations:
            variations.append({
                'name': variation.name,
                'aspect_ratio': variation.aspect_ratio,
                'dimensions': variation.dimensions,
                'elements': [
                    {
                        'name': e.name,
                        'max_chars': e.max_chars,
                        'description': e.description,
                        'required': e.required
                    } for e in variation.elements
                ]
            })
        
        return variations
    
    def scan_and_update_templates(self, figma_templates: List[Dict[str, Any]], template_requirements: Dict[str, Any] = None):
        """Scan and update templates based on Figma plugin data and JSON guide requirements"""
        try:
            # First, ensure we have the existing templates loaded
            if not self.templates:
                self.load_cached_templates()
            
            print(f"🔍 Starting scan with {len(self.templates)} existing templates")
            
            # Process each template found by the Figma plugin
            for figma_template in figma_templates:
                template_name = figma_template.get('name', '')
                print(f"🔍 Processing Figma template: {template_name}")
                
                # Check if we have JSON requirements for this template
                if template_requirements and template_name in template_requirements:
                    guide_data = template_requirements[template_name]
                    print(f"🔍 Found JSON guide data for {template_name}:", guide_data)
                    
                    # Create template from JSON guide data
                    template = self._create_template_from_guide(template_name, guide_data, figma_template)
                    if template:
                        self.templates[template_name] = template
                        print(f"✅ Created template from guide: {template_name}")
                    else:
                        print(f"⚠️ Failed to create template from guide for {template_name}")
                
                # For existing templates without guide data, preserve them
                elif template_name in self.templates:
                    print(f"✅ Template {template_name} already exists in cache")
                else:
                    print(f"⚠️ No guide data for {template_name}, preserving existing template if available")
            
            print(f"🔍 Final template count: {len(self.templates)}")
            print(f"🔍 Template names: {list(self.templates.keys())}")
            
            # Save updated templates to cache
            self.save_template_cache()
            print(f"✅ Updated template cache with {len(self.templates)} templates")
            
        except Exception as e:
            print(f"❌ Error scanning templates: {e}")
            # Fallback to loading cached templates
            self.load_cached_templates()
    
    def _create_template_from_guide(self, template_name: str, guide_data: Dict[str, Any], figma_template: Dict[str, Any]) -> Optional[Template]:
        """Create a template from JSON guide data"""
        try:
            # Extract template information
            base_name = guide_data.get('template_name', template_name)
            text_elements = guide_data.get('text_elements', {})
            image_data = guide_data.get('image', {})
            prompt_guidance = guide_data.get('prompt_guidance', '')
            
            # Create template elements from text_elements
            elements = []
            for element_name, element_data in text_elements.items():
                if isinstance(element_data, dict):
                    max_chars = element_data.get('max_chars', 100)
                    description = element_data.get('description', f'{element_name} text element')
                else:
                    max_chars = 100
                    description = f'{element_name} text element'
                
                elements.append(TemplateElement(
                    name=element_name,
                    max_chars=max_chars,
                    description=description
                ))
            
            # Create variations (portrait and square)
            variations = [
                TemplateVariation(
                    name='01-portrait',
                    aspect_ratio='9:16',
                    dimensions={'width': 1080, 'height': 1440},
                    elements=elements
                ),
                TemplateVariation(
                    name='01-square',
                    aspect_ratio='1:1',
                    dimensions={'width': 1080, 'height': 1080},
                    elements=elements
                )
            ]
            
            # Determine category based on template name
            category = self._determine_category(base_name)
            
            # Create template
            template = Template(
                name=template_name,
                base_name=base_name,
                category=category,
                description=f'Template created from Figma guide: {prompt_guidance[:100]}...',
                variations=variations,
                image_weights=image_data.get('weights', 'general'),
                metadata={
                    'source': 'figma_guide_json',
                    'prompt_guidance': prompt_guidance,
                    'guide_data': guide_data
                }
            )
            
            return template
            
        except Exception as e:
            print(f"❌ Error creating template from guide: {e}")
            return None

# Global template manager instance
template_manager = TemplateManager()

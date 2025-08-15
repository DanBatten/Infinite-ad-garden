# Template Management System - Infinite Ad Garden

## Overview

The Template Management System allows you to dynamically manage design templates from Figma, scan for new templates, and generate claims specifically tailored to each template's requirements. This system enables you to create different types of ad content based on the specific text elements and character limits defined in your Figma templates.

## Key Features

### 🎯 Template-Specific Claims Generation
- Generate claims that respect template text element requirements
- Automatic character limit enforcement
- Template category-based angle selection
- Support for multiple template variations

### 📋 Template Discovery & Management
- Scan Figma files for templates in the `_Template_Library` page
- Automatic template requirement parsing
- Template variation management
- Template caching and refresh capabilities

### 🔄 Template Variations
- Support for multiple variations of the same template type
- Different aspect ratios and dimensions
- Consistent text element requirements across variations

## How It Works

### 1. Template Structure in Figma

Templates should be created in a page called `_Template_Library` with the following structure:

```
_Template_Library
├── Template-Value_Prop_Tick-02-portrait
│   ├── # Template-Valule_Prop_Tick-02-Guide (Text layer with requirements)
│   ├── Headline (#HEADLINE)
│   ├── Value Props (#VALUE_PROP-01, #VALUE_PROP-02, etc.)
│   └── #IMAGE (Image placeholder)
├── Template-Value_Prop_Tick-02-Square
└── Template-Problem_Solution-01-s
```

### 2. Template Guide Text Format

Each template should include a text layer (typically named with "Guide" or similar) that contains:

```
Text Elements:
#HEADLINE
#VALUE_PROP-01
#VALUE_PROP-02
#VALUE_PROP-03
#VALUE_PROP-04

Text Character Max
Headline: 90
Value Props: 30

Image weights:
Generally works really well with a product image focussing on the jar or the pill, etc.
```

### 3. Template Naming Convention

Templates should follow this naming pattern:
- `Template-{BaseName}-{Variation}-{AspectRatio}`
- Example: `Template-Value_Prop_Tick-02-portrait`

## API Endpoints

### Template Management

#### List All Templates
```
GET /templates
```
Returns a list of all available templates with their metadata.

#### Get Template Details
```
GET /templates/{template_name}
```
Returns detailed information about a specific template including requirements.

#### Get Template Variations
```
GET /templates/{template_name}/variations
```
Returns all variations available for a specific template.

#### Get Template Requirements
```
GET /templates/{template_name}/requirements?variation={variation_name}
```
Returns the claims requirements for a specific template and variation.

#### Scan for New Templates
```
POST /templates/scan
```
Scans Figma files for new templates (placeholder for Figma API integration).

#### Refresh Template Cache
```
POST /templates/refresh
```
Refreshes the template cache and reloads all templates.

### Claims Generation with Templates

#### Generate Template-Specific Claims
```
POST /generate-claims
{
  "brandFile": "Metra",
  "claimCount": 10,
  "claimStyle": "benefit-focused",
  "templateName": "Template-Value_Prop_Tick-02-portrait",
  "templateVariation": "02-portrait"
}
```

## Template Categories

The system automatically categorizes templates based on their names:

- **value_proposition**: Templates focused on highlighting benefits and value
- **problem_solution**: Templates that address problems and present solutions
- **benefit_focused**: Templates emphasizing positive outcomes
- **social_proof**: Templates building credibility and trust
- **urgency_driven**: Templates creating action and immediacy
- **storytelling**: Templates focused on narrative and stories
- **general**: Default category for other templates

## Template Elements

Each template defines required text elements with:

- **Name**: The element identifier (e.g., `#HEADLINE`)
- **Max Characters**: Character limit for the element
- **Description**: Human-readable description of the element
- **Required**: Whether the element is mandatory

## Usage Examples

### 1. Generate Claims for a Value Proposition Template

```javascript
// In the Figma plugin UI
const templateName = "Template-Value_Prop_Tick-02-portrait";
const templateVariation = "02-portrait";

// This will generate claims that work with:
// - #HEADLINE (max 90 chars)
// - #VALUE_PROP-01 (max 30 chars)
// - #VALUE_PROP-02 (max 30 chars)
// - #VALUE_PROP-03 (max 30 chars)
// - #VALUE_PROP-04 (max 30 chars)
```

### 2. Template Requirements in Claims Generation

When a template is selected, the system:

1. **Loads template requirements** from the template manager
2. **Adjusts LLM prompts** to include template-specific constraints
3. **Enforces character limits** during copy expansion
4. **Selects appropriate angles** based on template category
5. **Generates compliant content** that fits the template structure

### 3. Template Variations in Ad Generation

```javascript
// Select a template
const template = "Template-Value_Prop_Tick-02-portrait";

// Choose a variation
const variation = "02-portrait"; // or "02-Square"

// Generate ads with the specific variation requirements
```

## File Structure

```
orchestrator/
├── templates.py              # Template management system
├── template_cache.json       # Cached template definitions
├── claims.py                 # Updated claims generation
└── main.py                   # Updated orchestrator

figma-plugin/
├── ui.html                   # Updated UI with template selection
└── code.js                   # Updated plugin logic

claims_api.py                 # New template API endpoints
```

## Configuration

### Template Cache

Templates are cached in `orchestrator/template_cache.json` for performance. The cache includes:

- Template definitions
- Element requirements
- Character limits
- Image weights
- Metadata

### Environment Variables

No additional environment variables are required for the template system.

## Future Enhancements

### 1. Figma API Integration
- Direct scanning of Figma files
- Automatic template discovery
- Real-time template updates

### 2. Advanced Template Features
- Conditional text elements
- Dynamic character limits
- Template inheritance
- Custom validation rules

### 3. Template Analytics
- Usage tracking
- Performance metrics
- Template effectiveness scoring

## Troubleshooting

### Common Issues

1. **Templates not loading**
   - Check if `template_cache.json` exists
   - Verify API server is running on port 8002
   - Check browser console for errors

2. **Template requirements not applying**
   - Ensure template name is correctly specified
   - Check if template exists in cache
   - Verify template has valid element definitions

3. **Character limits not enforced**
   - Check template element definitions
   - Verify `max_chars` values are set
   - Ensure template is properly selected

### Debug Commands

```javascript
// In browser console
console.log('Templates:', window.templates);
console.log('Selected template:', document.getElementById('templateSelector').value);
console.log('Selected variation:', document.getElementById('templateVariation').value);
```

## Getting Started

1. **Start the API server**:
   ```bash
   python3 claims_api.py
   ```

2. **Open the Figma plugin** and navigate to the Template Management section

3. **Scan for templates** or refresh the template cache

4. **Select a template** in the Claims Generator section

5. **Generate template-specific claims** that respect the template requirements

6. **Use the template** in Ad Generation with appropriate variations

## Support

For issues or questions about the Template Management System:

1. Check the browser console for error messages
2. Verify template definitions in `template_cache.json`
3. Ensure all required files are present
4. Check API endpoint responses

The system is designed to be robust and will fall back to standard claims generation if template requirements cannot be loaded.

# Infinite Ad Garden - AI-Powered Ad Generation System

A comprehensive local prototype that generates compelling ad claims, creates ad variants, and automatically matches them with relevant images using AI-powered analysis.

## 🚀 What It Does

1. **Claims Generation**: Uses AI to generate strategic claims based on your brand strategy and product details
2. **Ad Variant Creation**: Expands claims into complete ad copy (headlines, bylines, CTAs)
3. **Image Matching**: Automatically matches ad headlines with relevant images from your asset library
4. **Figma Integration**: Seamlessly generates ad frames directly in Figma with your content

## 🏗️ System Architecture

- **Claims API Server** (Port 8002): Flask server that triggers claims generation
- **Static File Server** (Port 8001): Serves job files and images
- **Figma Plugin**: UI for controlling the entire system
- **Python Orchestrator**: Core AI-powered claims and ad generation logic

## 🚀 Quick Start

### 1) Setup Python Environment
```bash
cd ad-factory-prototype
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure Your Brand Strategy
- **Option A**: Use the existing `inputs/metra_enhanced.json` (Metra beauty supplement)
- **Option B**: Create your own brand strategy file with the required structure
- **Required Fields**: `brand`, `strategy`, `formulation`, `angles`

### 3) Start the Claims API Server
```bash
source .venv/bin/activate
python3 claims_api.py
# -> Claims API running at http://localhost:8002
```

### 4) Start the Static File Server (Optional)
```bash
python3 server.py
# -> Static files served at http://localhost:8001
```

### 5) Setup Figma Template
- In your Figma file, create a frame named **Template/1080x1440** sized 1080×1440.
- Inside it, add:
  - Text layer named **#H1** (for headlines)
  - Text layer named **#BYLINE** (for supporting copy)
  - Text layer named **#CTA** (for call-to-action)
  - Rectangle named **#IMAGE_HERO** (this will get the image fill)
- **Fonts**: Set to Inter Bold (headlines) and Inter Regular (body copy), or your brand fonts

### 6) Install the Figma Plugin
- In Figma desktop: `Plugins → Development → New Plugin... → Click "Link existing plugin"`
- Choose the folder `ad-factory-prototype/figma-plugin` and select `manifest.json`
- The plugin will appear in your plugins list

## 🎯 How to Use the System

### 1) Generate Claims
- Open the Figma plugin
- In the **Claim Generator** section:
  - Select your brand file (e.g., "Metra")
  - Set claim count (1-20)
  - Choose claim style (Benefit-Focused, Problem-Solution, etc.)
  - Click **"Generate Claims"**
- The system will:
  - Show a loading spinner (takes 2-3 minutes)
  - Generate claims using your brand strategy
  - Create a job file with complete ad variants

### 2) View Generated Claims
- After claims are generated, click **"View Claims"**
- See all generated claims with their style and angle information
- Claims are extracted from the job file variants

### 3) Generate Ad Variants
- In the **Ad Generation** section:
  - Enter the Job ID from claims generation (or leave empty for latest)
  - Choose layout mode (Batch Frame or Continue Grid)
  - Set template name (e.g., "Template/1080x1440")
  - Click **"Generate Ads"**
- The system will:
  - Create frames based on your template
  - Populate with generated headlines, bylines, and CTAs
  - Position frames in a grid layout

### 4) Image Matching
- In the **Image Engine** section:
  - Adjust matching threshold (0-100%)
  - Click **"Scan Images"** to find tagged images
  - Click **"Test Matching"** to see image-headline matches
- The system automatically matches ad headlines with relevant images

## 🔧 Configuration Options

### Brand Strategy File Structure
```json
{
  "brand": {
    "name": "Your Brand",
    "tagline": "Your tagline",
    "logo_url": "http://localhost:8001/static/images/logo.png",
    "palette": ["#color1", "#color2"],
    "type": {
      "heading": "Font Name",
      "body": "Font Name"
    }
  },
  "strategy": {
    "format": "1080x1440",
    "target_count": 30
  },
  "formulation": {
    "product_name": "Your Product",
    "key_ingredients": [...]
  },
  "angles": [
    {
      "id": "angle-id",
      "name": "Angle Name",
      "pain_point": "Problem description",
      "positioning": "Solution positioning"
    }
  ]
}
```

### Port Configuration
- **Claims API**: Port 8002 (Flask server for claims generation)
- **Static Files**: Port 8001 (HTTP server for job files and images)
- **Figma Plugin**: Connects to both ports automatically

## 🚀 Advanced Usage

### Custom Brand Strategies
1. Create your brand strategy file in `inputs/your-brand/`
2. Update the brand file selector in the Figma plugin
3. Ensure all required fields are present

### Batch Processing
- Generate multiple claim sets with different styles
- Use different brand strategies for A/B testing
- Export job files for external processing

### Image Tagging System
- Tag your Figma images with descriptive names
- Use keywords that match your brand messaging
- The AI will automatically score and match images to headlines

## 🔍 Troubleshooting

### Common Issues
1. **"No module named 'orchestrator'"**
   - Ensure you're in the project root directory
   - Use `PYTHONPATH=. python3 orchestrator/main.py`

2. **Claims API not responding**
   - Check if the server is running on port 8002
   - Verify virtual environment is activated

3. **No claims generated**
   - Check brand strategy file for missing fields
   - Ensure `logo_url`, `palette`, and `type` are present

4. **Figma plugin errors**
   - Check browser console for network errors
   - Verify both servers are running (ports 8001 and 8002)

### Debug Mode
- Claims API runs in debug mode by default
- Check terminal output for detailed error messages
- Use browser dev tools to inspect API responses

## 📝 Notes & Future Enhancements

### Current Features
- ✅ AI-powered claims generation using OpenAI GPT models
- ✅ Complete ad variant creation (headlines, bylines, CTAs)
- ✅ Automatic image matching with configurable thresholds
- ✅ Figma plugin integration with loading states
- ✅ Session management and unique frame naming
- ✅ Comprehensive brand strategy support

### Planned Enhancements
- 🔄 Compliance guardrails in `orchestrator/compliance.py` (enhanced)
- 🔄 Image generation integration (DALL-E, Midjourney APIs)
- 🔄 Export functionality (PNG/SVG with custom naming)
- 🔄 Cloud storage integration (S3, GCS)
- 🔄 Multi-brand strategy management
- 🔄 A/B testing and performance tracking

### File Structure
```
ad-factory-prototype/
├── orchestrator/          # Core AI logic
├── inputs/               # Brand strategy files
├── out/                  # Generated job files
├── figma-plugin/         # Figma plugin UI
├── claims_api.py         # Claims generation API
├── server.py             # Static file server
└── requirements.txt      # Python dependencies
```

## 🤝 Contributing

This is a prototype system designed for rapid iteration. Key areas for contribution:
- Enhanced compliance and safety features
- Additional AI model integrations
- Improved image matching algorithms
- Extended export and sharing capabilities

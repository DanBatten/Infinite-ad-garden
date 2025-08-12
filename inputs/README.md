# Brand Input Structure

This directory contains brand-specific folders for the Infinite Ad Garden system. Each brand has its own organized folder structure for scalability.

## 📁 Current Structure

```
inputs/
├── Metra/                          # Metra brand folder
│   ├── brand_docs/                 # All reference documents
│   │   ├── brand.txt              # Brand notes
│   │   ├── *.pdf                  # PDF documents (brand decks, research, etc.)
│   │   └── *.rtf                  # Rich text documents
│   ├── metra_enhanced.json        # Generated brand strategy JSON
│   └── brand_config.json          # Brand configuration file
├── BRAND_TEMPLATE/                 # Template for new brands
│   └── brand_config.json          # Template configuration
└── README.md                       # This file
```

## 🚀 Adding New Brands

### 1. Create Brand Folder
```bash
mkdir -p inputs/BRAND_NAME/brand_docs
```

### 2. Copy Template Configuration
```bash
cp inputs/BRAND_TEMPLATE/brand_config.json inputs/BRAND_NAME/
```

### 3. Edit Configuration
Update `inputs/BRAND_NAME/brand_config.json` with your brand details:
- Replace `BRAND_NAME` with actual brand name
- Update industry, product, audience, and positioning
- Adjust file paths as needed

### 4. Add Brand Documents
Place all brand reference documents in `inputs/BRAND_NAME/brand_docs/`:
- Brand guidelines
- Market research
- Product specifications
- Target audience data
- Any other relevant documents

### 5. Update Document Processor
Modify `document_processor.py` to process your new brand:
```python
# Add new brand processing
document_analyses = processor.process_documents("inputs/BRAND_NAME/brand_docs", "BRAND_NAME")
```

### 6. Update Orchestrator
Modify `orchestrator/main.py` to load your brand's JSON:
```python
cfg = load_json("inputs/BRAND_NAME/BRAND_NAME_enhanced.json")
```

## 📋 Brand Configuration Fields

Each `brand_config.json` contains:

- **brand_name**: Display name for the brand
- **brand_folder**: Path to brand folder
- **brand_docs_path**: Path to reference documents
- **output_json**: Path to generated strategy JSON
- **brand_info**: Basic brand information
- **document_processor**: Processing paths
- **orchestrator**: Orchestrator paths
- **figma_plugin**: Plugin display settings

## 🔄 Workflow

1. **Document Processing**: Documents in `brand_docs/` are analyzed
2. **Strategy Generation**: Creates `BRAND_NAME_enhanced.json`
3. **Claims Generation**: Orchestrator uses the enhanced JSON
4. **Ad Generation**: Figma plugin generates ads from claims

## 📝 Benefits of New Structure

- **Scalable**: Easy to add new brands
- **Organized**: Clear separation of concerns
- **Maintainable**: Each brand is self-contained
- **Configurable**: Brand-specific settings
- **Template-driven**: Quick setup for new brands

## 🎯 Example: Adding Nike

```bash
# 1. Create folder structure
mkdir -p inputs/Nike/brand_docs

# 2. Copy and configure template
cp inputs/BRAND_TEMPLATE/brand_config.json inputs/Nike/
# Edit inputs/Nike/brand_config.json

# 3. Add documents
# Copy Nike brand docs to inputs/Nike/brand_docs/

# 4. Process documents
python document_processor.py

# 5. Generate ads
# Use the generated nike_enhanced.json
```

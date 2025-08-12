// Minimal JS version (no TypeScript needed)

// Image matching system for tagged assets
class ImageMatcher {
  constructor() {
    this.imageAssets = [];
    this.threshold = 70; // Default threshold (70%)
    this.tagWeights = {
      // Category weights
      'lifestyle': 3,
      'product': 2,
      'portrait': 2,
      'abstract': 1,
      
      // Mood/Style weights
      'fitness': 2,
      'sophisticated': 2,
      'playful': 1.5,
      'serene': 1.5,
      'empowering': 2,
      'natural': 1.5,
      
      // Content weights
      'model': 2,
      'supplement_bottle': 2,
      'capsules': 1.5,
      'yoga_pose': 1.5,
      'hair_care': 1.5,
      
      // Context weights
      'product': 2,
      'background': 1,
      'hero': 2,
      'supporting': 1
    };
  }

  // Scan Figma file for tagged images
  async scanForTaggedImages() {
    try {
      console.log('🔍 Starting image scan...');
      
      // First, find the BrandAssets frame by searching through all frames
      const allFrames = figma.root.findAll(node => node.type === 'FRAME');
      console.log(`📁 Found ${allFrames.length} total frames:`, allFrames.map(f => f.name));
      
      const brandAssetsFrame = allFrames.find(frame => frame.name === 'BrandAssets');
      
      if (!brandAssetsFrame) {
        console.log('⚠️ BrandAssets frame not found. Please create a frame named "BrandAssets" and add your tagged images there.');
        console.log('💡 Available frames:', allFrames.map(f => f.name));
        return [];
      }
      
      console.log('✅ Found BrandAssets frame:', brandAssetsFrame.name);
      
      // Find all images within the BrandAssets frame
      const allNodes = brandAssetsFrame.findAll(node => true);
      console.log(`🔍 Found ${allNodes.length} total nodes in BrandAssets frame:`, allNodes.map(n => `${n.type}: ${n.name}`));
      
      const images = brandAssetsFrame.findAll(node => 
        node.type === 'RECTANGLE' && 
        node.fills && 
        node.fills.some(fill => fill.type === 'IMAGE')
      );
      
      console.log(`🖼️ Found ${images.length} image rectangles in BrandAssets frame:`, images.map(img => img.name));
      
      this.imageAssets = [];
      
      for (const image of images) {
        if (image.name && image.name.includes('-')) {
          const tags = this.extractTagsFromFilename(image.name);
          if (tags.length > 0) {
            this.imageAssets.push({
              id: image.id,
              name: image.name,
              tags: tags,
              node: image
            });
          }
        }
      }
      
      console.log(`📸 Found ${this.imageAssets.length} tagged images in BrandAssets frame:`, this.imageAssets.map(img => img.name));
      return this.imageAssets;
    } catch (error) {
      console.error('Error scanning for tagged images:', error);
      return [];
    }
  }

  // Extract tags from filename (e.g., "Lifestyle-fitness-model-product.png")
  extractTagsFromFilename(filename) {
    // Remove file extension and split by dashes
    const cleanName = filename.replace(/\.[^/.]+$/, '');
    const tags = cleanName.split('-').map(tag => tag.toLowerCase());
    return tags;
  }

  // Score image relevance to headline
  scoreImageRelevance(imageTags, headline) {
    const headlineLower = headline.toLowerCase();
    let score = 0;
    
    // Check each tag against the headline
    for (const tag of imageTags) {
      // Exact match gets highest score
      if (headlineLower.includes(tag)) {
        score += this.tagWeights[tag] || 2;
      }
      
      // Check for semantic matches
      const semanticMatches = this.getSemanticMatches(tag, headlineLower);
      score += semanticMatches;
    }
    
    // Add bonus for category relevance
    const categoryBonus = this.getCategoryBonus(imageTags, headlineLower);
    score += categoryBonus;
    
    // Add bonus for mood/style relevance
    const moodBonus = this.getMoodBonus(imageTags, headlineLower);
    score += moodBonus;
    
    return score;
  }

  // Get semantic matches (e.g., "beauty" matches "beautiful", "wellness" matches "healthy")
  getSemanticMatches(tag, headline) {
    const semanticMap = {
      // Beauty & Wellness
      'beauty': ['glow', 'radiant', 'radiance', 'beautiful', 'attractive', 'gorgeous', 'stunning', 'skin', 'complexion'],
      'wellness': ['healthy', 'well', 'vitality', 'energy', 'boost', 'nourish', 'nourishing', 'transform'],
      'lifestyle': ['routine', 'daily', 'everyday', 'lifestyle', 'living', 'balance', 'harmony'],
      
      // Product & Ingredients
      'product': ['supplement', 'capsule', 'bottle', 'ingredient', 'formula', 'blend', 'solution'],
      'ingredients': ['ingredient', 'extract', 'natural', 'organic', 'pure', 'clean', 'authentic'],
      'pills': ['capsule', 'pill', 'supplement', 'tablet', 'dose'],
      
      // Mood & Style
      'vibey': ['vibrant', 'energetic', 'dynamic', 'lively', 'exciting', 'powerful', 'transformative'],
      'sophisticated': ['elegant', 'premium', 'luxury', 'refined', 'classy', 'upscale', 'high-end'],
      'natural': ['organic', 'pure', 'clean', 'authentic', 'earth', 'botanical', 'plant-based'],
      
      // Fitness & Health
      'fitness': ['fit', 'healthy', 'strong', 'active', 'workout', 'exercise', 'energy', 'vitality'],
      'health': ['healthy', 'wellness', 'well-being', 'vitality', 'strength', 'energy'],
      
      // Model & Person
      'model': ['person', 'woman', 'lady', 'individual', 'you', 'your', 'self'],
      
      // Specific Benefits
      'hair': ['hair', 'locks', 'tresses', 'mane', 'follicle'],
      'skin': ['skin', 'complexion', 'dermis', 'epidermis', 'texture'],
      'mood': ['mood', 'emotion', 'feeling', 'happiness', 'joy', 'confidence'],
      'energy': ['energy', 'vitality', 'strength', 'power', 'boost', 'recharge']
    };
    
    const matches = semanticMap[tag] || [];
    let score = 0;
    
    for (const match of matches) {
      if (headline.includes(match)) {
        score += 1.5; // Higher score for semantic matches
      }
    }
    
    return score;
  }

  // Get bonus for category relevance
  getCategoryBonus(imageTags, headline) {
    let bonus = 0;
    
    // Beauty/Wellness headlines get bonus for lifestyle/product images
    if (headline.includes('glow') || headline.includes('radiant') || headline.includes('beauty') || 
        headline.includes('skin') || headline.includes('transform') || headline.includes('nourish')) {
      if (imageTags.includes('lifestyle') || imageTags.includes('product') || imageTags.includes('ingredients')) {
        bonus += 2;
      }
    }
    
    // Fitness/Energy headlines get bonus for fitness/lifestyle images
    if (headline.includes('energy') || headline.includes('boost') || headline.includes('vitality') || 
        headline.includes('strength') || headline.includes('active')) {
      if (imageTags.includes('fitness') || imageTags.includes('lifestyle')) {
        bonus += 2;
      }
    }
    
    // Natural/Organic headlines get bonus for natural/ingredient images
    if (headline.includes('natural') || headline.includes('organic') || headline.includes('pure') || 
        headline.includes('ingredient') || headline.includes('extract')) {
      if (imageTags.includes('natural') || imageTags.includes('ingredients') || imageTags.includes('vibey')) {
        bonus += 2;
      }
    }
    
    return bonus;
  }

  // Get bonus for mood/style relevance
  getMoodBonus(imageTags, headline) {
    let bonus = 0;
    
    // Sophisticated/premium headlines get bonus for sophisticated images
    if (headline.includes('premium') || headline.includes('luxury') || headline.includes('elegant') || 
        headline.includes('refined') || headline.includes('upscale')) {
      if (imageTags.includes('sophisticated') || imageTags.includes('direct')) {
        bonus += 1.5;
      }
    }
    
    // Dynamic/energetic headlines get bonus for vibey images
    if (headline.includes('transform') || headline.includes('supercharge') || headline.includes('elevate') || 
        headline.includes('powerful') || headline.includes('dynamic')) {
      if (imageTags.includes('vibey') || imageTags.includes('playful')) {
        bonus += 1.5;
      }
    }
    
    return bonus;
  }

  // Find best matching image for a headline
  findBestImageForHeadline(headline) {
    if (this.imageAssets.length === 0) {
      console.log('⚠️ No tagged images found. Run scanForTaggedImages() first.');
      return null;
    }

    let bestMatch = null;
    let bestScore = 0;

    for (const image of this.imageAssets) {
      const score = this.scoreImageRelevance(image.tags, headline);
      
      if (score > bestScore) {
        bestScore = score;
        bestMatch = image;
      }
    }

    // Apply threshold - only accept matches above threshold
    const thresholdScore = (this.threshold / 100) * 10; // Convert percentage to 0-10 scale
    
    if (bestMatch && bestScore >= thresholdScore) {
      console.log(`🎯 Best image match for "${headline}": ${bestMatch.name} (score: ${bestScore}, threshold: ${thresholdScore})`);
      return bestMatch;
    } else if (bestMatch) {
      // If no match meets threshold, log it but still return the best available as fallback
      console.log(`⚠️ Best image "${bestMatch.name}" (score: ${bestScore}) below threshold ${thresholdScore}, using as fallback`);
      return bestMatch;
    }

    return null;
  }

  // Update matching threshold
  updateThreshold(newThreshold) {
    this.threshold = newThreshold;
    console.log(`🎯 Updated matching threshold to: ${this.threshold}%`);
  }

  // Get all images ranked by relevance to headline
  getRankedImagesForHeadline(headline) {
    if (this.imageAssets.length === 0) {
      return [];
    }

    const scoredImages = this.imageAssets.map(image => {
      return {
        id: image.id,
        name: image.name,
        tags: image.tags,
        node: image.node,
        score: this.scoreImageRelevance(image.tags, headline)
      };
    });

    // Sort by score (highest first)
    return scoredImages.sort((a, b) => b.score - a.score);
  }
}

// Initialize image matcher
const imageMatcher = new ImageMatcher();

// Session counter for unique frame names
let sessionRunCounter = 0;

// Make functions globally accessible for console testing
globalThis.imageMatcher = imageMatcher;
globalThis.scanImages = () => imageMatcher.scanForTaggedImages();
globalThis.testHeadline = (headline) => imageMatcher.findBestImageForHeadline(headline);
globalThis.debugMatching = () => debugImageMatching();
globalThis.getThreshold = () => imageMatcher.threshold;
globalThis.setThreshold = (threshold) => imageMatcher.updateThreshold(threshold);
globalThis.getSessionCounter = () => sessionRunCounter;
globalThis.resetSessionCounter = () => { sessionRunCounter = 0; console.log('Session counter reset to 0'); };
globalThis.debugBatchPositions = () => {
  const page = figma.currentPage;
  const batches = page.findAll(n => n.type === "FRAME" && n.name && n.name.startsWith("Batch/"));
  console.log(`📊 Found ${batches.length} batch frames:`);
  batches.forEach((batch, i) => {
    console.log(`${i + 1}. ${batch.name}: x=${batch.x}, y=${batch.y}, width=${batch.width}, height=${batch.height}`);
  });
};

// Function to place best matching image in ad
async function placeBestImageForHeadline(headline, targetFrame) {
  try {
    // First scan for tagged images if we haven't already
    if (imageMatcher.imageAssets.length === 0) {
      await imageMatcher.scanForTaggedImages();
    }
    
    // Find the best matching image
    const bestImage = imageMatcher.findBestImageForHeadline(headline);
    
    if (!bestImage) {
      console.log('⚠️ No suitable image found for headline:', headline);
      return null;
    }
    
    // Clone the image and place it in the target frame
    const clonedImage = bestImage.node.clone();
    
    // Position the image in the target frame (you can adjust positioning as needed)
    clonedImage.x = targetFrame.x + 50; // Adjust these values based on your template
    clonedImage.y = targetFrame.y + 100;
    
    // Resize to fit your template (adjust dimensions as needed)
    clonedImage.resize(400, 400); // Adjust size based on your template needs
    
    // Add to the target frame
    targetFrame.appendChild(clonedImage);
    
    console.log(`🖼️ Placed image "${bestImage.name}" for headline: "${headline}"`);
    
    return clonedImage;
  } catch (error) {
    console.error('Error placing image:', error);
    return null;
  }
}

// Function to get image suggestions for debugging
function getImageSuggestionsForHeadline(headline) {
  const rankedImages = imageMatcher.getRankedImagesForHeadline(headline);
  console.log(`📊 Image suggestions for "${headline}":`);
  
  rankedImages.forEach((image, index) => {
    console.log(`${index + 1}. ${image.name} (score: ${image.score}) - Tags: ${image.tags.join(', ')}`);
  });
  
  return rankedImages;
}

// Debug function to test image matching system
async function debugImageMatching() {
  console.log('🔍 Debugging Image Matching System...');
  
  // First scan for tagged images
  await imageMatcher.scanForTaggedImages();
  
  if (imageMatcher.imageAssets.length === 0) {
    console.log('❌ No tagged images found. Make sure you have images in a "BrandAssets" frame with names like "Lifestyle-fitness-model-product.png"');
    return;
  }
  
  // Test with some sample headlines
  const testHeadlines = [
    "Transform your beauty routine with holistic wellness",
    "Get fit and feel confident with our premium supplements",
    "Natural ingredients for a healthier lifestyle",
    "Empower yourself with science-backed beauty solutions"
  ];
  
  console.log('\n🧪 Testing Image Matching with Sample Headlines:');
  
  for (const headline of testHeadlines) {
    console.log(`\n📝 Headline: "${headline}"`);
    getImageSuggestionsForHeadline(headline);
  }
  
  console.log('\n✅ Image matching system debug complete!');
}

// Function to find a good fallback product image
async function findFallbackProductImage() {
  try {
    // First scan for tagged images if we haven't already
    if (imageMatcher.imageAssets.length === 0) {
      await imageMatcher.scanForTaggedImages();
    }
    
    if (imageMatcher.imageAssets.length === 0) {
      return null;
    }
    
    // Priority order for fallback images:
    // 1. Product images (highest priority)
    // 2. Ingredient images 
    // 3. Any other image as last resort
    
    // Look for product images first
    const productImages = imageMatcher.imageAssets.filter(img => 
      img.tags.includes('product') || img.tags.includes('bottle') || img.tags.includes('capsules')
    );
    
    if (productImages.length > 0) {
      // Prefer direct/hero shots over vibey/abstract ones
      const directProductImages = productImages.filter(img => 
        img.tags.includes('direct') || img.tags.includes('hero')
      );
      
      if (directProductImages.length > 0) {
        return directProductImages[0]; // Return first direct product image
      }
      
      return productImages[0]; // Return first product image
    }
    
    // Look for ingredient images as second choice
    const ingredientImages = imageMatcher.imageAssets.filter(img => 
      img.tags.includes('ingredients') || img.tags.includes('pills')
    );
    
    if (ingredientImages.length > 0) {
      return ingredientImages[0];
    }
    
    // Last resort: return any available image
    return imageMatcher.imageAssets[0];
    
  } catch (error) {
    console.error('Error finding fallback product image:', error);
    return null;
  }
}

// ---------------- Font resolver (robust + cached + debug) ----------------
let FONT_INDEX_PROMISE = null;
async function getFontIndex() {
  if (!FONT_INDEX_PROMISE) {
    FONT_INDEX_PROMISE = figma.listAvailableFontsAsync();
  }
  return await FONT_INDEX_PROMISE;
}

// normalize: lower-case, strip spaces, dashes, punctuation
function norm(s) { return String(s || "").toLowerCase().replace(/[\s_\-./]+/g, ""); }
const BOLDISH = ["bold","semibold","semibld","demibold","demibld","medium","heavy","black"];
const REGULARISH = ["regular","book","normal","roman"];

async function resolveFontOrNull(family, style) {
  if (!family) return null;
  
  try {
    const fontIndex = await getFontIndex();
    const normalizedFamily = norm(family);
    const normalizedStyle = norm(style);
    
    // Find exact match first
    for (const font of fontIndex) {
      if (norm(font.fontName.family) === normalizedFamily && 
          norm(font.fontName.style) === normalizedStyle) {
        return font.fontName;
      }
    }
    
    // Find family match with any style
    for (const font of fontIndex) {
      if (norm(font.fontName.family) === normalizedFamily) {
        return font.fontName;
      }
    }
    
    return null;
  } catch (error) {
    return null;
  }
}

async function inheritNodeFont(node) {
  if (node.fontName && typeof node.fontName === 'object') {
    return node.fontName;
  }
  return { family: "Inter", style: "Regular" };
}

async function setText(node, value, desiredFamily = null, desiredStyle = "Regular") {
  if (!node || node.type !== "TEXT") return;
  
  try {
    // Try to load the desired font
    const font = await resolveFontOrNull(desiredFamily, desiredStyle);
    if (font) {
      await figma.loadFontAsync(font);
      node.fontName = font;
      figma.notify(`✅ Font loaded: ${font.family} / ${font.style}`);
    }
    
    // Set the text content
    node.characters = value || "";
    
  } catch (error) {
    // Fallback to existing font
    try {
      await inheritNodeFont(node);
      node.characters = value || "";
    } catch (fallbackError) {
      console.error("Failed to set text:", error);
    }
  }
}

// ---------------- Helpers ----------------
async function fetchJob(jobId) {
  const res = await fetch(`http://localhost:8001/out/${jobId}.json`);
  if (!res.ok) throw new Error(`Cannot fetch job: ${res.status}`);
  return await res.json();
}

function positionFrame(frame, template, index, cols = 5, gap = 120, startBelowTemplate = true) {
  const w = template.width;
  const h = template.height;
  const col = index % cols;
  const row = Math.floor(index / cols);
  const xStart = template.x + (startBelowTemplate ? 0 : (w + gap));
  const yStart = template.y + (startBelowTemplate ? (h + gap) : 0);
  frame.x = xStart + col * (w + gap);
  frame.y = yStart + row * (h + gap);
}

function focusOn(node) {
  figma.currentPage.selection = [node];
  figma.viewport.scrollAndZoomIntoView([node]);
}

function positionFrameInGrid(frame, cellWidth, cellHeight, index, cols = 5, gap = 120, pad = gap) {
  const col = index % cols;
  const row = Math.floor(index / cols);
  frame.x = pad + col * (cellWidth + gap);
  frame.y = pad + row * (cellHeight + gap);
}

function existingVariantCount(prefix = "Ad/") {
  return figma.currentPage.findAll(n => n.type === "FRAME" && n.name.startsWith(prefix)).length;
}

function ensureBatchFrame(jobId, template, cols = 5, rows = 6, gap = 120, pad = gap) {
  const page = figma.currentPage;
  let batch = page.findOne(n => n.type === "FRAME" && n.name === `Batch/${jobId}`);
  if (!batch) {
    batch = figma.createFrame();
    batch.name = `Batch/${jobId}`;
    const w = (cols * template.width) + ((cols - 1) * gap) + (pad * 2);
    const h = (rows * template.height) + ((rows - 1) * gap) + (pad * 2);
    batch.resizeWithoutConstraints(w, h);
    // Calculate position based on existing batch frames
    const existingBatches = page.findAll(n => n.type === "FRAME" && n.name && n.name.startsWith("Batch/"));
    let xOffset = template.x + template.width + 200; // Default offset from template
    
    if (existingBatches.length > 0) {
      // Find the rightmost batch frame
      const rightmostBatch = existingBatches.reduce((rightmost, current) => {
        return (current.x + current.width) > (rightmost.x + rightmost.width) ? current : rightmost;
      });
      
      // Position new batch to the right of the rightmost existing batch
      xOffset = rightmostBatch.x + rightmostBatch.width + 120; // 120px gap between batches
      
      console.log(`📍 Positioning new batch: existing rightmost at x=${rightmostBatch.x}, width=${rightmostBatch.width}, new batch at x=${xOffset}`);
    } else {
      console.log(`📍 First batch: positioning at default offset x=${xOffset}`);
    }
    
    batch.x = xOffset;
    batch.y = template.y;
    batch.clipsContent = false;
    // Solid white background
    batch.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
    // Optional: subtle border/rounding
    // batch.strokes = [{ type: "SOLID", color: { r: 0, g: 0, b: 0 }, opacity: 0.06 }];
    // batch.strokeWeight = 1; batch.cornerRadius = 16;
    page.appendChild(batch);
  }
  return batch;
}

async function placeImageFill(rect, url) {
  const res = await fetch(url);
  const bytes = await res.arrayBuffer();
  const image = figma.createImage(new Uint8Array(bytes));
  rect.fills = [{ type: "IMAGE", scaleMode: "FILL", imageHash: image.hash }];
}

function findTemplate(name) {
  const node = figma.root.findOne(n => n.type === "FRAME" && n.name === name);
  if (!node) throw new Error(`Template frame '${name}' not found`);
  return node;
}

// ---------------- Build variant ----------------
async function buildVariant(template, v) {
  const frame = template.clone();
  frame.name = `Ad/${v.id}`;

  const h1   = frame.findOne(n => n.type === "TEXT" && n.name === "#H1");
  const by   = frame.findOne(n => n.type === "TEXT" && n.name === "#BYLINE");
  const cta  = frame.findOne(n => n.type === "TEXT" && n.name === "#CTA");
  const hero = frame.findOne(n => n.type === "RECTANGLE" && n.name === "#IMAGE_HERO");

  // Brand fonts from job JSON (with optional styles)
  const headingFamily = (v && v.type && v.type.heading) || null;
  const bodyFamily    = (v && v.type && v.type.body)    || null;
  const headingStyle  = (v && v.type && v.type.headingStyle) || "Regular";
  const bodyStyle     = (v && v.type && v.type.bodyStyle)    || "Regular";
  const ctaStyle      = (v && v.type && v.type.ctaStyle)     || "Bold";

  await setText(h1,  v.headline, headingFamily, headingStyle);
  await setText(by,  v.byline,   bodyFamily,    bodyStyle);
  await setText(cta, v.cta,      headingFamily, ctaStyle);

  // Try to place best matching tagged image, fallback to URL if no match
  try {
    const bestImage = await placeBestImageForHeadline(v.headline, frame);
    if (bestImage) {
      // Position the image over the hero rectangle
      bestImage.x = hero.x;
      bestImage.y = hero.y;
      bestImage.resize(hero.width, hero.height);
      
      // Move the image to the bottom of the layer stack (behind text)
      frame.insertChild(0, bestImage);
      
      // Hide the original hero rectangle since we're using a tagged image
      hero.visible = false;
      
      console.log(`🖼️ Successfully placed tagged image for headline: "${v.headline}"`);
    } else {
      // Smart fallback: try to find any product image if no good match
      const fallbackImage = await findFallbackProductImage();
      if (fallbackImage) {
        // Place the fallback product image
        const clonedImage = fallbackImage.node.clone();
        clonedImage.x = hero.x;
        clonedImage.y = hero.y;
        clonedImage.resize(hero.width, hero.height);
        
        // Move the image to the bottom of the layer stack (behind text)
        frame.insertChild(0, clonedImage);
        
        // Hide the original hero rectangle
        hero.visible = false;
        
        console.log(`🖼️ Using fallback product image for headline: "${v.headline}"`);
      } else {
        // Last resort: use URL-based image
        await placeImageFill(hero, v.image_url);
        console.log(`🖼️ Using URL image as last resort for headline: "${v.headline}"`);
      }
    }
  } catch (error) {
    console.log(`⚠️ Image placement failed, using fallback: ${error.message}`);
    // Try fallback product image first
    try {
      const fallbackImage = await findFallbackProductImage();
      if (fallbackImage) {
        const clonedImage = fallbackImage.node.clone();
        clonedImage.x = hero.x;
        clonedImage.y = hero.y;
        clonedImage.resize(hero.width, hero.height);
        frame.insertChild(0, clonedImage);
        hero.visible = false;
        console.log(`🖼️ Using fallback product image after error for headline: "${v.headline}"`);
      } else {
        await placeImageFill(hero, v.image_url);
        console.log(`🖼️ Using URL image after error for headline: "${v.headline}"`);
      }
    } catch (fallbackError) {
      await placeImageFill(hero, v.image_url);
      console.log(`🖼️ Using URL image as final fallback for headline: "${v.headline}"`);
    }
  }

  return frame;
}

async function exportFrame(frame) {
  return await frame.exportAsync({ format: "PNG" });
}

// ---------------- UI + message handler ----------------
figma.showUI(__html__, { width: 850, height: 800 });

figma.ui.onmessage = async (msg) => {
  console.log('[Plugin] Received message:', msg);
  
  if (msg.type === "run-job") {

  const jobId = (msg.jobId || "").trim();
  const mode  = msg.mode || "batch";
  const templateName = msg.template || `Template/${job.format}`;
  

  try {
    const BASE = "http://localhost:8001";
    console.log(`[Plugin] Fetching job: ${jobId} from ${BASE}`);
    
    const res = await fetch(`${BASE}/out/${jobId}.json`);
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    const job = await res.json();
    
    console.log(`[Plugin] Job loaded:`, job);
    console.log(`[Plugin] Job format: ${job.format}, variants: ${(job.variants && job.variants.length) || 0}`);

    // Match your strategy.format; your main.py sets layout = `Template/${format}`
    const templateName = msg.template || `Template/${job.format}`;
    console.log(`[Plugin] Looking for template: ${templateName}`);
    
    const template = findTemplate(templateName);
    console.log(`[Plugin] Template found:`, template);
    
    if (!template) {
      throw new Error(`Template frame '${templateName}' not found. Please ensure you have a frame named '${templateName}' in your Figma file.`);
    }
    
    const cellW = template.width;
    const cellH = template.height;

    let i = 0;

    if (mode === "batch") {
      const rows = Math.ceil(job.variants.length / 5); // Default to 5 columns
      const pad  = 120; // Default gap of 120px
      sessionRunCounter++; // Increment counter for unique frame names
      const batch = ensureBatchFrame(`${job.job_id || jobId}_run${sessionRunCounter}`, template, 5, rows, 120, pad);

      for (const v of job.variants) {
        const frame = await buildVariant(template, v);
        batch.appendChild(frame);
        positionFrameInGrid(frame, cellW, cellH, i, 5, 120, pad);
        i++;
      }
      figma.currentPage.selection = [batch];
      figma.viewport.scrollAndZoomIntoView([batch]);
      figma.notify(`Built ${i} variants into Batch/${job.job_id || jobId}_run${sessionRunCounter}`);
    } else {
      const startIndex = existingVariantCount("Ad/");
      sessionRunCounter++; // Increment counter for unique frame names
      for (const v of job.variants) {
        const frame = await buildVariant(template, v);
        frame.x = template.x;
        frame.y = template.y + template.height + 120;
        // Add run counter to frame name to avoid conflicts
        frame.name = `${frame.name}_run${sessionRunCounter}`;
        positionFrameInGrid(frame, cellW, cellH, startIndex + i, 5, 120, 120);
        i++;
      }
      figma.notify(`Infinite Ad Garden: built ${i} variants (continued grid, run ${sessionRunCounter})`);
    }

    // Send success status to UI
    figma.ui.postMessage({
      type: 'status',
      data: {
        adCount: i,
        imageCount: 0
      },
      message: `Successfully generated ${i} ad variants!`,
      status: 'success'
    });

  } catch (e) {
    console.error(`[Plugin] Error:`, e);
    figma.notify(`Error: ${e.message || e}`);
    
    // Send error status to UI
    figma.ui.postMessage({
      type: 'status',
      message: `Error: ${e.message || e}`,
      status: 'error'
    });
  }
  
  } else if (msg.type === "update-threshold") {
    // Update the image matching threshold
    if (msg.threshold !== undefined) {
      imageMatcher.updateThreshold(msg.threshold);
      figma.notify(`Threshold updated to ${msg.threshold}%`);
    }
  } else if (msg.type === "clear-all") {
    // Clear all ad variants
    try {
      const adFrames = figma.currentPage.findAll(node => 
        node.name && (node.name.startsWith("Ad/") || node.name.startsWith("Batch/"))
      );
      
      for (const frame of adFrames) {
        frame.remove();
      }
      
      // Reset session counter when clearing all
      sessionRunCounter = 0;
      
      figma.notify(`Cleared ${adFrames.length} ad frames and reset session counter`);
      
      // Send success status to UI
      figma.ui.postMessage({
        type: 'status',
        message: `Cleared ${adFrames.length} ad frames`,
        status: 'success'
      });
      
    } catch (e) {
      console.error(`[Plugin] Error clearing frames:`, e);
      figma.ui.postMessage({
        type: 'status',
        message: `Error clearing frames: ${e.message}`,
        status: 'error'
      });
    }
    
  } else if (msg.type === "scan-images") {
    // Scan for tagged images
    try {
      const imageMatcher = new ImageMatcher();
      const images = await imageMatcher.scanForTaggedImages();
      
      figma.notify(`Found ${images.length} tagged images`);
      
      // Send success status to UI
      figma.ui.postMessage({
        type: 'status',
        message: `Found ${images.length} tagged images`,
        status: 'success'
      });
      
    } catch (e) {
      console.error(`[Plugin] Error scanning images:`, e);
      figma.ui.postMessage({
        type: 'status',
        message: `Error scanning images: ${e.message}`,
        status: 'error'
      });
    }
  }
};
// Minimal JS version (no TypeScript needed)

// Image matching system for tagged assets
class ImageMatcher {
  constructor() {
    this.imageAssets = [];
    this.threshold = 70; // Default threshold (70%)
    this.tagWeights = {
      // Category weights
      'lifestyle': 3,
      'product': 3,
      'social': 2,
      'ingredient': 3,
      'portrait': 2,
      'abstract': 1,
      'closeup': 1.5,
      
      // Mood/Style weights
      'fitness': 2,
      'sophisticated': 2,
      'playful': 1.5,
      'serene': 1.5,
      'empowering': 2,
      'natural': 1.5,
      'dramatic': 1.5,
      'vibey': 1.5,
      
      // Content weights
      'model': 2,
      'supplement_bottle': 2,
      'capsules': 1.5,
      'ingredients': 1.5,
      'flower': 1.2,
      'yoga_pose': 1.5,
      'hair_care': 1.5,
      'hair': 1.5,
      'skin': 1.5,
      'nail': 1.5,
      'nails': 1.5,
      'gut': 1.5,
      'nutrition': 1.2,
      
      // Context weights
      'product': 2,
      'background': 1,
      'hero': 2.5,
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
          // Add inferred orientation as a tag
          try {
            const ori = computeOrientationTag(image.width, image.height);
            if (ori) tags.push(ori);
          } catch (e) {
            // ignore
          }
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
    // Remove file extension
    const cleanName = filename.replace(/\.[^/.]+$/, '');
    const raw = cleanName.split('-');
    const tags = [];
    for (let t of raw) {
      if (!t) continue;
      let token = String(t).toLowerCase();
      // ignore simple index suffixes like h05, n02, g01, sf04
      if (/^(h|n|g|sf)\d+$/i.test(token)) continue;
      tags.push(token);
      // also split on underscores to capture sub-tags (e.g., hair_care -> hair, care)
      if (token.indexOf('_') !== -1) {
        const subtokens = token.split('_').filter(Boolean);
        for (const st of subtokens) {
          // avoid re-adding the same combined token
          if (!tags.includes(st)) tags.push(st);
        }
      }
    }
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
      'saffron': ['saffron', 'affron', 'calm', 'balance', 'mood', 'sleep'],
      'affron': ['saffron', 'calm', 'balance', 'mood', 'sleep'],
      'chromax': ['chromium', 'metabolic', 'metabolism', 'glucose', 'cravings', 'energy'],
      'de111': ['probiotic', 'gut', 'digest', 'digestive', 'microbiome', 'immune'],
      'lustriva': ['biotin', 'silica', 'hair', 'skin', 'nails', 'elasticity'],
      'biotin': ['hair', 'nails', 'strength'],
      'hyaluronic': ['hydrate', 'hydration', 'moisture', 'plump'],
      'collagen': ['elasticity', 'firm', 'wrinkle', 'supple', 'skin'],
      
      // Mood & Style
      'vibey': ['vibrant', 'energetic', 'dynamic', 'lively', 'exciting', 'powerful', 'transformative'],
      'sophisticated': ['elegant', 'premium', 'luxury', 'refined', 'classy', 'upscale', 'high-end'],
      'natural': ['organic', 'pure', 'clean', 'authentic', 'earth', 'botanical', 'plant-based'],
      'dramatic': ['bold', 'striking', 'high-contrast'],
      
      // Fitness & Health
      'fitness': ['fit', 'healthy', 'strong', 'active', 'workout', 'exercise', 'energy', 'vitality'],
      'health': ['healthy', 'wellness', 'well-being', 'vitality', 'strength', 'energy'],
      
      // Model & Person
      'model': ['person', 'woman', 'lady', 'individual', 'you', 'your', 'self'],
      'hair': ['hair', 'locks', 'tresses', 'mane', 'follicle'],
      'nail': ['nail', 'manicure', 'polish'],
      'skin': ['skin', 'complexion', 'dermis', 'epidermis', 'texture'],
      
      // Specific Benefits
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
      if (imageTags.includes('lifestyle') || imageTags.includes('product') || imageTags.includes('ingredients') || imageTags.includes('model')) {
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
        headline.includes('ingredient') || headline.includes('extract') || headline.includes('saffron') || headline.includes('biotin') || headline.includes('collagen') || headline.includes('hyaluronic') || headline.includes('chromax')) {
      if (imageTags.includes('natural') || imageTags.includes('ingredients') || imageTags.includes('vibey') || imageTags.includes('flower')) {
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
// Cache for template requirements parsed from Guide frames (by full Template- name)
let templateRequirementsCache = {};
// Track images chosen within a single batch to encourage diversity
let BATCH_CHOSEN_IMAGES = new Set();

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

globalThis.alignBatchHeights = () => {
  const page = figma.currentPage;
  const batches = page.findAll(n => n.type === "FRAME" && n.name && n.name.startsWith("Batch/"));
  if (batches.length > 1) {
    const firstBatch = batches[0];
    batches.forEach((batch, i) => {
      if (i > 0) {
        batch.y = firstBatch.y;
        console.log(`📍 Aligned ${batch.name} to Y=${firstBatch.y}`);
      }
    });
    figma.notify(`Aligned ${batches.length - 1} batch frames to same height`);
  } else {
    console.log('📍 Only one batch found, no alignment needed');
  }
};

function computeOrientationTag(w, h) {
  if (!w || !h) return null;
  const ratio = w / h;
  if (Math.abs(ratio - 1) < 0.05) return 'square';
  return ratio > 1 ? 'landscape' : 'portrait';
}

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

// New: pick best image for a variant using headline/messages + guide #IMAGE.weights and orientation
async function placeBestImageForVariant(variant, frame, imagePlaceholder, cleanTemplateName) {
  try {
    if (imageMatcher.imageAssets.length === 0) {
      await imageMatcher.scanForTaggedImages();
    }

    // Build query text from variant fields
    const parts = [];
    // Include headline-like fields
    const vEntries = Object.entries(variant || {});
    for (const [k, v] of vEntries) {
      if (typeof v !== 'string') continue;
      const key = String(k).toLowerCase();
      if (key === 'headline' || key.includes('headline') || key.includes('#headline') || key.startsWith('#h1') || key === 'h1') {
        parts.push(v);
      }
    }
    // Also include message/value prop style fields
    for (const [k, v] of vEntries) {
      if (typeof v !== 'string') continue;
      const key = String(k).toLowerCase();
      if (key.includes('message') || key.includes('msg') || key.includes('value_prop')) {
        parts.push(v);
      }
    }

    // Add weights from guide if available
    const fullTemplateKey = cleanTemplateName ? `Template-${cleanTemplateName}` : (variant && variant.template_name);
    const guide = fullTemplateKey ? templateRequirementsCache[fullTemplateKey] : null;
    const weights = guide && guide['#IMAGE'] && guide['#IMAGE'].weights ? String(guide['#IMAGE'].weights) : '';
    if (weights) parts.push(weights);

    const query = parts.join(' \n ');

    // Desired orientation from variant or placeholder
    let desiredOrientation = null;
    if (variant && typeof variant.template_variation === 'string') {
      if (variant.template_variation.indexOf('square') !== -1) desiredOrientation = 'square';
      else if (variant.template_variation.indexOf('portrait') !== -1) desiredOrientation = 'portrait';
      else if (variant.template_variation.indexOf('landscape') !== -1) desiredOrientation = 'landscape';
    }
    if (!desiredOrientation && imagePlaceholder) {
      desiredOrientation = computeOrientationTag(imagePlaceholder.width, imagePlaceholder.height);
    }

    // Rank images using existing tag-based relevance plus simple boosts from weights and orientation
    const ranked = imageMatcher.imageAssets.map(img => {
      // base score from headline only as before
      const headline = (variant && typeof variant.headline === 'string') ? variant.headline : '';
      let score = imageMatcher.scoreImageRelevance(img.tags, headline);

      // boost if tags appear in weights or query text
      const boostText = `${weights} ${query}`.toLowerCase();
      for (const t of img.tags) {
        if (!t) continue;
        if (boostText.indexOf(t) !== -1) score += 1.0;
      }

      // orientation bonus
      if (desiredOrientation && img.tags.indexOf(desiredOrientation) !== -1) score += 2.0;
      // light penalty if already used in this batch
      try { if (BATCH_CHOSEN_IMAGES && BATCH_CHOSEN_IMAGES.has(img.id)) score -= 1.5; } catch (e) {}

      return { img, score };
    }).sort((a, b) => b.score - a.score);

    // Diversity sampling controlled by threshold slider (lower threshold -> more variety)
    const threshold = Number(imageMatcher.threshold || 70);
    const diversity = Math.max(0, Math.min(1, (100 - threshold) / 100)); // 0..1
    const topK = Math.max(1, Math.min(ranked.length, 1 + Math.round(diversity * 4))); // 1..5
    const temperature = 0.5 + diversity * 1.5; // 0.5..2.0

    let pick = null;
    if (ranked.length) {
      const subset = ranked.slice(0, topK);
      const weights = subset.map(r => Math.exp(r.score / temperature));
      const sum = weights.reduce((a, b) => a + b, 0);
      let r = Math.random() * sum;
      for (let i = 0; i < subset.length; i++) {
        r -= weights[i];
        if (r <= 0) { pick = subset[i].img; break; }
      }
      if (!pick) pick = subset[0].img;
    }
    if (!pick) return null;

    // Clone and place
    const cloned = pick.node.clone();
    cloned.x = imagePlaceholder.x;
    cloned.y = imagePlaceholder.y;
    cloned.resize(imagePlaceholder.width, imagePlaceholder.height);
    frame.insertChild(0, cloned);
    imagePlaceholder.visible = false;
    try { if (BATCH_CHOSEN_IMAGES) BATCH_CHOSEN_IMAGES.add(pick.id); } catch (e) {}
    console.log(`🖼️ Placed image "${pick.name}" for template ${fullTemplateKey} (topK=${topK}, temp=${temperature.toFixed(2)})`);
    return cloned;
  } catch (err) {
    console.error('Error in placeBestImageForVariant:', err);
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
// Optional family alias map to handle common naming differences between brand docs and Figma
const FAMILY_ALIASES = {
  // normalized source -> normalized figma family
  "freightdisppro": "freightdisplaypro",
  "freightdisp": "freightdisplaypro",
  "freightdisplay": "freightdisplaypro",
};
const BOLDISH = ["bold","semibold","semibld","demibold","demibld","medium","heavy","black"];
const REGULARISH = ["regular","book","normal","roman"];

async function resolveFontOrNull(family, style) {
  if (!family) return null;
  
  try {
    const fontIndex = await getFontIndex();
    console.log(`[Fonts] Requested family/style => ${family} / ${style}`);
    let normalizedFamily = norm(family);
    const normalizedStyle = norm(style);
    if (FAMILY_ALIASES[normalizedFamily]) {
      normalizedFamily = FAMILY_ALIASES[normalizedFamily];
    }
    // Also map common typography synonyms
    const STYLE_SYNONYMS = {
      bold: ["bold","demibold","semibold","semi bold","demi bold"],
      regular: ["regular","book","roman","normal"],
      black: ["black","heavy","extrabold","extra bold"],
    };
    function synonymMatches(a, b){
      const na = norm(a), nb = norm(b);
      if (na===nb) return true;
      for (const arr of Object.values(STYLE_SYNONYMS)){
        if (arr.includes(na) && arr.includes(nb)) return true;
      }
      return false;
    }
    
    // helper: candidate style order by desired style (nearest-first)
    const buildStyleCandidates = (desired) => {
      const s = norm(desired || "");
      if (s === "bold") return ["Bold","Semibold","DemiBold","Medium","Regular","Book","Roman","Black","Heavy","ExtraBold"]; 
      if (s === "semibold" || s === "demibold") return ["SemiBold","DemiBold","Bold","Medium","Regular"]; 
      if (s === "medium") return ["Medium","SemiBold","Bold","Regular"]; 
      if (s === "black" || s === "heavy" || s === "extrabold") return ["Black","Heavy","ExtraBold","Bold","SemiBold","Medium","Regular"]; 
      if (s === "light" || s === "thin") return ["Light","Book","Regular"]; 
      if (s === "book" || s === "roman" || s === "normal" || s === "regular") return ["Regular","Book","Roman","Normal"]; 
      return [desired];
    };

    // Find exact match first
    for (const font of fontIndex) {
      if (norm(font.fontName.family) === normalizedFamily && 
          (norm(font.fontName.style) === normalizedStyle || synonymMatches(font.fontName.style, style))) {
        return font.fontName;
      }
    }
    
    // Prefer family match with closest style
    const familyFonts = fontIndex.filter(f => norm(f.fontName.family) === normalizedFamily);
    if (familyFonts.length) {
      console.log(`[Fonts] Available styles for ${family}:`, Array.from(new Set(familyFonts.map(f => f.fontName.style))));
    }
    if (familyFonts.length) {
      const candidates = buildStyleCandidates(style);
      for (const cand of candidates) {
        const hit = familyFonts.find(f => norm(f.fontName.style) === norm(cand));
        if (hit) return hit.fontName;
      }
      // Loose contains search for Bold/Regular, prefer non-italic
      const want = norm(style || "");
      if (want === "bold") {
        const loose = familyFonts.find(f => /bold/i.test(f.fontName.style) && !/oblique|italic/i.test(f.fontName.style));
        if (loose) return loose.fontName;
      }
      if (want === "regular") {
        const loose = familyFonts.find(f => /regular|book|roman/i.test(f.fontName.style) && !/oblique|italic/i.test(f.fontName.style));
        if (loose) return loose.fontName;
      }
      // last resort: return first family font
      return familyFonts[0].fontName;
    }

    // Fuzzy family matching: includes/startsWith
    const families = Array.from(new Set(fontIndex.map(f => f.fontName.family)));
    const normalizedFamilies = families.map(f => ({ raw: f, n: norm(f) }));
    // Try includes or startsWith either direction
    const fuzzy = normalizedFamilies.find(ff => ff.n.includes(normalizedFamily) || normalizedFamily.includes(ff.n));
    if (fuzzy) {
      // Pick the first style available for that family
      const anyFont = fontIndex.find(f => norm(f.fontName.family) === norm(fuzzy.raw));
      if (anyFont) return anyFont.fontName;
    }
    
    return null;
  } catch (error) {
    return null;
  }
}

async function inheritNodeFont(node) {
  try {
    // Check if node has a valid font
    if (node.fontName && typeof node.fontName === 'object' && 
        node.fontName.family && node.fontName.style) {
      return node.fontName;
    }
    
    // Check parent nodes for font inheritance
    let parent = node.parent;
    while (parent) {
      if (parent.fontName && typeof parent.fontName === 'object' && 
          parent.fontName.family && parent.fontName.style) {
        return parent.fontName;
      }
      parent = parent.parent;
    }
    
    // Default fallback
    return { family: "Inter", style: "Regular" };
  } catch (error) {
    console.warn("⚠️ Error in inheritNodeFont:", error);
    return { family: "Inter", style: "Regular" };
  }
}

async function setText(node, value, desiredFamily = null, desiredStyle = "Regular") {
  if (!node || node.type !== "TEXT") return;
  
  try {
    // First, ensure we have a working font
    let workingFont = null;
    
    // Try to load the desired font
    if (desiredFamily) {
      try {
        const font = await resolveFontOrNull(desiredFamily, desiredStyle);
        if (font) {
          await figma.loadFontAsync(font);
          workingFont = font;
          console.log(`✅ Font loaded: ${font.family} / ${font.style}`);
        }
      } catch (fontError) {
        console.warn(`⚠️ Failed to load desired font ${desiredFamily} ${desiredStyle}:`, fontError);
      }
    }
    
    // If desired font failed, try to inherit from node or use fallback
    if (!workingFont) {
      try {
        workingFont = await inheritNodeFont(node);
        await figma.loadFontAsync(workingFont);
        console.log(`✅ Using inherited/fallback font: ${workingFont.family} / ${workingFont.style}`);
      } catch (inheritError) {
        console.warn(`⚠️ Failed to inherit font:`, inheritError);
        // Last resort: use Inter Regular
        workingFont = { family: "Inter", style: "Regular" };
        await figma.loadFontAsync(workingFont);
        console.log(`✅ Using fallback font: ${workingFont.family} / ${workingFont.style}`);
      }
    }
    
    // Set the text content then enforce font across the entire range
    node.characters = value || "";
    if (workingFont) {
      try {
        // Apply to whole range to override existing range styles (e.g., Black)
        node.setRangeFontName(0, node.characters.length, workingFont);
      } catch (rangeErr) {
        node.fontName = workingFont;
      }
    }
    console.log(`✅ Text set successfully: "${value}"`);
    
  } catch (error) {
    console.error("❌ Failed to set text:", error);
    // Try one more time with basic Inter font
    try {
      const basicFont = { family: "Inter", style: "Regular" };
      await figma.loadFontAsync(basicFont);
      node.fontName = basicFont;
      node.characters = value || "";
      console.log(`✅ Text set with basic font fallback: "${value}"`);
    } catch (finalError) {
      console.error("❌ Final fallback failed:", finalError);
      figma.notify(`❌ Failed to set text: ${error.message}`);
    }
  }
}

// ---------------- Font Management ----------------
async function preloadCommonFonts() {
  const commonFonts = [
    { family: "Inter", style: "Regular" },
    { family: "Inter", style: "Medium" },
    { family: "Inter", style: "Bold" },
    { family: "Inter", style: "SemiBold" }
  ];
  
  try {
    for (const font of commonFonts) {
      await figma.loadFontAsync(font);
      console.log(`✅ Preloaded font: ${font.family} ${font.style}`);
    }
  } catch (error) {
    console.warn("⚠️ Some fonts failed to preload:", error);
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

function ensureBatchFrame(batchName, template, cols = 5, rows = 6, gap = 120, pad = gap) {
  const page = figma.currentPage;
  let batch = page.findOne(n => n.type === "FRAME" && n.name === batchName);
  if (!batch) {
    batch = figma.createFrame();
    batch.name = batchName;
    // mark as IAG batch so we can find it later regardless of naming convention
    try { batch.setPluginData('iag-batch', '1'); } catch (e) {}
    const w = (cols * template.width) + ((cols - 1) * gap) + (pad * 2);
    const h = (rows * template.height) + ((rows - 1) * gap) + (pad * 2);
    batch.resizeWithoutConstraints(w, h);
    // Calculate position based on existing batch frames (by plugin data flag)
    const existingBatches = page.findAll(n => n.type === "FRAME" && (n.getPluginData && n.getPluginData('iag-batch') === '1'));
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
    
    // Ensure all batches are aligned at the same height
    if (existingBatches.length > 0) {
      // Use the Y position of the first batch to maintain consistent height alignment
      batch.y = existingBatches[0].y;
      console.log(`📍 Aligning height: using existing batch Y position ${batch.y}`);
    } else {
      // First batch: use template Y position
      batch.y = template.y;
      console.log(`📍 First batch: using template Y position ${batch.y}`);
    }
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
  console.log(`🔧 Building variant for:`, v);
  const frame = template.clone();
  frame.name = `Ad/${v.id}`;
  
  // Debug: Show all text elements in the template
  const allTextNodes = frame.findAll(n => n.type === "TEXT");
  console.log(`🔍 Template contains ${allTextNodes.length} text elements:`, allTextNodes.map(n => n.name));
  console.log(`🔍 Text node names:`, allTextNodes.map(n => n.name));
  
  // Debug: Show all rectangles (potential image placeholders)
  const allRectangles = frame.findAll(n => n.type === "RECTANGLE");
  console.log(`🔍 Template contains ${allRectangles.length} rectangles:`, allRectangles.map(n => n.name));

  // Brand fonts from job JSON (with optional styles)
  const headingFamily = (v && v.type && v.type.heading) || null;
  const bodyFamily    = (v && v.type && v.type.body)    || null;
  const headingStyle  = (v && v.type && v.type.headingStyle) || "Regular";
  const bodyStyle     = (v && v.type && v.type.bodyStyle)    || "Regular";
  const ctaStyle      = (v && v.type && v.type.ctaStyle)     || "Bold";

  // Dynamically find and populate all text elements based on what exists in the template
  // This makes the system completely flexible to any template structure
  
  // Get all available text fields from the variant data
  const textFields = Object.entries(v).filter(([key, value]) => 
    typeof value === 'string' && value.trim() && 
    !['id', 'layout', 'template_name', 'template_variation', 'logo_url', 'palette'].includes(key)
  );
  
  console.log(`🔍 Available text fields in variant:`, textFields.map(([key, value]) => `${key}: "${value}"`));
  
  // For each text field, try to find a matching text node in the template
  for (const [fieldName, fieldValue] of textFields) {
    let textNode = null;
    
    // Try to find text nodes that match the field name
    if (fieldName === 'headline') {
      textNode = frame.findOne(n => n.type === "TEXT" && (
        n.name.includes("HEADLINE") || n.name.includes("H1") || n.name.includes("TITLE")
      ));
    } else if (fieldName === 'cta') {
      textNode = frame.findOne(n => n.type === "TEXT" && (
        n.name.includes("CTA") || n.name.includes("CALL") || n.name.includes("ACTION")
      ));
    } else if (fieldName === 'value_props' && Array.isArray(fieldValue)) {
      // Handle value_props as an array - look for numbered value prop nodes
      const valuePropNodes = frame.findAll(n => n.type === "TEXT" && n.name.includes("VALUE_PROP"));
      console.log(`🔍 Found ${valuePropNodes.length} value prop nodes:`, valuePropNodes.map(n => n.name));
      
      // Sort them to ensure consistent ordering
      valuePropNodes.sort((a, b) => a.name.localeCompare(b.name));
      
      // Populate each value prop node with corresponding data
      for (let i = 0; i < Math.min(valuePropNodes.length, fieldValue.length); i++) {
        if (fieldValue[i]) {
          await setText(valuePropNodes[i], fieldValue[i], bodyFamily, bodyStyle);
          console.log(`✅ Set ${valuePropNodes[i].name}: "${fieldValue[i]}"`);
        }
      }
      continue; // Skip the regular text setting for arrays
    } else {
      // For any other field, try multiple matching strategies
      textNode = frame.findOne(n => n.type === "TEXT" && (
        // Strategy 1: Exact name match
        n.name === fieldName ||
        // Strategy 2: Name contains field name
        n.name.toLowerCase().includes(fieldName.toLowerCase()) ||
        // Strategy 3: Map generated field names to Figma text layer names
        (fieldName === 'message_01' && (n.name === '#MESSAGE1' || n.name.includes('MESSAGE1') || n.name.includes('MSG1') || n.name.includes('TEXT1'))) ||
        (fieldName === 'message_02' && (n.name === '#MESSAGE2' || n.name.includes('MESSAGE2') || n.name.includes('MSG2') || n.name.includes('TEXT2'))) ||
        (fieldName === 'headline' && (n.name === '#HEADLINE' || n.name.includes('HEADLINE') || n.name.includes('H1') || n.name.includes('TITLE'))) ||
        // Strategy 4: Look for common text layer naming patterns
        n.name.includes('#') && n.name.toLowerCase().includes(fieldName.toLowerCase())
      ));
      
      if (!textNode) {
        console.log(`🔍 No exact match for ${fieldName}, trying broader search...`);
        // Last resort: look for any text node that might be related
        const potentialMatches = frame.findAll(n => n.type === "TEXT" && 
          (n.name.includes('#') || n.name.includes('TEXT') || n.name.includes('LABEL')));
        console.log(`🔍 Potential text nodes for ${fieldName}:`, potentialMatches.map(n => n.name));
      }
    }
    
    // Set the text if we found a matching node
    if (textNode) {
      const upper = String(fieldName || '').toUpperCase();
      const isHeadlineField = (fieldName === 'headline') || upper.includes('HEADLINE') || upper.includes('#HEADLINE') || upper === 'H1' || upper === '#H1' || upper === 'TITLE';
      const isCtaField = (fieldName === 'cta') || upper.includes('CTA') || upper.includes('#CTA') || upper.includes('CALL TO ACTION');

      const fontFamily = isHeadlineField ? (headingFamily || bodyFamily) : bodyFamily;
      const fontStyle = isHeadlineField ? (headingStyle || 'Regular') : (isCtaField ? (ctaStyle || 'Bold') : (bodyStyle || 'Regular'));

      await setText(textNode, fieldValue, fontFamily, fontStyle);
      console.log(`✅ Set ${fieldName}: "${fieldValue}" using ${fontFamily || 'inherited'} / ${fontStyle}`);
    } else {
      console.log(`⚠️ No text node found for field: ${fieldName}`);
    }
  }

  // Dynamically find image placeholder (could be #IMAGE, #IMAGE_HERO, #HERO, etc.)
  const imagePlaceholder = frame.findOne(n => n.type === "RECTANGLE" && (
    n.name.includes("IMAGE") || 
    n.name.includes("HERO") || 
    n.name.includes("PHOTO")
  ));
  
  if (imagePlaceholder) {
    console.log(`🔍 Found image placeholder: ${imagePlaceholder.name}`);
    
    // Try to place best matching tagged image using variant context + guide weights
    try {
      const cleanTemplateName = (v && v.template_name) ? v.template_name.replace(/^Template-/, '') : null;
      const placed = await placeBestImageForVariant(v, frame, imagePlaceholder, cleanTemplateName);
      if (placed) {
        // already positioned inside helper
      } else {
        // Smart fallback: try to find any product image if no good match
        const fallbackImage = await findFallbackProductImage();
        if (fallbackImage) {
          // Place the fallback product image
          const clonedImage = fallbackImage.node.clone();
          clonedImage.x = imagePlaceholder.x;
          clonedImage.y = imagePlaceholder.y;
          clonedImage.resize(imagePlaceholder.width, imagePlaceholder.height);
          
          // Move the image to the bottom of the layer stack (behind text)
          frame.insertChild(0, clonedImage);
          
          // Hide the original image placeholder
          imagePlaceholder.visible = false;
          
          console.log(`🖼️ Using fallback product image for headline: "${v.headline}"`);
        } else {
          // Last resort: use URL-based image if available, otherwise skip
          if (v.image_url) {
            await placeImageFill(imagePlaceholder, v.image_url);
            console.log(`🖼️ Using URL image as last resort for headline: "${v.headline}"`);
          } else {
            console.log(`⚠️ No image URL available for headline: "${v.headline}", skipping image placement`);
          }
        }
      }
    } catch (error) {
      console.log(`⚠️ Image placement failed, using fallback: ${error.message}`);
      // Try fallback product image first
      try {
        const fallbackImage = await findFallbackProductImage();
        if (fallbackImage) {
          const clonedImage = fallbackImage.node.clone();
          clonedImage.x = imagePlaceholder.x;
          clonedImage.y = imagePlaceholder.y;
          clonedImage.resize(imagePlaceholder.width, imagePlaceholder.height);
          frame.insertChild(0, clonedImage);
          imagePlaceholder.visible = false;
          console.log(`🖼️ Using fallback product image after error for headline: "${v.headline}"`);
        } else {
          if (v.image_url) {
            await placeImageFill(imagePlaceholder, v.image_url);
            console.log(`🖼️ Using URL image after error for headline: "${v.headline}"`);
          } else {
            console.log(`⚠️ No image URL available for headline: "${v.headline}", skipping image placement`);
          }
        }
      } catch (fallbackError) {
        if (v.image_url) {
          await placeImageFill(imagePlaceholder, v.image_url);
          console.log(`🖼️ Using URL image as final fallback for headline: "${v.headline}"`);
        } else {
          console.log(`⚠️ No image URL available for headline: "${v.headline}", skipping image placement`);
        }
      }
    }
  } else {
    console.log(`⚠️ No image placeholder found in template, skipping image placement`);
  }

  return frame;
}

async function exportFrame(frame) {
  return await frame.exportAsync({ format: "PNG" });
}

// ---------------- UI + message handler ----------------
figma.showUI(__html__, { width: 850, height: 900 });

// Preload common fonts when plugin starts
preloadCommonFonts().then(() => {
  console.log("✅ Common fonts preloaded successfully");
}).catch(error => {
  console.warn("⚠️ Font preloading failed:", error);
});

figma.ui.onmessage = async (msg) => {
  console.log('[Plugin] Received message:', msg);
  
  if (msg.type === "run-job") {

  const jobId = (msg.jobId || "").trim();
  const mode  = msg.mode || "batch";
  const templateVersion = msg.templateVersion || "";
  const variations = msg.variations || ["portrait", "square"];
  

  try {
    const BASE = "http://localhost:8001";
    console.log(`[Plugin] Fetching job: ${jobId} from ${BASE}`);
    
    const res = await fetch(`${BASE}/out/${jobId}.json`);
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    const job = await res.json();
    
    console.log(`[Plugin] Job loaded:`, job);
    console.log(`[Plugin] Job format: ${job.format}, variants: ${(job.variants && job.variants.length) || 0}`);
    console.log(`[Plugin] Template version: ${templateVersion}, variations: ${variations.join(', ')}`);

    // Filter variants based on selected variations
    let filteredVariants = job.variants;
    
    // Debug: Show variant structure
    console.log(`[Plugin] All variants:`, job.variants.map(v => ({
      id: v.id,
      layout: v.layout,
      template_variation: v.template_variation,
      template_name: v.template_name
    })));
    
    if (templateVersion && variations.length > 0) {
      filteredVariants = job.variants.filter(variant => {
        if (variant.template_variation) {
          const parts = String(variant.template_variation).split('-');
          const variantType = parts.length > 1 ? parts[1] : undefined; // Expect 'portrait' or 'square'
          console.log(`[Plugin] Variant ${variant.id}: template_variation="${variant.template_variation}", extracted type="${variantType}"`);
          // If we can't extract a type (e.g., template_variation is just '01'), don't filter it out
          if (!variantType) return true;
          return variations.includes(variantType);
        }
        console.log(`[Plugin] Variant ${variant.id}: no template_variation field, including by default`);
        return true; // Include if no template variation specified
      });
      if (filteredVariants.length === 0) {
        console.warn(`[Plugin] No variants matched the requested variations; falling back to all variants.`);
        filteredVariants = job.variants;
      }
      console.log(`[Plugin] Filtered variants: ${filteredVariants.length} of ${job.variants.length} based on selected variations`);
    }

    // Use the first variant's template name as the base template
    // This should come from the claims generation, not be constructed from job format
    const baseTemplateName = (filteredVariants[0] && filteredVariants[0].template_name) || (job.variants[0] && job.variants[0].template_name);
    if (!baseTemplateName) {
      throw new Error(`No template name found in variants. Please ensure claims were generated with a template.`);
    }
    console.log(`[Plugin] Base template name: ${baseTemplateName}`);
    
    // Extract the base name without "Template-" prefix for searching
    const cleanTemplateName = baseTemplateName.replace(/^Template-/, '');
    console.log(`[Plugin] Clean template name: ${cleanTemplateName}`);
    
    // Debug: Show what we're actually looking for
    console.log(`[Plugin] Job format: ${job.format}`);
    console.log(`[Plugin] First variant template_name: ${filteredVariants[0] && filteredVariants[0].template_name}`);
    console.log(`[Plugin] All variant template names:`, filteredVariants.map(v => v.template_name));
    
    // First try to find template on the _Template_Library page
    let template = null;
    let templatePage = null;
    
    // Look for _Template_Library page
    for (const page of figma.root.children) {
      if (page.name === "_Template_Library") {
        templatePage = page;
        break;
      }
    }
    
    // Debug: Show what templates are available in the Figma file
    if (templatePage) {
      const availableTemplates = templatePage.findAll(node => 
        node.type === "FRAME" && 
        (node.name.startsWith("Template-") || node.name.startsWith("Design-") || node.name.startsWith("Guide-"))
      );
      console.log(`[Plugin] Available templates on _Template_Library page:`, availableTemplates.map(t => t.name));
    }
    
    // Also check current page for available templates
    const currentPageTemplates = figma.currentPage.findAll(node => 
      node.type === "FRAME" && 
      (node.name.startsWith("Template-") || node.name.startsWith("Design-") || node.name.startsWith("Guide-"))
    );
    console.log(`[Plugin] Available templates on current page:`, currentPageTemplates.map(t => t.name));
    
    // Try multiple template name patterns for Design frames first, then Guide frames as fallback
    const templateNamePatterns = [
      // Design frames (preferred for ad generation)
      `Design-${cleanTemplateName}-${templateVersion || '01'}-${variations[0] || 'portrait'}`, // Full Design frame name
      `Design-${cleanTemplateName}-${templateVersion || '01'}-${variations[1] || 'square'}`, // Alternative variation
      `Design-${cleanTemplateName}-${templateVersion || '01'}`, // Design frame with version only
      `Design-${cleanTemplateName}-portrait`, // Design frame with portrait
      `Design-${cleanTemplateName}-square`, // Design frame with square
      // Guide frames (fallback if Design frames not found)
      `Guide-${cleanTemplateName}-${templateVersion || '01'}`, // Guide frame with version
      `Guide-${cleanTemplateName}`, // Guide frame without version
      // Also try the original template name as a fallback
      baseTemplateName
    ];
    
    console.log(`[Plugin] Trying template name patterns:`, templateNamePatterns);
    console.log(`[Plugin] Looking for template: ${baseTemplateName}`);
    console.log(`[Plugin] Clean template name: ${cleanTemplateName}`);
    console.log(`[Plugin] Template version: ${templateVersion}`);
    console.log(`[Plugin] Variations:`, variations);
    
    if (templatePage) {
      console.log(`[Plugin] Looking for template on _Template_Library page`);
      
      // Debug: Show all available frame names on the template page
      const allFrames = templatePage.findAll(node => node.type === "FRAME");
      console.log(`[Plugin] Available frames on _Template_Library page:`, allFrames.map(f => f.name));
      
      for (const pattern of templateNamePatterns) {
        template = templatePage.findOne(node => 
          node.type === "FRAME" && 
          node.name === pattern
        );
        if (template) {
          console.log(`[Plugin] Found template with pattern: ${pattern}`);
          break;
        }
      }
    }
    
    // If not found on template page, try current page as fallback
    if (!template) {
      console.log(`[Plugin] Template not found on _Template_Library page, trying current page`);
      for (const pattern of templateNamePatterns) {
        template = findTemplate(pattern);
        if (template) {
          console.log(`[Plugin] Found template on current page with pattern: ${pattern}`);
          break;
        }
      }
    }
    
    console.log(`[Plugin] Template found:`, template);
    
    if (!template) {
      throw new Error(`Template frame not found. Tried patterns: ${templateNamePatterns.join(', ')}. Please ensure you have a frame with one of these names in the _Template_Library page or current page.`);
    }
    
    const cellW = template.width;
    const cellH = template.height;

    let i = 0;

    if (mode === "batch") {
      const rows = Math.ceil(filteredVariants.length / 5); // Default to 5 columns
      const pad  = 120; // Default gap of 120px
      sessionRunCounter++; // Increment counter for unique frame names
      // Build a descriptive batch frame name from user selections and job metadata
      const brandName = (job && job.brand) ? String(job.brand).trim() : "Brand";
      const version = (templateVersion || '01');
      const varLabel = (Array.isArray(variations) && variations.length > 0) ? variations.join('+') : 'all';
      const style = (filteredVariants[0] && filteredVariants[0].style) ? filteredVariants[0].style : (job.claim_style || 'style');
      const batchName = `${brandName}-${cleanTemplateName}-${style}-v${version}-${varLabel}-${job.job_id || jobId}_run${sessionRunCounter}`;

      // Reset per-batch chosen images set to encourage diversity within this batch
      try { BATCH_CHOSEN_IMAGES = new Set(); } catch (e) {}
      const batch = ensureBatchFrame(batchName, template, 5, rows, 120, pad);

      for (const v of filteredVariants) {
        const frame = await buildVariant(template, v);
        batch.appendChild(frame);
        positionFrameInGrid(frame, cellW, cellH, i, 5, 120, pad);
        i++;
      }
      figma.currentPage.selection = [batch];
      figma.viewport.scrollAndZoomIntoView([batch]);
      figma.notify(`Built ${i} variants into ${batchName}`);
    } else {
      const startIndex = existingVariantCount("Ad/");
      sessionRunCounter++; // Increment counter for unique frame names
      for (const v of filteredVariants) {
        const frame = await buildVariant(template, v);
        frame.x = template.x;
        frame.y = template.y + template.height + 120;
        // Add run counter to frame name to avoid conflicts
        frame.name = `${frame.name}_run${sessionRunCounter}`;
        positionFrameInBox(frame, cellW, cellH, startIndex + i, 5, 120, 120);
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
  
  } else if (msg.type === "scan-templates") {
    // Scan templates from Figma file
    try {
      console.log(`🔍 Scanning for templates in Figma file...`);
      
      // First, try to find the _Template_Library page
      let templatePage = null;
      for (const page of figma.root.children) {
        if (page.name === "_Template_Library") {
          templatePage = page;
          break;
        }
      }
      
      if (!templatePage) {
        // Fallback to current page if _Template_Library not found
        templatePage = figma.currentPage;
        console.log(`[Plugin] _Template_Library page not found, using current page`);
      } else {
        console.log(`[Plugin] Found _Template_Library page: ${templatePage.name}`);
      }
      
      // Look for template frames on the template page
      // Only show Template containers in the dropdown (parent containers)
      // Design frames and Guide frames are found automatically when generating ads
      const templateFrames = templatePage.findAll(node => 
        node.type === "FRAME" && 
        node.name && 
        node.name.startsWith("Template-")
      );
      
      // Also find all Design and Guide frames for version dropdown population
      const allFrames = templatePage.findAll(node => 
        node.type === "FRAME" && 
        node.name && 
        (node.name.startsWith("Template-") || node.name.startsWith("Design-") || node.name.startsWith("Guide-"))
      );
      
      // Scan Guide frames to extract JSON template requirements
      const guideFrames = templatePage.findAll(node => 
        node.type === "FRAME" && 
        node.name && 
        node.name.startsWith("Guide-")
      );
      
      console.log(`[Plugin] Found ${guideFrames.length} guide frames for template requirements`);
      console.log(`[Plugin] Guide frame names:`, guideFrames.map(f => f.name));
      
      // Extract template requirements from Guide frames
      const templateRequirements = {};
      for (const guideFrame of guideFrames) {
        try {
          // Find the #GUIDE text layer within the guide frame
          const guideTextNode = guideFrame.findOne(node => 
            node.type === "TEXT" && 
            node.name === "#GUIDE"
          );
          
          console.log(`[Plugin] Searching for #GUIDE text in ${guideFrame.name}...`);
          console.log(`[Plugin] All text nodes in ${guideFrame.name}:`, guideFrame.findAll(node => node.type === "TEXT").map(t => t.name));
          
                      if (guideTextNode && guideTextNode.characters) {
              console.log(`[Plugin] Found #GUIDE text in ${guideFrame.name}:`, guideTextNode.characters.substring(0, 100) + "...");
              
              // Try to parse the JSON content
              try {
                const guideData = JSON.parse(guideTextNode.characters);
                const templateName = guideData.template_name;
                
                if (templateName) {
                  // Map the template name to the actual Template frame name
                  const actualTemplateName = `Template-${templateName}`;
                  templateRequirements[actualTemplateName] = guideData;
                  console.log(`[Plugin] Successfully parsed guide for ${templateName}, mapped to ${actualTemplateName}:`, guideData);
                }
              } catch (parseError) {
                console.log(`[Plugin] Failed to parse JSON in ${guideFrame.name}:`, parseError.message);
              }
            }
        } catch (error) {
          console.log(`[Plugin] Error processing guide frame ${guideFrame.name}:`, error.message);
        }
      }
      
      console.log(`[Plugin] Found ${templateFrames.length} template containers on ${templatePage.name}:`, templateFrames.map(f => f.name));
      console.log(`[Plugin] Found ${allFrames.length} total frames (including Design and Guide frames)`);
      
      // Log each template found for debugging
      templateFrames.forEach((frame, index) => {
        console.log(`[Plugin] Template ${index + 1}: "${frame.name}" (${frame.width}x${frame.height})`);
      });
      
      // Send the found templates to the UI to update the cache
      console.log(`[Plugin] Sending template requirements to UI:`, templateRequirements);
      console.log(`[Plugin] Template requirements keys:`, Object.keys(templateRequirements));
      console.log(`[Plugin] Template frame names:`, templateFrames.map(f => f.name));
      console.log(`[Plugin] Template requirements mapping:`, Object.entries(templateRequirements).map(([key, value]) => `${key} -> ${value.template_name}`));
      
      // Also cache template requirements locally for image matching
      try {
        templateRequirementsCache = templateRequirements || {};
      } catch (e) {
        templateRequirementsCache = {};
      }

      figma.ui.postMessage({
        type: 'templates-scanned',
        templates: templateFrames.map(f => ({
          name: f.name,
          type: f.type,
          width: f.width,
          height: f.height
        })),
        allFrames: allFrames.map(f => ({
          name: f.name,
          type: f.type,
          width: f.width,
          height: f.height
        })),
        templateRequirements: templateRequirements
      });
      
      figma.notify(`Found ${templateFrames.length} template frames on ${templatePage.name}`);
      
      // Send success status to UI
      figma.ui.postMessage({
        type: 'status',
        message: `Template scanning completed: Found ${templateFrames.length} templates on ${templatePage.name}`,
        status: 'success'
      });
      
    } catch (error) {
      console.error('Error scanning templates:', error);
      figma.notify(`Error scanning templates: ${error.message}`);
      
      // Send error status to UI
      figma.ui.postMessage({
        type: 'status',
        message: `Error scanning templates: ${error.message}`,
        status: 'error'
      });
    }
    
  } else if (msg.type === "generate-claims") {
    // Generate claims using the existing system
    try {
      console.log(`🎯 Triggering claims generation: ${msg.claimCount} claims, style: ${msg.claimStyle}, brand: ${msg.brandFile}`);
      
      // Show progress notification
      figma.notify(`🚀 Starting claims generation for ${msg.brandFile}...`);
      
      // Show loading state in UI
      figma.ui.postMessage({ type: 'show-loading' });
      
      // Call the claims API
      fetch('http://localhost:8002/generate-claims', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          brandFile: msg.brandFile,
          claimCount: msg.claimCount,
          claimStyle: msg.claimStyle,
          templateName: msg.templateName,
          knowledgeAdInfluence: msg.knowledgeAdInfluence || 'medium',
          knowledgeBrandInfluence: msg.knowledgeBrandInfluence || 'medium'
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          figma.ui.postMessage({ 
            type: 'claims-generated', 
            claims: data.claims,
            message: data.message,
            job_id: data.job_id
          });
          figma.notify(`✅ ${data.message}`);
        } else {
          figma.ui.postMessage({ type: 'hide-loading' });
          figma.notify(`❌ Error: ${data.error}`);
        }
      })
      .catch(error => {
        figma.ui.postMessage({ type: 'hide-loading' });
        figma.notify(`❌ Network error: ${error.message}`);
      });
      
    } catch (error) {
      console.error('Error triggering claims generation:', error);
      figma.ui.postMessage({ type: 'hide-loading' });
      figma.notify(`Error: ${error.message}`);
    }
  } else if (msg.type === "view-claims") {
    // View generated claims from existing system
    try {
      figma.notify(`📝 Checking for generated claims...`);
      
      // This will be handled by the UI to show the claims display
      figma.ui.postMessage({ type: 'show-claims' });
      
    } catch (error) {
      console.error('Error viewing claims:', error);
      figma.notify(`Error: ${error.message}`);
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
        || (node.getPluginData && node.getPluginData('iag-batch') === '1')
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
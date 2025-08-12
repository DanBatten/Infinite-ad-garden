#!/usr/bin/env python3
"""
Document Processor for AI Ad Generator
Uses OpenAI to analyze brand documents and create structured input
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DocumentProcessor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def analyze_pdf_text(self, pdf_path: str, brand_name: str) -> Dict[str, Any]:
        """Analyze PDF text content using OpenAI"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"\n--- Page Content ---\n{page_text.strip()}\n"
                    except:
                        continue
                
                if text.strip():
                    print(f"📄 Extracted {len(text)} characters from {Path(pdf_path).name}")
                    
                    # Use OpenAI to analyze the extracted text
                    response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": f"""
You are a brand strategy expert analyzing text extracted from a PDF for {brand_name}.

Please analyze this extracted text and extract comprehensive brand strategy information:

{text[:3000]}  # Limit text length for API

Extract and structure the information into a detailed JSON object with these sections:

**BRAND IDENTITY (Deep Dive):**
- name, tagline, mission, vision, values, personality, brand story, founding story, brand evolution
- **brand_narrative: core story arc, key moments, transformation journey, brand mythology**
- **brand_voice: personality traits, communication style, tone guidelines, language preferences**
- **brand_promise: what customers can expect, guarantee, commitment to customers**

**TARGET AUDIENCE (Detailed Personas):**
- demographics: age, gender, location, income, education, occupation, family status, lifestyle_stage
- psychographics: lifestyle, values, beliefs, attitudes, interests, hobbies, media consumption, aspirations
- behavioral: purchasing behavior, brand loyalty, decision-making process, usage patterns, shopping_preferences
- pain_points: specific challenges, frustrations, unmet needs, pain points in detail
- motivations: emotional drivers, goals, aspirations, what they want to achieve
- objections: why they might not buy, concerns, hesitations, barriers
- **customer_journey: awareness, consideration, purchase, usage, loyalty stages with specific touchpoints and pain points**
- **brand_interaction: how they discover, research, engage with brands, preferred communication channels**

**MARKET POSITIONING (Strategic Analysis):**
- unique_value_proposition: detailed UVP with specific benefits
- positioning_statement: comprehensive positioning statement
- competitive_advantages: specific advantages over competitors
- market_landscape: key competitors, market trends, industry insights
- differentiation: how they stand out, unique features, proprietary elements

**PRODUCT/SERVICE (Comprehensive):**
- key_offerings: detailed product descriptions, variants, SKUs
- features: specific features with benefits, technical specifications
- benefits: primary and secondary benefits, emotional and functional
- pricing_strategy: pricing tiers, value proposition, cost structure
- use_cases: specific scenarios, applications, when/how to use
- quality_indicators: certifications, testing, quality assurance

**VISUAL IDENTITY (Detailed):**
- color_palette: specific hex codes, color psychology, usage guidelines
- typography: font families, hierarchy, usage rules, brand fonts
- design_style: detailed style description, design principles, aesthetic guidelines
- brand_personality: visual personality traits, mood, feeling
- logo_guidelines: logo usage, variations, clear space, applications

**MESSAGING (Strategic):**
- key_messages: primary messages, supporting messages, campaign themes
- tone_of_voice: detailed tone description, personality traits, communication style
- communication_style: how they communicate, language preferences, style
- content_themes: major themes, sub-themes, content pillars
- storytelling_approach: narrative structure, story elements, brand stories
- messaging_hierarchy: primary, secondary, tertiary messages

**MARKETING CHANNELS (Tactical):**
- primary_channels: main channels, channel mix, digital vs traditional
- content_strategy: content types, frequency, themes, formats
- campaign_approach: campaign strategy, seasonal themes, promotional approach
- distribution: how products reach customers, retail strategy, online presence

**ART DIRECTION (Creative):**
- visual_style: detailed style description, aesthetic preferences, design direction
- image_references: specific visual references, inspiration sources, mood boards
- mood_boards: visual themes, color stories, photographic style
- photography_style: specific photography approach, lighting, composition
- design_elements: recurring design elements, patterns, visual motifs

**CONTENT STRATEGY (Content Marketing):**
- content_themes: major content pillars, themes, topics
- storytelling_approach: narrative approach, story structure, brand storytelling
- key_narratives: main brand stories, customer journey narratives, transformation stories
- content_formats: preferred content types, media formats, distribution channels

**CUSTOMER JOURNEY & BRAND INTERACTION:**
- **customer_journey_stages: awareness, consideration, purchase, usage, loyalty with specific touchpoints**
- **pain_points_by_stage: what frustrates customers at each journey stage**
- **opportunities_by_stage: where brands can add value and differentiate**
- **brand_interaction_patterns: how customers discover, research, engage, and stay loyal**
- **communication_preferences: preferred channels, timing, frequency, content types by stage**

**COMPLIANCE (Regulatory):**
- industry_regulations: specific regulations, compliance requirements, industry standards
- legal_requirements: legal obligations, disclaimers, terms of service
- disclaimers: required disclaimers, health claims, legal language
- avoid: restricted language, prohibited claims, compliance guidelines

**INDUSTRY ANALYSIS (Market Context):**
- industry_overview: industry size, growth trends, market dynamics
- market_trends: emerging trends, consumer behavior shifts, industry evolution
- competitive_landscape: key players, market share, competitive positioning
- industry_challenges: industry-wide challenges, regulatory changes, market pressures
- opportunities: market gaps, emerging needs, growth opportunities

Return only valid JSON with comprehensive details in each section.
"""
                            }
                        ],
                        max_tokens=4000,
                        temperature=0.1
                    )
                    
                    content = response.choices[0].message.content.strip()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if start != -1 and end != 0:
                            return json.loads(content[start:end])
                
                # If no text extracted, return basic structure
                return {
                    "brand_identity": {"name": brand_name},
                    "extraction_method": "pdf_fallback",
                    "note": "Limited text extraction from PDF"
                }
                
        except Exception as e:
            print(f"PDF analysis failed: {e}")
            return {
                "brand_identity": {"name": brand_name},
                "extraction_method": "error",
                "error": str(e)
            }
    
    def analyze_text_file(self, txt_path: str, brand_name: str) -> Dict[str, Any]:
        """Analyze text files using OpenAI"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            print(f"📝 Analyzing text file: {Path(txt_path).name}")
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
You are a brand strategy expert analyzing a text document for {brand_name}.

Please analyze this text and extract brand strategy information:

{content}

Extract and structure the information into a JSON object with these sections:
- brand_identity: name, tagline, mission, values, personality
- target_audience: demographics, psychographics, pain_points, motivations
- market_positioning: unique_value_proposition, positioning_statement, competitive_advantages
- product_service: key_offerings, features, benefits, pricing_strategy
- visual_identity: color_palette, typography, design_style, brand_personality
- messaging: key_messages, tone_of_voice, communication_style, content_themes
- marketing_channels: primary_channels, content_strategy, campaign_approach
- art_direction: visual_style, image_references, mood_boards, photography_style
- content_strategy: content_themes, storytelling_approach, key_narratives
- compliance: industry_regulations, legal_requirements, disclaimers, avoid

Return only valid JSON.
"""
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    return {
                        "brand_identity": {"name": brand_name},
                        "extraction_method": "text_analysis",
                        "raw_response": content
                    }
                    
        except Exception as e:
            print(f"Error analyzing text file {txt_path}: {e}")
            return {}
    
    def process_documents(self, input_folder: str, brand_name: str) -> Dict[str, Any]:
        """Process all documents in a folder"""
        combined_analysis = {}
        input_path = Path(input_folder)
        
        # Process PDFs
        for pdf_file in input_path.glob("*.pdf"):
            print(f"🤖 Processing PDF: {pdf_file.name}")
            pdf_analysis = self.analyze_pdf_text(str(pdf_file), brand_name)
            if pdf_analysis:
                combined_analysis[f"pdf_{pdf_file.stem}"] = pdf_analysis
        
        # Process text files
        for txt_file in input_path.glob("*.txt"):
            txt_analysis = self.analyze_text_file(str(txt_file), brand_name)
            if txt_analysis:
                combined_analysis[f"txt_{txt_file.stem}"] = txt_analysis
        
        return combined_analysis
    
    def synthesize_brand_strategy(self, document_analyses: Dict[str, Any], brand_name: str) -> Dict[str, Any]:
        """Synthesize all document analyses into a unified brand strategy"""
        
        prompt = f"""
You are a senior brand strategy expert synthesizing multiple document analyses for {brand_name}.

Below are analyses from different documents (PDFs and text files). Please synthesize them into a single, comprehensive brand strategy JSON that will be used for generating compelling advertising claims.

IMPORTANT: Create a RICH, DETAILED strategy that provides deep insights for claims generation. Fill in ALL fields with comprehensive, actionable information.

Document analyses:
{json.dumps(document_analyses, indent=2)}

Please create a unified brand strategy that combines all the information from these documents.
If there are conflicts, resolve them logically. If information is missing, make reasonable inferences based on the brand name and context.

**CRITICAL REQUIREMENTS FOR CLAIMS GENERATION:**
- Provide SPECIFIC, ACTIONABLE insights that can be turned into compelling claims
- Include DETAILED personas with specific pain points and motivations
- Offer COMPREHENSIVE competitive analysis and positioning
- Include INDUSTRY context and market trends
- Provide EMOTIONAL and FUNCTIONAL benefit details
- Include OBJECTION HANDLING insights
- Offer STORYTELLING elements for narrative claims

Return ONLY a valid JSON object with this comprehensive structure:
{{
  "brand_identity": {{
    "name", "tagline", "mission", "vision", "values", "personality", 
    "brand_story", "founding_story", "brand_evolution", "core_beliefs",
    "brand_narrative", "brand_voice", "brand_promise"
  }},
  "target_audience": {{
    "demographics": {{ "age", "gender", "location", "income", "education", "occupation", "family_status", "lifestyle_stage" }},
    "psychographics": {{ "lifestyle", "values", "beliefs", "attitudes", "interests", "hobbies", "media_consumption", "aspirations" }},
    "behavioral": {{ "purchasing_behavior", "brand_loyalty", "decision_making", "usage_patterns", "shopping_preferences" }},
    "pain_points": {{ "primary_pains", "secondary_pains", "daily_frustrations", "unmet_needs", "pain_point_intensity" }},
    "motivations": {{ "emotional_drivers", "goals", "aspirations", "desired_outcomes", "motivation_strength" }},
    "objections": {{ "primary_concerns", "hesitations", "barriers", "competitive_switching", "price_sensitivity" }},
    "personas": [
      {{
        "name", "age", "occupation", "lifestyle", "primary_pain", "primary_motivation", 
        "decision_factors", "media_preferences", "shopping_behavior", "brand_relationship"
      }}
    ],
    "customer_journey": {{ "awareness", "consideration", "purchase", "usage", "loyalty" }},
    "brand_interaction": {{ "discovery", "research", "engagement", "loyalty_patterns" }}
  }},
  "market_positioning": {{
    "unique_value_proposition", "positioning_statement", "competitive_advantages", 
    "market_landscape", "differentiation", "brand_promise", "value_proposition", "market_gap"
  }},
  "product_service": {{
    "key_offerings", "features", "benefits", "pricing_strategy", "use_cases", 
    "quality_indicators", "product_story", "ingredients_benefits", "scientific_backing"
  }},
  "visual_identity": {{
    "color_palette", "typography", "design_style", "brand_personality", 
    "logo_guidelines", "visual_principles", "aesthetic_guidelines"
  }},
  "messaging": {{
    "key_messages", "tone_of_voice", "communication_style", "content_themes", 
    "storytelling_approach", "messaging_hierarchy", "emotional_triggers", "benefit_language"
  }},
  "marketing_channels": {{
    "primary_channels", "content_strategy", "campaign_approach", "distribution", 
    "channel_effectiveness", "audience_reach", "content_preferences"
  }},
  "art_direction": {{
    "visual_style", "image_references", "mood_boards", "photography_style", 
    "design_elements", "creative_guidelines", "visual_inspiration"
  }},
  "content_strategy": {{
    "content_themes", "storytelling_approach", "key_narratives", "content_formats", 
    "narrative_structure", "transformation_stories", "customer_journey"
  }},
  "customer_journey_insights": {{
    "customer_journey_stages": {{ "awareness", "consideration", "purchase", "usage", "loyalty" }},
    "pain_points_by_stage": {{ "awareness": "Limited information", "consideration": "Price sensitivity", "purchase": "Lack of immediate results", "usage": "Complexity", "loyalty": "Lack of ongoing support" }},
    "opportunities_by_stage": {{ "awareness": "Enhanced visibility", "consideration": "Value proposition", "purchase": "Immediate results", "usage": "Easy to use", "loyalty": "Ongoing support" }},
    "brand_interaction_patterns": {{ "discovery": "Content marketing", "research": "Social media", "engagement": "Interactive content", "loyalty_patterns": "Personalized recommendations" }},
    "communication_preferences": {{ "awareness": "Educational content", "consideration": "Value-based messaging", "purchase": "Results-focused", "usage": "Supportive content", "loyalty": "Engagement-driven" }}
  }},
  "compliance": {{
    "industry_regulations", "legal_requirements", "disclaimers", "avoid", 
    "health_claims", "regulatory_guidelines", "compliance_notes"
  }},
  "industry_analysis": {{
    "industry_overview", "market_trends", "competitive_landscape", "industry_challenges", 
    "opportunities", "market_size", "growth_potential", "consumer_behavior_shifts"
  }},
  "claims_insights": {{
    "primary_claim_themes", "emotional_benefits", "functional_benefits", "social_proof_elements", 
    "urgency_triggers", "credibility_factors", "differentiation_claims", "objection_counters"
  }}
}}

**IMPORTANT: Make this output RICH with specific details that can be directly used for claims generation.**
Return only the JSON object, no additional text.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=6000
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    try:
                        return json.loads(json_str)
                    except:
                        pass
                
                # If all else fails, create a basic structure
                print("⚠️ Creating fallback brand strategy structure")
                return {
                    "brand_identity": {
                        "name": brand_name,
                        "tagline": "Innovative solutions for modern challenges",
                        "mission": "To provide cutting-edge solutions that empower our customers",
                        "values": ["Innovation", "Quality", "Customer Focus", "Sustainability"],
                        "personality": "Professional, innovative, and trustworthy"
                    },
                    "target_audience": {
                        "demographics": "Professionals aged 25-45",
                        "psychographics": ["Tech-savvy", "Quality-conscious", "Innovation-seeking"],
                        "pain_points": ["Complex solutions", "Poor user experience", "Lack of innovation"],
                        "motivations": ["Efficiency", "Innovation", "Quality", "Success"]
                    },
                    "market_positioning": {
                        "unique_value_proposition": "Cutting-edge solutions that simplify complex challenges",
                        "positioning_statement": "The innovative partner for modern business success",
                        "competitive_advantages": ["Advanced technology", "Superior user experience", "Proven results"]
                    },
                    "product_service": {
                        "key_offerings": ["Technology solutions", "Consulting services", "Product development"],
                        "features": ["User-friendly", "Scalable", "Secure", "Innovative"],
                        "benefits": ["Increased efficiency", "Cost savings", "Competitive advantage"],
                        "pricing_strategy": "Premium value-based pricing"
                    },
                    "visual_identity": {
                        "color_palette": ["#2563EB", "#1E40AF", "#FFFFFF", "#F3F4F6"],
                        "typography": {"heading": "Inter", "body": "Inter"},
                        "design_style": "Modern, clean, and professional",
                        "brand_personality": "Innovative and trustworthy"
                    },
                    "messaging": {
                        "key_messages": ["Innovation that works", "Simplify complexity", "Drive success"],
                        "tone_of_voice": "Professional, confident, and approachable",
                        "communication_style": "Clear, concise, and compelling",
                        "content_themes": ["Innovation", "Technology", "Success", "Efficiency"]
                    },
                    "marketing_channels": {
                        "primary_channels": ["Digital marketing", "Content marketing", "Social media"],
                        "content_strategy": "Educational and thought leadership content",
                        "campaign_approach": "Data-driven and results-focused"
                    },
                    "art_direction": {
                        "visual_style": "Modern and professional",
                        "image_references": ["Clean technology", "Professional environments", "Innovation"],
                        "mood_boards": ["Tech-forward", "Professional", "Innovative"],
                        "photography_style": "Clean, modern, and professional"
                    },
                    "content_strategy": {
                        "content_themes": ["Innovation", "Technology", "Success", "Efficiency"],
                        "storytelling_approach": "Customer success stories and innovation narratives",
                        "key_narratives": ["Transforming challenges into opportunities", "Innovation that delivers results"]
                    },
                    "compliance": {
                        "industry_regulations": ["Data protection", "Industry standards"],
                        "legal_requirements": ["Privacy compliance", "Terms of service"],
                        "disclaimers": ["Results may vary", "Professional advice recommended"],
                        "avoid": ["Over-promising", "Technical jargon", "Complex explanations"]
                    }
                }
                    
        except Exception as e:
            print(f"Error synthesizing brand strategy: {e}")
            return {}
    
    def create_enhanced_input_json(self, brand_strategy: Dict[str, Any], brand_name: str) -> Dict[str, Any]:
        """Create the enhanced input JSON that includes image generation capabilities"""
        
        # Ensure brand_strategy is a dict, not a string
        if isinstance(brand_strategy, str):
            try:
                brand_strategy = json.loads(brand_strategy)
            except:
                brand_strategy = {}
        
        # Enhanced structure with comprehensive details for claims generation
        enhanced_json = {
            "brand_name": brand_name,
            "strategy": {
                "audience": brand_strategy.get("target_audience", {}).get("demographics", "General audience"),
                "channels": brand_strategy.get("marketing_channels", {}).get("primary_channels", ["Social Media", "Digital"]),
                "format": "1080x1440",
                "target_count": 30,
                "style_weights": {
                    "first_person": 0.4,
                    "why_explainer": 0.3,
                    "stat_hook": 0.3
                }
            },
            "brand": {
                "name": brand_strategy.get("brand_identity", {}).get("name", brand_name),
                "tagline": brand_strategy.get("brand_identity", {}).get("tagline", ""),
                "mission": brand_strategy.get("brand_identity", {}).get("mission", ""),
                "vision": brand_strategy.get("brand_identity", {}).get("vision", ""),
                "values": brand_strategy.get("brand_identity", {}).get("values", []),
                "personality": brand_strategy.get("brand_identity", {}).get("personality", "Professional and trustworthy"),
                "tone": brand_strategy.get("messaging", {}).get("tone_of_voice", "Professional and friendly"),
                "brand_story": brand_strategy.get("brand_identity", {}).get("brand_story", ""),
                "founding_story": brand_strategy.get("brand_identity", {}).get("founding_story", ""),
                "brand_evolution": brand_strategy.get("brand_identity", {}).get("brand_evolution", ""),
                "core_beliefs": brand_strategy.get("brand_identity", {}).get("core_beliefs", []),
                "brand_narrative": brand_strategy.get("brand_identity", {}).get("brand_narrative", ""),
                "brand_voice": brand_strategy.get("brand_identity", {}).get("brand_voice", ""),
                "brand_promise": brand_strategy.get("brand_identity", {}).get("brand_promise", ""),
                "logo_url": f"http://localhost:8001/static/images/{brand_name.lower()}_logo.png",
                "palette": brand_strategy.get("visual_identity", {}).get("color_palette", ["#2C3E50", "#E74C3C", "#ECF0F1", "#3498DB", "#FFFFFF"]),
                "type": {
                    "heading": "Inter Bold",
                    "body": "Inter Regular"
                }
            },
            "audience": {
                "primary": brand_strategy.get("target_audience", {}).get("demographics", "General audience"),
                "psychographics": brand_strategy.get("target_audience", {}).get("psychographics", []),
                "pain_points": brand_strategy.get("target_audience", {}).get("pain_points", []),
                "motivations": brand_strategy.get("target_audience", {}).get("motivations", []),
                "behavioral": brand_strategy.get("target_audience", {}).get("behavioral", {}),
                "objections": brand_strategy.get("target_audience", {}).get("objections", {}),
                "personas": brand_strategy.get("target_audience", {}).get("personas", []),
                "customer_journey": brand_strategy.get("target_audience", {}).get("customer_journey", {}),
                "brand_interaction": brand_strategy.get("target_audience", {}).get("brand_interaction", {})
            },
            "positioning": {
                "uvp": brand_strategy.get("market_positioning", {}).get("unique_value_proposition", ""),
                "positioning_statement": brand_strategy.get("market_positioning", {}).get("positioning_statement", ""),
                "competitive_advantages": brand_strategy.get("market_positioning", {}).get("competitive_advantages", []),
                "market_landscape": brand_strategy.get("market_positioning", {}).get("market_landscape", ""),
                "differentiation": brand_strategy.get("market_positioning", {}).get("differentiation", ""),
                "brand_promise": brand_strategy.get("market_positioning", {}).get("brand_promise", ""),
                "value_proposition": brand_strategy.get("market_positioning", {}).get("value_proposition", ""),
                "market_gap": brand_strategy.get("market_positioning", {}).get("market_gap", "")
            },
            "product": {
                "key_offerings": brand_strategy.get("product_service", {}).get("key_offerings", []),
                "features": brand_strategy.get("product_service", {}).get("features", []),
                "benefits": brand_strategy.get("product_service", {}).get("benefits", []),
                "pricing_strategy": brand_strategy.get("product_service", {}).get("pricing_strategy", ""),
                "use_cases": brand_strategy.get("product_service", {}).get("use_cases", []),
                "quality_indicators": brand_strategy.get("product_service", {}).get("quality_indicators", []),
                "product_story": brand_strategy.get("product_service", {}).get("product_story", ""),
                "ingredients_benefits": brand_strategy.get("product_service", {}).get("ingredients_benefits", []),
                "scientific_backing": brand_strategy.get("product_service", {}).get("scientific_backing", "")
            },
            "visual": {
                "color_palette": brand_strategy.get("visual_identity", {}).get("color_palette", ["#000000", "#FFFFFF"]),
                "typography": {
                    "heading": "Inter",  # Use default for now
                    "body": "Inter"      # Use default for now
                },
                "design_style": brand_strategy.get("visual_identity", {}).get("design_style", "Clean and modern"),
                "brand_personality": brand_strategy.get("visual_identity", {}).get("brand_personality", "Professional"),
                "logo_guidelines": brand_strategy.get("visual_identity", {}).get("logo_guidelines", ""),
                "visual_principles": brand_strategy.get("visual_identity", {}).get("visual_principles", ""),
                "aesthetic_guidelines": brand_strategy.get("visual_identity", {}).get("aesthetic_guidelines", "")
            },
            "messaging": {
                "key_messages": brand_strategy.get("messaging", {}).get("key_messages", []),
                "tone_of_voice": brand_strategy.get("messaging", {}).get("tone_of_voice", "Professional and friendly"),
                "communication_style": brand_strategy.get("messaging", {}).get("communication_style", "Clear and engaging"),
                "content_themes": brand_strategy.get("content_strategy", {}).get("content_themes", []),
                "storytelling_approach": brand_strategy.get("content_strategy", {}).get("storytelling_approach", ""),
                "messaging_hierarchy": brand_strategy.get("messaging", {}).get("messaging_hierarchy", ""),
                "emotional_triggers": brand_strategy.get("messaging", {}).get("emotional_triggers", []),
                "benefit_language": brand_strategy.get("messaging", {}).get("benefit_language", [])
            },
            "art_direction": {
                "visual_style": brand_strategy.get("art_direction", {}).get("visual_style", "Clean and modern"),
                "image_references": brand_strategy.get("art_direction", {}).get("image_references", []),
                "mood_boards": brand_strategy.get("art_direction", {}).get("mood_boards", []),
                "photography_style": brand_strategy.get("art_direction", {}).get("photography_style", "Professional product photography"),
                "image_style": brand_strategy.get("art_direction", {}).get("image_style", "minimal, product-focused with brand colors"),
                "design_elements": brand_strategy.get("art_direction", {}).get("design_elements", []),
                "creative_guidelines": brand_strategy.get("art_direction", {}).get("creative_guidelines", ""),
                "visual_inspiration": brand_strategy.get("art_direction", {}).get("visual_inspiration", "")
            },
            "compliance": {
                "industry_regulations": brand_strategy.get("compliance", {}).get("industry_regulations", []),
                "legal_requirements": brand_strategy.get("compliance", {}).get("legal_requirements", []),
                "disclaimers": brand_strategy.get("compliance", {}).get("disclaimers", []),
                "avoid": brand_strategy.get("compliance", {}).get("avoid", []),
                "health_claims": brand_strategy.get("compliance", {}).get("health_claims", []),
                "regulatory_guidelines": brand_strategy.get("compliance", {}).get("regulatory_guidelines", ""),
                "compliance_notes": brand_strategy.get("compliance", {}).get("compliance_notes", "")
            },
            "industry_analysis": {
                "industry_overview": brand_strategy.get("industry_analysis", {}).get("industry_overview", ""),
                "market_trends": brand_strategy.get("industry_analysis", {}).get("market_trends", []),
                "competitive_landscape": brand_strategy.get("industry_analysis", {}).get("competitive_landscape", ""),
                "industry_challenges": brand_strategy.get("industry_analysis", {}).get("industry_challenges", []),
                "opportunities": brand_strategy.get("industry_analysis", {}).get("opportunities", []),
                "market_size": brand_strategy.get("industry_analysis", {}).get("market_size", ""),
                "growth_potential": brand_strategy.get("industry_analysis", {}).get("growth_potential", ""),
                "consumer_behavior_shifts": brand_strategy.get("industry_analysis", {}).get("consumer_behavior_shifts", [])
            },
            "claims_insights": {
                "primary_claim_themes": brand_strategy.get("claims_insights", {}).get("primary_claim_themes", []),
                "emotional_benefits": brand_strategy.get("claims_insights", {}).get("emotional_benefits", []),
                "functional_benefits": brand_strategy.get("claims_insights", {}).get("functional_benefits", []),
                "social_proof_elements": brand_strategy.get("claims_insights", {}).get("social_proof_elements", []),
                "urgency_triggers": brand_strategy.get("claims_insights", {}).get("urgency_triggers", []),
                "credibility_factors": brand_strategy.get("claims_insights", {}).get("credibility_factors", []),
                "differentiation_claims": brand_strategy.get("claims_insights", {}).get("differentiation_claims", []),
                "objection_counters": brand_strategy.get("claims_insights", {}).get("objection_counters", [])
            },
            "customer_journey_insights": {
                "customer_journey_stages": brand_strategy.get("customer_journey_insights", {}).get("customer_journey_stages", {}),
                "pain_points_by_stage": brand_strategy.get("customer_journey_insights", {}).get("pain_points_by_stage", {}),
                "opportunities_by_stage": brand_strategy.get("customer_journey_insights", {}).get("opportunities_by_stage", {}),
                "brand_interaction_patterns": brand_strategy.get("customer_journey_insights", {}).get("brand_interaction_patterns", {}),
                "communication_preferences": brand_strategy.get("customer_journey_insights", {}).get("communication_preferences", {})
            },
            "assets": {
                "logo_url": f"http://localhost:8001/static/images/{brand_name.lower()}_logo.png",
                "product_image_url": f"http://localhost:8001/static/images/{brand_name.lower()}_product.png",
                "brand_guidelines_url": f"http://localhost:8001/static/images/{brand_name.lower()}_guidelines.pdf"
            },
            "image_generation": {
                "enabled": True,
                "style_model": "dall-e-3",
                "art_direction": brand_strategy.get("art_direction", {}).get("visual_style", "Clean and modern"),
                "reference_images": brand_strategy.get("art_direction", {}).get("image_references", []),
                "color_constraints": brand_strategy.get("visual_identity", {}).get("color_palette", ["#000000", "#FFFFFF"]),
                "composition_preferences": brand_strategy.get("art_direction", {}).get("composition_preferences", "Product-focused with clean backgrounds"),
                "brand_elements": brand_strategy.get("art_direction", {}).get("brand_elements", [])
            },
            "formulation": {
                "product_name": brand_strategy.get("product", {}).get("name", "Holistic Beauty Supplement"),
                "key_ingredients": brand_strategy.get("product", {}).get("ingredients", []),
                "banned_claims": [
                    "treat disease", "cure illness", "prevent medical conditions",
                    "medical treatment", "therapeutic cure", "healing properties"
                ]
            },
            "angles": [
                {
                    "id": "beauty-from-within",
                    "name": "Beauty from Within",
                    "pain_point": "External beauty products don't address root causes",
                    "trigger": "Frustration with surface-level solutions",
                    "positioning": "Holistic beauty through internal nourishment",
                    "headline_examples": [
                        "Transform your beauty routine from the inside out",
                        "Why your skincare routine isn't working (and what does)"
                    ]
                },
                {
                    "id": "busy-lifestyle",
                    "name": "Busy Lifestyle Solutions",
                    "pain_point": "No time for complex beauty routines",
                    "trigger": "Overwhelmed by beauty choices",
                    "positioning": "Simple, effective beauty in one daily capsule",
                    "headline_examples": [
                        "Busy woman? Get holistic beauty benefits without the hassle",
                        "One capsule, five beauty benefits, zero time wasted"
                    ]
                },
                {
                    "id": "scientific-backing",
                    "name": "Science-Backed Beauty",
                    "pain_point": "Skeptical of unproven beauty claims",
                    "trigger": "Desire for credible solutions",
                    "positioning": "Clinically-supported ingredients for visible results",
                    "headline_examples": [
                        "The science behind beauty supplements that actually work",
                        "Clinically-proven ingredients for your beauty transformation"
                    ]
                }
            ]
        }
        
        return enhanced_json

    def create_brand_config(self, brand_name, enhanced_json):
        """Create a brand configuration file based on the enhanced JSON"""
        try:
            # Read the template config file
            template_path = "inputs/BRAND_TEMPLATE/brand_config.json"
            if not os.path.exists(template_path):
                print(f"⚠️ Template config not found: {template_path}")
                return False
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            # Update template with brand-specific information
            config = template_config.copy()
            config["brand_name"] = brand_name
            config["brand_folder"] = f"inputs/{brand_name}"
            config["brand_docs_path"] = f"inputs/{brand_name}/brand_docs"
            config["output_json"] = f"inputs/{brand_name}/{brand_name.lower()}_enhanced.json"
            
            # Update brand info from enhanced JSON
            if "brand" in enhanced_json:
                config["brand_info"]["industry"] = enhanced_json.get("strategy", {}).get("industry", "Unknown")
                config["brand_info"]["primary_product"] = enhanced_json.get("brand", {}).get("product_name", "Unknown")
                config["brand_info"]["target_audience"] = enhanced_json.get("audience", {}).get("primary", "Unknown")
                config["brand_info"]["brand_positioning"] = enhanced_json.get("positioning", {}).get("uvp", "Unknown")
            
            # Update document processor paths
            config["document_processor"]["input_folder"] = f"inputs/{brand_name}/brand_docs"
            config["document_processor"]["output_json"] = f"inputs/{brand_name}/{brand_name.lower()}_enhanced.json"
            config["document_processor"]["raw_analyses"] = f"inputs/{brand_name}/{brand_name.lower()}_raw_analyses.json"
            
            # Update orchestrator paths
            config["orchestrator"]["input_json"] = f"inputs/{brand_name}/{brand_name.lower()}_enhanced.json"
            
            # Update Figma plugin display
            config["figma_plugin"]["brand_display_name"] = f"{brand_name} (inputs/{brand_name}/)"
            config["figma_plugin"]["brand_value"] = brand_name.lower()
            
            # Save the config file
            config_path = f"inputs/{brand_name}/brand_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating brand config: {str(e)}")
            return False

def main():
    """Main function to process documents and generate brand strategy"""
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in a .env file")
        return
    
    # Get brand name from command line arguments
    import sys
    if len(sys.argv) > 1:
        brand_name = sys.argv[1]
    else:
        brand_name = "Metra"  # Default fallback
    
    processor = DocumentProcessor()
    
    # Brand configuration
    brand_folder = f"inputs/{brand_name}"
    brand_docs_path = f"{brand_folder}/brand_docs"
    
    # Check if brand folder and docs exist
    if not os.path.exists(brand_folder):
        print(f"❌ Brand folder not found: {brand_folder}")
        print(f"Please create the folder structure: inputs/{brand_name}/brand_docs/")
        return
    
    if not os.path.exists(brand_docs_path):
        print(f"❌ Brand documents folder not found: {brand_docs_path}")
        print(f"Please add your brand documents to: inputs/{brand_name}/brand_docs/")
        return
    
    # Process brand documents
    print(f"🔄 Processing {brand_name} brand documents...")
    document_analyses = processor.process_documents(brand_docs_path, brand_name)
    
    if not document_analyses:
        print("❌ No documents processed successfully")
        return
    
    print(f"✅ Processed {len(document_analyses)} documents")
    
    # Synthesize all analyses into unified brand strategy
    print("🤖 Synthesizing brand strategy from all documents...")
    brand_strategy = processor.synthesize_brand_strategy(document_analyses, brand_name)
    
    if not brand_strategy:
        print("❌ Failed to synthesize brand strategy")
        return
    
    print("✅ Brand strategy synthesized successfully")
    
    # Create enhanced input JSON
    print("📝 Creating enhanced input JSON...")
    enhanced_json = processor.create_enhanced_input_json(brand_strategy, brand_name)
    
    # Save the enhanced JSON
    output_path = f"{brand_folder}/{brand_name.lower()}_enhanced.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Enhanced input JSON saved to {output_path}")
    print(f"📊 Generated {len(enhanced_json)} top-level sections")
    
    # Show key information
    print("\n🎯 Key Brand Information:")
    print(f"   Brand: {enhanced_json['brand']['name']}")
    print(f"   Tagline: {enhanced_json['brand']['tagline']}")
    print(f"   Audience: {enhanced_json['audience']['primary']}")
    print(f"   UVP: {enhanced_json['positioning']['uvp']}")
    print(f"   Visual Style: {enhanced_json['visual']['design_style']}")
    
    # Save raw analyses for debugging
    debug_path = f"{brand_folder}/{brand_name.lower()}_raw_analyses.json"
    with open(debug_path, 'w', encoding='utf-8') as f:
        json.dump(document_analyses, f, indent=2, ensure_ascii=False)
    print(f"🔍 Raw analyses saved to {debug_path} for debugging")
    
    # Create brand config file
    print("⚙️ Creating brand configuration file...")
    config_created = processor.create_brand_config(brand_name, enhanced_json)
    if config_created:
        print(f"✅ Brand config file created: {brand_folder}/brand_config.json")
    else:
        print(f"⚠️ Failed to create brand config file")

if __name__ == "__main__":
    main()

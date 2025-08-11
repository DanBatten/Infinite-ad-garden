from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Ingredient:
    name: str
    dose_mg: int
    evidence_level: str

@dataclass
class Strategy:
    audience: str
    pain_points: List[str]
    desired_outcomes: List[str]
    angle: str
    channels: List[str]
    format: str

@dataclass
class Brand:
    name: str
    tone: str
    palette: List[str]
    type: Dict[str, str]
    do_nots: List[str]
    logo_url: str
    image_style: str

@dataclass
class Formulation:
    product_name: str
    key_ingredients: List[Ingredient]
    banned_claims: List[str]

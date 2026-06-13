#!/usr/bin/env python3
"""
translation.py — Vocabulary Wall Translation Skill
===================================================

Tank upload: "I know the vocabulary wall."

Detects and translates queries that hit the vocabulary wall — when a model
can compute the answer but doesn't understand the domain terminology.

The fleet translator routes through three strategies:
1. Direct computation (Stage 4: Seed-mini)
2. Scaffolding with activation keys (Stage 2-3)
3. Full translation with domain context
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class VocabularyWallHit:
    """Detected vocabulary wall collision."""
    original_query: str
    blocked_terms: List[str]
    domain: str
    confidence: float
    suggested_translation: str
    tier: int  # 1=direct, 2=scaffolded, 3=incompetent


# Known vocabulary wall patterns
WALL_PATTERNS = {
    "eisenstein": {
        "terms": ["eisenstein", "eisenstein integer", "norm form", "ω", "omega", "algebraic integer"],
        "domain": "math",
        "translation_template": "Compute a² − ab + b² for a={a}, b={b}",
        "activation_key": "Eisenstein norm",
    },
    "mobius": {
        "terms": ["möbius", "mobius", "μ(n)", "moebius"],
        "domain": "math",
        "translation_template": "For n={n}, count prime factors. If squared factor exists → 0, if k distinct primes → (−1)^k",
        "activation_key": "Möbius function",
    },
    "conservation": {
        "terms": ["conservation law", "γ+H", "gamma plus H", "coupling entropy"],
        "domain": "fleet-health",
        "translation_template": "Verify that total_weight({weights}) + entropy({weights}) ≈ C − α·ln({volume})",
        "activation_key": "Conservation law",
    },
    "hebbian": {
        "terms": ["hebbian", "co-activation", "coupling strength"],
        "domain": "fleet-health",
        "translation_template": "Update weight w_ij += η · (x_i · x_j − λ · w_ij) for rooms {rooms}",
        "activation_key": "Hebbian dynamics",
    },
}


def detect_vocabulary_wall(query: str) -> Optional[VocabularyWallHit]:
    """
    Detect if a query will hit the vocabulary wall.

    Returns a VocabularyWallHit if wall terms are detected, None otherwise.
    """
    query_lower = query.lower()

    for pattern_name, pattern in WALL_PATTERNS.items():
        matched_terms = [t for t in pattern["terms"] if t.lower() in query_lower]
        if matched_terms:
            # Determine tier based on term count
            if len(matched_terms) >= 2:
                tier = 1  # Direct — enough context to compute
            elif len(matched_terms) == 1:
                tier = 2  # Needs scaffolding
            else:
                tier = 3

            return VocabularyWallHit(
                original_query=query,
                blocked_terms=matched_terms,
                domain=pattern["domain"],
                confidence=min(1.0, len(matched_terms) * 0.4),
                suggested_translation=pattern["translation_template"],
                tier=tier,
            )

    return None


def translate_query(query: str, target_tier: int = 1) -> str:
    """
    Translate a query to avoid vocabulary wall collisions.

    Args:
        query: Original query
        target_tier: 1=direct computation, 2=scaffolded, 3=full context

    Returns:
        Translated query
    """
    hit = detect_vocabulary_wall(query)
    if not hit:
        return query  # No wall detected, pass through

    if target_tier == 1:
        # Direct: extract numbers and compute
        return hit.suggested_translation
    elif target_tier == 2:
        # Scaffolding: add activation key
        key = _get_activation_key(hit.domain)
        return f"Using {key}: {query}"
    else:
        # Full context: explain domain then ask
        return f"In the domain of {hit.domain}: {query} (Note: {hit.suggested_translation})"


def route_tier(query: str) -> int:
    """
    Determine which tier a query should be routed to.

    Returns:
        1 = Direct computation (Seed-mini)
        2 = Scaffolded (Qwen3, DeepSeek)
        3 = Full context needed
    """
    hit = detect_vocabulary_wall(query)
    if not hit:
        return 1  # No wall, direct is fine
    return hit.tier


def _get_activation_key(domain: str) -> str:
    """Get activation key for a domain."""
    for pattern in WALL_PATTERNS.values():
        if pattern["domain"] == domain:
            return pattern["activation_key"]
    return domain


def add_wall_pattern(name: str, terms: List[str], domain: str,
                     translation_template: str, activation_key: str) -> None:
    """Register a new vocabulary wall pattern."""
    WALL_PATTERNS[name] = {
        "terms": terms,
        "domain": domain,
        "translation_template": translation_template,
        "activation_key": activation_key,
    }

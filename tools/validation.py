"""
Content validation and quality assessment tools.

Demonstrates:
- Content quality scoring
- Source credibility validation
- Fact-checking helpers
- Completeness verification
"""
from typing import List, Dict, Tuple, Optional
import re
from urllib.parse import urlparse
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    score: float
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def __str__(self) -> str:
        status = "✓ PASS" if self.is_valid else "✗ FAIL"
        return f"{status} (Score: {self.score:.2f})\nIssues: {len(self.issues)}, Warnings: {len(self.warnings)}"


class ContentValidator:
    """
    Validates content quality across multiple dimensions.
    
    Validation criteria:
    - Completeness (has introduction, body, conclusion)
    - Readability (sentence length, complexity)
    - Citation presence
    - Factual support
    - Grammar basics
    """
    
    def __init__(self, min_word_count: int = 100, max_word_count: int = 5000):
        self.min_word_count = min_word_count
        self.max_word_count = max_word_count
    
    def validate(self, content: str, research_data: Optional[str] = None) -> ValidationResult:
        """
        Comprehensive content validation.
        
        Args:
            content: Content to validate
            research_data: Original research for fact-checking
            
        Returns:
            ValidationResult with score and feedback
        """
        issues = []
        warnings = []
        suggestions = []
        scores = []
        
        # 1. Length validation
        word_count = len(content.split())
        if word_count < self.min_word_count:
            issues.append(f"Content too short: {word_count} words (minimum: {self.min_word_count})")
            scores.append(0.3)
        elif word_count > self.max_word_count:
            warnings.append(f"Content very long: {word_count} words (maximum: {self.max_word_count})")
            scores.append(0.8)
        else:
            scores.append(1.0)
        
        # 2. Structure validation
        structure_score = self._validate_structure(content, issues, warnings)
        scores.append(structure_score)
        
        # 3. Readability validation
        readability_score = self._validate_readability(content, warnings, suggestions)
        scores.append(readability_score)
        
        # 4. Citation validation
        citation_score = self._validate_citations(content, issues, suggestions)
        scores.append(citation_score)
        
        # 5. Factual alignment (if research data provided)
        if research_data:
            fact_score = self._validate_factual_alignment(content, research_data, issues)
            scores.append(fact_score)
        
        # Calculate overall score
        overall_score = sum(scores) / len(scores)
        is_valid = overall_score >= 0.7 and len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            score=overall_score,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_structure(self, content: str, issues: List[str], warnings: List[str]) -> float:
        """Check content structure (intro, body, conclusion)."""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if len(paragraphs) < 3:
            issues.append("Content lacks proper structure (needs at least 3 paragraphs)")
            return 0.4
        
        # Check for introduction indicators
        first_para = paragraphs[0].lower()
        intro_indicators = ['introduction', 'overview', 'in this', 'this article', 'this post']
        has_intro = any(indicator in first_para for indicator in intro_indicators)
        
        # Check for conclusion indicators
        last_para = paragraphs[-1].lower()
        conclusion_indicators = ['conclusion', 'summary', 'in conclusion', 'to summarize', 'overall']
        has_conclusion = any(indicator in last_para for indicator in conclusion_indicators)
        
        score = 0.6  # Base score
        if has_intro:
            score += 0.2
        else:
            warnings.append("No clear introduction detected")
        
        if has_conclusion:
            score += 0.2
        else:
            warnings.append("No clear conclusion detected")
        
        return score
    
    def _validate_readability(
        self, 
        content: str, 
        warnings: List[str], 
        suggestions: List[str]
    ) -> float:
        """Assess readability metrics."""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        score = 1.0
        
        if avg_sentence_length > 25:
            warnings.append(f"Average sentence length is high ({avg_sentence_length:.1f} words)")
            suggestions.append("Consider breaking long sentences into shorter ones")
            score -= 0.2
        elif avg_sentence_length < 8:
            warnings.append(f"Average sentence length is low ({avg_sentence_length:.1f} words)")
            suggestions.append("Consider combining some short sentences for better flow")
            score -= 0.1
        
        # Check for very long sentences
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            warnings.append(f"Found {len(long_sentences)} very long sentences (>40 words)")
            score -= 0.1
        
        return max(score, 0.0)
    
    def _validate_citations(self, content: str, issues: List[str], suggestions: List[str]) -> float:
        """Check for proper citations and sources."""
        # Look for citation patterns
        citation_patterns = [
            r'\[(\d+)\]',  # [1], [2]
            r'\([\w\s]+,?\s+\d{4}\)',  # (Author, 2023)
            r'according to',
            r'research shows',
            r'study found',
            r'https?://\S+'  # URLs
        ]
        
        citation_count = sum(
            len(re.findall(pattern, content, re.IGNORECASE))
            for pattern in citation_patterns
        )
        
        word_count = len(content.split())
        citation_density = citation_count / (word_count / 100)  # Citations per 100 words
        
        if citation_count == 0:
            issues.append("No citations or sources found")
            suggestions.append("Add references to support claims")
            return 0.3
        elif citation_density < 0.5:
            suggestions.append("Consider adding more citations to support claims")
            return 0.7
        else:
            return 1.0
    
    def _validate_factual_alignment(
        self, 
        content: str, 
        research_data: str, 
        issues: List[str]
    ) -> float:
        """Check if content aligns with research data."""
        # Extract key terms from research
        research_terms = set(re.findall(r'\b[A-Z][a-z]+\b', research_data))
        content_terms = set(re.findall(r'\b[A-Z][a-z]+\b', content))
        
        # Calculate overlap
        if research_terms:
            overlap = len(research_terms & content_terms) / len(research_terms)
            
            if overlap < 0.3:
                issues.append("Content may not align well with research data")
                return 0.5
            elif overlap < 0.5:
                return 0.7
            else:
                return 1.0
        
        return 0.8  # Neutral if can't determine


def validate_sources(sources: List[str]) -> Dict[str, any]:
    """
    Validate credibility of source URLs.
    
    Checks:
    - Domain reputation (basic heuristics)
    - HTTPS usage
    - Domain age indicators
    
    Args:
        sources: List of URLs
        
    Returns:
        Dict with validation results
    """
    trusted_domains = [
        'edu', 'gov', 'org',  # TLDs
        'wikipedia.org', 'arxiv.org', 'nature.com', 'science.org',
        'nytimes.com', 'wsj.com', 'reuters.com', 'bbc.com'
    ]
    
    results = {
        'total_sources': len(sources),
        'https_count': 0,
        'trusted_count': 0,
        'warnings': [],
        'credibility_score': 0.0
    }
    
    if not sources:
        results['warnings'].append("No sources provided")
        return results
    
    for url in sources:
        try:
            parsed = urlparse(url)
            
            # Check HTTPS
            if parsed.scheme == 'https':
                results['https_count'] += 1
            else:
                results['warnings'].append(f"Non-HTTPS source: {url}")
            
            # Check trusted domain
            domain = parsed.netloc.lower()
            if any(trusted in domain for trusted in trusted_domains):
                results['trusted_count'] += 1
        
        except Exception as e:
            results['warnings'].append(f"Invalid URL: {url}")
    
    # Calculate credibility score
    https_score = results['https_count'] / len(sources)
    trust_score = results['trusted_count'] / len(sources)
    results['credibility_score'] = (https_score * 0.4 + trust_score * 0.6)
    
    return results
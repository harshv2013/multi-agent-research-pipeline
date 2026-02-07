"""
Data extraction and processing tools for agents.

Demonstrates:
- Text analysis and key point extraction
- Information structuring
- Summary generation
- Entity recognition (basic)
"""
from typing import List, Dict, Optional, Tuple
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class KeyPoint:
    """Represents an extracted key point."""
    text: str
    category: str
    importance: float
    source: Optional[str] = None
    
    def __str__(self) -> str:
        return f"[{self.category}] {self.text} (importance: {self.importance:.2f})"


class DataExtractor:
    """
    Extracts structured information from unstructured text.
    
    Capabilities:
    - Key point extraction
    - Topic identification
    - Entity extraction (simple pattern-based)
    - Statistics extraction
    - Quote extraction
    """
    
    def __init__(self):
        self.stat_patterns = [
            r'\d+%',  # Percentages
            r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
            r'\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|thousand|k|m|b))?',  # Numbers
        ]
        
        self.quote_pattern = r'["""]([^"""]+)["""]'
    
    def extract_key_points(
        self, 
        text: str, 
        max_points: int = 10,
        min_sentence_length: int = 20
    ) -> List[KeyPoint]:
        """
        Extract key points from text based on heuristics.
        
        Heuristics:
        - Contains statistics or numbers
        - Longer sentences (more informative)
        - Contains important keywords
        - Position in text (first/last sentences often key)
        
        Args:
            text: Input text
            max_points: Maximum number of key points
            min_sentence_length: Minimum length for consideration
            
        Returns:
            List of KeyPoint objects
        """
        sentences = self._split_into_sentences(text)
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            if len(sentence) < min_sentence_length:
                continue
            
            score = self._score_sentence(sentence, i, len(sentences))
            category = self._categorize_sentence(sentence)
            
            key_point = KeyPoint(
                text=sentence,
                category=category,
                importance=score
            )
            scored_sentences.append(key_point)
        
        # Sort by importance and return top N
        scored_sentences.sort(key=lambda x: x.importance, reverse=True)
        return scored_sentences[:max_points]
    
    def extract_statistics(self, text: str) -> List[Dict[str, str]]:
        """
        Extract numerical statistics from text.
        
        Returns:
            List of dicts with 'value' and 'context'
        """
        statistics = []
        
        for pattern in self.stat_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                stat_value = match.group(0)
                
                # Get surrounding context (30 chars before and after)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                statistics.append({
                    'value': stat_value,
                    'context': context
                })
        
        return statistics
    
    def extract_quotes(self, text: str) -> List[str]:
        """Extract quoted text."""
        quotes = re.findall(self.quote_pattern, text)
        return [q.strip() for q in quotes if len(q.strip()) > 10]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Simple entity extraction using pattern matching.
        
        In production, use spaCy or other NER libraries.
        
        Returns:
            Dict with entity types as keys and lists of entities as values
        """
        entities = {
            'organizations': [],
            'locations': [],
            'dates': [],
            'emails': [],
            'urls': []
        }
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Extract dates (simple patterns)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'  # Month DD, YYYY
        ]
        for pattern in date_patterns:
            entities['dates'].extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Capitalized words (potential organizations/locations)
        # This is very basic; use NER in production
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities['organizations'] = list(set(capitalized))[:10]  # Limit to 10
        
        return entities
    
    def generate_summary(self, text: str, num_sentences: int = 3) -> str:
        """
        Generate extractive summary by selecting most important sentences.
        
        Args:
            text: Input text
            num_sentences: Number of sentences in summary
            
        Returns:
            Summary string
        """
        key_points = self.extract_key_points(text, max_points=num_sentences)
        
        # Get original order of sentences
        sentences_dict = {kp.text: kp for kp in key_points}
        all_sentences = self._split_into_sentences(text)
        
        summary_sentences = [s for s in all_sentences if s in sentences_dict]
        
        return " ".join(summary_sentences[:num_sentences])
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (improve with nltk/spaCy in production)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _score_sentence(self, sentence: str, position: int, total: int) -> float:
        """
        Score sentence importance based on heuristics.
        
        Scoring factors:
        - Contains statistics: +0.3
        - Contains quotes: +0.2
        - Length (sweet spot 50-150 chars): up to +0.2
        - Position (first 3 or last 3): +0.2
        - Contains keywords: +0.1 per keyword
        """
        score = 0.0
        
        # Statistical content
        has_stats = any(re.search(pattern, sentence) for pattern in self.stat_patterns)
        if has_stats:
            score += 0.3
        
        # Contains quotes
        if re.search(self.quote_pattern, sentence):
            score += 0.2
        
        # Length score (prefer medium-length sentences)
        length = len(sentence)
        if 50 <= length <= 150:
            score += 0.2
        elif 150 < length <= 200:
            score += 0.1
        
        # Position score (beginning and end are important)
        if position < 3 or position >= total - 3:
            score += 0.2
        
        # Keyword presence
        keywords = [
            'important', 'significant', 'key', 'critical', 'essential',
            'shows', 'demonstrates', 'reveals', 'indicates', 'suggests',
            'according to', 'research', 'study', 'found', 'discovered'
        ]
        keyword_count = sum(1 for kw in keywords if kw.lower() in sentence.lower())
        score += min(keyword_count * 0.1, 0.3)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _categorize_sentence(self, sentence: str) -> str:
        """Categorize sentence by content type."""
        sentence_lower = sentence.lower()
        
        if any(re.search(pattern, sentence) for pattern in self.stat_patterns):
            return "statistic"
        elif re.search(self.quote_pattern, sentence):
            return "quote"
        elif any(word in sentence_lower for word in ['however', 'but', 'although', 'despite']):
            return "contrast"
        elif any(word in sentence_lower for word in ['therefore', 'thus', 'consequently', 'as a result']):
            return "conclusion"
        elif any(word in sentence_lower for word in ['first', 'second', 'third', 'finally']):
            return "enumeration"
        elif '?' in sentence:
            return "question"
        else:
            return "general"


# Convenience function for quick use
def extract_key_points(text: str, max_points: int = 10) -> List[KeyPoint]:
    """
    Quick extraction of key points from text.
    
    Args:
        text: Input text
        max_points: Maximum key points to extract
        
    Returns:
        List of KeyPoint objects
    """
    extractor = DataExtractor()
    return extractor.extract_key_points(text, max_points)
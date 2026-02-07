"""
Unit tests for tools functionality.
"""
import pytest
from tools.web_search import WebSearchTool, web_search_tool
from tools.data_extraction import DataExtractor, extract_key_points
from tools.validation import ContentValidator, validate_sources


class TestWebSearchTool:
    """Test web search tool."""
    
    def test_web_search_tool_initialization(self):
        """Test search tool initializes."""
        tool = WebSearchTool()
        assert tool is not None
        assert tool.cache is not None
    
    def test_mock_search(self):
        """Test mock search returns results."""
        results = web_search_tool("test query", num_results=3)
        assert isinstance(results, str)
        assert "Result 1" in results
        assert "Result 2" in results
        assert "Result 3" in results


class TestDataExtractor:
    """Test data extraction tool."""
    
    def test_extractor_initialization(self):
        """Test extractor initializes."""
        extractor = DataExtractor()
        assert extractor is not None
    
    def test_extract_key_points(self):
        """Test key point extraction."""
        text = """
        This is a test document. It has multiple sentences.
        Some sentences contain important information with 50% statistics.
        Other sentences provide additional context and details.
        The conclusion summarizes the main findings.
        """
        
        key_points = extract_key_points(text, max_points=5)
        assert isinstance(key_points, list)
        assert len(key_points) <= 5
    
    def test_extract_statistics(self):
        """Test statistics extraction."""
        extractor = DataExtractor()
        text = "The study found 75% improvement and $1,000,000 in savings."
        
        stats = extractor.extract_statistics(text)
        assert len(stats) > 0
        assert any('75%' in s['value'] for s in stats)
    
    def test_extract_quotes(self):
        """Test quote extraction."""
        extractor = DataExtractor()
        text = 'He said "this is a quote" and she replied "another quote here".'
        
        quotes = extractor.extract_quotes(text)
        assert len(quotes) == 2
        assert "this is a quote" in quotes[0]


class TestContentValidator:
    """Test content validator."""
    
    def test_validator_initialization(self):
        """Test validator initializes."""
        validator = ContentValidator()
        assert validator is not None
    
    def test_validate_short_content(self):
        """Test validation of short content."""
        validator = ContentValidator(min_word_count=100)
        result = validator.validate("Too short")
        
        assert result.is_valid is False
        assert len(result.issues) > 0
    
    def test_validate_good_content(self):
        """Test validation of good content."""
        validator = ContentValidator(min_word_count=50)
        content = """
        This is a well-structured article with an introduction.
        
        The body contains multiple paragraphs with good information.
        It includes citations [1] and references to sources.
        The content is clear and well-organized.
        
        In conclusion, this article demonstrates proper structure
        and includes all necessary elements for quality content.
        """
        
        result = validator.validate(content)
        assert result.score > 0.5


class TestSourceValidation:
    """Test source validation."""
    
    def test_validate_sources_https(self):
        """Test HTTPS source validation."""
        sources = [
            "https://example.edu/article",
            "http://example.com/article"
        ]
        
        result = validate_sources(sources)
        assert result['total_sources'] == 2
        assert result['https_count'] == 1
    
    def test_validate_trusted_domains(self):
        """Test trusted domain validation."""
        sources = [
            "https://stanford.edu/research",
            "https://nature.com/article",
            "https://random-blog.com/post"
        ]
        
        result = validate_sources(sources)
        assert result['trusted_count'] >= 2
        assert result['credibility_score'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
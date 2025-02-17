class ScrapingException(Exception):
    """Base exception for scraping errors"""
    pass

class ConfigGenerationError(ScrapingException):
    """Raised when config generation fails"""
    pass

class ContentExtractionError(ScrapingException):
    """Raised when content extraction fails"""
    pass
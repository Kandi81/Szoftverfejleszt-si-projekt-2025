"""
AI service factory for switching between providers
"""
from typing import Optional, Literal
from .gemini_service import GeminiService
from .perplexity_service import PerplexityService


AIProvider = Literal["gemini", "perplexity"]


class AIServiceFactory:
    """Factory for creating AI service instances"""
    
    @staticmethod
    def create(provider: AIProvider = "perplexity") -> Optional[object]:
        """Create AI service instance
        
        Args:
            provider: AI provider name ("gemini" or "perplexity")
            
        Returns:
            AI service instance or None if initialization fails
        """
        try:
            if provider == "gemini":
                return GeminiService()
            elif provider == "perplexity":
                return PerplexityService()
            else:
                raise ValueError(f"Unknown AI provider: {provider}")
        except Exception as e:
            print(f"[AI_FACTORY] Failed to initialize {provider}: {e}")
            return None
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available AI providers"""
        providers = []
        
        # Check Gemini
        try:
            GeminiService()
            providers.append("gemini")
        except Exception:
            pass
        
        # Check Perplexity
        try:
            PerplexityService()
            providers.append("perplexity")
        except Exception:
            pass
        
        return providers

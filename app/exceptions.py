class ChatbotError(Exception):
    """Base Exception for the chatbot application"""

class ConversationNotFoundError(ChatbotError):
    """Raised when a conversation does not exist."""

class NoActiveConversationError(ChatbotError):
    """Raised when an operation requires an active conversation"""

class InvalidMessageError(ChatbotError):
    """Raised when a message is invalid"""

class LLMServiceError(ChatbotError):
    """Raised when then LLM provided fails"""

class ConfigureError(ChatbotError):
    """Raised when application configuration is invalid"""
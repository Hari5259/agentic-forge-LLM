"""
Ollama Configuration Module
Handles local LLM setup using Ollama with LangChain integration.
No external API keys required - runs completely locally.
"""

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler


# Default model configuration
DEFAULT_MODEL = "llama3"
OLLAMA_BASE_URL = "http://localhost:11434"


def get_llm(model: str = DEFAULT_MODEL, temperature: float = 0.7, streaming: bool = False):
    """
    Initialize and return an Ollama LLM instance.
    
    Args:
        model: The Ollama model to use (default: llama3)
        temperature: Creativity level (0.0-1.0)
        streaming: Enable streaming output
    
    Returns:
        Configured Ollama LLM instance
    """
    kwargs = {
        "model": model,
        "base_url": OLLAMA_BASE_URL,
        "temperature": temperature,
    }
    if streaming:
        kwargs["callbacks"] = [StreamingStdOutCallbackHandler()]
    
    return Ollama(**kwargs)


def get_embeddings(model: str = None):
    """
    Initialize and return Ollama embeddings for vector operations.
    
    Args:
        model: The Ollama model to use for embeddings
    
    Returns:
        Configured OllamaEmbeddings instance
    """
    if model is None:
        # Detect if we have an embedding-specific model
        available = list_available_models()
        embed_models = [m for m in available if "embed" in m]
        if embed_models:
            model = embed_models[0]
        else:
            # Fallback to nomic-embed-text or DEFAULT_MODEL
            model = "nomic-embed-text" if "nomic-embed-text" in available else DEFAULT_MODEL
            
    return OllamaEmbeddings(
        model=model,
        base_url=OLLAMA_BASE_URL,
    )


def check_ollama_connection():
    """
    Verify Ollama is running and accessible.
    
    Returns:
        tuple: (bool, str) - Success status and message
    """
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            return True, f"Ollama connected. Available models: {model_names}"
        return False, "Ollama responded but with unexpected status"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Ollama. Make sure it's running on localhost:11434"
    except Exception as e:
        return False, f"Error checking Ollama: {str(e)}"


def list_available_models():
    """
    List all models available in the local Ollama installation.
    
    Returns:
        list: Available model names
    """
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m.get("name", "").split(":")[0] for m in models]
        return []
    except:
        return []

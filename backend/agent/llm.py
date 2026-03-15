import os
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
from config import settings

def _groq_key():
    """Get Groq API key from settings."""
    return settings.GROQ_API_KEY

def _gemini_key():
    """Get Gemini API key from settings."""
    return settings.GEMINI_API_KEY

def _deepseek_key():
    """Get DeepSeek API key from settings."""
    return settings.DEEPSEEK_API_KEY

def get_primary_llm(temperature: float = 0):
    """Qwen3-32B via Groq: strong structured output + tool calling."""
    return ChatGroq(
        model="qwen/qwen3-32b",
        temperature=temperature,
        reasoning_effort="none",
        api_key=_groq_key(),
    )

def get_vision_llm():
    """Gemini 2.5 Flash-Lite for resume parsing/tailoring - strong doc understanding, generous free tier"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.2,
        google_api_key=_gemini_key(),
    )

def get_deepseek_llm(temperature: float = 0.1):
    """DeepSeek V3 - 5M free tokens/month, excellent at following constraints, great for resume tailoring."""
    return OpenAI(
        api_key=_deepseek_key(),
        base_url="https://api.deepseek.com"
    )

# Main LLM for search queries, routing, etc.
def get_main_llm():
    return get_primary_llm(temperature=0.1)

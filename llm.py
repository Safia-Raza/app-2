import os
from crewai import LLM

MODEL_NAME = "openai/gpt-oss-120b"


def get_llm() -> LLM:
    """Create the shared Groq-backed CrewAI LLM."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to Streamlit Secrets."
        )

    # CrewAI routes groq/* models through LiteLLM. The actual model is hosted by Groq.
    return LLM(
        model=f"groq/{MODEL_NAME}",
        api_key=api_key,
        temperature=0.1,
        max_tokens=5000,
    )

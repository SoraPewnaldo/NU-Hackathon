import os
from groq import Groq
from flask import current_app

def call_llm(messages):
    """
    messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
    """
    api_key = current_app.config.get("LLM_API_KEY") or os.getenv("LLM_API_KEY")
    model   = current_app.config.get("LLM_MODEL") or os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        return f'{{"reply_text": "LLM API key missing.", "suggestions": []}}'

    client = Groq(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        return completion.choices[0].message.content
    except Exception as e:
        # Return JSON error so parsing doesn't die
        return f'{{"reply_text": "Groq error: {str(e)}", "suggestions": []}}'
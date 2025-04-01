import openai
from app.config import settings

# Thiết lập API key từ biến môi trường
openai.api_key = settings.KEY_API_GPT

def get_gpt_response(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 100):
    try:
        # Gửi yêu cầu tới OpenAI GPT API
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return str(e)

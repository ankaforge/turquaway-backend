import json
import os
import sys
from pathlib import Path

import environ
from google import genai
from google.genai import types


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    env = environ.Env()
    environ.Env.read_env(base_dir / '.env')

    api_key = env('GEMINI_API_KEY', default=os.getenv('GEMINI_API_KEY'))
    if not api_key:
        print('FAIL: GEMINI_API_KEY is missing.')
        return 1

    if api_key.strip().lower() in {'your-gemini-api-key', 'changeme', 'test'}:
        print('FAIL: GEMINI_API_KEY appears to be a placeholder value.')
        return 1

    try:
        client = genai.Client(api_key=api_key)
        model_name = env('GEMINI_MODEL', default=os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'))
        response = client.models.generate_content(
            model=model_name,
            contents='Return only valid JSON object with key "ping" and value "pong".',
            config=types.GenerateContentConfig(response_mime_type='application/json'),
        )
        payload = json.loads((response.text or '').strip())
        print(f'SUCCESS: Gemini API key is working with model: {model_name}.')
        print(f'Response preview: {payload}')
        return 0
    except Exception as exc:
        print(f'FAIL: Gemini request failed: {exc.__class__.__name__}: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
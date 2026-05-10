# Computing Helpbot
An attempt to let my friends have some way to finally practice their Computing skills!

Powered by an OpenAI-compatible chat completions endpoint.


## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run main.py
```

## Secrets

For local development, either create a file called `confidential.py` from `confidential.example.py`, or create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example`.

Both files use the same keys:

```python
OPENAI_API_KEY = "your-api-key"

# Optional. Defaults to https://api.openai.com/v1/chat/completions.
OPENAPI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Optional. Defaults to gpt-4o-mini.
OPENAI_MODEL = "gpt-4o-mini"
```

On Streamlit Cloud, add those same keys in the app's Secrets settings. Do not upload `confidential.py` or `.streamlit/secrets.toml`.

If you are using another OpenAI-compatible provider, set `OPENAPI_ENDPOINT` to that provider's `/chat/completions` endpoint and set `OPENAI_MODEL` to a model available there. `OPENAI_ENDPOINT` is also supported as an alias.

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIG ---
N8N_API_URL = os.getenv("N8N_API_URL", "https://n8n.sitepreviews.dev/api/v1")
N8N_API_KEY = os.getenv("N8N_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNTk3OTkxYy01MTkzLTRlMmUtYTYzZS05MDJlN2Q5NGNkNzUiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU0Mzg1MjA2fQ.C08dpFtkQs1RlnngZuGAq3qxM-Yv1Hq38dJfJcRuU9M")

# --- LLM API Keys ---
# OpenRouter (commented out - credits finished)
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

# Gemini API (primary)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBXsJyhZhrP2wKpV8kS3r_pSrsUgK2jpyU")  # Enter your Gemini API key here

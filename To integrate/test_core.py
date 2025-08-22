#!/usr/bin/env python3
"""
Test script to verify core chatbot functionality without Streamlit.
This helps isolate whether the issue is with Streamlit or the core dependencies.
"""

try:
    import requests
    print("✅ requests imported successfully")
except ImportError as e:
    print(f"❌ requests import failed: {e}")

try:
    import openai
    print("✅ openai imported successfully")
except ImportError as e:
    print(f"❌ openai import failed: {e}")

try:
    import json
    print("✅ json imported successfully")
except ImportError as e:
    print(f"❌ json import failed: {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported successfully")
except ImportError as e:
    print(f"❌ python-dotenv import failed: {e}")

try:
    from config import N8N_API_URL, N8N_API_KEY, GEMINI_API_KEY
    print("✅ config imported successfully")
    print(f"   N8N_API_URL: {N8N_API_URL}")
    print(f"   N8N_API_KEY: {N8N_API_KEY[:20]}...")
    print(f"   GEMINI_API_KEY: {GEMINI_API_KEY[:20] if GEMINI_API_KEY else 'Not set'}...")
except ImportError as e:
    print(f"❌ config import failed: {e}")

try:
    import google.generativeai as genai
    print("✅ google-generativeai imported successfully")
except ImportError as e:
    print(f"❌ google-generativeai import failed: {e}")

print("\n" + "="*50)
print("Core dependency test completed!")
print("="*50)

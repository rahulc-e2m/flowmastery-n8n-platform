#!/usr/bin/env python3
"""
Simple command-line interface for the n8n chatbot.
Useful for testing the core functionality without the Streamlit UI.
"""

from n8n_chatbot import answer_user

def main():
    print("🤖 n8n Chatbot - Command Line Interface")
    print("=" * 50)
    print("Type 'quit' or 'exit' to stop the chatbot")
    print("=" * 50)
    
    while True:
        try:
            user_query = input("\n💬 Ask something about your n8n instance: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not user_query:
                print("❌ Please enter a question.")
                continue
            
            print("\n🤖 Processing...")
            answer = answer_user(user_query)
            print(f"\n📝 Answer:\n{answer}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()

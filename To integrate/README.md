# 🤖 n8n Chatbot with Streamlit UI

A modern chatbot interface for interacting with your n8n instance using natural language. This application allows you to query workflows, filter by status, and get workflow details through a beautiful Streamlit web interface.

## ✨ Features

- **Natural Language Processing**: Ask questions about your n8n workflows in plain English
- **Modern UI**: Beautiful Streamlit interface with gradient styling and smooth animations
- **Real-time Chat**: Interactive chat interface with message history
- **Example Queries**: Pre-built example queries for quick testing
- **Workflow Management**: Query, filter, and manage your n8n workflows
- **API Integration**: Seamless integration with n8n REST API and OpenAI GPT-3.5 Turbo

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- n8n instance with API access
- OpenAI API key (via OpenRouter)

### Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**:
   
   Create a `.env` file in the project root with your API keys:
   ```env
   N8N_API_URL=https://your-n8n-instance.com/api/v1
   N8N_API_KEY=your_n8n_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```
   
   Or modify the `config.py` file directly with your keys.

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** and navigate to `http://localhost:8501`

## 📝 Usage Examples

### Example Queries

- "Show me all workflows"
- "List only active workflows"
- "Show me inactive workflows"
- "Get workflow details for ID 123"
- "How many workflows do I have?"
- "Show me the first 5 workflows"

### How It Works

1. **User Input**: Type your question in natural language
2. **LLM Processing**: The system uses GPT-3.5 Turbo to understand your intent
3. **API Translation**: Converts your question to the appropriate n8n API call
4. **Data Retrieval**: Fetches data from your n8n instance
5. **Response Generation**: Formats the response in a user-friendly way

## 🏗️ Project Structure

```
n8n-chatbot/
├── app.py              # Main Streamlit application
├── n8n_chatbot.py      # Core chatbot logic
├── config.py           # Configuration and API keys
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔧 Configuration

### Environment Variables

- `N8N_API_URL`: Your n8n instance API URL
- `N8N_API_KEY`: Your n8n API key
- `OPENROUTER_API_KEY`: Your OpenRouter API key

### Customization

You can customize the application by modifying:

- **Styling**: Edit the CSS in `app.py`
- **Example Queries**: Modify the `example_queries` list in `app.py`
- **API Behavior**: Adjust the LLM prompts in `n8n_chatbot.py`

## 🛠️ Development

### Running in Development Mode

```bash
# Install in development mode
pip install -r requirements.txt

# Run with auto-reload
streamlit run app.py --server.runOnSave true
```

### Debugging

The application includes detailed logging. Check the console output for:
- API request details
- LLM response parsing
- Error messages

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Consider using a `.env` file (not included in this repo)
- Regularly rotate your API keys

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are correctly set in `config.py` or `.env`
2. **Connection Issues**: Verify your n8n instance is accessible
3. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify your API keys and URLs
3. Ensure your n8n instance is running and accessible

## 🎯 Roadmap

- [ ] Add workflow execution capabilities
- [ ] Support for more n8n API endpoints
- [ ] Export functionality for workflow data
- [ ] User authentication
- [ ] Multi-language support

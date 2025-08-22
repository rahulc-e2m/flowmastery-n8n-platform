# 🚀 FlowMastery + n8n Chatbot Integration Guide

This guide explains how to set up and use the integrated n8n chatbot system within the FlowMastery React application.

## 🎯 Overview

The integration combines:
- **React Frontend**: Modern chatbot UI with enhanced n8n metrics dashboard
- **Python Backend**: FastAPI server with comprehensive n8n integration
- **n8n Integration**: Natural language processing + real-time metrics monitoring
- **Dual Mode Support**: Traditional webhooks + intelligent n8n API queries
- **Metrics Dashboard**: Live n8n instance analytics with user-provided API keys
- **Secure Configuration**: Encrypted API key storage with connection testing

## 📋 Prerequisites

- Python 3.8+ installed
- Node.js 16+ installed  
- n8n instance (local or cloud)
- OpenAI/Gemini API key (optional, for enhanced AI features)

## 🛠️ Installation Steps

### Step 1: Set up Python Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the n8n integration files:
```bash
# Copy files from "To integrate" folder to backend directory
cp "../To integrate/n8n_chatbot.py" .
cp "../To integrate/config.py" .
```

4. Configure API credentials in `config.py`:
```python
# n8n Configuration
N8N_API_URL = "https://your-n8n-instance.com/api/v1"
N8N_API_KEY = "your_n8n_api_key"

# AI Configuration (optional)
GEMINI_API_KEY = "your_gemini_api_key"  # For enhanced AI responses
```

5. Start the backend server:
```bash
python app.py
```

The backend will start at `http://localhost:8000`

### Step 2: Set up React Frontend

1. Navigate to the main project directory:
```bash
cd ..
```

2. Install React dependencies (if not already installed):
```bash
npm install
```

3. Start the React development server:
```bash
npm start
```

The frontend will start at `http://localhost:3000`

## 🔧 Configuration

### n8n Setup

1. **Create n8n Workflow**: Set up workflows in your n8n instance
2. **Generate API Key**: Create an API key in your n8n settings
3. **Configure Webhooks**: Set up webhook endpoints for external integrations

### Environment Variables

Create a `.env` file in the backend directory:
```env
N8N_API_URL=https://your-n8n-instance.com/api/v1
N8N_API_KEY=your_n8n_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🎮 How to Use

### 1. Creating Chatbots

1. Click "New Chatbot" in the FlowMastery dashboard
2. Fill in chatbot details:
   - **Name**: Your chatbot's name
   - **Description**: What the chatbot does
   - **Type**: Support, Sales, FAQ, or Custom
   - **Webhook URL**: Your n8n webhook endpoint
3. Click "Create Chatbot"

### 2. Testing Chatbots

1. Click the play button on any chatbot card
2. Choose between popup or full-window chat mode
3. Send test messages to interact with your chatbot

### 3. Enhanced Features

#### Intelligent Routing
The system automatically:
- Tries the n8n API backend first for intelligent responses
- Falls back to direct webhook calls if the backend is unavailable
- Provides contextual fallback responses if both fail

#### Chat Controls
- **Quick Suggestions**: Pre-built prompts for easy testing
- **Export Chat**: Download conversation history as JSON
- **Sound Toggle**: Enable/disable notification sounds
- **Clear Chat**: Reset conversation with confirmation
- **Copy Messages**: Copy individual messages to clipboard

#### n8n Integration Features
- **Natural Language Queries**: Ask questions about workflows in plain English
- **Workflow Management**: List, filter, and control n8n workflows
- **Execution Monitoring**: Track workflow executions and status
- **Direct API Access**: Query n8n resources through natural language

## 🔍 API Endpoints

The backend provides these endpoints:

### Health Check
```
GET /health
```
Check backend and n8n connectivity status.

### Chat Message
```
POST /api/chat/message
{
  "message": "Show me all active workflows",
  "chatbot_id": "optional"
}
```
Send a message with intelligent routing.

### Direct n8n Query  
```
POST /api/n8n/query
{
  "query": "List all workflows",
  "include_raw_response": false
}
```
Direct n8n API query with natural language processing.

### n8n Workflows
```
GET /api/n8n/workflows?active=true&limit=100
```
Get n8n workflows with filtering options.

### n8n Executions
```
GET /api/n8n/executions?status=success&limit=50
```
Get workflow executions with filtering.

## 💡 Example Queries

You can ask the chatbots natural language questions like:

### Workflow Management
- "Show me all workflows"
- "List only active workflows"  
- "How many workflows do I have?"
- "Show me workflows created this week"

### Execution Monitoring
- "Show me recent executions"
- "List failed executions"
- "What executions are currently running?"

### User Management
- "List all users"
- "Show me admin users"
- "Who has access to project X?"

### General n8n Operations
- "Show me all variables"
- "List available tags"
- "What credentials are configured?"

## 🔄 Integration Architecture

```
React Frontend (localhost:3000)
    ↓
FastAPI Backend (localhost:8000)
    ↓
n8n Instance (your-domain.com)
    ↓
Gemini AI (optional, for enhanced responses)
```

### Message Flow

1. **User sends message** in React chat interface
2. **Frontend calls backend** at `/api/chat/message`
3. **Backend analyzes message** for n8n-related content
4. **Routes to appropriate handler**:
   - n8n API integration (for workflow/automation queries)
   - Direct webhook (for custom chatbot responses)
   - Fallback response (if both fail)
5. **Response sent back** to React interface

## 🛟 Troubleshooting

### Backend Won't Start
- Check Python version (3.8+ required)
- Install dependencies: `pip install -r requirements.txt`
- Verify n8n credentials in `config.py`

### n8n Connection Issues
- Check n8n instance URL and API key
- Ensure n8n API is enabled
- Test connectivity: `GET /health`

### Frontend Integration Issues  
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify React dev server is on port 3000

### Chat Not Responding
- Check backend logs for errors
- Verify webhook URLs are accessible
- Test with health endpoint first

## 🎨 Customization

### Adding New Chatbot Types
Edit the `typeColors` object in `ChatbotCategory.tsx`:
```typescript
const typeColors = {
  support: '#10b981',
  sales: '#f59e0b', 
  faq: '#6366f1',
  custom: '#8b5cf6',
  newType: '#your-color'
} as const;
```

### Custom Quick Suggestions
Update the `quickSuggestions` array:
```typescript
const quickSuggestions = [
  "Your custom suggestion",
  "Another helpful prompt",
  // ... more suggestions
];
```

### Styling Modifications
All styles are in `ChatbotCategory.css` - modify CSS variables and classes to match your design.

## 🚀 Deployment

### Production Backend
1. Use a production WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
```

2. Set up environment variables securely
3. Use HTTPS for n8n API communication

### Production Frontend
1. Build the React app:
```bash
npm run build
```

2. Serve with Nginx or your preferred web server
3. Update backend URL in production build

## 📝 License

This integration builds upon the existing FlowMastery project and n8n chatbot functionality. Please respect the licenses of all included components.

## 🤝 Support

For issues related to:
- **React Frontend**: Check FlowMastery documentation
- **n8n Integration**: Refer to n8n API documentation  
- **Backend API**: Review FastAPI logs and documentation
- **AI Features**: Check Gemini AI/OpenAI documentation

---

**🎉 Congratulations!** You now have a powerful, integrated chatbot system that combines the best of traditional webhook responses with intelligent n8n workflow management capabilities.

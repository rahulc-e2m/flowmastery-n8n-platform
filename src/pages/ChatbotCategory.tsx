// src/pages/ChatbotCategory.tsx
import React, { useState, useEffect } from 'react';
import './ChatbotCategory.css';
import { 
  FaRobot, 
  FaPlus, 
  FaCog, 
  FaChartLine, 
  FaComments,
  FaCode,
  FaPlay,
  FaPause,
  FaCheck,
  FaTimes,
  FaExternalLinkAlt,
  FaCopy,
  FaEdit,
  FaTrash,
  FaEye,
  FaSearch,
  FaFilter,
  FaBrain,
  FaGlobe,
  FaShieldAlt,
  FaClock,
  FaUsers,
  FaExpand,
  FaCompress,
  FaWindowMaximize,
  FaWindowMinimize,
  FaTrashAlt,
  FaDownload,
  FaPaperPlane,
  FaVolumeUp,
  FaVolumeMute,
  FaMicrophone,
  FaKeyboard,
  FaLightbulb,
  FaHistory
} from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';

// n8n Integration Service
interface N8nApiResponse {
  response: string;
  message_id: string;
  timestamp: string;
  processing_time: number;
  source: 'n8n_api' | 'webhook' | 'fallback' | 'error';
}

interface N8nWorkflow {
  id: string;
  name: string;
  active: boolean;
  createdAt?: string;
  updatedAt?: string;
}

interface N8nExecution {
  id: string;
  status: 'success' | 'error' | 'waiting';
  workflowId: string;
  startedAt: string;
  stoppedAt?: string;
}

class N8nApiService {
  private static baseUrl = 'http://localhost:8000';
  
  static async sendMessage(message: string, chatbotId?: string): Promise<N8nApiResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          chatbot_id: chatbotId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('N8n API Error:', error);
      throw error;
    }
  }
  
  static async queryN8n(query: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/n8n/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('N8n Direct Query Error:', error);
      throw error;
    }
  }
  
  static async getWorkflows(active?: boolean): Promise<N8nWorkflow[]> {
    try {
      const params = new URLSearchParams();
      if (active !== undefined) params.append('active', active.toString());
      
      const response = await fetch(`${this.baseUrl}/api/n8n/workflows?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.workflows || [];
    } catch (error) {
      console.error('N8n Workflows Error:', error);
      return [];
    }
  }
  
  static async getExecutions(status?: string, workflowId?: string): Promise<N8nExecution[]> {
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (workflowId) params.append('workflow_id', workflowId);
      
      const response = await fetch(`${this.baseUrl}/api/n8n/executions?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.executions || [];
    } catch (error) {
      console.error('N8n Executions Error:', error);
      return [];
    }
  }
  
  static async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      const data = await response.json();
      return data.status === 'healthy' && data.n8n_integration;
    } catch (error) {
      console.error('Backend Health Check Failed:', error);
      return false;
    }
  }
}

interface Chatbot {
  id: string;
  name: string;
  description: string;
  webhookUrl: string;
  status: 'active' | 'inactive' | 'testing';
  type: 'support' | 'sales' | 'faq' | 'custom';
  analytics: {
    totalMessages: number;
    activeUsers: number;
    avgResponseTime: string;
    satisfactionRate: number;
  };
  lastUpdated: string;
  features: string[];
}

const ChatbotCategory: React.FC = () => {
  const [chatbots, setChatbots] = useState<Chatbot[]>([
    {
      id: '1',
      name: 'Customer Support Bot',
      description: 'AI-powered support agent for instant customer assistance',
      webhookUrl: 'https://n8n.example.com/webhook/support-bot',
      status: 'active',
      type: 'support',
      analytics: {
        totalMessages: 15420,
        activeUsers: 342,
        avgResponseTime: '1.2s',
        satisfactionRate: 94.5
      },
      lastUpdated: '2 hours ago',
      features: ['Multi-language', 'Sentiment Analysis', 'Auto-escalation']
    },
    {
      id: '2',
      name: 'Sales Assistant',
      description: 'Intelligent sales bot for lead qualification and conversion',
      webhookUrl: 'https://n8n.example.com/webhook/sales-bot',
      status: 'active',
      type: 'sales',
      analytics: {
        totalMessages: 8932,
        activeUsers: 156,
        avgResponseTime: '0.8s',
        satisfactionRate: 91.2
      },
      lastUpdated: '5 hours ago',
      features: ['Lead Scoring', 'CRM Integration', 'Product Recommendations']
    },
    {
      id: '3',
      name: 'FAQ Bot',
      description: 'Quick answers to frequently asked questions',
      webhookUrl: 'https://n8n.example.com/webhook/faq-bot',
      status: 'testing',
      type: 'faq',
      analytics: {
        totalMessages: 5621,
        activeUsers: 89,
        avgResponseTime: '0.5s',
        satisfactionRate: 88.7
      },
      lastUpdated: '1 day ago',
      features: ['Knowledge Base', 'Smart Search', 'Auto-learning']
    }
  ]);

  const [selectedChatbot, setSelectedChatbot] = useState<Chatbot | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showTestChat, setShowTestChat] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [testMessages, setTestMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'bot', timestamp: Date}>>([]);
  const [newChatbot, setNewChatbot] = useState({
    name: '',
    description: '',
    type: 'support' as 'support' | 'sales' | 'faq' | 'custom',
    webhookUrl: '',
    features: [] as string[]
  });
  const [isCreating, setIsCreating] = useState(false);
  const [webhookError, setWebhookError] = useState('');
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [isFullWindow, setIsFullWindow] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [messageCount, setMessageCount] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  
  // Quick suggestion prompts
  const quickSuggestions = [
    "Tell me about your features",
    "How can you help me?",
    "What services do you offer?",
    "Can you explain pricing?",
    "I need technical support",
    "Show me examples",
    "Help me get started",
    "What are your capabilities?"
  ];

  const typeColors = {
    support: '#10b981',
    sales: '#f59e0b',
    faq: '#6366f1',
    custom: '#8b5cf6'
  } as const;

  const validateWebhookUrl = (url: string): boolean => {
    try {
      const parsed = new URL(url);
      return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleAddChatbot = () => {
    setNewChatbot({
      name: '',
      description: '',
      type: 'support',
      webhookUrl: '',
      features: []
    });
    setWebhookError('');
    setShowAddModal(true);
  };

  const handleCreateChatbot = async () => {
    // Validation
    if (!newChatbot.name.trim()) {
      setWebhookError('Please enter a chatbot name');
      return;
    }
    
    if (!newChatbot.description.trim()) {
      setWebhookError('Please enter a description');
      return;
    }
    
    if (!newChatbot.webhookUrl.trim()) {
      setWebhookError('Please enter a webhook URL');
      return;
    }
    
    if (!validateWebhookUrl(newChatbot.webhookUrl)) {
      setWebhookError('Please enter a valid webhook URL (must start with http:// or https://)');
      return;
    }

    setIsCreating(true);
    setWebhookError('');

    try {
      // Test the webhook URL by sending a test ping
      const testResponse = await fetch(newChatbot.webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'ping',
          test: true,
          timestamp: new Date().toISOString()
        })
      });

      // Create the new chatbot
      const newBot: Chatbot = {
        id: (Date.now()).toString(),
        name: newChatbot.name,
        description: newChatbot.description,
        webhookUrl: newChatbot.webhookUrl,
        status: testResponse.ok ? 'active' : 'testing',
        type: newChatbot.type,
        analytics: {
          totalMessages: 0,
          activeUsers: 0,
          avgResponseTime: '0s',
          satisfactionRate: 0
        },
        lastUpdated: 'Just now',
        features: newChatbot.features
      };

      setChatbots(prev => [...prev, newBot]);
      setShowAddModal(false);
      
      // Automatically open the chat interface for the newly created chatbot
      handleTestChat(newBot);
      
    } catch (error) {
      console.error('Error testing webhook:', error);
      
      // Still create the chatbot but mark it as testing
      const newBot: Chatbot = {
        id: (Date.now()).toString(),
        name: newChatbot.name,
        description: newChatbot.description,
        webhookUrl: newChatbot.webhookUrl,
        status: 'testing',
        type: newChatbot.type,
        analytics: {
          totalMessages: 0,
          activeUsers: 0,
          avgResponseTime: '0s',
          satisfactionRate: 0
        },
        lastUpdated: 'Just now',
        features: newChatbot.features
      };

      setChatbots(prev => [...prev, newBot]);
      setShowAddModal(false);
      
      // Still open the chat interface
      handleTestChat(newBot);
      
    } finally {
      setIsCreating(false);
    }
  };

  const handleTestChat = (chatbot: Chatbot) => {
    setSelectedChatbot(chatbot);
    setShowTestChat(true);
    setTestMessages([
      {
        id: '1',
        text: `Hello! I'm ${chatbot.name}. How can I help you today?`,
        sender: 'bot',
        timestamp: new Date()
      }
    ]);
  };

  const copyWebhook = (url: string) => {
    navigator.clipboard.writeText(url);
  };

  const sendTestMessage = async (message: string) => {
    if (!selectedChatbot || isSendingMessage) return;
    
    const newMessage = {
      id: Date.now().toString(),
      text: message,
      sender: 'user' as const,
      timestamp: new Date()
    };
    setTestMessages(prev => [...prev, newMessage]);
    setIsSendingMessage(true);

    try {
      let botResponseText = 'Sorry, I couldn\'t process your message.';
      let responseSource = 'fallback';
      
      // First, try the n8n API backend service for intelligent responses
      try {
        console.log('Attempting n8n API backend service...');
        const n8nResponse = await N8nApiService.sendMessage(message, selectedChatbot.id);
        
        if (n8nResponse && n8nResponse.response) {
          botResponseText = n8nResponse.response;
          responseSource = n8nResponse.source || 'n8n_api';
          console.log(`n8n API success (source: ${responseSource}):`, botResponseText);
        } else {
          throw new Error('Invalid n8n API response');
        }
      } catch (n8nError) {
        console.log('n8n API backend not available or failed:', n8nError);
        
        // Fallback to direct webhook approach
        console.log('Falling back to direct webhook:', selectedChatbot.webhookUrl);
        
        // Try different payload formats that n8n might expect
        const payloads = [
          // Format 1: Simple message field
          { message: message },
          // Format 2: Message with metadata
          {
            message: message,
            timestamp: new Date().toISOString(),
            userId: `user_${Date.now()}`,
            chatbotId: selectedChatbot.id
          },
          // Format 3: Text field instead of message
          { text: message },
          // Format 4: Input field
          { input: message },
          // Format 5: User message format
          { userMessage: message },
          // Format 6: Chat format
          { chat: message, user: `user_${Date.now()}` }
        ];
        
        let response;
        let data;
        let payloadUsed = null;
        
        // Try each payload format until one works
        for (let i = 0; i < payloads.length; i++) {
          try {
            console.log(`Trying payload format ${i + 1}:`, payloads[i]);
            
            response = await fetch(selectedChatbot.webhookUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
              },
              body: JSON.stringify(payloads[i])
            });
            
            console.log(`Response status for format ${i + 1}:`, response.status);
            
            if (response.ok) {
              const responseText = await response.text();
              console.log(`Raw response for format ${i + 1}:`, responseText);
              
              try {
                data = JSON.parse(responseText);
                payloadUsed = i + 1;
                console.log(`Successfully parsed JSON for format ${i + 1}:`, data);
                break;
              } catch (jsonError) {
                // If it's not JSON, treat the text as the response
                if (responseText.trim()) {
                  data = responseText.trim();
                  payloadUsed = i + 1;
                  console.log(`Using text response for format ${i + 1}:`, data);
                  break;
                }
              }
            }
          } catch (fetchError) {
            console.log(`Fetch error for format ${i + 1}:`, fetchError);
            continue;
          }
        }
        
        if (data) {
          console.log(`Webhook success with payload format ${payloadUsed}:`, data);
          responseSource = 'webhook';
          
          // Extract the response text from webhook response
          if (typeof data === 'string') {
            botResponseText = data;
          } else if (data && typeof data === 'object') {
            // Try different response field names
            if (data.response) {
              botResponseText = data.response;
            } else if (data.message) {
              botResponseText = data.message;
            } else if (data.text) {
              botResponseText = data.text;
            } else if (data.output) {
              botResponseText = data.output;
            } else if (data.result) {
              botResponseText = data.result;
            } else if (data.reply) {
              botResponseText = data.reply;
            } else if (data.answer) {
              botResponseText = data.answer;
            } else {
              // If it's an object but no known field, stringify it
              botResponseText = JSON.stringify(data, null, 2);
            }
          }
        } else {
          // Ultimate fallback - generate a contextual response
          botResponseText = `I understand you're asking: "${message}". I'm currently experiencing connectivity issues, but I'm working to resolve this. Please try again in a moment.`;
          responseSource = 'fallback';
        }
      }
      
      console.log(`Final bot response (${responseSource}):`, botResponseText);

      const botResponse = {
        id: (Date.now() + 1).toString(),
        text: botResponseText,
        sender: 'bot' as const,
        timestamp: new Date()
      };
      
      setTestMessages(prev => [...prev, botResponse]);
      
    } catch (error) {
      console.error('Error in sendTestMessage:', error);
      
      const errorResponse = {
        id: (Date.now() + 1).toString(),
        text: `I apologize, but I'm experiencing technical difficulties. Error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        sender: 'bot' as const,
        timestamp: new Date()
      };
      
      setTestMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsSendingMessage(false);
    }
  };

  // Utility Functions
  const clearChat = () => {
    setTestMessages([
      {
        id: '1',
        text: `Hello! I'm ${selectedChatbot?.name}. How can I help you today?`,
        sender: 'bot',
        timestamp: new Date()
      }
    ]);
    setMessageCount(0);
    setShowClearConfirm(false);
  };

  const exportChatHistory = () => {
    if (!selectedChatbot || testMessages.length === 0) return;
    
    const chatData = {
      chatbot: selectedChatbot.name,
      exported: new Date().toISOString(),
      messages: testMessages.map(msg => ({
        sender: msg.sender,
        text: msg.text,
        timestamp: msg.timestamp.toISOString()
      }))
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedChatbot.name.replace(/\s+/g, '_')}_chat_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyMessage = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const sendSuggestion = (suggestion: string) => {
    sendTestMessage(suggestion);
    setShowSuggestions(false);
  };

  const playNotificationSound = () => {
    if (soundEnabled) {
      // Create a simple notification sound
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.value = 0.1;
      
      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.2);
    }
  };

  // Update message count and play notification sound when new messages are added
  useEffect(() => {
    if (testMessages.length > 1) { // Exclude the initial greeting
      setMessageCount(Math.floor((testMessages.length - 1) / 2)); // Divide by 2 since each exchange has user + bot message
      
      // Play notification sound for bot messages (not the initial greeting)
      const lastMessage = testMessages[testMessages.length - 1];
      if (lastMessage.sender === 'bot' && testMessages.length > 1) {
        playNotificationSound();
      }
    }
  }, [testMessages, soundEnabled]);
  
  // Simulate connection status changes
  useEffect(() => {
    if (selectedChatbot) {
      setConnectionStatus('connecting');
      const timer = setTimeout(() => {
        setConnectionStatus(selectedChatbot.status === 'active' ? 'connected' : 'disconnected');
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [selectedChatbot]);

  const filteredChatbots = chatbots.filter(bot => {
    const matchesSearch = bot.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         bot.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || bot.type === (filterType as any);
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="chatbot-category">
      <div className="chatbot-header">
        <div className="header-content">
          <div className="header-text">
            <h1>
              <FaRobot className="header-icon" />
              AI Chatbots
            </h1>
            <p>Manage and deploy intelligent conversational agents</p>
          </div>
          <button className="add-chatbot-btn" onClick={handleAddChatbot}>
            <FaPlus /> New Chatbot
          </button>
        </div>

        <div className="control-bar">
          <div className="search-box">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search chatbots..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="filter-buttons">
            <button 
              className={`filter-btn ${filterType === 'all' ? 'active' : ''}`}
              onClick={() => setFilterType('all')}
            >
              All
            </button>
            <button 
              className={`filter-btn ${filterType === 'support' ? 'active' : ''}`}
              onClick={() => setFilterType('support')}
            >
              Support
            </button>
            <button 
              className={`filter-btn ${filterType === 'sales' ? 'active' : ''}`}
              onClick={() => setFilterType('sales')}
            >
              Sales
            </button>
            <button 
              className={`filter-btn ${filterType === 'faq' ? 'active' : ''}`}
              onClick={() => setFilterType('faq')}
            >
              FAQ
            </button>
          </div>
        </div>
      </div>

      <div className="stats-overview">
        <div className="stat-card gradient-1">
          <div className="stat-icon">
            <FaComments />
          </div>
          <div className="stat-content">
            <h3>29,973</h3>
            <p>Total Messages</p>
          </div>
        </div>
        <div className="stat-card gradient-2">
          <div className="stat-icon">
            <FaUsers />
          </div>
          <div className="stat-content">
            <h3>587</h3>
            <p>Active Users</p>
          </div>
        </div>
        <div className="stat-card gradient-3">
          <div className="stat-icon">
            <FaClock />
          </div>
          <div className="stat-content">
            <h3>0.8s</h3>
            <p>Avg Response</p>
          </div>
        </div>
        <div className="stat-card gradient-4">
          <div className="stat-icon">
            <FaChartLine />
          </div>
          <div className="stat-content">
            <h3>91.5%</h3>
            <p>Satisfaction</p>
          </div>
        </div>
      </div>

      <motion.div className="chatbots-grid">
        <AnimatePresence>
          {filteredChatbots.map((chatbot, index) => (
            <motion.div
              key={chatbot.id}
              className="chatbot-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -5 }}
            >
              <div className="card-header">
                <div className="card-title">
                  <div 
                    className="bot-type-badge"
                    style={{ backgroundColor: typeColors[chatbot.type] }}
                  >
                    {chatbot.type}
                  </div>
                  <div className={`status-indicator ${chatbot.status}`}>
                    <span className="status-dot"></span>
                    {chatbot.status}
                  </div>
                </div>
                <div className="card-actions">
                  <button className="action-btn" onClick={() => handleTestChat(chatbot)}>
                    <FaPlay />
                  </button>
                  <button className="action-btn">
                    <FaCog />
                  </button>
                </div>
              </div>

              <div className="card-body">
                <h3>{chatbot.name}</h3>
                <p>{chatbot.description}</p>

                <div className="webhook-section">
                  <label>Webhook URL</label>
                  <div className="webhook-input-group">
                    <input
                      type="text"
                      value={chatbot.webhookUrl}
                      readOnly
                      className="webhook-input"
                    />
                    <button 
                      className="copy-btn"
                      onClick={() => copyWebhook(chatbot.webhookUrl)}
                    >
                      <FaCopy />
                    </button>
                  </div>
                </div>

                <div className="features-list">
                  {chatbot.features.map((feature, idx) => (
                    <span key={idx} className="feature-tag">
                      {feature}
                    </span>
                  ))}
                </div>

                <div className="analytics-mini">
                  <div className="analytic-item">
                    <FaComments />
                    <span>{chatbot.analytics.totalMessages.toLocaleString()}</span>
                  </div>
                  <div className="analytic-item">
                    <FaUsers />
                    <span>{chatbot.analytics.activeUsers}</span>
                  </div>
                  <div className="analytic-item">
                    <FaClock />
                    <span>{chatbot.analytics.avgResponseTime}</span>
                  </div>
                  <div className="analytic-item">
                    <FaChartLine />
                    <span>{chatbot.analytics.satisfactionRate}%</span>
                  </div>
                </div>

                <div className="card-footer">
                  <span className="last-updated">Updated {chatbot.lastUpdated}</span>
                  <button className="view-analytics-btn">
                    View Analytics <FaExternalLinkAlt />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {showAddModal && (
          <motion.div 
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAddModal(false)}
          >
            <motion.div 
              className="modal-content"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2>Create New Chatbot</h2>
                <button className="close-btn" onClick={() => setShowAddModal(false)}>
                  <FaTimes />
                </button>
              </div>
              
              <div className="modal-body">
                {webhookError && (
                  <div className="error-message">
                    {webhookError}
                  </div>
                )}
                
                <div className="form-group">
                  <label>Chatbot Name</label>
                  <input 
                    type="text" 
                    placeholder="Enter chatbot name"
                    value={newChatbot.name}
                    onChange={(e) => setNewChatbot({...newChatbot, name: e.target.value})}
                  />
                </div>
                
                <div className="form-group">
                  <label>Description</label>
                  <textarea 
                    placeholder="Describe your chatbot's purpose" 
                    rows={3}
                    value={newChatbot.description}
                    onChange={(e) => setNewChatbot({...newChatbot, description: e.target.value})}
                  />
                </div>
                
                <div className="form-group">
                  <label>Type</label>
                  <select 
                    value={newChatbot.type}
                    onChange={(e) => setNewChatbot({...newChatbot, type: e.target.value as 'support' | 'sales' | 'faq' | 'custom'})}
                  >
                    <option value="support">Customer Support</option>
                    <option value="sales">Sales Assistant</option>
                    <option value="faq">FAQ Bot</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>n8n Webhook URL</label>
                  <input 
                    type="text" 
                    placeholder="https://your-n8n-instance.com/webhook/..."
                    value={newChatbot.webhookUrl}
                    onChange={(e) => setNewChatbot({...newChatbot, webhookUrl: e.target.value})}
                  />
                  <small>Enter the webhook URL from your n8n workflow</small>
                </div>

                <div className="form-group">
                  <label>Features</label>
                  <div className="feature-checkboxes">
                    <label className="checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={newChatbot.features.includes('Multi-language Support')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewChatbot({...newChatbot, features: [...newChatbot.features, 'Multi-language Support']});
                          } else {
                            setNewChatbot({...newChatbot, features: newChatbot.features.filter(f => f !== 'Multi-language Support')});
                          }
                        }}
                      />
                      <span>Multi-language Support</span>
                    </label>
                    <label className="checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={newChatbot.features.includes('Sentiment Analysis')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewChatbot({...newChatbot, features: [...newChatbot.features, 'Sentiment Analysis']});
                          } else {
                            setNewChatbot({...newChatbot, features: newChatbot.features.filter(f => f !== 'Sentiment Analysis')});
                          }
                        }}
                      />
                      <span>Sentiment Analysis</span>
                    </label>
                    <label className="checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={newChatbot.features.includes('Auto-escalation')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewChatbot({...newChatbot, features: [...newChatbot.features, 'Auto-escalation']});
                          } else {
                            setNewChatbot({...newChatbot, features: newChatbot.features.filter(f => f !== 'Auto-escalation')});
                          }
                        }}
                      />
                      <span>Auto-escalation</span>
                    </label>
                    <label className="checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={newChatbot.features.includes('Analytics Dashboard')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewChatbot({...newChatbot, features: [...newChatbot.features, 'Analytics Dashboard']});
                          } else {
                            setNewChatbot({...newChatbot, features: newChatbot.features.filter(f => f !== 'Analytics Dashboard')});
                          }
                        }}
                      />
                      <span>Analytics Dashboard</span>
                    </label>
                  </div>
                </div>
              </div>
              
              <div className="modal-footer">
                <button className="btn-secondary" onClick={() => setShowAddModal(false)} disabled={isCreating}>
                  Cancel
                </button>
                <button className="btn-primary" onClick={handleCreateChatbot} disabled={isCreating}>
                  {isCreating ? 'Creating...' : 'Create Chatbot'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Interface - Both Popup and Full Window */}
      <AnimatePresence>
        {showTestChat && selectedChatbot && (
          <>
            {/* Full Window Chat */}
            {isFullWindow && (
              <motion.div 
                className="chat-full-window"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className="chat-full-background">
                  <div className="gradient-orb orb-1"></div>
                  <div className="gradient-orb orb-2"></div>
                  <div className="grid-pattern"></div>
                </div>
                
                <div className="chat-full-header">
                  <div className="chat-full-info">
                    <div className="chatbot-avatar">
                      <FaRobot />
                    </div>
                    <div className="chatbot-details">
                      <h2>{selectedChatbot.name}</h2>
                      <p>{selectedChatbot.description}</p>
                      <div className="chatbot-status">
                        <div className={`status-indicator ${selectedChatbot.status}`}>
                          <span className="status-dot"></span>
                          {selectedChatbot.status}
                        </div>
                        <span className="chatbot-type" style={{ color: typeColors[selectedChatbot.type] }}>
                          {selectedChatbot.type}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="chat-full-controls">
                    <div className="chat-stats">
                      <span className="message-count">{messageCount} exchanges</span>
                      <div className={`connection-status ${connectionStatus}`}>
                        <span className="status-dot"></span>
                        {connectionStatus}
                      </div>
                    </div>
                    
                    <div className="utility-controls">
                      <button 
                        className="utility-btn"
                        onClick={() => setShowSuggestions(!showSuggestions)}
                        title="Quick suggestions"
                      >
                        <FaLightbulb />
                      </button>
                      <button 
                        className="utility-btn"
                        onClick={exportChatHistory}
                        title="Export chat history"
                        disabled={testMessages.length <= 1}
                      >
                        <FaDownload />
                      </button>
                      <button 
                        className="utility-btn"
                        onClick={() => setSoundEnabled(!soundEnabled)}
                        title={soundEnabled ? 'Disable sound' : 'Enable sound'}
                      >
                        {soundEnabled ? <FaVolumeUp /> : <FaVolumeMute />}
                      </button>
                      <button 
                        className="utility-btn danger"
                        onClick={() => setShowClearConfirm(true)}
                        title="Clear chat"
                        disabled={testMessages.length <= 1}
                      >
                        <FaTrashAlt />
                      </button>
                    </div>
                    
                    <div className="window-controls">
                      <button 
                        className="control-btn"
                        onClick={() => setIsFullWindow(false)}
                        title="Minimize to popup"
                      >
                        <FaWindowMinimize />
                      </button>
                      <button 
                        className="control-btn close-btn"
                        onClick={() => {
                          setShowTestChat(false);
                          setIsFullWindow(false);
                        }}
                        title="Close chat"
                      >
                        <FaTimes />
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="chat-full-container">
                  {/* Quick Suggestions Panel */}
                  <AnimatePresence>
                    {showSuggestions && (
                      <motion.div
                        className="suggestions-panel"
                        initial={{ opacity: 0, x: -300 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -300 }}
                        transition={{ type: "spring", damping: 25 }}
                      >
                        <div className="suggestions-header">
                          <h4><FaLightbulb /> Quick Suggestions</h4>
                          <button 
                            className="close-suggestions"
                            onClick={() => setShowSuggestions(false)}
                          >
                            <FaTimes />
                          </button>
                        </div>
                        <div className="suggestions-list">
                          {quickSuggestions.map((suggestion, index) => (
                            <motion.button
                              key={index}
                              className="suggestion-item"
                              onClick={() => sendSuggestion(suggestion)}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                            >
                              <FaPaperPlane className="suggestion-icon" />
                              {suggestion}
                            </motion.button>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  <div className="chat-full-messages">
                    {testMessages.map((message) => (
                      <motion.div 
                        key={message.id} 
                        className={`message ${message.sender}`}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="message-avatar">
                          {message.sender === 'bot' ? <FaRobot /> : <FaUsers />}
                        </div>
                        <div className="message-content">
                          <div className="message-bubble">
                            {message.text}
                            <div className="message-actions">
                              <button 
                                className="message-action"
                                onClick={() => copyMessage(message.text)}
                                title="Copy message"
                              >
                                <FaCopy />
                              </button>
                            </div>
                          </div>
                          <span className="message-time">
                            {message.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                      </motion.div>
                    ))}
                    {isSendingMessage && (
                      <motion.div 
                        className="message bot"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                      >
                        <div className="message-avatar">
                          <FaRobot />
                        </div>
                        <div className="message-content">
                          <div className="message-bubble typing">
                            <div className="typing-indicator">
                              <span></span>
                              <span></span>
                              <span></span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                  
                  <div className="chat-full-input">
                    <div className="input-container">
                      <input 
                        type="text" 
                        placeholder="Type your message..."
                        disabled={isSendingMessage}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && e.currentTarget.value && !isSendingMessage) {
                            sendTestMessage(e.currentTarget.value);
                            e.currentTarget.value = '';
                          }
                        }}
                      />
                      <button 
                        className="send-btn" 
                        disabled={isSendingMessage}
                        onClick={(e) => {
                          const input = e.currentTarget.parentElement?.querySelector('input') as HTMLInputElement;
                          if (input && input.value && !isSendingMessage) {
                            sendTestMessage(input.value);
                            input.value = '';
                          }
                        }}
                      >
                        {isSendingMessage ? 'Sending...' : 'Send'}
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            
            {/* Popup Chat */}
            {!isFullWindow && (
              <motion.div 
                className="test-chat-container"
                initial={{ x: 400, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 400, opacity: 0 }}
              >
                <div className="test-chat-header">
                  <div className="chat-info">
                    <h3>{selectedChatbot.name}</h3>
                    <span className="test-mode">Test Mode</span>
                  </div>
                  <div className="chat-controls">
                    <div className="popup-status">
                      <div className={`connection-indicator ${connectionStatus}`} title={connectionStatus}></div>
                      <span className="message-count">{messageCount}</span>
                    </div>
                    
                    <div className="popup-actions">
                      <button 
                        className="popup-menu-btn"
                        onClick={() => setShowSuggestions(!showSuggestions)}
                        title="Options"
                      >
                        <FaCog />
                      </button>
                      <button 
                        className="expand-btn"
                        onClick={() => setIsFullWindow(true)}
                        title="Expand to full window"
                      >
                        <FaExpand />
                      </button>
                      <button 
                        className="close-chat-btn" 
                        onClick={() => setShowTestChat(false)}
                        title="Close chat"
                      >
                        <FaTimes />
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="test-chat-messages">
                  {/* Popup Options Menu */}
                  <AnimatePresence>
                    {showSuggestions && (
                      <motion.div
                        className="popup-options-menu"
                        initial={{ opacity: 0, scale: 0.9, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: -10 }}
                        transition={{ type: "spring", damping: 25 }}
                      >
                        <div className="popup-menu-header">
                          <span>Chat Options</span>
                          <button onClick={() => setShowSuggestions(false)}>
                            <FaTimes />
                          </button>
                        </div>
                        
                        <div className="popup-menu-section">
                          <h4>Quick Suggestions</h4>
                          <div className="popup-suggestions">
                            {quickSuggestions.slice(0, 3).map((suggestion, index) => (
                              <button
                                key={index}
                                className="suggestion-popup-item"
                                onClick={() => sendSuggestion(suggestion)}
                              >
                                <FaPaperPlane className="suggestion-icon" />
                                {suggestion}
                              </button>
                            ))}
                          </div>
                        </div>
                        
                        <div className="popup-menu-section">
                          <h4>Actions</h4>
                          <div className="popup-menu-actions">
                            <button 
                              className="popup-action-btn"
                              onClick={exportChatHistory}
                              disabled={testMessages.length <= 1}
                            >
                              <FaDownload /> Export Chat
                            </button>
                            <button 
                              className="popup-action-btn"
                              onClick={() => setSoundEnabled(!soundEnabled)}
                            >
                              {soundEnabled ? <FaVolumeUp /> : <FaVolumeMute />} 
                              {soundEnabled ? 'Sound On' : 'Sound Off'}
                            </button>
                            <button 
                              className="popup-action-btn danger"
                              onClick={() => {
                                setShowSuggestions(false);
                                setShowClearConfirm(true);
                              }}
                              disabled={testMessages.length <= 1}
                            >
                              <FaTrashAlt /> Clear Chat
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  {testMessages.map((message) => (
                    <div key={message.id} className={`message ${message.sender}`}>
                      <div className="message-bubble">
                        {message.text}
                      </div>
                      <span className="message-time">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                  {isSendingMessage && (
                    <div className="message bot">
                      <div className="message-bubble typing">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="test-chat-input">
                  <input 
                    type="text" 
                    placeholder="Type a test message..."
                    disabled={isSendingMessage}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value && !isSendingMessage) {
                        sendTestMessage(e.currentTarget.value);
                        e.currentTarget.value = '';
                      }
                    }}
                  />
                  <button 
                    className="send-btn" 
                    disabled={isSendingMessage}
                    onClick={(e) => {
                      const input = e.currentTarget.parentElement?.querySelector('input') as HTMLInputElement;
                      if (input && input.value && !isSendingMessage) {
                        sendTestMessage(input.value);
                        input.value = '';
                      }
                    }}
                  >
                    {isSendingMessage ? 'Sending...' : 'Send'}
                  </button>
                </div>
              </motion.div>
            )}
          </>
        )}
      </AnimatePresence>
      
      {/* Clear Chat Confirmation Modal */}
      <AnimatePresence>
        {showClearConfirm && (
          <motion.div 
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowClearConfirm(false)}
          >
            <motion.div 
              className="modal-content confirmation-modal"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="confirmation-header">
                <FaTrashAlt className="warning-icon" />
                <h3>Clear Chat History</h3>
              </div>
              
              <div className="confirmation-body">
                <p>Are you sure you want to clear all chat messages?</p>
                <p className="warning-text">This action cannot be undone.</p>
              </div>
              
              <div className="confirmation-footer">
                <button 
                  className="btn-secondary"
                  onClick={() => setShowClearConfirm(false)}
                >
                  Cancel
                </button>
                <button 
                  className="btn-danger"
                  onClick={clearChat}
                >
                  Clear Chat
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ChatbotCategory;

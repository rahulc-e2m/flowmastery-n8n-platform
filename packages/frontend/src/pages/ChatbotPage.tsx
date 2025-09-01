import React, { useState, useRef, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Send,
  Bot,
  User,
  Settings,
  X,
  MessageCircle,
  Building2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

interface ChatMessage {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
}

import { ChatbotApi } from '@/services/chatbotApi'

export function ChatbotPage() {
  const { id } = useParams<{ id: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showConfig, setShowConfig] = useState(false)
  const [webhookUrl, setWebhookUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch chatbot details
  const { data: chatbot, isLoading: isChatbotLoading } = useQuery({
    queryKey: ['chatbot', id],
    queryFn: () => ChatbotApi.getById(id!),
    enabled: !!id
  })

  useEffect(() => {
    if (chatbot) {
      setWebhookUrl(chatbot.webhook_url)
    }
  }, [chatbot])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || !webhookUrl) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
        },
        body: JSON.stringify({
          message: userMessage.content,
          timestamp: userMessage.timestamp.toISOString()
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      let botResponseText = 'No response received'
      if (data.output) {
        botResponseText = data.output
      } else if (data.result) {
        botResponseText = data.result
      } else if (data.text) {
        botResponseText = data.text
      } else if (data.message) {
        botResponseText = data.message
      } else if (typeof data === 'string') {
        botResponseText = data
      }

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: botResponseText,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error: any) {
      console.error('Error sending message:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: `Error: ${error.message}. Please check your webhook URL and try again.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      toast.error('Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    toast.success('Chat cleared')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (isChatbotLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading chatbot...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!chatbot) {
    return (
      <div className="p-6 space-y-6">
        <div className="text-center py-12">
          <MessageCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Chatbot not found</h3>
          <p className="text-muted-foreground mb-4">
            The chatbot you're looking for doesn't exist or has been removed.
          </p>
          <Link to="/chatbots">
            <Button>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Chatbots
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/chatbots">
            <Button variant="ghost" size="sm" className="flex items-center space-x-2">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Chatbots</span>
            </Button>
          </Link>
          <div className="flex items-center space-x-3">
            <motion.div 
              className="p-3 rounded-xl bg-blue-500 text-white"
              whileHover={{ scale: 1.05 }}
            >
              <MessageCircle className="w-6 h-6" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold">{chatbot.name}</h1>
              <div className="flex items-center space-x-4 text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <Building2 className="w-4 h-4" />
                  <span>{chatbot.client_name}</span>
                </div>
                {chatbot.description && (
                  <span>• {chatbot.description}</span>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={chatbot.is_active ? "default" : "secondary"}>
            {chatbot.is_active ? "Active" : "Inactive"}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowConfig(true)}
            className="flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Configure</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={clearChat}
            className="flex items-center space-x-2"
          >
            <X className="w-4 h-4" />
            <span>Clear Chat</span>
          </Button>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chat Area */}
        <div className="lg:col-span-2">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <MessageCircle className="w-5 h-5" />
                    <span>Chat Interface</span>
                  </CardTitle>
                  <CardDescription>Interactive conversation with your AI assistant</CardDescription>
                </div>
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                  Connected
                </Badge>
              </div>
            </CardHeader>
            
            {/* Messages Area */}
            <CardContent className="flex-1 flex flex-col p-0">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex items-start space-x-2 max-w-[80%] ${
                        message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                      }`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          message.type === 'user' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {message.type === 'user' ? (
                            <User className="w-4 h-4" />
                          ) : (
                            <Bot className="w-4 h-4" />
                          )}
                        </div>
                        <div className={`rounded-lg px-4 py-2 ${
                          message.type === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                          <p className="text-xs opacity-70 mt-1">
                            {message.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start"
                  >
                    <div className="flex items-start space-x-2">
                      <div className="w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="bg-muted rounded-lg px-4 py-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
              
              {/* Input Area */}
              <div className="border-t p-4">
                <div className="flex space-x-2">
                  <Input
                    placeholder="Type your message..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading || !webhookUrl}
                    className="flex-1"
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={isLoading || !inputMessage.trim() || !webhookUrl}
                    size="sm"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                {!webhookUrl && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Configure webhook URL to start chatting
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Chat Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Messages</span>
                <span className="font-medium">{messages.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">User Messages</span>
                <span className="font-medium">{messages.filter(m => m.type === 'user').length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Bot Responses</span>
                <span className="font-medium">{messages.filter(m => m.type === 'bot').length}</span>
              </div>
            </CardContent>
          </Card>

          {/* Chatbot Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Chatbot Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <span className="text-sm text-muted-foreground">Created</span>
                <p className="font-medium">{new Date(chatbot.created_at).toLocaleDateString()}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Webhook URL</span>
                <p className="font-medium text-xs break-all">{chatbot.webhook_url}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Status</span>
                <p className="font-medium">{chatbot.is_active ? 'Active' : 'Inactive'}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Configuration Dialog */}
      <Dialog open={showConfig} onOpenChange={setShowConfig}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Configure Chatbot</DialogTitle>
            <CardDescription>
              Update webhook URL and optional API key for the chatbot integration.
            </CardDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="webhook">Webhook URL</Label>
              <Input
                id="webhook"
                placeholder="https://your-n8n-webhook-url.com"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="apikey">API Key (Optional)</Label>
              <Input
                id="apikey"
                type="password"
                placeholder="Your API key for authentication"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfig(false)}>
              Cancel
            </Button>
            <Button onClick={() => {
              setShowConfig(false)
              toast.success('Configuration updated')
            }}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
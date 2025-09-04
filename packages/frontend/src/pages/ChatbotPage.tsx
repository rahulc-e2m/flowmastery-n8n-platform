import React, { useState, useRef, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Send,
  Bot,
  User,
  Settings,
  X,
  MessageCircle,
  Building2,
  ArrowDown,
  History,
  Clock,
  MessageSquare
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'
import { MarkdownMessage } from '@/components/ui/markdown-message'

interface ChatMessage {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
}

interface Conversation {
  conversation_id: string
  last_message_time: string
  last_user_message: string
}

import { ChatbotApi } from '@/services/chatbotApi'

export function ChatbotPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showConfig, setShowConfig] = useState(false)
  const [webhookUrl, setWebhookUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const [activeTab, setActiveTab] = useState('chat')
  const [shouldLoadHistory, setShouldLoadHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Fetch chatbot details
  const { data: chatbot, isLoading: isChatbotLoading } = useQuery({
    queryKey: ['chatbot', id],
    queryFn: () => ChatbotApi.getById(id!),
    enabled: !!id
  })

  // Fetch chat history
  const { data: chatHistory } = useQuery({
    queryKey: ['chatHistory', id, conversationId],
    queryFn: async () => {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const url = conversationId
        ? `${API_BASE_URL}/api/v1/chat/${id}/history?conversation_id=${conversationId}`
        : `${API_BASE_URL}/api/v1/chat/${id}/history`

      const response = await fetch(url, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to fetch chat history')
      }

      const result = await response.json()
      console.log('Chat history API response:', result) // Debug log

      // The backend returns data wrapped in a response format
      return result.data || result
    },
    enabled: !!id && shouldLoadHistory && conversationId !== null,
    refetchOnWindowFocus: false
  })

  // Fetch conversations list
  const { data: conversations, isLoading: conversationsLoading } = useQuery({
    queryKey: ['conversations', id],
    queryFn: async () => {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/${id}/conversations`, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to fetch conversations')
      }

      const result = await response.json()
      console.log('Conversations API response:', result) // Debug log

      // The backend returns data wrapped in a response format
      return result.data || result
    },
    enabled: !!id,
    refetchOnWindowFocus: false
  })

  useEffect(() => {
    if (chatbot) {
      setWebhookUrl(chatbot.webhook_url)
    }
  }, [chatbot])

  // Debug effect to log conversations data
  useEffect(() => {
    console.log('Conversations data updated:', conversations)
  }, [conversations])

  // Load chat history into messages state
  useEffect(() => {
    if (chatHistory?.messages) {
      const historyMessages: ChatMessage[] = chatHistory.messages
        .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
        .map((msg: any) => [
          {
            id: `${msg.id}-user`,
            type: 'user' as const,
            content: msg.user_message,
            timestamp: new Date(msg.timestamp)
          },
          {
            id: `${msg.id}-bot`,
            type: 'bot' as const,
            content: msg.bot_response,
            timestamp: new Date(msg.timestamp)
          }
        ]).flat()

      setMessages(historyMessages)
    } else if (chatHistory && !chatHistory.messages) {
      // If we have a response but no messages, clear the current messages
      setMessages([])
    }
  }, [chatHistory])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    // Only auto-scroll if user is near the bottom or if it's a new message
    const scrollContainer = messagesContainerRef.current
    if (scrollContainer && messages.length > 0) {
      const isNearBottom = scrollContainer.scrollTop + scrollContainer.clientHeight >= scrollContainer.scrollHeight - 100
      if (isNearBottom || messages.length <= 2) {
        setTimeout(scrollToBottom, 100) // Small delay to ensure DOM is updated
      }
    }
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      // Use our backend API instead of calling webhook directly
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for authentication
        body: JSON.stringify({
          message: userMessage.content,
          chatbot_id: id,
          conversation_id: conversationId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Use the response from our backend API
      const botResponseText = data.response || 'No response received'

      // Update conversation ID if we got one back
      const newConversationId = data.conversation_id || conversationId
      if (data.conversation_id && !conversationId) {
        setConversationId(data.conversation_id)
        setShouldLoadHistory(true) // Enable history loading for this new conversation
      }

      const botMessage: ChatMessage = {
        id: data.message_id || `bot-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'bot',
        content: botResponseText,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, botMessage])

      // Refresh conversations list to show the updated conversation
      queryClient.invalidateQueries({ queryKey: ['conversations', id] })

      // Don't refetch history immediately to avoid overwriting current messages
      // The messages are already persisted on the backend
    } catch (error: any) {
      console.error('Error sending message:', error)
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
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

  const startNewChat = () => {
    // Clear local state
    setMessages([])
    setConversationId(null) // Reset conversation ID for new chat
    setShouldLoadHistory(false) // Prevent loading any history

    // Clear the chat history query cache to prevent auto-loading
    queryClient.removeQueries({ queryKey: ['chatHistory', id] })

    // Refresh conversations list to show updated list
    queryClient.invalidateQueries({ queryKey: ['conversations', id] })

    toast.success('New chat started')
  }

  const loadConversation = async (selectedConversationId: string) => {
    try {
      // Set the conversation ID first
      setConversationId(selectedConversationId)
      setShouldLoadHistory(true) // Enable history loading for this conversation

      // Invalidate and refetch the chat history query with the new conversation ID
      await queryClient.invalidateQueries({
        queryKey: ['chatHistory', id, selectedConversationId]
      })

      // Switch to chat tab
      setActiveTab('chat')
      toast.success('Conversation loaded')
    } catch (error) {
      console.error('Error loading conversation:', error)
      toast.error('Failed to load conversation')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (isChatbotLoading) {
    return (
      <div className="p-6">
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
      <div className="p-6">
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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-6 pb-4 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link to="/chatbots">
              <Button variant="ghost" size="sm" className="flex items-center space-x-2 hover:bg-accent/50">
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Chatbots</span>
              </Button>
            </Link>
            <div className="flex items-center space-x-3">
              <motion.div
                className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg"
                whileHover={{ scale: 1.05 }}
              >
                <MessageCircle className="w-5 h-5" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">{chatbot.name}</h1>
                <div className="flex items-center space-x-3 text-sm text-muted-foreground">
                  <div className="flex items-center space-x-1">
                    <Building2 className="w-3.5 h-3.5" />
                    <span>{chatbot.client_name}</span>
                  </div>
                  {chatbot.description && (
                    <span>• {chatbot.description}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Badge variant={chatbot.is_active ? "default" : "secondary"} className="px-3 py-1">
              {chatbot.is_active ? "Active" : "Inactive"}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowConfig(true)}
              className="flex items-center space-x-2 hover:bg-accent/50"
            >
              <Settings className="w-4 h-4" />
              <span>Configure</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={startNewChat}
              className="flex items-center space-x-2 hover:bg-accent/50"
            >
              <X className="w-4 h-4" />
              <span>Clear Chat</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content with Tabs */}
      <div className="flex-1 p-6 pt-4">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
          {/* Main Area with Tabs */}
          <div className="lg:col-span-3">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <TabsList className="grid w-full grid-cols-2 max-w-sm">
                  <TabsTrigger value="chat" className="flex items-center space-x-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                    <MessageCircle className="w-4 h-4" />
                    <span>Chat</span>
                  </TabsTrigger>
                  <TabsTrigger value="conversations" className="flex items-center space-x-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                    <History className="w-4 h-4" />
                    <span>Conversations</span>
                  </TabsTrigger>
                </TabsList>
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  Connected
                </Badge>
              </div>

              <TabsContent value="chat" className="flex-1 mt-0">
                <Card className="h-full flex flex-col border-0 shadow-lg">
                  <CardHeader className="pb-4 px-6 pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="flex items-center space-x-2 text-lg">
                          <MessageCircle className="w-5 h-5 text-primary" />
                          <span>Chat Interface</span>
                        </CardTitle>
                        <CardDescription className="mt-1">Interactive conversation with your AI assistant</CardDescription>
                      </div>
                    </div>
                  </CardHeader>

                  {/* Messages Area */}
                  <CardContent className="flex-1 flex flex-col p-0">
                    <div
                      ref={messagesContainerRef}
                      className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scroll-smooth relative bg-gradient-to-b from-background to-muted/20"
                      style={{
                        minHeight: '400px',
                        maxHeight: 'calc(100vh - 300px)',
                        scrollBehavior: 'smooth'
                      }}
                      onScroll={(e) => {
                        const container = e.currentTarget
                        const isNearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100
                        setShowScrollButton(!isNearBottom && messages.length > 0)
                      }}
                    >
                      {messages.length === 0 && !isLoading && (
                        <div className="flex items-center justify-center h-full text-center py-12">
                          <div className="space-y-4">
                            <div className="w-16 h-16 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full flex items-center justify-center mx-auto">
                              <MessageCircle className="w-8 h-8 text-primary" />
                            </div>
                            <div className="space-y-2">
                              <p className="text-lg font-medium text-foreground">Start a conversation</p>
                              <p className="text-sm text-muted-foreground max-w-sm">Type a message below to begin chatting with your AI assistant</p>
                            </div>
                          </div>
                        </div>
                      )}

                      <AnimatePresence>
                        {messages.map((message) => (
                          <motion.div
                            key={message.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                          >
                            <div className={`flex items-start space-x-3 max-w-[85%] ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                              }`}>
                              <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${message.type === 'user'
                                ? 'bg-gradient-to-br from-primary to-primary/80 text-primary-foreground'
                                : 'bg-gradient-to-br from-muted to-muted/80 text-muted-foreground border border-border/50'
                                }`}>
                                {message.type === 'user' ? (
                                  <User className="w-4 h-4" />
                                ) : (
                                  <Bot className="w-4 h-4" />
                                )}
                              </div>
                              <div className={`rounded-2xl px-4 py-3 shadow-sm ${message.type === 'user'
                                ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground'
                                : 'bg-background border border-border/50 text-foreground'
                                }`}>
                                {message.type === 'bot' ? (
                                  <MarkdownMessage 
                                    content={message.content} 
                                    className="text-sm leading-relaxed" 
                                  />
                                ) : (
                                  <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">{message.content}</p>
                                )}
                                <p className={`text-xs mt-2 ${message.type === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                          <div className="flex items-start space-x-3">
                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-muted to-muted/80 text-muted-foreground flex items-center justify-center border border-border/50 shadow-sm">
                              <Bot className="w-4 h-4" />
                            </div>
                            <div className="bg-background border border-border/50 rounded-2xl px-4 py-3 shadow-sm">
                              <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}

                      <div ref={messagesEndRef} />

                      {/* Scroll to bottom button */}
                      {showScrollButton && (
                        <motion.button
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.8 }}
                          onClick={scrollToBottom}
                          className="absolute bottom-6 right-6 bg-primary text-primary-foreground rounded-full p-3 shadow-lg hover:bg-primary/90 transition-all duration-200 hover:scale-110 border-2 border-background"
                        >
                          <ArrowDown className="w-4 h-4" />
                        </motion.button>
                      )}
                    </div>

                    {/* Input Area */}
                    <div className="border-t border-border/50 p-6 bg-background/95 backdrop-blur-sm">
                      <div className="flex space-x-3">
                        <Input
                          placeholder="Type your message... (Press Enter to send)"
                          value={inputMessage}
                          onChange={(e) => setInputMessage(e.target.value)}
                          onKeyPress={handleKeyPress}
                          disabled={isLoading}
                          className="flex-1 h-11 bg-background border-border/50 focus:border-primary/50 focus:ring-primary/20"
                          autoFocus
                        />
                        <Button
                          onClick={sendMessage}
                          disabled={isLoading || !inputMessage.trim()}
                          size="default"
                          className="h-11 px-4 bg-primary hover:bg-primary/90"
                        >
                          {isLoading ? (
                            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                      {conversationId && (
                        <p className="text-xs text-muted-foreground mt-3 flex items-center space-x-1">
                          <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                          <span>Conversation: {conversationId.slice(-8)}</span>
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="conversations" className="flex-1 mt-0">
                <Card className="h-full flex flex-col border-0 shadow-lg">
                  <CardHeader className="pb-4 px-6 pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="flex items-center space-x-2 text-lg">
                          <History className="w-5 h-5 text-primary" />
                          <span>Conversations</span>
                        </CardTitle>
                        <CardDescription className="mt-1">Browse and load previous conversations</CardDescription>
                      </div>
                      <Badge variant="outline" className="px-3 py-1.5 bg-muted/50">
                        {conversations?.conversations?.length || 0} Total
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="flex-1 overflow-y-auto px-6 py-4 bg-gradient-to-b from-background to-muted/20">
                    {conversationsLoading ? (
                      <div className="flex items-center justify-center h-full py-12">
                        <div className="text-center">
                          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                          <p className="text-muted-foreground">Loading conversations...</p>
                        </div>
                      </div>
                    ) : !conversations?.conversations || conversations?.conversations?.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-center py-12">
                        <div className="space-y-4">
                          <div className="w-16 h-16 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full flex items-center justify-center mx-auto">
                            <MessageSquare className="w-8 h-8 text-primary" />
                          </div>
                          <div className="space-y-2">
                            <p className="text-lg font-medium text-foreground">No conversations yet</p>
                            <p className="text-sm text-muted-foreground max-w-sm">Start chatting to create your first conversation</p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {conversations?.conversations?.map((conversation: Conversation) => (
                          <motion.div
                            key={conversation.conversation_id}
                            className="group p-5 rounded-xl border border-border/50 hover:border-primary/30 transition-all duration-200 hover:bg-accent/30 cursor-pointer hover:shadow-md"
                            onClick={() => loadConversation(conversation.conversation_id)}
                            whileHover={{ scale: 1.01, x: 4 }}
                            whileTap={{ scale: 0.99 }}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-3 mb-3">
                                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center flex-shrink-0">
                                    <MessageSquare className="w-5 h-5 text-primary" />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                                      Conversation {conversation.conversation_id.slice(-8)}
                                    </p>
                                    <div className="flex items-center space-x-1.5 text-xs text-muted-foreground mt-1">
                                      <Clock className="w-3 h-3" />
                                      <span>
                                        {formatDistanceToNow(new Date(conversation.last_message_time), { addSuffix: true })}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                                <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed pl-13">
                                  {conversation.last_user_message}
                                </p>
                              </div>
                              <div className="ml-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-primary/10">
                                  <ArrowLeft className="w-4 h-4 rotate-180 text-primary" />
                                </Button>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Chat Statistics */}
            <Card className="border-0 shadow-lg">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg flex items-center space-x-2">
                  <div className="w-2 h-2 bg-primary rounded-full"></div>
                  <span>Chat Statistics</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-3">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                    <span className="text-sm text-muted-foreground">Messages</span>
                    <span className="font-semibold text-lg">{messages.length}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30">
                    <span className="text-sm text-muted-foreground">User Messages</span>
                    <span className="font-semibold text-lg text-blue-600 dark:text-blue-400">{messages.filter(m => m.type === 'user').length}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950/30">
                    <span className="text-sm text-muted-foreground">Bot Responses</span>
                    <span className="font-semibold text-lg text-green-600 dark:text-green-400">{messages.filter(m => m.type === 'bot').length}</span>
                  </div>
                </div>
                {conversationId && (
                  <div className="pt-4 border-t border-border/50">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-primary/10">
                      <span className="text-sm text-muted-foreground">Active Conversation</span>
                      <span className="font-medium text-sm text-primary">{conversationId.slice(-8)}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="border-0 shadow-lg">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg flex items-center space-x-2">
                  <div className="w-2 h-2 bg-primary rounded-full"></div>
                  <span>Quick Actions</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="outline"
                  size="default"
                  onClick={() => setActiveTab('conversations')}
                  className="w-full flex items-center space-x-2 h-11 hover:bg-primary/10 hover:border-primary/30"
                >
                  <History className="w-4 h-4" />
                  <span>View All Conversations</span>
                </Button>
                <Button
                  variant="outline"
                  size="default"
                  onClick={startNewChat}
                  className="w-full flex items-center space-x-2 h-11 hover:bg-destructive/10 hover:border-destructive/30 hover:text-destructive"
                >
                  <X className="w-4 h-4" />
                  <span>Start New Chat</span>
                </Button>
              </CardContent>
            </Card>

            {/* Chatbot Info */}
            <Card className="border-0 shadow-lg">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg flex items-center space-x-2">
                  <div className="w-2 h-2 bg-primary rounded-full"></div>
                  <span>Chatbot Details</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-muted/30">
                    <span className="text-sm text-muted-foreground block mb-1">Created</span>
                    <p className="font-medium text-sm">{new Date(chatbot.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/30">
                    <span className="text-sm text-muted-foreground block mb-1">Webhook URL</span>
                    <p className="font-medium text-xs break-all leading-relaxed">{chatbot.webhook_url}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/30">
                    <span className="text-sm text-muted-foreground block mb-1">Status</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${chatbot.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                      <p className="font-medium text-sm">{chatbot.is_active ? 'Active' : 'Inactive'}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
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
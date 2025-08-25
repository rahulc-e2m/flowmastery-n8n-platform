import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import ChatInterface from '@/components/ChatInterface'
import { 
  Bot, 
  Plus, 
  Search, 
  Settings, 
  Play, 
  Pause, 
  MessageSquare,
  Users,
  Clock,
  TrendingUp,
  Copy,
  ExternalLink,
  Filter
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Chatbot {
  id: string
  name: string
  description: string
  webhookUrl: string
  status: 'active' | 'inactive' | 'testing'
  type: 'support' | 'sales' | 'faq' | 'custom'
  analytics: {
    totalMessages: number
    activeUsers: number
    avgResponseTime: string
    satisfactionRate: number
  }
  lastUpdated: string
  features: string[]
}

const ChatbotsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedChatbot, setSelectedChatbot] = useState<Chatbot | null>(null)
  const [showChat, setShowChat] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [newChatbot, setNewChatbot] = useState({
    name: '',
    description: '',
    type: 'support' as 'support' | 'sales' | 'faq' | 'custom',
    webhookUrl: ''
  })

  const [chatbots] = useState<Chatbot[]>([
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
  ])

  const typeColors = {
    support: 'success',
    sales: 'warning', 
    faq: 'default',
    custom: 'secondary'
  } as const

  const statusColors = {
    active: 'success',
    inactive: 'secondary',
    testing: 'warning'
  } as const

  const filteredChatbots = chatbots.filter(bot => {
    const matchesSearch = bot.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         bot.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || bot.type === filterType
    return matchesSearch && matchesFilter
  })

  const copyWebhook = (url: string) => {
    navigator.clipboard.writeText(url)
  }

  const handleTestChat = (chatbot: Chatbot) => {
    setSelectedChatbot(chatbot)
    setShowChat(true)
  }

  const handleCreateChatbot = () => {
    // Validation would go here
    const newBot: Chatbot = {
      id: Date.now().toString(),
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
      features: []
    }
    
    // In real app, this would be added to state/API
    setShowAddModal(false)
    setNewChatbot({ name: '', description: '', type: 'support', webhookUrl: '' })
    
    // Auto-open chat for new chatbot
    handleTestChat(newBot)
  }

  const totalStats = {
    totalMessages: chatbots.reduce((sum, bot) => sum + bot.analytics.totalMessages, 0),
    activeUsers: chatbots.reduce((sum, bot) => sum + bot.analytics.activeUsers, 0),
    avgSatisfaction: chatbots.reduce((sum, bot) => sum + bot.analytics.satisfactionRate, 0) / chatbots.length
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Bot className="h-8 w-8 text-primary" />
            AI Chatbots
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage and deploy intelligent conversational agents
          </p>
        </div>
        
        <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
          <DialogTrigger asChild>
            <Button variant="gradient" className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              New Chatbot
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Chatbot</DialogTitle>
              <DialogDescription>
                Set up a new AI chatbot for your workflows
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Chatbot Name</label>
                <Input 
                  placeholder="Enter chatbot name"
                  value={newChatbot.name}
                  onChange={(e) => setNewChatbot({...newChatbot, name: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Textarea 
                  placeholder="Describe your chatbot's purpose"
                  value={newChatbot.description}
                  onChange={(e) => setNewChatbot({...newChatbot, description: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Type</label>
                <Select 
                  value={newChatbot.type} 
                  onValueChange={(value: any) => setNewChatbot({...newChatbot, type: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="support">Support</SelectItem>
                    <SelectItem value="sales">Sales</SelectItem>
                    <SelectItem value="faq">FAQ</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Webhook URL</label>
                <Input 
                  placeholder="https://your-n8n-instance.com/webhook/..."
                  value={newChatbot.webhookUrl}
                  onChange={(e) => setNewChatbot({...newChatbot, webhookUrl: e.target.value})}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddModal(false)}>
                Cancel
              </Button>
              <Button variant="gradient" onClick={handleCreateChatbot}>
                Create Chatbot
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search chatbots..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="flex gap-2">
          {['all', 'support', 'sales', 'faq'].map((type) => (
            <Button
              key={type}
              variant={filterType === type ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterType(type)}
              className="capitalize"
            >
              {type}
            </Button>
          ))}
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalStats.totalMessages.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Total Messages</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-success-500/10 rounded-lg">
                <Users className="h-6 w-6 text-success-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalStats.activeUsers}</div>
                <div className="text-sm text-muted-foreground">Active Users</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-warning-500/10 rounded-lg">
                <TrendingUp className="h-6 w-6 text-warning-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalStats.avgSatisfaction.toFixed(1)}%</div>
                <div className="text-sm text-muted-foreground">Avg Satisfaction</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chatbots Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredChatbots.map((chatbot) => (
          <Card key={chatbot.id} className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <Badge variant={typeColors[chatbot.type]} className="capitalize">
                    {chatbot.type}
                  </Badge>
                  <Badge 
                    variant={statusColors[chatbot.status]}
                    className={cn(
                      "flex items-center gap-1",
                      chatbot.status === 'active' && "animate-pulse"
                    )}
                  >
                    <div className="w-2 h-2 rounded-full bg-current" />
                    {chatbot.status}
                  </Badge>
                </div>
                
                <div className="flex gap-1">
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    className="h-8 w-8"
                    onClick={() => handleTestChat(chatbot)}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-8 w-8">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <CardTitle className="text-xl">{chatbot.name}</CardTitle>
              <CardDescription>{chatbot.description}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Webhook URL */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Webhook URL</label>
                <div className="flex gap-2">
                  <Input 
                    value={chatbot.webhookUrl} 
                    readOnly 
                    className="text-xs"
                  />
                  <Button 
                    size="icon" 
                    variant="outline"
                    onClick={() => copyWebhook(chatbot.webhookUrl)}
                    className="shrink-0"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Features */}
              <div className="flex flex-wrap gap-1">
                {chatbot.features.map((feature, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {feature}
                  </Badge>
                ))}
              </div>

              {/* Analytics */}
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="flex items-center gap-2 text-sm">
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  <span>{chatbot.analytics.totalMessages.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span>{chatbot.analytics.activeUsers}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>{chatbot.analytics.avgResponseTime}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <span>{chatbot.analytics.satisfactionRate}%</span>
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">
                Updated {chatbot.lastUpdated}
              </span>
              <Button variant="outline" size="sm" className="flex items-center gap-2">
                View Analytics
                <ExternalLink className="h-3 w-3" />
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {filteredChatbots.length === 0 && (
        <div className="text-center py-12">
          <Bot className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No chatbots found</h3>
          <p className="text-muted-foreground mb-4">
            {searchTerm || filterType !== 'all' 
              ? 'Try adjusting your search or filter criteria'
              : 'Create your first chatbot to get started'
            }
          </p>
          {!searchTerm && filterType === 'all' && (
            <Button variant="gradient" onClick={() => setShowAddModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Chatbot
            </Button>
          )}
        </div>
      )}

      {/* Chat Interface */}
      {selectedChatbot && (
        <ChatInterface
          chatbot={selectedChatbot}
          isOpen={showChat}
          onClose={() => {
            setShowChat(false)
            setIsFullscreen(false)
          }}
          isFullscreen={isFullscreen}
          onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
        />
      )}
    </div>
  )
}

export default ChatbotsPage
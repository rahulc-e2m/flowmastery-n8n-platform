import React, { useState, useEffect } from 'react';
import styles from './Homepage.module.css';
import { 
  FaRobot, 
  FaSearch, 
  FaChartLine, 
  FaUsers, 
  FaCalendarCheck,
  FaArrowRight,
  FaBolt,
  FaShieldAlt,
  FaCog,
  FaPlay,
  FaClock,
  FaEye,
  FaCheck,
  FaTimes,
  FaPause,
  FaSync
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

interface WorkflowStat {
  label: string;
  value: string;
  trend: number;
  isLoading?: boolean;
}

interface N8nMetrics {
  status: string;
  timestamp: string;
  response_time: number;
  connection_healthy: boolean;
  workflows: {
    total_workflows: number;
    active_workflows: number;
    inactive_workflows: number;
  };
  executions: {
    total_executions: number;
    success_executions: number;
    error_executions: number;
    success_rate: number;
    today_executions: number;
  };
  users: {
    total_users: number;
    admin_users: number;
    member_users: number;
  };
  system: {
    total_variables: number;
    total_tags: number;
  };
  derived_metrics: {
    time_saved_hours: number;
    activity_score: number;
    automation_efficiency: number;
    workflows_per_user: number;
    executions_per_workflow: number;
  };
}

const Homepage: React.FC = () => {
  const [activeWorkflow, setActiveWorkflow] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [n8nMetrics, setN8nMetrics] = useState<N8nMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [hasN8nConfig, setHasN8nConfig] = useState(false);
  const navigate = useNavigate();

  // Fetch n8n metrics directly - try metrics first, fall back to config check
  const fetchN8nData = async (useFastMetrics = true) => {
    setMetricsLoading(true);
    try {
      // Try to fetch metrics directly
      const metricsEndpoint = useFastMetrics ? 
        'http://localhost:8000/api/metrics/fast' : 
        'http://localhost:8000/api/metrics/dashboard';
      
      const metricsResponse = await fetch(metricsEndpoint);
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        if (metricsData.status === 'success') {
          setN8nMetrics(metricsData);
          setHasN8nConfig(true);
          return;
        }
      }
      
      // If direct metrics fetch failed, try checking config status
      try {
        const configResponse = await fetch('http://localhost:8000/api/config/n8n/status');
        if (configResponse.ok) {
          const configData = await configResponse.json();
          setHasN8nConfig(configData.configured && configData.connection_healthy);
        } else {
          setHasN8nConfig(false);
        }
      } catch (configError) {
        console.log('Config service not available, assuming not configured');
        setHasN8nConfig(false);
      }
    } catch (error) {
      console.log('Failed to fetch n8n metrics:', error);
      setHasN8nConfig(false);
    } finally {
      setMetricsLoading(false);
    }
  };

  useEffect(() => {
    setIsVisible(true);
    fetchN8nData();
    
    const interval = setInterval(() => {
      setActiveWorkflow((prev) => (prev + 1) % 4);
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const workflows = [
    {
      icon: <FaRobot />,
      title: "AI Chatbots",
      description: "Intelligent conversational agents for customer support",
      color: "#6366f1",
      gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    {
      icon: <FaSearch />,
      title: "SEO Auditor",
      description: "Comprehensive SEO analysis and optimization tools",
      color: "#10b981",
      gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    {
      icon: <FaChartLine />,
      title: "Lead Generation",
      description: "Automated lead capture and nurturing workflows",
      color: "#f59e0b",
      gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
    },
    {
      icon: <FaCalendarCheck />,
      title: "Meeting Summarizer",
      description: "AI-powered meeting notes and action items",
      color: "#8b5cf6",
      gradient: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
    }
  ];

  // Generate stats based on n8n metrics or loading state
  const generateStats = (): WorkflowStat[] => {
    if (metricsLoading) {
      // Show loading state with placeholders
      return [
        { label: "Active Workflows", value: "---", trend: 0, isLoading: true },
        { label: "Executions Today", value: "---", trend: 0, isLoading: true },
        { label: "Time Saved", value: "---", trend: 0, isLoading: true },
        { label: "Success Rate", value: "---", trend: 0, isLoading: true }
      ];
    }
    
    if (n8nMetrics && hasN8nConfig) {
      // Calculate proper trends based on actual data
      const successTrend = n8nMetrics.executions.success_rate > 50 ? Math.min(n8nMetrics.executions.success_rate / 10, 10) : -5;
      const executionTrend = n8nMetrics.executions.today_executions > 0 ? 8 : -2;
      
      return [
        { 
          label: "Active Workflows", 
          value: n8nMetrics.workflows.active_workflows.toString(), 
          trend: Math.round((n8nMetrics.workflows.active_workflows / Math.max(1, n8nMetrics.workflows.total_workflows)) * 100),
          isLoading: false 
        },
        { 
          label: "Total Workflows", 
          value: n8nMetrics.workflows.total_workflows.toLocaleString(), 
          trend: 12,
          isLoading: false 
        },
        { 
          label: "Today's Executions", 
          value: n8nMetrics.executions.today_executions > 0 ? 
                 n8nMetrics.executions.today_executions.toLocaleString() : 
                 "None yet", 
          trend: executionTrend,
          isLoading: false 
        },
        { 
          label: "Success Rate", 
          value: n8nMetrics.executions.total_executions > 0 ? 
                 `${n8nMetrics.executions.success_rate}%` : 
                 "N/A", 
          trend: successTrend,
          isLoading: false 
        }
      ];
    }
    
    // No connection - show placeholder message
    return [
      { label: "Active Workflows", value: "--", trend: 0, isLoading: false },
      { label: "Total Workflows", value: "--", trend: 0, isLoading: false },
      { label: "Today's Executions", value: "--", trend: 0, isLoading: false },
      { label: "Success Rate", value: "--", trend: 0, isLoading: false }
    ];
  };

  const stats = generateStats();

  return (
    <div className={`homepage ${isVisible ? 'visible' : ''}`}>
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <div className="gradient-orb orb-1"></div>
          <div className="gradient-orb orb-2"></div>
          <div className="gradient-orb orb-3"></div>
          <div className="grid-pattern"></div>
        </div>
        
        <nav className="navbar">
          <div className="nav-container">
            <div className="logo">
              <FaBolt className="logo-icon" />
              <span>WorkflowHub</span>
            </div>
            <div className="nav-links">
              <a href="#workflows">Workflows</a>
              <a href="#features">Features</a>
              <a href="#analytics">Analytics</a>
              <button className="nav-cta">Get Started</button>
            </div>
          </div>
        </nav>

        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              <span className="gradient-text">Centralize</span> Your
              <br />
              n8n Workflows
            </h1>
            <p className="hero-subtitle">
              One powerful platform to manage, execute, and monitor all your automation workflows. 
              From chatbots to SEO tools, everything in one place.
            </p>
            <div className="hero-buttons">
              <button 
                className="btn-primary" 
                onClick={() => document.getElementById('analytics')?.scrollIntoView({ behavior: 'smooth' })}
              >
                <FaEye /> View n8n Metrics
              </button>
              <button className="btn-secondary" onClick={() => document.getElementById('workflows')?.scrollIntoView({ behavior: 'smooth' })}>
                View Workflows <FaArrowRight />
              </button>
            </div>
            
            {/* n8n Status Badge */}
            <div className="n8n-status-badge">
              {metricsLoading ? (
                <span className="status-indicator loading">
                  <FaClock /> Checking n8n connection...
                </span>
              ) : hasN8nConfig ? (
                <span className="status-indicator connected">
                  <FaPlay /> n8n Connected • Live Data
                </span>
              ) : (
                <span className="status-indicator disconnected">
                  <FaCog /> Configure n8n for Live Metrics
                </span>
              )}
            </div>
          </div>
          
          <div className="hero-visual">
            <div className="workflow-carousel">
              {workflows.map((workflow, index) => (
                <div 
                  key={index}
                  className={`workflow-card ${activeWorkflow === index ? 'active' : ''}`}
                  style={{ '--card-color': workflow.color } as React.CSSProperties}
                >
                  <div className="card-icon">{workflow.icon}</div>
                  <h3>{workflow.title}</h3>
                  <p>{workflow.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-container">
          {stats.map((stat, index) => (
            <div key={index} className={`stat-card ${stat.isLoading ? 'loading' : ''}`}>
              {stat.isLoading ? (
                <>
                  <div className="stat-value skeleton">Loading...</div>
                  <div className="stat-label">{stat.label}</div>
                  <div className="stat-trend">
                    <FaClock className="loading-icon" /> Fetching...
                  </div>
                </>
              ) : (
                <>
                  <div className="stat-value">{stat.value}</div>
                  <div className="stat-label">{stat.label}</div>
                  <div className={`stat-trend ${stat.trend > 0 ? 'positive' : 'negative'}`}>
                    {stat.trend > 0 ? '↑' : '↓'} {Math.abs(stat.trend)}%
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Detailed n8n Metrics Section */}
      {hasN8nConfig && n8nMetrics && (
        <section className="n8n-metrics-section" id="analytics">
          <div className="section-header">
            <h2><FaRobot /> Live n8n Instance Metrics</h2>
            <p>Real-time insights from your automation workflows</p>
            <div className="metrics-refresh">
              <button onClick={() => fetchN8nData(true)} className="refresh-btn">
                <FaSync className={metricsLoading ? 'spinning' : ''} /> Fast Refresh
              </button>
              <button onClick={() => fetchN8nData(false)} className="refresh-btn detailed">
                <FaChartLine /> Full Details
              </button>
              <span className="last-updated">
                Last updated: {new Date(n8nMetrics.timestamp).toLocaleTimeString()} • Response: {n8nMetrics.response_time}s
              </span>
            </div>
          </div>

          <div className="metrics-grid">
            {/* Workflow Overview */}
            <div className="metric-card workflows-card">
              <div className="metric-header">
                <h3><FaRobot /> Workflow Overview</h3>
                <div className="metric-status healthy">
                  <FaCheck /> {n8nMetrics.workflows.total_workflows} Total
                </div>
              </div>
              <div className="metric-content">
                <div className="workflow-breakdown">
                  <div className="workflow-stat active">
                    <FaPlay />
                    <div>
                      <span className="count">{n8nMetrics.workflows.active_workflows}</span>
                      <span className="label">Active</span>
                    </div>
                  </div>
                  <div className="workflow-stat inactive">
                    <FaPause />
                    <div>
                      <span className="count">{n8nMetrics.workflows.inactive_workflows}</span>
                      <span className="label">Inactive</span>
                    </div>
                  </div>
                </div>
                <div className="metric-footer">
                  <span>Response time: {n8nMetrics.response_time}s</span>
                </div>
              </div>
            </div>

            {/* Execution Analytics */}
            <div className="metric-card executions-card">
              <div className="metric-header">
                <h3><FaChartLine /> Execution Analytics</h3>
                <div className="metric-status success">
                  <FaCheck /> {n8nMetrics.executions.success_rate}% Success Rate
                </div>
              </div>
              <div className="metric-content">
                <div className="execution-breakdown">
                  <div className="execution-bar">
                    <div 
                      className="execution-fill success"
                      style={{ 
                        width: `${(n8nMetrics.executions.success_executions / n8nMetrics.executions.total_executions) * 100}%` 
                      }}
                    ></div>
                  </div>
                  <div className="execution-stats">
                    <div className="stat success">
                      <span className="count">{n8nMetrics.executions.success_executions.toLocaleString()}</span>
                      <span className="label">Successful</span>
                    </div>
                    <div className="stat error">
                      <span className="count">{n8nMetrics.executions.error_executions.toLocaleString()}</span>
                      <span className="label">Failed</span>
                    </div>
                  </div>
                </div>
                <div className="metric-footer">
                  <span>Total: {n8nMetrics.executions.total_executions.toLocaleString()} executions</span>
                </div>
              </div>
            </div>

            {/* User & Team Info */}
            <div className="metric-card users-card">
              <div className="metric-header">
                <h3><FaUsers /> Team & Users</h3>
                <div className="metric-status info">
                  <FaUsers /> {n8nMetrics.users.total_users} Total Users
                </div>
              </div>
              <div className="metric-content">
                <div className="user-breakdown">
                  <div className="user-stat admin">
                    <span className="count">{n8nMetrics.users.admin_users}</span>
                    <span className="label">Administrators</span>
                  </div>
                  <div className="user-stat member">
                    <span className="count">{n8nMetrics.users.member_users}</span>
                    <span className="label">Members</span>
                  </div>
                </div>
                <div className="metric-footer">
                  <span>Avg: {n8nMetrics.derived_metrics.workflows_per_user} workflows/user</span>
                </div>
              </div>
            </div>

            {/* System Performance */}
            <div className="metric-card system-card">
              <div className="metric-header">
                <h3><FaCog /> System Performance</h3>
                <div className="metric-status performance">
                  <FaBolt /> {n8nMetrics.derived_metrics.activity_score}/100 Activity Score
                </div>
              </div>
              <div className="metric-content">
                <div className="system-stats">
                  <div className="system-stat">
                    <span className="label">Variables</span>
                    <span className="value">{n8nMetrics.system.total_variables}</span>
                  </div>
                  <div className="system-stat">
                    <span className="label">Tags</span>
                    <span className="value">{n8nMetrics.system.total_tags}</span>
                  </div>
                  <div className="system-stat">
                    <span className="label">Efficiency</span>
                    <span className="value">{n8nMetrics.derived_metrics.automation_efficiency}%</span>
                  </div>
                </div>
                <div className="metric-footer">
                  <span>{n8nMetrics.derived_metrics.executions_per_workflow} avg executions/workflow</span>
                </div>
              </div>
            </div>
          </div>

          {/* Time Saved Highlight */}
          <div className="time-saved-highlight">
            <div className="time-saved-content">
              <div className="time-icon">
                <FaClock />
              </div>
              <div className="time-stats">
                <h3>Time Saved This Week</h3>
                <div className="time-value">{n8nMetrics.derived_metrics.time_saved_hours} Hours</div>
                <p>Your automation workflows have saved your team significant time this week</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Features Grid */}
      <section className="features-section" id="features">
        <div className="section-header">
          <h2>Everything You Need</h2>
          <p>Powerful features to streamline your workflow automation</p>
        </div>
        
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <FaCog />
            </div>
            <h3>Easy Integration</h3>
            <p>Connect all your n8n workflows with a single API endpoint</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <FaShieldAlt />
            </div>
            <h3>Secure & Reliable</h3>
            <p>Enterprise-grade security with 99.9% uptime guarantee</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <FaChartLine />
            </div>
            <h3>Real-time Analytics</h3>
            <p>Monitor performance and track execution metrics in real-time</p>
          </div>
          
          <div className="feature-card featured">
            <div className="feature-icon">
              <FaUsers />
            </div>
            <h3>Team Collaboration</h3>
            <p>Share workflows and collaborate with your team seamlessly</p>
            <button className="feature-cta">Learn More →</button>
          </div>
        </div>
      </section>

      {/* Workflow Categories */}
      <section className="categories-section" id="workflows">
        <div className="section-header">
          <h2>Workflow Categories</h2>
          <p>Explore our comprehensive collection of automation tools</p>
        </div>
        
        <div className="categories-container">
          {workflows.map((workflow, index) => (
            <div 
              key={index} 
              className="category-card"
              onMouseEnter={() => setActiveWorkflow(index)}
              onClick={() => { if (workflow.title === 'AI Chatbots') navigate('/chatbots'); }}
            >
              <div className="category-header" style={{ background: workflow.gradient }}>
                <div className="category-icon">{workflow.icon}</div>
              </div>
              <div className="category-content">
                <h3>{workflow.title}</h3>
                <p>{workflow.description}</p>
                <div className="category-stats">
                  <span>12 workflows</span>
                  <span>•</span>
                  <span>2.4k runs</span>
                </div>
                <button className="category-btn" onClick={() => { if (workflow.title === 'AI Chatbots') navigate('/chatbots'); }}>
                  Explore <FaArrowRight />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Streamline Your Workflows?</h2>
          <p>Join thousands of teams automating their work with WorkflowHub</p>
          <button className="cta-button">
            Start Free Trial
            <span className="button-glow"></span>
          </button>
        </div>
      </section>
    </div>
  );
};

export default Homepage; 
import React, { useState, useEffect } from 'react';
import './N8nMetricsDashboard.css';
import { 
  FaRobot, 
  FaPlay, 
  FaPause, 
  FaCheck, 
  FaTimes, 
  FaClock, 
  FaUsers, 
  FaChartLine,
  FaSync,
  FaCog,
  FaEye,
  FaEyeSlash
} from 'react-icons/fa';

interface MetricsData {
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

interface ConfigStatus {
  configured: boolean;
  connection_healthy?: boolean;
  instance_name?: string;
  api_url?: string;
  masked_api_key?: string;
  message?: string;
}

const N8nMetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [configStatus, setConfigStatus] = useState<ConfigStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  const fetchConfigStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/config/n8n/status');
      const data = await response.json();
      setConfigStatus(data);
      return data.configured;
    } catch (err) {
      console.error('Failed to fetch config status:', err);
      return false;
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/metrics/dashboard');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      setMetrics(null);
    }
  };

  const loadData = async () => {
    setLoading(true);
    const isConfigured = await fetchConfigStatus();
    
    if (isConfigured) {
      await fetchMetrics();
    }
    
    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="metrics-dashboard">
        <div className="loading-spinner">
          <FaSync className="spinning" />
          <p>Loading n8n metrics...</p>
        </div>
      </div>
    );
  }

  if (!configStatus?.configured) {
    return (
      <div className="metrics-dashboard">
        <div className="config-needed">
          <FaCog className="config-icon" />
          <h3>n8n Configuration Required</h3>
          <p>Configure your n8n instance to view metrics and analytics</p>
          <button className="config-button" onClick={() => setShowConfig(true)}>
            Configure n8n Instance
          </button>
        </div>
        {showConfig && (
          <N8nConfigModal 
            onClose={() => setShowConfig(false)} 
            onSuccess={() => {
              setShowConfig(false);
              loadData();
            }} 
          />
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div className="metrics-dashboard">
        <div className="error-state">
          <FaTimes className="error-icon" />
          <h3>Failed to Load Metrics</h3>
          <p>{error}</p>
          <button className="retry-button" onClick={handleRefresh}>
            <FaSync /> Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="metrics-dashboard">
        <div className="no-data">
          <FaChartLine className="no-data-icon" />
          <h3>No Metrics Available</h3>
          <p>Unable to retrieve metrics from your n8n instance</p>
        </div>
      </div>
    );
  }

  return (
    <div className="metrics-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-info">
          <h2>
            <FaRobot /> n8n Instance Metrics
          </h2>
          <p>
            {configStatus?.instance_name} • 
            <span className={`status ${metrics.connection_healthy ? 'healthy' : 'unhealthy'}`}>
              {metrics.connection_healthy ? 'Connected' : 'Disconnected'}
            </span>
          </p>
        </div>
        <div className="header-actions">
          <button 
            className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <FaSync className={refreshing ? 'spinning' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          <button className="config-btn" onClick={() => setShowConfig(true)}>
            <FaCog /> Settings
          </button>
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="metrics-grid">
        {/* Key Stats Cards */}
        <div className="stat-card workflows">
          <div className="stat-icon">
            <FaRobot />
          </div>
          <div className="stat-content">
            <h3>{metrics.workflows.total_workflows}</h3>
            <p>Total Workflows</p>
            <div className="stat-details">
              <span className="active">
                <FaPlay /> {metrics.workflows.active_workflows} Active
              </span>
              <span className="inactive">
                <FaPause /> {metrics.workflows.inactive_workflows} Inactive
              </span>
            </div>
          </div>
        </div>

        <div className="stat-card executions">
          <div className="stat-icon">
            <FaChartLine />
          </div>
          <div className="stat-content">
            <h3>{metrics.executions.today_executions}</h3>
            <p>Executions Today</p>
            <div className="stat-details">
              <span className="success">
                <FaCheck /> {metrics.executions.success_rate}% Success Rate
              </span>
            </div>
          </div>
        </div>

        <div className="stat-card time-saved">
          <div className="stat-icon">
            <FaClock />
          </div>
          <div className="stat-content">
            <h3>{metrics.derived_metrics.time_saved_hours}h</h3>
            <p>Time Saved</p>
            <div className="stat-details">
              <span>Last 7 days</span>
            </div>
          </div>
        </div>

        <div className="stat-card users">
          <div className="stat-icon">
            <FaUsers />
          </div>
          <div className="stat-content">
            <h3>{metrics.users.total_users}</h3>
            <p>Total Users</p>
            <div className="stat-details">
              <span>{metrics.users.admin_users} Admins, {metrics.users.member_users} Members</span>
            </div>
          </div>
        </div>

        {/* Detailed Execution Stats */}
        <div className="detail-card execution-breakdown">
          <h4>Execution Breakdown (Last 7 Days)</h4>
          <div className="execution-stats">
            <div className="execution-stat success">
              <div className="stat-bar">
                <div 
                  className="stat-fill success"
                  style={{ width: `${(metrics.executions.success_executions / metrics.executions.total_executions) * 100}%` }}
                ></div>
              </div>
              <div className="stat-info">
                <span className="count">{metrics.executions.success_executions}</span>
                <span className="label">Successful</span>
              </div>
            </div>
            
            <div className="execution-stat error">
              <div className="stat-bar">
                <div 
                  className="stat-fill error"
                  style={{ width: `${(metrics.executions.error_executions / metrics.executions.total_executions) * 100}%` }}
                ></div>
              </div>
              <div className="stat-info">
                <span className="count">{metrics.executions.error_executions}</span>
                <span className="label">Failed</span>
              </div>
            </div>

            <div className="total-executions">
              Total: {metrics.executions.total_executions} executions
            </div>
          </div>
        </div>

        {/* System Overview */}
        <div className="detail-card system-overview">
          <h4>System Overview</h4>
          <div className="system-stats">
            <div className="system-stat">
              <span className="label">Variables</span>
              <span className="value">{metrics.system.total_variables}</span>
            </div>
            <div className="system-stat">
              <span className="label">Tags</span>
              <span className="value">{metrics.system.total_tags}</span>
            </div>
            <div className="system-stat">
              <span className="label">Workflows per User</span>
              <span className="value">{metrics.derived_metrics.workflows_per_user}</span>
            </div>
            <div className="system-stat">
              <span className="label">Executions per Workflow</span>
              <span className="value">{metrics.derived_metrics.executions_per_workflow}</span>
            </div>
            <div className="system-stat">
              <span className="label">Activity Score</span>
              <span className="value">{metrics.derived_metrics.activity_score}/100</span>
            </div>
            <div className="system-stat">
              <span className="label">Response Time</span>
              <span className="value">{metrics.response_time}s</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="dashboard-footer">
        <p>
          Last updated: {new Date(metrics.timestamp).toLocaleString()} • 
          Data refreshed automatically every 5 minutes
        </p>
      </div>

      {/* Config Modal */}
      {showConfig && (
        <N8nConfigModal 
          onClose={() => setShowConfig(false)} 
          onSuccess={() => {
            setShowConfig(false);
            loadData();
          }}
          currentConfig={configStatus}
        />
      )}
    </div>
  );
};

// Configuration Modal Component
interface N8nConfigModalProps {
  onClose: () => void;
  onSuccess: () => void;
  currentConfig?: ConfigStatus | null;
}

const N8nConfigModal: React.FC<N8nConfigModalProps> = ({ onClose, onSuccess, currentConfig }) => {
  const [apiUrl, setApiUrl] = useState(currentConfig?.api_url || '');
  const [apiKey, setApiKey] = useState('');
  const [instanceName, setInstanceName] = useState(currentConfig?.instance_name || 'My n8n Instance');
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const testConnection = async () => {
    if (!apiUrl || !apiKey) return;
    
    setTesting(true);
    setTestResult(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/config/n8n/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_url: apiUrl, api_key: apiKey, instance_name: instanceName })
      });
      
      const result = await response.json();
      setTestResult(result);
    } catch (err) {
      setTestResult({ connection: 'failed', message: 'Connection test failed' });
    }
    
    setTesting(false);
  };

  const saveConfiguration = async () => {
    if (!apiUrl || !apiKey) return;
    
    setSaving(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/config/n8n', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_url: apiUrl, api_key: apiKey, instance_name: instanceName })
      });
      
      if (response.ok) {
        onSuccess();
      } else {
        const error = await response.json();
        alert(`Failed to save configuration: ${JSON.stringify(error)}`);
      }
    } catch (err) {
      alert('Failed to save configuration');
    }
    
    setSaving(false);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="config-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Configure n8n Instance</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="form-group">
            <label>Instance Name</label>
            <input
              type="text"
              value={instanceName}
              onChange={e => setInstanceName(e.target.value)}
              placeholder="My n8n Instance"
            />
          </div>
          
          <div className="form-group">
            <label>API URL</label>
            <input
              type="url"
              value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
              placeholder="https://your-n8n-instance.com"
            />
            <small>Enter your n8n instance URL (without /api/v1)</small>
          </div>
          
          <div className="form-group">
            <label>API Key</label>
            <div className="api-key-input">
              <input
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder="Your n8n API key"
              />
              <button
                type="button"
                className="toggle-visibility"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>
            <small>Generate this in your n8n Settings → API Keys</small>
          </div>
          
          {testResult && (
            <div className={`test-result ${testResult.connection}`}>
              <p>{testResult.message}</p>
              {testResult.workflows_found !== undefined && (
                <p>Found {testResult.workflows_found} workflows</p>
              )}
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <button
            className="test-btn"
            onClick={testConnection}
            disabled={testing || !apiUrl || !apiKey}
          >
            {testing ? <FaSync className="spinning" /> : <FaCheck />}
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          
          <button
            className="save-btn"
            onClick={saveConfiguration}
            disabled={saving || !apiUrl || !apiKey}
          >
            {saving ? <FaSync className="spinning" /> : <FaCheck />}
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default N8nMetricsDashboard;

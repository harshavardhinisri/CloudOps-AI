import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  AlertCircle,
  Activity,
  Clock,
  CheckCircle,
  RefreshCw,
  Zap,
  TrendingDown,
  Users
} from 'lucide-react'
import IncidentFeed from './components/IncidentFeed'
import AIAnalysis from './components/AIAnalysis'
import RecommendedActions from './components/RecommendedActions'
import IncidentTimeline from './components/IncidentTimeline'

const API_BASE = import.meta.env.REACT_APP_API_URL || 'http://localhost:3001'

function App() {
  const [incidents, setIncidents] = useState([])
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Fetch incidents
  const fetchIncidents = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`${API_BASE}/api/incidents`)
      setIncidents(response.data || [])
      if (response.data?.length > 0 && !selectedIncident) {
        setSelectedIncident(response.data[0])
      }
    } catch (err) {
      console.error('Failed to fetch incidents:', err)
      setError('Failed to load incidents')
    } finally {
      setLoading(false)
    }
  }

  // Analyze selected incident
  const analyzeIncident = async () => {
    if (!selectedIncident) return
    
    try {
      setLoading(true)
      const response = await axios.post(
        `${API_BASE}/api/incidents/${selectedIncident.id}/analyze`
      )
      setSelectedIncident(response.data)
      setIncidents(prev => 
        prev.map(i => i.id === response.data.id ? response.data : i)
      )
    } catch (err) {
      console.error('Analysis failed:', err)
      setError('Failed to analyze incident')
    } finally {
      setLoading(false)
    }
  }

  // Simulate incident
  const simulateOutage = async () => {
    const types = ['db_timeout', 'redis_unavailable', 'http_spike', 'high_latency']
    const randomType = types[Math.floor(Math.random() * types.length)]
    
    try {
      setLoading(true)
      const response = await axios.post(`${API_BASE}/api/incidents`, {
        type: randomType,
        severity: 'high',
        message: `${randomType.replace('_', ' ').toUpperCase()} detected`,
        logs: generateSampleLogs(randomType)
      })
      
      const newIncident = response.data
      setIncidents(prev => [newIncident, ...prev])
      setSelectedIncident(newIncident)
      
      // Auto-analyze after creation
      setTimeout(() => analyzeIncident(), 1000)
    } catch (err) {
      console.error('Failed to create incident:', err)
      setError('Failed to simulate outage')
    } finally {
      setLoading(false)
    }
  }

  // Approve remediation
  const approveRemediation = async () => {
    if (!selectedIncident) return
    
    try {
      setLoading(true)
      const response = await axios.post(
        `${API_BASE}/api/incidents/${selectedIncident.id}/remediation/approve`
      )
      setSelectedIncident(response.data)
      setIncidents(prev => 
        prev.map(i => i.id === response.data.id ? response.data : i)
      )
    } catch (err) {
      console.error('Approval failed:', err)
      setError('Failed to approve remediation')
    } finally {
      setLoading(false)
    }
  }

  // Load incidents on mount
  useEffect(() => {
    fetchIncidents()
    const interval = setInterval(fetchIncidents, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">CloudOps AI</h1>
                <p className="text-sm text-slate-400">AI-Powered SRE Platform</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={simulateOutage}
                disabled={loading}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <AlertCircle className="w-4 h-4" />
                {loading ? 'Processing...' : 'Simulate Outage'}
              </button>
              
              <button
                onClick={fetchIncidents}
                disabled={loading}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-900 border border-red-700 text-red-100 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel: Incident Feed */}
          <div className="lg:col-span-1">
            <IncidentFeed
              incidents={incidents}
              selectedId={selectedIncident?.id}
              onSelect={setSelectedIncident}
              loading={loading}
            />
          </div>

          {/* Right Panels: Analysis and Timeline */}
          <div className="lg:col-span-2 space-y-6">
            {selectedIncident ? (
              <>
                <AIAnalysis
                  incident={selectedIncident}
                  onAnalyze={analyzeIncident}
                  loading={loading}
                />
                <RecommendedActions
                  incident={selectedIncident}
                  onApprove={approveRemediation}
                  loading={loading}
                />
                <IncidentTimeline incident={selectedIncident} />
              </>
            ) : (
              <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center">
                <Activity className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <p className="text-slate-400">No incidents yet. Click "Simulate Outage" to get started.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function generateSampleLogs(type) {
  const logs = {
    db_timeout: [
      'ERROR: Connection timeout on pool-1',
      'WARN: Retrying connection attempt 1/3',
      'WARN: Retrying connection attempt 2/3',
      'ERROR: Failed to acquire connection after 30s',
      'CRITICAL: Database unavailable - circuit breaker activated'
    ],
    redis_unavailable: [
      'WARN: Redis connection timeout',
      'ERROR: Cache service unavailable',
      'WARN: Falling back to slower query path',
      'ERROR: Multiple cache misses detected',
      'CRITICAL: Performance degradation - cache down for 120s'
    ],
    http_spike: [
      'WARN: Request queue depth: 50',
      'WARN: Request queue depth: 150',
      'ERROR: 503 Service Unavailable',
      'ERROR: Request timeout - server overloaded',
      'CRITICAL: 95th percentile latency at 2000ms'
    ],
    high_latency: [
      'WARN: P95 latency: 500ms',
      'WARN: P95 latency: 800ms',
      'ERROR: P95 latency: 1200ms',
      'WARN: Slow query detected - 5000ms',
      'CRITICAL: Customer facing latency SLA breach'
    ]
  }
  return logs[type] || logs.db_timeout
}

export default App

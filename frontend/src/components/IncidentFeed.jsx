import React from 'react'
import { AlertCircle, Clock, AlertTriangle } from 'lucide-react'

function IncidentFeed({ incidents, selectedId, onSelect, loading }) {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-900 border-red-700 text-red-100'
      case 'high':
        return 'bg-orange-900 border-orange-700 text-orange-100'
      case 'medium':
        return 'bg-yellow-900 border-yellow-700 text-yellow-100'
      default:
        return 'bg-slate-700 border-slate-600 text-slate-100'
    }
  }

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-600'
      case 'high':
        return 'bg-orange-600'
      case 'medium':
        return 'bg-yellow-600'
      default:
        return 'bg-slate-600'
    }
  }

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
      <div className="p-4 bg-slate-900 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-orange-500" />
          Incident Feed
        </h2>
      </div>

      <div className="overflow-y-auto max-h-96">
        {incidents.length === 0 ? (
          <div className="p-6 text-center text-slate-400">
            <p>No incidents yet</p>
          </div>
        ) : (
          incidents.map((incident) => (
            <button
              key={incident.id}
              onClick={() => onSelect(incident)}
              className={`w-full p-4 border-b border-slate-700 text-left transition-colors hover:bg-slate-700 ${
                selectedId === incident.id ? 'bg-slate-700 border-l-4 border-l-blue-600' : ''
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <span className={`px-2 py-1 rounded text-xs font-bold ${getSeverityBadge(incident.severity)}`}>
                  {incident.severity.toUpperCase()}
                </span>
                {incident.status === 'resolved' && (
                  <span className="text-green-400 text-xs font-semibold">✓ RESOLVED</span>
                )}
              </div>
              
              <p className="text-white font-medium text-sm mb-2 truncate">
                {incident.message}
              </p>
              
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(incident.created_at).toLocaleTimeString()}
                </div>
                {incident.analysis?.confidence && (
                  <div className="flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    {Math.round(incident.analysis.confidence * 100)}% confidence
                  </div>
                )}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}

export default IncidentFeed

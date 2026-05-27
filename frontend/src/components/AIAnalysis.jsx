import React from 'react'
import { Brain, Zap, TrendingDown, RotateCw } from 'lucide-react'

function AIAnalysis({ incident, onAnalyze, loading }) {
  const hasAnalysis = incident?.analysis && Object.keys(incident.analysis).length > 0

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
      <div className="p-4 bg-slate-900 border-b border-slate-700 flex items-center justify-between">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-500" />
          AI Analysis
        </h2>
        <button
          onClick={onAnalyze}
          disabled={loading || !incident}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded text-sm font-medium transition-colors flex items-center gap-2"
        >
          <Zap className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      <div className="p-6 space-y-4">
        {hasAnalysis ? (
          <>
            <div>
              <label className="text-sm font-semibold text-slate-300 block mb-2">
                Root Cause
              </label>
              <p className="text-white bg-slate-700 p-3 rounded">
                {incident.analysis.root_cause || 'Analyzing...'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-semibold text-slate-300 block mb-2">
                  Confidence
                </label>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-500 h-full transition-all"
                      style={{ width: `${(incident.analysis.confidence || 0) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-bold text-blue-400">
                    {Math.round((incident.analysis.confidence || 0) * 100)}%
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-300 block mb-2">
                  Impact
                </label>
                <p className="text-white font-semibold">
                  {incident.analysis.estimated_impact || 'Calculating...'}
                </p>
              </div>
            </div>

            {incident.analysis.affected_services && (
              <div>
                <label className="text-sm font-semibold text-slate-300 block mb-2">
                  Affected Services
                </label>
                <div className="flex flex-wrap gap-2">
                  {incident.analysis.affected_services.map((service, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-red-900 text-red-100 rounded-full text-xs font-medium"
                    >
                      {service}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {incident.analysis.logs_analyzed && (
              <div className="pt-2 border-t border-slate-700">
                <p className="text-xs text-slate-400">
                  Analyzed {incident.analysis.logs_analyzed} log entries
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="py-8 text-center">
            <Brain className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">Click "Analyze" to run AI analysis</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default AIAnalysis

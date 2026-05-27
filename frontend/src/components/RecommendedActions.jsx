import React from 'react'
import { CheckCircle, AlertTriangle } from 'lucide-react'

function RecommendedActions({ incident, onApprove, loading }) {
  const hasRemediation = incident?.recommended_action && incident.recommended_action.length > 0

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
      <div className="p-4 bg-slate-900 border-b border-slate-700 flex items-center justify-between">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-500" />
          Recommended Remediation
        </h2>
        {incident?.status !== 'resolved' && (
          <button
            onClick={onApprove}
            disabled={loading || !hasRemediation}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded font-medium transition-colors flex items-center gap-2"
          >
            <CheckCircle className="w-4 h-4" />
            {loading ? 'Approving...' : 'Approve & Execute'}
          </button>
        )}
      </div>

      <div className="p-6">
        {hasRemediation ? (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-semibold text-slate-300 block mb-2">
                Suggested Action
              </label>
              <p className="text-white bg-slate-700 p-4 rounded leading-relaxed">
                {incident.recommended_action}
              </p>
            </div>

            {incident.remediation?.status === 'approved' && (
              <div className="bg-green-900 border border-green-700 rounded p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-green-100">Remediation Approved</p>
                    <p className="text-sm text-green-200 mt-1">
                      Action executed. System is recovering...
                    </p>
                    {incident.remediation?.executed_at && (
                      <p className="text-xs text-green-300 mt-2">
                        Executed: {new Date(incident.remediation.executed_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {incident.analysis?.estimated_mttr && (
              <div className="bg-slate-700 p-3 rounded">
                <p className="text-sm text-slate-300">
                  <span className="font-semibold">Estimated MTTR:</span>{' '}
                  <span className="text-white font-bold">{incident.analysis.estimated_mttr}</span>
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 text-center">
            <AlertTriangle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">Waiting for AI analysis to generate recommendations</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default RecommendedActions

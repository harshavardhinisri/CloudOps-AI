import React from 'react'
import { Clock, CheckCircle, AlertCircle, Zap } from 'lucide-react'

function IncidentTimeline({ incident }) {
  const getEventIcon = (type) => {
    switch (type) {
      case 'created':
        return <AlertCircle className="w-4 h-4" />
      case 'analyzed':
        return <Zap className="w-4 h-4" />
      case 'remediation_approved':
        return <CheckCircle className="w-4 h-4" />
      case 'resolved':
        return <CheckCircle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  const getEventColor = (type) => {
    switch (type) {
      case 'created':
        return 'bg-red-900 text-red-100'
      case 'analyzed':
        return 'bg-blue-900 text-blue-100'
      case 'remediation_approved':
        return 'bg-yellow-900 text-yellow-100'
      case 'resolved':
        return 'bg-green-900 text-green-100'
      default:
        return 'bg-slate-700 text-slate-100'
    }
  }

  const timeline = incident?.timeline || [
    {
      type: 'created',
      timestamp: incident?.created_at,
      message: 'Incident detected'
    },
    ...(incident?.analysis ? [{
      type: 'analyzed',
      timestamp: incident?.analyzed_at,
      message: 'AI analysis completed'
    }] : []),
    ...(incident?.remediation?.approved ? [{
      type: 'remediation_approved',
      timestamp: incident?.remediation?.executed_at,
      message: 'Remediation approved and executed'
    }] : []),
    ...(incident?.status === 'resolved' ? [{
      type: 'resolved',
      timestamp: incident?.resolved_at,
      message: 'Incident marked resolved'
    }] : [])
  ]

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
      <div className="p-4 bg-slate-900 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Clock className="w-5 h-5 text-cyan-500" />
          Incident Timeline
        </h2>
      </div>

      <div className="p-6">
        <div className="space-y-4">
          {timeline.map((event, idx) => (
            <div key={idx} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className={`p-2 rounded-full ${getEventColor(event.type)}`}>
                  {getEventIcon(event.type)}
                </div>
                {idx < timeline.length - 1 && (
                  <div className="w-1 h-8 bg-slate-700 my-2"></div>
                )}
              </div>
              
              <div className="pt-2 flex-1">
                <p className="text-white font-semibold text-sm">
                  {event.message}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'Pending'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default IncidentTimeline

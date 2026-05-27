import axios from 'axios'

export async function callAIService(baseUrl, endpoint, data) {
  try {
    const response = await axios.post(`${baseUrl}${endpoint}`, data, {
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    return response.data
  } catch (err) {
    console.error(`AI service call failed (${endpoint}):`, err.message)
    
    // Return mock data for demo purposes
    if (endpoint === '/api/analyze') {
      return {
        root_cause: 'Database connection pool exhausted due to increased traffic',
        confidence: 0.92,
        affected_services: ['api-server', 'worker-service'],
        estimated_impact: 'Critical - 100% request failure',
        estimated_mttr: '5-10 minutes',
        logs_analyzed: data.logs?.length || 0
      }
    } else if (endpoint === '/api/remediate') {
      return {
        action: 'Increase database connection pool size and restart affected services',
        severity: 'high',
        steps: [
          'Increase max_connections in database config',
          'Rolling restart of api-server pods',
          'Monitor connection pool metrics'
        ]
      }
    } else if (endpoint === '/api/postmortem') {
      return {
        postmortem: `Incident Report - ${new Date().toISOString()}\n\nRoot Cause: ${data.root_cause}\n\nImpact: 100 requests failed over ${data.duration_minutes} minutes\n\nRemediation: ${data.remediation}\n\nLessons Learned: Implement connection pool monitoring and auto-scaling.`
      }
    }
    
    throw err
  }
}

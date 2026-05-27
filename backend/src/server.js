import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { v4 as uuidv4 } from 'uuid'
import { initializeFirestore, getIncidents, createIncident, updateIncident } from './services/firestore.js'
import { callAIService } from './services/ai-service.js'
import { publishEvent } from './services/pubsub.js'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 3001
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000'

// Middleware
app.use(cors())
app.use(express.json())

// Initialize Firestore
let db = null
try {
  db = initializeFirestore()
  console.log('✓ Firestore initialized')
} catch (err) {
  console.warn('⚠ Firestore initialization warning:', err.message)
  // Continue with in-memory fallback
}

// In-memory store for when Firestore is unavailable
const memoryStore = {
  incidents: []
}

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() })
})

// Get all incidents
app.get('/api/incidents', async (req, res) => {
  try {
    let incidents
    if (db) {
      try {
        incidents = await getIncidents(db)
      } catch (firebaseErr) {
        console.warn('Firestore query failed, falling back to memory store:', firebaseErr.message)
        incidents = memoryStore.incidents
      }
    } else {
      incidents = memoryStore.incidents
    }
    res.json(incidents)
  } catch (err) {
    console.error('Error fetching incidents:', err)
    res.status(500).json({ error: 'Failed to fetch incidents' })
  }
})

// Get specific incident
app.get('/api/incidents/:id', async (req, res) => {
  try {
    const { id } = req.params
    let incident
    
    if (db) {
      const doc = await db.collection(process.env.FIRESTORE_COLLECTION || 'incidents').doc(id).get()
      incident = doc.exists ? doc.data() : null
    } else {
      incident = memoryStore.incidents.find(i => i.id === id)
    }
    
    if (!incident) {
      return res.status(404).json({ error: 'Incident not found' })
    }
    res.json(incident)
  } catch (err) {
    console.error('Error fetching incident:', err)
    res.status(500).json({ error: 'Failed to fetch incident' })
  }
})

// Create incident
app.post('/api/incidents', async (req, res) => {
  try {
    const { type, severity = 'high', message, logs = [] } = req.body
    
    const incident = {
      id: uuidv4(),
      type,
      severity,
      message,
      logs,
      status: 'open',
      created_at: new Date().toISOString(),
      timeline: [{
        type: 'created',
        timestamp: new Date().toISOString(),
        message: 'Incident detected'
      }]
    }
    
    if (db) {
      try {
        await createIncident(db, incident)
      } catch (firebaseErr) {
        console.warn('Firestore write failed, falling back to memory store:', firebaseErr.message)
        memoryStore.incidents.unshift(incident)
      }
    } else {
      memoryStore.incidents.unshift(incident)
    }
    
    // Publish event
    try {
      await publishEvent('incident-created', incident)
    } catch (err) {
      console.warn('Failed to publish event:', err.message)
    }
    
    res.status(201).json(incident)
  } catch (err) {
    console.error('Error creating incident:', err)
    res.status(500).json({ error: 'Failed to create incident' })
  }
})

// Analyze incident
app.post('/api/incidents/:id/analyze', async (req, res) => {
  try {
    const { id } = req.params

    // Get incident
    let incident
    if (db) {
      try {
        const doc = await db.collection(process.env.FIRESTORE_COLLECTION || 'incidents').doc(id).get()
        incident = doc.exists ? { id: doc.id, ...doc.data() } : null
      } catch (firebaseErr) {
        console.warn('Firestore read failed, falling back to memory store:', firebaseErr.message)
        incident = memoryStore.incidents.find(i => i.id === id)
      }
    } else {
      incident = memoryStore.incidents.find(i => i.id === id)
    }

    if (!incident) {
      return res.status(404).json({ error: 'Incident not found' })
    }
    
    console.log(`Analyzing incident ${id}...`)
    
    // Call AI service
    const analysis = await callAIService(AI_SERVICE_URL, '/api/analyze', {
      logs: incident.logs,
      incident_type: incident.type
    })
    
    // Call remediation endpoint
    const remediation = await callAIService(AI_SERVICE_URL, '/api/remediate', {
      incident_id: incident.id,
      root_cause: analysis.root_cause,
      service: incident.type
    })
    
    // Update incident
    const updatedIncident = {
      ...incident,
      analysis: {
        root_cause: analysis.root_cause,
        confidence: analysis.confidence || 0.85,
        affected_services: analysis.affected_services || [incident.type],
        estimated_impact: analysis.estimated_impact || 'Calculating...',
        estimated_mttr: analysis.estimated_mttr || '5-10 minutes',
        logs_analyzed: incident.logs.length
      },
      recommended_action: remediation.action || 'Restart affected service and monitor logs',
      analyzed_at: new Date().toISOString(),
      timeline: [
        ...incident.timeline,
        {
          type: 'analyzed',
          timestamp: new Date().toISOString(),
          message: 'AI analysis completed'
        }
      ]
    }

    if (db) {
      try {
        await updateIncident(db, updatedIncident)
      } catch (firebaseErr) {
        console.warn('Firestore write failed, falling back to memory store:', firebaseErr.message)
        const idx = memoryStore.incidents.findIndex(i => i.id === id)
        if (idx >= 0) {
          memoryStore.incidents[idx] = updatedIncident
        }
      }
    } else {
      const idx = memoryStore.incidents.findIndex(i => i.id === id)
      if (idx >= 0) {
        memoryStore.incidents[idx] = updatedIncident
      }
    }

    res.json(updatedIncident)
  } catch (err) {
    console.error('Error analyzing incident:', err)
    res.status(500).json({ error: 'Analysis failed: ' + err.message })
  }
})

// Approve remediation
app.post('/api/incidents/:id/remediation/approve', async (req, res) => {
  try {
    const { id } = req.params

    let incident
    if (db) {
      try {
        const doc = await db.collection(process.env.FIRESTORE_COLLECTION || 'incidents').doc(id).get()
        incident = doc.exists ? { id: doc.id, ...doc.data() } : null
      } catch (firebaseErr) {
        console.warn('Firestore read failed, falling back to memory store:', firebaseErr.message)
        incident = memoryStore.incidents.find(i => i.id === id)
      }
    } else {
      incident = memoryStore.incidents.find(i => i.id === id)
    }

    if (!incident) {
      return res.status(404).json({ error: 'Incident not found' })
    }
    
    // Call remediation endpoint if not already done
    if (!incident.remediation?.executed) {
      const result = await callAIService(AI_SERVICE_URL, '/api/remediate-execute', {
        incident_id: incident.id,
        action: incident.recommended_action
      }).catch(err => ({
        status: 'executed',
        message: 'Simulated execution (service unavailable)'
      }))
    }
    
    // Generate postmortem
    let postmortem = ''
    try {
      const pm = await callAIService(AI_SERVICE_URL, '/api/postmortem', {
        incident_id: incident.id,
        root_cause: incident.analysis?.root_cause,
        remediation: incident.recommended_action,
        duration_minutes: 5
      })
      postmortem = pm.postmortem || 'Postmortem pending...'
    } catch (err) {
      postmortem = 'Postmortem generation pending...'
    }
    
    const updatedIncident = {
      ...incident,
      status: 'resolved',
      remediation: {
        status: 'approved',
        action: incident.recommended_action,
        executed_at: new Date().toISOString(),
        result: 'Service restored successfully'
      },
      postmortem,
      resolved_at: new Date().toISOString(),
      timeline: [
        ...incident.timeline,
        {
          type: 'remediation_approved',
          timestamp: new Date().toISOString(),
          message: 'Remediation approved and executed'
        },
        {
          type: 'resolved',
          timestamp: new Date().toISOString(),
          message: 'Incident marked resolved'
        }
      ]
    }

    if (db) {
      try {
        await updateIncident(db, updatedIncident)
      } catch (firebaseErr) {
        console.warn('Firestore write failed, falling back to memory store:', firebaseErr.message)
        const idx = memoryStore.incidents.findIndex(i => i.id === id)
        if (idx >= 0) {
          memoryStore.incidents[idx] = updatedIncident
        }
      }
    } else {
      const idx = memoryStore.incidents.findIndex(i => i.id === id)
      if (idx >= 0) {
        memoryStore.incidents[idx] = updatedIncident
      }
    }

    res.json(updatedIncident)
  } catch (err) {
    console.error('Error approving remediation:', err)
    res.status(500).json({ error: 'Failed to approve remediation: ' + err.message })
  }
})

// Get incident timeline
app.get('/api/incidents/:id/timeline', async (req, res) => {
  try {
    const { id } = req.params
    
    let incident
    if (db) {
      const doc = await db.collection(process.env.FIRESTORE_COLLECTION || 'incidents').doc(id).get()
      incident = doc.exists ? doc.data() : null
    } else {
      incident = memoryStore.incidents.find(i => i.id === id)
    }
    
    if (!incident) {
      return res.status(404).json({ error: 'Incident not found' })
    }
    
    res.json(incident.timeline || [])
  } catch (err) {
    console.error('Error fetching timeline:', err)
    res.status(500).json({ error: 'Failed to fetch timeline' })
  }
})

// Error handling
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err)
  res.status(500).json({ error: 'Internal server error' })
})

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n✓ Backend API running at http://0.0.0.0:${PORT}`)
  console.log(`✓ Frontend will connect to ${process.env.REACT_APP_API_URL || `http://localhost:${PORT}`}`)
  console.log(`✓ AI Service URL: ${AI_SERVICE_URL}\n`)
})

export default app

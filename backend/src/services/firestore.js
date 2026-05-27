import admin from 'firebase-admin'
import dotenv from 'dotenv'

dotenv.config()

let db = null

export function initializeFirestore() {
  try {
    // Check for credentials in environment
    if (!admin.apps.length) {
      if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
        admin.initializeApp({
          projectId: process.env.GOOGLE_CLOUD_PROJECT
        })
      } else {
        console.warn('⚠ GOOGLE_APPLICATION_CREDENTIALS not set. Using Application Default Credentials.')
        admin.initializeApp({
          projectId: process.env.GOOGLE_CLOUD_PROJECT
        })
      }
    }
    
    db = admin.firestore()
    console.log('✓ Firestore initialized')
    return db
  } catch (err) {
    console.error('Failed to initialize Firestore:', err.message)
    throw err
  }
}

export async function getIncidents(database) {
  try {
    const collection = database.collection(process.env.FIRESTORE_COLLECTION || 'incidents')
    const snapshot = await collection.orderBy('created_at', 'desc').get()
    
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }))
  } catch (err) {
    console.error('Error fetching incidents:', err)
    throw err
  }
}

export async function createIncident(database, incident) {
  try {
    const collection = database.collection(process.env.FIRESTORE_COLLECTION || 'incidents')
    await collection.doc(incident.id).set(incident)
    return incident
  } catch (err) {
    console.error('Error creating incident:', err)
    throw err
  }
}

export async function updateIncident(database, incident) {
  try {
    const collection = database.collection(process.env.FIRESTORE_COLLECTION || 'incidents')
    const { id, ...data } = incident
    await collection.doc(id).set(data, { merge: true })
    return incident
  } catch (err) {
    console.error('Error updating incident:', err)
    throw err
  }
}

export async function getIncident(database, incidentId) {
  try {
    const collection = database.collection(process.env.FIRESTORE_COLLECTION || 'incidents')
    const doc = await collection.doc(incidentId).get()
    
    if (!doc.exists) {
      return null
    }
    
    return {
      id: doc.id,
      ...doc.data()
    }
  } catch (err) {
    console.error('Error getting incident:', err)
    throw err
  }
}

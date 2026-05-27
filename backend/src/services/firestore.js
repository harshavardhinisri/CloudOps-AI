import admin from 'firebase-admin'
import dotenv from 'dotenv'

dotenv.config()

let db = null

export function initializeFirestore() {
  try {
    // Check for credentials in environment
    if (!admin.apps.length) {
      admin.initializeApp({
        projectId: process.env.GOOGLE_CLOUD_PROJECT
      })
      console.log('Firebase Admin initialized with project:', process.env.GOOGLE_CLOUD_PROJECT)
    }

    // Get Firestore instance - explicitly use default database
    db = admin.firestore()

    // Verify connection by attempting a simple query
    db.collection('_test').limit(1).get().then(() => {
      console.log('✓ Firestore connection verified')
    }).catch(err => {
      console.warn('⚠ Firestore connection test failed:', err.message)
    })

    return db
  } catch (err) {
    console.error('Failed to initialize Firestore:', err.message)
    throw err
  }
}

export async function getIncidents(database) {
  try {
    const collection = database.collection(process.env.FIRESTORE_COLLECTION || 'incidents')
    // First try with orderBy, if it fails fall back to no ordering
    try {
      const snapshot = await collection.orderBy('created_at', 'desc').get()
      return snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }))
    } catch (orderErr) {
      console.warn('orderBy query failed, trying without ordering:', orderErr.message)
      // Fallback to simple query without ordering
      const snapshot = await collection.get()
      return snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }))
    }
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

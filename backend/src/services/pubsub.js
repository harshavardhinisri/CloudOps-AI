import { PubSub } from '@google-cloud/pubsub'

let pubsub = null
let topic = null

export function initializePubSub() {
  try {
    pubsub = new PubSub({
      projectId: process.env.GOOGLE_CLOUD_PROJECT
    })
    console.log('✓ Pub/Sub initialized')
  } catch (err) {
    console.warn('⚠ Pub/Sub initialization warning:', err.message)
  }
}

export async function publishEvent(eventType, data) {
  try {
    if (!pubsub) {
      initializePubSub()
    }
    
    const topicName = process.env.PUBSUB_TOPIC || 'incident-events'
    const topic = pubsub.topic(topicName)
    
    const message = {
      json: {
        event_type: eventType,
        timestamp: new Date().toISOString(),
        data
      }
    }
    
    const messageId = await topic.publish(Buffer.from(JSON.stringify(message.json)))
    console.log(`Published event ${eventType} with message ID: ${messageId}`)
    return messageId
  } catch (err) {
    console.warn('Failed to publish to Pub/Sub:', err.message)
    // Don't throw - continue with local processing
    return null
  }
}

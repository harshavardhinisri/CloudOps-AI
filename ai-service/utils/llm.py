import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_llm_response(prompt: str) -> Optional[str]:
    """
    Get response from LLM (Vertex AI or other provider)
    Defaults to mock response for demo
    """
    provider = os.getenv('LLM_PROVIDER', 'vertex_ai')
    
    try:
        if provider == 'vertex_ai':
            return get_vertex_ai_response(prompt)
        elif provider == 'openrouter':
            return get_openrouter_response(prompt)
        else:
            return get_mock_response(prompt)
    except Exception as e:
        logger.warning(f'LLM call failed: {str(e)}, using mock response')
        return get_mock_response(prompt)

def get_vertex_ai_response(prompt: str) -> str:
    """
    Call Vertex AI Gemini Flash
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        project = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        model_name = os.getenv('VERTEX_AI_MODEL', 'gemini-1.5-flash-001')
        
        vertexai.init(project=project, location=location)
        
        model = GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        return response.text if response else None
    except ImportError:
        logger.warning('vertexai package not installed, using mock')
        return get_mock_response(prompt)
    except Exception as e:
        logger.error(f'Vertex AI error: {str(e)}')
        raise

def get_openrouter_response(prompt: str) -> str:
    """
    Call OpenRouter API
    """
    try:
        import requests
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError('OPENROUTER_API_KEY not set')
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': os.getenv('OPENROUTER_MODEL', 'mistral/mistral-7b-instruct:free'),
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f'OpenRouter error: {response.status_code}')
    except Exception as e:
        logger.error(f'OpenRouter error: {str(e)}')
        raise

def get_mock_response(prompt: str) -> str:
    """
    Generate mock response for demo/testing
    """
    if 'root cause' in prompt.lower():
        return 'Database connection pool exhaustion due to increased traffic and connection timeouts'
    elif 'remediation' in prompt.lower():
        return '''1. Increase database connection pool from 50 to 100
2. Rolling restart of affected api-server pods
3. Monitor connection pool metrics for 10 minutes
4. Gradually scale down if metrics normalize'''
    elif 'postmortem' in prompt.lower():
        return '''Incident Postmortem Report

Timeline:
- 14:30 UTC: Incident detected via alert
- 14:32 UTC: Root cause identified (connection pool exhaustion)
- 14:35 UTC: Remediation applied (pool increase and restart)
- 14:42 UTC: Service fully recovered

Impact: 500 affected users, ~7 minutes downtime

Root Cause: Database connection pool size (50) insufficient for peak traffic
Remediation: Increased to 100 connections, deployed connection monitoring

Prevention: Implement automated horizontal scaling based on pool utilization
Follow-up: Review capacity planning for database tier'''
    else:
        return 'Service issue detected and analyzed. Remediation recommended.'

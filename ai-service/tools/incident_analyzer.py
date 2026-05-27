def analyze_incident(incident_data: dict) -> dict:
    """
    Analyze incident characteristics
    """
    return {
        'type': incident_data.get('type', 'unknown'),
        'severity': incident_data.get('severity', 'medium'),
        'duration': 0,
        'services_affected': 1,
        'estimated_users_impacted': 100
    }

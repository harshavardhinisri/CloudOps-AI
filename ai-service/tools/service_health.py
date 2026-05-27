def get_service_health(service: str) -> dict:
    """
    Get current health status of a service (simulation)
    """
    return {
        'service': service,
        'status': 'degraded',
        'cpu_usage': 87,
        'memory_usage': 92,
        'error_rate': 15.5,
        'latency_p95': 2500
    }

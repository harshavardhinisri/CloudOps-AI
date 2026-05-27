#!/usr/bin/env python3
"""
Local testing script for CloudOps AI - Google ADK implementation
Run this to verify the entire multi-agent system before Cloud Run deployment
"""

import asyncio
import json
import sys
from datetime import datetime

# Color codes for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

async def test_imports():
    """Test all critical imports"""
    print_header("Testing Critical Imports")

    tests_passed = 0
    tests_failed = 0

    # Test FastAPI
    try:
        from fastapi import FastAPI
        print_success("FastAPI imported")
        tests_passed += 1
    except ImportError as e:
        print_error(f"FastAPI import failed: {e}")
        tests_failed += 1

    # Test Pydantic
    try:
        from pydantic import BaseModel
        print_success("Pydantic imported")
        tests_passed += 1
    except ImportError as e:
        print_error(f"Pydantic import failed: {e}")
        tests_failed += 1

    # Test Google ADK Agent
    try:
        from google.adk.agents import Agent
        print_success("google.adk.agents.Agent imported")
        tests_passed += 1
    except ImportError as e:
        print_error(f"Google ADK Agent import failed: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Test Google ADK Runner
    try:
        from google.adk.runners import InMemoryRunner
        print_success("google.adk.runners.InMemoryRunner imported")
        tests_passed += 1
    except ImportError as e:
        print_error(f"Google ADK Runner import failed: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Test Vertex AI
    try:
        from vertexai.generative_models import GenerativeModel
        print_success("vertexai.generative_models.GenerativeModel imported")
        tests_passed += 1
    except ImportError as e:
        print_warning(f"Vertex AI import failed (optional for local testing): {e}")

    # Test Hallucination Control
    try:
        from hallucination_control import HallucinationControlSystem
        print_success("HallucinationControlSystem imported")
        tests_passed += 1
    except ImportError as e:
        print_warning(f"Hallucination control import failed (will use fallback): {e}")

    return tests_passed, tests_failed

async def test_tool_functions():
    """Test tool functions"""
    print_header("Testing Tool Functions")

    from adk_agent import query_logs, get_service_health, get_remediation_options

    tests_passed = 0
    tests_failed = 0

    # Test query_logs
    try:
        result = query_logs("db_timeout", "high")
        data = json.loads(result)
        assert data["status"] == "success"
        assert len(data["logs"]) > 0
        print_success("query_logs('db_timeout', 'high') returned valid logs")
        print(f"    └─ Got {data['log_count']} logs")
        tests_passed += 1
    except Exception as e:
        print_error(f"query_logs failed: {e}")
        tests_failed += 1

    # Test get_service_health
    try:
        result = get_service_health("db_timeout")
        data = json.loads(result)
        assert "overall_status" in data
        assert "services" in data
        print_success("get_service_health('db_timeout') returned service status")
        print(f"    └─ Overall status: {data['overall_status']}")
        tests_passed += 1
    except Exception as e:
        print_error(f"get_service_health failed: {e}")
        tests_failed += 1

    # Test get_remediation_options
    try:
        result = get_remediation_options("connection_pool_exhaustion", '["api-server", "worker"]')
        data = json.loads(result)
        assert "primary_action" in data
        assert "steps" in data
        print_success("get_remediation_options returned remediation plan")
        print(f"    └─ Primary action: {data['primary_action'][:50]}...")
        tests_passed += 1
    except Exception as e:
        print_error(f"get_remediation_options failed: {e}")
        tests_failed += 1

    return tests_passed, tests_failed

async def test_agent_creation():
    """Test ADK agent creation"""
    print_header("Testing Google ADK Agent Creation")

    try:
        from google.adk.agents import Agent
        from google.adk.runners import InMemoryRunner
        from adk_agent import query_logs, get_service_health, get_remediation_options

        # Create test agent
        test_agent = Agent(
            name="test-analyzer",
            model="gemini-1.5-flash-001",
            instruction="You are a test analyst. Analyze the provided information.",
            tools=[
                {
                    "name": "query_logs",
                    "description": "Query incident logs",
                    "callable": query_logs
                },
                {
                    "name": "get_service_health",
                    "description": "Check service health",
                    "callable": get_service_health
                }
            ]
        )

        print_success("IncidentAnalysisAgent created successfully")
        print(f"    └─ Agent name: {test_agent.name}")
        print(f"    └─ Model: {test_agent.model}")
        print(f"    └─ Tools bound: {len(test_agent.tools)}")

        # Create runner
        runner = InMemoryRunner()
        print_success("InMemoryRunner created successfully")

        return 1, 0
    except Exception as e:
        print_error(f"Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

async def test_orchestrator():
    """Test the full orchestrator"""
    print_header("Testing IncidentResponseOrchestrator")

    try:
        from adk_agent import create_orchestrator, IncidentContext

        orchestrator = create_orchestrator()
        print_success("IncidentResponseOrchestrator created")

        # Create test incident context
        context = IncidentContext(
            incident_id="test-001",
            incident_type="db_timeout",
            logs=["ERROR: Connection timeout", "ERROR: Pool exhausted"],
            severity="high"
        )

        print_success("IncidentContext created")
        print(f"    └─ Incident ID: {context.incident_id}")
        print(f"    └─ Type: {context.incident_type}")
        print(f"    └─ Severity: {context.severity}")

        # Try to run analysis
        print_info("Starting incident analysis (this may take 5-10 seconds)...")
        result = await orchestrator.analyze_incident(context)

        if result["status"] == "success":
            print_success("Incident analysis completed successfully!")
            print(f"    └─ Root cause: {result['analysis'].get('root_cause', 'N/A')}")
            print(f"    └─ Confidence: {result['analysis'].get('confidence', 'N/A')}")
            print(f"    └─ Primary action: {result['remediation'].get('primary_action', 'N/A')[:50]}...")

            if "hallucination_report" in result:
                print(f"    └─ Safety check: {result['hallucination_report'].get('overall_safety', 'N/A')}")

            return 1, 0
        else:
            print_error(f"Analysis failed: {result.get('error_message', 'Unknown error')}")
            return 0, 1

    except Exception as e:
        print_error(f"Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

async def test_api_endpoints():
    """Test FastAPI endpoints"""
    print_header("Testing FastAPI Endpoints")

    try:
        from main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        tests_passed = 0
        tests_failed = 0

        # Test /health
        try:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            print_success("GET /health returned 200 OK")
            tests_passed += 1
        except Exception as e:
            print_error(f"GET /health failed: {e}")
            tests_failed += 1

        # Test /ready
        try:
            response = client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            print_success("GET /ready returned 200 OK")
            print(f"    └─ Status: {data.get('status')}")
            print(f"    └─ Orchestrator available: {data.get('orchestrator_available')}")
            print(f"    └─ Vertex AI available: {data.get('vertex_ai_available')}")
            print(f"    └─ Hallucination control: {data.get('hallucination_control_enabled')}")
            tests_passed += 1
        except Exception as e:
            print_error(f"GET /ready failed: {e}")
            tests_failed += 1

        # Test /api/info
        try:
            response = client.get("/api/info")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "CloudOps AI ADK Agent Service"
            print_success("GET /api/info returned 200 OK")
            tests_passed += 1
        except Exception as e:
            print_error(f"GET /api/info failed: {e}")
            tests_failed += 1

        # Test /api/analyze
        try:
            request_data = {
                "logs": ["ERROR: Connection timeout", "ERROR: Pool exhausted"],
                "incident_type": "db_timeout",
                "severity": "high",
                "incident_id": "test-api-001"
            }

            print_info("Sending POST /api/analyze request...")
            response = client.post("/api/analyze", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "analysis" in data
            assert "remediation" in data

            print_success("POST /api/analyze returned 200 OK")
            print(f"    └─ Incident ID: {data['incident_id']}")
            print(f"    └─ Root cause: {data['analysis'].get('root_cause', 'N/A')}")
            print(f"    └─ Remediation: {data['remediation'].get('primary_action', 'N/A')[:50]}...")
            tests_passed += 1
        except Exception as e:
            print_error(f"POST /api/analyze failed: {e}")
            tests_failed += 1

        return tests_passed, tests_failed

    except Exception as e:
        print_error(f"API endpoint testing failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

async def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*70}")
    print("  CloudOps AI - Local ADK Testing Suite")
    print("  Google ADK Multi-Agent Incident Response System")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}{RESET}\n")

    total_passed = 0
    total_failed = 0

    # Test 1: Imports
    passed, failed = await test_imports()
    total_passed += passed
    total_failed += failed

    # Test 2: Tool Functions
    passed, failed = await test_tool_functions()
    total_passed += passed
    total_failed += failed

    # Test 3: Agent Creation
    passed, failed = await test_agent_creation()
    total_passed += passed
    total_failed += failed

    # Test 4: Orchestrator
    passed, failed = await test_orchestrator()
    total_passed += passed
    total_failed += failed

    # Test 5: API Endpoints
    passed, failed = await test_api_endpoints()
    total_passed += passed
    total_failed += failed

    # Summary
    print_header("Test Summary")
    print(f"Total Tests Passed: {GREEN}{total_passed}{RESET}")
    print(f"Total Tests Failed: {RED}{total_failed}{RESET}")

    if total_failed == 0:
        print(f"\n{GREEN}🎉 All tests passed! Ready for Cloud Run deployment! 🎉{RESET}\n")
        return 0
    else:
        print(f"\n{RED}⚠️  Some tests failed. Please fix the issues before deploying.{RESET}\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

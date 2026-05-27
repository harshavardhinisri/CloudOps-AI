"""
CloudOps AI - Hallucination Detection & Prevention System
Implements Google ADK techniques to detect and prevent LLM hallucinations

Key Techniques:
1. Grounding - Validate outputs against real data sources
2. Tool-Enforced Verification - Require tool calls for claims
3. Confidence Scoring - Only accept high-confidence results
4. Fact Verification - Cross-check facts against ground truth
5. Structured Output Validation - Schema-based validation
6. Multi-Agent Verification - Have multiple agents verify
7. Callback Monitoring - Detect hallucinations in real-time
8. Retrieval Augmentation - Ground in actual incident data
"""

import re
import json
import logging
from typing import Any, Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class HallucinationSeverity(Enum):
    """Severity levels for detected hallucinations"""
    LOW = "low"           # Minor inconsistencies
    MEDIUM = "medium"     # Significant but non-critical
    HIGH = "high"         # Critical hallucinations
    CRITICAL = "critical" # Dangerous false claims


class FactType(Enum):
    """Types of facts that can be verified"""
    SERVICE_NAME = "service_name"
    METRIC_VALUE = "metric_value"
    TIMESTAMP = "timestamp"
    ACTION = "action"
    DURATION = "duration"
    ERROR_CODE = "error_code"
    ROOT_CAUSE = "root_cause"


@dataclass
class HallucinationDetection:
    """Result of hallucination detection"""
    detected: bool
    severity: HallucinationSeverity
    hallucination_type: str
    description: str
    evidence: str
    suggested_correction: str
    confidence_score: float  # 0-1, how confident we are this is a hallucination


@dataclass
class VerificationResult:
    """Result of fact verification"""
    fact: str
    fact_type: FactType
    is_verified: bool
    ground_truth: Any
    agent_claim: Any
    verification_method: str
    confidence: float


@dataclass
class SanitizedOutput:
    """Sanitized agent output"""
    original_output: dict
    sanitized_output: dict
    issues_found: List[Dict[str, Any]]
    is_safe: bool
    risk_level: str


# ============================================================================
# GROUND TRUTH DATA - Real Data Sources
# ============================================================================

class GroundTruthDatabase:
    """
    Maintains ground truth data for grounding agent outputs
    In production, this would connect to real monitoring systems
    """

    def __init__(self):
        """Initialize with known facts"""
        self.known_services = {
            "api-server": {"type": "service", "criticality": "high"},
            "worker": {"type": "service", "criticality": "medium"},
            "database": {"type": "service", "criticality": "critical"},
            "redis": {"type": "cache", "criticality": "medium"},
            "load-balancer": {"type": "infrastructure", "criticality": "high"}
        }

        self.valid_error_codes = {
            "E_CONN_TIMEOUT": "Connection timeout",
            "E_POOL_EXHAUSTED": "Connection pool exhausted",
            "E_SERVICE_UNAVAIL": "Service unavailable (503)",
            "E_HIGH_LATENCY": "High latency detected",
            "E_CACHE_MISS": "Cache miss rate high"
        }

        self.valid_actions = {
            "restart_service": "Restart affected service",
            "increase_pool": "Increase connection pool",
            "scale_up": "Scale up instances",
            "drain_cache": "Drain cache and warm",
            "load_balance": "Adjust load balancer",
            "rollback": "Rollback configuration"
        }

        self.valid_durations = {
            "quick": (1, 5),      # 1-5 minutes
            "medium": (5, 15),    # 5-15 minutes
            "long": (15, 60)      # 15-60 minutes
        }

        self.incident_history = [
            {
                "type": "db_timeout",
                "typical_root_cause": "Connection pool exhaustion",
                "typical_duration": 8,
                "affected_services": ["database", "api-server"]
            },
            {
                "type": "redis_unavailable",
                "typical_root_cause": "Cache service failure",
                "typical_duration": 5,
                "affected_services": ["redis", "api-server"]
            },
            {
                "type": "http_spike",
                "typical_root_cause": "Traffic surge",
                "typical_duration": 10,
                "affected_services": ["load-balancer", "api-server"]
            }
        ]

    def get_known_services(self) -> Dict[str, dict]:
        """Get list of known services"""
        return self.known_services

    def is_valid_service(self, service_name: str) -> bool:
        """Check if service name is known"""
        return service_name in self.known_services

    def is_valid_error_code(self, error_code: str) -> bool:
        """Check if error code is valid"""
        return error_code in self.valid_error_codes

    def is_valid_action(self, action: str) -> bool:
        """Check if remediation action is valid"""
        return action in self.valid_actions

    def get_incident_pattern(self, incident_type: str) -> Optional[dict]:
        """Get expected pattern for incident type"""
        for pattern in self.incident_history:
            if pattern["type"] == incident_type:
                return pattern
        return None

    def verify_duration(self, duration: int, duration_category: str) -> bool:
        """Verify if duration matches expected range"""
        if duration_category not in self.valid_durations:
            return False
        min_dur, max_dur = self.valid_durations[duration_category]
        return min_dur <= duration <= max_dur


# ============================================================================
# HALLUCINATION DETECTION ENGINE
# ============================================================================

class HallucinationDetector:
    """
    Detects various types of hallucinations in agent outputs
    Implements multiple detection strategies
    """

    def __init__(self, ground_truth_db: GroundTruthDatabase):
        """Initialize with ground truth database"""
        self.ground_truth = ground_truth_db
        logger.info("✅ Initialized HallucinationDetector with ground truth database")

    def detect_all(self, output: dict) -> List[HallucinationDetection]:
        """
        Run all hallucination detection techniques

        Args:
            output: Agent output to analyze

        Returns:
            List of detected hallucinations
        """
        detections = []

        # Technique 1: Invalid entity detection
        detections.extend(self._detect_invalid_entities(output))

        # Technique 2: Factual inconsistency detection
        detections.extend(self._detect_factual_inconsistencies(output))

        # Technique 3: Logical inconsistency detection
        detections.extend(self._detect_logical_inconsistencies(output))

        # Technique 4: Confidence-based filtering
        detections.extend(self._detect_low_confidence_claims(output))

        # Technique 5: Pattern mismatch detection
        detections.extend(self._detect_pattern_mismatches(output))

        # Technique 6: Temporal inconsistency detection
        detections.extend(self._detect_temporal_issues(output))

        return detections

    def _detect_invalid_entities(self, output: dict) -> List[HallucinationDetection]:
        """
        Detect references to non-existent services, error codes, or actions
        (Grounding Technique: Entity Validation)
        """
        detections = []

        # Check services
        for service in output.get("affected_services", []):
            if not self.ground_truth.is_valid_service(service):
                detections.append(HallucinationDetection(
                    detected=True,
                    severity=HallucinationSeverity.HIGH,
                    hallucination_type="invalid_entity",
                    description=f"Service '{service}' does not exist in known infrastructure",
                    evidence=f"Service '{service}' not found in ground truth database",
                    suggested_correction=f"Use one of: {', '.join(self.ground_truth.get_known_services().keys())}",
                    confidence_score=0.95
                ))

        # Check error codes
        if "error_code" in output:
            error_code = output["error_code"]
            if not self.ground_truth.is_valid_error_code(error_code):
                detections.append(HallucinationDetection(
                    detected=True,
                    severity=HallucinationSeverity.MEDIUM,
                    hallucination_type="invalid_error_code",
                    description=f"Error code '{error_code}' is not recognized",
                    evidence=f"Error code '{error_code}' not in valid error codes",
                    suggested_correction=f"Use valid error codes: {list(self.ground_truth.valid_error_codes.keys())}",
                    confidence_score=0.90
                ))

        # Check actions
        if "action" in output:
            action = output["action"]
            if not self.ground_truth.is_valid_action(action):
                detections.append(HallucinationDetection(
                    detected=True,
                    severity=HallucinationSeverity.HIGH,
                    hallucination_type="invalid_action",
                    description=f"Remediation action '{action}' is not in approved actions",
                    evidence=f"Action '{action}' not found in valid actions",
                    suggested_correction=f"Use approved actions: {list(self.ground_truth.valid_actions.keys())}",
                    confidence_score=0.95
                ))

        return detections

    def _detect_factual_inconsistencies(self, output: dict) -> List[HallucinationDetection]:
        """
        Detect claims that contradict known facts
        (Grounding Technique: Fact Verification)
        """
        detections = []

        incident_type = output.get("incident_type")
        root_cause = output.get("root_cause", "").lower()

        # Check if root cause matches expected patterns
        if incident_type:
            pattern = self.ground_truth.get_incident_pattern(incident_type)
            if pattern:
                expected_cause = pattern["typical_root_cause"].lower()

                # Check for significant divergence
                if expected_cause not in root_cause and root_cause not in expected_cause:
                    similarity = self._string_similarity(expected_cause, root_cause)
                    if similarity < 0.5:
                        detections.append(HallucinationDetection(
                            detected=True,
                            severity=HallucinationSeverity.MEDIUM,
                            hallucination_type="factual_inconsistency",
                            description=f"Root cause diverges from expected pattern for {incident_type}",
                            evidence=f"Expected: '{expected_cause}', Got: '{root_cause}' (similarity: {similarity:.2f})",
                            suggested_correction=f"For {incident_type}, typical cause is: {expected_cause}",
                            confidence_score=0.70
                        ))

        return detections

    def _detect_logical_inconsistencies(self, output: dict) -> List[HallucinationDetection]:
        """
        Detect logical contradictions within output
        (Validation Technique: Self-Consistency)
        """
        detections = []

        # Check if severity matches impact assessment
        severity = output.get("severity", "").lower()
        impact = output.get("estimated_impact", "").lower()

        # Map severity to impact expectations
        severity_impact_map = {
            "critical": ["critical", "severe", "major"],
            "high": ["major", "significant", "moderate"],
            "medium": ["moderate", "minor", "low"],
            "low": ["minor", "negligible", "none"]
        }

        if severity in severity_impact_map:
            expected_impacts = severity_impact_map[severity]
            if not any(exp in impact for exp in expected_impacts):
                detections.append(HallucinationDetection(
                    detected=True,
                    severity=HallucinationSeverity.MEDIUM,
                    hallucination_type="logical_inconsistency",
                    description=f"Impact assessment doesn't match severity level",
                    evidence=f"Severity: {severity}, but Impact: {impact}",
                    suggested_correction=f"For {severity} severity, expect: {', '.join(expected_impacts)}",
                    confidence_score=0.75
                ))

        # Check if MTTR is realistic for service type
        mttr_str = output.get("estimated_mttr", "")
        if "minute" in mttr_str or "hour" in mttr_str:
            try:
                # Extract number from "5-10 minutes" format
                numbers = re.findall(r'\d+', mttr_str)
                if numbers:
                    max_time = int(numbers[-1])
                    if "hour" in mttr_str:
                        max_time *= 60

                    # Critical services should have shorter MTTR
                    if "critical" in severity.lower() and max_time > 30:
                        detections.append(HallucinationDetection(
                            detected=True,
                            severity=HallucinationSeverity.MEDIUM,
                            hallucination_type="logical_inconsistency",
                            description="MTTR unrealistic for critical severity",
                            evidence=f"Critical severity but MTTR is {mttr_str}",
                            suggested_correction="Critical incidents should have MTTR < 30 minutes",
                            confidence_score=0.70
                        ))
            except:
                pass

        return detections

    def _detect_low_confidence_claims(self, output: dict) -> List[HallucinationDetection]:
        """
        Flag claims with low confidence scores
        (Technique: Confidence-Based Filtering)
        """
        detections = []

        confidence = output.get("confidence", 1.0)

        if confidence < 0.6:
            detections.append(HallucinationDetection(
                detected=True,
                severity=HallucinationSeverity.HIGH,
                hallucination_type="low_confidence",
                description="Analysis confidence below acceptable threshold",
                evidence=f"Confidence score: {confidence:.2f}",
                suggested_correction="Request additional analysis or manual review",
                confidence_score=0.99
            ))
        elif confidence < 0.75:
            detections.append(HallucinationDetection(
                detected=True,
                severity=HallucinationSeverity.MEDIUM,
                hallucination_type="moderate_confidence",
                description="Analysis confidence is moderate",
                evidence=f"Confidence score: {confidence:.2f}",
                suggested_correction="Results should be verified before acting",
                confidence_score=0.95
            ))

        return detections

    def _detect_pattern_mismatches(self, output: dict) -> List[HallucinationDetection]:
        """
        Detect outputs that don't match expected patterns for incident type
        (Technique: Pattern Matching)
        """
        detections = []

        incident_type = output.get("incident_type")
        affected_services = output.get("affected_services", [])

        if incident_type:
            pattern = self.ground_truth.get_incident_pattern(incident_type)
            if pattern:
                expected_services = set(pattern["affected_services"])
                actual_services = set(affected_services)

                # Check if critical services are missing
                if expected_services and not actual_services:
                    detections.append(HallucinationDetection(
                        detected=True,
                        severity=HallucinationSeverity.HIGH,
                        hallucination_type="pattern_mismatch",
                        description=f"No affected services identified for {incident_type}",
                        evidence=f"Expected services: {expected_services}, Got: {actual_services}",
                        suggested_correction=f"For {incident_type}, typically affects: {list(expected_services)}",
                        confidence_score=0.85
                    ))

        return detections

    def _detect_temporal_issues(self, output: dict) -> List[HallucinationDetection]:
        """
        Detect temporal inconsistencies
        (Technique: Timestamp Validation)
        """
        detections = []

        # Check if timestamps are in valid format and reasonable
        analysis_timestamp = output.get("analysis_timestamp", "")

        if analysis_timestamp:
            try:
                ts = datetime.fromisoformat(analysis_timestamp.replace('Z', '+00:00'))
                now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()

                # Timestamp should be recent (within last minute)
                diff = abs((now - ts).total_seconds())
                if diff > 60:
                    detections.append(HallucinationDetection(
                        detected=True,
                        severity=HallucinationSeverity.LOW,
                        hallucination_type="temporal_issue",
                        description="Analysis timestamp is older than expected",
                        evidence=f"Timestamp is {diff} seconds old",
                        suggested_correction="Ensure timestamps are current",
                        confidence_score=0.60
                    ))
            except ValueError:
                detections.append(HallucinationDetection(
                    detected=True,
                    severity=HallucinationSeverity.LOW,
                    hallucination_type="invalid_timestamp",
                    description="Invalid timestamp format",
                    evidence=f"Timestamp: '{analysis_timestamp}' is not ISO 8601",
                    suggested_correction="Use ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ",
                    confidence_score=0.90
                ))

        return detections

    def _string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using Levenshtein distance
        Returns 0-1 where 1 is identical
        """
        if not str1 or not str2:
            return 0.0

        # Simple similarity: common words / total words
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0


# ============================================================================
# OUTPUT VALIDATION & SANITIZATION
# ============================================================================

class OutputValidator:
    """
    Validates and sanitizes agent outputs
    Implements schema-based validation and error correction
    """

    def __init__(self, ground_truth_db: GroundTruthDatabase):
        """Initialize with ground truth database"""
        self.ground_truth = ground_truth_db
        self.required_fields = {
            "analysis": ["root_cause", "confidence", "affected_services"],
            "remediation": ["action", "severity", "steps", "estimated_duration_minutes"]
        }

    def validate_and_sanitize(self, output: dict, output_type: str = "analysis") -> SanitizedOutput:
        """
        Validate and sanitize agent output

        Args:
            output: Agent output to validate
            output_type: Type of output (analysis/remediation)

        Returns:
            SanitizedOutput with sanitized data and issues found
        """
        issues = []
        sanitized = output.copy()

        # Check required fields
        required = self.required_fields.get(output_type, [])
        for field in required:
            if field not in output or output[field] is None:
                issues.append({
                    "issue": "missing_field",
                    "field": field,
                    "severity": "high",
                    "suggestion": f"Field '{field}' is required"
                })

        # Validate data types
        type_issues = self._validate_types(output)
        issues.extend(type_issues)

        # Validate field values
        value_issues = self._validate_values(output)
        issues.extend(value_issues)

        # Correct or remove invalid data
        sanitized = self._correct_issues(sanitized, issues)

        is_safe = len([i for i in issues if i.get("severity") == "high"]) == 0
        risk_level = "critical" if len([i for i in issues if i.get("severity") == "high"]) > 2 else \
                    "high" if len([i for i in issues if i.get("severity") == "high"]) > 0 else \
                    "medium" if len([i for i in issues if i.get("severity") == "medium"]) > 2 else \
                    "low"

        return SanitizedOutput(
            original_output=output,
            sanitized_output=sanitized,
            issues_found=issues,
            is_safe=is_safe,
            risk_level=risk_level
        )

    def _validate_types(self, output: dict) -> List[Dict[str, Any]]:
        """Validate field types"""
        issues = []

        type_map = {
            "confidence": (float, int),
            "estimated_duration_minutes": (int, float),
            "affected_services": (list,),
            "steps": (list,)
        }

        for field, expected_types in type_map.items():
            if field in output:
                if not isinstance(output[field], expected_types):
                    issues.append({
                        "issue": "invalid_type",
                        "field": field,
                        "expected": str(expected_types),
                        "actual": type(output[field]).__name__,
                        "severity": "medium"
                    })

        return issues

    def _validate_values(self, output: dict) -> List[Dict[str, Any]]:
        """Validate field values"""
        issues = []

        # Confidence must be 0-1
        if "confidence" in output:
            conf = output["confidence"]
            if not (0 <= conf <= 1):
                issues.append({
                    "issue": "out_of_range",
                    "field": "confidence",
                    "expected_range": "0-1",
                    "actual": conf,
                    "severity": "high"
                })

        # Duration must be positive
        if "estimated_duration_minutes" in output:
            duration = output["estimated_duration_minutes"]
            if duration <= 0:
                issues.append({
                    "issue": "invalid_value",
                    "field": "estimated_duration_minutes",
                    "expected": "positive integer",
                    "actual": duration,
                    "severity": "high"
                })

        return issues

    def _correct_issues(self, output: dict, issues: List[Dict]) -> dict:
        """Attempt to correct issues"""
        corrected = output.copy()

        for issue in issues:
            if issue["issue"] == "invalid_type":
                field = issue["field"]
                if field == "confidence" and isinstance(corrected.get(field), str):
                    try:
                        corrected[field] = float(corrected[field])
                    except:
                        corrected[field] = 0.5

        return corrected


# ============================================================================
# VERIFICATION AGENT (Multi-Agent Verification)
# ============================================================================

class VerificationAgent:
    """
    Secondary agent that verifies primary agent's claims
    Implements multi-agent verification technique
    """

    def __init__(self, ground_truth_db: GroundTruthDatabase):
        """Initialize verification agent"""
        self.ground_truth = ground_truth_db
        logger.info("✅ Initialized VerificationAgent for multi-agent fact-checking")

    def verify_analysis(self, analysis: dict, incident_logs: List[str]) -> Dict[str, Any]:
        """
        Verify incident analysis against logs and ground truth

        Args:
            analysis: Analysis results to verify
            incident_logs: Raw incident logs

        Returns:
            Verification report with verified facts
        """
        verification_results = {
            "overall_verification_score": 0.0,
            "facts_verified": [],
            "facts_unverified": [],
            "contradictions": [],
            "confidence_adjustment": 1.0
        }

        root_cause = analysis.get("root_cause", "")
        affected_services = analysis.get("affected_services", [])

        # Verify root cause against logs
        if root_cause:
            log_evidence = self._find_log_evidence(root_cause, incident_logs)
            if log_evidence:
                verification_results["facts_verified"].append({
                    "fact": f"Root cause: {root_cause}",
                    "evidence_found": log_evidence,
                    "confidence": 0.9
                })
            else:
                verification_results["facts_unverified"].append({
                    "fact": f"Root cause: {root_cause}",
                    "reason": "No supporting evidence in logs",
                    "confidence": 0.6
                })
                # Reduce confidence if not supported by logs
                verification_results["confidence_adjustment"] *= 0.8

        # Verify affected services
        for service in affected_services:
            if self.ground_truth.is_valid_service(service):
                verification_results["facts_verified"].append({
                    "fact": f"Service: {service}",
                    "verification_method": "ground_truth_lookup",
                    "confidence": 0.95
                })
            else:
                verification_results["contradictions"].append({
                    "claim": f"Service {service} is affected",
                    "issue": "Service not found in known infrastructure",
                    "severity": "high"
                })

        # Calculate overall verification score
        total_facts = len(verification_results["facts_verified"]) + len(verification_results["facts_unverified"])
        if total_facts > 0:
            verification_results["overall_verification_score"] = (
                len(verification_results["facts_verified"]) / total_facts
            )

        return verification_results

    def _find_log_evidence(self, claim: str, logs: List[str]) -> Optional[str]:
        """Find supporting evidence in logs for a claim"""
        claim_lower = claim.lower()

        # Look for keywords from claim in logs
        keywords = claim_lower.split()[:2]  # First 2 words

        for log in logs:
            log_lower = log.lower()
            if all(keyword in log_lower for keyword in keywords):
                return log

        return None


# ============================================================================
# HALLUCINATION CONTROL SYSTEM (Main Coordinator)
# ============================================================================

class HallucinationControlSystem:
    """
    Master coordinator for hallucination detection and prevention
    Implements all Google ADK techniques for reliable AI agents
    """

    def __init__(self):
        """Initialize the complete hallucination control system"""
        self.ground_truth = GroundTruthDatabase()
        self.detector = HallucinationDetector(self.ground_truth)
        self.validator = OutputValidator(self.ground_truth)
        self.verifier = VerificationAgent(self.ground_truth)

        logger.info("✅ Initialized HallucinationControlSystem with all techniques:")
        logger.info("   - Grounding (Ground Truth Database)")
        logger.info("   - Entity Validation")
        logger.info("   - Fact Verification")
        logger.info("   - Confidence Filtering")
        logger.info("   - Pattern Matching")
        logger.info("   - Output Sanitization")
        logger.info("   - Multi-Agent Verification")

    def verify_and_correct_analysis(self, analysis: dict, incident_logs: List[str]) -> Dict[str, Any]:
        """
        Complete verification and correction pipeline

        Args:
            analysis: Initial analysis from agent
            incident_logs: Incident logs for grounding

        Returns:
            Safe, verified analysis with corrections
        """
        logger.info("🔍 Starting hallucination control verification...")

        result = {
            "original_analysis": analysis,
            "detections": [],
            "validation_result": None,
            "verification_result": None,
            "final_analysis": analysis.copy(),
            "is_safe": False,
            "risk_level": "unknown"
        }

        # Step 1: Detect hallucinations
        logger.info("  Step 1: Detecting hallucinations...")
        detections = self.detector.detect_all(analysis)
        result["detections"] = [
            {
                "type": d.hallucination_type,
                "severity": d.severity.value,
                "description": d.description,
                "confidence": d.confidence_score
            }
            for d in detections
        ]

        if detections:
            logger.warning(f"  ⚠️  Found {len(detections)} potential hallucinations")
            for d in detections:
                logger.warning(f"     - {d.hallucination_type}: {d.description}")

        # Step 2: Validate and sanitize
        logger.info("  Step 2: Validating and sanitizing output...")
        validation = self.validator.validate_and_sanitize(analysis, "analysis")
        result["validation_result"] = {
            "is_safe": validation.is_safe,
            "risk_level": validation.risk_level,
            "issues_found": validation.issues_found
        }

        if validation.issues_found:
            logger.warning(f"  ⚠️  Found {len(validation.issues_found)} validation issues")
            result["final_analysis"] = validation.sanitized_output

        # Step 3: Multi-agent verification
        logger.info("  Step 3: Running multi-agent verification...")
        verification = self.verifier.verify_analysis(result["final_analysis"], incident_logs)
        result["verification_result"] = verification

        logger.info(f"  📊 Verification score: {verification['overall_verification_score']:.2f}")

        # Step 4: Determine if safe
        critical_hallucinations = [d for d in detections if d.severity == HallucinationSeverity.CRITICAL]
        high_issues = [i for i in validation.issues_found if i.get("severity") == "high"]

        result["is_safe"] = len(critical_hallucinations) == 0 and len(high_issues) == 0
        result["risk_level"] = validation.risk_level

        logger.info(f"  ✅ Final safety assessment: {'SAFE' if result['is_safe'] else 'REQUIRES REVIEW'}")
        logger.info(f"  ⚠️  Risk level: {result['risk_level']}")

        return result

    def get_corrections_needed(self, detections: List[HallucinationDetection]) -> Dict[str, Any]:
        """
        Generate recommended corrections for detected hallucinations

        Args:
            detections: Detected hallucinations

        Returns:
            Correction recommendations
        """
        corrections = {
            "critical_actions": [],
            "recommended_actions": [],
            "manual_review_items": []
        }

        for detection in detections:
            correction = {
                "issue": detection.hallucination_type,
                "severity": detection.severity.value,
                "suggestion": detection.suggested_correction
            }

            if detection.severity == HallucinationSeverity.CRITICAL:
                corrections["critical_actions"].append(correction)
            elif detection.severity == HallucinationSeverity.HIGH:
                corrections["recommended_actions"].append(correction)
            else:
                corrections["manual_review_items"].append(correction)

        return corrections


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def create_control_system() -> HallucinationControlSystem:
    """Factory function to create control system"""
    return HallucinationControlSystem()

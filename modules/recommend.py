# Module 3: recommend.py
# Produces modernization/migration recommendations from stack + findings
from dataclasses import dataclass
from typing import List, Dict, Any
from modules.acquire import StackReport
from modules.triage import Finding

@dataclass
class Recommendation:
    rationale: str
    affected_file: str
    suggested_fix: str
    priority: str  # high/medium/low
    impact_score: int  # numeric (e.g., for sorting)
    finding_ref: Any  # ref to Finding or None

UPGRADE_MAP = [
    # (signal_substring, suggestion, rationale, priority, impact_score)
    ('AngularJS', 'Migrate to React, Vue, or Angular 2+', 'AngularJS 1.x is EOL since Jan 2022.', 'high', 95),
    ('Python 2', 'Migrate to Python 3.11+', 'Python 2 is EOL and unsupported.', 'high', 90),
    ('mysql_*', 'Replace with MySQLi or PDO', 'Deprecated PHP mysql_* APIs are insecure.', 'high', 85),
    ("'request' npm package", 'Switch to axios or node-fetch', 'The request npm package has been deprecated.', 'medium', 60),
    ('componentWillMount', 'Refactor React lifecycle (useEffect/useLayoutEffect)', 'Deprecated in React 16+', 'medium', 60),
    ('componentWillReceiveProps', 'Refactor React lifecycle (useEffect/useLayoutEffect)', 'Deprecated in React 16+', 'medium', 60),
]

def recommend(stack: StackReport, findings: List[Finding]) -> List[Recommendation]:
    recs = []
    # Recommend on detected legacy signals
    for f in findings:
        for signal_sub, suggestion, rationale, priority, impact in UPGRADE_MAP:
            if signal_sub in f.signal:
                recs.append(Recommendation(
                    rationale=rationale,
                    affected_file=f.file,
                    suggested_fix=suggestion,
                    priority=priority,
                    impact_score=impact + f.weight,
                    finding_ref=f,
                ))
    # Recommend from StackReport facts (ex. Python/JS/DB version upgrades, infra, etc.)
    if 'python' in stack.languages and '2' in stack.primary_language:
        recs.append(Recommendation(
            rationale="Codebase flagged as Python 2 (unsupported)",
            affected_file="",
            suggested_fix="Migrate to Python >=3.9 and re-test all features.",
            priority="high",
            impact_score=100,
            finding_ref=None,
        ))
    # Dockerfile missing
    if not stack.has_dockerfile:
        recs.append(Recommendation(
            rationale="No Dockerfile found; add containerization for modern CI/CD, portability.",
            affected_file="/",
            suggested_fix="Author a minimal Dockerfile and docker-compose config (see best practices)",
            priority="medium",
            impact_score=40,
            finding_ref=None,
        ))
    # OpenAPI missing
    if not stack.has_openapi:
        recs.append(Recommendation(
            rationale="No OpenAPI spec found; add one for auto-docs and contract testing.",
            affected_file="/",
            suggested_fix="Generate OpenAPI/Swagger for your API routes.",
            priority="medium",
            impact_score=38,
            finding_ref=None,
        ))
    return recs

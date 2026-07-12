# Module 2: triage.py
# Fast codebase triage via static pattern/regex scans
from dataclasses import dataclass
from typing import List, Dict, Any
import os
import re
from modules.language_db_lookups import LANGUAGE_EXTENSIONS, SKIP_DIRS, LEGACY_SIGNALS

@dataclass
class Finding:
    file: str
    line: int
    pattern: str
    context: str
    signal: str
    severity: str
    weight: int

def triage(local_path: str) -> List[Finding]:
    findings = []
    # Sample rules: legacy signals + common anti-patterns
    PATTERN_RULES = [
        # (regex, signal, severity, weight)
        (re.compile(r'\\beval\\b'), 'Use of eval()', 'high', 30),
        (re.compile(r'(?i)hard.?coded.?password'), 'Hardcoded password', 'high', 40),
        (re.compile(r'import .*pickle'), 'Use of pickle module (insecure)', 'medium', 20),
        (re.compile(r'(?i)jwt.*none'), 'JWT none algorithm', 'high', 40),
        (re.compile(r'(console|System)\\.log'), 'Debug logging left in code', 'low', 8),
        (re.compile(r'os\\.system'), 'Use of os.system (subprocess risk)', 'medium', 15),
    ]
    # Add legacy signals as simple substrings
    LEGACY_SIMPLE = [(signal['pattern'], signal['signal'], 'medium', signal['weight']) for signal in LEGACY_SIGNALS]

    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            # Focus on code files only
            if ext not in LANGUAGE_EXTENSIONS:
                continue
            file_path = os.path.join(root, f)
            rel_file = os.path.relpath(file_path, local_path)
            try:
                with open(file_path, 'r', errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        # Regex-based rules
                        for regex, signal, severity, weight in PATTERN_RULES:
                            if regex.search(line):
                                findings.append(Finding(
                                    file=rel_file,
                                    line=i,
                                    pattern=regex.pattern,
                                    context=line.strip()[:200],
                                    signal=signal,
                                    severity=severity,
                                    weight=weight,
                                ))
                        # Substring legacy rules
                        for pattern, signal, severity, weight in LEGACY_SIMPLE:
                            if pattern in line:
                                findings.append(Finding(
                                    file=rel_file,
                                    line=i,
                                    pattern=pattern,
                                    context=line.strip()[:200],
                                    signal=signal,
                                    severity=severity,
                                    weight=weight,
                                ))
            except Exception:
                continue
    return findings

# Module 4: deepfix.py
# Deep static analysis and auto-fix suggestions using AST, for Python initially
from dataclasses import dataclass
from typing import List, Any
import os
import ast
from modules.language_db_lookups import LANGUAGE_EXTENSIONS, SKIP_DIRS

@dataclass
class FixSuggestion:
    file: str
    line: int
    issue: str
    suggested_fix: str
    rationale: str
    severity: str
    impact: int  # score

# Basic deep fixer for Python anti-patterns
def deepfix_python(file_path: str, rel_file: str) -> List[FixSuggestion]:
    suggestions = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
            source = fh.read()
        tree = ast.parse(source, filename=file_path)
        # Example fix: bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    suggestions.append(FixSuggestion(
                        file=rel_file,
                        line=node.lineno,
                        issue='Bare except detected',
                        suggested_fix='Specify the exception type (e.g. except Exception as e:)',
                        rationale='Catching all exceptions breaks debuggability and can hide bugs.',
                        severity='medium',
                        impact=24,
                    ))
            # Example: exec() function usage
            if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'exec':
                suggestions.append(FixSuggestion(
                    file=rel_file,
                    line=node.lineno,
                    issue='Use of exec()',
                    suggested_fix='Refactor logic to avoid exec().',
                    rationale='Use of exec() can be a security risk and is discouraged.',
                    severity='high',
                    impact=40,
                ))
            # Example: import of pickle module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'pickle':
                        suggestions.append(FixSuggestion(
                            file=rel_file,
                            line=node.lineno,
                            issue='Importing pickle module',
                            suggested_fix='Avoid pickle for untrusted data. Use json or safe serialization.',
                            rationale='pickle is insecure for untrusted data.',
                            severity='high',
                            impact=35,
                        ))
    except Exception:
        pass
    return suggestions

def deepfix(local_path: str) -> List[FixSuggestion]:
    suggestions = []
    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            rel_file = os.path.relpath(os.path.join(root, f), local_path)
            file_path = os.path.join(root, f)
            if ext == '.py':
                suggestions += deepfix_python(file_path, rel_file)
            # Future: add JS/TS AST-based fixers here
    return suggestions

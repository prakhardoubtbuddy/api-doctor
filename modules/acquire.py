# Module 1: acquire.py
# Responsible for: cloning repo + detecting stack

from dataclasses import dataclass
from typing import List, Dict, Any
import os
import tempfile
import subprocess
import json
import re
from modules.language_db_lookups import LANGUAGE_EXTENSIONS, SKIP_DIRS, PACK_MANAGERS, FRAMEWORKS, DB_DEPS, LEGACY_SIGNALS

@dataclass
class StackReport:
    repo_url: str
    local_path: str
    languages: Dict[str, int]   # e.g., {"python": 3}
    primary_language: str
    frameworks: List[str]
    databases: List[str]
    package_managers: List[str]
    runtime_signals: List[dict] # e.g., [{signal, file, weight}]
    has_tests: bool
    has_dockerfile: bool
    has_openapi: bool
    xml_data_files: int
    total_source_files: int
    loc_estimate: int

def clone(repo_url: str, dest: str = None) -> str:
    """Shallow git clone (depth 1). Returns local path or raises on error."""
    if dest is None:
        dest = tempfile.mkdtemp(prefix="repo_clone_")
    cmd = ["git", "clone", "--depth", "1", repo_url, dest]
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=300)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Repo clone failed: {e.output.decode('utf-8')}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Repo clone timed out after 300s: {repo_url}")
    if not os.path.isdir(dest):
        raise RuntimeError("Clone did not produce a directory")
    return dest

def detect(repo_url: str, local_path: str) -> StackReport:
    languages = {}
    frameworks = set()
    databases = set()
    package_managers = set()
    runtime_signals = []
    has_tests = False
    has_dockerfile = False
    has_openapi = False
    xml_data_files = 0
    total_source_files = 0
    loc_estimate = 0

    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in LANGUAGE_EXTENSIONS:
                lang = LANGUAGE_EXTENSIONS[ext]
                languages[lang] = languages.get(lang, 0) + 1
                total_source_files += 1
            # Count XML files
            if ext == '.xml':
                xml_data_files += 1

            file_path = os.path.join(root, f)
            rel_file = os.path.relpath(file_path, local_path)
            # Count lines for LOC estimate
            try:
                with open(file_path, 'r', errors="ignore") as fh:
                    lines = fh.readlines()
                    loc_estimate += len(lines)
                    content = ''.join(lines)
            except Exception:
                continue

            # Check for tests
            if (f.startswith("test_") or ".test." in f or ".spec." in f or "fixture" in rel_file or "__tests__" in rel_file):
                has_tests = True

            # Check for Dockerfile
            if f == "Dockerfile" or (f.startswith("docker-compose") and (f.endswith(".yml") or f.endswith(".yaml"))):
                has_dockerfile = True

            # Check for OpenAPI spec
            if re.search(r'(openapi|swagger)\.(json|yaml)', f, flags=re.IGNORECASE):
                has_openapi = True

            # Parse manifest files for package manager, framework, DB
            for mfile, pmgr in PACK_MANAGERS:
                if f == mfile:
                    package_managers.add(pmgr)
                    # Detect frameworks and dbs
                    try:
                        txt = content
                        if mfile == "package.json":
                            data = json.loads(content)
                            deps = data.get("dependencies", {})
                            for dep_name in deps:
                                if dep_name in FRAMEWORKS[mfile]:
                                    frameworks.add(FRAMEWORKS[mfile][dep_name])
                                if dep_name in DB_DEPS[mfile]:
                                    databases.add(DB_DEPS[mfile][dep_name])
                        elif mfile == "requirements.txt":
                            for dep in lines:
                                dep = dep.strip()
                                for fw in FRAMEWORKS[mfile]:
                                    if fw in dep:
                                        frameworks.add(FRAMEWORKS[mfile][fw])
                                for dbdep in DB_DEPS[mfile]:
                                    if dbdep in dep:
                                        databases.add(DB_DEPS[mfile][dbdep])
                        elif mfile == "pyproject.toml":
                            for dbdep in DB_DEPS[mfile]:
                                if dbdep in content:
                                    databases.add(DB_DEPS[mfile][dbdep])
                    except Exception:
                        continue

            # Legacy signals (scan rel_file if source and small enough)
            if ext in LANGUAGE_EXTENSIONS and os.path.getsize(file_path) < 400*1024:
                for signal in LEGACY_SIGNALS:
                    if signal['pattern'] in content:
                        runtime_signals.append({'signal': signal['signal'], 'file': rel_file, 'weight': signal['weight']})

    # Primary language
    primary_language = max(languages, key=languages.get) if languages else "unknown"

    return StackReport(
        repo_url=repo_url,
        local_path=local_path,
        languages=languages,
        primary_language=primary_language,
        frameworks=list(frameworks),
        databases=list(databases),
        package_managers=list(package_managers),
        runtime_signals=runtime_signals,
        has_tests=has_tests,
        has_dockerfile=has_dockerfile,
        has_openapi=has_openapi,
        xml_data_files=xml_data_files,
        total_source_files=total_source_files,
        loc_estimate=loc_estimate,
    )


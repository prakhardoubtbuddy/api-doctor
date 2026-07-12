#!/usr/bin/env python3
import argparse
import json
import os
import sys
from modules import acquire, triage, recommend, deepfix
import datetime

# Helpers for modernization output files
def render_dockerfile(stack):
    if 'express' in stack.frameworks or 'react' in stack.frameworks or 'node' in stack.languages.keys():
        return '''# Example Dockerfile for Node.js/Express + React
FROM node:18 AS base
WORKDIR /app
COPY . .
RUN npm install
CMD ["npm", "start"]
'''
    if 'django' in stack.frameworks or 'python' in stack.languages.keys():
        return '''# Example Dockerfile for Python/Django
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]
'''
    return None

def render_openapi_yaml(stack):
    if 'express' in stack.frameworks or 'django' in stack.frameworks:
        return '''openapi: 3.0.0
info:
  title: Modernized API
  version: 1.0.0
servers:
  - url: http://localhost:3000/api
paths:
  /example:
    get:
      summary: Example endpoint
      responses:
        '200':
          description: Example response
'''
    return None

def render_docker_compose(stack):
    if 'postgres' in stack.databases:
        return '''version: '3.8'
services:
  db:
    image: postgres:13
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: appdb
    ports:
      - "5432:5432"
  app:
    build: .
    ports:
      - "3000:3000"
    depends_on:
      - db
'''
    return None

def get_next_run_dir(base_dir):
    runs = [d for d in os.listdir(base_dir) if d.endswith('run') or d.endswith('run/')]
    # sort as 1st run, 2nd run, ...
    nums = [int(d.split('st')[0]) if 'st' in d else int(d.split('nd')[0]) if 'nd' in d else int(d.split('rd')[0]) if 'rd' in d else int(d.split('th')[0]) if 'th' in d else 0 for d in runs]
    next_idx = (max(nums) if nums else 0) + 1
    suffix = ['st','nd','rd','th'][(next_idx-1) if next_idx < 4 else 3]
    if next_idx in [1]: suffix = 'st'
    elif next_idx == 2: suffix = 'nd'
    elif next_idx == 3: suffix = 'rd'
    else: suffix = 'th'
    run_name = f"{next_idx}{suffix} run"
    run_path = os.path.join(base_dir, run_name)
    os.makedirs(run_path, exist_ok=True)
    return run_name, run_path

def update_stats(base_dir, run_name, repo_url, stats):
    stats_file = os.path.join(base_dir, "stats.json")
    now = datetime.datetime.now().isoformat()
    entry = {
        "run_name": run_name,
        "timestamp": now,
        "repo_url": repo_url,
        **stats
    }
    all_stats = []
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                all_stats = json.load(f)
        except Exception:
            pass
    all_stats.append(entry)
    with open(stats_file, 'w') as f:
        json.dump(all_stats, f, indent=2)
    return all_stats

def main():
    parser = argparse.ArgumentParser(description="App Modernization Agent - Analyze, Triage, Recommend, Modernize")
    parser.add_argument("repo", help="Git URL or local path to analyze")
    parser.add_argument("--json", action="store_true", help="Output full JSON report")
    parser.add_argument("--output", type=str, default=None, help="Save report to JSON file")
    args = parser.parse_args()

    repo_input = args.repo
    # Local path or Git URL
    if os.path.isdir(repo_input):
        local_path = repo_input
        repo_url = os.path.abspath(repo_input)
    else:
        # Clone
        print(f"Cloning repo {repo_input}...")
        local_path = acquire.clone(repo_input)
        repo_url = repo_input

    print("Detecting stack (acquire)...")
    stack = acquire.detect(repo_url, local_path)
    print(f"Primary language: {stack.primary_language}\nFrameworks: {stack.frameworks}\nDatabases: {stack.databases}")

    print("Running fast codebase triage...")
    findings = triage.triage(local_path)
    print(f"Findings: {len(findings)} issues static-detected")

    print("Generating recommendations...")
    recs = recommend.recommend(stack, findings)
    print(f"Recommendations: {len(recs)}\n")

    print("Performing deep fixes...")
    deepfixes = deepfix.deepfix(local_path)
    print(f"Deep fix findings: {len(deepfixes)}\n")

    # Prepare JSON-serializable output
    def dataclass_to_dict(obj):
        if hasattr(obj, '__dataclass_fields__'):
            d = {k: dataclass_to_dict(v) for k, v in obj.__dict__.items()}
            return d
        if isinstance(obj, list):
            return [dataclass_to_dict(i) for i in obj]
        if isinstance(obj, dict):
            return {k: dataclass_to_dict(v) for k, v in obj.items()}
        return obj

    report = {
        'stack': dataclass_to_dict(stack),
        'findings': dataclass_to_dict(findings),
        'recommendations': dataclass_to_dict(recs),
        'deepfixes': dataclass_to_dict(deepfixes),
    }

    # --- Modernization output ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    run_name, run_path = get_next_run_dir(base_dir)

    # Write main report JSON
    rep_path = os.path.join(run_path, "report.json")
    with open(rep_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"JSON report saved to {rep_path}")

    # Write code recommendations automatically into new run folder
    for rec in recs:
        if rec.suggested_fix.startswith("Author a minimal Dockerfile"):
            dockerfile = render_dockerfile(stack)
            if dockerfile:
                with open(os.path.join(run_path, "Dockerfile"), 'w') as f:
                    f.write(dockerfile)
        if rec.suggested_fix.startswith("Generate OpenAPI"):
            openapi = render_openapi_yaml(stack)
            if openapi:
                with open(os.path.join(run_path, "openapi.yml"), 'w') as f:
                    f.write(openapi)
        if rec.suggested_fix.startswith("Author a minimal Dockerfile"):
            docker_compose = render_docker_compose(stack)
            if docker_compose:
                with open(os.path.join(run_path, "docker-compose.yml"), 'w') as f:
                    f.write(docker_compose)

    # Write stats and update aggregate log
    stats_obj = {
        "primary_language": stack.primary_language,
        "frameworks": list(stack.frameworks),
        "databases": list(stack.databases),
        "findings": len(findings),
        "recommendations": len(recs),
        "deepfixes": len(deepfixes),
        "repo_url": repo_url
    }
    all_stats = update_stats(base_dir, run_name, repo_url, stats_obj)
    print(f"All runs: {len(all_stats)}")
    print(json.dumps(all_stats[-1], indent=2))
    print(f"[Modernization outputs in: {run_path}]")

if __name__ == "__main__":
    main()


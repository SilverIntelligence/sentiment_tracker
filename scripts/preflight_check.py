#!/usr/bin/env python3
"""Pre-flight validation check (no dependencies required)."""

import os
import sys
from pathlib import Path

def check_file_structure():
    """Verify all required files exist."""
    print("Checking file structure...")
    
    required_files = [
        "app/main.py",
        "app/worker.py",
        "app/scheduler.py",
        "app/core/config.py",
        "app/db/database.py",
        "app/models/__init__.py",
        "app/nlp/entity_extractor.py",
        "app/nlp/sentiment_analyzer.py",
        "app/api/endpoints/summary.py",
        "app/workers/ingestion.py",
        "app/workers/aggregation.py",
        "app/workers/prices.py",
        "app/workers/publishing.py",
        "docker-compose.yml",
        "Dockerfile",
        "requirements.txt",
        ".env.example",
        "README.md",
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
            print(f"  ✗ Missing: {file}")
        else:
            print(f"  ✓ {file}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required files!")
        return False
    else:
        print("\n✅ All required files present")
        return True

def check_env_example():
    """Verify .env.example has required variables."""
    print("\nChecking environment template...")
    
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        "SECRET_KEY",
        "ADMIN_TOKEN",
    ]
    
    if not Path(".env.example").exists():
        print("  ✗ .env.example not found")
        return False
    
    with open(".env.example") as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var not in content:
            missing.append(var)
            print(f"  ✗ Missing: {var}")
        else:
            print(f"  ✓ {var}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required environment variables!")
        return False
    else:
        print("\n✅ Environment template complete")
        return True

def check_requirements():
    """Verify requirements.txt has key dependencies."""
    print("\nChecking Python dependencies...")
    
    required_deps = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "redis",
        "rq",
        "praw",
        "vaderSentiment",
        "prometheus-client",
    ]
    
    with open("requirements.txt") as f:
        content = f.read().lower()
    
    missing = []
    for dep in required_deps:
        if dep.lower() not in content:
            missing.append(dep)
            print(f"  ✗ Missing: {dep}")
        else:
            print(f"  ✓ {dep}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required dependencies!")
        return False
    else:
        print("\n✅ All key dependencies listed")
        return True

def check_docker_compose():
    """Verify docker-compose.yml has required services."""
    print("\nChecking Docker Compose configuration...")
    
    if not Path("docker-compose.yml").exists():
        print("  ✗ docker-compose.yml not found")
        return False
    
    with open("docker-compose.yml") as f:
        content = f.read()
    
    required_services = ["postgres", "redis", "web", "worker", "scheduler"]
    
    missing = []
    for service in required_services:
        if f"{service}:" not in content:
            missing.append(service)
            print(f"  ✗ Missing service: {service}")
        else:
            print(f"  ✓ {service}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required services!")
        return False
    else:
        print("\n✅ All required services defined")
        return True

def check_api_endpoints():
    """Check that API endpoint files exist."""
    print("\nChecking API endpoints...")
    
    endpoints = [
        "app/api/endpoints/summary.py",
        "app/api/endpoints/sentiment.py",
        "app/api/endpoints/posts.py",
        "app/api/endpoints/leaderboard.py",
        "app/api/endpoints/admin.py",
    ]
    
    missing = []
    for endpoint in endpoints:
        if not Path(endpoint).exists():
            missing.append(endpoint)
            print(f"  ✗ Missing: {endpoint}")
        else:
            print(f"  ✓ {endpoint}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} endpoints!")
        return False
    else:
        print("\n✅ All API endpoints present")
        return True

def main():
    """Run all pre-flight checks."""
    print("=" * 60)
    print("Sentiment Tracker Pre-Flight Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("File Structure", check_file_structure),
        ("Environment Template", check_env_example),
        ("Dependencies", check_requirements),
        ("Docker Compose", check_docker_compose),
        ("API Endpoints", check_api_endpoints),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            passed = check_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} check failed with error: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Pre-Flight Check Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    print()
    if all_passed:
        print("🎉 All pre-flight checks passed!")
        print("\nNext steps:")
        print("  1. Copy .env.example to .env and configure")
        print("  2. Run: ./scripts/validate_deployment.sh")
        print("  3. Access: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

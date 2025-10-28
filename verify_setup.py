#!/usr/bin/env python3
"""
Setup verification script for RAG Pipeline.
Checks project structure and configuration without requiring dependencies.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_directory_exists(dirpath: str, description: str) -> bool:
    """Check if a directory exists."""
    exists = Path(dirpath).is_dir()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {dirpath}")
    return exists


def main() -> int:
    """Run verification checks."""
    print("=" * 60)
    print("RAG Pipeline - Phase 0 Verification")
    print("=" * 60)
    print()

    checks_passed = 0
    checks_total = 0

    print("📁 Directory Structure:")
    print("-" * 60)
    
    directories = [
        ("app/", "Main application package"),
        ("app/models/", "Database models"),
        ("app/routers/", "API routers"),
        ("app/services/", "Business logic services"),
        ("app/schemas/", "Pydantic schemas"),
        ("app/utils/", "Utility functions"),
        ("tests/", "Test suite"),
        ("alembic/", "Database migrations"),
        ("alembic/versions/", "Migration versions"),
    ]
    
    for dirpath, description in directories:
        if check_directory_exists(dirpath, description):
            checks_passed += 1
        checks_total += 1
    
    print()
    print("📄 Core Files:")
    print("-" * 60)
    
    files = [
        ("app/__init__.py", "App package init"),
        ("app/main.py", "FastAPI application"),
        ("app/config.py", "Configuration settings"),
        ("requirements.txt", "Python dependencies"),
        ("pyproject.toml", "Project metadata"),
        (".env.example", "Environment variables template"),
        (".gitignore", "Git ignore rules"),
        ("Dockerfile", "Docker image definition"),
        ("alembic.ini", "Alembic configuration"),
        ("pytest.ini", "Pytest configuration"),
        ("README.md", "Documentation"),
    ]
    
    for filepath, description in files:
        if check_file_exists(filepath, description):
            checks_passed += 1
        checks_total += 1
    
    print()
    print("🧪 Test Files:")
    print("-" * 60)
    
    test_files = [
        ("tests/__init__.py", "Test package init"),
        ("tests/conftest.py", "Pytest fixtures"),
        ("tests/test_health.py", "Health endpoint tests"),
        ("tests/test_config.py", "Configuration tests"),
    ]
    
    for filepath, description in test_files:
        if check_file_exists(filepath, description):
            checks_passed += 1
        checks_total += 1
    
    print()
    print("=" * 60)
    print(f"Results: {checks_passed}/{checks_total} checks passed")
    print("=" * 60)
    
    if checks_passed == checks_total:
        print("✅ Phase 0 scaffold is complete!")
        print()
        print("📝 Next Steps:")
        print("   1. Copy .env.example to .env and add your API keys")
        print("   2. Option A (Docker): docker-compose up -d")
        print("   3. Option B (Local): Install Python 3.10-3.12, create venv, pip install -r requirements.txt")
        print()
        print("⚠️  Note: Python 3.13 is not fully compatible with all dependencies.")
        print("   Recommend using Python 3.10, 3.11, or 3.12, or use Docker.")
        return 0
    else:
        print("❌ Some files are missing. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


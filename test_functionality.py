#!/usr/bin/env python3
"""
Test all RAG Pipeline functionalities
"""
import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n[1] Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"    Status: {response.status_code}")
        data = response.json()
        print(f"    Service Status: {data.get('status')}")
        if 'services' in data:
            for service, status in data['services'].items():
                if 'healthy' in str(status):
                    print(f"    {service}: OK")
                else:
                    print(f"    {service}: {status[:50]}")
        return True
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

def test_api_info():
    """Test API info endpoint"""
    print("\n[2] Testing API Info Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"    Status: {response.status_code}")
        data = response.json()
        print(f"    Version: {data.get('version')}")
        print(f"    Environment: {data.get('environment')}")
        return True
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

def test_list_documents():
    """Test list documents endpoint"""
    print("\n[3] Testing List Documents...")
    try:
        response = requests.get(f"{BASE_URL}/v1/documents", timeout=10)
        print(f"    Status: {response.status_code}")
        data = response.json()
        print(f"    Total Documents: {data.get('total', 0)}")
        return True
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

def test_upload_document():
    """Test document upload"""
    print("\n[4] Testing Document Upload...")
    
    # Create a test file
    test_content = "This is a test document for the RAG Pipeline. It contains sample text about artificial intelligence and machine learning."
    with open("test_upload.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        with open("test_upload.txt", "rb") as f:
            files = {"files": ("test_upload.txt", f, "text/plain")}
            response = requests.post(
                f"{BASE_URL}/v1/documents/upload",
                files=files,
                timeout=120
            )
        print(f"    Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"    Upload Batch ID: {data.get('upload_batch_id')}")
            print(f"    Total Documents: {data.get('total_documents')}")
            print(f"    Successful: {data.get('successful_documents')}")
            return True, data.get('upload_batch_id')
        else:
            print(f"    Response: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"    ERROR: {e}")
        return False, None

def test_query_documents():
    """Test query endpoint"""
    print("\n[5] Testing Query Documents...")
    try:
        payload = {"query": "What is this document about?"}
        response = requests.post(
            f"{BASE_URL}/v1/query",
            json=payload,
            timeout=60
        )
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    Query: {data.get('query')}")
            print(f"    Answer: {data.get('answer', '')[:100]}...")
            return True
        else:
            print(f"    Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

def main():
    print("=" * 50)
    print("RAG PIPELINE FUNCTIONALITY TEST")
    print("=" * 50)
    
    results = {
        "Health Check": test_health(),
        "API Info": test_api_info(),
        "List Documents": test_list_documents(),
        "Upload Document": test_upload_document()[0],
        "Query Documents": test_query_documents(),
    }
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        color = "\033[92m" if result else "\033[91m"
        print(f"{color}{status}\033[0m - {test_name}")
    
    total = sum(results.values())
    print(f"\nTotal: {total}/{len(results)} tests passed")

if __name__ == "__main__":
    main()


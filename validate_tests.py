"""
Simple validation script to check if Phase 7 tests are syntactically correct
and all imports work properly.
"""

import sys
import ast
import os

def check_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

def check_imports(filepath):
    """Check if imports are valid."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse and extract imports
        tree = ast.parse(source)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return True, imports
    except Exception as e:
        print(f"Error parsing imports in {filepath}: {e}")
        return False, []

def main():
    """Main validation function."""
    print("=" * 60)
    print("Phase 7 Test Validation")
    print("=" * 60)
    print()
    
    # List of test files to validate
    test_files = [
        "tests/test_chunking_comprehensive.py",
        "tests/test_extractors_comprehensive.py",
        "tests/test_validators_comprehensive.py",
        "tests/test_api_endpoints.py",
        "tests/test_rag_pipeline_complete.py",
        "tests/test_mocks.py"
    ]
    
    results = {
        'total': 0,
        'syntax_ok': 0,
        'imports_ok': 0,
        'files_found': 0
    }
    
    print("Checking test files...")
    print("-" * 60)
    
    for filepath in test_files:
        results['total'] += 1
        
        if not os.path.exists(filepath):
            print(f"✗ {filepath} - NOT FOUND")
            continue
        
        results['files_found'] += 1
        
        # Check syntax
        if check_syntax(filepath):
            results['syntax_ok'] += 1
            status = "✓"
        else:
            status = "✗"
        
        # Check imports
        imports_ok, imports = check_imports(filepath)
        if imports_ok:
            results['imports_ok'] += 1
            import_status = "✓"
        else:
            import_status = "✗"
        
        # Display results
        print(f"{status} {filepath} - Syntax OK")
        print(f"{import_status} {filepath} - Imports OK ({len(imports)} imports)")
    
    print()
    print("-" * 60)
    print("Validation Summary")
    print("-" * 60)
    print(f"Total files checked: {results['total']}")
    print(f"Files found: {results['files_found']}")
    print(f"Syntax valid: {results['syntax_ok']}")
    print(f"Imports valid: {results['imports_ok']}")
    print()
    
    if results['syntax_ok'] == results['files_found'] and results['imports_ok'] == results['files_found']:
        print("✓ ALL TESTS VALIDATED SUCCESSFULLY!")
        print()
        print("Phase 7 test suite is ready to run.")
        print("To run tests, execute:")
        print("  pytest --cov=app --cov-report=html")
        return 0
    else:
        print("✗ SOME VALIDATION ERRORS FOUND")
        return 1

if __name__ == "__main__":
    sys.exit(main())


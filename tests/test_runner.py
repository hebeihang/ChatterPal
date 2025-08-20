"""
Comprehensive test runner for ChatterPal project.
Runs all tests and generates coverage reports.
"""

import sys
import os
import subprocess
import pytest
from pathlib import Path


def run_tests():
    """Run all tests with coverage reporting."""
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 Running ChatterPal Test Suite")
    print("=" * 50)
    
    # Test configuration
    test_args = [
        "--verbose",
        "--tb=short",
        "--cov=src/chatterpal",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=70",  # Require at least 70% coverage
        "tests/"
    ]
    
    try:
        # Run pytest
        result = pytest.main(test_args)
        
        if result == 0:
            print("\nAll tests passed!")
            print("📊 Coverage report generated in htmlcov/")
        else:
            print(f"\nTests failed with exit code: {result}")
            
        return result
        
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return 1


def run_specific_module_tests():
    """Run tests for specific modules individually."""
    
    test_modules = [
        "test_config.py",
        "test_asr.py", 
        "test_tts.py",
        "test_llm.py",
        "test_assessment.py",
        "test_services.py",
        "test_web_components.py"
    ]
    
    print("\n🔍 Running individual module tests")
    print("=" * 40)
    
    results = {}
    
    for module in test_modules:
        print(f"\n📋 Testing {module}...")
        
        try:
            result = pytest.main([
                "--verbose",
                "--tb=short",
                f"tests/{module}"
            ])
            
            results[module] = "PASS" if result == 0 else "FAIL"
            print(f"   {results[module]}")
            
        except Exception as e:
            results[module] = f"ERROR: {e}"
            print(f"   ERROR: {e}")
    
    # Summary
    print("\n📊 Test Results Summary")
    print("-" * 30)
    for module, result in results.items():
        status_emoji = " if result == "PASS" else "
        print(f"{status_emoji} {module}: {result}")
    
    return results


def check_test_dependencies():
    """Check if all required test dependencies are available."""
    
    print("🔧 Checking test dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-cov", 
        "pytest-asyncio",
        "numpy",
        "gradio"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  {package} - MISSING")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: uv add --dev " + " ".join(missing_packages))
        return False
    
    print("All test dependencies available")
    return True


def run_integration_tests():
    """Run integration tests specifically."""
    
    print("\n🔗 Running integration tests...")
    
    integration_tests = [
        "tests/test_services.py::TestServiceIntegration",
        "tests/test_web_components.py::TestWebComponentIntegration"
    ]
    
    for test in integration_tests:
        print(f"\n🧪 Running {test}...")
        result = pytest.main([
            "--verbose",
            "--tb=short",
            test
        ])
        
        if result != 0:
            print(f"Integration test failed: {test}")
            return False
    
    print("All integration tests passed!")
    return True


def generate_test_report():
    """Generate a comprehensive test report."""
    
    print("\n📋 Generating test report...")
    
    # Run tests with JUnit XML output
    result = pytest.main([
        "--verbose",
        "--tb=short",
        "--cov=src/chatterpal",
        "--cov-report=xml:coverage.xml",
        "--junit-xml=test-results.xml",
        "tests/"
    ])
    
    if result == 0:
        print("Test report generated:")
        print("  - coverage.xml (coverage data)")
        print("  - test-results.xml (test results)")
        print("  - htmlcov/ (HTML coverage report)")
    
    return result


def main():
    """Main test runner function."""
    
    print("🚀 ChatterPal Test Suite Runner")
    print("=" * 50)
    
    # Check dependencies first
    if not check_test_dependencies():
        print("\nCannot run tests due to missing dependencies")
        return 1
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "modules":
            run_specific_module_tests()
        elif command == "integration":
            return 0 if run_integration_tests() else 1
        elif command == "report":
            return generate_test_report()
        elif command == "coverage":
            return run_tests()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: modules, integration, report, coverage")
            return 1
    else:
        # Run all tests by default
        return run_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)








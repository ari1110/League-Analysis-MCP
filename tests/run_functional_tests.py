#!/usr/bin/env python3
"""
Functional test runner for League Analysis MCP Server.

Runs comprehensive functional tests that validate real user value delivery.
Supports different test modes: mock-based functional tests and real API integration tests.
"""

import sys
import os
import json
import subprocess
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional


class FunctionalTestRunner:
    """Runner for functional and integration tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = Path(__file__).parent
        self.functional_dir = self.tests_dir / "functional"
        self.integration_dir = self.tests_dir / "integration"
        
        # Test categories
        self.functional_tests = [
            "test_tools.py",
            "test_auth.py", 
            "test_analytics.py",
            "test_cache.py",
            "test_errors.py",
            "test_workflows.py"
        ]
        
        self.integration_tests = [
            "test_live_data.py",
            "test_historical.py"
        ] if self.integration_dir.exists() else []
    
    def check_environment(self) -> Dict[str, Any]:
        """Check test environment and dependencies."""
        env_status: Dict[str, Any] = {
            "python_available": True,
            "uv_available": False,
            "dependencies_installed": False,
            "yahoo_credentials": False,
            "issues": []
        }
        
        # Check UV
        try:
            result = subprocess.run(
                ["uv", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            env_status["uv_available"] = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            env_status["issues"].append("UV package manager not found - install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        
        # Check dependencies
        try:
            import pytest
            import unittest
            env_status["dependencies_installed"] = True
        except ImportError as e:
            env_status["issues"].append(f"Missing Python dependencies: {e}")
            env_status["dependencies_installed"] = False
        
        # Check Yahoo credentials (for integration tests)
        yahoo_vars = ["YAHOO_CONSUMER_KEY", "YAHOO_CONSUMER_SECRET"]
        if all(os.environ.get(var) for var in yahoo_vars):
            env_status["yahoo_credentials"] = True
        
        return env_status
    
    def run_functional_tests(self, verbose: bool = False, specific_test: Optional[str] = None) -> Dict[str, Any]:
        """Run mock-based functional tests."""
        print("Running Functional Tests (Mock-based)")
        print("=" * 60)
        
        results: Dict[str, Any] = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "test_results": {}
        }
        
        # Determine which tests to run
        if specific_test:
            tests_to_run = [specific_test] if specific_test in self.functional_tests else []
            if not tests_to_run:
                print(f"ERROR: Test file '{specific_test}' not found in functional tests")
                return results
        else:
            tests_to_run = self.functional_tests
        
        for test_file in tests_to_run:
            test_path = self.functional_dir / test_file
            
            if not test_path.exists():
                print(f"SKIP: {test_file} - file not found")
                continue
            
            print(f"\nRunning {test_file}")
            print("-" * 40)
            
            try:
                # Run individual test file
                cmd = [
                    sys.executable, 
                    str(test_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=300  # 5 minute timeout per test file
                )
                
                if verbose or result.returncode != 0:
                    print(result.stdout)
                    if result.stderr:
                        print("STDERR:", result.stderr)
                
                if result.returncode == 0:
                    print(f"PASS: {test_file}")
                    results["passed"] += 1
                else:
                    print(f"FAIL: {test_file}")
                    results["failed"] += 1
                    results["errors"].append({
                        "test": test_file,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    })
                
                results["test_results"][test_file] = {
                    "passed": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
            except subprocess.TimeoutExpired:
                print(f"TIMEOUT: {test_file} (5 minutes)")
                results["failed"] += 1
                results["errors"].append({
                    "test": test_file,
                    "error": "Test timeout after 5 minutes"
                })
            
            except Exception as e:
                print(f"ERROR: {test_file} - ERROR ({e})")
                results["failed"] += 1
                results["errors"].append({
                    "test": test_file,
                    "error": str(e)
                })
        
        return results
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests with real Yahoo API."""
        print("\nRunning Integration Tests (Real Yahoo API)")
        print("=" * 60)
        
        results: Dict[str, Any] = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "test_results": {}
        }
        
        # Check credentials first
        env_status = self.check_environment()
        if not env_status["yahoo_credentials"]:
            print("WARNING: Skipping integration tests - Yahoo credentials not found")
            print("   Set YAHOO_CONSUMER_KEY and YAHOO_CONSUMER_SECRET environment variables")
            results["skipped"] = len(self.integration_tests)
            return results
        
        if not self.integration_tests:
            print("WARNING: No integration test files found")
            results["skipped"] = 1
            return results
        
        for test_file in self.integration_tests:
            test_path = self.integration_dir / test_file
            
            if not test_path.exists():
                print(f"WARNING: {test_file} - SKIP (file not found)")
                results["skipped"] += 1
                continue
            
            print(f"\nRunning {test_file}")
            print("-" * 40)
            
            try:
                cmd = [sys.executable, str(test_path)]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=600  # 10 minute timeout for real API calls
                )
                
                if verbose or result.returncode != 0:
                    print(result.stdout)
                    if result.stderr:
                        print("STDERR:", result.stderr)
                
                if result.returncode == 0:
                    print(f"PASS: {test_file}")
                    results["passed"] += 1
                else:
                    print(f"FAIL: {test_file}")
                    results["failed"] += 1
                    results["errors"].append({
                        "test": test_file,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    })
                
                results["test_results"][test_file] = {
                    "passed": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
            except subprocess.TimeoutExpired:
                print(f"TIMEOUT: {test_file} - TIMEOUT (10 minutes)")
                results["failed"] += 1
            except Exception as e:
                print(f"ERROR: {test_file} - ERROR ({e})")
                results["failed"] += 1
        
        return results
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis including static analysis."""
        print("\nRunning Comprehensive Analysis")
        print("=" * 60)
        
        analysis_results: Dict[str, Any] = {
            "static_analysis": {"passed": False, "issues": []},
            "coverage_analysis": {"passed": False, "coverage": 0},
            "performance_check": {"passed": False, "issues": []}
        }
        
        # Run static analysis
        try:
            print("Running static analysis...")
            
            # Run ruff
            try:
                result = subprocess.run(
                    ["uv", "run", "ruff", "check", "src/", "--output-format", "json"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.stdout.strip():
                    issues = json.loads(result.stdout)
                    analysis_results["static_analysis"]["issues"].extend([
                        f"Ruff: {issue['filename']}:{issue['location']['row']} - {issue['message']}"
                        for issue in issues
                    ])
                else:
                    print("PASS: Ruff analysis passed")
                    analysis_results["static_analysis"]["passed"] = True
                    
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
                print("WARNING: Ruff not available")
            
            # Run mypy
            try:
                result = subprocess.run(
                    ["uv", "run", "mypy", "src/league_analysis_mcp_server/", "--ignore-missing-imports"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    print("PASS: MyPy analysis passed")
                else:
                    mypy_issues = [
                        line.strip() for line in result.stdout.split('\n') 
                        if 'error:' in line
                    ]
                    analysis_results["static_analysis"]["issues"].extend([
                        f"MyPy: {issue}" for issue in mypy_issues
                    ])
                    
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("WARNING: MyPy not available")
        
        except Exception as e:
            analysis_results["static_analysis"]["issues"].append(f"Static analysis error: {e}")
        
        return analysis_results
    
    def generate_report(self, functional_results: Dict, integration_results: Dict, 
                       analysis_results: Dict) -> str:
        """Generate comprehensive test report."""
        report_lines = []
        
        report_lines.append("League Analysis MCP Server - Functional Test Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Report generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        total_functional = functional_results["passed"] + functional_results["failed"]
        total_integration = integration_results["passed"] + integration_results["failed"] + integration_results.get("skipped", 0)
        
        report_lines.append("SUMMARY")
        report_lines.append("-" * 20)
        report_lines.append(f"Functional Tests: {functional_results['passed']}/{total_functional} passed")
        report_lines.append(f"Integration Tests: {integration_results['passed']}/{total_integration} passed ({integration_results.get('skipped', 0)} skipped)")
        report_lines.append("")
        
        # Functional test details
        if total_functional > 0:
            report_lines.append("FUNCTIONAL TEST RESULTS")
            report_lines.append("-" * 30)
            
            for test_file in self.functional_tests:
                if test_file in functional_results["test_results"]:
                    result = functional_results["test_results"][test_file]
                    status = "PASSED" if result["passed"] else "FAILED"
                    report_lines.append(f"{status} - {test_file}")
            report_lines.append("")
        
        # Integration test details
        if total_integration > 0:
            report_lines.append("INTEGRATION TEST RESULTS")
            report_lines.append("-" * 32)
            
            for test_file in self.integration_tests:
                if test_file in integration_results["test_results"]:
                    result = integration_results["test_results"][test_file]
                    status = "PASSED" if result["passed"] else "FAILED"
                    report_lines.append(f"{status} - {test_file}")
                else:
                    report_lines.append(f"SKIPPED - {test_file}")
            report_lines.append("")
        
        # Static analysis
        if analysis_results["static_analysis"]["issues"]:
            report_lines.append("STATIC ANALYSIS ISSUES")
            report_lines.append("-" * 25)
            for issue in analysis_results["static_analysis"]["issues"][:10]:  # Limit to first 10
                report_lines.append(f"  - {issue}")
            
            if len(analysis_results["static_analysis"]["issues"]) > 10:
                remaining = len(analysis_results["static_analysis"]["issues"]) - 10
                report_lines.append(f"  ... and {remaining} more issues")
            report_lines.append("")
        
        # Errors
        if functional_results["errors"] or integration_results["errors"]:
            report_lines.append("DETAILED ERRORS")
            report_lines.append("-" * 18)
            
            for error in functional_results["errors"]:
                report_lines.append(f"Functional - {error['test']}:")
                if "error" in error:
                    report_lines.append(f"  {error['error']}")
                else:
                    report_lines.append(f"  {error.get('stderr', 'Unknown error')}")
                report_lines.append("")
            
            for error in integration_results["errors"]:
                report_lines.append(f"Integration - {error['test']}:")
                if "error" in error:
                    report_lines.append(f"  {error['error']}")
                else:
                    report_lines.append(f"  {error.get('stderr', 'Unknown error')}")
                report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 17)
        
        if functional_results["failed"] > 0:
            report_lines.append("• Fix failing functional tests before production deployment")
        
        if integration_results.get("skipped", 0) > 0:
            report_lines.append("• Set up Yahoo API credentials to enable integration testing")
        
        if analysis_results["static_analysis"]["issues"]:
            report_lines.append("• Address static analysis issues to improve code quality")
        
        if functional_results["passed"] + integration_results["passed"] == 0:
            report_lines.append("• Critical: No tests are passing - investigate test framework setup")
        
        return "\n".join(report_lines)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run functional tests for League Analysis MCP Server"
    )
    parser.add_argument(
        "--mode", 
        choices=["functional", "integration", "all"],
        default="all",
        help="Test mode to run (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--test",
        help="Run specific test file (functional tests only)"
    )
    parser.add_argument(
        "--report",
        help="Save detailed report to file"
    )
    parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip static analysis"
    )
    
    args = parser.parse_args()
    
    runner = FunctionalTestRunner()
    
    # Check environment
    print("Environment Check")
    print("=" * 20)
    env_status = runner.check_environment()
    
    for issue in env_status["issues"]:
        print(f"WARNING: {issue}")
    
    if env_status["issues"]:
        print("\nERROR: Environment issues found. Please resolve before running tests.")
        return 1
    else:
        print("PASS: Environment ready for testing\n")
    
    # Initialize results with proper typing
    functional_results: Dict[str, Any] = {"passed": 0, "failed": 0, "errors": [], "test_results": {}}
    integration_results: Dict[str, Any] = {"passed": 0, "failed": 0, "skipped": 0, "errors": [], "test_results": {}}
    analysis_results: Dict[str, Any] = {"static_analysis": {"passed": True, "issues": []}}
    
    # Run tests based on mode
    if args.mode in ["functional", "all"]:
        functional_results = runner.run_functional_tests(args.verbose, args.test)
    
    if args.mode in ["integration", "all"] and not args.test:
        integration_results = runner.run_integration_tests(args.verbose)
    
    if not args.no_analysis and args.mode == "all":
        analysis_results = runner.run_comprehensive_analysis()
    
    # Generate and display report
    report = runner.generate_report(functional_results, integration_results, analysis_results)
    print("\n" + report)
    
    # Save report if requested
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {args.report}")
    
    # Determine exit code
    total_failed = functional_results["failed"] + integration_results["failed"]
    
    if total_failed == 0:
        print("\nSUCCESS: All tests passed!")
        return 0
    else:
        print(f"\nFAILED: {total_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
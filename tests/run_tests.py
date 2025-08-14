#!/usr/bin/env python3
"""
Test Runner for Financial Data Streaming System
Comprehensive test execution with reporting and CI/CD integration
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
import shutil

class TestRunner:
    """Comprehensive test runner for the Financial Data Streaming System."""
    
    def __init__(self, args):
        self.args = args
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.results_dir = self.project_root / "test_results"
        self.coverage_dir = self.results_dir / "coverage"
        
        # Create results directory
        self.results_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.test_config = {
            "unit": {
                "path": "tests/unit",
                "markers": "unit",
                "description": "Unit Tests"
            },
            "integration": {
                "path": "tests/integration",
                "markers": "integration",
                "description": "Integration Tests"
            },
            "performance": {
                "path": "tests/performance",
                "markers": "performance",
                "description": "Performance Tests"
            },
            "api": {
                "path": "tests/unit",
                "markers": "api",
                "description": "API Tests"
            }
        }
    
    def install_dependencies(self):
        """Install test dependencies."""
        print("🔧 Installing test dependencies...")
        
        try:
            # Install test requirements
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", 
                str(self.test_dir / "requirements.txt")
            ], check=True, capture_output=True)
            
            print("✅ Test dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def run_unit_tests(self):
        """Run unit tests."""
        print("\n🧪 Running Unit Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "unit"),
            "-v",
            "--tb=short",
            "--strict-markers",
            "-m", "unit",
            f"--junitxml={self.results_dir}/unit_tests.xml",
            f"--html={self.results_dir}/unit_tests.html",
            "--self-contained-html"
        ]
        
        if self.args.coverage:
            cmd.extend([
                "--cov=ec2_api_server",
                "--cov=ec2_stream_receiver", 
                "--cov=ec2_driver",
                "--cov=events",
                "--cov=config",
                "--cov=monitoring",
                f"--cov-report=html:{self.coverage_dir}/unit",
                f"--cov-report=xml:{self.coverage_dir}/unit_coverage.xml"
            ])
        
        return self._run_tests(cmd, "unit")
    
    def run_integration_tests(self):
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "integration"),
            "-v",
            "--tb=short",
            "--strict-markers",
            "-m", "integration",
            f"--junitxml={self.results_dir}/integration_tests.xml",
            f"--html={self.results_dir}/integration_tests.html",
            "--self-contained-html"
        ]
        
        if self.args.coverage:
            cmd.extend([
                "--cov=ec2_api_server",
                "--cov=ec2_stream_receiver",
                "--cov=ec2_driver", 
                "--cov=events",
                "--cov=config",
                "--cov=monitoring",
                f"--cov-report=html:{self.coverage_dir}/integration",
                f"--cov-report=xml:{self.coverage_dir}/integration_coverage.xml"
            ])
        
        return self._run_tests(cmd, "integration")
    
    def run_performance_tests(self):
        """Run performance tests."""
        print("\n⚡ Running Performance Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "performance"),
            "-v",
            "--tb=short",
            "--strict-markers",
            "-m", "performance",
            f"--junitxml={self.results_dir}/performance_tests.xml",
            f"--html={self.results_dir}/performance_tests.html",
            "--self-contained-html"
        ]
        
        return self._run_tests(cmd, "performance")
    
    def run_api_tests(self):
        """Run API tests."""
        print("\n🌐 Running API Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "unit"),
            "-v",
            "--tb=short",
            "--strict-markers",
            "-m", "api",
            f"--junitxml={self.results_dir}/api_tests.xml",
            f"--html={self.results_dir}/api_tests.html",
            "--self-contained-html"
        ]
        
        return self._run_tests(cmd, "api")
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n🚀 Running All Tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-v",
            "--tb=short",
            "--strict-markers",
            f"--junitxml={self.results_dir}/all_tests.xml",
            f"--html={self.results_dir}/all_tests.html",
            "--self-contained-html"
        ]
        
        if self.args.coverage:
            cmd.extend([
                "--cov=ec2_api_server",
                "--cov=ec2_stream_receiver",
                "--cov=ec2_driver",
                "--cov=events", 
                "--cov=config",
                "--cov=monitoring",
                f"--cov-report=html:{self.coverage_dir}/all",
                f"--cov-report=xml:{self.coverage_dir}/all_coverage.xml",
                "--cov-report=term-missing"
            ])
        
        return self._run_tests(cmd, "all")
    
    def _run_tests(self, cmd, test_type):
        """Execute test command and capture results."""
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            end_time = time.time()
            
            # Save test output
            output_file = self.results_dir / f"{test_type}_output.txt"
            with open(output_file, 'w') as f:
                f.write(f"Test Type: {test_type}\n")
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Duration: {end_time - start_time:.2f}s\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write("\n=== STDOUT ===\n")
                f.write(result.stdout)
                f.write("\n=== STDERR ===\n")
                f.write(result.stderr)
            
            # Print summary
            print(f"⏱️  Duration: {end_time - start_time:.2f}s")
            print(f"📊 Exit Code: {result.returncode}")
            
            if result.returncode == 0:
                print(f"✅ {test_type.title()} tests passed")
            else:
                print(f"❌ {test_type.title()} tests failed")
                print("📄 Check output file for details:", output_file)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running {test_type} tests: {e}")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📊 Generating Test Report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": "Financial Data Streaming System",
            "test_summary": {},
            "coverage": {},
            "recommendations": []
        }
        
        # Collect test results
        for test_type in ["unit", "integration", "performance", "api"]:
            xml_file = self.results_dir / f"{test_type}_tests.xml"
            if xml_file.exists():
                # Parse XML results (simplified)
                report["test_summary"][test_type] = {
                    "status": "completed",
                    "file": str(xml_file)
                }
            else:
                report["test_summary"][test_type] = {
                    "status": "not_run",
                    "file": None
                }
        
        # Collect coverage data
        if self.args.coverage:
            coverage_file = self.coverage_dir / "all_coverage.xml"
            if coverage_file.exists():
                report["coverage"]["overall"] = "available"
                report["coverage"]["file"] = str(coverage_file)
        
        # Generate recommendations
        if not report["test_summary"].get("unit", {}).get("status") == "completed":
            report["recommendations"].append("Run unit tests to ensure code quality")
        
        if not report["test_summary"].get("integration", {}).get("status") == "completed":
            report["recommendations"].append("Run integration tests to verify system components work together")
        
        if not report["test_summary"].get("performance", {}).get("status") == "completed":
            report["recommendations"].append("Run performance tests to ensure system meets performance requirements")
        
        # Save report
        report_file = self.results_dir / "test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Test report saved to: {report_file}")
        return report
    
    def run_linting(self):
        """Run code linting."""
        print("\n🔍 Running Code Linting...")
        
        try:
            # Run flake8
            flake8_result = subprocess.run([
                sys.executable, "-m", "flake8",
                str(self.project_root / "ec2_api_server"),
                str(self.project_root / "ec2_stream_receiver"),
                str(self.project_root / "ec2_driver"),
                str(self.project_root / "events"),
                str(self.project_root / "config"),
                str(self.project_root / "monitoring"),
                "--max-line-length=100",
                "--ignore=E501,W503"
            ], capture_output=True, text=True)
            
            # Run black check
            black_result = subprocess.run([
                sys.executable, "-m", "black",
                "--check",
                str(self.project_root / "ec2_api_server"),
                str(self.project_root / "ec2_stream_receiver"),
                str(self.project_root / "ec2_driver"),
                str(self.project_root / "events"),
                str(self.project_root / "config"),
                str(self.project_root / "monitoring")
            ], capture_output=True, text=True)
            
            # Save linting results
            lint_file = self.results_dir / "linting_results.txt"
            with open(lint_file, 'w') as f:
                f.write("=== FLAKE8 RESULTS ===\n")
                f.write(f"Exit Code: {flake8_result.returncode}\n")
                f.write(flake8_result.stdout)
                f.write(flake8_result.stderr)
                f.write("\n=== BLACK RESULTS ===\n")
                f.write(f"Exit Code: {black_result.returncode}\n")
                f.write(black_result.stdout)
                f.write(black_result.stderr)
            
            if flake8_result.returncode == 0 and black_result.returncode == 0:
                print("✅ Code linting passed")
                return True
            else:
                print("❌ Code linting failed")
                print(f"📄 Check linting results: {lint_file}")
                return False
                
        except Exception as e:
            print(f"❌ Error running linting: {e}")
            return False
    
    def run_security_scan(self):
        """Run security scanning."""
        print("\n🔒 Running Security Scan...")
        
        try:
            # Run bandit for security scanning
            bandit_result = subprocess.run([
                sys.executable, "-m", "bandit",
                "-r",
                str(self.project_root / "ec2_api_server"),
                str(self.project_root / "ec2_stream_receiver"),
                str(self.project_root / "ec2_driver"),
                str(self.project_root / "events"),
                str(self.project_root / "config"),
                str(self.project_root / "monitoring"),
                "-f", "json",
                "-o", str(self.results_dir / "security_scan.json")
            ], capture_output=True, text=True)
            
            if bandit_result.returncode == 0:
                print("✅ Security scan completed")
                return True
            else:
                print("⚠️ Security scan found issues")
                print(f"📄 Check security results: {self.results_dir}/security_scan.json")
                return False
                
        except Exception as e:
            print(f"❌ Error running security scan: {e}")
            return False
    
    def cleanup(self):
        """Clean up test artifacts."""
        if self.args.cleanup:
            print("\n🧹 Cleaning up test artifacts...")
            
            # Remove test cache
            cache_dirs = [
                self.project_root / ".pytest_cache",
                self.project_root / "__pycache__",
                self.test_dir / "__pycache__"
            ]
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
            
            print("✅ Cleanup completed")
    
    def run(self):
        """Main test runner execution."""
        print("🚀 Financial Data Streaming System - Test Runner")
        print("=" * 60)
        
        # Install dependencies if needed
        if self.args.install_deps:
            if not self.install_dependencies():
                return False
        
        # Run linting
        if self.args.lint:
            if not self.run_linting():
                if self.args.strict:
                    return False
        
        # Run security scan
        if self.args.security:
            if not self.run_security_scan():
                if self.args.strict:
                    return False
        
        # Run tests based on type
        test_results = {}
        
        if self.args.test_type == "unit":
            test_results["unit"] = self.run_unit_tests()
        elif self.args.test_type == "integration":
            test_results["integration"] = self.run_integration_tests()
        elif self.args.test_type == "performance":
            test_results["performance"] = self.run_performance_tests()
        elif self.args.test_type == "api":
            test_results["api"] = self.run_api_tests()
        elif self.args.test_type == "all":
            test_results["all"] = self.run_all_tests()
        else:
            # Run all test types
            test_results["unit"] = self.run_unit_tests()
            test_results["integration"] = self.run_integration_tests()
            test_results["performance"] = self.run_performance_tests()
            test_results["api"] = self.run_api_tests()
        
        # Generate report
        report = self.generate_test_report()
        
        # Cleanup
        self.cleanup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for test_type, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_type.title():15} {status}")
        
        print(f"\n📄 Results directory: {self.results_dir}")
        print(f"📊 Coverage directory: {self.coverage_dir}")
        
        # Return overall success
        return all(test_results.values())

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Financial Data Streaming System Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_tests.py
  
  # Run only unit tests
  python run_tests.py --test-type unit
  
  # Run with coverage
  python run_tests.py --coverage
  
  # Run with linting and security scan
  python run_tests.py --lint --security
  
  # Install dependencies and run tests
  python run_tests.py --install-deps --test-type all
  
  # Run in strict mode (fail on linting/security issues)
  python run_tests.py --strict --lint --security
        """
    )
    
    parser.add_argument(
        "--test-type",
        choices=["unit", "integration", "performance", "api", "all"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage reports"
    )
    
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run code linting"
    )
    
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security scanning"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies"
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on linting or security issues"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        default=True,
        help="Clean up test artifacts"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    args = parser.parse_args()
    
    # Create and run test runner
    runner = TestRunner(args)
    success = runner.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
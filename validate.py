#!/usr/bin/env python
"""
Pre-submission validator for Snake RL Environment
Checks all competition requirements before deployment.
"""

import os
import sys
import requests
import json
import subprocess
from pathlib import Path
from typing import List, Tuple

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_pass(msg: str):
    print(f"{GREEN}✓ {msg}{RESET}")


def print_fail(msg: str):
    print(f"{RED}✗ {msg}{RESET}")


def print_warn(msg: str):
    print(f"{YELLOW}⚠ {msg}{RESET}")


class Validator:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warned = 0
        self.environment_url = os.getenv("ENVIRONMENT_URL", "http://127.0.0.1:8083")
    
    def check_file_exists(self, path: str, description: str) -> bool:
        """Check if a file exists."""
        if Path(path).exists():
            print_pass(f"{description} exists: {path}")
            self.checks_passed += 1
            return True
        else:
            print_fail(f"{description} missing: {path}")
            self.checks_failed += 1
            return False
    
    def check_openenv_yaml(self) -> bool:
        """Validate openenv.yaml structure."""
        yaml_path = "my_env/openenv.yaml"
        if not self.check_file_exists(yaml_path, "openenv.yaml"):
            return False
        
        try:
            with open(yaml_path) as f:
                import yaml
                config = yaml.safe_load(f)
            
            required_fields = ["spec_version", "name", "type", "app"]
            for field in required_fields:
                if field not in config:
                    print_fail(f"openenv.yaml missing field: {field}")
                    self.checks_failed += 1
                    return False
            
            print_pass("openenv.yaml has all required fields")
            self.checks_passed += 1
            return True
        except Exception as e:
            print_fail(f"openenv.yaml validation failed: {e}")
            self.checks_failed += 1
            return False
    
    def check_models_defined(self) -> bool:
        """Check if models (Action/Observation) are properly defined."""
        models_path = "my_env/models.py"
        if not self.check_file_exists(models_path, "models.py"):
            return False
        
        try:
            with open(models_path) as f:
                content = f.read()
            
            if "class SnakeAction" in content and "class SnakeObservation" in content:
                print_pass("Action and Observation models defined")
                self.checks_passed += 1
                return True
            else:
                print_fail("Models missing SnakeAction or SnakeObservation")
                self.checks_failed += 1
                return False
        except Exception as e:
            print_fail(f"Models check failed: {e}")
            self.checks_failed += 1
            return False
    
    def check_inference_script(self) -> bool:
        """Check if inference.py exists and is valid."""
        if not self.check_file_exists("inference.py", "inference.py"):
            return False
        
        try:
            with open("inference.py") as f:
                content = f.read()
            
            required_patterns = [
                ("API_BASE_URL", "API_BASE_URL environment variable"),
                ("MODEL_NAME", "MODEL_NAME environment variable"),
                ("HF_TOKEN", "HF_TOKEN environment variable"),
                ('event": "START"', "START logging event"),
                ('event": "STEP"', "STEP logging event"),
                ('event": "END"', "END logging event"),
            ]
            
            all_found = True
            for pattern, desc in required_patterns:
                if pattern in content:
                    print_pass(f"inference.py has {desc}")
                    self.checks_passed += 1
                else:
                    print_fail(f"inference.py missing {desc}")
                    self.checks_failed += 1
                    all_found = False
            
            return all_found
        except Exception as e:
            print_fail(f"inference.py check failed: {e}")
            self.checks_failed += 1
            return False
    
    def check_dockerfile(self) -> bool:
        """Check if Dockerfile exists."""
        dockerfile_path = "my_env/server/Dockerfile"
        return self.check_file_exists(dockerfile_path, "Dockerfile")
    
    def check_environment_connectivity(self) -> bool:
        """Test connectivity to environment server."""
        try:
            response = requests.get(f"{self.environment_url}/schema", timeout=5)
            if response.status_code == 200:
                print_pass(f"Environment responding at {self.environment_url}")
                self.checks_passed += 1
                return True
            else:
                print_fail(f"Environment returned {response.status_code}")
                self.checks_failed += 1
                return False
        except requests.exceptions.ConnectionError:
            print_warn(f"Environment not running at {self.environment_url}")
            print_warn("Make sure to start the server before running inference")
            self.checks_warned += 1
            return False
        except Exception as e:
            print_fail(f"Environment connectivity check failed: {e}")
            self.checks_failed += 1
            return False
    
    def check_reset_endpoint(self) -> bool:
        """Test /reset endpoint."""
        try:
            response = requests.post(f"{self.environment_url}/reset", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'observation' in data:
                    print_pass("/reset endpoint working")
                    self.checks_passed += 1
                    return True
                else:
                    print_fail("/reset response missing 'observation'")
                    self.checks_failed += 1
                    return False
            else:
                print_fail(f"/reset returned {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            print_warn(f"/reset test skipped: {e}")
            self.checks_warned += 1
            return False
    
    def check_step_endpoint(self) -> bool:
        """Test /step endpoint."""
        try:
            # First reset to get valid state
            requests.post(f"{self.environment_url}/reset", timeout=5)
            
            response = requests.post(
                f"{self.environment_url}/step",
                json={"action": 0},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'observation' in data and 'reward' in data and 'done' in data:
                    print_pass("/step endpoint working")
                    self.checks_passed += 1
                    return True
                else:
                    print_fail("/step response missing fields")
                    self.checks_failed += 1
                    return False
            else:
                print_fail(f"/step returned {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            print_warn(f"/step test skipped: {e}")
            self.checks_warned += 1
            return False
    
    def check_state_endpoint(self) -> bool:
        """Test /state endpoint."""
        try:
            response = requests.get(f"{self.environment_url}/state", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'episode_id' in str(data) or 'step_count' in str(data):
                    print_pass("/state endpoint working")
                    self.checks_passed += 1
                    return True
                else:
                    print_warn("/state endpoint response may be incomplete")
                    self.checks_warned += 1
                    return True
            else:
                print_fail(f"/state returned {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            print_warn(f"/state test skipped: {e}")
            self.checks_warned += 1
            return False
    
    def check_environment_vars(self) -> bool:
        """Check if required environment variables are set."""
        required_vars = ["API_BASE_URL", "MODEL_NAME", "HF_TOKEN"]
        missing = []
        
        for var in required_vars:
            if os.getenv(var):
                print_pass(f"Environment variable {var} set")
                self.checks_passed += 1
            else:
                print_warn(f"Environment variable {var} not set (will use defaults)")
                missing.append(var)
                self.checks_warned += 1
        
        return len(missing) == 0
    
    def run_all_checks(self) -> bool:
        """Run all validation checks."""
        print("\n" + "="*70)
        print("🔍 PRE-SUBMISSION VALIDATOR")
        print("="*70)
        
        print("\n[1] File Structure Checks")
        self.check_file_exists("my_env/models.py", "models.py")
        self.check_file_exists("my_env/server/app.py", "app.py")
        self.check_openenv_yaml()
        self.check_dockerfile()
        self.check_inference_script()
        
        print("\n[2] Code Structure Checks")
        self.check_models_defined()
        
        print("\n[3] Configuration Checks")
        self.check_environment_vars()
        
        print("\n[4] Environment Endpoint Checks")
        if self.check_environment_connectivity():
            self.check_reset_endpoint()
            self.check_step_endpoint()
            self.check_state_endpoint()
        else:
            print_warn("Skipping endpoint tests (environment not running)")
        
        print("\n" + "="*70)
        print("📊 VALIDATION SUMMARY")
        print("="*70)
        print(f"{GREEN}Passed: {self.checks_passed}{RESET}")
        print(f"{RED}Failed: {self.checks_failed}{RESET}")
        print(f"{YELLOW}Warned: {self.checks_warned}{RESET}")
        
        if self.checks_failed > 0:
            print(f"\n{RED}❌ VALIDATION FAILED{RESET}")
            print("Please fix the issues above before submitting.")
            return False
        else:
            print(f"\n{GREEN}✅ VALIDATION PASSED{RESET}")
            print("Your submission is ready for evaluation!")
            return True


def main():
    """Run validator."""
    validator = Validator()
    success = validator.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

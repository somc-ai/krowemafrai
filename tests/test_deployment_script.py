#!/usr/bin/env python3
"""
Test script voor deploy-backend-auto.sh validation
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def test_script_exists():
    """Test if deployment script exists and is executable"""
    script_path = Path("deploy-backend-auto.sh")
    assert script_path.exists(), "deploy-backend-auto.sh niet gevonden"
    assert os.access(script_path, os.X_OK), "deploy-backend-auto.sh is niet uitvoerbaar"
    print("✅ Script bestaat en is uitvoerbaar")

def test_help_option():
    """Test --help option"""
    success, stdout, stderr = run_command("./deploy-backend-auto.sh --help")
    assert success, f"Help optie faalde: {stderr}"
    assert "Automated Backend Deployment Script" in stdout, "Help tekst niet gevonden"
    assert "--skip-confirm" in stdout, "Skip confirm optie niet in help"
    print("✅ Help functionaliteit werkt")

def test_prerequisites_check():
    """Test prerequisites validation zonder Azure login"""
    # Test met timeout omdat Azure login check kan lang duren
    success, stdout, stderr = run_command("timeout 10 ./deploy-backend-auto.sh --skip-confirm 2>&1 | head -20")
    
    # Script moet prerequisites checken
    assert "Checking prerequisites" in stdout or "Checking prerequisites" in stderr, "Prerequisites check niet gevonden"
    print("✅ Prerequisites check wordt uitgevoerd")

def test_docker_requirement():
    """Test dat Docker beschikbaar is (vereiste voor script)"""
    success, stdout, stderr = run_command("docker --version")
    assert success, "Docker is niet beschikbaar"
    print("✅ Docker is beschikbaar")

def test_azure_cli_requirement():
    """Test dat Azure CLI beschikbaar is (vereiste voor script)"""
    success, stdout, stderr = run_command("az --version")
    assert success, "Azure CLI is niet beschikbaar"
    print("✅ Azure CLI is beschikbaar")

def test_script_syntax():
    """Test bash script syntax"""
    success, stdout, stderr = run_command("bash -n deploy-backend-auto.sh")
    assert success, f"Bash syntax error: {stderr}"
    print("✅ Bash syntax is correct")

def test_dockerfile_exists():
    """Test dat Dockerfile.azure bestaat"""
    dockerfile_path = Path("src/backend/Dockerfile.azure")
    assert dockerfile_path.exists(), "src/backend/Dockerfile.azure niet gevonden"
    print("✅ Dockerfile.azure bestaat")

def test_backend_directory():
    """Test dat backend directory bestaat"""
    backend_dir = Path("src/backend")
    assert backend_dir.exists(), "src/backend directory niet gevonden"
    assert backend_dir.is_dir(), "src/backend is geen directory"
    print("✅ Backend directory bestaat")

def test_script_variables():
    """Test dat script juiste Azure variabelen bevat"""
    with open("deploy-backend-auto.sh", "r") as f:
        content = f.read()
    
    assert "ca2a76f03945acr" in content, "ACR naam niet gevonden in script"
    assert "rg-info-2259" in content, "Resource group niet gevonden in script"
    assert "backend-aiagents-gov" in content, "Container app naam niet gevonden in script"
    print("✅ Azure configuratie variabelen zijn correct")

def main():
    """Run all tests"""
    print("🧪 Testing deploy-backend-auto.sh script...")
    print("=" * 50)
    
    # Change to repo root directory
    os.chdir(Path(__file__).parent.parent)
    
    tests = [
        test_script_exists,
        test_script_syntax,
        test_help_option,
        test_docker_requirement,
        test_azure_cli_requirement,
        test_dockerfile_exists,
        test_backend_directory,
        test_script_variables,
        test_prerequisites_check,
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed_tests.append(test.__name__)
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed_tests.append(test.__name__)
    
    print("=" * 50)
    
    if failed_tests:
        print(f"❌ {len(failed_tests)} tests gefaald: {', '.join(failed_tests)}")
        sys.exit(1)
    else:
        print(f"✅ Alle {len(tests)} tests geslaagd!")
        print("🎉 deploy-backend-auto.sh is klaar voor gebruik!")

if __name__ == "__main__":
    main()
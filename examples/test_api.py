#!/usr/bin/env python3
"""
Test script for ModelSwitch API functionality.
"""

import requests
import json
import time
import random
from typing import List


class ModelSwitchTester:
    """Test client for ModelSwitch API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self) -> dict:
        """Check API health."""
        response = requests.get(f"{self.base_url}/healthz")
        return response.json()
    
    def get_models_info(self) -> List[dict]:
        """Get information about all models."""
        response = requests.get(f"{self.base_url}/admin/models")
        return response.json()
    
    def set_active_version(self, version: str) -> dict:
        """Set the active model version."""
        data = {"version": version}
        response = requests.post(f"{self.base_url}/admin/set-active-version", json=data)
        return response.json()
    
    def make_prediction(self, features: List[float], version: str = None) -> dict:
        """Make a prediction."""
        data = {"features": features}
        if version:
            data["version"] = version
        
        response = requests.post(f"{self.base_url}/predict", json=data)
        return response.json()
    
    def generate_test_features(self, n_features: int = 10) -> List[float]:
        """Generate random test features."""
        return [random.uniform(-2, 2) for _ in range(n_features)]


def test_basic_functionality():
    """Test basic API functionality."""
    print("🧪 Testing ModelSwitch API...")
    
    tester = ModelSwitchTester()
    
    # Health check
    print("\n1. Health Check:")
    try:
        health = tester.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Active Version: {health['active_version']}")
        print(f"   Available Versions: {health['available_versions']}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    # Get models info
    print("\n2. Models Information:")
    try:
        models_info = tester.get_models_info()
        for model in models_info:
            print(f"   {model['version']}: {'✅' if model['active'] else '❌'} "
                  f"(loaded: {model['loaded']}, size: {model.get('file_size', 0)} bytes)")
    except Exception as e:
        print(f"   ❌ Failed to get models info: {e}")
    
    # Test predictions
    print("\n3. Making Predictions:")
    
    # Test with active version
    try:
        features = tester.generate_test_features(10)
        result = tester.make_prediction(features)
        print(f"   Active version prediction: {result['prediction']}")
        print(f"   Model version used: {result['model_version']}")
        print(f"   Latency: {result['latency_ms']:.2f}ms")
    except Exception as e:
        print(f"   ❌ Prediction failed: {e}")
    
    # Test with specific version (if available)
    if health['available_versions']:
        try:
            test_version = health['available_versions'][0]
            features = tester.generate_test_features(10)
            result = tester.make_prediction(features, version=test_version)
            print(f"   Version {test_version} prediction: {result['prediction']}")
            print(f"   Latency: {result['latency_ms']:.2f}ms")
        except Exception as e:
            print(f"   ❌ Version-specific prediction failed: {e}")


def test_version_switching():
    """Test version switching functionality."""
    print("\n🔄 Testing Version Switching:")
    
    tester = ModelSwitchTester()
    
    # Get current state
    health = tester.health_check()
    available_versions = health['available_versions']
    
    if len(available_versions) < 2:
        print("   ⚠️  Need at least 2 model versions to test switching")
        return
    
    # Switch to first version
    version1 = available_versions[0]
    print(f"\n   Switching to {version1}:")
    result = tester.set_active_version(version1)
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    
    # Make prediction with new active version
    features = tester.generate_test_features(10)
    pred1 = tester.make_prediction(features)
    print(f"   Prediction with {version1}: {pred1['prediction']}")
    
    # Switch to second version
    version2 = available_versions[1]
    print(f"\n   Switching to {version2}:")
    result = tester.set_active_version(version2)
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    
    # Make prediction with new active version
    features = tester.generate_test_features(10)
    pred2 = tester.make_prediction(features)
    print(f"   Prediction with {version2}: {pred2['prediction']}")


def test_load_testing():
    """Test API performance with multiple requests."""
    print("\n⚡ Load Testing:")
    
    tester = ModelSwitchTester()
    
    # Make multiple predictions
    n_requests = 10
    latencies = []
    
    print(f"   Making {n_requests} predictions...")
    
    for i in range(n_requests):
        try:
            features = tester.generate_test_features(10)
            start_time = time.time()
            result = tester.make_prediction(features)
            end_time = time.time()
            
            actual_latency = (end_time - start_time) * 1000
            reported_latency = result['latency_ms']
            
            latencies.append(actual_latency)
            
            print(f"   Request {i+1}: {result['prediction']} "
                  f"(reported: {reported_latency:.2f}ms, actual: {actual_latency:.2f}ms)")
            
        except Exception as e:
            print(f"   Request {i+1}: ❌ {e}")
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"\n   Performance Summary:")
        print(f"   Average latency: {avg_latency:.2f}ms")
        print(f"   Min latency: {min_latency:.2f}ms")
        print(f"   Max latency: {max_latency:.2f}ms")


def main():
    """Run all tests."""
    print("🚀 ModelSwitch API Testing Suite")
    print("=" * 50)
    
    # Wait a moment for API to be ready
    print("Waiting for API to be ready...")
    time.sleep(2)
    
    # Run tests
    test_basic_functionality()
    test_version_switching()
    test_load_testing()
    
    print("\n✅ Testing complete!")
    print("\n📊 Check metrics at: http://localhost:8000/metrics")
    print("📈 Check Grafana at: http://localhost:3000 (admin/admin)")


if __name__ == "__main__":
    main() 
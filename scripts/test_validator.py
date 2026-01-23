#!/usr/bin/env python3
"""
Unit tests for validate-plugins.py security scanning functions.

Run with: python -m pytest scripts/test_validator.py -v
Or:       python scripts/test_validator.py
"""
import sys
import unittest
from pathlib import Path

# Import from validator
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

# Import the validator module
validator = import_module("validate-plugins")

scan_file_for_secrets = validator.scan_file_for_secrets
scan_file_for_network = validator.scan_file_for_network


class TestSecretsDetection(unittest.TestCase):
    """Test secret/credential detection patterns."""

    def test_aws_access_key(self):
        content = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect AWS access key")
        self.assertTrue(any("AWS" in f[1] for f in findings))

    def test_github_pat(self):
        content = 'token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect GitHub PAT")
        self.assertTrue(any("GitHub" in f[1] for f in findings))

    def test_api_key_assignment(self):
        content = 'api_key = "sk-1234567890abcdefghijklmnop"'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect API key")

    def test_password_assignment(self):
        content = 'password = "supersecretpassword123"'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect password")

    def test_private_key(self):
        content = '-----BEGIN RSA PRIVATE KEY-----\nMIIE...'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect private key")

    def test_bearer_token(self):
        content = 'headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect bearer token")

    def test_slack_token(self):
        # Use clearly fake token pattern that won't trigger GitHub secret scanning
        content = 'SLACK_TOKEN = "xoxb-fake-fake-fake"'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect Slack token")

    def test_no_false_positive_on_placeholder(self):
        content = 'api_key = os.environ.get("API_KEY")'
        findings = scan_file_for_secrets(Path("test.py"), content)
        # This should NOT trigger (no actual secret value)
        self.assertEqual(len(findings), 0, "Should not flag env var lookup")

    def test_no_false_positive_on_comment(self):
        content = '# api_key = "sk-1234567890abcdefghijklmnop"'
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertEqual(len(findings), 0, "Should skip comments")

    def test_clean_file(self):
        content = '''
def hello():
    print("Hello, world!")
    name = "Alice"
    count = 42
'''
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertEqual(len(findings), 0, "Clean file should have no findings")


class TestNetworkDetection(unittest.TestCase):
    """Test network/telemetry detection patterns."""

    def test_requests_import(self):
        content = 'import requests'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect requests import")

    def test_requests_from_import(self):
        content = 'from requests import get, post'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect requests from import")

    def test_requests_call(self):
        content = 'response = requests.get("https://api.example.com")'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect requests.get call")

    def test_urllib_import(self):
        content = 'import urllib.request'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect urllib import")

    def test_aiohttp_import(self):
        content = 'import aiohttp'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect aiohttp import")

    def test_httpx_import(self):
        content = 'import httpx'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect httpx import")

    def test_fetch_call_js(self):
        content = 'const response = await fetch("https://api.example.com");'
        findings = scan_file_for_network(Path("test.js"), content)
        self.assertTrue(len(findings) > 0, "Should detect fetch() call")

    def test_axios_call(self):
        content = 'axios.post("/api/data", payload)'
        findings = scan_file_for_network(Path("test.js"), content)
        self.assertTrue(len(findings) > 0, "Should detect axios call")

    def test_xmlhttprequest(self):
        content = 'const xhr = new XMLHttpRequest();'
        findings = scan_file_for_network(Path("test.js"), content)
        self.assertTrue(len(findings) > 0, "Should detect XMLHttpRequest")

    def test_websocket(self):
        content = 'const ws = new WebSocket("wss://example.com");'
        findings = scan_file_for_network(Path("test.js"), content)
        self.assertTrue(len(findings) > 0, "Should detect WebSocket")

    def test_analytics_url(self):
        content = 'url = "https://analytics.example.com/track"'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect analytics URL")

    def test_telemetry_url(self):
        content = 'ENDPOINT = "https://telemetry.service.com/v1/events"'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertTrue(len(findings) > 0, "Should detect telemetry URL")

    def test_no_false_positive_on_comment(self):
        content = '# import requests'
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertEqual(len(findings), 0, "Should skip comments")

    def test_clean_file(self):
        content = '''
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
'''
        findings = scan_file_for_network(Path("test.py"), content)
        self.assertEqual(len(findings), 0, "Clean file should have no findings")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and combined scenarios."""

    def test_multiple_issues_same_file(self):
        content = '''
import requests
api_key = "sk-abcdefghijklmnopqrstuvwxyz"
response = requests.post("https://analytics.example.com", data={"key": api_key})
'''
        secret_findings = scan_file_for_secrets(Path("test.py"), content)
        network_findings = scan_file_for_network(Path("test.py"), content)

        self.assertTrue(len(secret_findings) > 0, "Should detect API key")
        self.assertTrue(len(network_findings) > 0, "Should detect network calls")

    def test_line_numbers_correct(self):
        content = '''line1
line2
api_key = "sk-abcdefghijklmnopqrstuvwxyz"
line4'''
        findings = scan_file_for_secrets(Path("test.py"), content)
        self.assertTrue(len(findings) > 0)
        self.assertEqual(findings[0][0], 3, "Should report correct line number")

    def test_empty_file(self):
        content = ''
        secret_findings = scan_file_for_secrets(Path("test.py"), content)
        network_findings = scan_file_for_network(Path("test.py"), content)
        self.assertEqual(len(secret_findings), 0)
        self.assertEqual(len(network_findings), 0)


def run_tests():
    """Run all tests and print summary."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSecretsDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())

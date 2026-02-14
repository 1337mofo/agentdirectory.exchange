#!/usr/bin/env python3
"""
Pre-commit security check - prevents committing credentials
Run before every commit: python pre-commit-security-check.py
"""

import subprocess
import re
import sys

print("🔒 Running security scan on staged changes...")

# Get staged diff
result = subprocess.run(
    ["git", "diff", "--cached", "--diff-filter=ACM"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("❌ Error running git diff")
    sys.exit(1)

staged_changes = result.stdout

# Security patterns to block
BLOCKED_PATTERNS = [
    (r'(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token)\s*=\s*["\'][^"\']{8,}["\']', 
     "Password/secret hardcoded"),
    (r'postgresql://[^:]+:[^@]+@', 
     "Database URL with embedded password"),
    (r'mysql://[^:]+:[^@]+@', 
     "MySQL URL with embedded password"),
    (r'mongodb://[^:]+:[^@]+@',
     "MongoDB URL with embedded password"),
    (r'(AWS|GOOGLE|AZURE)_[A-Z_]*KEY\s*=\s*["\'][^"\']+["\']',
     "Cloud API key hardcoded"),
    (r'FROM_PASSWORD\s*=\s*["\'][^"\']{8,}["\']',
     "Email password hardcoded"),
]

violations = []

for pattern, message in BLOCKED_PATTERNS:
    matches = re.findall(pattern, staged_changes, re.IGNORECASE)
    if matches:
        violations.append(f"  ❌ {message}")
        for match in matches[:3]:  # Show first 3 matches
            if isinstance(match, tuple):
                match = match[0]
            violations.append(f"     Found: {match[:60]}...")

if violations:
    print("\n❌ SECURITY VIOLATIONS DETECTED:")
    print("\n".join(violations))
    print("\n🛡️  Use environment variables for all credentials")
    print("Example: os.getenv('PASSWORD') instead of 'hardcoded_password'")
    sys.exit(1)

print("✅ Security scan passed - no credentials detected")
sys.exit(0)

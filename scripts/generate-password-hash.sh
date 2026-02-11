#!/bin/bash
#
# Helper script to generate password hash for YouTube-Watcher authentication
# Issue #41: Optional Authentication
#
# Uses PBKDF2-SHA256 with Base64 output (~64 characters, URL-safe)
#
# Usage: ./generate-password-hash.sh [password]
# If no password is provided, you will be prompted to enter one

# Get password from argument or prompt
if [ -n "$1" ]; then
    PASSWORD="$1"
else
    echo -n "Enter password: "
    read -s PASSWORD
    echo
    echo -n "Confirm password: "
    read -s PASSWORD_CONFIRM
    echo
    
    if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
        echo "Error: Passwords do not match" >&2
        exit 1
    fi
fi

if [ -z "$PASSWORD" ]; then
    echo "Error: Password cannot be empty" >&2
    exit 1
fi

echo "Generating password hash..."

# Use Python with built-in libraries (no dependencies needed)
HASH=$(python3 -c "
import base64
import hashlib
import secrets
import sys

password = sys.argv[1]
salt = secrets.token_bytes(16)
pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
combined = salt + pwdhash
# URL-safe Base64 without padding
result = base64.urlsafe_b64encode(combined).decode('ascii').rstrip('=')
print(result)
" "$PASSWORD" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$HASH" ]; then
    echo
    echo "Your password hash (paste this into your .env file):"
    echo "$HASH"
    echo
    echo "Note: Each time you run this script, you'll get a different hash."
    echo "      This is normal - the salt is randomly generated each time."
    echo
    echo "Add this to your .env file:"
    echo "  AUTH_ENABLED=true"
    echo "  AUTH_USERNAME=admin"
    echo "  AUTH_PASSWORD_HASH=$HASH"
else
    echo "Error: Failed to generate hash. Make sure Python 3 is installed." >&2
    exit 1
fi

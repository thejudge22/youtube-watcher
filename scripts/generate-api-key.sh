#!/bin/bash
#
# Helper script to generate an API key for YouTube-Watcher
#
# Generates a secure, URL-safe random API key.
#
# Usage: ./generate-api-key.sh


echo "Generating API key..."

# Use Python with built-in libraries (no dependencies needed)
API_KEY=$(python3 -c "
import secrets
import base64

# Generate a 32-byte random key and encode as URL-safe Base64
key = secrets.token_urlsafe(32)
print(key)
" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$API_KEY" ]; then
    echo
    echo "Your API key (paste this into your .env file):"
    echo "$API_KEY"
    echo
    echo "Add this to your .env file:"
    echo "  API_KEY=$API_KEY"
    echo
    echo "To authenticate requests, include this header:"
    echo "  X-API-Key: $API_KEY"
else
    echo "Error: Failed to generate API key. Make sure Python 3 is installed." >&2
    exit 1
fi

#!/bin/bash

# Get current branch name
BRANCH=$(git branch --show-current)

# Extract date-based version (handles vYYYY-MM-DD or vYYYY-MM-DD-description)
# Removes leading 'v' and keeps only the date portion (first 10 chars)
VERSION=$(echo "$BRANCH" | sed -E 's/^v//' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}')

if [ -z "$VERSION" ]; then
  # Fallback: try legacy semver format (v1.0.0)
  VERSION=$(echo "$BRANCH" | sed -E 's/^v\.?//' | grep -E '^[0-9]')
fi

if [ -z "$VERSION" ]; then
  echo "Branch name '$BRANCH' does not contain a valid version (e.g., v2026-04-20 or v1.0.0)"
  exit 1
fi

echo "Updating project version to: $VERSION"

# Update frontend package.json
if [ -f "frontend/package.json" ]; then
  sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json
  echo "Updated frontend/package.json"
fi

# You can add more files here (e.g. backend/pyproject.toml) if needed

#!/bin/bash

# Get current branch name
BRANCH=$(git branch --show-current)

# Extract version number (handles v1.0.0, v1.01, v.1.1.1)
# Removes leading 'v' or 'v.' and ensures it starts with a digit
VERSION=$(echo $BRANCH | sed -E 's/^v\.?//' | grep -E '^[0-9]')

if [ -z "$VERSION" ]; then
  echo "Branch name '$BRANCH' does not contain a valid version (e.g., v1.0.0)"
  exit 1
fi

echo "Updating project version to: $VERSION"

# Update frontend package.json
if [ -f "frontend/package.json" ]; then
  sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json
  echo "Updated frontend/package.json"
fi

# You can add more files here (e.g. backend/pyproject.toml) if needed
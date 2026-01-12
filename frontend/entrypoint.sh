#!/bin/sh
# This script ensures that node modules are installed only if the vite binary is missing.

if [ ! -f "node_modules/.bin/vite" ]; then
  echo "Vite binary not found, running 'npm install'..."
  npm install
else
  echo "Vite binary found, skipping 'npm install'."
fi

# Execute the main command (starts the dev server)
exec npm run dev -- --host

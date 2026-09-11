#!/bin/bash
# Synchronize the date-based release version across the frontend and API.
# Usage: ./scripts/update_version.sh [vYYYY-MM-DD]
# If omitted, the first vYYYY-MM-DD token is read from the branch name.

set -euo pipefail

INPUT=${1:-$(git branch --show-current)}

if [[ $INPUT =~ v?([0-9]{4}-[0-9]{2}-[0-9]{2}) ]]; then
  DATE_VERSION="${BASH_REMATCH[1]}"
else
  echo "Error: '$INPUT' does not contain a vYYYY-MM-DD version" >&2
  exit 1
fi

YEAR=${DATE_VERSION%%-*}
MONTH_DAY=${DATE_VERSION#*-}
MONTH=${MONTH_DAY%%-*}
DAY=${MONTH_DAY##*-}
SEMVER_VERSION="$((10#$YEAR)).$((10#$MONTH)).$((10#$DAY))"

(
  cd frontend
  npm version "$SEMVER_VERSION" --no-git-tag-version --allow-same-version >/dev/null
)

python3 - "$DATE_VERSION" <<'PY'
from pathlib import Path
import re
import sys

version = sys.argv[1]
path = Path("backend/app/main.py")
content = path.read_text()
updated, count = re.subn(
    r'("version": ")[0-9]{4}-[0-9]{2}-[0-9]{2}("\s*,\s*"api_version")',
    rf'\g<1>{version}\g<2>',
    content,
)
if count != 1:
    raise SystemExit(f"Expected one API version field in {path}, found {count}")
path.write_text(updated)
PY

echo "Updated frontend package metadata to $SEMVER_VERSION"
echo "Updated API version to $DATE_VERSION"

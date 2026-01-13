# GitHub CLI Integration Guide

This project leverages the GitHub CLI (`gh`) to streamline development workflows, including pushing code, managing releases, and resolving issues.

## Prerequisites

- GitHub CLI installed (`gh --version`)
- Authenticated with GitHub (`gh auth status`)

## Common Workflows

### 1. Pushing Code and Creating Pull Requests

Instead of just pushing, you can create a PR in one command:

```bash
# Push current branch and create a PR
gh pr create --fill
```

### 2. Managing Releases

To create a new release for the project:

```bash
# Create a new release with automatically generated release notes
gh release create v1.0.2 --generate-notes
```

### 3. Issue Resolution

List open issues:

```bash
gh issue list
```

Create a new issue:

```bash
gh issue create --title "Bug: RSS parser failing" --body "The parser is not handling certain feeds correctly."
```

View and checkout an issue:

```bash
gh issue view 123
gh issue checkout 123
```

## Project Integration

We have integrated common commands into the `package.json` for easy access.

- `npm run gh:pr`: Create a PR for the current branch.
- `npm run gh:release`: Create a new release (requires version argument).
- `npm run gh:issues`: List open issues.

## Automatic Versioning

The project includes a script to automatically update the version in `package.json` based on the current git branch name.

- **Supported Branch Formats**: `v1.0.0`, `v1.01`, `v.1.1.1`
- **Usage**:
  ```bash
  ./scripts/update_version.sh
  ```
  This script is intended to be run before creating a release to ensure the project version matches the release tag.

## Automatic Tagging

A git `post-commit` hook has been installed to automatically tag every commit with the version extracted from the branch name.

- **How it works**: After every commit, the hook checks the branch name. If it matches a version format (e.g., `v1.0.0`), it automatically creates a local tag (e.g., `v1.0.0`) for that commit if it doesn't already exist.
- **Pushing Tags**: When you push your changes, remember to push the tags as well:
  ```bash
  git push origin --tags
  ```
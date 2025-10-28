#!/bin/bash

# Script to help with publishing the CortexDB TypeScript SDK to npm
# Usage: ./scripts/publish.sh [version]
# Example: ./scripts/publish.sh 0.1.0

set -e  # Exit on error

VERSION=$1

if [ -z "$VERSION" ]; then
  echo "❌ Error: Version number required"
  echo "Usage: ./scripts/publish.sh [version]"
  echo "Example: ./scripts/publish.sh 0.1.0"
  exit 1
fi

echo "📦 Publishing CortexDB TypeScript SDK v$VERSION"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
  echo "❌ Error: package.json not found. Run this script from clients/typescript/"
  exit 1
fi

# Check if we're logged in to npm
echo "1️⃣  Checking npm login..."
if ! npm whoami > /dev/null 2>&1; then
  echo "❌ Not logged in to npm. Please run: npm login"
  exit 1
fi
echo "   ✅ Logged in as: $(npm whoami)"
echo ""

# Clean and build
echo "2️⃣  Cleaning and building..."
npm run clean
npm run build
echo "   ✅ Build complete"
echo ""

# Update version
echo "3️⃣  Updating version to $VERSION..."
npm version $VERSION --no-git-tag-version
echo "   ✅ Version updated"
echo ""

# Show what will be published
echo "4️⃣  Preview of package contents:"
npm pack --dry-run
echo ""

# Ask for confirmation
read -p "🤔 Ready to publish? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Publish cancelled"
  git checkout package.json  # Revert version change
  exit 1
fi

# Publish
echo "5️⃣  Publishing to npm..."
npm publish --access public
echo "   ✅ Published successfully!"
echo ""

# Create git tag
echo "6️⃣  Creating git tag..."
git add package.json
git commit -m "chore(typescript): release v$VERSION"
git tag "typescript-v$VERSION"
echo "   ✅ Git tag created"
echo ""

echo "🎉 Success! Package published to npm"
echo ""
echo "Next steps:"
echo "  - Push changes: git push && git push --tags"
echo "  - Update CHANGELOG.md"
echo "  - Test installation: npm install @cortexdb/sdk@$VERSION"


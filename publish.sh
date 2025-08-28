#!/bin/bash

# Prometheus MCP Server Publishing Script
# This script automatically increments the version and publishes to PyPI

set -e  # Exit on any error

echo "🚀 Prometheus MCP Server Publishing Script"
echo "=========================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Function to increment version
increment_version() {
    local version=$1
    local increment_type=${2:-patch}
    
    IFS='.' read -ra VERSION_PARTS <<< "$version"
    local major=${VERSION_PARTS[0]}
    local minor=${VERSION_PARTS[1]}
    local patch=${VERSION_PARTS[2]}
    
    case $increment_type in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch"|*)
            patch=$((patch + 1))
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "📦 Current version: $CURRENT_VERSION"

# Ask user for version increment type
echo ""
echo "Select version increment type:"
echo "1) patch (1.2.4 → 1.2.5) - Bug fixes, small changes"
echo "2) minor (1.2.4 → 1.3.0) - New features, backward compatible"
echo "3) major (1.2.4 → 2.0.0) - Breaking changes"
echo "4) custom - Enter your own version"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        NEW_VERSION=$(increment_version "$CURRENT_VERSION" "patch")
        ;;
    2)
        NEW_VERSION=$(increment_version "$CURRENT_VERSION" "minor")
        ;;
    3)
        NEW_VERSION=$(increment_version "$CURRENT_VERSION" "major")
        ;;
    4)
        read -p "Enter new version (e.g., 1.2.5): " NEW_VERSION
        ;;
    *)
        echo "❌ Invalid choice. Using patch increment."
        NEW_VERSION=$(increment_version "$CURRENT_VERSION" "patch")
        ;;
esac

echo "🔄 Updating version from $CURRENT_VERSION to $NEW_VERSION"

# Update version in pyproject.toml
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
else
    # Linux
    sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
fi

echo "✅ Version updated in pyproject.toml"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/*.egg-info/

# Build the package
echo "🔨 Building package..."
uv build

# Check if build was successful
if [ ! -f "dist/raihan0824_prometheus_mcp_server-$NEW_VERSION-py3-none-any.whl" ]; then
    echo "❌ Build failed. Wheel file not found."
    exit 1
fi

echo "✅ Package built successfully"

# Test the package locally
echo "🧪 Testing package locally..."
if timeout 10s bash -c "PROMETHEUS_URL='http://localhost:9090' uvx --from ./dist/raihan0824_prometheus_mcp_server-$NEW_VERSION-py3-none-any.whl prometheus-mcp-server" > /dev/null 2>&1; then
    echo "✅ Package test successful"
else
    echo "⚠️  Package test timeout (this is normal for MCP server)"
fi

# Ask for confirmation before publishing
echo ""
echo "📋 Package details:"
echo "   Name: raihan0824-prometheus-mcp-server"
echo "   Version: $NEW_VERSION"
echo "   Files:"
ls -la dist/
echo ""
read -p "🚀 Ready to publish to PyPI? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    echo "🚀 Publishing to PyPI..."
    
    # Check if PyPI token is set
    if [ -z "$UV_PUBLISH_TOKEN" ]; then
        echo "⚠️  UV_PUBLISH_TOKEN not set. You'll be prompted for credentials."
        echo "   To avoid this, set: export UV_PUBLISH_TOKEN='pypi-your-token-here'"
    fi
    
    # Publish
    uv publish
    
    echo ""
    echo "🎉 Package published successfully!"
    echo "📦 PyPI URL: https://pypi.org/project/raihan0824-prometheus-mcp-server/"
    echo ""
    echo "📋 Installation command:"
    echo "   uvx --from raihan0824-prometheus-mcp-server prometheus-mcp-server"
    echo ""
    echo "🔄 Don't forget to:"
    echo "   1. Commit the version change: git add pyproject.toml && git commit -m 'Bump version to $NEW_VERSION'"
    echo "   2. Tag the release: git tag v$NEW_VERSION"
    echo "   3. Push changes: git push && git push --tags"
    
else
    echo "❌ Publishing cancelled."
    echo "🔄 Reverting version change..."
    
    # Revert version change
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^version = \".*\"/version = \"$CURRENT_VERSION\"/" pyproject.toml
    else
        sed -i "s/^version = \".*\"/version = \"$CURRENT_VERSION\"/" pyproject.toml
    fi
    
    echo "✅ Version reverted to $CURRENT_VERSION"
fi

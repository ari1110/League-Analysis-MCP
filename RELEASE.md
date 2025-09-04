# Release Guide

## Current Release: v0.2.1 ✅

**Status**: Published to PyPI  
**Install**: `uvx league-analysis-mcp-server` or `pip install league-analysis-mcp-server`  
**Repository**: https://github.com/ari1110/League-Analysis-MCP

## 🚀 Automated Release Process

### Option 1: Tag-Based Release (Recommended)
```bash
# Create and push a version tag
git tag v0.1.2
git push origin v0.1.2
```

**What happens automatically:**
1. ✅ **Tests** - Run on Python 3.10, 3.11, 3.12
2. ✅ **Build** - Create wheel and source distributions
3. ✅ **TestPyPI** - Publish to test environment first
4. ✅ **PyPI** - Publish to production after TestPyPI success
5. ✅ **GitHub Release** - Create release page with install instructions

### Option 2: Manual Workflow Trigger
```bash
# Trigger workflow manually
gh workflow run publish.yml

# Or via GitHub UI:
# Go to Actions → Build and Publish to PyPI → Run workflow
```

## 📋 Pre-Release Checklist

### 1. Version Management
- [ ] Update version in `pyproject.toml`
- [ ] Update version in `src/league_analysis_mcp_server/config/settings.json`
- [ ] Update `CHANGELOG.md` with new features/fixes
- [ ] Test locally: `uv build && python -m league_analysis_mcp_server`

### 2. Testing
- [ ] Run local tests: `uv run python test_server.py`
- [ ] Test PyPI installation: `uvx league-analysis-mcp-server`
- [ ] Verify MCP client integration

### 3. Documentation
- [ ] Update README.md with new features
- [ ] Update MCP_INTEGRATION_GUIDE.md if needed
- [ ] Check example configurations are current

### 4. Release
- [ ] Commit all changes
- [ ] Create version tag: `git tag vX.Y.Z`
- [ ] Push tag: `git push origin vX.Y.Z`
- [ ] Monitor GitHub Actions workflow
- [ ] Verify PyPI publication
- [ ] Test installation: `pip install league-analysis-mcp-server`

## 🔧 Manual Release (Backup)

If automated release fails:

```bash
# Build package
uv build

# Publish to TestPyPI
UV_PUBLISH_TOKEN=<test-token> uv publish --publish-url https://test.pypi.org/legacy/

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ league-analysis-mcp-server

# Publish to PyPI
UV_PUBLISH_TOKEN=<prod-token> uv publish

# Create GitHub release
gh release create vX.Y.Z --title "Release vX.Y.Z" --notes "See CHANGELOG.md for details"
```

## 📊 Release Verification

After each release, verify:

1. **PyPI Page**: https://pypi.org/project/league-analysis-mcp-server/
2. **Installation**: `uvx league-analysis-mcp-server` works
3. **GitHub Release**: https://github.com/ari1110/League-Analysis-MCP/releases
4. **MCP Functionality**: Server starts and initializes correctly

## 🔄 Version History

- **v0.1.6** - Enhanced test suite and code quality improvements
- **v0.1.5** - Automated OAuth flow with callback server
- **v0.1.4** - Critical OAuth redirect URI fix
- **v0.1.3** - Streamlined authentication setup tools
- **v0.1.2** - GitHub Actions and CI/CD improvements
- **v0.1.1** - Initial bug fixes and GitHub Actions
- **v0.1.0** - Initial PyPI release with full MCP functionality

## 🛠️ Troubleshooting Releases

### Common Issues:

**1. Version Already Exists on PyPI**
- Cannot overwrite existing versions
- Increment version number in `pyproject.toml`
- Create new tag with incremented version

**2. Token Permissions**
- Ensure tokens are project-scoped for `league-analysis-mcp-server`
- Check token expiration dates
- Update GitHub secrets if needed

**3. Workflow Failures**
- Check GitHub Actions logs: `gh run view --log-failed`
- Most common: test import issues (non-critical for release)
- Core functionality tests must pass for release

**4. Installation Issues**
- Wait 5-10 minutes after PyPI publication
- Clear pip cache: `pip cache purge`
- Use `--no-cache-dir` flag if needed

## 📞 Support

For release issues:
1. Check GitHub Actions logs
2. Verify PyPI package status
3. Test with fresh environment: `uvx league-analysis-mcp-server`

The automated release process is designed to be robust and handle most scenarios automatically.
# Deployment Guide

## Release Process

1. **Increment version** in `Cargo.toml`:
   ```toml
   [package]
   name = "sdl2_alpha"
   version = "0.2.0"  # Update this
   ```

2. **Commit the version bump**:
   ```bash
   git add Cargo.toml
   git commit -m "chore: bump version to 0.2.0"
   git push origin main
   ```

3. **Create a release from a passing commit**:
   - Go to GitHub → Releases → "Create a new release"
   - Tag: `v0.2.0` (must match Cargo.toml version)
   - Target: Select the commit with the version bump
   - Title: `v0.2.0`
   - Generate release notes or write changelog
   - Click "Publish release"

4. **Automated build & publish**:
   - GitHub Actions will automatically build optimized wheels for all platforms
   - Wheels will be published to PyPI via trusted publishing


## Pre-release Checklist

- [ ] All tests passing on main branch
- [ ] Version incremented in Cargo.toml
- [ ] CHANGELOG.md updated (if using)
- [ ] No "TODO" or debug code in release
- [ ] Performance benchmarks still meet targets
- [ ] Cross-platform builds tested

## Release Artifacts

Each release creates:
- **Linux**: x86_64, ARM64 wheels
- **Windows**: x86_64, i686 wheels  
- **macOS**: Intel, Apple Silicon wheels
- **Source distribution** (.tar.gz)

All wheels are fully optimized with `--release` builds.
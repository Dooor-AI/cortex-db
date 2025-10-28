# Publishing to NPM

This guide explains how to publish the CortexDB TypeScript SDK to npm.

## Prerequisites

1. **NPM Account**: You need an npm account with publish access
2. **NPM Token**: Generate an access token from [npmjs.com](https://www.npmjs.com/settings/~/tokens)
3. **Access Rights**: Must have publish rights to `@cortexdb` scope

## Pre-publish Checklist

Before publishing, ensure:

- [ ] All tests pass (when implemented)
- [ ] Code is properly formatted (`npm run format:check`)
- [ ] No linting errors (`npm run lint`)
- [ ] Build succeeds (`npm run build`)
- [ ] Version number is updated in `package.json`
- [ ] `CHANGELOG.md` is updated with changes
- [ ] README is up to date
- [ ] All examples work

## Manual Publish (Recommended for first release)

### Step 1: Login to NPM

```bash
npm login
```

### Step 2: Verify package contents

Check what will be published:

```bash
npm pack --dry-run
```

This shows all files that will be included. Verify:
- Only `dist/` is included (not `src/`)
- README, LICENSE, and package.json are included
- No sensitive files are included

### Step 3: Build

```bash
npm run clean
npm run build
```

### Step 4: Test locally

You can test the package locally before publishing:

```bash
npm pack
# This creates a .tgz file
# Install it in another project: npm install /path/to/cortexdb-sdk-0.1.0.tgz
```

### Step 5: Publish

For first-time publishing a scoped package:

```bash
npm publish --access public
```

For subsequent releases:

```bash
npm publish
```

### Step 6: Verify

After publishing, verify the package:

```bash
npm view @cortexdb/sdk

# Or install it in a test project
npm install @cortexdb/sdk
```

## Automated Publish via GitHub Actions

The repository includes a GitHub Actions workflow for automated publishing.

### Option 1: Publish on Release

1. Create a new release on GitHub
2. The workflow automatically publishes to npm

### Option 2: Manual Trigger

1. Go to Actions → "Publish to NPM"
2. Click "Run workflow"
3. Enter the version number
4. Workflow will:
   - Build the package
   - Update version in package.json
   - Publish to npm
   - Create a git tag

### Setup GitHub Actions

Add `NPM_TOKEN` to GitHub Secrets:

1. Go to repository Settings → Secrets → Actions
2. Add new secret: `NPM_TOKEN`
3. Value: Your npm automation token

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backward compatible
- **Patch** (0.0.1): Bug fixes, backward compatible

Update version:

```bash
# For patch (0.1.0 → 0.1.1)
npm version patch

# For minor (0.1.0 → 0.2.0)
npm version minor

# For major (0.1.0 → 1.0.0)
npm version major
```

## Post-publish

After publishing:

1. Test installation in a clean project
2. Update documentation with new version
3. Announce release (if significant)
4. Monitor npm downloads and issues

## Troubleshooting

### Error: 403 Forbidden

- Check if you're logged in: `npm whoami`
- Verify you have publish rights to `@cortexdb`
- Ensure the package name is available

### Error: Version already exists

- You cannot republish the same version
- Increment the version number and try again

### Error: Package not found after publish

- Wait a few minutes for npm CDN to sync
- Clear npm cache: `npm cache clean --force`

## Package Scope

The package is published as `@cortexdb/sdk` under the `@cortexdb` scope.

If this is the first package in the scope, you may need to:
1. Create the organization on npmjs.com
2. Add team members with publish rights


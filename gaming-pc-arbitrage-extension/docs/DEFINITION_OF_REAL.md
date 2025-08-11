# Definition of Real Contract

## For any feature Y to be considered "REAL" and "IMPLEMENTED", I must provide:

### 1. Code Files
- [ ] Complete implementation in TypeScript/React
- [ ] No placeholders, mocks, or static data in production code
- [ ] All imports resolve and types check
- [ ] Follows project architecture patterns

### 2. Tests
- [ ] Unit tests with >80% coverage
- [ ] Integration tests for user flows
- [ ] E2E tests for critical paths
- [ ] All tests passing in CI

### 3. Evidence
- [ ] Screenshots or DOM snapshots of working UI
- [ ] Console logs with timestamps showing data flow
- [ ] Network traces for API calls (if applicable)
- [ ] Chrome DevTools performance profile

### 4. Artifacts
- [ ] Built extension ZIP with checksum
- [ ] Manifest version matches claimed version
- [ ] No build warnings or errors
- [ ] Clean npm audit

### 5. Documentation
- [ ] API documentation for new modules
- [ ] User-facing help text
- [ ] Architecture decision records (ADRs) for significant choices

## Verification Protocol

```bash
# For each feature:
npm run test -- --coverage path/to/feature
npm run e2e -- --headed path/to/feature.e2e.ts
npm run build
sha256sum dist/extension.zip

# Must provide output of:
- Test results with coverage
- E2E video/screenshots
- Build log (no errors)
- ZIP checksum
```

## Example Evidence Package

For "Max Auto Engine" to be considered REAL:

1. **Code Files**:
   - `/extension/src/background/automation.ts` (engine)
   - `/extension/src/content/*/scanner.ts` (marketplace scanners)
   - `/extension/src/ui/pages/AutomationCenter.tsx` (UI)
   - `/extension/src/lib/automation/savedSearches.ts` (data layer)

2. **Tests**:
   - `automation.test.ts` - Unit tests for engine logic
   - `scanner.test.ts` - Parser tests with fixtures
   - `automation.e2e.ts` - Full flow test
   - Coverage report showing >80%

3. **Evidence**:
   - Screenshot of Automation Center with saved searches
   - Log excerpt: `[2024-01-10 14:23:45] Alarm fired: auto-scan`
   - Log excerpt: `[2024-01-10 14:23:47] Tab opened: https://facebook.com/marketplace/search?q=gaming+pc`
   - Log excerpt: `[2024-01-10 14:23:52] Scan complete: 12 candidates found`
   - Log excerpt: `[2024-01-10 14:23:53] Persisted to storage: 8 new, 4 duplicates`

4. **Artifacts**:
   - `extension-v3.1.0.zip` - SHA256: `a7b3c9d5e2f4...`
   - Version HUD showing "v3.1.0"

## Enforcement

Any claim of "implemented" or "done" without this evidence package = IMMEDIATE FAILURE

Signed: Claude (AI Assistant)
Date: Now
Status: BINDING CONTRACT
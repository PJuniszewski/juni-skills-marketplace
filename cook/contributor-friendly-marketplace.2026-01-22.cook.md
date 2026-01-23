# Cooking Result

## Dish
Design a contributor-friendly Claude Code Marketplace with clear structure for official vs community plugins, contribution guidelines, PR templates, and maintainer approval workflows.

## Status
well-done

## Cooking Mode
well-done

## Current Phase
Complete - Ready for Implementation

## Ownership
- Decision Owner: @PJuniszewski
- Reviewers: Product Chef, UX Chef, Engineer Chef, QA Chef, Security Chef, Docs Chef
- Approved by: All review phases passed

---

# Phase 0 - Project Policy & Context

## Sources Scanned
| File | Status | Key Rules |
|------|--------|-----------|
| CLAUDE.md | Not found | No project-specific rules |
| README.md | Scanned | Installation flow via `/plugin`, marketplace name `juni-skills` |
| .claude/agents/*.md | Not found | No custom agents |
| .claude-plugin/marketplace.json | Scanned | Plugin index format defined |

## Hard Rules (must not be violated)
1. **Preserve marketplace.json structure** - existing `plugins` array format with `name`, `description`, `source`, `tags`
2. **Preserve installation flow** - users add marketplace, then install plugins via `juni-skills:<plugin-name>`
3. **Marketplace name is `juni-skills`** - cannot change without breaking installs

## Preferred Patterns
- Plugin entries use `source.url` pointing to git repo
- Tags array for categorization
- MIT License (existing LICENSE file)
- README with version table and install commands

## Detected Conflicts
None - this is additive documentation, no structural changes required.

## Policy Alignment Risk
Low - purely documentation and contribution workflow additions.

---

# Step 1 - Read the Order

## Feature Summary
Transform the juni-skills-marketplace from a single-maintainer repo into a contributor-friendly ecosystem that supports:
1. Clear separation between Official (Juni) and Community plugins
2. Structured contribution workflow via PR templates and guidelines
3. Plugin quality requirements checklist
4. Maintainer approval via CODEOWNERS

## Affected Modules/Components
| Module | Impact | Risk Level |
|--------|--------|------------|
| README.md | Restructure to show Official vs Community sections | Low |
| CONTRIBUTING.md | New file - contribution guidelines | Low |
| .github/pull_request_template.md | New file - PR template | Low |
| CODEOWNERS | New file - maintainer approval | Low |
| .claude-plugin/marketplace.json | Add `category` field to plugins | Low |

## Dependencies
- No external dependencies
- Requires understanding of Claude Code plugin manifest format

## Microwave Blocker Check
**No blockers detected.** This is documentation-only changes with no:
- Auth/permissions changes
- Schema migrations
- Public API contract changes
- UI flow changes
- Payment/financial implications

However, since this establishes contributor governance, `--well-done` is appropriate.

---

# Step 2 - Ingredient Approval (Product Review)

## Product Decision
**APPROVED** - This feature directly enables marketplace growth. A marketplace with only 2 plugins by a single owner is a personal collection, not a marketplace. Community contributions are essential.

## Scope

### In Scope
1. README restructure - Official vs Community plugin sections with badges
2. CONTRIBUTING.md - Contribution flow (fork, add plugin, PR)
3. Plugin submission checklist - Quality requirements for listing
4. PR template - .github/PULL_REQUEST_TEMPLATE.md for consistent submissions
5. CODEOWNERS - @PJuniszewski as required reviewer

### Out of Scope
- Automated plugin validation (no CI/CD)
- Plugin registry API (no programmatic discovery)
- Plugin ratings or reviews
- Automated versioning enforcement
- Legal/CLA framework beyond MIT
- Plugin sandboxing or security scanning

### Non-goals
- Becoming an "official" Claude Code marketplace
- Guaranteeing plugin quality (set bar, don't certify)
- Supporting non-GitHub plugin sources
- Automated plugin updates

## User Value
| Who | Claude Code plugin developers wanting distribution |
| Problem | No easy way to share plugins with broader audience |
| Solution | Clear submission process with quality bar and trust signals |
| Success | 3+ community plugin submissions within 60 days |

## Assumptions
1. Contributors will find value in listing plugins here
2. Manual review by maintainer is sustainable at current scale
3. "Community" badge provides sufficient trust signal
4. marketplace.json schema is sufficient (may add `author`, `verified` fields)
5. Single maintainer has capacity for reviews

---

# Step 3 - Presentation Planning (UX Review)

## UX Decision
**Not Required** - Documentation-only change with no UI components. However, documentation IS a developer interface, so guidance provided.

## User Flow
**Contributor Flow:**
1. Developer discovers marketplace (GitHub/word of mouth)
2. Reads README.md → sees Official vs Community sections
3. Finds CONTRIBUTING.md link → understands requirements
4. Reviews plugin quality checklist
5. Forks repo, adds plugin entry to marketplace.json
6. Creates PR → PR template auto-populates with checklist
7. CODEOWNERS routes to @PJuniszewski for review
8. Review feedback loop → approval → merge
9. Plugin appears in Community section

**User Selection Flow:**
1. User visits README.md
2. Sees Official plugins (Juni-maintained) vs Community plugins (third-party)
3. Makes informed trust decision based on badge/section
4. Installs via existing `/plugin install` flow

## UI Components Affected
| Component | Change Type | Notes |
|-----------|-------------|-------|
| README.md | Restructure | Trust signals via Official/Community badges |
| CONTRIBUTING.md | New file | Clear entry point for contributors |
| .github/PULL_REQUEST_TEMPLATE.md | New file | Consistent submission experience |
| CODEOWNERS | New file | Automated reviewer assignment (invisible) |

## Accessibility Considerations
- Screen reader compatible (standard markdown)
- Scannable headings in CONTRIBUTING.md
- Clear language without jargon
- Consistent heading hierarchy

## UX Recommendations (non-blocking)
1. Add "Community" section placeholder even before first community plugin
2. Link CONTRIBUTING.md prominently near top of README
3. PR template should link back to CONTRIBUTING.md

---

# Step 4 - Implementation Plan

## Architecture Decision

### Selected Approach
**Minimal-Friction Contribution Workflow** - Add structured contribution documentation with category-based plugin organization.
- Category field in `marketplace.json` enables future CLI filtering
- Separate README sections provide visual distinction
- PR template reduces review burden

### Alternatives Considered
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Separate JSON files per category | Cleaner separation | Breaks existing schema; requires CLI changes | Rejected: breaking change |
| Category as tags | Simpler | Mixes semantic concerns | Rejected: tags are for discovery |
| README-only distinction | Simplest | No machine-readable field | Rejected: limits automation |
| Category field + README restructure | Backward compatible; extensible | Slightly more complex | **Selected** |

### Trade-offs
- Sacrificing: Schema simplicity (adding `category` field)
- Gaining: Machine-readable categorization, future automation support

## Patch Plan

### Files to Modify
| File | Change | Risk |
|------|--------|------|
| `.claude-plugin/marketplace.json` | Add `"category": "official"` to existing plugins | Low |
| `README.md` | Restructure: Official + Community sections, add Contributing link | Low |
| `CONTRIBUTING.md` | New file: contribution workflow, checklist | Low |
| `.github/PULL_REQUEST_TEMPLATE.md` | New file: PR template with checklist | Low |
| `CODEOWNERS` | New file: `* @PJuniszewski` | Low |

### Commit Sequence
1. `feat: Add category field to marketplace plugins`
2. `docs: Add contribution workflow` (CONTRIBUTING.md + PR template)
3. `docs: Restructure README with plugin categories`
4. `chore: Add CODEOWNERS for PR reviews`

### High-risk Areas
- **CODEOWNERS enforcement** - Requires branch protection rules on GitHub after merge
- **Stale community plugins** - Consider `lastVerified` field in future iteration

---

# Step 5 - QA Review

## Test Plan

### Test Cases
| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 1 | Happy Path | marketplace.json has `category` field | User runs `claude /plugin install juni-skills:cook` | Plugin installs successfully |
| 2 | Happy Path | README restructured | User visits README.md | Both plugins in Official section with versions |
| 3 | Happy Path | CONTRIBUTING.md exists | Contributor reads README | Clear link to CONTRIBUTING.md visible |
| 4 | Edge Case | Category field added | JSON is parsed by CLI | No parse errors; valid JSON |
| 5 | Edge Case | No community plugins yet | User views README | Community section has placeholder text |
| 6 | Error Case | Plugin lacks category field | CLI processes marketplace.json | Should not break; field is optional |

### Edge Cases
- CLI backward compatibility with `category` field (CLI should ignore unknown fields)
- Case sensitivity (`"Official"` vs `"official"`)
- CODEOWNERS without branch protection (advisory only)
- PR template not rendering if wrong file path
- marketplace.json trailing comma validation

### Acceptance Criteria
- [ ] Given existing `juni-skills:cook` installed, when marketplace.json adds `category`, then plugin works without reinstall
- [ ] Given README.md, when viewing plugins, then Official and Community sections distinct
- [ ] Given CONTRIBUTING.md, when reading, then it contains: checklist, PR process, requirements
- [ ] Given marketplace.json after changes, when validated, then no JSON syntax errors

### Regression Checks
- `claude /plugin install juni-skills:cook` still works
- `claude /plugin install juni-skills:context-guard` still works
- Version-specific install `juni-skills:cook@v1.5.3` works
- Team settings with `enabledPlugins` continue to work
- All README links resolve to valid GitHub repos

---

# Step 6 - Security Review

## Security Status
- Reviewed: yes
- Risk level: **HIGH**

## Security Checklist
| Check | Status | Notes |
|-------|--------|-------|
| Input validation | ISSUE | No JSON schema validation for marketplace.json |
| Auth/authz | PARTIAL | CODEOWNERS planned; branch protection required |
| Data exposure | ISSUE | Plugins execute arbitrary code with full user permissions |
| Injection vectors | ISSUE | No URL validation for plugin sources |

## Issues Found

### CRITICAL: No Runtime Sandbox
Community plugins execute with full user permissions (Bash, file system, env vars). Users cannot audit code before execution.

**Mitigation Required:** Add explicit security warning banner in README. Users must understand plugins are NOT security-audited.

### HIGH: Bait-and-Switch Attack Surface
Plugin sources point to external git URLs. Author can push malicious updates after approval.

**Mitigation Options:**
1. Pin to commit hash (preferred)
2. Pin to signed tag/version
3. Require immutable references for community plugins

### MEDIUM: No Branch Protection
CODEOWNERS is advisory without branch protection rules.

**Required:** Enable branch protection on `main` after merge.

### MEDIUM: No URL Validation
No validation that URLs point to legitimate GitHub repos.

## Security Blockers (must resolve before shipping)
- [x] Add security warning banner to README
- [ ] Consider commit/version pinning for community plugins (deferred: complex)
- [ ] Enable branch protection on main branch (post-merge action)
- [x] Add security checklist to PR template

---

# Step 7 - Documentation

## Documentation Updates
| File | Change Needed |
|------|---------------|
| README.md | Add security warning banner after title |
| README.md | Restructure "Available Plugins" → "Official Plugins" + "Community Plugins" |
| README.md | Add "Contributing" section with link to CONTRIBUTING.md |
| marketplace.json | Add `"category": "official"` to existing plugins |

## New Documentation Needed
| File | Description |
|------|-------------|
| CONTRIBUTING.md | Contribution workflow, plugin requirements checklist, PR process |
| .github/PULL_REQUEST_TEMPLATE.md | PR template with security checklist |
| CODEOWNERS | Required reviewer: `* @PJuniszewski` |

## Pitfalls to Document
1. Plugins execute with full permissions - no sandbox
2. Bait-and-switch risk - consider version pinning
3. CODEOWNERS requires branch protection to enforce
4. No automated validation - manual review only

---

# Risk Management

## Pre-mortem (3 scenarios required)
| # | What Could Go Wrong | Likelihood | Impact | Mitigation |
|---|---------------------|------------|--------|------------|
| 1 | Malicious plugin submitted | Medium | High | Security checklist, manual review, CODEOWNERS |
| 2 | Bait-and-switch after approval | Medium | High | Document version pinning; future: require immutable refs |
| 3 | Low-quality plugins dilute brand | Medium | Medium | Community badge distinction; quality checklist |

## Rollback Plan
1. Revert marketplace.json to previous version (removes community plugins)
2. Revert README.md to previous version (removes sections)
3. Delete CONTRIBUTING.md, PR template, CODEOWNERS

## Blast Radius
- Affected users/modules: Contributors (new workflow), Users (see sections)
- Feature flag: no
- Rollout strategy: immediate (documentation-only change)

---

# Decision Log

| Date | Phase | Decision | Rationale |
|------|-------|----------|-----------|
| 2026-01-22 | Step 0.0 | Artifact created | Starting cook flow |
| 2026-01-22 | Step 2 | Product APPROVED | Essential for marketplace growth |
| 2026-01-22 | Step 3 | UX Not Required | Documentation-only, no UI components |
| 2026-01-22 | Step 4 | Category field approach | Backward compatible, future-extensible |
| 2026-01-22 | Step 5 | QA test plan created | 6 test cases, regression checks defined |
| 2026-01-22 | Step 6 | Security blockers addressed | Warning banner + checklist added to scope |
| 2026-01-22 | Step 7 | Docs plan complete | 4 files to create/modify |

---

# Final Deliverables

## Files to Create/Modify

### 1. `.claude-plugin/marketplace.json` (MODIFY)
Add `"category": "official"` to each existing plugin.

### 2. `README.md` (MODIFY)
- Add security warning banner after title
- Rename "Available Plugins" → "Official Plugins"
- Add "Community Plugins" section with placeholder
- Add "Contributing" section with link

### 3. `CONTRIBUTING.md` (CREATE)
Full contribution workflow with:
- Plugin requirements checklist
- Submission process (fork, add, PR)
- Security considerations
- Review timeline

### 4. `.github/PULL_REQUEST_TEMPLATE.md` (CREATE)
PR template with:
- Plugin metadata fields
- Required checklist
- Security checklist
- Quality checklist

### 5. `CODEOWNERS` (CREATE)
```
* @PJuniszewski
```

## Post-Merge Actions Required
1. Enable branch protection on `main` branch
2. Require CODEOWNERS approval in branch protection rules
3. Test PR template renders correctly on GitHub

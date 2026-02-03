# AgentMesh Project Governance

This document describes the governance structure for the AgentMesh project.

## Overview

AgentMesh is an open governance project that aims to become the industry standard for AI agent security and compliance. We are committed to building a diverse, inclusive community of contributors and adopters.

## Project Roles

### Users
Anyone who uses AgentMesh. Users are encouraged to:
- Report bugs and request features via GitHub Issues
- Participate in discussions
- Help other users in community channels

### Contributors
Anyone who contributes code, documentation, or other artifacts. Contributors:
- Submit pull requests
- Review code from other contributors
- Participate in design discussions
- Help triage issues

### Maintainers
Contributors who have demonstrated sustained commitment to the project. Maintainers:
- Have write access to the repository
- Review and merge pull requests
- Participate in release planning
- Mentor new contributors

**Current Maintainers:**
| Name | GitHub | Organization | Focus Area |
|------|--------|--------------|------------|
| Imran Siddique | @imran-siddique | Microsoft | Project Lead, Architecture |

### Technical Steering Committee (TSC)

The TSC is responsible for:
- Setting technical direction and roadmap
- Resolving technical disputes
- Approving major architectural changes
- Managing releases and versioning
- Representing the project to external organizations

**Current TSC Members:**
| Name | GitHub | Organization | Term |
|------|--------|--------------|------|
| Imran Siddique | @imran-siddique | Microsoft | Founding Member |

*Seats open for additional TSC members from adopting organizations.*

## Decision Making

### Consensus-Based Decisions
Most decisions are made through lazy consensus:
1. A proposal is made via GitHub Issue or Discussion
2. If no objections within 72 hours, the proposal is accepted
3. Objections must include reasoning and alternative proposals

### Voting
For contentious issues, the TSC may call a vote:
- Each TSC member has one vote
- Decisions require simple majority (>50%)
- Quorum requires 2/3 of TSC members participating

### Appeals
Any community member may appeal a decision to the TSC by opening an issue with the `appeal` label.

## Becoming a Maintainer

Contributors may be nominated for maintainer status by existing maintainers. Criteria include:

1. **Sustained Contributions:** At least 3 months of active contribution
2. **Quality:** Demonstrated high-quality code and reviews
3. **Community:** Positive interactions with other contributors
4. **Understanding:** Deep knowledge of project architecture and goals

### Nomination Process
1. Existing maintainer opens a private discussion with other maintainers
2. If consensus, nominee is contacted to confirm interest
3. Announcement made via GitHub Discussion
4. 1-week comment period for community feedback
5. Final decision by TSC

### Emeritus Status
Maintainers who are no longer active may request or be moved to emeritus status. Emeritus maintainers:
- Are recognized for their past contributions
- May return to active status by demonstrating renewed activity
- Do not have merge privileges

## Becoming a TSC Member

TSC membership is typically granted to:
- Maintainers with 6+ months of active involvement
- Representatives of organizations with significant adoption
- Recognized experts in AI security/governance

### Process
1. Nomination by existing TSC member
2. Discussion among current TSC
3. Unanimous approval required for new members
4. Public announcement

## Code of Conduct

All participants are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

Violations should be reported to: governance@agentmesh.dev

## Meetings

### TSC Meetings
- Frequency: Monthly (or as needed)
- Format: Video call, open to observers
- Notes: Published to GitHub Discussions within 48 hours

### Community Meetings
- Frequency: Bi-weekly
- Format: Open video call
- Purpose: Demos, Q&A, roadmap discussion

## Releases

### Versioning
AgentMesh follows [Semantic Versioning](https://semver.org/):
- **MAJOR:** Breaking changes to public APIs
- **MINOR:** New features, backwards compatible
- **PATCH:** Bug fixes, backwards compatible

### Release Process
1. Maintainer proposes release (version, changelog)
2. 48-hour review period
3. At least one TSC member approves
4. Release is published to npm/PyPI

### LTS (Long-Term Support)
- Major versions receive security updates for 18 months
- LTS versions announced at release time

## Intellectual Property

### Licensing
AgentMesh is licensed under Apache 2.0.

### Contributor License Agreement
Contributors must sign the [CLA](CLA.md) before their first PR is merged. The CLA ensures:
- You have the right to contribute the code
- You grant the project perpetual license to use your contributions

### Trademark
"AgentMesh" and the AgentMesh logo are trademarks. Usage guidelines:
- ✅ "Built with AgentMesh"
- ✅ "AgentMesh compatible"
- ❌ "AgentMesh [Your Product]" (implies endorsement)

## Foundation Alignment

AgentMesh is working toward incubation with the **Linux Foundation AI & Data** (LF AI & Data). This governance document is designed to meet LF AI & Data incubation requirements.

### OpenSSF Compliance
We maintain an [OpenSSF Best Practices Badge](https://bestpractices.coreinfrastructure.org/) and comply with:
- Secure development practices
- Vulnerability disclosure policy
- Dependency security scanning

## Changes to Governance

This document may be amended by:
1. TSC member proposes change via PR
2. 1-week public comment period
3. TSC vote (simple majority)
4. Announcement to community

---

*Last updated: February 2026*
*Version: 1.0*

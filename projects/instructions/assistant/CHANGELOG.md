# Assistant Agent Changelog

## v2 - 2025-01-12
- Migrated to version-only architecture (highest version IS the instruction)
- Removed dual file structure, current instruction now in v2/ directory
- Registry updated to point to v2 as latest version

## v1 - 2025-01-11
- Initial migration to Option B package architecture
- Extracted variables from legacy composables structure
- Added support for optional instruction components (system_blocks, agent_skills, etc.)
- Registry-based resolution support
- Version snapshot created
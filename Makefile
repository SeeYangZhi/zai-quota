.PHONY: sync verify-sync build publish help

SKILL_SCRIPT = skills/zai-quota/scripts/check_quota.py
ROOT_SCRIPT = zai_quota.py

help:
	@echo "Available targets:"
	@echo "  sync         - Copy zai_quota.py to the skill entrypoint"
	@echo "  verify-sync  - Fail if root script and skill copy differ"
	@echo "  build        - Build wheel and sdist with uv"
	@echo "  publish      - Build and publish to PyPI with uv"

sync:
	cp $(ROOT_SCRIPT) $(SKILL_SCRIPT)
	chmod +x $(SKILL_SCRIPT)
	@echo "Synced $(ROOT_SCRIPT) -> $(SKILL_SCRIPT)"

verify-sync:
	@diff -q $(ROOT_SCRIPT) $(SKILL_SCRIPT) > /dev/null 2>&1 || (echo "Error: $(ROOT_SCRIPT) and $(SKILL_SCRIPT) are out of sync. Run 'make sync'." && exit 1)
	@echo "Scripts are in sync."

build:
	uv build

publish:
	uv build
	uv publish

PYTHON ?= python
ASSET_OUT := frontend/public
ASSET_AUDIT := data/processed/resolution_audit.csv

.PHONY: assets assets-check

assets:
	$(PYTHON) -m scripts.assets --out $(ASSET_OUT) --audit $(ASSET_AUDIT)

assets-check:
	$(PYTHON) -m scripts.check_assets --out $(ASSET_OUT) --audit $(ASSET_AUDIT)

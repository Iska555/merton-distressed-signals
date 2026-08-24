PYTHON ?= python
ASSET_OUT := frontend/public
.PHONY: assets assets-check verify

assets:
	$(PYTHON) -m scripts.assets --out $(ASSET_OUT)

assets-check:
	$(PYTHON) -m scripts.check_assets --out $(ASSET_OUT)

verify:
	$(PYTHON) -m scripts.verify

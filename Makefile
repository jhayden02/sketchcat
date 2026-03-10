KITTY_CONFIG_DIR := $(HOME)/.config/kitty
KITTEN_LINK := $(KITTY_CONFIG_DIR)/sketchcat.py

.PHONY: install uninstall

install:
	uv sync
	mkdir -p $(KITTY_CONFIG_DIR)
	ln -sf $(CURDIR)/sketchcat.py $(KITTEN_LINK)
	@echo "Installed sketchcat kitten to $(KITTEN_LINK)"

uninstall:
	rm -f $(KITTEN_LINK)
	@echo "Removed sketchcat kitten from $(KITTEN_LINK)"

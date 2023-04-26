BASE_THEME	= yeti
THEMES_DIR	= themes
OUTPUT_DIR	= ../inginious/frontend/static/css/themes

compile:
	if [ ! -d "node_modules" ]; then make install; fi
	if [ ! -d "$(OUTPUT_DIR)/$(theme)" ]; then cp -r $(OUTPUT_DIR)/default $(OUTPUT_DIR)/$(theme); fi
	./node_modules/grunt/bin/grunt swatch:$(theme)
	mv $(THEMES_DIR)/$(theme)/bootstrap.min.css $(OUTPUT_DIR)/$(theme)/.

install:
	npm install
	npm install grunt-cli

help:
	echo "Usage : make theme={your_theme_name}"

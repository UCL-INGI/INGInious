BOOTSWATCH_URL	= https://github.com/thomaspark/bootswatch.git
BASE_THEME	= yeti

compile:
	if [ ! -d "bootswatch" ]; then make install; fi
	cd bootswatch; ./node_modules/grunt/bin/grunt swatch:$(theme)
	mv bootswatch/dist/$(theme)/bootstrap.css $(theme).css

install:
	git clone $BOOTSWATCH_URL
	cd bootswatch
	npm install
	npm install grunt-cli

help:
	echo "Usage : make theme={your_theme_name}"

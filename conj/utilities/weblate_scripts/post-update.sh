#! /bin/bash
# -*- coding: utf-8 -*-

#   Copyright (c) 2017 Olivier Martin
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This script generates an unique .pot file from all .java files founded from the root of the git.
# This script updates all .po file with the new .pot.
# This script auto update the git
# This script is used by weblate. DO NOT USE IT MANUALLY !

MAIN_POT="utilities/Translations/main.pot";
MAIN_RUN="utilities/run.py";

echo '[1] Generating .pot file from JAVA sources and run script';

# We list all .java files
JAVA_LIST=$(find . -name "*.java" -exec echo -n '{} ' \; | tr '\n' ' ');
# We list the custom scripts compatible with translations
CUSTOM_TRANSLATABLE=$(find . -name "custom_translatable.py" -exec echo -n '{} ' \; | tr '\n' ' ');

#Generate the .pot file
xgettext -k_ --from-code UTF-8 -o $MAIN_POT $MAIN_RUN $JAVA_LIST $CUSTOM_TRANSLATABLE;

git add $MAIN_POT;

# Update all .po file from .pot to stay consistent with the Strings present in .java sources.
echo '[2] Updating .po file from .pot';
shopt -s nullglob;
for i in utilities/Translations/*.po; do
    msgmerge -vU $i $MAIN_POT 2>/dev/null;
    git add $i;
done

git commit -m "Auto commit: updating .pot and .po files";
git push;

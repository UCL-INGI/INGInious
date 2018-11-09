#! /bin/bash

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

# This script place in all tasks defined in {arr} the translations(.properties for Java and .mo for python)

echo "[3] Generating .properties files"

arr=(

"m01Q2" "m01Q3" "m01Q4" "m01Q5" "m01Q6" "m01Q7" "m01Q8" "m01Q9" "m01Q10" "m01Q11" "m01Q12" "m01Q13" "m01Q14" "m01Q15" "m01Q16" "m01Q17" "m01Q18" "mX1Q19" "m01Q20" "m01_bf"

"m02dem2" "m02dem3" "m02dem4" "m02dem5" "m02Q1" "m02Q3" "m02Q4" "m02Q5" "m02Q6" "m02Q7" "m02Q8" "m02Q9" "m02Q10" "m02_bf"

"m03dem2" "m03dem3" "m03dem4" "m03dem5" "m03Q1" "m03Q2" "m03Q3" "m03Q4" "m03Q5" "m03Q6" "m03Q7" "m03_bf"

"m04dem1" "m04dem2" "m04dem3" "m04dem4" "m04dem5" "m04Q1" "m04Q2" "m04Q3" "m04Q4" "m04Q5" "m04Q6" "m04Q7" "m04Q8" "m04Q9" "m04Q10" "m04Q11" "m04_bf"

"m05dem1" "m05dem2" "m05dem3" "m05dem4" "m05dem5" "m05Q1" "m05Q2" "m05Q3" "m05Q4" "m05Q5" "m05Q6" "m05Q7" "m05Q8" "m05Q9" "m05Q10" "m05Q11" "m05Q12" "m05_bf"

"m06dem1" "m06dem2" "m06dem3" "m06dem4" "m06Q1" "m06Q2" "m06Q3" "m06Q4" "m06Q5" "m06Q6" "m06Q7" "m06Q8" "m06Q9" "m06Q10" "m06Q11" "m06_bf"

"m07dem1" "m07dem2" "m07Q1" "m07Q2" "m07Q3" "m07Q4" "m07Q5" "m07Q6" "m07Q7" "m07Q8" "m07Q9" "m07Q10" "m07Q11" "m07_bf"

"m08dem1" "m08dem2" "m08Q1" "m08Q2" "m08Q3" "m08Q4" "m08Q5" "m08Q6" "m08Q7"

"m09dem1" "m09dem2" "m09Q1" "m09Q2" "m09Q3" "m09Q4" "m09Q5" "m09Q6" "m09Q7"

"m10dem1" "m10dem2" "m10Q1" "m10Q2" "m10Q3" "m10Q4"

"m11Q1" "m11Q2" "m11Q3" "m11Q4" "m11Q5" "m11Q6"

)

TASK_JAVA_TRANSLATION_FOLDER="student/Translations/translations_java"
TASK_RUN_TRANSLATION_FOLDER="student/Translations/translations_run"
TASK_TRANSLATION="student/Translations"

shopt -s nullglob;
for j in "${arr[@]}"; do
    if [ ! -d $j ]; then
        echo "Task $j does not exist";
        exit;
    fi
done

for i in utilities/Translations/*.po; do

    # Extract the file name (without path and extention)
    filename=$(basename "$i");
    extension="${filename##*.}";
    filename="${filename%.*}";
    code_LANG=$(basename "$filename") # for example : en, en_US, fr, ...

    #The main .properties for the LANG code_LANG
    properties_file="utilities/Translations/MessagesBundle_$code_LANG.properties"

    #For the translations of the run script
    mkdir -p "utilities/Translations/translations_run/$code_LANG/LC_MESSAGES"
    run_mo_file="utilities/Translations/translations_run/$code_LANG/LC_MESSAGES/run.mo"

    #Generates the .properties file for JAVA
    msgcat $i --properties-output --output-file=$properties_file;
    #Generates the .mo file for PYTHON
    msgfmt $i -o $run_mo_file

    git add $properties_file
    git add $run_mo_file

    # We copy all translations in all tasks
    for j in "${arr[@]}"; do
        #for Java
        mkdir -p $j/$TASK_JAVA_TRANSLATION_FOLDER/
        cp $properties_file $j/$TASK_JAVA_TRANSLATION_FOLDER/MessagesBundle_$code_LANG.properties
        git add $j/$TASK_JAVA_TRANSLATION_FOLDER/MessagesBundle_$code_LANG.properties

        #for run script
        cp -r utilities/Translations/translations_run $j/$TASK_TRANSLATION/;
        git add $j/$TASK_RUN_TRANSLATION_FOLDER
    done
done

git commit -m "Update translations of all tasks"
git push

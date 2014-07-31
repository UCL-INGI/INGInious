#!/bin/sh

export PATH=/usr/local/mozart/bin:$PATH

mkdir /tmp/work
cd /tmp/work

python3 /task/insert_input.py ${input}

# "--max-memory=100" is used to limit the size of each heap in Oz (there are two heaps).
# Without this command, the default heaps size is way too huge for the tiny VMs.
ozengine --max-memory=100 x-oz://system/Compile.ozf -c new_file.oz 2> errC.txt
if [ -f new_file.ozf ]; then # Run new_file.ozf only if there is no compilation errors.
	ozengine --max-memory=100 new_file.ozf 1> out.txt 2> errR.txt
else
	if [ ! -f errR.txt ]; then
		touch errR.txt # Because we check "if errR.txt is empty" in feedback.py
	fi
	if [ ! -f out.txt ]; then
		touch out.txt  # Because we check "if out.txt is empty" in feedback.py
	fi
fi

python3 /task/feedback.py

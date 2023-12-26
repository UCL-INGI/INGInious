#! /bin/bash

FIRST=/tmp/.first
STUDENT_LOGIN="/student_login"

if [[ ! -f "${FIRST}" ]]
then
    # On first login within the KVM
    touch "${FIRST}"

    if [[ -f "${STUDENT_LOGIN}" ]]
    then
	# If the task specifies a given setup to launch (e.g. a mininet script), run it
	./"${STUDENT_LOGIN}"
    else
	# Else, simply spawn a shell in the KVM
	/bin/bash
    fi
else
    /bin/bash
fi

.. _inginious-submission-anonymizer:

inginious-submission-anonymizer
================================

Anonymize INGInious submissions and install them in an INGInious instance if possible (see -c and -p).

If this script is run outside of an INGInious installation, it will output a directory reproducing 
the course structure in the current directory.

Users should note that anonymizing a submission is a possibly destructive operation for tasks
graders since they may rely on some of the cleared fields to produce their feedback. Here is an 
exhaustive list of cleared fields ``[user_ip, _id, archive, grade, submitted_on, time, @email, 
@username]``.

.. program:: inginious-submission-anonymizer

::
    
    inginious-submission-anonymizer [-h] [-c CONFIGURATION] [-p PREFIX] courseid archive

.. option::  -h, --help

    Display the help message.

.. option::  -c CONFIGURATION, --configuration CONFIGURATION

    Path towards an INGInious instance configuration file.

    This is the preferred method to directly install the anonymized submissions within an existing
    instance.

.. option::  -p PREFIX, --prefix PREFIX

    Path towards the tasks directory of an existing INGInious instance. 

    It will be used if this script is run outside of a valid INGInious installation. Otherwise,
    this option is ignored.

.. option::  courseid

    The course ID corresponding to the submissions to anonymize.

.. option::  archive

   Path to the submissions archive.

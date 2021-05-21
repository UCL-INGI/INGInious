Translating tasks
=================

INGInious provides support for translating tasks in the language of your student.
Most users will want to use the `feedback-msg-tpl` command, which is the most straighforward way to do translation.

Another possible method is to use `gettext`. This is by default supported in Python script and feedback templates, but you can use
gettext in any language.

Four steps are necessary to translate a task:

- Mark strings as translatable
- Extract strings to create a `.po` file
- Translate the extracted strings
- Compile the translated strings into a `.mo` file

Marking strings in Python scripts
---------------------------------

Simply import `inginious.lang` and run the command `inginious.lang.init()`. This will install the function `_()` that can be used to mark strings
as translatable.

::

    print(_("Hello"))


Marking strings in feedback templates
-------------------------------------

The function `_()` in always available in feedback templates:

::

    {{ _("Hello") }}

Extracting strings
------------------

Now you need to extract the strings, for this we use `babel`. If it's not already done, install babel:

::

    pip3 install babel

Create a file named "mapping.babel", which contains the `babel mapping <http://babel.pocoo.org/en/latest/messages.html#extraction-method-mapping-and-configuration>`.
Here is an example of mapping that will extract both strings marked in Python and in feedback (Jinja2) templates:

::

    [python: **.py]
    [jinja2: **.tpl]
    encoding = utf-8

If you use other languages, you may want to add the needed options in this file. Refer to the babel documentation.

Now, simply run the following command, which will creates a messages.pot file in your current directory:

::

    pybabel extract -o messages.pot -F mapping.babel .

This messages.pot contains a very simple representation of the strings to translate. Here is an example of what you should obtain after running the
command:

::

    #: test.tpl:1
    msgid "Hello"
    msgstr ""

This will be the basis for all your translations.
Let us put the file in the right place, by creating the correct directory structure:

::

    pybabel init -i messages.pot -d lang -l fr_FR

Replace `fr_FR` by the language your are translating to. This will create a file `lang/fr_FR/LC_MESSAGES/message.po`.

Translating strings
-------------------

In this file, simply change the `msgstr` entries with the translation of the immediately above `msgid`. For example, to
translate the previous example in French (fr_FR):

::

    #: test.tpl:1
    msgid "Hello"
    msgstr "Bonjour"

Compile your `.po` file into a `.mo`
------------------------------------

The final step is to compile your text-based `.po` file into a binary `.mo` file, which ensures that translation occurs smoothly.

::

    pybabel compile -d lang

Which will update all your translations.

I need more help with gettext
-----------------------------

Gettext is a widely used tool; you will find a lot of software-independent help on the net :-)

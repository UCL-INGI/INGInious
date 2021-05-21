.. _StaticPages:

Static pages
============

Static pages can be defined and put in the static folder (see :ref:`ConfigReference`).

A static page is a YAML file with a title and an reStructuredText content. Its filename
is ``<page_id>[.<ISO631>].yaml`` where ``<page_id>`` is an alphanumerical identifier for
the page and ``ISO631`` is the optional ISO-631 language code to display the appropriate
translation to the user if available. Pages are served at ``http(s)://host[:port]/pages/<page_id>``

For instance, the page ``welcome.yaml``, containing the following:
  ::

      title: Welcome !
      content: Welcome on INGInious !

will the served at ``http(s)://host[:port]/pages/welcome``. If ``welcome.fr.yaml`` is specified
and the user has set his/her language to French, ``welcome.fr.yaml`` will be used instead.

Welcome page
------------

A static page can be set as the welcome page, instead of the course list, using the
``welcome_page`` option (see :ref:`ConfigReference`).

Terms of Service & Privacy Policy
---------------------------------

You may have to make some terms of service and/or privacy policy public to your users and make them accept
them before using INGInious.

You can set two static pages and specify them in the configuration file using the ``terms_page``
and ``privacy_page`` options (see :ref:`ConfigReference`).
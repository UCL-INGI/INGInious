Using ReStructuredText in INGInious
===================================

This guide gives some examples on how to use ReStructuredText in INGInious.

Links, images, tables, and other basic things
---------------------------------------------

`The RST documentation is pretty complete <http://docutils.sourceforge.net/docs/ref/rst/directives.html>`_, and
INGInious supports **most** of it. See below for some basic examples.

Example
```````

.. image:: https://raw.githubusercontent.com/UCL-INGI/INGInious/master/inginious/frontend/static/images/header.png

`A link to the image <https://raw.githubusercontent.com/UCL-INGI/INGInious/master/inginious/frontend/static/images/header.png>`_

Math block:

.. math::

  α_t(i) = P(O_1, O_2, … O_t, q_t = S_i λ)

A sentence with inline math: :math:`α_t(i) = P(O_1, O_2, … O_t, q_t = S_i λ)` (you see, it's inline).
:math:`\LaTeX` is supported.


.. table::

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====


Code
````

.. code:: rst

    `The RST documentation is pretty complete <http://docutils.sourceforge.net/docs/ref/rst/directives.html>`_, and
    INGInious supports **most** of it. See below for some basic examples.

    Example
    ```````

    .. image:: https://raw.githubusercontent.com/UCL-INGI/INGInious/master/inginious/frontend/static/images/header.png

    `A link to the image <https://raw.githubusercontent.com/UCL-INGI/INGInious/master/inginious/frontend/static/images/header.png>`_

    Math block:

    .. math::

      α_t(i) = P(O_1, O_2, … O_t, q_t = S_i λ)

    A sentence with inline math: :math:`α_t(i) = P(O_1, O_2, … O_t, q_t = S_i λ)` (you see, it's inline).
    :math:`\LaTeX` is supported.


    .. table::

       =====  =====
         A    not A
       =====  =====
       False  True
       True   False
       =====  =====


Admonitions - warnings, tips, ...
---------------------------------

The following warning/tips/... can be displayed using the code given below.
INGInious is able to parse `standard RST admonitions  <http://docutils.sourceforge.net/docs/ref/rst/directives.html#admonitions>`_
(which are displayed as `bootstrap alerts <https://getbootstrap.com/docs/4.3/components/alerts/>`_).

We also introduced a new option, `:title:`, which allows providing a title. In case a title is given, the
admonitions are displayed as `bootstrap cards <https://getbootstrap.com/docs/4.3/components/card/>`_.

Example
```````

.. raw:: html

    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <div class="card mb-3 border-danger">
    <div class="card-header bg-danger text-white">
    A custom danger title</div>
    <div class="card-body">
    Beware killer rabbits!</div>
    </div>
    <div class="card mb-3 border-warning">
    <div class="card-header bg-warning text-white">
    A custom warning title</div>
    <div class="card-body">
    Water is humid!</div>
    </div>
    <div class="card mb-3 border-info">
    <div class="card-header bg-info text-white">
    You may need this</div>
    <div class="card-body">
    Take this tip with you</div>
    </div>
    <div class="card mb-3 border-default">
    <div class="card-header bg-default">
    Some note</div>
    <div class="card-body">
    Write something here</div>
    </div>
    <div class="card mb-3 border-success">
    <div class="card-header bg-success text-white">
    Bravo!</div>
    <div class="card-body">
    You succeeded!</div>
    </div>
    <div class="card mb-3 border-primary">
    <div class="card-header bg-primary text-white">
    Now in blue</div>
    <div class="card-body">
    Some blue for you</div>
    </div>
    <div class="card mb-3 border-secondary">
    <div class="card-header bg-secondary">
    Now in grey</div>
    <div class="card-body">
    Some grey for you</div>
    </div>
    <div class="card mb-3 border-dark">
    <div class="card-header bg-dark text-white">
    Some dark in the light</div>
    <div class="card-body">
    ...</div>
    </div>
    <div class="alert alert-danger">
    Beware killer rabbits!</div>
    <div class="alert alert-warning">
    Water is humid!</div>
    <div class="alert alert-info">
    Take this tip with you</div>
    <div class="alert alert-success">
    You succeeded!</div>
    <div class="alert alert-primary">
    Some blue for you</div>
    <div class="alert alert-dark">
    ...</div>

Code
````

.. code:: rst

    .. danger::
       :title: A custom danger title

       Beware killer rabbits!

    .. warning::
       :title: A custom warning title

       Water is humid!

    .. tip::
       :title: You may need this

       Take this tip with you

    .. note::
       :title: Some note

       Write something here

    .. admonition:: success
       :title: Bravo!

       You succeeded!

    .. admonition:: primary
       :title: Now in blue

       Some blue for you

    .. admonition:: secondary
       :title: Now in grey

       Some grey for you

    .. admonition:: dark
       :title: Some dark in the light

       ...

    .. danger::
       Beware killer rabbits!

    .. warning::
       Water is humid!

    .. tip::
       Take this tip with you

    .. admonition:: success

       You succeeded!

    .. admonition:: primary

       Some blue for you

    .. admonition:: dark

       ...


Hidden-until
------------

`hidden-until` is a special directive to give feedback after a given date is reached.
The recommended format to indicate the date is `YYYY-MM-DD hh:mm:ss`.

.. code:: rst

    .. hidden-until:: 2020-01-01 12:00:03

        This sentence will only be displayed after the 1st January 2020 at 12:00:03.


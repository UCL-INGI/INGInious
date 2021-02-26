Frontend
========

Social Binding
--------------

It is possible to bind some authentification through social media ( e.g. Facebook,Twitter,Github,...).
Logical part of the binding is manage in a plugin called ``Auth``. It is available in the plugin part of the frontend by default. 
All you need to do is to activate it through the configuration file. 
It is designed as a not mandatory part because of the basic email registration system already implemented in INGInious.
Auth plugin lets you manage different authentification systems (Most of the classical ones).
If you want to add a new auth system, you can simply implement the abstract class ``AuthMethod`` from the user_manager. This defines all the necessary methods.

Most of the methods use OAuth protocol to authenticate users. To correctly implement this protocol, Some methods are mandatory like an authorization link method and a callback.

From another side, INGInious frontend manage specific page to handle good behavior of the workflow. GET and POST handlers are defined for Authentification, Callback and Share functionnalities.
This lets the authentification fully pluginable and adaptable to most of the social media authentification.

LTI
---


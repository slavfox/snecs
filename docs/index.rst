=====
snecs
=====
.. image:: _static/snecs_logo.png
   :alt: snecs - the straightforward, nimble ECS for Python
   :align: center

A straightforward, nimble ECS for Python.
=========================================

.. include:: ../README.rst
   :start-after: teaser-start
   :end-before: teaser-end


Installation
============

``snecs`` is hosted on PyPI_; you can install it the same way as any
PyPI_ package.
Depending on the dependency manager you're using for your project:

pip_:

.. code-block:: console

   $ pip install snecs

Pipenv_:

.. code-block:: console

   $ pipenv install snecs

Poetry_:

.. code-block:: console

   $ poetry add snecs

.. note::

    I highly recommend Poetry. It offers a very pleasant development
    experience, and makes it effortless to manage dependencies, and your
    entire project.

    Regardless of which tool you're using, I recommend installing ``snecs``
    and other Python packages in a `virtual environment`_. Poetry and Pipenv
    handle that for you!

.. _PyPI: https://pypi.org/project/snecs
.. _pip: https://pip.pypa.io/en/stable/
.. _Poetry: https://python-poetry.org/
.. _Pipenv: https://pipenv.pypa.io/en/latest/
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/

A guided tour of ``snecs``
==========================

This documentation is a tour of ``snecs``, structured into sections of
increasing technical detail.

- If you're not familiar with Entity-Component-Systems, the :ref:`ECS` page
  provides a quick explanation of the design pattern.
- When you're ready to start developing with ``snecs``, read
  :ref:`getting_started`. It's a high-level explanation of the library,
  detailing the general flow of working with it.
- You can find the full documentation of all the names that are part of the
  ``snecs`` public API in :ref:`api_reference`.


Notes
=====

``snecs`` is made available under the terms of the Mozilla Public License
Version 2.0, the full text of which is available here_, and included in
LICENSE_. If
you have questions about the license, check Mozilla’s `MPL FAQ`_.

The font used for headings in this documentation is `xkcd Script`_,
distributed by the `ipython`_ organization, and used and redistributed here
under the terms of the `Creative Commons Attribution-NonCommercial 3.0
License`_.

.. _here: https://www.mozilla.org/en-US/MPL/2.0/
.. _LICENSE: https://github.com/slavfox/snecs/blob/master/LICENSE
.. _MPL FAQ: https://www.mozilla.org/en-US/MPL/2.0/FAQ/
.. _xkcd Script: https://github.com/ipython/xkcd-font
.. _ipython: https://github.com/ipython
.. _Creative Commons Attribution-NonCommercial 3.0 License:
    https://github.com/ipython/xkcd-font/blob/master/LICENSE

Full Table of Contents
======================


.. toctree::
   :maxdepth: 2

   ecs
   getting_started
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

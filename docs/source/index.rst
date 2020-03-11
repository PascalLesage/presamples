.. presamples documentation master file, created by
   sphinx-quickstart on Thu Jun  6 16:42:28 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: presamples_logo.png
   :scale: 50 %
   :alt: presamples logo
   :align: right

presamples
======================================

Presamples is used to write, load, manage and verify *presample arrays*.

Presample arrays refer to arrays of values that specific parameters or matrix elements can take on.
The presamples package allows these arrays to be generated *ahead* of their use in a particular model.
This is useful if:

- Generating these values is computationally expensive and there is no need to recalculate them with each model run;
- We want to reuse the *same* values every time a model is solved.

Presamples was initially built specifically for parameters and matrix elements used in life cycle assessment (LCA),
and hence has many methods specifically geared at making the integration of presamples in LCA models easy.
However, it can be used in any other type of model.

Presample's source code is `hosted on github <https://github.com/PascalLesage/presamples/>`_.

Contents:

.. toctree::
   :maxdepth: 2

   installing
   quickstart
   use_with_bw2
   tech_ref
   examples
   pubs
   contributing

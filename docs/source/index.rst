.. presamples documentation master file, created by
   sphinx-quickstart on Thu Jun  6 16:42:28 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

presamples
======================================

Presamples is used to write, load, manage and verify *presample arrays*.

Presample arrays refer to arrays of values that specific parameters can take on. Presamples allows these arrays
to be generated *ahead* of their use in a particular model. This is useful if:

- Generating these values is computationally expensive and there is no need to recalculate them with each model run;
- We want to reuse the *same* values every time a model is solved.

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




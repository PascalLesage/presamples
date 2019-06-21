.. _use_with_bw2:

Using presamples with brightway2
================================

.. _bw2_intro:
Introduction
---------------------------
The presamples package was initially developed for LCA models built using the
`Brightway2 framework <https://brightwaylca.org/>`_. It can efficiently replace values in the different matrices used in
LCA. This can allow you to do many things, among others:

  - Replace randomly sampled values with arrays of correlated values (e.g. to make sure fuel combustion emissions and
  fuel consumption are correlated);
  - Create and easily reuse sets of presample packages representing different scenarios;
  - Include arrays of measured in LCA calculations;
  - Use aggregated datasets in simplified tools and include their uncertainties by storing and using previously
  calculated arrays of aggregated LCI (or LCIA) results;
  - Create under-specified and very uncertain baseline models that can be easily updated with more specific data for
  the evaluation of scenarios.

This section will provide an overview of the most common operations via simple examples. See the :ref:`examples` section
for more detailed use cases.


.. _bw2_matrix_data:
Passing matrix data to presample creation
---------------------------




.. _bw2_lca:
Using presamples in LCA
---------------------------

.. _bw2_MC:
Using presamples in MonteCarloLCA
---------------------------


.. _bw2_fixed_sums:
Fixed sums helper model
---------------------------


.. _bw2_kronecker:
Kronecker delta helper model
---------------------------

.. _bw2_pbm:
Parameterized brightway models
---------------------------


# Docs

* Introduction and use cases
* How to generate presamples
* Data format for different kinds of presamples
* How to specify presamples for a new matrix (dtype, row_formatter, metadata)
* How to use presamples

# Presample generation

* From parameterized inventories
* From generic outside model

# Parameters

Need some major work here on integrating `bw2data` parameters in an easy-to-use way. We need to be able to do the following:

* Load all parameters on any level. Loading parameters on a lower level will automatically load dependent parameters from the higher levels as well. However, we should also be able to pass an "exclusion list", as some values will be defined in other presamples.
* Mangle parameter names. This is already defined in a simple way in bw2parameters (https://bitbucket.org/cmutel/brightway2-parameters/src/default/bw2parameters/mangling.py), but we need auto-generated and consistent prefixes, and the ability to mangle dependent variable names.

# Campaigns

* API and user stories for generating presamples and presample resources (packages?)
* Campaign.replace_presample_package,
* Campaign.add_presample_packages
* Campaign.add_local_presamples: Validate files, figure out if getting name and description from metadata is sensible
* PresamplePackage.metadata

# Tests

* Finish matrix presamples consolidation tests (in matrix_presamples)
* Test parameterized inventory generation and use
* Complete campaign tests

# Models

* Model to generate presamples for a whole database (check processed array md5?)
* Model to generate presamples for an LCIA method (check processed array md5?)

# Packaging

* Adjust CF presamples package to include method that generated them, if available
* Adjust LCA class to filter presamples based LCIA method (need to think about best way)

# Bw2calc

* Tests for multi-column presamples (single-column already done)
* Get changes to PVLCA from Pascal's fork re: storing variable values

# Bw2data

* Load parameters as dictionary or ParameterSet

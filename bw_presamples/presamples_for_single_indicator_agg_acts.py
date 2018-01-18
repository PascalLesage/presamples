import json
import numpy as np
from bw2data import Method
import pyprind
import os
from bw2io.utils import activity_hash
from bw2calc import LCA
from .create_presamples_package import create_presamples_package
# from .campaigns import load_campaign_from_registry


def create_set_of_presamples_packages_for_agg_data(database,
                                                   method,
                                                   presampled_base_dir,
                                                   hash_dict=None,
                                                   overwrite=False):
    """Create presamples packages for dependently sampled aggregated indicator scores arrays
    See [database_wide_monte_carlo](https://github.com/PascalLesage/database_wide_monte_carlo)

    Arguments:
    * ``database``: database with aggregated datasets. Each dataset should contain one biosphere exchange of type "unit impact" for the method of interest.
    * ``method``: tuple for the LCIA method for which the presample is created.
    * ``presampled_base_dict``: location of the dependently sampled arrays.
    *``hash_dict``: if required, a translation table between keys in presampled_base_dir and in database
    Stores presamples arrays in projects presamples directory
    Returns list of filepaths for presamples
    """

    presamples_filepaths = []
    exc_input = ('biosphere3', 'unit impact - {}'.format(Method(method).get_abbreviation()))
    for act in pyprind.prog_bar(database):
        exc_output = act.key
        inv_element = [exc_input, exc_output, 'biosphere']
        if hash_dict:
          arr = np.load(os.path.join(presampled_base_dir, Method(method).get_abbreviation(), hash_dict[act.key[1]]+'.npy'))
        else:
          arr = np.load(os.path.join(presampled_base_dir, Method(method).get_abbreviation(), act.key[1]+'.npy'))
        name = "{} agg result for {}".format(Method(method).get_abbreviation(), act.key)
        id_, fp = create_presamples_package(inventory_elements=[inv_element],
                                            inventory_elements_samples=arr,
                                            name=name,
                                            overwrite=overwrite
                                           )
        presamples_filepaths.append(fp)
    return presamples_filepaths

def list_agg_presamples_in_lca(act, database, campaign_with_agg_datasets_presamples):
    """For a given activity, identify all used presamples for a given aggregated database
    Returns a list of filepaths that can then be used in instanciation of a Monte-Carlo object
    """
    lca = LCA({act:1})
    lca.lci()
    rev_act_dict = {v:k for k, v in lca.activity_dict.items()}
    non_zero_supply = np.nonzero(lca.supply_array)
    potentials = [rev_act_dict[index] for index in list(non_zero_supply[0])]
    all_fps = load_campaign_from_registry(campaign_name = campaign_with_agg_datasets_presamples).ordered_presamples_fps
    presamples_name_to_fp_dict = {json.load(open(os.path.join(fp, 'datapackage.json'), 'r'))['name']: fp for fp in all_fps}
    list_fps = []
    for act in potentials:
        if act[0]==database:
            try:
                list_fps.extend([v for k, v in presamples_name_to_fp_dict.items() if act[1] in k])
            except:
                print("couldn't find anything for {}".format(act))
    return list_fps

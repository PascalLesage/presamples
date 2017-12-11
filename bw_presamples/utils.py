""" Set of functions that generate presample arrays from inventory parameters
    or that assist in doing so.
"""

from bw2data import databases, Database, get_activity
from bw2data.backends.peewee.proxies import Activity, Exchange
from stats_arrays import uncertainty_choices, UncertaintyBase
import numpy as np

def get_exchange(param):
    """ Temporary function that returns an exchange based on input and output keys and type.
    Will not return anything if there is ambiguity.
    Eventually needs to be replaced with something more robust
    Param defined as tuple of input activity, output activity, string label for exchange type (one of technosphere, biosphere or production)
    """
    try:
        act = get_activity(param[1])
    except:
        print("Output for exchange {} not found".format(param))
        return None
    if param[2] == 'technosphere':
        candidates_for_exc = [exc for exc in act.technosphere() if exc.input == param[0]]
    elif param[2] == 'biosphere':
        candidates_for_exc = [exc for exc in act.biosphere() if exc.input == param[0]]
    elif param[2] == 'production':
        candidates_for_exc = [exc for exc in act.production() if exc.input == param[0]]
    else:
        print("Exchange type for {} not well defined: no such exchange type {}".format(param, param[2]))
        return None        
    if len(candidates_for_exc) == 0:
        print("Exchange {} not found".format(exc_approx_id))
        return None
    elif len(candidates_for_exc) > 1:
        print("Exchange {} ambiguous (more than one exchange found)".format(exc_approx_id))
        return None
    else: # If the exchange is found:
        return candidates_for_exc[0]

def convert_exchange_to_param(exc):
    """Transforms a bw2data.backends.peewee.proxies.Exchange into a param (input['key'], output['key'], type)"""
    return (exc.input.key, exc.output.key, exc['type'])

def get_technosphere_input_params_with_shared_unit(act_key, unit, as_params=True):
    """ Returns all technosphere inputs with a specified unit
    If ``as_params``, the params, as (input.key, output.key, type) are returned,
    else the actual exchanges are returned"""
    act = get_activity(act_key)
    exchanges = [exc for exc in act.technosphere() if exc['unit']==unit]
    if as_params:
        return [convert_exchange_to_param(exc) for exc in exchanges]
    else:
        return exchanges

def sum_amounts_of_exchanges(list_exchanges):
    """ Returns the sum of statiic amounts of a set of exchanges.
    Will refuse to cooperate if the exchanges do not have the same unit.
    TODO: Could be refined to convert units (e.g. MJ to kWh to sum heat and electricity)
    """
    assert isinstance(list_exchanges, list), "list_exchanges should be a list"
    assert len(set([exc['unit'] for exc in list_exchanges]))==1, "Exchanges do not all have the same unit" 
    total = 0
    for exc in list_exchanges:
        total += exc['amount']
    return total

def get_rough_samples(exchange_list, iterations):
    """Helper function to generate samples for set of exchanges. 
    Rough samples are postprocessed according to different rules in other functions"""
    samples_arr = np.empty([len(exchange_list), iterations])
    # Populate array and positions_df
    for i, exc in enumerate(exchange_list):
        samples_arr[i, :] = exc.random_sample(iterations)
    return samples_arr
	

def inputs_sum_to_fixed_amount_sample(params, expected_sum='total_static', hold_certain_values_constant=True, iterations=1000):
    """Return a sample array where a set of technosphere exchanges sum to a predetermined amount.
    Useful only in cases where all exchanges are either input or output.
    The fixed sum is ensured by a post hoc rescaling of sampled values, for each iteration

    Input arguments:
    * ``params``: The parameters representing the technosphere exchanges that need to be rescaled
    * ``expected_sum``: The amount all exchanges should add to when rescaling
    * ``hold_certain_values_constant``: If True, exchanges with no uncertainty (uncertainty_type in (0, 1)) are not rescaled
    * ``iterations``: Number of iterations to generate

    Note: there is no way for now to unambiguously identify an exchange. If there is ambiguity, the 
    function will not return anything.
    """    
    # Ensure technosphere inputs all refer to the same activity
    assert len(set([param[1] for param in params]))==1, "All inputs should be for the same activity"
    # Ensure all params are for technosphere inputs
    assert all([param[2]=='technosphere' for param in params]), "All params should refer to technosphere inputs"
    # Get exchange proxy objects:
    exc_list = [get_exchange(param) for param in params]
    # Ensure exc_list does not contain any None
    if any([exc is None for exc in exc_list]):
        print("Could not find all exchanges, no sample generated")
        return None
    # Get expected sum
    if expected_sum == 'total_static':
        expected_sum = sum_amounts_of_exchanges(exc_list)

    # Get rough samples
    samples_arr = get_rough_samples(exc_list, iterations)    

    if hold_certain_values_constant == True:
        # Create collector for exchanges with no uncertainty:
        fixed_indices = []
        for param, exc in zip(params, exc_list):
            if not hasattr(exc, 'uncertainty') or exc.uncertainty['uncertainty type'] in [0, 1]:
                fixed_indices.append(params.index(param))
        if fixed_indices:
            non_fixed_indices = list(set([*range(len(params))]) - set(fixed_indices))        
            for i in range(iterations):
                scaling = (expected_sum-samples_arr[fixed_indices, i].sum())/samples_arr[non_fixed_indices, i].sum()
                samples_arr[non_fixed_indices, i] = scaling * samples_arr[non_fixed_indices, i]
        else:
            hold_certain_values_constant = False # Distinction no longer relevant
    if hold_certain_values_constant == False:
        for i in range(iterations):
            scaling = expected_sum/samples_arr[:, i].sum()
            samples_arr[:, i] = scaling * samples_arr[:, i]
    return samples_arr
		
	
def kronecker_delta_selector(params, negative=False, use_amounts=True, iterations=1000, also_return_random_var=False):
    """Return a sample array where only one exchange amount is not 0, based on the relative probability of occurence of exchanges
    
    Input arguments:
    * ``params``: The parameters representing the exchanges that will be set to 0 or another value for each iteration
    * ``Negative``: If True, the non-zero amounts are negative
    * ``Use amounts``: If True, the non-zero amounts are set to the initial exchange amount. If False, the amounts are 1 or -1
    * ``Iterations``: Number of iterations
    * ``also_return_random_var``: The criteria used to determine whether an exchange amount is 0 or not uses a random sampling between 0 and 1. 
        If this value is True, the sampled values for this variable are also returned. This can be useful for
        sensitivity or contribution to variance analyses
    Note: there is no way for now to unambiguously identify an exchange from params. If there is ambiguity, the 
    function will not return anything.
    Note: The function only makes sense if functionaly equivalent exchanges are randomly selected. This entails that 
    they should all be of the same type (e.g. all technosphere inputs, all emissions, etc.) If they are not,
    the function will not return anything.
    """
    # ensure all exchanges are of the same type
    assert [param[2] for param in params].count(params[0][2]) == len(params), "All exchanges must be of the same type"
    
    exc_list = [get_exchange(param) for param in params]
    # Ensure exc_list does not contain any None
    if any([exc is None for exc in exc_list]):
        print("Could not find all exchanges, no sample generated")
        return None
    
    # Get rough samples
    samples_arr = get_rough_samples(exc_list, iterations)    
    
    # Norm samples so that they will be between 0 and 1
    normed = samples_arr/samples_arr.sum(axis=0)
    # Cummulative sum for each iteration
    cum = np.cumsum(normed, axis=0)
    # Add a zero row
    cum_w_0 = np.concatenate((np.zeros((1, cum.shape[1])), cum), axis=0)
    # Randomly generate values between 0 and 1
    rand = np.random.random(cum_w_0.shape[1])
    # 1 if random value is in range defined by cum_w_0[i-1, i], 0 otherwise
    probs = np.transpose(np.array(
                [[cum_w_0[i-1, j] <= rand[j] < cum_w_0[i, j]
                    for i in np.arange(1, cum_w_0.shape[0])]
                    for j in np.arange(cum_w_0.shape[1])],
                dtype=int))
    # Change sign as necessary:
    if negative:
        probs = np.absolute(probs) * -1
    
    if not use_amounts:
        if also_return_random_var:
            return probs, rand
        else:
            return probs
    else:
        scaling = np.array([exc['amount'] for exc in exc_list])
        if also_return_random_var:
            return np.dot(np.diag(scaling), probs), rand
        else:
            return np.dot(np.diag(scaling), probs)  
        
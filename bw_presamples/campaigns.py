import os
import pandas as pd
import json
import uuid
from bw2data import projects

'''
Registry: dict
{campaign_name:campaign_dict}

campaign: dict
{description: text, presamples: list_presamples_fps, inherits_from:{}}}


'''


''' A dictionary with information on registered ``campaigns``.
	Keys are unique campaign names.
	campaigns are themselves dictionaries with the following information: 
	* ``description``: optional, markdown text description
	* ``presamples``: list, ordered list of presamples filepaths 
	* ``inherits_from``: ordered list of (registry, campaign) tuples on which the given campaign was built.
'''
def create_empty_campaign_registry(registry_name='default', overwrite=False):
	'''Helper function that generates an empty registry.'''
	base_dir = projects.request_directory(r'presamples/_registries')
	registry_fp = os.path.join(base_dir, registry_name + '.json')
	if os.path.isfile(registry_fp):
		if overwrite is False:
			raise FileExistsError("A registry with name {} already exists. Choose a new name or set overwrite to True".format(registry_name))
		else:
			os.remove(registry_fp)
	registry = {}
	with open(registry_fp, 'w') as f:
		json.dump(registry, f)
	return registry_fp

def load_campaign_from_registry(campaign_name, registry_name='default'):
	"""Returns a campaign object based on a campaign name in a specific registry"""
	registry_base_dir = os.path.join(projects.dir, r'presamples/_registries')
	registry_fp = os.path.join(registry_base_dir, registry_name+'.json')
	assert os.path.isfile(registry_fp), "Registry {} does not exist.".format(registry_name)
	with open(registry_fp) as f:
	    registry = json.load(f)
	assert campaign_name in registry, "The campaign {} is not registered in campaign registry {}.".format(campaign_name, registry_name)

	return Campaign(name='campaign_name',\
					description=registry[campaign_name]['description'],\
					inherits_from=registry[campaign_name]['inherits_from'],\
					presamples=registry[campaign_name]['presamples'])

def list_campaigns(registry_name='default'):
	registry_base_dir = os.path.join(projects.dir, r'presamples/_registries')
	registry_fp = os.path.join(registry_base_dir, registry_name+'.json')
	assert os.path.isfile(registry_fp), "Registry {} does not exist.".format(registry_name)
	with open(registry_fp) as f:
	    registry = json.load(f)
	return [campaign_name for campaign_name in registry.keys()]

class Campaign():
	'''Used to describe a campaign, whose main property is an ordered list of presamples.'''
	def __init__(self, name=None, description="", inherits_from=[], presamples=[]):
		'''Create a new campaign instance, which is simply a dictionary. Typical usage is to send a campaign to the campaign registry. 
		Args:
		* ``name``: Unique name to refer to the campaign. If ``None``, the name is set to a random UUID.  
		* ``description``: Optional markdown description of campaign content and context  
		* ``inherits_from``: Used if the campaign builds on an existing campaign. The key:values of the ``inherits_from`` dict respectively refer to registries and lists of campaigns that are registered in the registry. If a registry is missing, or if a campaign is missing from the registry, then the creation of the ``campaign`` will fail.
		* ``presamples``: Used to pass presamples directly to the ``campaign``. Should be a collection of presamples filepaths.
		'''
		if name is None:
			name = uuid.uuid4().hex
		self.name = name
		self.description = description
		self.inherits_from = inherits_from
		self.ordered_presamples_fps = self.load_parent_presamples(inherits_from=inherits_from)
		if presamples:
			self.add_new_presamples(presamples, location='end')

	def load_parent_presamples(self, inherits_from):
		'''Add presamples from registered campaigns listed in the ``inherits_from`` argument in the order that they are listed.
		'''
		assert isinstance(inherits_from, list), "The `inherits_from` argument should be a list of (registry name, campaign name) tuples"
		assert all([isinstance(t, tuple) for t in inherits_from]), "The `inherits_from` contains elements that are not tuples"
		presamples_fps = []
		registry_base_dir = os.path.join(projects.dir, r'presamples/_registries')
		for t in inherits_from:
			campaign = load_campaign_from_registry(t)
			presamples_fps.extend(campaign['presamples'])
		return presamples_fps

	def add_new_presamples(self, presamples, location='end'):
		self.validate_presamples(presamples)
		current_presamples = self.ordered_presamples_fps or []
		LOCATION_ERROR_TEXT = "Valid location arguments are 'beginning', 'end' or tuples with the format ('before', _id) or ('after', _id)."
		NO_REFERENCE_FOR_LOCATION = "Cannot place presamples {} {}: {} not found in presamples list"
		
		def insert_l1_in_l2_at_index(base_list, list_to_insert, index_for_insertion):
			new_list = []
			for i_before in range(index_for_insertion):
				new_list.append(base_list[i_before])
			for obj in list_to_insert:
				new_list.append(obj)
			for i_after in range(index_for_insertion, len(base_list)):
				new_list.append(base_list[i_after])
			return new_list

		if location not in ['beginning', 'end']:
			assert isinstance(location, tuple), LOCATION_ERROR_TEXT
			assert location[0] in ['before', 'after'], LOCATION_ERROR_TEXT
			assert location[1] in current_presamples, NO_REFERENCE_FOR_LOCATION.format(
				location[0], location[1], location[1]
				)

		if self.ordered_presamples_fps == None and location in ['beginning', 'end']:
			index = 'skip'
		elif location=='beginning':
			index=0
		elif location=='end':
			index=len(self.ordered_presamples_fps)
		elif location[0]=='before':
			index=self.ordered_presamples_fps.index(location[1])
		elif location[0]=='after':
			index=self.ordered_presamples_fps.index(location[1])+1
		if index !='skip':
			self.ordered_presamples_fps = insert_l1_in_l2_at_index(
				base_list=current_presamples,
				list_to_insert=presamples,
				index_for_insertion=index
				)
		else:
			self.ordered_presamples_fps = presamples
		return None

	def validate_presamples(self, presamples):
		"""Ensure...that the ``presamples`` argument is a list of existing presamples ``id_``s"""
		BASE_ERROR_TEXT = "The presamples argument should be a list of presamples filepaths."
		assert isinstance(presamples, list), BASE_ERROR_TEXT
		for presample_fp in presamples:
			assert os.path.isfile(os.path.join(presample_fp, 'datapackage.json')),\
				BASE_ERROR_TEXT + "No datapackage at {}".format(presample_fp)


	def add_campaign_to_registry(self, registry_name='default', overwrite=False, return_registry=False):
		'''Add campaign dictionary to specified registry. 
		If registry does not exist, a new one is created.
		If campaign with same name already exists, it is overwritten only if ``overwrite`` is True
		'''
		new_campaign_dict = {
			self.name:{
				'description':self.description,
				'inherits_from':self.inherits_from,
				'presamples':self.ordered_presamples_fps
				}
			}

		registry_fp = os.path.join(
			projects.request_directory(r'presamples/_registries'),
			registry_name+'.json'
			)
		if not os.path.isfile(registry_fp):
			registry={}
		else:
			with open(registry_fp, 'r') as f:
				registry = json.load(f)
		if self.name in registry and overwrite is False:
			raise PermissionError(
				"Campaign {} already exists in registry {}, use ``overwrite=True`` to overwrite".format(
					self.name, registry_name
					)
				)
		registry.update(new_campaign_dict)
		json.dump(registry, open(registry_fp, 'w'))
		if return_registry:
			return registry
		else:
			return None

	def as_dict(self):
		return {key:value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}
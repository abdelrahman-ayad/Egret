#  ___________________________________________________________________________
#
#  EGRET: Electrical Grid Research and Engineering Tools
#  Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
#  (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
#  Government retains certain rights in this software.
#  This software is distributed under the Revised BSD License.
#  ___________________________________________________________________________

"""
The data used for building models in EGRET is stored in a nested Python dictionary.
The format for this dictionary is as follows:

.. code-block:: python
   :linenos:

    {
    'elements':
        {
        <element-type>:
            {
            <element-name>:
                {
                <attribute-1>: <value-1>,
                <attribute-2>: <value-2>,
                ...
                }
            }
        }
    'system':
        {
        <attribute-1>, <value-1>
        }
    }

* The main level must contain the following keys: "elements" and "system".

* data["elements"] is a dictionary where the keys are the element types (e.g. "generator",
  "bus", "load"). Each of these is a dictionary where the keys are the model element names.
  Each of these is a dictionary containing the attributes and values.

* Attributes on modeling elements are typically floats, but can also be any desired
  dictionary-based data structure. There are some specialized attribute values that
  are recognized if the attribute is itself a dictionary with the key "data_type".
  Some supported data types are "time_series" and "cost_curve".

* There are a number of data types in addition to native python data.
  if the "data_type" is equal to "time_series", then the "values" key is interpreted
  as a dictionary that contains key, value pairs where the keys are the timestamps.
  These timestamps could be used to create a slice of the data object at a particular
  time. (See :py:meth:GridData.`slice_at_index`)

* data["system"] is intended to store additional system-wide requirements
  which are not part of the physical infrastructure or modeling elements.

For an example of the dictionary data structure, see the following:

.. code-block:: python
   :linenos:

    {
    'elements':
        {
        'generator':
            {
            'G1': {
                  'generator_type': 'thermal',
                  'connected_bus': 'B1',
                  'pg': 100.0,
                  'qg': 11.0,
                  'in_service': True
                  },
            'G2': {
                  'generator_type': 'solar',
                  'connected_bus': 'B1',
                  'pg': 200.0,
                  'qg': 22.0,
                  'in_service': True
                  }
             },
        'bus':
            {
            'B1': {'bus_type': 'PV'}
            'B2': {'bus_type': 'PQ'}
            'B3': {'bus_type': 'PQ'}
            }
        'branch':
            {
            'TL1': {
                   'from': 'B1',
                   'to': 'B2'
                   }
            'TL1': {
                   'from': 'B2',
                   'to': 'B3'
                   }
            }
        'load':
            {
            'L1': {
                  'connected_bus': 'B2',
                  'Pl': {
                      'data_type':'time_series',
                      'values': {0.0: 11.0, 1.0:111.0, 2.0:111.1}
                      },
                  'Ql': 11.0
                }
            }
        },
    'system': { 
              'reference_bus': 'B1',
              'reference_bus_angle': 0.0,
              },
    }

This module provides the helper class :py:class:`ModelData` that
provides utilities for interacting and manipulating this
nested dictionary structure.

.. todo::

    * Document the data-types for attributes

"""
import logging
import egret.data.data_utils as du
logger = logging.getLogger('egret.model_data')

class ModelData(object):
    @staticmethod
    def empty_model_data_dict():
        """
        Create an empty model_data dictionary with the high-level "elements"
        and "system" keys.

        Returns
        -------
            dict : a new model_data dictionary
        """
        return {"elements": dict(), "system": dict()}
    
    def __init__(self, data=None):
        """
        Create a new ModelData object to wrap a model_data dictionary with some helper methods.

        Parameters
        ----------
        data : dict or None
           An initial model_data dictionary if it is available, otherwise, a new model_data
           dictionary is created.
        """
        if data:
            self.data = data
        else:
            self.data = ModelData.empty_model_data_dict()

    @classmethod
    def read(cls, filename, file_type=None):
        """
        Reads data from a file into a new ModelData object

        Parameters
        ----------
        filename : str
            The path to the file
        file_type : None,str (optional)
            The specification of the file_type. Valid values are 'json', 'json.gz' for json-ed
            EGRET ModelData objects, 'm' for MATPOWER files, 'dat' for Prescient data files, and
            'pglib-uc' for json files from pglib-uc. If None, the file type is inferred from the
            extension.
        """
        valid_file_types = ['json', 'json.gz', 'm', 'dat', 'pglib-uc']
        if file_type is not None and file_type not in valid_file_types:
            raise Exception("Unrecognized file_type {}. Valid file types are {}".format(file_type, valid_file_types))
        elif file_type is None:
            ## identify the file type
            if filename[-5:] == '.json':
                file_type = 'json'
            elif filename[-8:] == '.json.gz':
                file_type = 'json.gz'
            elif filename[-2:] == '.m':
                file_type = 'm'
            elif filename[-4:] == '.dat':
                file_type = 'dat'
            else:
                raise Exception("Could not infer type of file {} from its extension!".format(filename))

        if file_type == 'json':
            import json
            with open(filename) as f:
                data = json.load(f)
        elif file_type == 'json.gz':
            import json
            import gzip
            with gzip.open(filename, 'rt') as f:
                data = json.load(f)
        elif file_type == 'm':
            from egret.parsers.matpower_parser import create_model_data_dict
            data = create_model_data_dict(filename)
        elif file_type == 'dat':
            from egret.parsers.prescient_dat_parser import create_model_data_dict
            data = create_model_data_dict(filename)
        elif file_type == 'pglib-uc':
            from egret.parsers.pglib_uc_parser import create_model_data_dict
            data = create_model_data_dict(filename)

        logger.debug("ModelData read from {}".format(filename))

        return cls(data=data)

    def elements(self, element_type, **kwargs):
        """
        A python generator that loops over modeling elements of a particular element type
        and, if requested, other sub-attributes

        This method provides a generator that loops over the model elements (dictionaries)
        defined in model_data["elements"][element_type]. If additional arguments are provided,
        then those subattributes are also tested.

        Parameters
        ----------
        element_type : str
           Desired element type.
        **kwargs : key=str named arguments
           Additional arguments provides key=value pairs to test on each element.

        Returns
        -------
            generator

        .. todo::
           * need a better error message when element_type is not found

        """
        if element_type not in self.data['elements'].keys():
            return

        if len(kwargs) == 0:
            for name, elem in self.data['elements'][element_type].items():
                yield name, elem
            return

        # additional attributes have been specified
        for name, elem in self.data['elements'][element_type].items():
            include = True
            for k, v in kwargs.items():
                if k not in elem or elem[k] != v:
                    include = False
                    break
            if include:
                yield name, elem

    def attributes(self, element_type, **kwargs):
        """
        Returns a dictionary arranged by attribute -- element-name -- value instead of
        element-name -- attribute -- value.

        This method loops over the modeling elements of a particular element type
        and, if requested, filtes using other sub-attributes. While the original 
        structure follows:

        >>> data['elements'][<element-name>][<attribute>] = <value>  # doctest: +SKIP

        the returned dictionary follows:

        >>> d[<attribute>][<element-name>] = <value>  # doctest: +SKIP

        Note that this call is actually building a dictionary (not a generator).

        Parameters
        ----------
        element_type : str
           Desired element type.
        **kwargs : key=str named arguments
           Additional arguments provides key=value pairs to test on each element.

        Returns
        -------
            dict

        .. todo::
           * need a better error message when element_type is not found

        """
        if element_type not in self.data['elements']:
            return None

        retdict = dict()
        retdict['names'] = list()

        for name, elem in self.elements(element_type=element_type, **kwargs):
            retdict['names'].append(name)
            for attrib, value in elem.items():
                if attrib not in retdict:
                    retdict[attrib] = dict()
                retdict[attrib][name] = value

        return retdict

    def clone(self):
        """
        Create a copy of this ModelData object using a deep copy on the underlying dictionary

        Returns
        -------
            ModelData
        """
        return ModelData(cp.deepcopy(self.data))

    def clone_in_service(self):
        """
        Create a copy of this ModelData object using a deep copy on the underlying dictionary,
        only returning the elements for which the in_service flag is not set to False

        Returns
        -------
            ModelData
        """
        return ModelData(du._copy_only_in_service(self.data))

    def clone_at_time(self, time):
        """
        Create a copy of the ModelData object using values from a single time.

        Create a copy of this ModelData object, but with the following change. Whenever
        a time_series is encountered (recognized by "data_type"="time_series"), the
        attribute containing the time series is replaced with a float value corresponding
        to the specified time, which must be a member of self.data['system']['time_indices'].

        .. todo::
           This can actually be made general based on "data_type" and idx instead of specific to time_series

        Parameters
        ----------
        time : str, int,
           The desired time to use when collapsing the representation.

        Returns
        -------
            ModelData
        """
        time_indices = self.data['system']['time_indices']

        try:
            time_index = time_indices.index(time)
        except ValueError:
            raise ValueError("time {} not found in time_indices'")

        gd = self.clone_at_timeindex(time_index)

        return gd

    def clone_at_time_keys(self, time_keys):
        """
        Creae a copy of the ModelData object using values from a subset of times.

        Create a copy of this ModelData object, but with the following change. Whenever
        a time_series is encountered (recognized by "data_type"="time_series"), the
        attribute containing the time series is replaced with the values corresponding 
        to the times only in times_list. The values in times_list should be a subset 
        of those in self.data['system']['time_indices']

        Parameters
        ----------
        times_list : list 
           A list of times to slice out

        Returns
        -------
            ModelData
        """

        all_times = self.data['system']['time_indices']
        time_indices = du._get_sub_list_indicies(all_times, time_slice)

        gd = self.clone_at_timeindices(time_indices)

        return gd

    def clone_at_time_index(self, time_index):
        """
        Creae a copy of the ModelData object using values from a single time index value.

        Create a copy of this ModelData object, but with the following change. Whenever
        a time_series is encountered (recognized by "data_type"="time_series"), the
        attribute containing the time series is replaced with a float value corresponding
        to the time self.data['system']['time_indices'][time_index].

        Parameters
        ----------
        time_index : int
            The index into time series data at which to copy

        Returns
        -------
            ModelData
        """
        mdclone = ModelData(du._recurse_into_time_index(self.data, time_index))

        ## the new model data has no time
        del mdclone.data['system']['time_indices']

        return mdclone

    def clone_at_time_indices(self, time_indices):
        """
        Creae a copy of the ModelData object using values from a single time index value.

        Create a copy of this ModelData object, but with the following change. Whenever
        a time_series is encountered (recognized by "data_type"="time_series"), the
        time series data is sliced with time_indices, i.e., the times associated with
        the time_indices of 

        Parameters
        ----------
        time_indices : list of ints
            The index into time series data at which to copy

        Returns
        -------
            ModelData
        """
        mdclone = ModelData(du._recurse_into_time_indices(self.data, time_indices))

        old_times = self.data['system']['time_indices']

        mdclone.data['system']['time_indices'] = [old_times[i] for i in time_indices]

        return mdclone

    def write(self, filename, file_type=None):
        """
        Dumps the ModelData object dict to the specified file.
        Optionally, the file_type can be specified if not inferred.

        Parameters
        ----------
        filename : str
            The full filename including extension and path.
        file_type : None
            If specified, the encoding used when writing the file.
            If None, it will be inferred from the file extension.
        """
        valid_file_types = ['json', 'json.gz']
        if file_type is not None and file_type not in valid_file_types:
            raise Exception("Unrecognized file_type {}. Valid file types are {}".format(file_type, valid_file_types))
        elif file_type is None:
            if filename[-5:] == '.json':
                file_type = 'json'
            elif filename[-8:] == '.json.gz':
                file_type = 'json.gz'
            else:
                logger.warning("Unrecognized file_type for file {} in ModelData.write, using 'json'".format(filename))
                file_type = 'json'

        if file_type == 'json':
            import json
            with open(filename,'w') as f:
                json.dump(self.data, f)
        elif file_type == 'json.gz':
            import json
            import gzip
            with gzip.open(filename, 'wt') as f:
                json.dump(self.data, f)
        logger.debug("ModelData written to {}".format(filename))

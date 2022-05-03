import jsonschema
import json
from read_data import read_json

#data_schema_file_name = 'data_schema_error.json' # validating with this should cause an error
data_schema_file_name = 'data_schema.json'
sol_schema_file_name = 'sol_schema.json'

class Validator(object):

    def __init__(self, data_schema=None, sol_schema=None):

        if data_schema is None:
            self.data_schema_file_name = data_schema_file_name
        else:
            self.data_schema_file_name = data_schema
        if sol_schema is None:
            self.sol_schema_file_name = sol_schema_file_name
        else:
            self.sol_schema_file_name = sol_schema
        self.data_schema = read_json(self.data_schema_file_name)
        self.sol_schema = read_json(self.sol_schema_file_name)

    def validate_json_data(self, data):

        jsonschema.validate(instance=data, schema=self.data_schema)

    def validate_json_sol(self, sol):
    
        jsonschema.validate(instance=sol, schema=self.sol_schema)

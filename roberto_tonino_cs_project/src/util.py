# Taken from https://github.com/ojroques/garbled-circuit
import json


# HELPER FUNCTIONS
def parse_json(json_path):
    with open(json_path) as json_file:
        return json.load(json_file)

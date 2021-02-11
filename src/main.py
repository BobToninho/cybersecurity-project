#!/usr/bin/env python3
import logging
import util
import yao
from abc import ABC, abstractmethod
from binary_adder import *
from n_bit_binary_adder import make_n_bit_adder

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)


# Taken from https://github.com/ojroques/garbled-circuit
class YaoGarbler(ABC):
    """An abstract class for Yao garblers (e.g. Alice). Used for local simulation as well"""

    def __init__(self, circuits):
        circuits = util.parse_json(circuits)
        self.name = circuits["name"]
        self.circuits = []

        for circuit in circuits["circuits"]:
            garbled_circuit = yao.GarbledCircuit(circuit)
            pbits = garbled_circuit.get_pbits()
            entry = {
                "circuit": circuit,
                "garbled_circuit": garbled_circuit,
                "garbled_tables": garbled_circuit.get_garbled_tables(),
                "keys": garbled_circuit.get_keys(),
                "pbits": pbits,
                "pbits_out": {w: pbits[w]
                              for w in circuit["out"]},
            }
            self.circuits.append(entry)

    @abstractmethod
    def start(self):
        pass


# Taken from https://github.com/ojroques/garbled-circuit
class LocalTest(YaoGarbler):
    """A class for local tests.

    Print a circuit evaluation or garbled tables.

    Args:
        circuits: the JSON file containing circuits
        print_mode: Print a clear version of the garbled tables or
            the circuit evaluation (the default).
    """

    def __init__(self, circuits, print_mode="circuit"):
        super().__init__(circuits)
        self._print_mode = print_mode
        self.modes = {
            "circuit": self._print_evaluation,
        }
        logging.info(f"Print mode: {print_mode}")

    def start(self):
        """Start local Yao protocol."""
        for circuit in self.circuits:
            self.modes[self.print_mode](circuit)

    def _print_evaluation(self, entry):
        """
        Print circuit evaluation and perform equality check of the result.
        """
        circuit, pbits, keys = entry["circuit"], entry["pbits"], entry["keys"]
        garbled_tables = entry["garbled_tables"]
        outputs = circuit["out"]

        # Alice
        a_wires = circuit.get("alice", [])  # Alice's wires
        a_inputs = {}  # map from Alice's wires to (key, encr_bit) inputs
        print(f'Alice\'s wires {a_wires[::-1]}')

        # Bob
        b_wires = circuit.get("bob", [])  # Bob's wires
        b_inputs = {}  # map from Bob's wires to (key, encr_bit) inputs
        print(f'Bob\'s wires {b_wires[::-1]}\n')

        pbits_out = {w: pbits[w] for w in outputs}  # p-bits of outputs
        total_wires = len(a_wires) + len(b_wires)
        print(f'Total wires: {total_wires}')

        possible_bit_combinations = [
            format(n, 'b').zfill(total_wires) for n in range(2 ** total_wires)]

        print(f"======== {circuit['id']} ========")

        # Generate all possible inputs for both Alice and Bob
        for bits in possible_bit_combinations:
            bits_a = [int(b) for b in bits[:len(a_wires)]]  # Alice's inputs
            bits_b = [int(b) for b in bits[total_wires -
                                           len(b_wires):]]  # Bob's inputs

            # Excluding carry
            bits_per_party = len(bits_b)

            # Map Alice's wires to (key, encr_bit)
            for i in range(len(a_wires)):
                a_inputs[a_wires[i]] = (keys[a_wires[i]][bits_a[i]],
                                        pbits[a_wires[i]] ^ bits_a[i])

            # Map Bob's wires to (key, encr_bit)
            for i in range(len(b_wires)):
                b_inputs[b_wires[i]] = (keys[b_wires[i]][bits_b[i]],
                                        pbits[b_wires[i]] ^ bits_b[i])

            result = yao.evaluate(circuit, garbled_tables, pbits_out, a_inputs,
                                  b_inputs)

            result_list = list(result.values())

            # Format output
            str_bits_a = ''.join(bits[:len(a_wires)])
            str_bits_b = ''.join(bits[len(a_wires):])
            mpc_result = ''.join([str(result[w]) for w in outputs])

            # === Performing the non-MPC function evaluation ===
            n_bits_adder = make_n_bit_adder(bits_per_party)
            non_mpc_result = n_bits_adder(bits_a, bits_b)

            # This operation is necessary because the result of
            # n_bits_adder will have the following shape:
            # R_3, R_2, R_1, R_0, C_3
            #
            # Therefore the displayed wires order needs to be modified accordingly.
            output_wires = outputs[::-1][1:]
            output_wires.append(outputs[-1])

            print(f"Alice{a_wires[::-1]} = {str_bits_a} - "
                  f"Bob{b_wires[::-1]} = {str_bits_b}  ->  "
                  f"Outputs{output_wires} = {mpc_result}  -  "
                  f"Correct result = {non_mpc_result} - "
                  f"Are they equal? {'Yes' if verifyResults(mpc_result, non_mpc_result) else 'No'}")

    @property
    def print_mode(self):
        return self._print_mode

    @print_mode.setter
    def print_mode(self, print_mode):
        if print_mode not in self.modes:
            logging.error(f"Unknown print mode '{print_mode}', "
                          f"must be in {list(self.modes.keys())}")
            return
        self._print_mode = print_mode


def verifyResults(first_input, second_input):
    """
    Equality check performed on the two paramenters. This function
    is used to compare the results of the MPC evaluation and of the
    non-MPC evaluation.
    (The two inputs need to be strings)
    """
    return first_input == second_input


def main(
    party,
    circuit_path,
):
    logging.getLogger().setLevel(logging.CRITICAL)

    if party == "local":
        local = LocalTest(circuit_path, print_mode="circuit")
        local.start()
    else:
        logging.error(f"Unknown party '{party}'")


if __name__ == '__main__':
    import argparse

    def init():
        print('Started running Yao Protocol...\n')

        loglevels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }

        parser = argparse.ArgumentParser(description="Run Yao protocol.")
        parser.add_argument("party",
                            choices=["local"],
                            help="the yao party to run")

        parser.add_argument(
            "-c",
            "--circuit",
            metavar="4bit-adder.json",
            default="src/4bit-adder.json",
            help=("the JSON circuit file for alice and local tests"),
        )

        main(
            party=parser.parse_args().party,
            circuit_path=parser.parse_args().circuit,
        )

    init()

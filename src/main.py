#!/usr/bin/env python3
import logging
# import ot
import util
import yao
from binary_adder import *
from abc import ABC, abstractmethod

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)


# Taken from https://github.com/ojroques/garbled-circuit
class YaoGarbler(ABC):
    """An abstract class for Yao garblers (e.g. Alice)."""

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
            "table": self._print_tables,
        }
        logging.info(f"Print mode: {print_mode}")

    def start(self):
        """Start local Yao protocol."""
        for circuit in self.circuits:
            self.modes[self.print_mode](circuit)

    def _print_tables(self, entry):
        """Print garbled tables."""
        entry["garbled_circuit"].print_garbled_tables()

    def _print_evaluation(self, entry):
        """Print circuit evaluation."""
        circuit, pbits, keys = entry["circuit"], entry["pbits"], entry["keys"]
        garbled_tables = entry["garbled_tables"]
        outputs = circuit["out"]

        # Alice
        a_wires = circuit.get("alice", [])  # Alice's wires
        a_inputs = {}  # map from Alice's wires to (key, encr_bit) inputs
        print(f'Alice\'s wires {a_wires}')

        # Bob
        b_wires = circuit.get("bob", [])  # Bob's wires
        b_inputs = {}  # map from Bob's wires to (key, encr_bit) inputs
        print(f'Bob\'s wires {b_wires}\n')

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
            str_result = ''.join([str(result[w]) for w in outputs])

            alice_carry, *alice_real_input = bits_a

            temp_carry = int(str_bits_a[0], 2)
            result = ''

            for i in range(bits_per_party):
                current_bit_alice = alice_real_input[i]
                current_bit_bob = bits_b[i]
                # print(type(current_bit_alice), type(current_bit_bob))

                # Alice's carry, current Alice's bit, current Bob's bit
                partial_carry, partial_sum = full_adder(
                    temp_carry, current_bit_alice, current_bit_bob)

                result += str(partial_sum)

                temp_carry = partial_carry

            whole_result = str(result) + str(temp_carry)

            print(f"Alice{a_wires} = {str_bits_a} "
                  f"Bob{b_wires} = {str_bits_b}\t"
                  f"Outputs{outputs} = {str_result}   "
                  f"Correct result = {whole_result} "
                  f"Are they equal? {verify(str_result, whole_result)}")

        print()

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

# Inputs as strings


def verify(first_input, second_input):
    return first_input == second_input


def main(
    party,
    circuit_path="add.json",
    print_mode="circuit",
):
    logging.getLogger().setLevel(logging.CRITICAL)

    if party == "local":
        local = LocalTest(circuit_path, print_mode=print_mode)
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
                            choices=["alice", "bob", "local"],
                            help="the yao party to run")
        parser.add_argument(
            "-c",
            "--circuit",
            metavar="circuit.json",
            default="circuits/default.json",
            help=("the JSON circuit file for alice and local tests"),
        )
        parser.add_argument(
            "-m",
            metavar="mode",
            choices=["circuit", "table"],
            default="circuit",
            help="the print mode for local tests (default 'circuit')")

        main(
            party=parser.parse_args().party,
            circuit_path=parser.parse_args().circuit,
            print_mode=parser.parse_args().m,
        )

    init()

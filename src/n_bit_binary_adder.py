from binary_adder import *


def add_n_bits(alice_input, bob_input, bits_per_party=4):
    """
    Computes the sum of two n-bit inputs using concatenated 1bit full adders.
    It returns the result of the sum with the carry appended.

    Input example:
        alice_input = "11101" (1 initial carry, 4 bits representing the number)
        bob_input = "0011" (4 bits representing the number)
        bits_per_party = 4
    Output example: "00011" (4 bits representing the sum, 1 final carry)
    """
    sum_result = ''

    alice_carry, *alice_input_number = alice_input

    # Temporary carry used for subsequent 1bit full adder circuits
    temp_carry = alice_carry

    for i in range(bits_per_party):
        current_bit_alice = alice_input_number[i]
        current_bit_bob = bob_input[i]

        # full_adder arguments:
        #   - current carry
        #   - alice's i-th input bit
        #   - bob's i-th input bit
        partial_carry, partial_sum = full_adder(
            temp_carry, current_bit_alice, current_bit_bob)

        sum_result += str(partial_sum)

        # Carry stored for the next concatenated 1bit full adder
        temp_carry = partial_carry

    return str(sum_result) + str(temp_carry)


def make_n_bit_adder(bits_per_party):
    """
    High order function that dynamically generates the non-MPC function
    to compute according to the number of inputs.
    """
    return lambda x, y: add_n_bits(x, y, bits_per_party)

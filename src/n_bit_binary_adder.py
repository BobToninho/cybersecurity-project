from binary_adder import *


def add_n_bits(alice_input, bob_input, bits_per_party=4):
    result = ''

    alice_carry, *alice_real_input = alice_input
    temp_carry = alice_carry

    for i in range(bits_per_party):
        current_bit_alice = alice_real_input[i]
        current_bit_bob = bob_input[i]

        # Current carry, current Alice's bit, current Bob's bit
        partial_carry, partial_sum = full_adder(
            temp_carry, current_bit_alice, current_bit_bob)

        result += str(partial_sum)

        temp_carry = partial_carry

    # whole_result = str(result) + str(temp_carry)

    return str(result) + str(temp_carry)


def make_n_bit_adder(bits_per_party):
    return lambda x, y: add_n_bits(x, y, bits_per_party)

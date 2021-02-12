# Taken from https://gist.githubusercontent.com/wray/16f972ec739c5e3f0cb8/raw/497ce48d684221d7fa740a10b0d4cb7514782450/binary_adder.py
#
# To use these functions, you can run python and then import like -
# from binary_adder import *
#
# These methods carry out binary addition via 'digital logic'
# This is really what happens at the logic circuit level.
# So, this is a pretty abstract use of programming to illustrate
# what happens on silicon using code many, many, levels above that!
#

def half_adder(a, b):
    """
    A binary half adder -- performing addition only using logic operators,
    A half adder simply adds two bits and outputs a sum and carry
    """

    # ^ is logical xor in python
    sum = a ^ b
    carry = a and b
    return carry, sum


def full_adder(carry_in, a, b):
    """
    A binary full adder
    The full adder can add 3 bits (can handle an incoming carry)
    Also returns a sum and carry
    """
    carry1, sum1 = half_adder(carry_in, a)
    carry2, sum = half_adder(sum1, b)
    carry = carry1 or carry2
    return carry, sum


def binary_adder(a, b):
    """
    This method virtually chains together binary full adders in order
    to add binary numbers of arbitrary size.

    a and b are expected to be strings representing binary integers.
    """

    an = len(a)
    bn = len(b)

    # Convert strings to list of bits -- very functional syntax here
    al = list(int(x, 2) for x in list(a))
    bl = list(int(x, 2) for x in list(b))

    # Pad smaller list with 0's
    dif = an - bn
    # more digits in a than b
    if dif > 0:
        for i in range(dif):
            bl.insert(0, 0)
    else:
        for i in range(abs(dif)):
            al.insert(0, 0)

    # print(al)
    # print(bl)

    result = []
    carry = 0
    # Iterate through list right to left, calling full_adder each time and
    # inserting the sum each time
    for i in range(len(al)-1, -1, -1):
        carry, sum = full_adder(carry, al[i], bl[i])
        result.insert(0, sum)
        # print (result)
    result.insert(0, carry)

    return ''.join(str(x) for x in result)


def test_binary_adder(a, b):
    result = binary_adder(a, b)
    print(result)
    if (int(a, 2) + int(b, 2)) == int(result, 2):
        print("Woo hoo! It works")
    else:
        print("FAIL!!")
    print(str(int(a, 2)) + " + " + str(int(b, 2)) + " = " + str(int(result, 2)))

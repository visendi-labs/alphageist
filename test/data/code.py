import random
from sympy import isprime

def generate_random_prime(start, end):
    """A function that generates random prime numbers"""
    while True:
        num = random.randint(start, end)
        if isprime(num):
            return num
# helloworld.py
def add(a, b):
    return a + b

# def test_add():
  #  assert add(2, 3) == 5  # This is a pytest test function


    # test.py

from helloworld import add

def test_add():
    assert add(2, 3) == 6  # This will fail because 2 + 3 is 5, not 6



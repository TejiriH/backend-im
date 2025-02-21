# helloworld.py

def hello_world():
    print("Hello, World!")
    # Fixed syntax error: Added parentheses to the print statement
    print("This will no longer cause a syntax error")

if __name__ == "__main__":
    hello_world()

# helloworld.py
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5  # This is a pytest test function



import time
# print("lineee", end="\r")
# time.sleep(1.5)

# print("\aaaa")
inp = input("press key")
print(inp)
try:
    try:
        open("nonexistentfile")
    except Exception as e:
        print(f'caught exception: {e}')
        raise Exception('my custom exception')

excepts Exception as ox:
    print(f'got my second exception: {ox}')

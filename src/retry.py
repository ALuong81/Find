import time

def retry(func, n=3):
    for _ in range(n):
        try:
            return func()
        except:
            time.sleep(1)
    return None

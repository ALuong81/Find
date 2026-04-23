import time

def retry(func, max_retry=3):

    for i in range(max_retry):
        try:
            return func()
        except Exception as e:

            if "Rate Limit" in str(e):
                print("⏳ WAIT RATE LIMIT...")
                time.sleep(10)

            else:
                time.sleep(2)

    return None

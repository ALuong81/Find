from concurrent.futures import ThreadPoolExecutor

def parallel_map(func, items, max_workers=10):

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(func, i) for i in items]

        for f in futures:
            try:
                results.append(f.result())
            except:
                continue

    return results

import numpy as np


# this function generates load randomly uniformly distributed
def _generate_load(eta, sigma):
    # to reproduce results
    np.random.seed(100)
    # WARNING: randomness generates problems with the optimization
    tmp = np.random.randint(eta - sigma / 2, eta + sigma / 2)
    return tmp

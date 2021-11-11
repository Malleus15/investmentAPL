import numpy as np
import business_logic.constant as const


class Investor:
    def __init__(self, index, itype, beta, eta, sigma):
        # the index is required to have a fixed and static position in the coalition tuple
        # and to sort the investors in the coalition
        self.index = index
        self.type = itype
        self.beta = beta
        self.eta = eta
        self.sigma = sigma

    # this function generates load randomly uniformly distributed
    def _generate_load_all_t(self):
        # to reproduce results
        np.random.seed(100)
        # WARNING: randomness generates problems with the optimization
        tmp = np.random.randint(self.eta - self.sigma, self.eta + self.sigma, const.T_HORIZON)
        return tmp

    def converted_load_all_t(self):
        if self.type != 'NO':
            # conversion to numpy to do the multiplication after
            load = np.array(self._generate_load_all_t())
            # converting load in needed resources to serve the load
            converted_load = load * const.GAMMA
        else:
            converted_load = np.zeros(shape=const.T_HORIZON)
        return converted_load

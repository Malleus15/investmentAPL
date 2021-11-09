import numpy as np

from itertools import chain, combinations
import constant as const

from investor import Investor


# this function generates load randomly uniformly distributed
def generate_load(eta, sigma):
    # to reproduce results
    np.random.seed(100)
    # WARNING: randomness generates problems with the optimization
    tmp = np.random.randint(eta - sigma / 2, eta + sigma / 2)
    return tmp


def _all_permutations(iterable):
    "all_permutation([0,1,2]) --> () (0,) (1,) (2,) (0,1) (0,2) (1,2) (0,1,2)"
    s = list(iterable)
    return list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))


# with this function we calculate all the combination of investors
def feasible_permutations(investors_number, rt_players):
    set_investors = []

    if rt_players is None:
        # one half rt and the other half nrt
        rt_players = round((investors_number - 1) / 2)
    # assign type to players
    for i in range(investors_number):
        # valid only for SPs
        # SPs NRT
        if i != 0 and rt_players > 0:
            set_investors.append(Investor("rt", const.RT_BETA))
            rt_players -= 1
        # SPs NRT
        elif i != 0:
            set_investors.append(Investor("nrt", const.NRT_BETA))
        # NO
        else:
            set_investors.append(Investor("NO", const.NO_BETA))

    perms = _all_permutations(set_investors)
    return perms

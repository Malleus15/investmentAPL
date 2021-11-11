from itertools import chain, combinations
import constant as const

from investor import Investor


def _all_permutations(iterable):
    "all_permutation([0,1,2]) --> () (0,) (1,) (2,) (0,1) (0,2) (1,2) (0,1,2)"
    s = list(iterable)
    return list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))


# with this function we calculate all the combination of investors
def feasible_permutations(players_number, rt_players):
    set_investors = []

    if rt_players is None:
        # one half rt and the other half nrt
        rt_players = round((players_number - 1) / 2)
    # assign type to players
    for i in range(players_number):
        # valid only for SPs
        # SPs NRT
        if i != 0 and rt_players > 0:

            set_investors.append(Investor(i, "rt", const.RT_BETA, const.RT_ETA, const.RT_SIGMA))
            rt_players -= 1
        # SPs NRT
        elif i != 0:
            set_investors.append(Investor(i, "nrt", const.NRT_BETA, const.NRT_ETA, const.NRT_SIGMA))
        # NO
        else:
            set_investors.append(Investor(i, "NO", const.NO_BETA, const.NO_ETA, const.NO_SIGMA))

    perms = _all_permutations(set_investors)

    return perms

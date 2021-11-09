import numpy as np

from business_logic import utils
from business_logic.game import Game


def main(investors_number, number_rt_players, price_cpu, hosting_capacity, duration_cpu):
    game = Game(investors_number, price_cpu, hosting_capacity, duration_cpu)
    # the number of non realtime players is calculated removing from the investors number rt number and the Host
    # investor
    nrt_players_numb = investors_number - number_rt_players - 1

    # each coalition element is a tuple player = (id, type)
    coalitions = utils.feasible_permutations(investors_number, number_rt_players)
    grand_coalition = coalitions[-1]

    all_infos = []
    payoff_vector = []
    beta_centr = price_cpu / (duration_cpu * 96)  # are the time slots

    # trying configurations
    configurations = [beta_centr / 5, beta_centr / 4, beta_centr / 3, beta_centr / 2, beta_centr, 1 * beta_centr,
                      2 * beta_centr, 3 * beta_centr, 4 * beta_centr, 5 * beta_centr, 6 * beta_centr,
                      7 * beta_centr,
                      8 * beta_centr]

    for configuration in configurations:
        infos_all_coal_one_config = []
        all_coal_payoffs = []
        beta = configuration
        # setto beta per ogni service provider
        # we exclude the empty coalition
        for coalition in coalitions[1:]:
            # preparing parameters to calculate payoff
            game.set_coalition(coalition)
            # total payoff is the result of the maximization of the v(S)
            sol = game.calculate_coal_payoff()

if __name__ == '__main__':
    main(3, 1, 0.5, 20000000000, 3)
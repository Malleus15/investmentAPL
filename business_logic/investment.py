import numpy as np
import business_logic.constant as const

from business_logic import utils
from business_logic.game import Game
from business_logic.fair_game import FairGame


def simulate_invest(investors_number, number_rt_players, price_cpu, hosting_capacity, duration_cpu,
                    fairness=True):
    if fairness:
        #CORREGGIII E DISCTINGUI FAIR E NON
        game = FairGame(investors_number, price_cpu, hosting_capacity, duration_cpu)
    else:
        game = FairGame(investors_number, price_cpu, hosting_capacity, duration_cpu)
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
            if coalition == coalitions[-1]:
                PIPPO = sol['x'][-1] * price_cpu
                resources_alloc = sol['x']
            # we store payoffs and the values that optimize the total coalition's payoff
            coal_payoff = -sol['fun']
            info_dict = {"configuration": {
                "cpu_price_mCore": configuration,
                "horizon": duration_cpu
            }, "coalition": coalition,
                "coalitional_payoff": coal_payoff,
            }

            # keeping the best coalition for a given configuration
            infos_all_coal_one_config.append(info_dict)
            all_coal_payoffs.append(coal_payoff)
            if coalition == grand_coalition:
                grand_coal_payoff = coal_payoff

        # choosing info of all coalition for the best config
        payoff_vector = game.shapley_value_payoffs(infos_all_coal_one_config,
                                                   investors_number,
                                                   coalitions)

        print("Shapley value is in the core, the fair payoff is:", payoff_vector, "\n")
        # Further verification of the solution (payoff vector) in the core
        # check_core = business_logic.verify_properties(all_coal_payoffs, grand_coal_payoff, payoff_vector)

        if True:
            print("Coalition net incomes:", grand_coal_payoff)
            print("Capacity:", sol['x'][-1], "\n")
            print("Resources split", sol['x'][:-1], "\n")
        all_infos.append(infos_all_coal_one_config)

        print("Each player pay:\n")

        print("Proceeding with calculation of revenues vector and payments\n")
        # res = business_logic.how_much_rev_paym(payoff_vector, sol['x'])
        res = np.identity(investors_number)

        print("Revenue array:", res[0], "\n")
        print("Payment array:", res[1], "\n")
        if abs(PIPPO - sum(res[1])) > 0.001:
            print("ERROR: the sum of single payments (for each players) doesn't match the  ")
        else:
            print("Total payment and sum of single payments are equal!\n")

        return grand_coal_payoff, payoff_vector, res[0], res[1]

# the check of parameters is done by the business_logic and not by the DataBase because the business logic is up
# to the business_logic
def check_parameters(investors_number, rt_numb_invest, price_cpu, duration_cpu, hosting_capacity):
    price_check = (const.MIN_PRICE_CPU <= price_cpu <= const.MAX_PRICE_CPU)
    # limited for computational reasons
    inv_num_check = (const.MIN_INV_NUM <= investors_number <= const.MAX_INV_NUM)
    # years
    duration_check = (const.MIN_DURATION <= duration_cpu <= const.MAX_DURATION)
    # in milliCore
    hc_check = (const.MIN_HC <= hosting_capacity <= const.MAX_HC)
    # we check the rt investors are less than the numb of investors
    rt_numb_check = (0 <= rt_numb_invest <= investors_number - 1)
    return price_check and inv_num_check and duration_check and hc_check and rt_numb_check



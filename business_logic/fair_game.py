import math

import coop_properties as cp
from business_logic.game import Game


class FairGame(Game):

    def is_convex(self, coalitions_infos):
        return cp.is_convex(coalitions_infos)


    def shapley_value_payoffs(self, infos_all_coal_one_config, players_number, coalitions):
        x_payoffs = []
        N_factorial = math.factorial(players_number)
        for player in coalitions[-1]:
            coalitions_dict_without_i = []
            coalitions_dict_with_i = []
            for coalition_dict in infos_all_coal_one_config:
                if player not in coalition_dict["coalition"]:
                    coalitions_dict_without_i.append(coalition_dict)
                else:
                    coalitions_dict_with_i.append(coalition_dict)
            summation = 0
            for S in coalitions_dict_without_i:
                for q in coalitions_dict_with_i:
                    if tuple(set(S["coalition"]).symmetric_difference(q["coalition"])) == (player,):
                        contribution = q["coalitional_payoff"] - S["coalitional_payoff"]
                        tmp = math.factorial(len(S["coalition"])) * math.factorial(
                            players_number - len(S["coalition"]) - 1) * contribution
                        summation = summation + tmp
            x_payoffs.append((1 / N_factorial) * summation)

        return x_payoffs
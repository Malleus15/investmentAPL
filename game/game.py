import numpy as np

import game.coop_properties as cp
from game import core
from scipy.optimize import linprog
import constant as const

class Game:
    def __init__(self, p_cpu, duration_cpu, hosting_capacity, investors_number, investors_array):
        self.p_cpu = p_cpu
        self.duration_cpu = duration_cpu
        self.hosting_capacity = hosting_capacity
        self.investors_number = investors_number
        self.investors_array = investors_array

    # the check of parameters is done by the game and not by the DataBase because the business logic is up to the game
    def check_parameters(self):
        price_check = (const.MIN_PRICE_CPU <= self.price_cpu <= const.MAX_PRICE_CPU)
        # limited for computational reasons
        inv_num_check = (const.MIN_INV_NUM <= self.investors_number <= const.MAX_INV_NUM)
        # years
        duration_check = (const.MIN_DURATION <= self.duration_cpu <= const.MAX_DURATION)
        # in milliCore
        hc_check = (const.MIN_HC <= self.hosting_capacity <= const.MAX_HC)
        # we check that ay least the main investor and one secondary investor is present
        tmp = self.investors_array
        array_check = (tmp.count("host") == 1) and (tmp.count("rt") >= 1 or tmp.count("nrt") >= 1)
        return price_check and inv_num_check and duration_check and hc_check and array_check

    # this function convert the load from requests per timeslot
    # to millicore (computational resources needed to serve the load)
    def _convert_load_at_t(self, investor_type):
        # if a real time SP, e.g. Peugeot
        if investor_type == "rt":
            # eta is the average value to generate load
            # sigma is the variability of the range in which we generate the variables
            load = self._generate_load(const.RT_ETA, const.RT_SIGMA)
        # if not real time SP, e.g. Netflix
        else:
            load = self._generate_load(const.NRT_ETA, const.NRT_SIGMA)
        # converting load in needed resources
        converted_load = load * const.GAMMA
        return converted_load

    def calculate_coal_payoff(self):
        # matrix with all the b for each player
        b = np.zeros(shape=self.players_numb * const.T_HORIZON)
        # if the network operator is not in the coalition or It is alone etc...
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition or (len(coalition) == 0) or (len(coalition) == 1):
            pass
        else:
            # we calculate utility function at t for a player only for SPs
            # coalition is a tuple that specify the type of player also
            indx = 2
            for player in coalition[1:]:
                # in the paper y_t^S
                for t in range(T_horizon):
                    player_type = player[1]
                    tmp0 = self._player_utility_t(player_type)
                    b[indx] = tmp0
                    indx += 1
                # we divide by 2 the used resources because we need to split the payoff in a non fair way adding a
                # false use of resources by the NO in order to pay the NO for his presence, in fact the cpu exists
                # thanks to him
        # cost vector with benefit factor and cpu price
        # we use a minimize-function, so to maximize we minimize the opposite
        # Creating c vector
        tmp0 = expiration * np.concatenate((np.zeros(shape=T_horizon), betas[0] * np.ones(shape=T_horizon),
                                            betas[1] * np.ones(shape=T_horizon)))
        tmp1 = expiration * chi * np.ones(shape=(players_numb * T_horizon))
        tmp2 = np.zeros(shape=players_numb)
        c = np.concatenate((tmp0, tmp1, tmp2, [-p_cpu]), axis=0)
        # Creating A matrix
        identity = np.identity(players_numb * T_horizon)
        zeros = np.zeros(shape=(players_numb * T_horizon, players_numb * T_horizon))
        zeros_column = np.zeros(shape=(players_numb * T_horizon, 1))
        tmp0 = np.zeros(shape=(players_numb * T_horizon, players_numb))
        mega_row_A0 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        tmp = 0
        for col in range(players_numb):
            for row in range(T_horizon):
                tmp0[row + tmp, col] = -1
            tmp += T_horizon

        mega_row_A1 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        mega_row_A2 = np.concatenate((zeros, identity, tmp0, zeros_column), axis=1)

        tmp = np.zeros(shape=(players_numb * T_horizon, players_numb))
        mega_row_A3 = np.concatenate((zeros, identity, -tmp, zeros_column), axis=1)

        tmp0 = np.zeros(shape=(1, 2 * players_numb * T_horizon))
        tmp1 = np.zeros(shape=(1, players_numb))
        mega_row_A4 = np.concatenate((tmp0, tmp1, [[-1]]), axis=1)

        tmp1 = np.ones(shape=(1, players_numb))
        A_eq = np.concatenate((tmp0, tmp1, [[-1]]), axis=1)
        b_eq = [[0]]

        A = np.concatenate((mega_row_A0, mega_row_A1, mega_row_A2, mega_row_A3, mega_row_A4), axis=0)

        tmp0 = np.zeros(shape=(players_numb * T_horizon))
        b = np.concatenate((b, tmp0, b, tmp0, [HC]), axis=0)
        # for A_ub and b_ub I change the sign to reduce the matrices in the desired form
        bounds = ((0, None),) * (4 * players_numb * T_horizon + players_numb + 1)
        params = (c, A, b, A_eq, b_eq, bounds, T_horizon)
        # sol = core.find_core(params)
        sol = core.find_core(p_cpu, T_horizon, coalition, players_numb, HC, betas, loads, expiration)
        return sol


def calculate_core(infos_all_coal_one_config):
    players_numb = self.get_params()[5]
    A_eq = np.ones(shape=players_numb)
    b_eq = infos_all_coal_one_config[-1]["coalitional_payoff"]

    for i in range(len(infos_all_coal_one_config) - 1):
        tmp0 = [0] * players_numb
        for pl in infos_all_coal_one_config[i]["coalition"]:
            tmp0[pl[0]] = -1
        if i == 0:
            tmp = tmp0
        else:
            tmp = np.concatenate((tmp, tmp0))
    A = [[-1, 0, 0], [0, -1, 0], [0, 0, -1], [-1, -1, 0], [-1, 0, -1], [0, -1, -1]]
    b = []

    for info in infos_all_coal_one_config[:-1]:
        b.append(-info["coalitional_payoff"])

    coefficients_min_y = [0] * (len(A[0]))
    res = linprog(coefficients_min_y, A_eq=A_eq, b_eq=b_eq, A_ub=A, b_ub=b)
    return res['x']


def verify_properties(all_coal_payoff, coal_payoff, payoffs_vector):
    print("Verifying properties of payoffs \n")
    if cp.is_an_imputation(coal_payoff, payoffs_vector):
        print("The vector is an imputation (efficiency + individual rationality)!\n")
        print("Check if payoff vector is group rational...\n")
        if cp.is_group_rational(all_coal_payoff, -coal_payoff):
            print("The payoff vector is group rational!\n")
            print("The payoff vector is in the core!\n")
            print("Core verification terminated SUCCESSFULLY!\n")
            return True
        else:
            print("The payoff vector isn't group rational!\n")
            print("The payoff vector is not in the core!\n")
            print("Core verification terminated unsuccessfully!\n")
    else:
        print("The payoff vector isn't an imputation\n")
        print("Core verification terminated unsuccessfully!\n")
    return False

    def how_much_rev_paym(self, payoff_vector, w):
        p_cpu, T_horizon, coalition, _, beta, players_numb, chi, alpha, HC, betas, gammas, loads, expiration = get_params()
        # Creating c vector
        tmp0 = expiration * np.concatenate(
            (np.zeros(shape=T_horizon), betas[0] * np.ones(shape=T_horizon), betas[1] * np.ones(shape=T_horizon)))
        tmp1 = expiration * chi * np.ones(shape=(players_numb * T_horizon))
        tmp2 = np.zeros(shape=players_numb)
        beta_vec = np.concatenate((tmp0, tmp1, tmp2), axis=0)
        # building A matrix
        identity = np.identity(players_numb)
        tmp0 = np.concatenate((identity, -identity), axis=1)
        ones = np.ones(shape=(1, players_numb))
        zeros = np.zeros(shape=(1, players_numb))
        tmp1 = np.concatenate((ones, zeros), axis=1)
        zeros = np.zeros(shape=(players_numb - 1, players_numb + 1))
        identity = np.identity(players_numb - 1)
        tmp2 = np.concatenate((identity, zeros), axis=1)
        A_eq = np.concatenate((tmp0, tmp1, tmp2), axis=0)
        print(A_eq)
        # building b vector
        b_eq = np.zeros(shape=(players_numb + 1))
        tmp0 = (np.array(payoff_vector[:-1]) / (sum(payoff_vector) + 0.000001)) * (sum(payoff_vector) + p_cpu * w[-1])
        for i in range(players_numb):
            b_eq[i] = payoff_vector[i]
        b_eq[-1] = np.matmul(w[:len(beta_vec)], beta_vec)
        coefficients_min_y = [0] * (len(A_eq[0]))
        b_eq = np.concatenate((np.array(b_eq), tmp0), axis=0)
        res = linprog(coefficients_min_y, A_eq=A_eq, b_eq=b_eq, method="simplex")
        return res['x'][0:players_numb], res['x'][players_numb:]

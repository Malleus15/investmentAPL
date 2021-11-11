import numpy as np

import business_logic.coop_properties as cp
from business_logic import core
from scipy.optimize import linprog
import constant as const


class Game:
    def __init__(self, investors_number, price_cpu, hosting_capacity, duration_cpu):
        self.coalition = None
        self.p_cpu = price_cpu
        self.duration_cpu = duration_cpu
        self.hosting_capacity = hosting_capacity
        self.investors_number = investors_number

    # the check of parameters is done by the business_logic and not by the DataBase because the business logic is up
    # to the business_logic
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

    def calculate_coal_payoff(self):
        # matrix with all the b for each player
        b = np.zeros(shape=self.investors_number * const.T_HORIZON)
        c = np.zeros(shape=2 * self.investors_number * const.T_HORIZON + self.investors_number + 1)
        # if the network operator is not in the coalition or It is alone etc..
        check_NO = next((x for x in self.coalition if x.type == 'NO'), True)
        # print((check_NO,) == self.coalition, (check_NO,), self.coalition)
        # I write the comparison == with true because if no I return the object in some case
        condition = check_NO == True or (check_NO,) == self.coalition or (len(self.coalition) == 0) or (
                len(self.coalition) == 1)
        # print("condition", condition)

        if not condition:
            # we calculate utility function for all t for a player only for SPs
            # coalition is a tuple of investors
            b = np.array([])
            c = np.array([])

            for i in range(self.investors_number):
                # if there is that investor in the coalition we create the array for that player
                check = next((x for x in self.coalition if x.index == i), False)
                if check!=False:
                    tmp0 = check.converted_load_all_t()
                    tmp1 = check.beta * np.ones(shape=const.T_HORIZON)
                else:
                    tmp0 = np.zeros(shape=const.T_HORIZON)
                    tmp1 = tmp0

                b = np.concatenate((b, tmp0))
                c = np.concatenate((c, tmp1))

            # Creating c vector
            # cost vector with benefit factor and cpu price
            c = np.concatenate((c, np.zeros(shape=self.investors_number),
                                const.CHI * np.ones(shape=self.investors_number * const.T_HORIZON), [-self.p_cpu]))

        # Creating A matrix
        identity = np.identity(self.investors_number * const.T_HORIZON)
        zeros = np.zeros(shape=(self.investors_number * const.T_HORIZON, self.investors_number * const.T_HORIZON))
        zeros_column = np.zeros(shape=(self.investors_number * const.T_HORIZON, 1))
        tmp0 = np.zeros(shape=(self.investors_number * const.T_HORIZON, self.investors_number))
        mega_row_A0 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        tmp = 0
        for col in range(self.investors_number):
            for row in range(const.T_HORIZON):
                tmp0[row + tmp, col] = -1
            tmp += const.T_HORIZON

        mega_row_A1 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        mega_row_A2 = np.concatenate((zeros, identity, tmp0, zeros_column), axis=1)

        tmp = np.zeros(shape=(self.investors_number * const.T_HORIZON, self.investors_number))
        mega_row_A3 = np.concatenate((zeros, identity, -tmp, zeros_column), axis=1)

        tmp0 = np.zeros(shape=(1, 2 * self.investors_number * const.T_HORIZON))
        tmp1 = np.zeros(shape=(1, self.investors_number))
        mega_row_A4 = np.concatenate((tmp0, tmp1, [[-1]]), axis=1)

        tmp1 = np.ones(shape=(1, self.investors_number))
        A_eq = np.concatenate((tmp0, tmp1, [[-1]]), axis=1)
        b_eq = [[0]]

        A = np.concatenate((mega_row_A0, mega_row_A1, mega_row_A2, mega_row_A3, mega_row_A4), axis=0)

        tmp0 = np.zeros(shape=(self.investors_number * const.T_HORIZON))
        b = np.concatenate((b, tmp0, b, tmp0, [self.hosting_capacity]), axis=0)
        # for A_ub and b_ub I change the sign to reduce the matrices in the desired form
        bounds = ((0, None),) * (4 * self.investors_number * const.T_HORIZON + self.investors_number + 1)
        params = (c, A, b, A_eq, b_eq, bounds, const.T_HORIZON)
        sol = core.find_core(params)
        return sol

    def calculate_core(self, infos_all_coal_one_config):
        A_eq = np.ones(shape=self.investors_number)
        b_eq = infos_all_coal_one_config[-1]["coalitional_payoff"]

        for i in range(len(infos_all_coal_one_config) - 1):
            tmp0 = [0] * self.investors_number
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

    def set_coalition(self, coalition):
        self.coalition = coalition

    def verify_properties(self, all_coal_payoff, coal_payoff, payoffs_vector):
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

    def split_rev_paym(self, payoff_vector, w):
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

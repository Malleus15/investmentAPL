# benefit factor
RT_BETA = 0.005
NRT_BETA = 0.002
# mean for load
RT_ETA = 1000
NRT_ETA = 100
# variation for load
RT_SIGMA = RT_ETA/4
NRT_SIGMA = NRT_ETA/4
# conversion factor (from requests to millicore)
GAMMA = 10
# number of timeslots that we consider for the investment
T_HORIZON = 96

# BOUNDS
# cpu's price
MIN_PRICE_CPU = 0.05
MAX_PRICE_CPU = 1
# hosting capacity
MIN_HC = 1000
MAX_HC = 1000000
# duration cpu (years)
MIN_DURATION = 1
MAX_DURATION = 5
# investors number bounds (for computational reasons at most 8, i.e. to be fast enough)
MIN_INV_NUM = 2
MAX_INV_NUM = 8

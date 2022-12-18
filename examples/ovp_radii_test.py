import sys
import pythonnuketools
from pythonnuketools import OverpressureRingCalculator
from glasstone.overpressure import brode_overpressure
from scipy import optimize

#Main Loop
if len(sys.argv) != 3:
    raise ValueError('Please provide a yield (in kilotons) and the altitude of detonation')

oc = OverpressureRingCalculator()

ops = oc.GetOverpressureRadii(float(sys.argv[1]), float(sys.argv[2]), [20,5,2,1])

print(ops)

print(optimize.fixed_point(lambda r: brode_overpressure(750, r, 2000, opunits='psi'), 5.0))
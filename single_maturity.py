''' Single maturity support function arbitrage test.

This script implements the single maturity Davis-Hobson (2007) 
conditions used in my MSc dissertation.

Required input columns:
    k : normalised strike
    r : normalised call price

'''

import cvxpy as cp
import numpy as np
import pandas as pd

# Import the normalised strike and call price data.
# The data includes the artificial zero strike point (0,1).
df = pd.read_csv("single_maturity_data.csv")

# Create a NumPy array for the k and r values.
k = np.array(df['k'], dtype=float)
r = np.array(df['r'], dtype=float)

# Sort the observations by increasing k values.
order = np.argsort(k)
k = k[order]
r = r[order]

# Calculate the number of strikes. 
n = len(k)

''' Here we construct the greatest decreasing support function
using the CVXPY formulation. R[i] represents R_i discussed in 
Section 7.2.1 of the dissertaion. The solver stores a NumPy 
array of the k and r values used to construct the support function it finds. 
'''

# Define the unknown support function values to be found with
# n optimisation variables.
R = cp.Variable(n)

# Create constraints for the support function.
constraints = []
constraints += [R <= r] # Below observed prices.
constraints += [R >=0] # Non-negativity.
constraints += [R[0] == 1] # Artificial zero strike point.

# Monotonicity.
for i in range(n-1):
    constraints += [R[i+1] <=  R[i]]

# Convexity, successive slopes must be non-decreasing.
for i in range(n-2):
    slope_left = ((R[i+1] - R[i]) / (k[i+1] - k[i]))
    slope_right = ((R[i+2] - R[i+1]) / (k[i+2] - k[i+1]))

    constraints += [slope_left <= slope_right]


# Create the objective function to find the greatest
# decreasing convex function as outlined in Section 7.2.1.    
objective = cp.Maximize(cp.sum(R))

# Combine the objective and constraints to form 
# the optimisation problem and slove it.
prob = cp.Problem(objective, constraints)
prob.solve()

# Check whether the solver has found a solution.
print('Status:', prob.status)


''' Next we check the single maturity arbitrage
conditions with the support function just found.
'''

# Store the optimal support function values for each strike obtained.
R_hat =R.value

# Define the numerical tolerance used for comparisons.
tolerance = 1e-8

# 1. Strict decrease condition.
# Find the first strike with a zero call price (with our numerical 
# tolerance included).
zero_index  = np.where(r[1:] <= tolerance)[0]

# If no such point exists we use the last strike.
# The +/- 1 below are solely for python indexing issues.
if len(zero_index) > 0:
    z_0 = zero_index[0] + 1
else:
     z_0 = len(r) -1

strict_decrease = np.all(np.diff(R_hat[:z_0 + 1]) < -tolerance)

# 2. Contact condition: R(k_i) = r_i (with our numerical tolerance included).
contact = np.all(np.abs(R_hat - r) <= tolerance)

# 3. Derivative condition: R'+(0) >= -1 (with our numerical tolerance included).
first_slope = ((R_hat[1] - R_hat[0]) / (k[1] - k[0]))

derivative = first_slope >= -1 - tolerance

''' Arbitrage classification.'''

if contact and derivative and strict_decrease:
    arbitrage_type = 'AOA'

elif contact and derivative and (r[-1] > tolerance) and not strict_decrease:
    arbitrage_type = 'Weak arbitrage'

else:
    arbitrage_type = 'MIA'


# Output results.
print("Contact condition:", contact)
print("Derivative condition:", derivative)
print("Strict decrease condition:", strict_decrease)
print("Classification:", arbitrage_type)

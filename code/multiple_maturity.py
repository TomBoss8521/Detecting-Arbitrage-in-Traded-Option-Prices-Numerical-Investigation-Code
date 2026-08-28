''' Multiple-maturity support function arbitrage test.

This script implements the multiple-maturity Davis-Hobson (2007) 
conditions used in my MSc dissertation. For each maturity T_j, 
the support function is constructed using observations from
T_j and all later maturities.

Required input columns:
    maturity : option maturity dates
    k : normalised strike
    r : normalised call price

'''


import cvxpy as cp
import numpy as np
import pandas as pd

# Import the combined normalised strike and call price data.
# The data includes the artificial zero strike point (0,1)
# for each maturity.
df = pd.read_csv("multiple_maturity_data.csv")
df['maturity'] = pd.to_datetime(df['maturity'])


# Create a function to make the support function and
# check the theorem conditions.
def multiple_maturity_support_func(df):

    # Extract all distinc maturity dates and arrange them in increasing order. 
    maturities = np.sort(df['maturity'].unique())

    # Set the numerical tolerance used for comparisons.
    tolerance = 1e-8

    # List to store the results for each time we run thorugh the solver and checker.
    results = []

    ''' Loop through each maturity T_j in chronological order as we have to make sure
    each support function consisitng of the maturities T_j onwards satisfies the conditions.
    We do this until we have run out of maturities. If we had three maturities labled as T_1, T_2 
    and T_3, then this would run three times using the joint sets of (T_1,T_2,T_3), (T_2,T_3)
    and finally (T_3).
    '''

    for maturity in maturities:

        # Select the observations belonging to the current maturity T_j
        # together with every maturity occurring after T_j. 
        future_df = df[df['maturity'] >= maturity].copy()

        # Extract all normalised strikes and prices from the current and 
        # later maturities.
        k_all = np.array(future_df['k'], dtype=float)
        r_all = np.array(future_df['r'], dtype=float)


        # Sort observations by increasing k values.
        order = np.argsort(k_all)
        k_all = k_all[order]
        r_all = r_all[order]

        # Extract the distinct normalised strike values appearing in the 
        # joint dataset.
        k = np.unique(k_all)
        
        # At a repeated strike, the support function must lie below every observed price.
        # Therefore, the smallest observed price at that strike provides the bound.
        r = np.array([np.min(r_all[np.isclose(k_all, x, atol=1e-10, rtol=1e-10)]) for x in k])

        # Calculate the number of distinct strikes in the joint strike grid
        n = len(k)


        ''' Here we construct the greatest decreasing support function 
        using the CVXPY formulation. R[i] represents R_i discussed in 
        Section 7.2.1. The solver stores a NumPy array of the k and r values used
        to construct the support function it finds. '''

        # Define the unknown support function values to be found with
        # n optimisation variables.
        R = cp.Variable(n)


        # Create constraints for the support function.
        constraints = []

        constraints += [R <= r] # Below observed prices.
        constraints += [R >= 0] # Non-negativity.
        constraints += [R[0] == 1] # Artificial zero strike point.


        # Monotonicity
        for j in range(n-1):
            constraints += [R[j+1] <=  R[j]]


        # Convexity, successive slopes must be non-decreasing.
        for j in range(n-2):
            slope_left = ((R[j+1] - R[j]) / (k[j+1] - k[j]))
            slope_right = ((R[j+2] - R[j+1]) / (k[j+2] - k[j+1]))

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

        ''' Next we check the multiple-maturity arbitrage
        conditions with the support function just found.'''


        # Store the optimal support function values for each strike obtained.
        R_hat = R.value


        # Select only the observations belonging to the current maturity T_j.
        current_df = df[df['maturity'] == maturity].copy()

         # Order the current maturity observations by increasing strike.
        current_df = current_df.sort_values('k')

         # Extract the current T_j maturity's normalised strikes and prices.
        k_current = np.array(current_df['k'], dtype=float)
        r_current = np.array(current_df['r'], dtype=float)

        # Create an empty list for support function values at the current maturity strikes.
        R_current = []

        # Loop through each current maturity strike.
        for x in k_current:

            # Find the location of the current strike x in the joint support function grid.
            index = np.where(np.isclose(k, x, atol=1e-12, rtol=1e-12))[0]

            # Store the corresponding optimal support function value.
            R_current.append(R_hat[index[0]])

        # Convert the collected support function values into a NumPy array.
        R_current = np.array(R_current)


        # 1. Strict decrease condition.
        # Find the first strike with a zero call price.
        # Search the current maturity for the first strike value whose normalised
        # price is zero (with our numerical tolerance included).
        zero_index = np.where(r_current[1:] <= tolerance)[0]

        # Check whether such a zero price exists, if so record the strike of the
        # first zero priced current maturity option.
        if len(zero_index) > 0:
            z_0 = zero_index[0] + 1
            last_k = k_current[z_0]

        # If no zero price occurs, use the last strike value.    
        else:
            last_k = k_current[-1]

        # Find all points of the joint support function grid up to the relevant current maturity.
        relevant = k <= last_k

        # Extract the support function values over this relevant interval.
        R_rel = R_hat[relevant]

        # Check that the support function is strictly decreasing over the required interval
        #(with our numerical tolerance included).
        strict_decrease = np.all(np.diff(R_rel) < -tolerance)

        # 2. Contact condition: R(k_i) = r_i (with our numerical tolerance included).
        contact = np.all(np.abs(R_current - r_current) <= tolerance)


        # 3. Derivative condition: R'+(0) >= -1 (with our numerical tolerance included).
        first_slope = ((R_hat[1] - R_hat[0]) / (k[1] - k[0]))

        derivative = first_slope >= -1 - tolerance

        
        ''' Arbitrage classification.'''
        
        if contact and derivative and strict_decrease:
            arb_type = 'AOA'

        elif contact and derivative and (r_current[-1] > tolerance) and not strict_decrease:
            arb_type = 'weak arbitrage'

        else:
            arb_type = 'MIA'

        # Additional code if you want to see the maximum contact error bewteen the support
        # function and current maturity points.
        # max_contact_error = np.max(np.abs(R_current - r_current))
        
        # Store the theorem conditions for the curent maturity T_j.
        # Note that each row refers to the joint dataset consisting of T_j
        # together with all later maturities.
        results.append({
        'Starting Maturity': maturity,
        'Contact': contact,
        'Derivative': derivative,
        'Strict decrease': strict_decrease,
        'Arbitrage type': arb_type,
        # 'Max contact error': max_contact_error 
        })

    # Convert the list of results into a pandas table.
    results_df = pd.DataFrame(results)

    # Return the completed results table.
    return results_df

# Apply the multiple-maturity test to the original market data we imported.
results = multiple_maturity_support_func(df)

# Dsiplay the classification results
print(results)


'''Optional perturbation experiment used in Section 7.3.2 . Remove
docstring to use.
'''


'''
# Create a copy of the original data so that the market observations remain unchanged.
df_test = df.copy()

# Extract and sort the distinct maturity dates.
maturities = np.sort(df_test["maturity"].unique())

# Select the final maturity, which is September 2027 in the empirical example.
september = maturities[-1]

# Define the observations to be perturbed:
# only positive strike options belonging to the final maturity are selected.
# This excludes the artificial zero strike point as it would automatically fail
# the conditions if we perturb this.
condition = (
    (df_test["maturity"] == september)
     & (df_test["k"] > 0)
 )

# Reduce each selected September normalised option price by 1%.
# The artificial zero strike point (0,1) is therefore left unchanged.
df_test.loc[condition, "r"] *= 0.99

# Apply the multiple-maturity theorem test to the perturbed dataset.
perturbed_results = multiple_maturity_support_func(df_test)

# Display the resulting classifications after perturbation.
print(perturbed_results)
'''

# Detecting-Arbitrage-in-Traded-Option-Prices-Numerical-Investigation-Code

This repository contains the Python implementation used in my MSc Dissertation "Detecting Arbitrage in Traded Option Prices: A Theoretical and Numerical Investigation Into European Option Prices".

The code implements both the single-maturity and multiple-maturity support function tests based on conditions developed by Davis and Hobson (2007) [2].

##  Files
- `single_maturity.py` – constructs the single-maturity support function and checks the contact, derivative and strict decrease conditions.
- `multiple_maturity.py` - extends the procedure to the current and all later maturities and performs the corresponding joint consistency tests for the multiple-maturity case.

## Test Data
We provide a folder of artificial test data to see how the different cases run and are classified.

## Requirements
- Python 3
- CVXPY [1,3]  
- NumPy
- Pandas

## Variables and Inputs
The single-maturity script requires the columns `k` and `r`, representing the normalised strike price and normalised option price respectively. The zero strike and price must also be included.
The multiple-maturity script requires the columns `Maturity`, `k` and `r` where each maturity is expected to have the zero strike and price included.

## References
[1] Agrawal, A., Verschueren, R., Diamond, S. and Boyd, S.,
‘A rewriting system for convex optimization problems’, *Journal of Control and Decision*. 5 (2018), 1, 42-60, doi:
10.1080/23307706.2017.1397554.

[2] Davis, M.H.A. and Hobson, D.G., ‘The range of traded option prices’, *Mathematical Finance*. 17 (2007), 1, 1-14, doi:
10.1111/j.1467-9965.2007.00291.x.

[3] Diamond, S. and Boyd, S., ‘CVXPY: A Python-embedded modelling language for convex optimization’, *Journal of Machine
Learning Research*. 17 (2016), 83, 1-15.

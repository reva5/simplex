import numpy as np
from fractions import Fraction

def adjust_for_minimize():
    global optimal
    optimal = optimal * -1

def adjust_for_non_positivity(i):
    def replace():
        global variables
        variables[i] = variables[i] * -1
    return replace

def adjust_for_unbounded(i):
    def replace():
        global variables
        variables[i] -= variables[i + 1]
        del variables[i + 1]
    return replace

def simplex(canon_tab, **kwargs):
    rows_num, cols_num = np.shape(canon_tab)

    optimal = 0
    variables = [0] * (cols_num - 2)

    if 'basic' in kwargs:
        basic = kwargs['basic']
    else:
        basic = {i: j for i, j in zip(range(1, rows_num), range(cols_num - 1 - (rows_num - 1), cols_num - 1))}

    while canon_tab[0][pivot_col_i := min(range(1, cols_num - 1), key=lambda i: canon_tab[0][i])] < 0:
        pivot_col = canon_tab.T[pivot_col_i]

        try: 
            pivot_row_i = min([i for i in range(1, len(pivot_col)) if pivot_col[i] > 0], key=lambda i: canon_tab.T[-1][i] / pivot_col[i])
        except ValueError:
            print("Problem is unbounded/has no solution")
            exit()

        pivot_row = canon_tab[pivot_row_i]

        pivot = canon_tab[pivot_row_i][pivot_col_i]
        canon_tab[pivot_row_i] /= pivot
        for i in range(len(canon_tab)):
            if i == pivot_row_i:
                continue

            canon_tab[i] = canon_tab[i] - canon_tab[i][pivot_col_i] * canon_tab[pivot_row_i]

        basic[pivot_row_i] = pivot_col_i

    optimal = float(canon_tab[0][-1])
    for k, v in basic.items():
        variables[v - 1] = float(canon_tab.T[-1][k])

    return optimal, variables, basic

corrections = []

constraints_num = int(input("Enter number of constraints: "))
variables_num = int(input("Enter number of variables: "))
print()

print("Enter coefficients for objective function:\n")
obj_coeff = []
for i in range(variables_num):
    obj_coeff.append(Fraction(input(f"Coefficient for variable {i + 1}: ")))

maximize = bool(int(input("Maximize objective function? (1 if yes, 0 otherwise): ")))
if not maximize:
    for i in range(variables_num):
        obj_coeff[i] = obj_coeff[i] * -1
    corrections.append(adjust_for_minimize)
print()

b_values = []
slack_coeff = []
artificial_coeff = []
constraints_coeff = []
for i in range(constraints_num):
    print(f"Constraint {i + 1}:\n")
    constraint_coeff = []
    for j in range(variables_num):
        constraint_coeff.append(Fraction(input(f"Coefficient for variable {j + 1}: ")))

    b_value = Fraction(input("b-value for constraint: "))

    type = int(input("Type of constraint (0 for <=; 1 for >=; 2 for =): "))
    if b_value < 0:
        b_value = b_value * -1
        constraint_coeff = [coeff * -1 for coeff in constraint_coeff]
        if type in [0, 1]:
            type = (type + 1) % 2

    constraints_coeff.append(constraint_coeff)
    b_values.append([b_value])

    match type:
        case 0:
            slack_coeff.append([[1] if i == j else [0] for j in range(constraints_num)])
        case 1:
            slack_coeff.append([[-1] if i == j else [0] for j in range(constraints_num)])
            artificial_coeff.append([[1] if i == j else [0] for j in range(constraints_num)])
        case 2:
            artificial_coeff.append([[1] if i == j else [0] for j in range(constraints_num)])

    print()

i = 0
while i < len(obj_coeff):
    type = int(input(f"Is variable {i + 1} positive (0), negative (1), or unbounded (2)? "))
    match type:
        case 1:
            for j in range(len(constraints_coeff)):
                constraint = constraints_coeff[j]
                constraint[i] = constraint[i] * -1
            obj_coeff[i] = obj_coeff[i] * -1
            corrections.append(adjust_for_non_positivity(i))
        case 2:
            for j in range(len(constraints_coeff)):
                constraint = constraints_coeff[j]
                constraint.insert(i + 1, constraint[i] * -1)
            obj_coeff.insert(i + 1, obj_coeff[i] * -1)
            i += 1
            corrections.append(adjust_for_unbounded(i))
    i += 1
print()

for i in range(len(slack_coeff)):
    obj_coeff.append(0)
    constraints_coeff = np.concatenate((constraints_coeff, slack_coeff[i]), 1)

for i in range(len(artificial_coeff)):
    constraints_coeff = np.concatenate((constraints_coeff, artificial_coeff[i]), 1)

##########
# PHASE I
##########

canon_tab = [[1] + [0] * len(obj_coeff) + [1] * len(artificial_coeff) + [0]]
for i in range(len(constraints_coeff)):
    canon_tab.append([0] + list(constraints_coeff[i]) + b_values[i])
canon_tab = np.array(canon_tab, dtype=object)

p1_basic = {}
if len(artificial_coeff) != 0:
    for i in range(-1, -1 - len(artificial_coeff), -1):
        canon_tab[0] -= canon_tab[i]

    optimal, variables, p1_basic = simplex(canon_tab)
    if optimal != 0:
        print("No basic feasible solution")
        exit()

###########
# PHASE II
###########

to_delete = []

for i in range(1, 1 + len(obj_coeff)):
    if canon_tab[0][i] > 0:
        to_delete.append(i)

for i in range(len(obj_coeff) + 1, len(obj_coeff) + 1 + len(artificial_coeff)):
    if i not in p1_basic.values():
        to_delete.append(i)

canon_tab[0] = [1] + [coeff * -1 for coeff in obj_coeff] + [0] * len(artificial_coeff) + [0]
canon_tab[:, to_delete] = 0

if p1_basic:
    optimal, variables, _ = simplex(canon_tab, basic=p1_basic)
else:
    optimal, variables, _ = simplex(canon_tab)

variables = variables[:len(obj_coeff)]

for correction in corrections:
    correction()

print(optimal)
print(variables)

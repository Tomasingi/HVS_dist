#!python -m pip install -i https://pypi.gurobi.com gurobipy[matrixapi]
from gurobipy import *

import sys
from innlestur_2 import lesa_gogn
from error_handler import errorHandler
from model_generator import generate_model
from excel_generator import generate_excel
from solutionCheck import solutionCheck, printSolutionCheck

def rada(in_dir, out_dir='out', skraningar='skraningar.xlsx', mrs='mrs_stadlad.xlsx', auka_upplysingar='auka_upplysingar.xlsx'):
    try:
        M = lesa_gogn(in_dir, skraningar, mrs, auka_upplysingar)
    except Exception as err:
        errorHandler(err)
        return

    likan, x = generate_model(M)
    likan.optimize()

    if likan.Status != 2:
        # do something if model could not be solved (infeasible, unbounded, etc.)
        print('módel ekki bestað')
        pass


    year = 2022 # í öðrum skrám er þetta lesið úr skrá, er ekki betri leið til að fá þetta??

    try:
        generate_excel(M, x, year, out_dir)
    except:
        # handle errors from generating excel files
        print('villa við að búa til excel skjöl')
        pass

    try:
        result = solutionCheck(x, M)
        printSolutionCheck(result, verbose=False)
    except:
        # handle errors from checking the solution
        print('villa við að athuga lausn')
        pass


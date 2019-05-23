#  ___________________________________________________________________________
#
#  EGRET: Electrical Grid Research and Engineering Tools
#  Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
#  (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
#  Government retains certain rights in this software.
#  This software is distributed under the Revised BSD License.
#  ___________________________________________________________________________

'''
acopf tester
'''
import os
import math
import unittest
from pyomo.opt import SolverFactory, TerminationCondition
from egret.models.acopf import *
from egret.data.model_data import ModelData
from parameterized import parameterized
from egret.parsers.matpower_parser import create_ModelData

current_dir = os.path.dirname(os.path.abspath(__file__))
case_names = ['pglib_opf_case3_lmbd','pglib_opf_case30_ieee','pglib_opf_case300_ieee']#,'pglib_opf_case3012wp_k','pglib_opf_case13659_pegase']
test_cases = [os.path.join(current_dir, 'transmission_test_instances', 'pglib-opf-master', '{}.m'.format(i)) for i in case_names]
soln_cases = [os.path.join(current_dir, 'transmission_test_instances', 'acopf_solution_files', '{}_acopf_solution.json'.format(i)) for i in case_names]


class TestPSVACOPF(unittest.TestCase):
    show_output = True

    @classmethod
    def setUpClass(self):
        download_dir = os.path.join(current_dir, 'transmission_test_instances')
        if not os.path.exists(os.path.join(download_dir, 'pglib-opf-master')):
            from egret.thirdparty.get_pglib import get_pglib
            get_pglib(download_dir)

    @parameterized.expand(zip(test_cases, soln_cases))
    def test_acopf_model(self, test_case, soln_case):
        acopf_model = create_psv_acopf_model

        md_soln = ModelData()
        md_soln.read_from_json(soln_case)

        md_dict = create_ModelData(test_case)

        md, results = solve_acopf(md_dict, "ipopt", acopf_model_generator=acopf_model, solver_tee=False, return_results=True)

        self.assertTrue(results.solver.termination_condition == TerminationCondition.optimal)
        comparison = math.isclose(md.data['system']['total_cost'], md_soln.data['system']['total_cost'], rel_tol=1e-4)
        self.assertTrue(comparison)


class TestRSVACOPF(unittest.TestCase):
    show_output = True

    @classmethod
    def setUpClass(self):
        download_dir = os.path.join(current_dir, 'transmission_test_instances')
        if not os.path.exists(os.path.join(download_dir, 'pglib-opf-master')):
            from egret.thirdparty.get_pglib import get_pglib
            get_pglib(download_dir)

    @parameterized.expand(zip(test_cases, soln_cases))
    def test_acopf_model(self, test_case, soln_case):
        acopf_model = create_rsv_acopf_model

        md_soln = ModelData()
        md_soln.read_from_json(soln_case)

        md_dict = create_ModelData(test_case)

        md, results = solve_acopf(md_dict, "ipopt", acopf_model_generator=acopf_model, solver_tee=False, return_results=True)

        self.assertTrue(results.solver.termination_condition == TerminationCondition.optimal)
        comparison = math.isclose(md.data['system']['total_cost'], md_soln.data['system']['total_cost'], rel_tol=1e-4)
        self.assertTrue(comparison)


class TestRIVACOPF(unittest.TestCase):
    show_output = True

    @classmethod
    def setUpClass(self):
        download_dir = os.path.join(current_dir, 'transmission_test_instances')
        if not os.path.exists(os.path.join(download_dir, 'pglib-opf-master')):
            from egret.thirdparty.get_pglib import get_pglib
            get_pglib(download_dir)

    @parameterized.expand(zip(test_cases, soln_cases))
    def test_acopf_model(self, test_case, soln_case):
        acopf_model = create_riv_acopf_model

        md_soln = ModelData()
        md_soln.read_from_json(soln_case)

        md_dict = create_ModelData(test_case)

        md, results = solve_acopf(md_dict, "ipopt", acopf_model_generator=acopf_model, solver_tee=False, return_results=True)

        self.assertTrue(results.solver.termination_condition == TerminationCondition.optimal)
        comparison = math.isclose(md.data['system']['total_cost'], md_soln.data['system']['total_cost'], rel_tol=1e-4)
        self.assertTrue(comparison)


if __name__ == '__main__':
    unittest.main()

"""Accelerate the frozen solver's CG pressure systems with a fixed multigrid hierarchy."""

import numpy as np
import pyamg
from scipy.sparse.linalg import cg


def attach(solver):
    jacobi = solver._jacobi_cg
    preconditioner = None

    def solve(matrix, rhs, tol=1e-7, maxiter=3000, x0=None):
        nonlocal preconditioner
        norm = float(np.linalg.norm(rhs))
        if norm < 1e-30:
            return np.zeros_like(rhs), 0, 0.0
        if preconditioner is None:
            hierarchy = pyamg.ruge_stuben_solver(matrix, max_coarse=40)
            preconditioner = hierarchy.aspreconditioner(cycle="V")
        solution, info = cg(matrix, rhs, x0=x0, rtol=tol, atol=0.0, maxiter=min(maxiter, 200), M=preconditioner)
        residual = float(np.linalg.norm(matrix @ solution - rhs)) / norm
        if info != 0 or residual > tol:
            return jacobi(matrix, rhs, tol, maxiter, x0)
        return solution, int(info), residual

    solver._jacobi_cg = solve

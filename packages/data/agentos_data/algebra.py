import numpy as np
from scipy import interpolate, linalg


def linear_regression(x: np.ndarray, y: np.ndarray) -> dict:
    A = np.column_stack([x, np.ones_like(x)])
    coeffs, residuals, _, _ = np.linalg.lstsq(A, y, rcond=None)
    return {"slope": float(coeffs[0]), "intercept": float(coeffs[1])}


def interpolate_1d(
    x: np.ndarray, y: np.ndarray, x_new: np.ndarray, kind: str = "linear"
) -> np.ndarray:
    f = interpolate.interp1d(x, y, kind=kind, fill_value="extrapolate")
    return f(x_new)


def svd(matrix: np.ndarray) -> dict:
    U, s, Vt = linalg.svd(matrix, full_matrices=False)
    return {"U": U, "singular_values": s, "Vt": Vt}


def solve_linear_system(A: np.ndarray, b: np.ndarray) -> np.ndarray:
    return linalg.solve(A, b)


def pca_reduce(data: np.ndarray, n_components: int = 2) -> np.ndarray:
    centered = data - data.mean(axis=0)
    _, _, Vt = linalg.svd(centered, full_matrices=False)
    return centered @ Vt[:n_components].T

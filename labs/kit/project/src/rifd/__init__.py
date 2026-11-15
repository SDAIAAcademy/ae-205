"""Rifd Mutual Insurance claims services (lab project of the SDAIA Academy course AE-205)."""

import os

# One request is one row: let each worker predict on one thread. scikit-learn's gradient boosting
# otherwise starts an OpenMP thread per core for every prediction, and on a busy machine a single
# prediction can take seconds. Scale with workers and replicas instead (lab 3.4).
os.environ.setdefault("OMP_NUM_THREADS", "1")

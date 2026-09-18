"""Secondary air: the rotating side of the cooling supply.

Separate from `solvers/thermal`, which owns the stationary network (D3's
budget, D7's stage-1 nozzle), because this is where rotation enters --
pumping, relative total pressures, and the backflow margins on a blade
rather than a vane.
"""

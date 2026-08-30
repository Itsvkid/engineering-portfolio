function result = nozzle_exit(station_in, ambient_pressure, efficiency, cp, gamma)
%NOZZLE_EXIT  A convergent nozzle: expands to ambient pressure if it can,
%   chokes (exit Mach 1) if the available pressure ratio exceeds the
%   critical value for this gas. Mirrors
%   projects/08-cycle-model/src/components.py:nozzle_exit exactly,
%   including the convergent-only Mach-1 cap. This is NOT project 08's
%   convergent-divergent nozzle (cd_nozzle_exit, an opt-in extension) --
%   it matches the DEFAULT solve_cycle() path, which is what the
%   reference-design numbers in project 08's README were generated from,
%   so it's the right thing to compare a first Simulink cross-check
%   against.
%
%   result = [T_exit, p_exit, velocity, choked(0/1)]
R = cp * (1 - 1/gamma);
exponent = (gamma - 1) / gamma;
critical_pressure_ratio = ((gamma + 1) / 2) ^ (1 / exponent);
available_pressure_ratio = station_in(2) / ambient_pressure;

if available_pressure_ratio < critical_pressure_ratio
    exit_station = expand_to_pressure(station_in, ambient_pressure, efficiency, cp, gamma);
    velocity = sqrt(2 * cp * (station_in(1) - exit_station(1)));
    result = [exit_station(1), exit_station(2), velocity, 0];
else
    t_exit = station_in(1) * 2 / (gamma + 1);
    velocity = sqrt(gamma * R * t_exit);
    specific_work_required = cp * (station_in(1) - t_exit);
    matched = expand_for_work(station_in, specific_work_required, efficiency, cp, gamma);
    result = [t_exit, matched(2), velocity, 1];
end
end

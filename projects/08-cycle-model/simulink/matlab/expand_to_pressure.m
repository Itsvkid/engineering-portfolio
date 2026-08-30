function station_out = expand_to_pressure(station_in, exit_pressure, efficiency, cp, gamma)
%EXPAND_TO_PRESSURE  Expand to a known exit pressure -- the unchoked-
%   nozzle problem, and the general turbine relation with pressure ratio
%   given rather than required work. Actual delta-T is efficiency times
%   the ideal delta-T: an imperfect expansion recovers less of the
%   available drop. Mirrors
%   projects/08-cycle-model/src/components.py:expand_to_pressure.
exponent = (gamma - 1) / gamma;
ideal_ratio = (exit_pressure / station_in(2)) ^ exponent;
delta_t_ideal = station_in(1) * (1 - ideal_ratio);
delta_t_actual = efficiency * delta_t_ideal;
station_out = [station_in(1) - delta_t_actual, exit_pressure];
end

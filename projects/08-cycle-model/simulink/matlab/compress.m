function station_out = compress(station_in, pressure_ratio, efficiency, cp, gamma)
%COMPRESS  A compressor or fan stage. Mirrors
%   projects/08-cycle-model/src/components.py:compress -- the ideal
%   delta-T is divided by efficiency (an imperfect machine needs MORE
%   temperature rise for the same pressure ratio, not less).
%   station_in / station_out are [T, p] row vectors (stagnation K, Pa).
exponent = (gamma - 1) / gamma;
ideal_ratio = pressure_ratio ^ exponent;
delta_t_ideal = station_in(1) * (ideal_ratio - 1);
delta_t_actual = delta_t_ideal / efficiency;
station_out = [station_in(1) + delta_t_actual, station_in(2) * pressure_ratio];
end

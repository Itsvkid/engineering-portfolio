function [station_out, f] = combust(station_in, exit_temperature, lhv, efficiency, pressure_loss_fraction, cp_cold, cp_hot)
%COMBUST  Heat addition to a specified turbine-entry temperature -- TET
%   is the design input here, not an output. Solves the fuel-air ratio
%   f = mdot_fuel/mdot_air from the energy balance
%
%       mdot_air*cp_cold*T_in + mdot_fuel*LHV*eta = (mdot_air+mdot_fuel)*cp_hot*T_exit
%
%   Pressure drops by pressure_loss_fraction regardless of f. Mirrors
%   projects/08-cycle-model/src/components.py:combust.
numerator = cp_hot * exit_temperature - cp_cold * station_in(1);
denominator = efficiency * lhv - cp_hot * exit_temperature;
f = numerator / denominator;
station_out = [exit_temperature, station_in(2) * (1 - pressure_loss_fraction)];
end

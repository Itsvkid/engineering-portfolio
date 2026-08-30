function station_out = expand_for_work(station_in, specific_work_required, efficiency, cp, gamma)
%EXPAND_FOR_WORK  A turbine stage sized to deliver exactly
%   specific_work_required (J/kg) -- the work-matching problem every
%   turbine in this cycle actually solves, since its pressure ratio is
%   not a free choice, it is whatever drop produces the power the
%   compressor on its shaft demands. Also reused, unmodified, for a
%   choked nozzle's pressure. Mirrors
%   projects/08-cycle-model/src/components.py:expand_for_work.
exponent = (gamma - 1) / gamma;
delta_t_actual = specific_work_required / cp;
delta_t_ideal = delta_t_actual / efficiency;
t_exit_ideal = station_in(1) - delta_t_ideal;
pressure_ratio = (station_in(1) / t_exit_ideal) ^ (1 / exponent);
station_out = [station_in(1) - delta_t_actual, station_in(2) / pressure_ratio];
end

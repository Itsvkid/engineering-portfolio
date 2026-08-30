function test_physics_standalone()
%TEST_PHYSICS_STANDALONE  Run the reference design through the plain
%   MATLAB physics functions directly -- no Simulink involved at all.
%
%   Run this FIRST, before build_turbofan_model. It is the fastest,
%   lowest-risk way to check the ported physics agrees with project 08's
%   Python: if these numbers don't match
%   projects/08-cycle-model/README.md's reference design table, the bug
%   is in compress.m / expand_for_work.m / nozzle_exit.m / etc., not in
%   any Simulink wiring -- fix it here first, since build_turbofan_model
%   calls these exact same functions from inside its blocks.
here = fileparts(mfilename('fullpath'));
addpath(here);

% Reference design point -- see TurbofanDesignPoint in
% projects/08-cycle-model/src/cycle.py.
altitude = 10668.0; mach = 0.78;
core_mass_flow = 40.0; bypass_ratio = 6.0;
fan_pr = 1.6; booster_pr = 1.6; hpc_pr = 14.0;
tet = 1650.0;

intake_recovery = 0.98;
fan_eff = 0.90; booster_eff = 0.88; hpc_eff = 0.87;
combustor_eff = 0.99; hpt_eff = 0.90; lpt_eff = 0.91;
mech_eff = 0.995; core_nozzle_eff = 0.98; bypass_nozzle_eff = 0.98;
combustor_ploss = 0.04; bypass_duct_ploss = 0.01;
fuel_lhv = 43.0e6;

[cp_cold, gamma_cold] = gas_properties('air');
[cp_hot, gamma_hot] = gas_properties('combustion');

% ---- Intake: freestream to fan face stagnation conditions ----
[t_static, p_static] = isa_atmosphere(altitude);
sound_speed = sqrt(gamma_cold * (cp_cold * (1 - 1/gamma_cold)) * t_static);
v0 = mach * sound_speed;
t0 = t_static * (1 + 0.5 * (gamma_cold - 1) * mach^2);
p0 = p_static * (t0 / t_static) ^ (gamma_cold / (gamma_cold - 1));
fan_face = [t0, p0 * intake_recovery];

% ---- Core and bypass compression ----
fan_exit = compress(fan_face, fan_pr, fan_eff, cp_cold, gamma_cold);
bypass_nozzle_inlet = [fan_exit(1), fan_exit(2) * (1 - bypass_duct_ploss)];
booster_exit = compress(fan_exit, booster_pr, booster_eff, cp_cold, gamma_cold);
hpc_exit = compress(booster_exit, hpc_pr, hpc_eff, cp_cold, gamma_cold);

% ---- Combustor: TET is the input, fuel-air ratio is solved ----
[combustor_exit, f] = combust(hpc_exit, tet, fuel_lhv, combustor_eff, ...
    combustor_ploss, cp_cold, cp_hot);
turbine_mass_flow = core_mass_flow * (1 + f);

% ---- HPT work-matched to the HPC it drives ----
hpc_power = core_mass_flow * cp_cold * (hpc_exit(1) - booster_exit(1));
hpt_work_required = (hpc_power / mech_eff) / turbine_mass_flow;
hpt_exit = expand_for_work(combustor_exit, hpt_work_required, hpt_eff, cp_hot, gamma_hot);

% ---- LPT work-matched to the fan + booster it drives ----
total_fan_mass_flow = core_mass_flow * (1 + bypass_ratio);
fan_power = total_fan_mass_flow * cp_cold * (fan_exit(1) - fan_face(1));
booster_power = core_mass_flow * cp_cold * (booster_exit(1) - fan_exit(1));
lpt_work_required = ((fan_power + booster_power) / mech_eff) / turbine_mass_flow;
lpt_exit = expand_for_work(hpt_exit, lpt_work_required, lpt_eff, cp_hot, gamma_hot);

% ---- Both nozzles ----
core_result = nozzle_exit(lpt_exit, p_static, core_nozzle_eff, cp_hot, gamma_hot);
bypass_result = nozzle_exit(bypass_nozzle_inlet, p_static, bypass_nozzle_eff, cp_cold, gamma_cold);

% ---- Thrust and efficiency ----
bypass_mass_flow = core_mass_flow * bypass_ratio;
total_intake_mass_flow = core_mass_flow + bypass_mass_flow;
fuel_mass_flow = core_mass_flow * f;

core_gross = turbine_mass_flow * core_result(3);
if core_result(4) > 0.5
    r_hot = cp_hot * (1 - 1/gamma_hot);
    core_density = core_result(2) / (r_hot * core_result(1));
    core_area = turbine_mass_flow / (core_density * core_result(3));
    core_gross = core_gross + core_area * (core_result(2) - p_static);
end

bypass_gross = bypass_mass_flow * bypass_result(3);
if bypass_result(4) > 0.5
    r_cold = cp_cold * (1 - 1/gamma_cold);
    bypass_density = bypass_result(2) / (r_cold * bypass_result(1));
    bypass_area = bypass_mass_flow / (bypass_density * bypass_result(3));
    bypass_gross = bypass_gross + bypass_area * (bypass_result(2) - p_static);
end

ram_drag = total_intake_mass_flow * v0;
net_thrust = core_gross + bypass_gross - ram_drag;
tsfc_g_per_kns = (fuel_mass_flow / net_thrust) * 1.0e6;

core_eff_v = core_gross / turbine_mass_flow;
if bypass_mass_flow == 0
    bypass_eff_v = 0;
else
    bypass_eff_v = bypass_gross / bypass_mass_flow;
end
jet_kinetic_power = 0.5 * turbine_mass_flow * core_eff_v^2 ...
    + 0.5 * bypass_mass_flow * bypass_eff_v^2 ...
    - 0.5 * total_intake_mass_flow * v0^2;
fuel_heat_rate = fuel_mass_flow * fuel_lhv;
thermal_eff = jet_kinetic_power / fuel_heat_rate;
thrust_power = net_thrust * v0;
propulsive_eff = thrust_power / jet_kinetic_power;
overall_eff = thrust_power / fuel_heat_rate;

% ---- Print, side by side with the Python reference (README.md) ----
fprintf('%-28s%14s%14s\n', 'Quantity', 'MATLAB', 'Python (README)');
fprintf('%-28s%14.2f%14.2f\n', 'Net thrust, kN', net_thrust / 1000, 57.67);
fprintf('%-28s%14.2f%14.2f\n', 'TSFC, g/(kN*s)', tsfc_g_per_kns, 22.07);
fprintf('%-28s%14.1f%14.1f\n', 'Thermal efficiency, %', thermal_eff * 100, 46.7);
fprintf('%-28s%14.1f%14.1f\n', 'Propulsive efficiency, %', propulsive_eff * 100, 52.2);
fprintf('%-28s%14.1f%14.1f\n', 'Overall efficiency, %', overall_eff * 100, 24.4);
fprintf('%-28s%14.2f%14.2f\n', 'Fuel-air ratio, %', f * 100, 3.18);
fprintf('\n');
fprintf('%-28s%14.1f%14.1f\n', 'Core nozzle T, K', core_result(1), 909.1);
fprintf('%-28s%14.1f%14.1f\n', 'Core nozzle p, kPa', core_result(2) / 1000, 88.3);
fprintf('%-28s%14.1f%14.1f\n', 'Core nozzle V, m/s', core_result(3), 613.7);
fprintf('%-28s%14s%14s\n', 'Core nozzle choked', mat2str(core_result(4) > 0.5), 'true');
fprintf('%-28s%14.1f%14.1f\n', 'Bypass nozzle T, K', bypass_result(1), 237.2);
fprintf('%-28s%14.1f%14.1f\n', 'Bypass nozzle p, kPa', bypass_result(2) / 1000, 28.8);
fprintf('%-28s%14.1f%14.1f\n', 'Bypass nozzle V, m/s', bypass_result(3), 308.8);
fprintf('%-28s%14s%14s\n', 'Bypass nozzle choked', mat2str(bypass_result(4) > 0.5), 'true');
end

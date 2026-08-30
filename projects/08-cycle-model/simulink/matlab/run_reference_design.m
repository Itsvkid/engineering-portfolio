function run_reference_design()
%RUN_REFERENCE_DESIGN  Simulate TurbofanCycle08.slx and print a table
%   comparing every number against project 08's published reference
%   design (projects/08-cycle-model/README.md). Run build_turbofan_model
%   first if TurbofanCycle08.slx does not exist yet.
%
%   There is nothing time-varying in this model -- every block is a pure
%   function of its inputs, computed once. StopTime is set short only so
%   the solver takes the minimum number of steps; every row the "To
%   Workspace" block logs is identical, so this reads the last one.
here = fileparts(mfilename('fullpath'));
addpath(here);

mdl = 'TurbofanCycle08';
mdl_file = fullfile(here, [mdl '.slx']);
if ~bdIsLoaded(mdl)
    if exist(mdl_file, 'file') ~= 2
        error('run_reference_design:missing_model', ...
            ['%s.slx not found in %s. Run build_turbofan_model() ' ...
             'first to generate it.'], mdl, here);
    end
    load_system(mdl_file);
end

sim(mdl, 'StopTime', '0.001');

% The To Workspace block writes 'cycle_results' into the base workspace
% during sim(). If your MATLAB/Simulink version instead returns it only
% through a Simulink.SimulationOutput object, use
%   simOut = sim(mdl, 'StopTime', '0.001');
%   data = simOut.get('cycle_results');
% in place of the two lines below.
data = evalin('base', 'cycle_results');
r = data(end, :);

names = {'Net thrust, kN', 'TSFC, g/(kN*s)', 'Thermal efficiency, %', ...
         'Propulsive efficiency, %', 'Overall efficiency, %', ...
         'Fuel-air ratio, %', 'Core gross thrust, kN', 'Bypass gross thrust, kN'};
published = [57.67, 22.07, 46.7, 52.2, 24.4, 3.18, NaN, NaN];
scale = [1e-3, 1, 1, 1, 1, 1, 1e-3, 1e-3];

fprintf('%-28s%14s%14s\n', 'Quantity', 'Simulink', 'Python (README)');
for i = 1:numel(names)
    val = r(i) * scale(i);
    if isnan(published(i))
        fprintf('%-28s%14.2f%14s\n', names{i}, val, '--');
    else
        fprintf('%-28s%14.2f%14.2f\n', names{i}, val, published(i));
    end
end
end

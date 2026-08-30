function [cp, gamma, R] = gas_properties(name)
%GAS_PROPERTIES  cp (J/(kg*K)), gamma and derived R for the two gases this
%   cycle uses, matching projects/08-cycle-model/src/gas.py exactly: air
%   (cold side) and the combustion-product gas (hot side, after the
%   combustor). R = cp*(1 - 1/gamma), the perfect-gas relation cp - cv = R.
switch name
    case 'air'
        cp = 1005.0;
        gamma = 1.4;
    case 'combustion'
        cp = 1244.0;
        gamma = 1.333;
    otherwise
        error('gas_properties:unknown', 'unknown gas %s', name);
end
R = cp * (1 - 1/gamma);
end

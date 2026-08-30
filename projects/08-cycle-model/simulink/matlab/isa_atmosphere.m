function [T, p] = isa_atmosphere(altitude)
%ISA_ATMOSPHERE  Static temperature (K) and pressure (Pa) at `altitude`
%   (m), troposphere + lower stratosphere, matching
%   projects/08-cycle-model/src/atmosphere.py exactly -- same constants,
%   same two-branch formula. Only valid for altitude >= 0; this port
%   drops the Python version's negative-altitude error() guard, since a
%   MATLAB Function block (if this is called from inside one) rejects
%   exception-raising control flow for code generation -- callers should
%   not pass altitude < 0.
T0 = 288.15;
P0 = 101325.0;
LAPSE = 0.0065;
G0 = 9.80665;
R_AIR = 287.05287;
TROPOPAUSE = 11000.0;
T_STRATOSPHERE = T0 - LAPSE * TROPOPAUSE;

if altitude <= TROPOPAUSE
    T = T0 - LAPSE * altitude;
    p = P0 * (T / T0) ^ (G0 / (LAPSE * R_AIR));
else
    p_tropopause = P0 * (T_STRATOSPHERE / T0) ^ (G0 / (LAPSE * R_AIR));
    T = T_STRATOSPHERE;
    p = p_tropopause * exp(-G0 * (altitude - TROPOPAUSE) / (R_AIR * T_STRATOSPHERE));
end
end

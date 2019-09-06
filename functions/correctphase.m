%
% CORRECTPHASE Phase correction of complex-valued data
%
%   Vc = CORRECTPHASE(V)
%   Performs a phase optimization on the complex-valued data (V) by
%   minimization of the imaginary component of the data. The phase
%   corrected data (Vc) is returned normalized.
%
%   Vc = CORRECTPHASE(V,ph)
%   Corrects the phase of data vector V using user-supplied phase (ph), in
%   radians.
%
%   Vc = CORRECTPHASE(V,ph,true/false)
%   A third boolean argument can be passed to enable/diasable the fitting
%   of a possible offset on the imaginary component of the data. Defaults
%   to false.
%
%   [Vc,ph,io] = CORRECTPHASE(V)
%   Additional output arguments can be requested to return the optimal
%   phase (ph) and imaginary offset (io) employed for the correction.
%
%
% Adapted from Gunnar Jeschke, DeerAnalysis 2018
%
% Copyright(C) 2019  Luis Fabregas, DeerAnalysis2
%
% This program is free software: you can redistribute it and/or modify
% it under the terms of the GNU General Public License 3.0 as published by
% the Free Software Foundation.

function [Vc,Phase,ImagOffset] = correctphase(V,Phase,fitImagOffset)

%--------------------------------------------------------------------------
%Input parsing
%--------------------------------------------------------------------------
switch nargin
    case 0
        help(mfilename);
        return
    case 1
        Phase = [];
        fitImagOffset = false;
        ImagOffset = 0;
    case 2
        fitImagOffset = false;
        ImagOffset = 0;
    case 3
    otherwise
        error('Wrong number of input arguments.');
end

validateattributes(V,{'numeric'},{},mfilename,'PrimaryData')
if ~isempty(Phase)
    validateattributes(Phase,{'numeric'},{'scalar','nonnegative'},mfilename,'Phase')
end
validateattributes(fitImagOffset,{'logical'},{'nonempty'},mfilename,'FittedImaginaryOffset')

if iscolumn(V)
    V = V.';
end

% If phase is not provided, then fit it (and imag. offset)
if isempty(Phase)
    %phi0 = angle(V(end)); % use phase of last point as starting point for fit
    phi0 = mean(angle(V)); % use average phase as starting point for fit
    pars(1) = phi0;
    if fitImagOffset
        pars(2) = 0;
    end
    FitStart = round(length(V)/8); % use only last 7/8 of data for phase/offset correction
    pars = fminsearch(@ImagNorm_PhaseOffset,pars,[],V(FitStart:end));
    Phase = pars(1);
    if fitImagOffset
        ImagOffset = pars(2);
    end
    % Flip phase if necessary to render signal mostly positive
    if sum(real(V*exp(1i*Phase)))<0
        Phase = Phase+pi;
    end
elseif ~isempty(Phase) && fitImagOffset
    offset = 0;
    FitStart = round(length(V)/8); % use only last 7/8 of data for phase/offset correction
    ImagOffset = fminsearch(@(offset)ImagNorm_PhaseOffset([Phase offset],V(FitStart:end)),offset);
end

%Do phase correction and normalize
Vc = (V - 1i*ImagOffset)*exp(1i*Phase);

end

function ImagNorm = ImagNorm_PhaseOffset(params,V)
% Computes norm of the imaginary part of phase-corrected data from zero before
% phase correction, an offset can be subtracted from the imaginary part.
%
% FitParam(1)  phase correction phi (rad)
% FitParam(2)  offset
% V            complex data trace
%
% ImagNorm     norm of imaginary part
%
% G. Jeschke, 2009, Luis Fabregas 2020

phase = params(1);
if numel(params)>1
    imoffset = params(2);
else
    imoffset = 0;
end

if imoffset<0
    ImagNorm = 1e6;
    return
end

ImagComponent = imag((V-1i*imoffset)*exp(1i*phase));
ImagNorm = norm(ImagComponent);

end
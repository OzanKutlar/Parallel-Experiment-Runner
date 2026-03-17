function op = bbob_problems(fid, op)
% BBOB_PROBLEMS  Define BBOB 2009 optimization problem struct.
%
%   op = bbob_problems(fid, dim, iid)
%
%   Inputs:
%     fid  - BBOB function ID (1..24)
%     dim  - problem dimensionality
%     iid  - instance number (1..15)
%
%   Output:
%     op   - struct with fields:
%              dim        : dimensionality
%              bbob_iid   : instance ID
%              bounds     : [lb ub] (same for all dimensions)
%              opt        : global optimum location (1 x dim)
%              opt_known  : true (optimum is known for all BBOB functions)
%              isMin      : true (all BBOB functions are minimization)
%              fun        : function handle f(x), x is (N x dim)

op.bounds   = [-5 5];
op.opt_known = true;
op.isMin    = true;

D = op.dim;

fe = 1e5 * op.dim;
if op.maxFE ~= fe
    warning(strcat("Maximum function evaluation was changed to maxFe=",num2str(fe)," as requirement for this problem."));
    op.maxFE = fe;
end

switch fid

    %% ================================================================
    %  GROUP 1 – Separable functions (f1–f5)
    %% ================================================================

    case 1
        % ------ Sphere -----------------------------------------------
        [xopt, fopt] = bbob_instance(1, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) sum((x - xopt).^2, 2) + fopt;

    case 2
        % ------ Separable Ellipsoidal --------------------------------
        [xopt, fopt] = bbob_instance(2, op.bbob_iid, D);
        op.opt = xopt;
        % z = Tosz(x - xopt),  weights 10^(6*(i-1)/(D-1))
        w = 10 .^ (6 * (0:D-1) / max(D-1,1));   % 1 x D
        op.fun = @(x) sum( w .* Tosz(x - xopt).^2, 2) + fopt;

    case 3
        % ------ Rastrigin (separable) --------------------------------
        [xopt, fopt] = bbob_instance(3, op.bbob_iid, D);
        op.opt = xopt;
        % z = Lambda^10 * Tasy^0.2 * Tosz(x - xopt)
        op.fun = @(x) f_rastrigin_sep(x, xopt, fopt, D);

    case 4
        % ------ Büche-Rastrigin --------------------------------------
        [xopt, fopt] = bbob_instance(4, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_bueche_rastrigin(x, xopt, fopt, D);

    case 5
        % ------ Linear Slope -----------------------------------------
        % xopt is on the boundary: sign drawn, then placed at ±5
        seed = 10000*5 + op.bbob_iid;
        rng(seed, 'twister');
        xopt_sign = sign(-4 + 8*rand(1,D));          % signs only
        xopt_sign(xopt_sign == 0) = 1;
        xopt_bd   = 5 * xopt_sign;                   % boundary point
        fopt = round(100 * tan(pi*(rand-0.5))) / 100;
        fopt = max(-1000, min(1000, fopt));
        op.opt = xopt_bd;
        op.fun = @(x) f_linear_slope(x, xopt_bd, fopt, D);

    %% ================================================================
    %  GROUP 2 – Low / moderate conditioning (f6–f9)
    %% ================================================================

    case 6
        % ------ Attractive Sector ------------------------------------
        [xopt, fopt] = bbob_instance(6, op.bbob_iid, D);
        [Q, R] = bbob_rotations(6, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_attractive_sector(x, xopt, fopt, D, Q, R);

    case 7
        % ------ Step Ellipsoidal -------------------------------------
        [xopt, fopt] = bbob_instance(7, op.bbob_iid, D);
        [Q, R] = bbob_rotations(7, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_step_ellipsoidal(x, xopt, fopt, D, Q, R);

    case 8
        % ------ Rosenbrock (original) --------------------------------
        [xopt, fopt] = bbob_instance(8, op.bbob_iid, D);
        op.opt = xopt;
        % xopt drawn from [-3,3]^D for this function
        op.fun = @(x) f_rosenbrock(x, xopt, fopt, D);

    case 9
        % ------ Rosenbrock (rotated) ---------------------------------
        [xopt, fopt] = bbob_instance(9, op.bbob_iid, D);
        [~, R] = bbob_rotations(9, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_rosenbrock_rotated(x, fopt, D, R);

    %% ================================================================
    %  GROUP 3 – High conditioning, unimodal (f10–f14)
    %% ================================================================

    case 10
        % ------ Ellipsoidal (rotated) --------------------------------
        [xopt, fopt] = bbob_instance(10, op.bbob_iid, D);
        [~, R] = bbob_rotations(10, op.bbob_iid, D);
        op.opt = xopt;
        w = 10 .^ (6 * (0:D-1) / max(D-1,1));
        op.fun = @(x) sum( w .* Tosz(( x - xopt) * R').^2, 2) + fopt;

    case 11
        % ------ Discus -----------------------------------------------
        [xopt, fopt] = bbob_instance(11, op.bbob_iid, D);
        [~, R] = bbob_rotations(11, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_discus(x, xopt, fopt, D, R);

    case 12
        % ------ Bent Cigar -------------------------------------------
        [xopt, fopt] = bbob_instance(12, op.bbob_iid, D);
        [~, R] = bbob_rotations(12, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_bent_cigar(x, xopt, fopt, D, R);

    case 13
        % ------ Sharp Ridge ------------------------------------------
        [xopt, fopt] = bbob_instance(13, op.bbob_iid, D);
        [Q, R] = bbob_rotations(13, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_sharp_ridge(x, xopt, fopt, D, Q, R);

    case 14
        % ------ Different Powers -------------------------------------
        [xopt, fopt] = bbob_instance(14, op.bbob_iid, D);
        [~, R] = bbob_rotations(14, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_different_powers(x, xopt, fopt, D, R);

    %% ================================================================
    %  GROUP 4 – Multimodal, adequate global structure (f15–f19)
    %% ================================================================

    case 15
        % ------ Rastrigin (rotated) ----------------------------------
        [xopt, fopt] = bbob_instance(15, op.bbob_iid, D);
        [Q, R] = bbob_rotations(15, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_rastrigin_rot(x, xopt, fopt, D, Q, R);

    case 16
        % ------ Weierstrass ------------------------------------------
        [xopt, fopt] = bbob_instance(16, op.bbob_iid, D);
        [Q, R] = bbob_rotations(16, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_weierstrass(x, xopt, fopt, D, Q, R);

    case 17
        % ------ Schaffers F7 -----------------------------------------
        [xopt, fopt] = bbob_instance(17, op.bbob_iid, D);
        [Q, R] = bbob_rotations(17, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_schaffers(x, xopt, fopt, D, Q, R, 10);

    case 18
        % ------ Schaffers F7 (ill-conditioned) -----------------------
        [xopt, fopt] = bbob_instance(18, op.bbob_iid, D);
        [Q, R] = bbob_rotations(18, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_schaffers(x, xopt, fopt, D, Q, R, 1000);

    case 19
        % ------ Composite Griewank-Rosenbrock (F8F2) -----------------
        [xopt, fopt] = bbob_instance(19, op.bbob_iid, D);
        [~, R] = bbob_rotations(19, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_griewank_rosenbrock(x, fopt, D, R);

    %% ================================================================
    %  GROUP 5 – Multimodal, weak global structure (f20–f24)
    %% ================================================================

    case 20
        % ------ Schwefel ---------------------------------------------
        [xopt, fopt] = bbob_instance(20, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_schwefel(x, xopt, fopt, D);

    case 21
        % ------ Gallagher 101-me Peaks -------------------------------
        [xopt, fopt, peaks21] = bbob_gallagher_init(21, op.bbob_iid, D, 101);
        op.opt = xopt;
        op.fun = @(x) f_gallagher(x, fopt, D, peaks21);

    case 22
        % ------ Gallagher 21-hi Peaks --------------------------------
        [xopt, fopt, peaks22] = bbob_gallagher_init(22, op.bbob_iid, D, 21);
        op.opt = xopt;
        op.fun = @(x) f_gallagher(x, fopt, D, peaks22);

    case 23
        % ------ Katsuura ---------------------------------------------
        [xopt, fopt] = bbob_instance(23, op.bbob_iid, D);
        [Q, R] = bbob_rotations(23, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_katsuura(x, xopt, fopt, D, Q, R);

    case 24
        % ------ Lunacek bi-Rastrigin ---------------------------------
        [xopt, fopt] = bbob_instance(24, op.bbob_iid, D);
        [Q, R] = bbob_rotations(24, op.bbob_iid, D);
        op.opt = xopt;
        op.fun = @(x) f_lunacek(x, xopt, fopt, D, Q, R);

    otherwise
        error('bbob_problems: fid must be between 1 and 24.');
end
end % bbob_problems


%% ====================================================================
%  INSTANCE GENERATOR  (COCO-style)
%% ====================================================================
function [xopt, fopt] = bbob_instance(fid, iid, dim)
    seed = 10000*fid + iid;
    rng(seed, 'twister');
    xopt = -4 + 8*rand(1, dim);
    fopt = round(100 * tan(pi*(rand-0.5))) / 100;
    fopt = max(-1000, min(1000, fopt));
end


%% ====================================================================
%  ROTATION MATRICES  (one pair Q,R per function/instance/dimension)
%% ====================================================================
function [Q, R] = bbob_rotations(fid, iid, dim)
    seed = 10000*fid + iid + 1;          % offset to differ from xopt seed
    rng(seed, 'twister');
    R = orth(randn(dim));
    Q = orth(randn(dim));
end


%% ====================================================================
%  HELPER TRANSFORMATIONS
%% ====================================================================

% Tosz : element-wise oscillation (applied row-wise)
function y = Tosz(x)
    xhat = zeros(size(x));
    nz   = x ~= 0;
    xhat(nz) = log(abs(x(nz)));
    c1 = (x > 0)*10 + (x <= 0)*5.5;
    c2 = (x > 0)*7.9 + (x <= 0)*3.1;
    y  = sign(x) .* exp(xhat + 0.049*(sin(c1.*xhat) + sin(c2.*xhat)));
end

% Tasy^beta : element-wise (applied row-wise)
function y = Tasy(x, beta, D)
    y = x;
    idx = x > 0;
    i_vec = repmat((1:D), size(x,1), 1);
    exp_vec = 1 + beta * (i_vec - 1) / max(D-1, 1) .* sqrt(max(x,0));
    y(idx) = x(idx) .^ exp_vec(idx);
end

% Lambda^alpha diagonal scaling matrix applied row-wise
function y = lambda_scale(x, alpha, D)
    lam = alpha .^ (0.5 * (0:D-1) / max(D-1,1));   % 1 x D
    y   = x .* lam;
end

% Boundary penalty
function p = fpen(x)
    p = sum(max(0, abs(x) - 5).^2, 2);
end


%% ====================================================================
%  INDIVIDUAL FUNCTION IMPLEMENTATIONS
%% ====================================================================

% ---- f3: Separable Rastrigin ----------------------------------------
function v = f_rastrigin_sep(x, xopt, fopt, D)
    z = lambda_scale(Tasy(Tosz(x - xopt), 0.2, D), 10, D);
    v = 10*(D - sum(cos(2*pi*z), 2)) + sum(z.^2, 2) + fopt;
end

% ---- f4: Büche-Rastrigin --------------------------------------------
function v = f_bueche_rastrigin(x, xopt, fopt, D)
    i_vec = 1:D;
    odd   = mod(i_vec,2) == 1;                          % 1,3,5,...
    t     = Tosz(x - xopt);                             % N x D
    s     = 10 .^ (0.5*(i_vec-1)/max(D-1,1));          % 1 x D  (base scale)
    % Start with base scale, then boost odd columns where t > 0
    si = repmat(s, size(x,1), 1);                       % N x D
    for col = 1:D
        if odd(col)
            si(t(:,col) > 0, col) = 10 * s(col);
        end
    end
    z = si .* t;
    v = 10*(D - sum(cos(2*pi*z),2)) + sum(z.^2,2) + 100*fpen(x) + fopt;
end

% ---- f5: Linear Slope -----------------------------------------------
function v = f_linear_slope(x, xopt_bd, fopt, D)
    i_vec = 1:D;
    si    = sign(xopt_bd) .* 10.^((i_vec-1)/max(D-1,1));  % 1 x D
    % clip: if xi passed xopt in that direction, map back
    z     = x;
    for j = 1:D
        overshoot = xopt_bd(j)*x(:,j) > xopt_bd(j)^2;    % xi beyond xopt
        z(overshoot,j) = xopt_bd(j);
    end
    v = sum(5*abs(si) - si.*z, 2) + fopt;
end

% ---- f6: Attractive Sector ------------------------------------------
function v = f_attractive_sector(x, xopt, fopt, D, Q, R)
    lam10 = diag(10 .^ ((0:D-1)/max(D-1,1)));
    z  = (x - xopt) * R' * lam10 * Q';    % N x D   (z = Q*Lam10*R*(x-xopt))
    si = ones(size(z));
    si(z .* xopt > 0) = 100;              % element-wise compare with xopt broadcast
    % broadcast xopt properly
    xopt_mat = repmat(xopt, size(x,1), 1);
    si = ones(size(z));
    si(z .* xopt_mat > 0) = 100;
    v  = Tosz(sum((si.*z).^2, 2)).^0.9 + fopt;
end

% ---- f7: Step Ellipsoidal -------------------------------------------
function v = f_step_ellipsoidal(x, xopt, fopt, D, Q, R)
    lam10 = diag(10 .^ ((0:D-1)/max(D-1,1)));
    zhat  = (x - xopt) * R' * lam10';    % N x D
    % rounding to produce plateaus
    ztilde = zeros(size(zhat));
    for j = 1:D
        c1 = abs(zhat(:,j)) > 0.5;
        ztilde( c1,j) = floor(0.5 + zhat( c1,j));
        ztilde(~c1,j) = floor(0.5 + 10*zhat(~c1,j))/10;
    end
    z  = ztilde * Q';                     % N x D
    w  = 10 .^ (2*(0:D-1)/max(D-1,1));   % 1 x D
    v  = 0.1 * max(abs(zhat(:,1))/1e4, sum(w.*z.^2,2)) + fpen(x) + fopt;
end

% ---- f8: Rosenbrock (original) --------------------------------------
function v = f_rosenbrock(x, xopt, fopt, D)
    scale = max(1, sqrt(D)/8);
    z     = scale*(x - xopt) + 1;        % N x D,  zopt = 1
    v = sum(100*(z(:,1:end-1).^2 - z(:,2:end)).^2 + (z(:,1:end-1)-1).^2, 2) + fopt;
end

% ---- f9: Rosenbrock (rotated) ---------------------------------------
function v = f_rosenbrock_rotated(x, fopt, D, R)
    scale = max(1, sqrt(D)/8);
    z     = scale * x * R' + 0.5;        % N x D,  zopt = 1
    v = sum(100*(z(:,1:end-1).^2 - z(:,2:end)).^2 + (z(:,1:end-1)-1).^2, 2) + fopt;
end

% ---- f11: Discus ----------------------------------------------------
function v = f_discus(x, xopt, fopt, D, R)
    z    = Tosz((x - xopt) * R');        % N x D
    v    = 1e6*z(:,1).^2 + sum(z(:,2:end).^2, 2) + fopt;
end

% ---- f12: Bent Cigar ------------------------------------------------
function v = f_bent_cigar(x, xopt, fopt, D, R)
    t = (x - xopt) * R';
    z = Tasy(t, 0.5, D) * R;            % N x D : R * Tasy * R * (x-xopt)
    v = z(:,1).^2 + 1e6*sum(z(:,2:end).^2, 2) + fopt;
end

% ---- f13: Sharp Ridge -----------------------------------------------
function v = f_sharp_ridge(x, xopt, fopt, D, Q, R)
    lam10 = diag(10 .^ ((0:D-1)/max(D-1,1)));
    z = (x - xopt) * R' * lam10 * Q';
    v = z(:,1).^2 + 100*sqrt(sum(z(:,2:end).^2, 2)) + fopt;
end

% ---- f14: Different Powers ------------------------------------------
function v = f_different_powers(x, xopt, fopt, D, R)
    z    = (x - xopt) * R';             % N x D
    i_v  = 2 + 4*(0:D-1)/max(D-1,1);   % exponents 2..6
    v    = sqrt(sum(abs(z).^i_v, 2)) + fopt;
end

% ---- f15: Rastrigin (rotated) ---------------------------------------
function v = f_rastrigin_rot(x, xopt, fopt, D, Q, R)
    lam10 = diag(10 .^ ((0:D-1)/max(D-1,1)));
    z = Tasy(Tosz((x-xopt)*R'), 0.2, D) * lam10 * Q';
    v = 10*(D - sum(cos(2*pi*z),2)) + sum(z.^2,2) + fopt;
end

% ---- f16: Weierstrass -----------------------------------------------
function v = f_weierstrass(x, xopt, fopt, D, Q, R)
    lam_inv = diag((1/100) .^ ((0:D-1)/max(D-1,1)));
    z  = Tosz((x - xopt)*R') * lam_inv * Q';   % N x D
    ks = 0:11;
    f0 = sum((1/2).^ks .* cos(2*pi*3.^ks*0.5));
    wt = (1/2).^ks;                              % 1 x 12
    inner = zeros(size(x,1), D);
    for j = 1:D
        inner(:,j) = sum(wt .* cos(2*pi*(3.^ks).*(z(:,j)+0.5)), 2);
    end
    v = (10*(sum(inner,2)/D - f0)).^3 + (10/D)*fpen(x) + fopt;
end

% ---- f17/f18: Schaffers F7 ------------------------------------------
function v = f_schaffers(x, xopt, fopt, D, Q, R, cond_alpha)
    lam = diag(cond_alpha .^ ((0:D-1)/max(D-1,1)));
    z   = Tasy((x-xopt)*R', 0.5, D) * lam * Q';   % N x D
    s   = sqrt(z(:,1:end-1).^2 + z(:,2:end).^2);  % N x (D-1)
    v   = (sum(sqrt(s) + sqrt(s).*sin(50*s.^0.2).^2, 2)/(D-1)).^2 ...
          + 10*fpen(x) + fopt;
end

% ---- f19: Composite Griewank-Rosenbrock -----------------------------
function v = f_griewank_rosenbrock(x, fopt, D, R)
    scale = max(1, sqrt(D)/8);
    z     = scale * x * R' + 0.5;                   % N x D
    si    = 100*(z(:,1:end-1).^2 - z(:,2:end)).^2 + (z(:,1:end-1)-1).^2;
    v     = 10*sum(si/4000 - cos(si), 2)/(D-1) + 10 + fopt;
end

% ---- f20: Schwefel --------------------------------------------------
function v = f_schwefel(x, xopt, fopt, D)
    % sign vector from xopt (signs of xopt determine 1^±)
    sgn   = sign(xopt);
    sgn(sgn==0) = 1;
    xhat  = 2 * sgn .* x;                           % N x D (element-wise)
    % build zhat
    xopt_abs = abs(xopt);
    zhat  = [xhat(:,1), xhat(:,2:end) + 0.25*(xhat(:,1:end-1) - 2*xopt_abs(1:end-1))];
    lam10 = 10 .^ ((0:D-1)/max(D-1,1));
    z     = 100*(lam10.*(zhat - 2*xopt_abs) + 2*xopt_abs);
    v     = -(sum(z.*sin(sqrt(abs(z))),2))/(100*D) + 4.189828872724339 ...
            + 100*fpen(z/100) + fopt;
end

% ---- f21/f22: Gallagher initialisation ------------------------------
function [xopt, fopt, peaks] = bbob_gallagher_init(fid, iid, D, npeaks)
    seed = 10000*fid + iid;
    rng(seed, 'twister');
    xopt_raw = -4 + 8*rand(1,D);
    fopt = round(100*tan(pi*(rand-0.5)))/100;
    fopt = max(-1000,min(1000,fopt));

    % rotation matrix
    R = orth(randn(D));

    % peak heights w_i
    if npeaks == 101
        w = [10, 1.1 + 8*(1:100)/99];               % i=1 is global
        alpha_set = 1000.^(2*(0:99)/99);
    else  % 21
        w = [10, 1.1 + 8*(1:20)/19];
        alpha_set = 1000.^(2*(0:19)/19);
    end

    % peak locations y_i
    % global optimum y_1 in [-4,4]^D, rest in [-5,5]^D ([-4.9,4.9] per spec)
    y1   = -4 + 8*rand(1,D);
    yrest = -4.9 + 9.8*rand(npeaks-1, D);
    Y    = [y1; yrest];                              % npeaks x D

    % alpha values for each peak (random permutation of set)
    alpha_idx = randperm(npeaks-1);
    alphas    = [alpha_set(end), alpha_set(alpha_idx)];   % peak 1 gets largest

    % Build C_i matrices: Lambda^{alpha_i}/alpha_i^{1/4}, randomly permuted diag
    Cs = cell(npeaks,1);
    for i = 1:npeaks
        lam_diag = alphas(i) .^ (0.5*(randperm(D)-1)/max(D-1,1));
        Cs{i}    = diag(lam_diag / alphas(i)^0.25);
    end

    xopt = y1;
    peaks.npeaks = npeaks;
    peaks.w  = w;
    peaks.Y  = Y;
    peaks.Cs = Cs;
    peaks.R  = R;
end

% ---- f21/f22: Gallagher evaluator -----------------------------------
function v = f_gallagher(x, fopt, D, peaks)
    N = size(x,1);
    npeaks = peaks.npeaks;
    vals = zeros(N, npeaks);
    for i = 1:npeaks
        dy = x - peaks.Y(i,:);                      % N x D
        tmp = dy * peaks.R' * peaks.Cs{i} * peaks.R;  % N x D
        vals(:,i) = peaks.w(i) * exp(-sum(tmp.*dy,2)/(2*D));
    end
    v = Tosz(10 - max(vals,[],2)).^2 + fpen(x) + fopt;
end

% ---- f23: Katsuura --------------------------------------------------
function v = f_katsuura(x, xopt, fopt, D, Q, R)
    lam100 = diag(100 .^ ((0:D-1)/max(D-1,1)));
    z  = (x - xopt) * R' * lam100 * Q';             % N x D
    js = 2.^(1:32);                                  % 1 x 32
    prod_val = ones(size(x,1), 1);
    for j = 1:D
        zj  = z(:,j);                                % N x 1
        arg = js .* zj;                              % N x 32 via broadcasting
        inner = sum(abs(arg - round(arg)) ./ js, 2); % N x 1
        prod_val = prod_val .* (1 + j*inner).^(10/D^1.2);
    end
    v = (10/D^2)*(prod_val - 10/D^2) + fpen(x) + fopt;
end

% ---- f24: Lunacek bi-Rastrigin --------------------------------------
function v = f_lunacek(x, xopt, fopt, D, Q, R)
    mu0 = 2.5;
    d   = 1;
    s   = 1 - 1/(2*sqrt(D+20) - 8.2);
    mu1 = -sqrt((mu0^2 - d)/s);

    sgn  = sign(xopt);
    sgn(sgn==0) = 1;
    xhat = 2*sgn.*x;                                 % N x D

    lam100 = diag(100 .^ ((0:D-1)/max(D-1,1)));
    z   = (xhat - mu0) * R' * lam100 * Q';           % N x D

    term1 = sum((xhat - mu0).^2, 2);
    term2 = d*D + s*sum((xhat - mu1).^2, 2);
    cos_part = 10*(D - sum(cos(2*pi*z),2));

    v = min(term1, term2) + cos_part + 1e4*fpen(x) + fopt;
end
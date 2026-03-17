%% Run a (mu lambda) Evolution Strategy (ES) with One Fifth rule on a given single-objective optimization problem
% Input
% - op: a struct describing the optimization problem with the following attributes:
%   - .fun: handler of the objective function
%   - .dim: problem dimensionality
%   - .bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
%   - .opt: a matrix mxd points in d dimension representing the m true optima in the search space
%   - .opt_known: a boolean flag set to true if the optimum/optima is/are known 
%   - .isMin: a boolean flag set to true if the problem is minimization, false if maximization
%   - .maxFE: maximum number of function evaluation budget
% - algo: a struct containing the parameters and settings of the ES algorithm with the following attributes:
%   - .pop_size or .lambda: population size (this is lambda)
%   - .mu: number of parents
%   - .sigma: initial mutation strength (scalar)
%   - .survival: struct containing settings about the survival scheme to be executed, containing the following attributes:
%       - schema: string defining the type of survival to be performed, it could be:
%           - "(µ+λ)": perform elitist survival by adding both populations, sorting them, taking the µ best
%           - "(µ,λ)": perform non-elitist survival by copying the best µ of the λ offspring in the new population with µ individuals
%   - .verbose: boolean flag to print output log
%   - .plotting: boolean flag to visualize the plot
%   - .refresh: duration of pause between plots
% Output
% - best: a struct containing the all time best solution (respectively) with the following attributes:
%   - .point: an array 1xd representing the point of the best solution in d dimensions
%   - .fit: fitness of the individual
% - error: a struct containing the error with respect of the true optimum, with the following attributes:
%   - .src_space: error in the search space, i.e. Euclidean distance to true optimum (or -1 if unknown)
%   - .obj_space: error in the objective space, absolute value of difference with objective value of true optimum (or -1 if unknown)
% - runtime: runtime in seconds
% - convergence_array: an array ix2 containing all the errors for each function evaluations to check convergence
function [best, error, runtime, convergence_array] = run_ES_OneFifth(op, algo)
    close all;
    rng shuffle;
    
    %-- INITIALIZATION --%
    if algo.lambda <= 0
        algo.mu = 10*op.dim;
    end
    if algo.mu <= 0 || algo.mu > algo.lambda
        algo.mu = floor(algo.lambda/4);
    end
    
    % The 1/5 Rule uses a GLOBAL SCALAR sigma
    sigma_global = algo.sigma; 
    
    convergence_array = zeros(round((op.maxFE/op.dim)/algo.lambda),2);
    conv_idx = 1;
    target_precision = 1e-8;
    total_budget_FE = op.maxFE;
    tic;
    iteration = 1;

    %-- INITIAL POPULATION --%
    matPool = Shared.initializeRandomPopulation(algo.mu, op.dim, op.bounds);
    
    if ~strcmp(algo.survival.schema,"(µ,λ)")
        [matPool, op.maxFE] = Shared.evaluate(matPool, op.fun, op.maxFE);
        [best, ~] = Shared.findBestWorst(matPool, op.isMin);
        error = Shared.calculateError(op,best);

        %--UPDATE CONVERGENCE ARRAY
        if op.opt_known == true
            [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, error.obj_space);
        else
            [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, best.fit);
        end
    end

    while op.maxFE > 0
        %-- EVOLUTIONARY OPERATIONS --%
        % New function returns parent indices (p_idx) to calculate success rate
        [off, p_idx] = Shared.gaussianMutationOneFifth(matPool, sigma_global, algo.lambda, op.bounds);
        
        [off, op.maxFE] = Shared.evaluate(off, op.fun, op.maxFE);
        
        %-- 1/5 RULE LOGIC: Calculate Success Rate --%
        % We check how many offspring are better than their specific parent
        successes = 0;
        for i = 1:algo.lambda
            if op.isMin
                if off(i, end) < matPool(p_idx(i), end)
                    successes = successes + 1;
                end
            else
                if off(i, end) > matPool(p_idx(i), end)
                    successes = successes + 1;
                end
            end
        end
        
        % Update Sigma: ps is the success probability
        ps = successes / algo.lambda;
        c = 0.85; % Constant factor
        if ps > 0.2
            sigma_global = sigma_global / c;
        elseif ps < 0.2
            sigma_global = sigma_global * c;
        end

        %-- SURVIVAL --%
        matPool = survival(matPool, off, algo.survival, op.isMin);

        %-- UPDATE BEST SOLUTION & LOGGING (Same as your original code) --%
        [current_best, ~] = Shared.findBestWorst(off, op.isMin);
        if iteration == 1, best = current_best; else, best = Shared.updateBest(best, current_best, op.isMin); end
        error = Shared.calculateError(op,best);
        
        % Update convergence array, verbose, and plotting (Same as original)
        if op.opt_known == true
            [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, error.obj_space);
        else
            [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, best.fit);
        end
        
        if algo.verbose, Shared.showLog(iteration, op.maxFE, error.obj_space, best.fit, op.opt_known); end
        if algo.plotting, Shared.plotPopulation(off, best, op, iteration == 1); pause(algo.refresh); end
        
        iteration = iteration + 1;
        if error.obj_space <= target_precision, break; end
    end
    runtime = toc;
    convergence_array(conv_idx:end,:) = [];
    best = rmfield(best,'idx');
end

%% Perform survival stage (i.e., environmental selection)
% Input
% - pop: a matrix µx(d+1) of µ points in d dimensions representing the current population, last column is fitness value
% - off: a matrix λx(d+1) of λ points in d dimensions representing the offspring, last column is fitness value
% - sigma_pop: a matrix µxd of µ mutation strengths for each of the µ points in 'pop' and for each of their d dimensions
% - sigma_off: a matrix λxd of λ mutation strengths for each of the λ points in 'off' and for each of their d dimensions
% - .survival: struct containing settings about the survival scheme to be executed, containing the following attributes:
%    - schema: string defining the type of survival to be performed, it could be:
%       - "(µ+λ)": perform elitist survival by adding both populations, sorting them, taking the µ best
%       - "(µ,λ)": perform non-elitist survival by copying the best µ of the λ offspring in the new population with µ individuals
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - pop: a matrix µx(d+1) of µ points in d dimensions representing the new population, last column will be fitness value
% - sigma_pop: the updated mutation strenght matrix µxd 
function [pop] = survival(pop, off, survival, isMin)
    switch survival.schema
        case "(µ+λ)"
            [pop, ~] = Shared.survival_elitist_muPlusLambda(pop, off, isMin);
        case "(µ,λ)"
            [pop, ~] = Shared.survival_nonElitist(pop, off, isMin);
    end
end
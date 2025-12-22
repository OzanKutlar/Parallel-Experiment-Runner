%% Run a (mu, lambda) Evolution Strategy (ES) on a given single-objective optimization problem
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
%   - .pop_size: population size (this is lambda)
%   - .mu: number of parents
%   - .sigma: initial mutation strength (scalar)
%   - .tau: learning rate for step-size adaptation (local)
%   - .tau_prime: learning rate for step-size adaptation (global)
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
% - convergence_array: an array ix1 containing all the best fitness for each iteration to check convergence
function [best, error, runtime, convergence_array] = run_ES(op, algo)
    close all;
    rng shuffle;

    %-- INITIALIZATION --%
    if algo.pop_size <= 0
        algo.pop_size = 100;
    end
    if algo.pop_size <= 0 || algo.pop_size > algo.off_size
        algo.mu = floor(algo.off_size/3);
    end

    % allocate mutation strengths for each parent
    sigma_pop = algo.sigma * ones(algo.pop_size, op.dim);

    convergence_array = [];

    tic;  % start timer

    iteration = 1;

    %-- INITIAL POPULATION --%
    matPool = Shared.initializeRandomPopulation(algo.pop_size, op.dim, op.bounds);
    if ~strcmp(algo.survival.schema,"(µ,λ)")
        [matPool, op.maxFE] = Shared.evaluate(matPool, op.fun, op.maxFE);
    end

    while op.maxFE > 0
        
        %--EVOLUTIONARY OPERATIONS
        [off, sigma_off] = Shared.gaussianMutationWithSigmaSelfAdaptation(matPool, sigma_pop, algo.off_size, algo.tau_prime, algo.tau, op.bounds);   % mutate
        [off, op.maxFE] = Shared.evaluate(off, op.fun, op.maxFE);                                       % evaluate
        [matPool, sigma_pop] = survival(matPool, off, sigma_pop, sigma_off, algo.survival, op.isMin);   % survival

        %--UPDATE BEST SOLUTION
        [current_best, ~] = Shared.findBestWorst(off, op.isMin);
        if iteration == 1
            best = current_best;
        else
            best = Shared.updateBest(best, current_best, op.isMin);
        end

        convergence_array = [convergence_array; best.fit];

        %--VERBOSE (SHOW LOG)
        if algo.verbose
            fprintf('IT: %d  FEs: %d)\t', iteration, op.maxFE);
            fprintf('Fit: %.10f\n', best.fit);
        end
        
        %--PLOT (SHOW SEARCH SPACE)
        if algo.plotting
            Shared.plotPopulation(off, best, op, iteration == 1);
            pause(algo.refresh);
        end

        iteration = iteration + 1;
    end

    runtime = toc;

    error = Shared.calculateError(op,best);     % calculate error
    best = rmfield(best,'idx');                 % remove field .idx from 'best' because it is not used outside this function
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
function [pop, sigma_pop] = survival(pop, off, sigma_pop, sigma_off, survival, isMin)

    switch survival.schema
        case "(µ+λ)"
            [pop, indices] = Shared.survival_elitist_muPlusLambda(pop, off, isMin);
            sigma_pop = [sigma_pop;sigma_off];
            sigma_pop = sigma_pop(indices,:); % update sigma
        case "(µ,λ)"
            [pop, indices] = Shared.survival_nonElitist(pop, off, isMin);
            sigma_pop = sigma_off(indices,:); % update sigma
    end
end



%% Run a steady-state Genetic Algorithm on a given single-objective optimization problem
% Input
% - op: a struct describing the optimization problem with the following attributes:
%   - .fun: handler of the objective function
%   - .dim: problem dimensionality
%   - bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
%   - .opt: a matrix mxd points in d dimension representing the m true optima in the search space
%   - .opt_known: a boolean flag set to true if the optimum/optima is/are known 
%   - .isMin: a boolean flag set to true if the problem is minimization, false if maximization
%   - .maxFE: maximum number of function evaluation budget
% - algo: a struct containing the parameters and settings of the algorithm with the following attributes:
%   - .pop_size: population size
%   - .crossover: a struct containing the parameters of the sbx crossover with the following attributes:
%     - .p_c: probability of crossover
%     - .eta_c: eta parameter of sbx (higher values will generate offspring closer to their parents)
%   - .mutation: a struct containing the parameters of the polynomial mutation with the following attributes:
%     - .p_m: probability of mutation
%     - .eta_m: eta parameter of polynomial mutation (higher values will generate mutated individuals closer to their original)
%   - .verbose: a boolean flag set to true if you desired the output log to be printed on screen in real time
%   - .plotting: a boolean flag set to true if you desired to visualize the plot with solutions evolving in real time
%   - .refresh: duration of the pause between plots
% Output
% - best: a struct containing the all time best solution (respectively) with the following attributes:
%   - .point: an array 1xd representing the point of the best solution in d dimensions
%   - .fit: fitness of the individual
% - error: a struct containing the error with respect of the true optimum, with the following attributes:
%   - .src_space: error in the search space, i.e. Euclidean distance to true optimum (or -1 if unknown)
%   - .obj_space: error in the objective space, absolute value of difference with objective value of true optimum (or -1 if unknown)
% - runtime: runtime in seconds
% - convergence_array: an array ix2 containing all the errors for each function evaluations to check convergence
function [best, error, runtime, convergence_array] = run_RGA_steady_state(op, algo)
    
    close all;
    rng shuffle;
    
    %--INITIALIZATION 
    
    % in case a funny user decides to have an odd number of idividuals in the population...
    if mod(algo.pop_size,2) ~= 0
        algo.pop_size = algo.pop_size + 1;
    end
    if algo.pop_size <= 0
        algo.pop_size = 100;
    end

    convergence_array = zeros(round((op.maxFE/op.dim)/algo.pop_size),2);    % convergence array for plotting
    conv_idx = 1;   % index of the current element in the convergence array

    target_precision = 1e-8;    % target precision
    total_budget_FE = op.maxFE; % original value of maximum function evaluations budget

    tic;    % start timer
    pop = Shared.initializeRandomPopulation(algo.pop_size, op.dim, op.bounds);     % init population 
    [pop, op.maxFE] = Shared.evaluate(pop, op.fun, op.maxFE);                      % evaluate
    [best, ~] = Shared.findBestWorst(pop, op.isMin);                               % update best
    error = Shared.calculateError(op,best);                                        % calculate error
    
    %--UPDATE CONVERGENCE ARRAY
    if op.opt_known == true
        [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, error.obj_space);
    else
        [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, best.fit);
    end

    %--PLOT (DRAW SEARCH SPACE)
    if algo.plotting == true
        Shared.plotPopulation(pop,best,op,true);
        pause(algo.refresh);
    end
   
    %--ITERATIONS
    iteration = 1;
    while op.maxFE > 0

        %--CONVERGENCE TO TARGET stops when reached the target in precision 
        if error.obj_space <= target_precision
            if algo.verbose
                disp('Target reached! Stopping run.');
            end
            break;
        end

        %--EVOLUTIONARY OPERATIONS
        matPool = Shared.kWayTournamentSelection(pop, 2, 2, op.isMin);   % selection 
        off = variation(matPool, algo.crossover, algo.mutation, op.bounds);             % variation
        [off, op.maxFE] = Shared.evaluate(off, op.fun, op.maxFE);                       % evaluate
        pop = Shared.survival_bestToWorst(pop, off, op.isMin);                          % survival

        %--UPDATE BEST SOLUTION
        [pop_best, ~] = Shared.findBestWorst(pop, op.isMin);
        best = Shared.updateBest(best, pop_best, op.isMin);
        error = Shared.calculateError(op,best);     

        %--UPDATE CONVERGENCE ARRAY
        if op.opt_known == true
            [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, error.obj_space);
        else
            [convergence_array, conv_idx] = Shared.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, best.fit);
        end

        %--VERBOSE (SHOW LOG)
        if algo.verbose
            Shared.showLog(iteration, op.maxFE, error.obj_space, best.fit, op.opt_known, array_partSizes);
        end
        
        %--PLOT (DRAW SEARCH SPACE)
        if algo.plotting == true
            Shared.plotPopulation(pop,best,op,false);
            pause(algo.refresh);
        end

        iteration = iteration + 1;
    end  
    runtime = toc; % stop timer

    convergence_array(conv_idx:end,:) = []; % delete unused parts of convergence array
    best = rmfield(best,'idx');                 % remove field .idx from 'best' because it is not used outside this function
end

%% Perform variation operations (i.e., crossover and mutation)
% Input
% - matPool: a matrix nx(d+1) of n points in d dimensions representing the mating pool, i.e. the parents to undergoe reproduction
% - .cross_params: a struct containing the parameters of the sbx crossover with the following attributes:
%   - .p_c: probability of crossover
%   - .eta_c: eta parameter of sbx (higher values will generate offspring closer to their parents)
% - .mut_params: a struct containing the parameters of the polynomial mutation with the following attributes:
%   - .p_m: probability of mutation
%   - .eta_m: eta parameter of polynomial mutation (higher values will generate mutated individuals closer to their original)
% - .bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
% Output
% - off: a matrix 2x(d+1) of 2 points in d dimensions representing the two offspring, last column is fitness value
function [off] = variation(matPool, cross_params, mut_params, bounds)
    
    d = size(matPool,2);

    % declare a static array of chromosomes filled with zeros
    off = zeros(2,d);
    
    % crossover
    p1 = matPool(1,1:end-1);
    p2 = matPool(2,1:end-1);

    [o1, o2] = Shared.sbxCrossover(p1, p2, cross_params, bounds);

    % mutation
    off(1,1:end-1) = Shared.polynomialMutation(o1, mut_params, bounds);
    off(2,1:end-1) = Shared.polynomialMutation(o2, mut_params, bounds);
        
end

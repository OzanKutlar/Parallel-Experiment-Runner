%% Run the Big Bang-Big Crunch Algorithm on a given single-objective optimization problem
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
%   - .fasten: coefficient to divide the extent of mutation at each generation for faster convergence (default = 1)
%   - .survival: struct containing settings about the survival scheme to be executed, containing the following attributes:
%       - schema: string defining the type of survival to be performed, it could be:
%           - "non-elitist": perform non elitist survival, in which the new population is composed only by the offspring (classic BBBC from the original paper)
%           - "replacement": perform elitist survival, in which the center of mass is reintroduced in the population and replaces the current worst (not in the original paper)
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
% - convergence_array: an array ix1 containing all the best fitness for each iteration to check convergence
function [best, error, runtime, convergence_array]  = run_BBBC(op, algo)
    close all;
    rng shuffle;
    
    %--INITIALIZATION 
    % in case a funny user decides to have an odd number of idividuals in the population...
    if algo.pop_size <= 0
        algo.pop_size = 100;
    end

    convergence_array = [];

    tic;    % start timer
   
    %--ITERATIONS
    iteration = 1;
    while op.maxFE > 0
        if iteration == 1
            pop = Shared.initializeRandomPopulation(algo.pop_size, op.dim, op.bounds);     % init population 
        else
            pop = Shared.gaussianMutation(pop_best.point, algo.pop_size, iteration*algo.fasten, op.bounds);
        end

        [pop, op.maxFE] = Shared.evaluate(pop, op.fun, op.maxFE);  % evaluation
        if iteration ~= 1 && strcmp(algo.survival.schema,"replacement")
            pop = Shared.survival_bestToWorst(pop, [pop_best.point, pop_best.fit], op.isMin);     % survival
        end

        [pop_best, ~] = Shared.findBestWorst(pop, op.isMin);       % update best
        if iteration == 1
            best = pop_best;
        else
            best = Shared.updateBest(best, pop_best, op.isMin);
        end

        convergence_array = [convergence_array; best.fit];
        
        %--VERBOSE (SHOW LOG)
        if algo.verbose
            fprintf('IT: %d FEs: %d)\t', iteration, op.maxFE);
            fprintf('Fit: %.10f ', best.fit);
            fprintf('\n');
        end
        
        %--PLOT (SHOW SEARCH SPACE)
        if algo.plotting == true
            Shared.plotPopulation(pop,best,op,iteration==1);
            pause(algo.refresh);
        end

        iteration = iteration + 1;
         
    end  
    runtime = toc; % stop timer

    error = Shared.calculateError(op,best);     % calculate error
    best = rmfield(best,'idx');                 % remove field .idx from 'best' because it is not used outside this function
end


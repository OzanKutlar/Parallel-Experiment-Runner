%% Run a generational Genetic Algorithm on a given single-objective optimization problem
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
%   - .off_size: number of desired offspring (increases selection pressure), by default is the same as 'pop_size'
%   - .crossover: a struct containing the parameters of the sbx crossover with the following attributes:
%     - .p_c: probability of crossover
%     - .eta_c: eta parameter of sbx (higher values will generate offspring closer to their parents)
%   - .mutation: a struct containing the parameters of the polynomial mutation with the following attributes:
%     - .p_m: probability of mutation
%     - .eta_m: eta parameter of polynomial mutation (higher values will generate mutated individuals closer to their original)
%   - .survival: struct containing settings about the survival scheme to be executed, containing the following attributes:
%       - schema: string defining the type of survival to be performed, it could be:
%           - "(µ+λ)": perform elitist survival by adding both populations, sorting them, taking the µ best
%           - "(µ,λ)": perform non-elitist survival by copying the best µ of the λ offspring in the new population with µ individuals
%           - "α": perform elitist survival by taking α% old elites and 100-α% new offspring (if α=0 it is non-elitist)
%       - alpha: if the α-schema is selected, this is the percentage of old elites that will survive
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
function [best, error, runtime, convergence_array] = run_RGA_generational(op, algo)

    close all;
    rng shuffle;
    
    %--INITIALIZATION 
    if mod(algo.pop_size,2) ~= 0
        algo.pop_size = algo.pop_size + 1;
    end
    if algo.pop_size <= 0
        algo.pop_size = 100;
    end
    if algo.off_size < algo.pop_size
        algo.off_size = algo.pop_size;
    end
    if isfield(algo.survival, 'alpha')
        algo.survival.alpha = max(0,min(100,algo.survival.alpha));  % keep the value of α as a percentage (i.e., with 0% is non elitist, with 100% it will not evolve!!)
    end

    convergence_array = [];
    
    tic;    % start timer
    pop = Shared.initializeRandomPopulation(algo.pop_size, op.dim, op.bounds);     % init population 
    [pop, op.maxFE] = Shared.evaluate(pop, op.fun, op.maxFE);                      % evaluate
    [best, ~] = Shared.findBestWorst(pop, op.isMin);                               % update best

    %--PLOT (SHOW SEARCH SPACE)
    if algo.plotting == true
        Shared.plotPopulation(pop,best,op,true);
        pause(algo.refresh);
    end
   
    %--ITERATIONS
    iteration = 1;
    while op.maxFE > 0

        %--EVOLUTIONARY OPERATIONS
        matPool = Shared.kWayTournamentSelection(pop, 2, algo.pop_size, algo.off_size, op.isMin);    % selection 
        off = variation(matPool, algo.crossover, algo.mutation, op.bounds);                         % variation
        [off, op.maxFE] = Shared.evaluate(off, op.fun, op.maxFE);                                    % evaluation
        pop = survival(pop, off, algo.survival, op.isMin);                                          % survival
        
        %--UPDATE BEST SOLUTION
        [pop_best, ~] = Shared.findBestWorst(pop, op.isMin);
        best = Shared.updateBest(best, pop_best, op.isMin);

        convergence_array = [convergence_array; best.fit];
        
        %--VERBOSE (SHOW LOG)
        if algo.verbose
            fprintf('IT: %d FEs: %d)\t', iteration, op.maxFE);
            fprintf('Fit: %.10f ', best.fit);
            fprintf('\n');
        end
        
        %--PLOT (SHOW SEARCH SPACE)
        if algo.plotting == true
            Shared.plotPopulation(pop,best,op,false);
            pause(algo.refresh);
        end

        iteration = iteration + 1;
                         
    end  
    runtime = toc; % stop timer

    error = Shared.calculateError(op,best);     % calculate error
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
% - off: a matrix mx(d+1) of m points in d dimensions representing the offspring, last column is fitness value
function [off] = variation(matPool, cross_params, mut_params, bounds)

    [n,d] = size(matPool); 
    matPool = matPool(randperm(size(matPool,1)), :); % shuffle the mating pool
    
    off = zeros(n,d);
    for i=1:2:n

        % crossover
        p1 = matPool(i,1:end-1);
        p2 = matPool(i+1,1:end-1);

        [o1, o2] = Shared.sbxCrossover(p1, p2, cross_params, bounds);   

        % mutation
        o1 = Shared.polynomialMutation(o1, mut_params, bounds);
        o2 = Shared.polynomialMutation(o2, mut_params, bounds);

        off(i,1:end-1) = o1;
        off(i+1,1:end-1) = o2;

    end
end


%% Perform survival stage (i.e., environmental selection)
% Input
% - pop: a matrix µx(d+1) of µ points in d dimensions representing the current population, last column is fitness value
% - off: a matrix λx(d+1) of λ points in d dimensions representing the offspring, last column is fitness value
% - .survival: struct containing settings about the survival scheme to be executed, containing the following attributes:
%    - schema: string defining the type of survival to be performed, it could be:
%       - "(µ+λ)": perform elitist survival by adding both populations, sorting them, taking the µ best
%       - "(µ,λ)": perform non-elitist survival by copying the best µ of the λ offspring in the new population with µ individuals
%       - "α": perform elitist survival by taking α% old elites and 100-α% new offspring (if α=0 it is non-elitist)
%    - alpha: if the α-schema is selected, this is the percentage of old elites that will survive
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - pop: a matrix µx(d+1) of µ points in d dimensions representing the new population, last column will be fitness value
function [pop] = survival(pop, off, survival, isMin)

    switch survival.schema
        case "(µ+λ)"
            pop = Shared.survival_elitist_muPlusLambda(pop, off, isMin);
        case "α"
            pop = Shared.survival_elitist_alpha(pop, off, survival.alpha, isMin);
        case "(µ,λ)"
            pop = Shared.survival_nonElitist(pop, off, isMin);
    end
end



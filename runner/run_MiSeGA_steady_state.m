%% Run a steady-state Genetic Algorithm on a given single-objective optimization problem
% Input
% - op: a struct describing the optimization problem with the following attributes:
%   - .fun: handler of the objective function
%   - .dim: problem dimensionality
%   - bounds: a matrix 1*2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
%   - .opt: a matrix m*d points in d dimension representing the m true optima in the search space
%   - .opt_known: a boolean flag set to true if the optimum/optima is/are known 
%   - .isMin: a boolean flag set to true if the problem is minimization, false if maximization
%   - .maxFE: maximum number of function evaluation budget
% - algo: a struct containing the parameters and settings of the algorithm with the following attributes:
%   - selection_methods: string with name of the selection method for each partition (e.g., "tournament","rank","sus","truncation"); its size dynamically sets the value 'm' that is the number of partitions
%   - partition_size: size of each partition
%   - pop_size: overall population size, automatically set to partition_size * number of partitions
%   - recombination_mode: string that decides the type of recombination mode:
%       - "intra", variation is done only within partition for each independent selection method
%       - "inter", variation is done inter partition among all individuals selected from all partitions
%   - mixed_modality: string that decides the type of partitioning:
%       - "uniform", sizes of partitions is static and never changes
%       - "adaptive", sizes of partitions adapt to the scuccess of each selection method until one dominates the others and becomes the only partition
%       - "restart", sizes of partitions adapt to the scuccess of each selection method and when one dominates the others, all partitions sizes are reset to the same size
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
%   - .point: an array 1*d representing the point of the best solution in d dimensions
%   - .fit: fitness of the individual
% - error: a struct containing the error with respect of the true optimum, with the following attributes:
%   - .src_space: error in the search space, i.e. Euclidean distance to true optimum (or -1 if unknown)
%   - .obj_space: error in the objective space, absolute value of difference with objective value of true optimum (or -1 if unknown)
% - runtime: runtime in seconds
% - convergence_array: an array i*2 containing all the errors for each function evaluations to check convergence
function [best, error, runtime, convergence_array] = run_MISEGA_steady_state(op, algo)
    
    close all;
    rng shuffle;
    
    %--INITIALIZATION 
    m = size(algo.selection_methods,2); % number of partitions
    algo.off_size = 2;
    
    % in case a funny user decides to have an odd number of idividuals in the population...
    if mod(algo.partition_size,2) ~= 0
        algo.partition_size = algo.partition_size + 1;
    end
    if algo.partition_size <= 0
        algo.partition_size = 4*op.dim;
    end
    
    algo.pop_size       = m * algo.partition_size;          % total population set to number of partitions * partition size
    array_partSizes     = ones(m,1) * algo.partition_size;  % array with size of partitions
    part_refs           = zeros(algo.pop_size,1);           % array containing reference to which partition each individual belongs to (if generated in first generation, then it is 0, otherwise from 1 to m)

    convergence_array = zeros(round((op.maxFE/op.dim)/algo.pop_size),2);    % convergence array for plotting
    conv_idx = 1;   % index of the current element in the convergence array

    target_precision = 1e-8;    % target precision
    total_budget_FE = op.maxFE; % original value of maximum function evaluations budget

    tic;        % start timer
    pop             = inter.initializeRandomPopulation(algo.pop_size, op.dim, op.bounds);  % init population 
    [pop, op.maxFE] = inter.evaluate(pop, op.fun, op.maxFE);                               % evaluate
    [best, ~]       = inter.findBestWorst(pop, op.isMin);                                  % update best
    error           = inter.calculateError(op,best);                                       % calculate error
    
    %--UPDATE CONVERGENCE ARRAY
    if op.opt_known == true
        [convergence_array, conv_idx] = inter.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, error.obj_space);
    else
        [convergence_array, conv_idx] = inter.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, best.fit);
    end

    %--PLOT (DRAW SEARCH SPACE)
    if algo.plotting == true
        inter.plotPopulation(pop,best,op,true);
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
        
        %--PREPARE PARTITIONS
        pop         = [pop, part_refs];         % add a reference to which partition the respective individual was generated from 
        off         = zeros(2*m,size(pop,2));     % prepares the offspring array
        matPool     = zeros(2*m,size(pop,2));     % prepares the mating pool array
        pop         = inter.shuffle_population(pop);  % shuffle for random partitioning
        idxStart    = 1;
        idxEnd      = 0;
        for p = 1:m

            idxEnd = idxEnd + array_partSizes(p,1);
            pop_part = pop(idxStart:idxEnd,1:end-1);

            if size(pop_part,1) == 0
                continue;
            end


            %--MIXED SELECTION
            switch algo.selection_methods{p}
                case "tournament"
                    matPool_part = inter.kWayTournamentSelection(pop_part, 2, algo.off_size, op.isMin);   
                case "rank"
                    matPool_part = inter.rankSelection(pop_part, algo.off_size, op.isMin);
                case "truncation"
                    matPool_part = inter.truncationSelection(pop_part, algo.off_size, op.isMin);
                case "sus"
                    matPool_part = inter.susSelection(pop_part, algo.off_size, op.isMin);
                otherwise
                    error("Selection method not implemented!");
            end
            
            if strcmp(algo.recombination_mode,"intra") == true
                off_part = variation(matPool_part, algo.crossover, algo.mutation, op.bounds, false);    % variation
                [off_part, op.maxFE] = inter.evaluate(off_part, op.fun, op.maxFE);         % evaluate
                off(algo.off_size*p-algo.off_size+1:algo.off_size*p,1:end-1) = off_part;
                off(algo.off_size*p-algo.off_size+1:algo.off_size*p,end) = p;
            else
                matPool(algo.off_size*p-algo.off_size+1:algo.off_size*p,1:end-1) = matPool_part;
                matPool(algo.off_size*p-algo.off_size+1:algo.off_size*p,end) = p;
            end

            idxStart = idxEnd + 1;
        end

        if strcmp(algo.recombination_mode,"inter") == true
            off = variation(matPool, algo.crossover, algo.mutation, op.bounds, true);    % variation
            off_refs = off(:,end);
            off(:,end) = [];
            [off, op.maxFE] = inter.evaluate(off, op.fun, op.maxFE);         % evaluate
            off(:,end+1) = off_refs;
        end

        %--SURVIVAL
        pop = inter.swapFitPart(pop); % swap fitness and partition reference such that fitness is the last column
        off = inter.swapFitPart(off); % swap fitness and partition reference such that fitness is the last column
        pop = inter.survival_bestToWorst(pop, off, op.isMin);  % survival
        pop = inter.swapFitPart(pop); % swap fitness and partition reference such that partition reference is the last column

        if strcmp(algo.mixed_modality,"adaptive") || strcmp(algo.mixed_modality,"restart")
            [array_partSizes] = inter.resizePartitions(pop, array_partSizes, op.isMin, algo.mixed_modality);
        end
        
        part_refs   = pop(:,end);       % save partition reference in the external array
        pop(:,end)  = [];               % remove partition reference for next operations (to be consistent with the library functions)

        %--UPDATE BEST SOLUTION
        [pop_best, ~] = inter.findBestWorst(pop, op.isMin);
        best = inter.updateBest(best, pop_best, op.isMin);
        error = inter.calculateError(op,best);     

        %--UPDATE CONVERGENCE ARRAY
        if op.opt_known == true
            [convergence_array, conv_idx] = inter.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, error.obj_space);
        else
            [convergence_array, conv_idx] = inter.updateConvergenceArray(convergence_array, conv_idx, total_budget_FE, op.maxFE, best.fit);
        end

        %--VERBOSE (SHOW LOG)
        if algo.verbose
            inter.showLog(iteration, op.maxFE, error.obj_space, best.fit, op.opt_known, array_partSizes);
        end
        
        %--PLOT (DRAW SEARCH SPACE)
        if algo.plotting == true
            inter.plotPopulation(pop,best,op,false);
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
% - matPool: a matrix n*(d+1) of n points in d dimensions representing the mating pool, i.e. the parents to undergoe reproduction
% - .cross_params: a struct containing the parameters of the sbx crossover with the following attributes:
%   - .p_c: probability of crossover
%   - .eta_c: eta parameter of sbx (higher values will generate offspring closer to their parents)
% - .mut_params: a struct containing the parameters of the polynomial mutation with the following attributes:
%   - .p_m: probability of mutation
%   - .eta_m: eta parameter of polynomial mutation (higher values will generate mutated individuals closer to their original)
% - bounds: a matrix 1*2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
% - isinter:   a boolean set to true if the recombination (i.e., variation) is performed among all offspring, false if within partition only
% Output
% - off: a matrix m*(d+1) of m points in d dimensions representing the offspring, last column is fitness value
function [off] = variation(matPool, cross_params, mut_params, bounds, isinter)

    [n,d] = size(matPool); 
    matPool = matPool(randperm(size(matPool,1)), :); % shuffle the mating pool
    
    off = zeros(n,d);
    for i=1:2:n

        % crossover
        if isinter == true
            part1 = matPool(i,end);
            part2 = matPool(i+1,end);
            p1 = matPool(i,1:end-2);
            p2 = matPool(i+1,1:end-2);
        else
            p1 = matPool(i,1:end-1);
            p2 = matPool(i+1,1:end-1);
        end

        [o1, o2] = inter.sbxCrossover(p1, p2, cross_params, bounds);   

        % mutation
        o1 = inter.polynomialMutation(o1, mut_params, bounds);
        o2 = inter.polynomialMutation(o2, mut_params, bounds);

        if isinter == true
            off(i,1:end-2) = o1;
            off(i,end) = part1;
            off(i+1,1:end-2) = o2;
            off(i+1,end) = part2;
        else
            off(i,1:end-1) = o1;
            off(i+1,1:end-1) = o2;
        end

    end
end




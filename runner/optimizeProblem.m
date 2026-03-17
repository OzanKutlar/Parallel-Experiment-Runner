function [best, error, runtime, convergence_array] = optimizeProblem()
    
    % OPTIMIZATION PROBLEM DEFINITION ----------
    op = struct;
    op.dim = 2;     % dimensionality of the problem
    op.maxFE = 5000 * op.dim;   % max function evaluations, this is also set in "selectOptimizationProblem" in case there is a default one for that problem 
    op.bbob_iid = 5;   % only for Black-Box Optimization Benchmark 2009 (BBOB), different instances for shifting the optimum in the landscape (from 1 to 15 according to COCO)
    op = selectOptimizationProblem("BBOB_1", op); % "sphere", "rosenbrock", "rastrigin", "ackley", "griewank", "schwefel", "zakharov", "dixon-price", "levy", "michalewicz", "styblinski–tang"

    % -- WHAT TO RUN
    run = "ga_generational"; % "ga_generational", "ga_steadyState", "bbbc", "es_adaptive", "es_oneFifth"

    % ALGORITHM PARAMETERS ---------

    algo = struct;
    algo.pop_size = 10*op.dim;    % population size
    algo.verbose = true;   % print log
    algo.plotting = true;  % draw plot
    algo.refresh = 0.05;

    if startsWith(run,"ga_")
        algo.crossover = struct;
        algo.crossover.p_c = 1;         % probability of crossover
        algo.crossover.eta_c = 20;      % eta of sbx crossover
        algo.mutation = struct;
        algo.mutation.p_m = 0.5;        % probability of mutation
        algo.mutation.eta_m = 20;       % eta of polynomial mutation
    elseif startsWith(run,"es_")
        algo.lambda = algo.pop_size;    % offspring size
        algo.mu = floor(algo.lambda/4);                    % population / parent / mating pool size / µ --> if set to 1 (µ=1), it will run (1+λ)ES or (1,λ)ES based on the survival scheme
        algo.sigma = (op.bounds(2)-op.bounds(1))/(2*sqrt(op.dim));       % initial mutation strength
        algo.survival = struct;     
        algo.survival.schema = "(µ,λ)"; % type of survival scheme, can be "(µ+λ)", "(µ,λ)"
    end

    switch run
        case "ga_generational"
            algo.off_size = 100;            % offspring population size
            algo.survival = struct;     
            algo.survival.schema = "α";     % type of survival scheme, can be "(µ+λ)", "(µ,λ)", "α"
            algo.survival.alpha = 40;       % percentage of elites to be preserved in α-scheme only
            [best, error, runtime, convergence_array] = run_RGA_generational(op, algo);
        
        case "ga_steadyState"
            [best, error, runtime, convergence_array] = run_RGA_steady_state(op, algo);

        case "bbbc"
            algo.fasten = 1;    % speed of convergence -- coefficient of reduction of extent of mutation
            algo.survival = struct;     
            algo.survival.schema = "replacement"; % type of survival scheme, can be "replacement", "non-elitist"
            [best, error, runtime, convergence_array] = run_BBBC(op, algo);

        case "es_adaptive"
            [best, error, runtime, convergence_array] = run_ES_SelfAdaptive(op, algo);
        
        case "es_oneFifth"
            [best, error, runtime, convergence_array] = run_ES_OneFifth(op, algo);
    end

    %Shared.plotConvergence(convergence_array, op.dim, op.opt_known);
    Shared.plotConvergenceLOG(convergence_array, op.dim, op.opt_known);
end
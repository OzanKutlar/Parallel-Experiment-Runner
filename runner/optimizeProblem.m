function [best, error, runtime, convergence_array] = optimizeProblem()
    
    % OPTIMIZATION PROBLEM DEFINITION ----------
    op              = struct;
    op.dim          = 40;     % dimensionality of the problem
    op.maxFE        = 5000 * op.dim;   % max function evaluations, this is also set in "selectOptimizationProblem" in case there is a default one for that problem 
    op.bbob_iid     = 1;   % only for Black-Box Optimization Benchmark 2009 (BBOB), different instances for shifting the optimum in the landscape (from 1 to 15 according to COCO)
    op              = selectOptimizationProblem("BBOB_1", op); % "sphere", "rosenbrock", "rastrigin", "ackley", "griewank", "schwefel", "zakharov", "dixon-price", "levy", "michalewicz", "styblinski–tang"

    % -- WHAT TO RUN
    run = "ga_generational"; % "ga_generational", "ga_steadyState", "bbbc", "es_adaptive", "es_oneFifth", "misega_generational", "misega_steadyState"

    % ALGORITHM PARAMETERS ---------
    algo            = struct;    
    algo.verbose    = false;   % print log
    algo.plotting   = false;  % draw plot
    algo.refresh    = 0.05;

    switch run
        % SETTINGS FOR GENERATIONAL REAL-CODED GENETIC ALGORITHM -----------------
        case "ga_generational"
            algo.pop_size           = 640;           % population size
            algo.crossover          = struct;
            algo.crossover.p_c      = 0.9;          % probability of crossover
            algo.crossover.eta_c    = 20;           % eta of sbx crossover
            algo.mutation           = struct;
            algo.mutation.p_m       = 1/op.dim;     % probability of mutation
            algo.mutation.eta_m     = 20;           % eta of polynomial mutation
            algo.off_size           = algo.pop_size;            % offspring population size
            algo.survival           = struct;     
            algo.survival.schema    = "α";     % type of survival scheme, can be "(µ+λ)", "(µ,λ)", "α"
            algo.survival.alpha     = 40;       % percentage of elites to be preserved in α-scheme only
            [best, error, runtime, convergence_array] = run_RGA_generational(op, algo);
        
        % SETTINGS FOR STEADY-STATE REAL-CODED GENETIC ALGORITHM -----------------
        case "ga_steadyState"
            algo.pop_size           = 10*op.dim;           % population size
            algo.crossover          = struct;
            algo.crossover.p_c      = 0.9;          % probability of crossover
            algo.crossover.eta_c    = 20;           % eta of sbx crossover
            algo.mutation           = struct;
            algo.mutation.p_m       = 1/op.dim;     % probability of mutation
            algo.mutation.eta_m     = 20;           % eta of polynomial mutation
            [best, error, runtime, convergence_array] = run_RGA_steady_state(op, algo);
        
        % SETTINGS FOR BIG BANG-BIG CRUNCH ALGORITHM -----------------
        case "bbbc"
            algo.pop_size           = 10*op.dim;           % population size
            algo.fasten             = 1;    % speed of convergence -- coefficient of reduction of extent of mutation
            algo.survival           = struct;     
            algo.survival.schema    = "replacement"; % type of survival scheme, can be "replacement" (1+λ), "non-elitist" (1,λ)
            [best, error, runtime, convergence_array] = run_BBBC(op, algo);
        
        % SETTINGS FOR EVOLUTIONARY STRATEGY WITH SELF ADAPTATION -----------------
        case "es_adaptive"
            algo.pop_size           = 10*op.dim;               % population size
            algo.lambda             = algo.pop_size;    % offspring size
            algo.mu                 = floor(algo.lambda/4);                    % population / parent / mating pool size / µ --> if set to 1 (µ=1), it will run (1+λ)ES or (1,λ)ES based on the survival scheme
            algo.sigma              = (op.bounds(2)-op.bounds(1))/(2*sqrt(op.dim));       % initial mutation strength
            algo.survival           = struct;     
            algo.survival.schema    = "(µ,λ)"; % type of survival scheme, can be "(µ+λ)", "(µ,λ)"
            [best, error, runtime, convergence_array] = run_ES_SelfAdaptive(op, algo);
        
        % SETTINGS FOR EVOLUTIONARY STRATEGY WITH 1/5 RULE ADAPTATION -----------------
        case "es_oneFifth"
            algo.pop_size           = 10*op.dim;               % population size
            algo.lambda             = algo.pop_size;    % offspring size
            algo.mu                 = floor(algo.lambda/4);                    % population / parent / mating pool size / µ --> if set to 1 (µ=1), it will run (1+λ)ES or (1,λ)ES based on the survival scheme
            algo.sigma              = (op.bounds(2)-op.bounds(1))/(2*sqrt(op.dim));       % initial mutation strength
            algo.survival           = struct;     
            algo.survival.schema    = "(µ,λ)"; % type of survival scheme, can be "(µ+λ)", "(µ,λ)"
            [best, error, runtime, convergence_array] = run_ES_OneFifth(op, algo);

        % SETTINGS FOR MIXED-SELECTION GENERATIONAL REAL-CODED GENETIC ALGORITHM -----------------
        case "misega_generational"
            algo.selection_methods  = {"tournament","rank","sus","truncation"};
            algo.partition_size     = 4*op.dim;    % partition size
            algo.crossover          = struct;
            algo.crossover.p_c      = 0.9;          % probability of crossover
            algo.crossover.eta_c    = 20;           % eta of sbx crossover
            algo.mutation           = struct;
            algo.mutation.p_m       = 1/op.dim;     % probability of mutation
            algo.mutation.eta_m     = 20;           % eta of polynomial mutation
            algo.recombination_mode = "inter";     % "intra", "inter"
            algo.mixed_modality     = "restart";    % "uniform", "adaptive", "restart"
            algo.survival           = struct;     
            algo.survival.schema    = "α";     % type of survival scheme, can be "(µ+λ)", "(µ,λ)", "α"
            algo.survival.alpha     = 40;       % percentage of elites to be preserved in α-scheme only
            [best, error, runtime, convergence_array] = run_MISEGA_generational(op, algo);
        
        % SETTINGS FOR MIXED-SELECTION STEADY-STATE REAL-CODED GENETIC ALGORITHM -----------------
        case "misega_steadyState"
            algo.selection_methods  = {"tournament","rank","sus","truncation"};
            algo.partition_size     = 4*op.dim;    % partition size
            algo.crossover          = struct;
            algo.crossover.p_c      = 0.9;          % probability of crossover
            algo.crossover.eta_c    = 20;           % eta of sbx crossover
            algo.mutation           = struct;
            algo.mutation.p_m       = 1/op.dim;     % probability of mutation
            algo.mutation.eta_m     = 20;           % eta of polynomial mutation
            algo.recombination_mode = "intra";     % "intra", "inter"
            algo.mixed_modality     = "adaptive";    % "uniform", "adaptive", "restart"
            [best, error, runtime, convergence_array] = run_MISEGA_steady_state(op, algo);
    end

    inter.plotConvergenceLOG(convergence_array, op.dim, op.opt_known);
end
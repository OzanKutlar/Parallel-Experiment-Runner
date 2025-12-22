function [best, error, runtime, convergence_array] = optimizeProblem()
    
    % OPTIMIZATION PROBLEM DEFINITION ----------
    op = struct;
    op.dim = 2;     % dimensionality of the problem
    op.maxFE = 5000 * op.dim;   % max function evaluations, this is also set in "selectOptimizationProblem" in case there is a default one for that problem 
    op = selectOptimizationProblem("CEC2008_5", op); % "sphere", "rosenbrock", "rastrigin", "ackley", "griewank", "schwefel", "zakharov", "dixon-price", "levy", "michalewicz", "styblinski–tang"

    % ALGORITHM PARAMETERS ----------

    run = "ga"; % "ga", "steady_state", "bbbc", "es"

    algo = struct;
    algo.pop_size = 100;    % population size
    if strcmp(run,"ga") || strcmp(run,"steady_state") 
        algo.crossover = struct;
        algo.crossover.p_c = 1;         % probability of crossover
        algo.crossover.eta_c = 20;      % eta of sbx crossover
        algo.mutation = struct;
        algo.mutation.p_m = 0.5;        % probability of mutation
        algo.mutation.eta_m = 20;       % eta of polynomial mutation
    end
    algo.verbose = true;   % print log
    algo.plotting = true;  % draw plot
    algo.refresh = 0.05;
    
    switch run
        case "ga"
            algo.off_size = 100;            % offspring population size
            algo.survival = struct;     
            algo.survival.schema = "(µ+λ)"; % type of survival scheme, can be "(µ+λ)", "(µ,λ)", "α"
            algo.survival.alpha = 40;       % percentage of elites to be preserved in α-scheme only
            [best, error, runtime, convergence_array] = run_RGA_generational(op, algo);
        
        case "steady_state"
            [best, error, runtime, convergence_array] = run_RGA_steady_state(op, algo);

        case "bbbc"
            algo.fasten = 1;    % speed of convergence -- coefficient of reduction of extent of mutation
            algo.survival = struct;     
            algo.survival.schema = "non-elitist"; % type of survival scheme, can be "replacement", "non-elitist"
            [best, error, runtime, convergence_array] = run_BBBC(op, algo);

        case "es"
            algo.pop_size = 30;     % population / parent / mating pool size / µ --> if set to 1 (µ=1), it will run (1+λ)ES or (1,λ)ES based on the survival scheme
            algo.off_size = 100;    % offspring size
            algo.sigma = 0.2;       % initial mutation strength
            algo.tau = 1/sqrt(2*op.dim);                % local learning rate
            algo.tau_prime = 1/sqrt(2*sqrt(op.dim));    % global learning rate
            algo.survival = struct;     
            algo.survival.schema = "(µ+λ)"; % type of survival scheme, can be "(µ+λ)", "(µ,λ)"
            [best, error, runtime, convergence_array] = run_ES(op, algo);
    end

    Shared.plotConvergence(convergence_array);
end
% Class containing functions shared by every algorithm
classdef Shared
methods (Static)

    
%% Plot the population, the true optimum/optima, and the current best
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population
% - best: struct containing information of the current best solution:
%   - .point: a matrix 1xd of a point in d dimension representing the current best 
%   - .fit: the fitness of the current best
% - op: a struct containing information about the optimization problem
%   - .dim: problem dimensionality
%   - .opt: a matrix mxd points in d dimension representing the m true optima in the search space
%   - .opt_known: a boolean flag set to true if the optimum/optima is/are known
%   - .bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
% - isNew: a flag set to true when this is the first figure of the animation, for visualization purposes only
function [] = plotPopulation(pop, best, op, isNew)
    
    if isNew == true
        f = figure;
        set(f,'WindowStyle','Docked');
    end
    
    switch op.dim
        case 1
            plot(pop(:,1),0,'bo');
        case 2
            plot(pop(:,1),pop(:,2),'bo');
        otherwise
            plot3(pop(:,1),pop(:,2),pop(:,3),'bo');
    end
    hold on;
    grid on;

    switch op.dim
        case 1
            plot(best.point(1),0,'go','LineWidth',10);
        case 2
            plot(best.point(1),best.point(2),'go','LineWidth',10);
        otherwise
            plot3(best.point(1),best.point(2),best.point(3),'go','LineWidth',10);
    end

    if op.opt_known == true
        switch op.dim
            case 1
                plot(op.opt(:,1), 0,'r+'); %optimum
            case 2
                plot(op.opt(:,1), op.opt(:,2),'r+'); %optimum
            otherwise
                plot3(op.opt(:,1), op.opt(:,2), op.opt(:,3),'r+'); %optimum
        end
    end

    switch op.dim
        case 1
            xlim(op.bounds);
        case 2
            xlim(op.bounds);
            ylim(op.bounds);
        otherwise
            xlim(op.bounds);
            ylim(op.bounds);
            zlim(op.bounds);
    end
    
    hold off;
end

%% Draw the convergence plot at the end of execution
% Input
% - convergence_array: an array ix1 containing all the best fitness for each iteration to check convergence
function [] = plotConvergence(convergence_array)
    f = figure;
    set(f,'WindowStyle','Docked');
    plot(convergence_array);
    xlabel("Iterations");
    ylabel("Best Fitness");
    title("Convergence Plot");
end

%% Initialize random population with uniform distribution in the search space
% Input
% - n: desired population size
% - d: problem dimensionality
% - bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
% Output
% - pop: a matrix nx(d+1) of n points in d dimensions representing the newly generated population -- the last column will contain the fitness value
function [pop] = initializeRandomPopulation(n, d, bounds)
    
    % generate population within bounds
    pop = (bounds(2)-bounds(1)) * rand(n,d) + bounds(1);

    % the last column will be the fitness value
    pop(:,d+1) = 0; 
end
    
%% Evaluate a given population
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population
% - obj_fun: handler of the objective function
% - maxFE: number of function evaluation budget before evaluation
% Output
% - pop: the updated population with last column (i.e., d+1) having the newly calculated fitness value
% - maxFE: number of function evaluation budget after evaluation
function [pop, maxFE] = evaluate(pop, obj_fun, maxFE)
    for i=1:size(pop,1)
        pop(i,end) = obj_fun(pop(i,1:end-1));     % store objective function in the last column
        maxFE = maxFE - 1;            
    end
end

%% K-Way Tournament Selection
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population
% - k: number of individuals to compete at the same time (usually used as k=2 for binary tournament selection)
% - pop_size: original population size
% - n: number of desired offspring (increase selection pressure)
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - matPool: a matrix nx(d+1) of n points in d dimensions representing the mating pool (i.e., the parents)
function matPool = kWayTournamentSelection(pop, k, pop_size, n, isMin)    
    d = size(pop,2);
    matPool = zeros(n,d);
    for i=1:n
        idx = ceil((pop_size)*rand(k,1));
        teams = pop(idx,:);
        if isMin
            [~, winner_index] = min(teams(:,end));
        else
            [~, winner_index] = max(teams(:,end));
        end
        matPool(i,:) = teams(winner_index,:);
    end
end

%% Simulated Binary Crossover (SBX)
% Input
% - p1: a point 1xd representing the first parent
% - p2: a point 1xd representing the second parent
% - cross_params: a struct containing the parameters of the sbx crossover with the following attributes:
%   - .p_c: probability of crossover
%   - .eta_c: eta parameter of sbx (higher values will generate offspring closer to their parents)
% - bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
% Output
% - o1: a point 1xd representing the first offspring
% - o2: a point 1xd representing the second offspring
function [o1,o2] = sbxCrossover(p1, p2, cross_params, bounds)

    o1 = p1;
    o2 = p2;
    if rand() <= cross_params.p_c
        k = rand(1, size(p1,2));  % one random value per dimension
        beta = zeros(size(k));
        
        for j = 1:length(k)
            if k(j) <= 0.5
                beta(j) = (2 * k(j))^(1 / (cross_params.eta_c + 1));
            else
                beta(j) = (1 / (2 * (1 - k(j))))^(1 / (cross_params.eta_c + 1));
            end
        end
        
        o1 = 0.5 * ((p1 + p2) - beta .* (p2 - p1));
        o2 = 0.5 * ((p1 + p2) + beta .* (p2 - p1));
        
        % Apply bounds per dimension
        o1 = max(min(o1, bounds(2)), bounds(1));
        o2 = max(min(o2, bounds(2)), bounds(1));
        
    end
end

%% Polynomial Mutation
% Input
% - original: a point 1xd representing the original individual
% - mut_params: a struct containing the parameters of the polynomial mutation with the following attributes:
%   - .p_c: probability of mutation
%   - .eta_c: eta parameter (higher values will mutate the individual closer to its original position)
% - bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension)
% Output
% - mutated: a point 1xd representing the mutated individual
function [mutated] = polynomialMutation(original, mut_params, bounds)
    mutated = original;
    if rand() <= mut_params.p_m
        r = rand(1, size(original,2));  % one random value per dimension
        delta = zeros(size(r));
        for j = 1:length(r)
            if r < 0.5
                delta(j) = (2.0*r(j))^(1.0/(mut_params.eta_m+1))-1.0;
            else
               delta(j) = 1.0-(2.0*(1-r(j)))^(1.0/(mut_params.eta_m+1));
            end
        end
        mutated = original + (bounds(2)-bounds(1))*delta;
        
        % Apply bounds per dimension
        mutated = max(min(mutated, bounds(2)), bounds(1));
    end
end

%% Apply Gaussian mutation to a point to generate offspring
% Input:
% - point: an array 1xd of a single point in d dimensions representing the point to be mutated
% - n: number of desired offspring
% - g: current iteration
% - bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension) 
% Output
% - pop: a matrix nxd of n points in d dimensions representing the newly generated offspring population
function pop = gaussianMutation(point, n, g, bounds)
    
    d = size(point,2);  % dimensionality

    % Scale and shift to [-1, 1]
    scaledNumbers = Shared.getNormalizedSetOfPoints(n, d);    % generate normal distribuition of n numbers between [-1 and 1]

    pop = zeros(n,d+1);

    for i=1:n
        pop(i,1:end-1) = point + ((bounds(2)-bounds(1))*scaledNumbers(i,:))/g; % mutate
        pop(i,1:end-1) = max(min(pop(i,1:end-1), bounds(2)), bounds(1));       % saturate values not to exceed the bounds
    end
end

%% Generate Normal Distribution of points and scale it to [-1, +1]
% Input
% - n: number of desired points
% - d: dimensionality of the points
% Output
% - scaledNumbers: an array nxd of n points in d dimensions normally distribuited between [-1, +1]
function [scaledNumbers] = getNormalizedSetOfPoints(n, d)
    mu = 0;     % fixed in between the range
    sigma = 1;  % fixed
    % Step 1: Generate normally distributed random numbers in [-∞,+∞]
    randomNumbers = normrnd(mu, sigma, [n, d]);
    
    % Step 2: Normalize the numbers to the range [-1, 1]
    minVal = min(randomNumbers); % Find the minimum value
    maxVal = max(randomNumbers); % Find the maximum value
    
    % Normalize to [0, 1]
    normalizedNumbers = (randomNumbers - minVal) ./ (maxVal - minVal);
    
    % Scale and shift to [-1, 1]
    scaledNumbers = 2 * normalizedNumbers - 1;
end

%% Apply Gaussian mutation to a set of points (with self-adaptive mutation strength) to generate offspring
% Input:
% - pop: a matrix µx(d+1) of µ points in d dimensions representing the parents -- the last column will contain the fitness value
% - sigma_pop: a matrix µxd of µ values of mutation strengths (σ) in d dimensions associated to each individual in 'pop'
% - lambda: number of desired offspring
% - tau_prime: local learning rate
% - tau: global learning rate
% - bounds: a matrix 1x2 having as first element lower bound and second element upper bound (assuming it is the same for each dimension) 
% Output
% - off: a matrix λxd of λ points in d dimensions representing the newly generated offspring population
function [off, sigma_off] = gaussianMutationWithSigmaSelfAdaptation(pop, sigma_pop, lambda, tau_prime, tau, bounds)
    [mu,d] = size(pop);
    off = zeros(lambda, d);
    sigma_off = zeros(lambda, d-1);

    for i = 1:lambda
        % choose a parent at random
        idx_p = randi(mu);

        % Step-size adaptation (log-normal)
        sigma_i = sigma_pop(idx_p,:) .* exp(tau_prime * randn * ones(1,d-1) + tau * randn(1,d-1));

        % mutate the parent
        off(i,1:end-1) = pop(idx_p,1:end-1) + sigma_i .* randn(1,d-1);

        % enforce bounds
        off(i,1:end-1) = max(min(off(i,1:end-1), bounds(2)), bounds(1));

        sigma_off(i,:) = sigma_i;
    end
end

%% Replace worst individuals of the population with the offspring, if better (usually for offspring size smaller than population size)
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population, last column is fitness value
% - off: a matrix mx(d+1) of m points in d dimensions representing the offspring, last column is fitness value, with m≪n
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - pop: a matrix nx(d+1) of n points in d dimensions representing the new population
function [pop] = survival_bestToWorst(pop, off, isMin)
    pop = [pop; off];
    for i=1:size(off,1)
        [~, worst] = Shared.findBestWorst(pop, isMin);
        pop(worst.idx,:) = [];
    end
end

%% Perform α-schema elitist survival
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population, last column is fitness value
% - off: a matrix mx(d+1) of m points in d dimensions representing the offspring, last column is fitness value
% - alpha: percentage of elites from 'pop' that will survive
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - pop: a matrix nx(d+1) of n points in d dimensions representing the new population
% - indices: a matrix nx1 containing the sorted indices of the original population (used for references in case another external data structure is linked to each individual)
function [pop, indices] = survival_elitist_alpha(pop, off, alpha, isMin)
    
    [n, d] = size(pop); 

    % calculate amounts for each population
    mu = round((alpha*n)/100);
    lambda = n - mu;

    % sort population
    if isMin
        [pop, indices_pop] = sortrows(pop,d,'ascend');
        [off, indices_off] = sortrows(off,d,'ascend');
    else
        [pop, indices_pop] = sortrows(pop,d,'descend');
        [off, indices_off] = sortrows(off,d,'descend');
    end

    % merge populations
    pop = [pop(1:mu,:); off(1:lambda,:)];
    indices = [indices_pop(1:mu); indices_off(1:lambda)];
end

%% Perform (µ+λ)-schema elitist survival
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population, last column is fitness value
% - off: a matrix nx(d+1) of n points in d dimensions representing the offspring, last column is fitness value
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - pop: a matrix nx(d+1) of n points in d dimensions representing the new population
% - indices: a matrix nx1 containing the sorted indices of the original population (used for references in case another external data structure is linked to each individual)
function [pop, indices] = survival_elitist_muPlusLambda(pop, off, isMin)
        
        [mu, d] = size(pop); 

        % merge populations
        pop = [pop; off];
        
        % sort population
        if isMin == true    
            [pop, indices] = sortrows(pop,d,'ascend');     % minimization
        else    
            [pop, indices] = sortrows(pop,d,'descend');    % maximization
        end
        
        % remove poor individuals
        pop(mu+1:end,:) = [];
        indices(mu+1:end) = [];
        
end

%% Perform (µ,λ)-schema non-elitist survival
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population, last column is fitness value
% - off: a matrix nx(d+1) of n points in d dimensions representing the offspring, last column is fitness value
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - pop: a matrix nx(d+1) of n points in d dimensions representing the new population
% - indices: a matrix nx1 containing the sorted indices of the original population (used for references in case another external data structure is linked to each individual)
function [pop, indices] = survival_nonElitist(pop, off, isMin)
    
    [mu, d] = size(pop); 
    
    % sort population
    if isMin == true    
        [off, indices] = sortrows(off,d,'ascend');     % minimization
    else    
        [off, indices] = sortrows(off,d,'descend');    % maximization
    end
    
    % remove poor individuals
    pop = [off(1:mu,:)];
    indices(mu+1:end) = [];
end


%% Return the best and worst individual in the population
% Input
% - pop: a matrix nx(d+1) of n points in d dimensions representing the current population
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - best, worst: two structs containing the best and worst individual in 'pop' (respectively) with the following attributes:
%   - .point: an array 1xd representing the point (either best or worst individual) in d dimensions
%   - .fit: fitness of the individual
%   - .idx: index of the individual in 'pop' for cross reference
function [best, worst] = findBestWorst(pop, isMin)
    d = size(pop,2);
    if isMin == true
        [best.fit, best.idx] = min(pop(:,d));
        [worst.fit, worst.idx] = max(pop(:,d));
    else
        [best.fit, best.idx] = max(pop(:,d));
        [worst.fit, worst.idx] = min(pop(:,d));
    end
    best.point = pop(best.idx,1:d-1);
    worst.point = pop(worst.idx,1:d-1);
end

%% Utility function to update the all time best solution at each iteration
% Input
% - best, pop_best: two structs containing the all time best and current best individual in the current population (respectively) with the following attributes:
%   - .point: an array 1xd representing the point (either best or worst individual) in d dimensions
%   - .fit: fitness of the individual
%   - .idx: index of the individual in 'pop' for cross reference
% - isMin: a boolean flag set to true if the problem is minimization, false if maximization
% Output
% - best: the updated all time best individual
function [best] = updateBest(best, pop_best, isMin)
    if (isMin && best.fit > pop_best.fit) || (~isMin && best.fit < pop_best.fit)
        best = pop_best;
    end
end

%% Calculate error between the true optima and the best retrieved solution  
function [error] = calculateError(op, best)
    
    error = struct;
    if op.opt_known == true
        if size(op.opt,1) == 1
            % single mode
            error.src_space = norm(op.opt - best.point);
            error.obj_space = abs(op.fun(op.opt) - best.fit);
        else
            % multimodal to any of the optima
            [error.src_space, index] = min(sqrt(sum((op.opt - best.point).^2, 2)));
            error.obj_space = abs(op.fun(op.opt(index,:)) - best.fit);
        end
    else
        error.src_space = -1;
        error.obj_space = -1;
    end
end

end
end
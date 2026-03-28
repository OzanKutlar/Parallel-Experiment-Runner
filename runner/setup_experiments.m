% all settings
fun = {"BBOB_1","BBOB_2","BBOB_3","BBOB_4","BBOB_5","BBOB_6","BBOB_7","BBOB_8","BBOB_9","BBOB_10",...
        "BBOB_11","BBOB_12","BBOB_13","BBOB_14","BBOB_15","BBOB_16","BBOB_17","BBOB_18","BBOB_19","BBOB_20", ...
        "BBOB_21","BBOB_22","BBOB_23","BBOB_24"};
dim = [2,5,10,20,40,80,100];
inst = 15;
m_val = {@(d)4*d, @(d)8*d, @(d)16*d}; 
recomb = {"intra", "inter"};
modality = {"uniform", "adaptive", "restart"};

% 105840 experiments

count = 1;

fprintf("SINGLE GENERATIONAL:\n");
for f=1:size(fun,2)
    for d=1:size(dim,2)
        for p=1:size(m_val,2)
            for i=1:1:inst
                op = struct;
                op.dim = dim(d);  
                op.maxFE = 1e5 * op.dim;
                op.bbob_iid = i;
                op = selectOptimizationProblem(fun{f}, op);
                
                algo = struct;
                algo.verbose = false; 
                algo.plotting = false;
                algo.refresh = 0.05;
    
                algo.pop_size           = m_val{p}(4*op.dim);           % population size
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
                %[best, error, runtime, convergence_array] = run_RGA_generational(op, algo);
                
                fprintf("SINGLE GENERATIONAL %d) Fun %s-%dD, Instance: %d, PopSize: %d\n", count, fun{f}, op.dim, i, algo.pop_size);
                count = count + 1;
    
            end
        end
    end
end
fprintf("--------------\n\n");

fprintf("MIXED GENERATIONAL:\n");
for f=1:size(fun,2)
    for d=1:size(dim,2)
        for p=1:size(m_val,2)
            for i=1:1:inst
                for r=1:1:size(recomb,2)
                    for m=1:1:size(modality,2)
                        op = struct;
                        op.dim = dim(d);  
                        op.maxFE = 1e5 * op.dim;
                        op.bbob_iid = i;
                        op = selectOptimizationProblem(fun{f}, op);
                        
                        algo = struct;
                        algo.verbose = false; 
                        algo.plotting = false;
                        algo.refresh = 0.05;
            
                        algo.selection_methods  = {"tournament","rank","sus","truncation"};
                        algo.partition_size     = m_val{p}(op.dim);    % partition size
                        algo.crossover          = struct;
                        algo.crossover.p_c      = 0.9;          % probability of crossover
                        algo.crossover.eta_c    = 20;           % eta of sbx crossover
                        algo.mutation           = struct;
                        algo.mutation.p_m       = 1/op.dim;     % probability of mutation
                        algo.mutation.eta_m     = 20;           % eta of polynomial mutation
                        algo.recombination_mode = recomb{r};     % "within_partition", "shared"
                        algo.mixed_modality     = modality{m};    % "uniform", "adaptive", "restart"
                        algo.survival           = struct;     
                        algo.survival.schema    = "α";     % type of survival scheme, can be "(µ+λ)", "(µ,λ)", "α"
                        algo.survival.alpha     = 40;       % percentage of elites to be preserved in α-scheme only
                        %[best, error, runtime, convergence_array] = run_MISEGA_generational(op, algo);
                        
                        fprintf("MIXED GENERATIONAL %d) %s - %s\tFun %s-%dD, Instance: %d, PopSize: %d\n", count, recomb{r}, modality{m}, fun{f}, op.dim, i, algo.partition_size*4);
                        count = count + 1;
                    end
                end            
            end
        end
    end
end
fprintf("--------------\n\n");

fprintf("SINGLE STEADY STATE:\n");
for f=1:size(fun,2)
    for d=1:size(dim,2)
        for p=1:size(m_val,2)
            for i=1:1:inst
                op = struct;
                op.dim = dim(d);  
                op.maxFE = 1e5 * op.dim;
                op.bbob_iid = i;
                op = selectOptimizationProblem(fun{f}, op);
                
                algo = struct;
                algo.verbose = false; 
                algo.plotting = false;
                algo.refresh = 0.05;
    
                algo.pop_size           = m_val{p}(4*op.dim);           % population size
                algo.crossover          = struct;
                algo.crossover.p_c      = 0.9;          % probability of crossover
                algo.crossover.eta_c    = 20;           % eta of sbx crossover
                algo.mutation           = struct;
                algo.mutation.p_m       = 1/op.dim;     % probability of mutation
                algo.mutation.eta_m     = 20;           % eta of polynomial mutation
                %[best, error, runtime, convergence_array] = run_RGA_steady_state(op, algo);
                
                fprintf("SINGLE STEADY STATE %d) Fun %s-%dD, Instance: %d, PopSize: %d\n", count, fun{f}, op.dim, i, algo.pop_size);
                count = count + 1;
    
            end
        end
    end
end
fprintf("--------------\n\n");

fprintf("MIXED STEADY STATE:\n");
for f=1:size(fun,2)
    for d=1:size(dim,2)
        for p=1:size(m_val,2)
            for i=1:1:inst
                for r=1:1:size(recomb,2)
                    for m=1:1:size(modality,2)
                        op = struct;
                        op.dim = dim(d);  
                        op.maxFE = 1e5 * op.dim;
                        op.bbob_iid = i;
                        op = selectOptimizationProblem(fun{f}, op);
                        
                        algo = struct;
                        algo.verbose = false; 
                        algo.plotting = false;
                        algo.refresh = 0.05;
            
                        algo.selection_methods  = {"tournament","rank","sus","truncation"};
                        algo.partition_size     = m_val{p}(op.dim);    % partition size
                        algo.crossover          = struct;
                        algo.crossover.p_c      = 0.9;          % probability of crossover
                        algo.crossover.eta_c    = 20;           % eta of sbx crossover
                        algo.mutation           = struct;
                        algo.mutation.p_m       = 1/op.dim;     % probability of mutation
                        algo.mutation.eta_m     = 20;           % eta of polynomial mutation
                        algo.recombination_mode = recomb{r};     % "within_partition", "shared"
                        algo.mixed_modality     = modality{m};    % "uniform", "adaptive", "restart"
                        %[best, error, runtime, convergence_array] = run_MISEGA_steady_state(op, algo);
                        
                        fprintf("MIXED STEADY STATE %d) %s - %s\tFun %s-%dD, Instance: %d, PopSize: %d\n", count, recomb{r}, modality{m}, fun{f}, op.dim, i, algo.partition_size*4);
                        count = count + 1;
                    end
                end            
            end
        end
    end
end
fprintf("--------------\n\n");




% % all settings
% fun = {"BBOB_1","BBOB_2","BBOB_3","BBOB_4","BBOB_5","BBOB_6","BBOB_7","BBOB_8","BBOB_9","BBOB_10",...
%         "BBOB_11","BBOB_12","BBOB_13","BBOB_14","BBOB_15","BBOB_16","BBOB_17","BBOB_18","BBOB_19","BBOB_20", ...
%         "BBOB_21","BBOB_22","BBOB_23","BBOB_24"};
% dim = [2,5,10,20,40,100];
% inst = 15;
% bbbc_survival = ["replacement","non-elitist"];
% es_survival = ["(µ+λ)","(µ,λ)"];
% es_mu = {@(lambda)1, @(lambda)floor(lambda/4)}; 
% 
% count = 1;
% 
% % for BBBC
% fprintf("BBBC:\n");
% for f=1:size(fun,2)
%     for d=1:size(dim,2)
%         for s=1:size(bbbc_survival,2)
%             for i=1:1:inst
%                 op = struct;
%                 op.dim = dim(d);  
%                 op.maxFE = 1e5 * op.dim;
%                 op.bbob_iid = i;
%                 op = selectOptimizationProblem(fun{f}, op);
% 
%                 algo = struct;
%                 algo.pop_size = 10*op.dim;
%                 algo.verbose = false; 
%                 algo.plotting = false;
%                 algo.refresh = 0.05;
%                 algo.survival = struct;     
%                 algo.survival.schema = bbbc_survival(s);
%                 %[best, error, runtime, convergence_array] = run_BBBC(op, algo);
% 
%                 fprintf("%d) Fun %s-%dD, Instance: %d, Survival: %s\n", count, fun{f}, op.dim, i, algo.survival.schema);
%                 count = count + 1;
%             end
%         end
%     end
% end
% fprintf("--------------\n\n");
% 
% % for ES 1/5
% fprintf("ES 1/5:\n");
% for f=1:size(fun,2)
%    for d=1:size(dim,2)
%         for s=1:size(es_survival,2)
%             for m=1:size(es_mu,2)
%                 for i=1:1:inst
%                     op.dim = dim(d);  
%                     op.maxFE = 1e5 * op.dim;
%                     op.bbob_iid = i;
%                     op = selectOptimizationProblem(fun{f}, op);
% 
%                     algo.lambda = 10*op.dim;
%                     algo.mu = es_mu{m}(algo.lambda);
%                     algo.sigma = (op.bounds(2)-op.bounds(1))/(2*sqrt(op.dim)); 
%                     algo.survival = struct;     
%                     algo.survival.schema = es_survival(s);
%                     algo.verbose = false; 
%                     algo.plotting = false;
%                     algo.refresh = 0.05;
% 
%                     %[best, error, runtime, convergence_array] = run_ES_OneFifth(op, algo);
%                     fprintf("%d) Fun %s-%dD, Instance: %d, µ: %d, λ: %d, Survival: %s, σ: %f\n", count, fun{f}, op.dim, i, algo.mu, algo.lambda, algo.survival.schema, algo.sigma);
%                     count = count + 1;
%                 end
%             end
%         end  
%     end
% end
% fprintf("--------------\n\n");
% 
% % for ES Self Adaptive
% fprintf("ES Self Adaptive:\n");
% for f=1:size(fun,2)
%    for d=1:size(dim,2)
%         for s=1:size(es_survival,2)
%             for m=1:size(es_mu,2)
%                 for i=1:1:inst
%                     op.dim = dim(d);  
%                     op.maxFE = 1e5 * op.dim;
%                     op.bbob_iid = i;
%                     op = selectOptimizationProblem(fun{f}, op);
% 
%                     algo.lambda = 10*op.dim;
%                     algo.mu = es_mu{m}(algo.lambda);
%                     algo.sigma = (op.bounds(2)-op.bounds(1))/(2*sqrt(op.dim)); 
%                     algo.survival = struct;     
%                     algo.survival.schema = es_survival(s);
%                     algo.verbose = false; 
%                     algo.plotting = false;
%                     algo.refresh = 0.05;
% 
%                     %[best, error, runtime, convergence_array] = run_ES_SelfAdaptive(op, algo);
%                     fprintf("%d) Fun %s-%dD, Instance: %d, µ: %d, λ: %d, Survival: %s, σ: %f\n", count, fun{f}, op.dim, i, algo.mu, algo.lambda, algo.survival.schema, algo.sigma);
%                     count = count + 1;
% 
%                 end
%             end
%         end  
%     end
% end
% fprintf("--------------\n\n");
% 
% 
% 
% 
% 

% all settings
fun = ["CEC2013_1","CEC2013_2","CEC2013_3","CEC2013_4","CEC2013_5","CEC2013_6","CEC2013_7","CEC2013_8","CEC2013_9","CEC2013_10","CEC2013_11","CEC2013_12","CEC2013_13","CEC2013_14","CEC2013_15"];
dim = [2,25,50,100,500,1000];
pop = [100,500];
n_runs = 25;
bbbc_survival = ["replacement","non-elitist"];
es_survival = ["(µ+λ)","(µ,λ)"];
es_mu = {@(lambda)1}; %START THE EXPERIMENT ONLY WITH µ=1, then when you are done also run es_mu = {@(lambda)round(lambda/5),@(lambda)round(lambda/3),@(lambda)round(lambda/2)};
es_sigma = {@(R,d)R/(20*sqrt(d)), @(R,D)R/(2*sqrt(d)), @(R,D)R/(sqrt(d))};

count = 1;

% for BBBC
fprintf("BBBC:\n");
for f=1:size(fun,2)
    for d=1:size(dim,2)
        for p=1:size(pop,2)
            for s=1:size(bbbc_survival,2)
        
                op = struct;
                op.dim = dim(d);  
                op.maxFE = 0;
                op = selectOptimizationProblem(fun(f), op);
                
                algo = struct;
                algo.pop_size = pop(p);
                algo.verbose = false; 
                algo.plotting = false;
                algo.refresh = 0.05;
                algo.survival = struct;     
                algo.survival.schema = bbbc_survival(s);
                [best, error, runtime, convergence_array] = run_BBBC(op, algo);
                
                fprintf("%d) Fun %s-%dD, Pop Size: %d, Survival: %s\n", count, fun(f), op.dim, algo.pop_size, algo.survival.schema);
                count = count + 1;
            end
        end
    end
end
fprintf("--------------\n\n");

% for ES
fprintf("BBBC:\n");
for f=1:size(fun,2)
    for d=1:size(dim,2)
        for p=1:size(pop,2)
            for s=1:size(es_survival,2)
                for mu=1:size(es_mu,2)
                    for sigma=1:size(es_sigma,2)

                        op = struct;
                        op.dim = dim(d);     
                        op.maxFE = 0;
                        op = selectOptimizationProblem(fun(f), op);
                        
                        algo = struct;
                        algo.off_size = pop(p);
                        algo.pop_size = es_mu{mu}(algo.off_size);
                        algo.verbose = false; 
                        algo.plotting = false;
                        algo.refresh = 0.05;
                        R = op.bounds(2)-op.bounds(1);
                        algo.sigma = es_sigma{sigma}(R,op.dim);
                        algo.tau = 1/sqrt(2*op.dim);
                        algo.tau_prime = 1/sqrt(2*sqrt(op.dim));
                        
                        algo.survival = struct;     
                        algo.survival.schema = es_survival(s);
                        %[best, error, runtime, convergence_array] = run_ES(op, algo);
                        fprintf("%d) Fun %s-%dD, µ: %d, λ: %d, Survival: %s, σ: %f\n", count, fun(f), op.dim, algo.pop_size, algo.off_size, algo.survival.schema, algo.sigma);
                        count = count + 1;

                    end
                end  
            end
        end
    end
end
fprintf("--------------\n\n");






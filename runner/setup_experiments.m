% all settings
fun = {"BBOB_1","BBOB_2","BBOB_3","BBOB_4","BBOB_5","BBOB_6","BBOB_7","BBOB_8","BBOB_9","BBOB_10",...
        "BBOB_11","BBOB_12","BBOB_13","BBOB_14","BBOB_15","BBOB_16","BBOB_17","BBOB_18","BBOB_19","BBOB_20", ...
        "BBOB_21","BBOB_22","BBOB_23","BBOB_24"};
dim = [2,5,10,20,40,80, 100];
inst = 15;
bbbc_survival = ["replacement","non-elitist"];
es_survival = ["(µ+λ)","(µ,λ)"];
es_mu = {@(lambda)1, @(lambda)floor(lambda/4)}; 

count = 1;

% for BBBC
fprintf("BBBC:\n");
for f=1:size(fun,2)
    for d=1:size(dim,2)
        for s=1:size(bbbc_survival,2)
            for i=1:1:inst
                op = struct;
                op.dim = dim(d);  
                op.maxFE = 1e5 * op.dim;
                op.bbob_iid = i;
                op = selectOptimizationProblem(fun{f}, op);
                
                algo = struct;
                algo.pop_size = 10*op.dim;
                algo.verbose = false; 
                algo.plotting = false;
                algo.refresh = 0.05;
                algo.survival = struct;     
                algo.survival.schema = bbbc_survival(s);
                %[best, error, runtime, convergence_array] = run_BBBC(op, algo);
                
                fprintf("%d) Fun %s-%dD, Instance: %d, Survival: %s\n", count, fun{f}, op.dim, i, algo.survival.schema);
                count = count + 1;
            end
        end
    end
end
fprintf("--------------\n\n");

% for ES 1/5
fprintf("ES 1/5:\n");
for f=1:size(fun,2)
   for d=1:size(dim,2)
        for s=1:size(es_survival,2)
            for m=1:size(es_mu,2)
                for i=1:1:inst
                    op.dim = dim(d);  
                    op.maxFE = 1e5 * op.dim;
                    op.bbob_iid = i;
                    op = selectOptimizationProblem(fun{f}, op);
                    
                    algo.lambda = 10*op.dim;
                    algo.mu = es_mu{m}(algo.lambda);
                    algo.sigma = (op.bounds(2)-op.bounds(1))/(2*sqrt(op.dim)); 
                    algo.survival = struct;     
                    algo.survival.schema = es_survival(s);
                    algo.verbose = false; 
                    algo.plotting = false;
                    algo.refresh = 0.05;
                    
                    %[best, error, runtime, convergence_array] = run_ES_OneFifth(op, algo);
                    fprintf("%d) Fun %s-%dD, Instance: %d, µ: %d, λ: %d, Survival: %s, σ: %f\n", count, fun{f}, op.dim, i, algo.mu, algo.lambda, algo.survival.schema, algo.sigma);
                    count = count + 1;
                end
            end
        end  
    end
end
fprintf("--------------\n\n");

% for ES Self Adaptive
fprintf("ES Self Adaptive:\n");
for f=1:size(fun,2)
   for d=1:size(dim,2)
        for s=1:size(es_survival,2)
            for m=1:size(es_mu,2)
                for i=1:1:inst
                    
                    
                    %[best, error, runtime, convergence_array] = run_ES_SelfAdaptive(op, algo);
                    fprintf("%d) Fun %s-%dD, Instance: %d, µ: %d, λ: %d, Survival: %s, σ: %f\n", count, fun{f}, op.dim, i, algo.mu, algo.lambda, algo.survival.schema, algo.sigma);
                    count = count + 1;
            
                end
            end
        end  
    end
end
fprintf("--------------\n\n");






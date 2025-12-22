function data = GetFromServer(ip, port, maxDelay)
    url = sprintf('http://%s:%s', ip, port);

    computerName = getenv('COMPUTERNAME');
    
    % Initial Options
    options = weboptions('HeaderFields', {'ComputerName', computerName}); 

    minDelay = 1;

    delay = round(minDelay + (maxDelay - minDelay) * rand());
    fprintf('Initial delay for %d seconds...\n', delay);
    pause(delay);
    
    while true
            data = webread(url, options);
            
            if isfield(data, 'message')
                fprintf('Server Message: %s\nStopping client.\n', data.message);
                % if exist('selfDestruct.bat', 'file')
                    % !start selfDestruct.bat
                % end
                return;
            end

            fprintf('Received Job ID: %d (%s - %s)\n', data.id, data.algo, data.fun);

            nameOfFile = runExperiment(data);

            uploadFileToServerAsJSON(nameOfFile, url, computerName, data.id);

            delay = round(minDelay + (maxDelay - minDelay) * rand());
            fprintf("Job %d Complete. Cooling down for %d seconds.\n", data.id, delay);
            pause(delay);
    end
end

function fileName = runExperiment(data)
    op = struct;
    op.dim = data.dim;  
    op.maxFE = 0;
    
    op = selectOptimizationProblem(data.fun, op);
    
    algo = struct;
    algo.verbose = false; 
    algo.plotting = false;
    algo.refresh = 0.05;
    algo.survival = struct;     
    algo.survival.schema = data.survival;
    algo.fasten = 1;

    if strcmp(data.algo, 'BBBC')
        algo.pop_size = data.pop_size;
        
        [best, error, runtime, convergence_array] = run_BBBC(op, algo);
        
    elseif strcmp(data.algo, 'ES')
        algo.off_size = data.off_size;
        
        if data.mu_type == 1
            algo.pop_size = 1;
        else
            algo.pop_size = 1; 
        end
        
        R = op.bounds(2) - op.bounds(1);
        
        if data.sigma_type == 1
            algo.sigma = R / (20 * sqrt(op.dim));
        elseif data.sigma_type == 2
            algo.sigma = R / (2 * sqrt(op.dim));
        elseif data.sigma_type == 3
            algo.sigma = R / sqrt(op.dim);
        end
        
        algo.tau = 1/sqrt(2*op.dim);
        algo.tau_prime = 1/sqrt(2*sqrt(op.dim));
        
        [best, error, runtime, convergence_array] = run_ES(op, algo);
    end

    fileName = sprintf('exp-%d.mat', data.id);
    
    save(fileName, 'best', 'error', 'runtime', 'convergence_array', 'op', 'algo');
end

function uploadFileToServerAsJSON(fileName, serverUrl, computerName, dataId)
    filePath = fullfile(pwd, fileName);
    if ~isfile(filePath)
        error('File "%s" does not exist at the specified path.', fileName);
    end

    try
        fid = fopen(filePath, 'rb'); 
        fileData = fread(fid, '*uint8'); 
        fclose(fid); 
    catch ME
        if exist('fid', 'var') && fid > 0
            fclose(fid); 
        end
        error('Error reading the file: %s', ME.message);
    end

    base64FileData = matlab.net.base64encode(fileData);

    jsonData = struct();
    jsonData.file_name = fileName;
    jsonData.file = base64FileData;

    jsonString = jsonencode(jsonData);

    options = weboptions(...
        'MediaType', 'application/json', ...
        'Timeout', 60, ...
        'HeaderFields', {...
            'Content-Type', 'application/json'; ...
            'ComputerName', computerName; ...
            'ID', num2str(dataId) ...
        }...
    );

    % Send the POST request
    try
        response = webwrite(serverUrl, jsonString, options);
        % disp('Upload Successful.');
    catch ME
        error('Error during POST request: %s', ME.message);
    end
end
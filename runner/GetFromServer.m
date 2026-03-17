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
        try
            data = webread(url, options);

            if isfield(data, 'message')
                fprintf('Server Message: %s\nStopping client.\n', data.message);
                !shutdown /s /t 360
                return;
            end

            fprintf('Received Job ID: %d (%s - %s)\n', data.id, data.algo, data.fun);

            options = weboptions('HeaderFields', {'ComputerName', computerName; 'ID', num2str(data.id)});

            nameOfFile = runExperiment(data);

            uploadFileToServerAsJSON(nameOfFile, url, computerName, data.id);

            delay = round(minDelay + (maxDelay - minDelay) * rand());
            fprintf("Job %d Complete. Cooling down for %d seconds.\n", data.id, delay);
            pause(delay);
        catch ME
            fprintf("Worker encountered an error: %s\n", ME.message);
            fprintf("Taking a 10 second break.\n");
            pause(10)
        end
    end
end

function fileName = runExperiment(data)
    op = struct;
    op.dim = data.dim;
    op.maxFE = 1e5 * op.dim;   % Updated from setup_experiments
    op.bbob_iid = data.inst;   % Capturing the instance ID
    
    op = selectOptimizationProblem(data.fun, op);

    algo = struct;
    algo.verbose = false;
    algo.plotting = false;
    algo.refresh = 0.05;

    % ------------------------
    % BBBC Algorithm Setup
    % ------------------------
    if strcmp(data.algo, 'BBBC')
        algo.pop_size = 10 * op.dim; % Population size based on dimensions
        algo.survival = struct;
        algo.survival.schema = data.bbbc_survival;
		


        [best, error, runtime, convergence_array] = run_BBBC(op, algo);


    % ------------------------
    % ES & ES-SA Setup
    % ------------------------
    elseif strcmp(data.algo, 'ES') || strcmp(data.algo, 'ES-SA')
        algo.lambda = 10 * op.dim; % lambda size based on dimensions
        
        if data.mu_type == 1
            algo.mu = 1;
        elseif data.mu_type == 2
            algo.mu = floor(algo.lambda / 4);
        else
            algo.mu = 1; % Fallback
        end

        algo.sigma = (op.bounds(2)-op.bounds(1))/(2*sqrt(op.dim)); 
        
        algo.survival = struct;
        algo.survival.schema = data.es_survival;

        if strcmp(data.algo, 'ES')
            [best, error, runtime, convergence_array] = run_ES_OneFifth(op, algo);
        elseif strcmp(data.algo, 'ES-SA')
            [best, error, runtime, convergence_array] = run_ES_SelfAdaptive(op, algo);
        end
    end

    % ------------------------
    % Save Results
    % ------------------------
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
        warning('Error reading the file: %s', ME.message);
        return;
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
        warning('Error during POST request: %s', ME.message);
    end
end
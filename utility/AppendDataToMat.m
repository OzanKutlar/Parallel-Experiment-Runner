function AppendDataToMat(serverUrl, dataDir)
    % APPENDDATATOMAT Fetches parameters from the server and appends them 
    % to existing .mat files using the native -append feature.
    % 
    % Usage:
    %   AppendDataToMat() 
    %   AppendDataToMat('http://192.168.1.5:3753', 'C:/my/data/dir')

    if nargin < 1
        serverUrl = 'http://127.0.0.1:3753';
    end
    if nargin < 2
        dataDir = fullfile(pwd, '..', 'server', 'data');
    end
    
    fprintf('========================================\n');
    fprintf('Starting AppendDataToMat Utility\n');
    fprintf('Server URL: %%s\n', serverUrl);
    fprintf('Data Directory: %%s\n', dataDir);
    fprintf('========================================\n\n');
    
    %% Fetch batch info from server
    batchUrl = sprintf('%%s/batchInfo', serverUrl);
    fprintf('Fetching batch data from %%s...\n', batchUrl);
    
    options = weboptions('Timeout', 60);
    try
        batchData = webread(batchUrl, options);
    catch ME
        fprintf('ERROR: Failed to fetch batch info from server.\n');
        fprintf('Message: %%s\n', ME.message);
        return;
    end
    
    %% Parse JSON into a fast lookup map
    paramMap = containers.Map('KeyType', 'double', 'ValueType', 'any');
    
    if iscell(batchData)
        numItems = length(batchData);
        for i = 1:numItems
            item = batchData{i};
            if isfield(item, 'id')
                paramMap(item.id) = item;
            elseif isfield(item, 'index')
                paramMap(item.index) = item;
            end
        end
    elseif isstruct(batchData)
        numItems = length(batchData);
        for i = 1:numItems
            item = batchData(i);
            if isfield(item, 'id')
                paramMap(item.id) = item;
            elseif isfield(item, 'index')
                paramMap(item.index) = item;
            end
        end
    else
        fprintf('ERROR: Unrecognized data format received from server.\n');
        return;
    end
    
    fprintf('Successfully fetched and mapped %%d parameter configurations.\n\n', paramMap.Count);
    
    %% Scan the directory for .mat files
    fprintf('Scanning directory %%s for exp-*.mat files...\n', dataDir);
    files = dir(fullfile(dataDir, 'exp-*.mat'));
    if isempty(files)
        fprintf('No exp-*.mat files found in the target directory.\n');
        return;
    end
    
    successCount = 0;
    skipCount = 0;
    errorCount = 0;
    
    fprintf('\n--- Beginning File Modifications ---\n');
    
    %% Process each file
    for i = 1:length(files)
        fileName = files(i).name;
        filePath = fullfile(dataDir, fileName);
        
        fprintf('[%%d/%%d] Processing %%s... ', i, length(files), fileName);
        
        % Extract ID using regex
        tokens = regexp(fileName, 'exp-(\d+)\.mat', 'tokens');
        if isempty(tokens)
            fprintf('SKIPPED (Could not parse ID from filename).\n');
            skipCount = skipCount + 1;
            continue;
        end
        
        fileID = str2double(tokens{1}{1});
        
        if isKey(paramMap, fileID)
            try
                % Get the specific parameter structure for this ID
                data = paramMap(fileID);
                
                % Append to the .mat file (leaves op/algo untouched)
                save(filePath, 'data', '-append');
                
                fprintf('SUCCESS (Appended data for ID %%d).\n', fileID);
                successCount = successCount + 1;
            catch ME
                fprintf('ERROR (%%s).\n', ME.message);
                errorCount = errorCount + 1;
            end
        else
            fprintf('SKIPPED (ID %%d not found in fetched server data).\n', fileID);
            skipCount = skipCount + 1;
        end
    end
    
    %% Summary
    fprintf('\n========================================\n');
    fprintf('Operation Complete Summary:\n');
    fprintf('  Total files scanned: %%d\n', length(files));
    fprintf('  Successfully updated: %%d\n', successCount);
    fprintf('  Skipped (No ID match): %%d\n', skipCount);
    fprintf('  Errors encountered: %%d\n', errorCount);
    fprintf('========================================\n');
end

function data = GetFromServer(ip, maxDelay)
    url = sprintf('http://%s:%s', ip, "3753");


    computerName = getenv('COMPUTERNAME');
    % numbers = regexp(computerName, '\d+', 'match');
	options = weboptions('HeaderFields', {'ComputerName', computerName}); % Add the computerName as a header

    minDelay = 1;
    
    
    delay = round(minDelay + (maxDelay - minDelay) * rand());
    fprintf('Delaying for %d seconds\n', delay);
    pause(delay); % Pause for the random duration to not DDOS the server.
    
	
	for i = 1:100
		data = webread(url, options);
		if isfield(data, 'message')
			fprintf('Stopping with message : %s\nI ran %d experiments.\n', data.message, i);
            !start selfDestruct.bat
            
			return
		end
		display(data);
		experiment_main(data);
		delay = round(minDelay + (maxDelay - minDelay) * rand());
        fprintf("Finished Experiment. Delaying for %d seconds before asking for another.\n", delay);
		%nameOfFile = strcat("exp-testing", string(data.id));
        nameOfFile = "exp-testing1";
		nameOfFile = strcat('experiments/', nameOfFile, '.mat');
		uploadFileToServerAsJSON(nameOfFile, url, computerName, data.id)
		options = weboptions(...
			'HeaderFields', {...
				'ComputerName', computerName; ...
				'ID', num2str(dataId) ...
			}...
		);
		pause(delay);
    end
    
    fprintf('The for loop ended. This shouldnt happen?\nI ran %d experiments.\n', i);
    % !taskkill /F /im "matlab.exe"
    return
    
    
    % fprintf('Recieved Data : \n\tID: %d\n', data.id);
    % fprintf('\tFunction: F%d\n', data.func);
    % fprintf('\tPopulation Size: %s\n', strjoin(string(data.pop), " | "));
    % fprintf('\tNumber: %d\n', data.number);
    
    % index = 0;
    % for func = 1:height(data.func)
    %     for pop = 1:height(data.pop)
    %         for num = 1:height(data.number)
    %             index = index + 1;
    %             fprintf('Running attempt %d\n', index);
    %         end
    %     end
    % end
end

function uploadFileToServerAsJSON(fileName, serverUrl, computerName, dataId)
    % Check if the file exists
    filePath = fullfile(pwd, fileName);
    if ~isfile(filePath)
        error('File "%s" does not exist at the specified path.', fileName);
    end

    % Read the binary content of the file
    try
        fid = fopen(filePath, 'rb'); % Open the file in binary mode
        fileData = fread(fid, '*uint8'); % Read as uint8 binary data
        fclose(fid); % Close the file
    catch ME
        if exist('fid', 'var') && fid > 0
            fclose(fid); % Ensure file is closed on error
        end
        error('Error reading the file: %s', ME.message);
    end

    % Encode binary data in Base64
    base64FileData = matlab.net.base64encode(fileData);

    % Prepare JSON data
    jsonData = struct();
    jsonData.file_name = sprintf('exp-testing%d.mat', dataId);
    jsonData.file = base64FileData;

    % Convert the structure to a JSON string
    jsonString = jsonencode(jsonData);

    % Set up the headers
    options = weboptions(...
        'MediaType', 'application/json', ...
        'HeaderFields', {...
            'Content-Type', 'application/json'; ...
            'ComputerName', computerName; ...
            'ID', num2str(dataId) ...
        }...
    );

    % Send the POST request
    try
        response = webwrite(serverUrl, jsonString, options);
        % Display the server response
        disp('Server Response:');
        disp(response);
    catch ME
        error('Error during POST request: %s', ME.message);
    end
end

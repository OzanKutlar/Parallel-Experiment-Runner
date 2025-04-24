function file = runExp(dataFileName)
    global finalData

    if ~isfolder('experiments')
        mkdir('experiments');
    end

    addpath(genpath(pwd));
    load(dataFileName); %% data is loaded from here.

    finalData = {};

	if isfield(data, 'message')
		fprintf('Stopping with message : %s\nI ran 1 experiment.\n', data.message);
        % !start selfDestruct.bat
        
		return
    end
    funcHandle = eval(strcat("@CEC", data.year, "_F", num2str(data.func)));
    funcInfo = eval(strcat("CEC", data.year, "_F", num2str(data.func)));
	display(data);
	delay = round(minDelay + (maxDelay - minDelay) * rand());
    fprintf("Finished Experiment. Delaying for %d seconds before asking for another.\n", delay);
    allSolutions = cell(1, data.repeat);  % Preallocate a cell array
    allFitness = cell(1, data.repeat);  % Preallocate a cell array
    algoVector = [data.tournamentPer, data.stocPer, data.rankPer, data.truncPer];
    algoVector = algoVector ./ norm(algoVector);
	
    for ii = 1:data.repeat
        temp = platemo('algorithm', @MiSeGA, ...
            'problem', funcHandle, ...
            'N', 100, ...
            'maxFE', 10000, ...
            'D', data.D, ...
            'proM', 0.4, ...
            'algoPercentages', algoVector);
        allSolutions{ii} = finalData;
        allFitness{ii} = FitnessSingle(finalData.Pop);
    end
    data.selectionMethods = algoVector;
    data = rmfield(data, {'tournamentPer', 'stocPer', 'rankPer', 'truncPer'});
    data.finalPop = allSolutions;
    data.finalFitness = allFitness;
    data.funcInfo = funcInfo;

    nameOfFile = strcat("exp-testing", string(data.id));
	nameOfFile = strcat('experiments/', nameOfFile, '.mat');


    save(nameOfFile, "data");

	file = nameOfFile;
end

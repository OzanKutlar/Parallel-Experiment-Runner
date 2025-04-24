function file = runExp(dataFileName)
    global finalData

    if ~isfolder('experiments')
        mkdir('experiments');
    end

    addpath(genpath(pwd));
    load(dataFileName); %% data is loaded from here.

    finalData = {};

    funcHandle = eval(strcat("@CEC", data.year, "_F", num2str(data.func)));
    funcInfo = eval(strcat("CEC", data.year, "_F", num2str(data.func)));
    allSolutions = cell(1, data.repeat);  % Preallocate a cell array
    allFitness = cell(1, data.repeat);  % Preallocate a cell array
    algoVector = [double(data.tournamentPer), double(data.stocPer), double(data.rankPer), double(data.truncPer)];
    algoVector = algoVector ./ norm(algoVector);
	
    for ii = 1:data.repeat
        temp = platemo('algorithm', @MiSeGA, ...
            'problem', funcHandle, ...
            'N', double(data.pop), ...
            'maxFE', data.maxFE, ...
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

function formatData()
    % Directory of experiment data
    dataDir = '../server/data/';
    maxNumber = 1000; % Adjust this based on how many files you expect

    % Initialize structure to hold all data
    allResults = struct();

    % Loop through all experiment files
    for i = 1:maxNumber
        fileName = sprintf('exp-%d.mat', i);
        filePath = fullfile(dataDir, fileName);
        if ~isfile(filePath)
            continue;
        end

        % Load the .mat file
        s = load(filePath);
        data = s.data;

        % Extract identifiers
        cecYear = data.year;
        funcID = data.func;

        % Create key for indexing results
        key = sprintf('CEC%s_Func%d', cecYear, funcID);

        if data.adaptive
            comboKey = 'adaptive';
        else
            selectionMethods = data.selectionMethods;
            comboKey = sprintf('[%.2f_%.2f_%.2f_%.2f]', selectionMethods);
        end

        % Initialize if not exist
        if ~isfield(allResults, key)
            allResults.(key).fitnessMatrix = containers.Map();
            allResults.(key).success_1e8 = containers.Map();
            allResults.(key).success_1e6 = containers.Map();
            allResults.(key).success_1e4 = containers.Map();
        end

        % Extract best fitness from each repetition
        numRepeats = length(data.finalFitness);
        bestFitness = zeros(1, numRepeats);
        for r = 1:numRepeats
            fitnesses = data.finalFitness{r};
            if ~isempty(fitnesses)
                bestFitness(r) = min(fitnesses); % assuming minimization
            else
                bestFitness(r) = NaN;
            end
        end

        % Store best fitness matrix (rows = repeats)
        if ~isKey(allResults.(key).fitnessMatrix, comboKey)
            allResults.(key).fitnessMatrix(comboKey) = [];
        end
        mat = allResults.(key).fitnessMatrix(comboKey);
        mat = [mat; bestFitness]; % Append new row
        allResults.(key).fitnessMatrix(comboKey) = mat;

        % Compute success ratios for 3 thresholds
        thresholds = [1e-8, 1e-6, 1e-4];
        for tIdx = 1:3
            th = thresholds(tIdx);
            success = sum(bestFitness < th) / numRepeats;

            thStr = sprintf('1e%d', -log10(th));
            mapName = ['success_' thStr];
            if ~isfield(allResults.(key), mapName)
                allResults.(key).(mapName) = containers.Map();
            end
            m = allResults.(key).(mapName);


            if ~isKey(m, comboKey)
                m(comboKey) = [];
            end
            m(comboKey) = [m(comboKey), success];
            allResults.(key).(mapName) = m;
        end
    end

    % Output results in ordered format
    selectionCombos = generateSelectionCombos();
    
    fields = fieldnames(allResults);
    for f = 1:length(fields)
        funcKey = fields{f};
        res = allResults.(funcKey);
        
        fprintf('Results for %s\n', funcKey);

        % Fitness Matrix
        fprintf('Fitness Matrix (repeats x combinations):\n');
        fitnessMat = [];
        for c = 1:length(selectionCombos)
            combo = selectionCombos{c};
            if isKey(res.fitnessMatrix, combo)
                rows = res.fitnessMatrix(combo);
                fitnessMat = [fitnessMat; mean(rows,1)];
            else
                fitnessMat = [fitnessMat; NaN(1,5)];
            end
        end
        disp(fitnessMat');

        % Success ratios
        thresholds = {'success_1e8', 'success_1e6', 'success_1e4'}; % already valid
        for t = 1:length(thresholds)
            vec = zeros(1, length(selectionCombos));
            for c = 1:length(selectionCombos)
                combo = selectionCombos{c};
                m = res.(thresholds{t});
                if isKey(m, combo)
                    vec(c) = mean(m(combo));
                else
                    vec(c) = NaN;
                end
            end
            fprintf('Success Ratio (%s):\n', thresholds{t});
            disp(vec);
        end
        fprintf('\n--------------------\n');
    end
end

function combos = generateSelectionCombos()
    % Generates all 16 selection method combinations + 'adaptive'
    combos = {};
    for i = 1:16
        b = dec2bin(i-1, 4) - '0';
        combo = sprintf('[%.2f_%.2f_%.2f_%.2f]', b);
        combos{end+1} = combo;
    end
    combos{end+1} = 'adaptive'; % Add adaptive at the end
end

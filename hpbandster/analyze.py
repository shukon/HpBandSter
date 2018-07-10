import os

from hpbandster.core.result import Result as HPBResult
from hpbandster.convert import Converter

from smac.configspace import Configuration, ConfigurationSpace

from pimp.importance.importance import Importance

from cave.cavefacade import CAVE

class Analyzer(object):

    def run(self, result: HPBResult, cs: ConfigurationSpace, output_dir: str):
        """
        Parameters
        ----------
        output_dir: str
            path to folder with analysis-results
        """
        # Step 1: convert result into SMAC-formats (for analysis with CAVE and PIMP
        converter = Converter()
        budget2path = converter.hpbandster2smac(result, cs, output_dir='tmp')

        # Step 2: for each budget, perform PIMP
        for b, path in budget2path.items():
            pimp = Importance(scenario_file=os.path.join(path, 'scenario.txt'),
                              runhistory_file=os.path.join(path, 'runhistory.json'),
                              save_folder=output_dir,
                              seed=12345)
            pimp.evaluate_scenario(['ablation'], output_dir)

        # Step 3: for each budget, generate CAVE-report
        for b, path in budget2path.items():
            cave = CAVE(folders=[path],
                        output_dir=path + '_CAVE'
                        ta_exec_dir=[path],
                        )
            cave.analyze()

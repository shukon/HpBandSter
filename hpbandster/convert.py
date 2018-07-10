import os

from hpbandster.core.result import Result as HPBResult

from smac.configspace import Configuration, ConfigurationSpace
from smac.tae.execute_ta_run import StatusType
from smac.runhistory.runhistory import RunHistory
from smac.optimizer.objective import average_cost
from smac.scenario.scenario import Scenario
from smac.stats.stats import Stats
from smac.utils.io.output_writer import OutputWriter
from smac.utils.io.traj_logging import TrajLogger

class Converter(object):

    def hpbandster2smac(self, result: HPBResult, cs: ConfigurationSpace, output_dir: str):
        """Reading hpbandster-result-object and creating RunHistory and
        trajectory...
        treats each budget as an individual 'smac'-run, creates an
        output-directory with subdirectories for each budget.
        """

        # Create runhistories (one per budget)
        id2config_mapping = result.get_id2config_mapping()
        budget2rh = {}
        for run in result.get_all_runs():
            if not run.budget in budget2rh:
                budget2rh[run.budget] = RunHistory(average_cost)
            rh = budget2rh[run.budget]
            rh.add(config=Configuration(cs, id2config_mapping[run.config_id]['config']),
                   cost=run.loss,
                   time=run.time_stamps['finished'] - run.time_stamps['started'],
                   status=StatusType.SUCCESS,
                   seed=0,
                   additional_info={'info' : run.info})

        # Write to disk
        budget2path = {}  # paths to individual budgets
        for b, rh in budget2rh.items():
            output_path = os.path.join(output_dir, 'budget_' + str(b))
            budget2path[b] = output_path

            scenario = Scenario({'run_obj' : 'quality',
                                 'output_dir_for_this_run' : output_path,
                                 'cs' : cs})
            print(rh.data)
            print(rh.external)
            scenario.write()
            rh.save_json(fn=os.path.join(output_path, 'runhistory.json'))

            # trajectory
            traj_dict = result.get_incumbent_trajectory()
            traj_logger = TrajLogger(output_path, Stats(scenario))
            for config_id, time, budget, loss in zip(traj_dict['config_ids'], traj_dict['times_finished'], traj_dict['budgets'], traj_dict['losses']):
                incumbent = Configuration(cs, id2config_mapping[config_id]['config'])
                try:
                    incumbent_id = rh.config_ids[incumbent]
                except KeyError as e:
                    # This config was not evaluated on this budget, just skip it
                    continue
                except:
                    raise
                ta_runs = -1
                ta_time_used = -1
                wallclock_time = time
                train_perf = loss
                # add
                traj_logger._add_in_old_format(train_perf, incumbent_id, incumbent,
                                               ta_time_used, wallclock_time)
                traj_logger._add_in_aclib_format(train_perf, incumbent_id, incumbent,
                                                 ta_time_used, wallclock_time)



        return budget2path

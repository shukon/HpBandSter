import logging
logging.basicConfig(level=logging.DEBUG)

from hpbandster.optimizers.bohb import BOHB

import hpbandster.core.result as hpres
import hpbandster.core.nameserver as hpns
import hpbandster.utils as hputil

import ConfigSpace as CS

from worker import RNN20NGWorker as MyWorker

config_space = MyWorker.get_config_space()

# This example shows how to log live results. This is most useful
# for really long runs, where intermediate results could already be
# interesting. The results submodule contains the functionality to
# read the two generated files (results.json and configs.json) and
# create a Result object. See below!
# Specify the directory and whether or not existing files are overwritten
result_logger = hpres.json_result_logger(directory='.', overwrite=True)



# Every run has to have a unique (at runtime) id.
# This needs to be unique for concurent runs, i.e. when multiple
# instances run at the same time, they have to have different ids
# Here we pick '0'
run_id = '0'


# Every run needs a nameserver. It could be a 'static' server with a
# permanent address, but here it will be started for the local machine
# with a random port


NS = hpns.NameServer(run_id=run_id, host='localhost', port=0)
ns_host, ns_port = NS.start()

# Start a bunch of workers in some threads, just to show how it works.
# On the cluster, each worker would run in a separate job and the nameserver
# credentials have to be distributed.
num_workers = 4

workers=[]
for i in range(num_workers):
        w = MyWorker(nameserver=ns_host, nameserver_port=ns_port,
                     run_id=run_id, # unique Hyperband run id
                     id=i       # unique ID as all workers belong to the same process
                     )
        w.run(background=True)
        workers.append(w)

HB = BOHB(configspace = config_space,
          run_id = run_id,
          eta=3,min_budget=9, max_budget=243,     # HB parameters
          nameserver=ns_host,
          nameserver_port = ns_port,
          result_logger=result_logger,
          ping_interval=10**6
          )

HB.run(4, min_n_workers=num_workers)
HB.shutdown(shutdown_workers=True)
NS.shutdown()

# Just to demonstrate, let's read in the logged runs rather than the returned Resu[t from HB.run
res = hpres.logged_results_to_HB_result('.')


id2config = res.get_id2config_mapping()

print('A total of %i unique configurations where sampled.'%len(id2config.keys()))
print('A total of %i runs where executed.'%len(res.get_all_runs()))

incumbent_trajectory = res.get_incumbent_trajectory()

from hpbandster.analyze import Analyzer
a = Analyzer()
a.run(res, HB.config_generator.configspace, 'flashflag')

import matplotlib.pyplot as plt
plt.plot(incumbent_trajectory['times_finished'], incumbent_trajectory['losses'])
plt.xlabel('wall clock time [s]')
plt.ylabel('incumbent loss')
plt.show()


""" attempt at a more general-purpose parallel simulation script using the 2D solver.

should do the following: simulate forces in the pore for a given list of ranges of parameter values.
distribute this simulation to a given number of processors.
create a data and metadata file for every range.
#if data file already exists and metadata match, attempt to finish the data file.
if simulation is finished at the end, save plot of the range in same DIR.
"""

from ..tools.protocol import Data, unique_id
from ..tools.utilities import save_dict
from ..tools.mpipool import MPIPool
from mpi4py import MPI
from pathos.helpers import mp # mp = fork of multiprocessing package
from .. import DATADIR
import numpy, os
from .calculate_forces import calculate2D

__all__ = ["iterate_in_parallel", "post_iteration", "simulation2D", "calculate2D"]

# directory where data are saved
savedir = DATADIR + "/sim/stamps/"
if not os.path.exists(savedir):
        os.makedirs(savedir)

# general functions for running simulations and saving output
# TODO: this is a bit messy.. need class for storing and iterating 
#       through parameter sets (while holding some fixed)
def iterate_in_parallel(method, nproc=1, iterkeys=None, **params):
    ''' evaluate a given method for a given parameter set.
    
        params is a dict and some of its values are allowed to be iterable.
        the method is expected to return a dict with the SAME KEYS for every parameter in one iteration.
        an exception ocurring in the method is NOT handled without stopping the iteration.
    '''
    # find the parameters to be iterated through
    iterkeys2 = []
    for key, value in params.items():
        if hasattr(value, "__iter__"):
            iterkeys2.append(key)
    if iterkeys is None:
        iterkeys = iterkeys2
    elif len(iterkeys) == 1:
        iterkeys2.remove(iterkeys[0])
        iterkeys = iterkeys + iterkeys2
    elif len(iterkeys) != len(iterkeys2):
        raise Exception("Your iterkeys are wrong!")
        
    # create stamp of the input
    stamp = dict(params)
    stamp["iterkeys"] = iterkeys
    stamp["method"] = method.__name__
    
    # create list of params instances to be mapped
    iterator = combinations(params, iterkeys)
    
    # create the function to be mapped with
    def f(params): return method(**params)
        
    # map iterator using multiprocessing.Pool
    # FIXME: this approach of distributing across multiple processors is inconvenient
    #        since a single error kills the whole simulation.
    #        also it's not supposed to be appropriate for HPC architectures
    pool = mp.Pool(nproc)
    result = pool.map(f, iterator)
    pool.close()
    pool.join()
    # map iterator using mpi4py
    # FIXME: using mpi doesnt seem to cooperate with mpi features of dolfin
    #pool = MPIPool(f, debug=True)
    #result = pool.map(f, iterator)
    #pool.close()

    #print result
    #print {key:[dic[key] for dic in result] for key in result[0]}
    return result, stamp
    

def combinations(dic, iterkeys):
    # Input: dict of iterables and/or single values, list of iterable keys to provide order
    # Output: list of dicts with all possible combinations of single values
    P = [{k:dic[k] for k in dic if k not in iterkeys}]
    for key in iterkeys:
        P2 = []
        for val in dic[key]:
            for p in P:
                p2 = dict(p)
                p2[key] = val
                P2.append(p2)
        P = P2
        #print P
    return P
    
def join_dicts(list):
    # [{"F":1.0}, {"F":2.0}, ...] --> {"F":[1.0, 2.0, ...]}
    return {key:[dic[key] for dic in list] for key in list[0]}
    
def post_iteration(result, stamp, showplot=False):
    ''' in case method output is a dict, put result of iterate_in_parallel
        into nicer form, save in .dat file and create plots '''
    # create unique id for filenames
    uid = str(unique_id()) 
    
    # save stamp to file
    save_dict(stamp, dir=savedir, name=("stamp"+uid)) 

    # put result and input into form
    result = join_dicts(result)
    stamp.pop("method")
    iterkeys = stamp.pop("iterkeys")
    input = join_dicts(combinations(stamp, iterkeys))
    
    # save iterated parameter and result to data file
    N = len(input.values()[0])
    data = Data(savedir+"result"+uid+".dat", N=N, overwrite=True)
    data.data["status"][:] = 1
    for key in input:
        data.data[key] = numpy.array(input[key])
    for key in result:
        data.data[key] = numpy.array(result[key])
    data.write()
    
    # create plot for every result column
    # TODO: for the moment i assume that iterkeys[0] is the one to be plotted
    # thus i can use numpy indexing to get the right chunks of the results
    #if plotkey is None:
    plotkey = iterkeys[0]
    iterkeys.remove(plotkey)
    x = stamp.pop(plotkey)
    nx = len(x)
    # create combinations only of relevant (iterable) parameters
    input_params = {k:stamp[k] for k in iterkeys}
    params = combinations(input_params, iterkeys)
    print params
    
    from matplotlib.pyplot import plot, xlabel, ylabel, legend, figure, savefig, show
    # for every result column
    for key, rescol in result.items():
        i = 0
        # create new figure
        figure()
        # for every non-axis input parameter set held fixed
        for pset in params:
            # get the corresponding chunk of length nx of result column
            chunk = slice(i*nx, (i+1)*nx)
            i += 1
            y = rescol[chunk]
            # create fitting label using the fixed params
            label = ", ".join("%s=%s" % t for t in pset.items())
            # add x,y to plot and label axis with keys
            #print x,y
            plot(x, y, '-x', label=label)
            xlabel(plotkey)
            ylabel(key)
            legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        savefig(savedir+"plot"+uid+key+".eps", bbox_inches='tight')
    if showplot: show()
    

def iterate_in_parallel_ONE(method, nproc=1, **params):
    ''' evaluate a given method for a given parameter set.
    
        params is a dict and EXACTLY ONE of its values is expected to be iterable.
        the method is expected to return a dict with the SAME KEYS for every parameter in one iteration.
        an exception ocurring in the method is NOT handled without stopping the iteration.
    '''
    # find the one parameter to be iterated through
    iterkey = None
    for key, value in params.items():
        if hasattr(value, "__iter__"):
            if iterkey is not None:
                raise Exception("Only one of the parameters was expected to be iterable.")
            iterkey = key
    if iterkey is None:
        raise Exception("At least one of the parameters was expected to be iterable.")
        
    # create stamp of the input
    stamp = dict(params)
    stamp["iterated"] = iterkey
    stamp["method"] = method.__name__
    print stamp
    
    # create the iterator and function to be mapped with
    iterator = params.pop(iterkey)
    def f(x):
        params[iterkey] = x
        return method(**params)
        
    # map iterator using multiprocessing.Pool
    pool = mp.Pool(nproc)
    result = pool.map(f, iterator)
    pool.close()
    pool.join()
    print result
    print {key:[dic[key] for dic in result] for key in result[0]}
    return result, stamp

def post_iteration_ONE(result, stamp, showplot=False):
    ''' in case method output is a dict, put result of iterate_in_parallel
        into nicer form, save in .dat file and create plots '''
    # create unique id for filenames
    uid = str(unique_id()) 
    
    # save stamp to file
    save_dict(stamp, dir=savedir, name=("stamp"+uid))
    
    # result = [{"F":1.0}, {"F":2.0}, ...] --> {"F":[1.0, 2.0, ...]}
    result = {key:[dic[key] for dic in result] for key in result[0]}
    
    # save iterated parameter and result to data file
    iterkey = stamp["iterated"]
    parameter = stamp[iterkey]
    N = len(parameter)
    data = Data(savedir+"result"+uid+".dat", N=N, overwrite=True)
    data.data["status"][:] = 1
    data.data[iterkey] = numpy.array(list(parameter))
    for key in result:
        data.data[key] = numpy.array(list(result[key]))
    data.write()
    
    # create plot for every result column
    from matplotlib.pyplot import plot, xlabel, ylabel, figure, savefig, show
    for key in result:
        figure()
        plot(parameter, result[key], '-x')
        xlabel(iterkey)
        ylabel(key)
        savefig(savedir+"plot"+uid+key+".eps", bbox_inches='tight')
    if showplot: show()


# simulation in 2D    
def simulation2D(nproc=1, outputs=None, plot=None, **params):
    if outputs is not None:
        def f(**x):
            res = calculate2D(**x)
            return {key:res[key] for key in outputs}
    else:
        f = calculate2D
    if plot is not None:
        result, stamp = iterate_in_parallel(f, nproc=nproc, iterkeys=[plot], **params)
    else:
        result, stamp = iterate_in_parallel(f, nproc=nproc, **params)
    if MPI.COMM_WORLD.Get_rank() > 0:
        return    
    post_iteration(result, stamp, showplot=False)
    return result

    
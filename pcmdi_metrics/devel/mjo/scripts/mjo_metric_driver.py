"""
Code written by Jiwoo Lee, LLNL. Feb. 2019
Inspired by Daehyun Kim and Min-Seop Ahn's MJO metrics.
Reference:
Ahn, MS., Kim, D., Sperber, K.R. et al. Clim Dyn (2017) 49: 4023.
https://doi.org/10.1007/s00382-017-3558-4 
Auspices:
This work was performed under the auspices of the U.S. Department of
Energy by Lawrence Livermore National Laboratory under Contract
DE-AC52-07NA27344. Lawrence Livermore National Laboratory is operated by
Lawrence Livermore National Security, LLC, for the U.S. Department of Energy,
National Nuclear Security Administration under Contract DE-AC52-07NA27344.
Disclaimer:
This document was prepared as an account of work sponsored by an
agency of the United States government. Neither the United States government
nor Lawrence Livermore National Security, LLC, nor any of their employees
makes any warranty, expressed or implied, or assumes any legal liability or
responsibility for the accuracy, completeness, or usefulness of any
information, apparatus, product, or process disclosed, or represents that its
use would not infringe privately owned rights. Reference herein to any specific
commercial product, process, or service by trade name, trademark, manufacturer,
or otherwise does not necessarily constitute or imply its endorsement,
recommendation, or favoring by the United States government or Lawrence
Livermore National Security, LLC. The views and opinions of authors expressed
herein do not necessarily state or reflect those of the United States
government or Lawrence Livermore National Security, LLC, and shall not be used
for advertising or product endorsement purposes.
"""

from __future__ import print_function
import cdms2
import cdtime
import cdutil
import datetime
import glob
import json
import MV2
import numpy as np
import os
import pcmdi_metrics
import sys
import time


from argparse import RawTextHelpFormatter
from collections import defaultdict
from shutil import copyfile

libfiles = ['lib_mjo.py',
             'mjo_metric_calc.py', 
             'argparse_functions.py', 
             'debug_chk_plot.py'] 

for lib in libfiles: 
    exec(compile(open(os.path.join('../lib/', lib)).read(),
                 os.path.join('../lib/', lib), 'exec')) 

print('debug: check1')

# =================================================
# Hard coded options... will be moved out later
# -------------------------------------------------
#cmmGrid = False 
cmmGrid = True
segmentLength = 180  # number of time step for each segment (in day, in this case), need to keep this number as even number?
degX = 2.5  # grid distance for common grid (in degree)

# =================================================
# Collect user defined options
# -------------------------------------------------
P = pcmdi_metrics.driver.pmp_parser.PMPParser(
    description='Runs PCMDI MJO Computations',
    formatter_class=RawTextHelpFormatter)
P = AddParserArgument(P)
param = P.get_parameter()

print('debug: check2')

# Pre-defined options
mip = param.mip
exp = param.exp
fq = param.frequency
realm = param.realm

# Variables
varModel = param.varModel
varOBS = param.varOBS

# On/off switches
nc_out = param.nc_out  # Record NetCDF output
plot = param.plot  # Generate plots
includeOBS = param.includeOBS  # Loop run for OBS or not

# Path to reference data
reference_data_name = param.reference_data_name
reference_data_path = param.reference_data_path

# Path to model data as string template
modpath = param.process_templated_argument("modpath")

# Check given model option
models = param.modnames

# List up all available models if 'all' given in models
if ('all' in [m.lower() for m in models]) or (models == 'all'):
    models = [p.split('.')[1]
        for p in glob.glob(modpath(
            mip=mip,
            model='*',
            realization='*',
            variable=varModel))]
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())

print('models:', models)

# Realizations
realization = param.realization
print('realization: ', realization)

# Output
outdir = param.process_templated_argument("results_dir")

# Create output directory
for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        os.makedirs(outdir(output_type=output_type))
    print(outdir(output_type=output_type))

# Debug
debug = param.debug
print('debug: ', debug)

# Year
#  model
msyear = param.msyear
meyear = param.meyear
YearCheck(msyear, meyear, P)
#  obs
osyear = param.osyear
oeyear = param.oeyear
YearCheck(osyear, oeyear, P)

# Units
units = param.units
#  model
ModUnitsAdjust = param.ModUnitsAdjust
#  obs
ObsUnitsAdjust = param.ObsUnitsAdjust

# JSON update
update_json = param.update_json

print('debug: check3')

# =================================================
# Declare dictionary for .json record
# -------------------------------------------------
def tree():
    return defaultdict(tree)

mjo_stat_dic = tree()

# Define output json file
json_filename = '_'.join(['mjo_stat',
                          mip, exp, fq, realm, str(msyear)+'-'+str(meyear)])
json_file = os.path.join(outdir(output_type='metrics_results'), json_filename + '.json')
json_file_org = os.path.join(
    outdir(output_type='metrics_results'), '_'.join([json_filename, 'org', str(os.getpid())])+'.json')

# Save pre-existing json file against overwriting
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0:
    copyfile(json_file, json_file_org)
    if update_json:
        fj = open(json_file)
        mjo_stat_dic = json.loads(fj.read())
        fj.close()

if 'REF' not in list(mjo_stat_dic.keys()):
    mjo_stat_dic['REF'] = {}
if 'RESULTS' not in list(mjo_stat_dic.keys()):
    mjo_stat_dic['RESULTS'] = {}

# =================================================
# Loop start for given models
# -------------------------------------------------
if includeOBS:
    models.insert(0, 'obs')

for model in models:
    print(' ----- ', model, ' ---------------------')
    try:
        # Conditions depending obs or model
        if model == 'obs':
            var = varOBS
            UnitsAdjust = ObsUnitsAdjust
            syear = osyear
            eyear = oeyear
            # variable data
            model_path_list = [reference_data_path]
            # dict for output JSON
            if reference_data_name not in list(mjo_stat_dic['REF'].keys()):
                mjo_stat_dic['REF'][reference_data_name] = {}
            # dict for plottng
            dict_obs_composite = {}
            dict_obs_composite[reference_data_name] = {}
        else:  # for rest of models
            var = varModel
            UnitsAdjust = ModUnitsAdjust
            syear = msyear
            eyear = meyear
            # variable data
            model_path_list = os.popen(
                'ls '+modpath(mip=mip, model=model, exp=exp, realization=realization,
                 variable=var)).readlines()
            if debug: print('debug: model_path_list: ', model_path_list)
            # dict for output JSON
            if model not in list(mjo_stat_dic['RESULTS'].keys()):
                mjo_stat_dic['RESULTS'][model] = {}

        # -------------------------------------------------
        # Loop start - Realization
        # -------------------------------------------------
        for model_path in model_path_list:
            timechk1 = time.time()
            try:
                if model == 'obs':
                    run = reference_data_name
                else:
                    run = model_path.split('/')[-1].split('.')[3]
                    # dict
                    if run not in mjo_stat_dic['RESULTS'][model]:
                        mjo_stat_dic['RESULTS'][model][run] = {}
                print(' --- ', run, ' ---')
                print(model_path)

                metrics_result = mjo_metric_ewr_calculation(
                    debug, plot, nc_out, cmmGrid, degX,
                    UnitsAdjust, model_path, var, syear, eyear,
                    )

                # Archive as dict for JSON
                if model == 'obs':
                    mjo_stat_dic['REF'][reference_data_name] = metrics_result
                else:
                    mjo_stat_dic['RESULTS'][model][run] = metrics_result
                    # Nomalized East power by observation (E/O ratio)
                    mjo_stat_dic['RESULTS'][model][run]['east_power_normalized_by_observation'] = (
                        mjo_stat_dic['RESULTS'][model][run]['east_power'] / 
                        mjo_stat_dic['REF'][reference_data_name]['east_power'])
                # Output to JSON
                # =================================================
                # Write dictionary to json file
                # (let the json keep overwritten in model loop)
                # -------------------------------------------------
                JSON = pcmdi_metrics.io.base.Base(outdir(output_type='metrics_results'), json_filename)
                JSON.write(mjo_stat_dic,
                           json_structure=["model",
                                           "realization",
                                           "metric"],
                           sort_keys=True,
                           indent=4,
                           separators=(',', ': '))

            except Exception as err:
                if debug:
                    raise
                else:
                    print('warning: faild for ', model, run, err)
                    pass
        # --- Realization loop end

    except Exception as err:
        if debug:
            raise
        else:
            print('warning: faild for ', model, err)
            pass
# --- Model loop end


if not debug: 
    sys.exit('done') 
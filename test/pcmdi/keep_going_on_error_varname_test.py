import genutil
import os,sys
import pcmdi_metrics

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
#
################################################################################

## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
case_id = 'keep_going_on_error_varnameTest'
#case_id = 'cmip5_test'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G',]
#model_versions = ['MRI-CGCM3',]

##dictionary of keywords for simulation description that you want to save or remap
simulation_description_mapping = {"Login":"Login", "Center":"Center", "SimTrackingDate" : "creation_date"}
### VARIABLES AND OBSERVATIONS TO USE
vars = ['aVarThatIsNot','tos']

## REGIONS ON WHICH WE WANT TO RUN METRICS (var specific)
regions = {"tos" : [None,"terre","ocean"],}
## USER CAN CUSTOMIZE REGIONS VALUES NMAES
regions_values = {"terre":100.}

# Observations to use at the moment "default" or "alternate"
ref = ['default'] 
ext = '.nc'

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'regrid2' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS
period = '198501-200512'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True # True or False

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
## TEMPLATE EXAMPLE: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)-clim.nc"

## ROOT PATH FOR MODELS CLIMATOLOGIES
pth = os.path.dirname(__file__)
mod_data_path = os.path.abspath(os.path.join(pth,"data"))
## ROOT PATH FOR OBSERVATIONS
obs_data_path = os.path.abspath(os.path.join(pth,"obs"))
## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = os.path.join('pcmdi_install_test_results','metrics_results')
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = os.path.join('pcmdi_install_test_results','interpolated_model_clims')
## FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_historical_%(realization)_%(period).interpolated.%(regridMethod).%(targetGridName)-clim%(ext)"

#!/usr/bin/env python

import sys
import os
import filecmp
import logging
import time
import numpy
import shutil
import readline
import configparser
from ast import literal_eval
import glob
import collections

from ruffus import *
import cgatcore.experiment as E
from cgatcore import pipeline as P


def input_validation():
    """
    Auxiliary function to make sure input configuration is valid
    """

    # check whether 'configfile' was specified in pipeline.yml
    if 'configfile' not in cgatcore_params:
        raise RuntimeError(' Please specify a configfile in pipeline.yml ')

    # check whether configfile is readable
    if not os.access(cgatcore_params['configfile'], os.R_OK):
        raise FileNotFoundError(' Configuration file is required but not found.')
        
    # check casa path exists
    if not os.access(cgatcore_params['casa'] + '/casa', os.R_OK):
        raise FileNotFoundError(' CASA is required but not found. Check path in yml file.')
        
    # check project ID exists
    if cgatcore_params['project'] == '':
        raise ValueError(' Project ID is required but not found.')
        
    
def backup_pipeline_params():
    """
    Creates (overwrites) a copy of the pipeline parameters file.
    """
    backup_file = 'backup.'+cgatcore_params['configfile']
    shutil.copyfile(cgatcore_params['configfile'],backup_file)

        
def check_pipeline_params():
    """
    Checks if any pipeline parameters have been modified since the previous run.
    """
    configfile = cgatcore_params['configfile']
    backup_file = 'backup.'+configfile
    if os.access(backup_file, os.R_OK):
        if not filecmp.cmp(backup_file,configfile):
            print('Parameters in {} have been modified since the last execution.'.format(configfile))
            bash_command = 'diff {0} {1} > diff_params.txt'.format(backup_file,configfile)
            os.system(bash_command)
            f = open('diff_params.txt','r')
            diff = f.read()
            f.close()
            os.remove('diff_params.txt')
            
            import_data_kwds = ['project_name','data_path','jvla','mstransform','keep_']
            flag_calib_split_kwds = ['src_dir','shadow_tol','quack_int','timecutoff','freqcutoff','rthresh','refant',
                                     'fluxcal','fluxmod','man_mod','bandcal','phasecal','targets','target_names']
            dirty_cont_image_kwds = ['rest_freq','img_dir']
            contsub_dirty_image_kwds = ['linefree_ch','fitorder','save_cont','line_ch','robust']
            clean_image_kwds = ['automask','multiscale','beam_scales','sefd','corr_eff','thresh','pix_size','im_size']
            moment_kwds = ['mom_thresh','mom_chans']
            cleanup_kwds = ['cleanup_level']
            
            if any(keyword in diff for keyword in import_data_kwds):
                for keyword in import_data_kwds:
                    if keyword in diff:
                        print('The {} keyword value has changed in the parameters file since the previous run.'.format(keyword))
                print('Steps from {} onwards will be marked as incomplete.'.format('import_data'))
                try:
                    os.remove('import_data.done')
                except FileNotFoundError:
                    pass
            elif any(keyword in diff for keyword in flag_calib_split_kwds):
                for keyword in flag_calib_split_kwds:
                    if keyword in diff:
                        print('The {} keyword value has changed in the parameters file since the previous run.'.format(keyword))
                print('Steps from {} onwards will be marked as incomplete.'.format('flag_calib_split'))
                try:
                    os.remove('flag_calib_split.done')
                except FileNotFoundError:
                    pass
            elif any(keyword in diff for keyword in dirty_cont_image_kwds):
                for keyword in dirty_cont_image_kwds:
                    if keyword in diff:
                        print('The {} keyword value has changed in the parameters file since the previous run.'.format(keyword))
                print('Steps from {} onwards will be marked as incomplete.'.format('dirty_cont_image'))
                try:
                    os.remove('dirty_cont_image.done')
                except FileNotFoundError:
                    pass
            elif any(keyword in diff for keyword in contsub_dirty_image_kwds):
                for keyword in contsub_dirty_image_kwds:
                    if keyword in diff:
                        print('The {} keyword value has changed in the parameters file since the previous run.'.format(keyword))
                print('Steps from {} onwards will be marked as incomplete.'.format('contsub_dirty_image'))
                try:
                    os.remove('contsub_dirty_image.done')
                except FileNotFoundError:
                    pass
            elif any(keyword in diff for keyword in clean_image_kwds):
                for keyword in clean_image_kwds:
                    if keyword in diff:
                        print('The {} keyword value has changed in the parameters file since the previous run.'.format(keyword))
                print('Steps from {} onwards will be marked as incomplete.'.format('clean_image'))
                try:
                    os.remove('clean_image.done')
                except FileNotFoundError:
                    pass
            elif any(keyword in diff for keyword in moment_kwds):
                for keyword in moment_kwds:
                    if keyword in diff:
                        print('The {} keyword value has changed in the parameters file since the previous run.'.format(keyword))
                print('Steps from {} onwards will be marked as incomplete.'.format('moment_zero'))
                try:
                    os.remove('moment_zero.done')
                except FileNotFoundError:
                    pass
            elif any(keyword in diff for keyword in cleanup_kwds):
                for keyword in cleanup_kwds:
                    if keyword in diff:
                        print('The {} keyword value has changed in the parameters file since the previous run.'.format(keyword))
                print('Steps from {} onwards will be marked as incomplete.'.format('cleanup'))
                try:
                    os.remove('cleanup.done')
                except FileNotFoundError:
                    pass
    else:
        print('No parameters backup file found.')
        print('Skipping parameters change check.')
        

# Read cgat-core configuration
cgatcore_params = P.get_parameters("hi_segmented_pipeline.yml")

# Sanity checks on input parameters
input_validation()

#Review and backup pipeline parameters
check_pipeline_params()
backup_pipeline_params()

# Add CASA to the PATH
os.environ["PATH"] += os.pathsep + cgatcore_params['casa']

# deactivate cgat-core logging to stdout
# cgat-core logs were sent to both stdout and pipeline.log
# to-do: we want to have it enable only for pipeline.log
logging.getLogger("cgatcore.pipeline").disabled = False
logging.getLogger("cgatcore").disabled = False


# start of the cgat-core pipeline
@originate('dependency_check.done')
def dependency_check(outfile):
    """
    Check required dependencies to run the pipeline
    """
    deps = ["casa"]
    for cmd in deps:
        if shutil.which(cmd) is None:
            raise EnvironmentError("Required dependency \"{}\" not found".format(cmd))
    
    scripts = ['import_data','flag_calib_split','dirty_cont_image','contsub_dirty_image','clean_image','cleanup','common_functions','moment_zero']
    for script in scripts:
        if not os.access(script+'.py', os.R_OK):
            os.symlink(cgatcore_params['scripts']+script+'.py',script+'.py')
        if not os.access(script+'.py', os.R_OK):
            os.unlink(script+'.py')
            raise FileNotFoundError('{0}.py file is required but not found in the scripts directory ({1}).'.format(script,cgatcore_params['scripts']))

    open(outfile, 'a').close()
    
    

@transform(dependency_check, suffix('dependency_check.done'), 'import_data.done'.format(cgatcore_params['project']))
def import_data(infile,outfile):
    statement = 'casa -c import_data.py {} && touch import_data.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    
@transform(import_data, suffix('import_data.done'.format(cgatcore_params['project'])), 'flag_calib_split.done'.format(cgatcore_params['project']))
def flag_calib_split(infile,outfile):
    statement = 'casa -c flag_calib_split.py {} && touch flag_calib_split.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    
@transform(flag_calib_split, suffix('flag_calib_split.done'.format(cgatcore_params['project'])), 'dirty_cont_image.done'.format(cgatcore_params['project']))
def dirty_cont_image(infile,outfile):
    statement = 'casa -c dirty_cont_image.py {} && touch dirty_cont_image.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    
@transform(dirty_cont_image, suffix('dirty_cont_image.done'.format(cgatcore_params['project'])), 'contsub_dirty_image.done'.format(cgatcore_params['project']))
def contsub_dirty_image(infile,outfile):
    statement = 'casa -c contsub_dirty_image.py {} && touch contsub_dirty_image.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    
@transform(contsub_dirty_image, suffix('contsub_dirty_image.done'.format(cgatcore_params['project'])), 'clean_image.done'.format(cgatcore_params['project']))
def clean_image(infile,outfile):
    statement = 'casa -c clean_image.py {} && touch clean_image.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)

@transform(clean_image, suffix('clean_image.done'.format(cgatcore_params['project'])), 'moment_zero.done'.format(cgatcore_params['project']))
def moment_zero(infile,outfile):
    statement = 'casa -c moment_zero.py {} && touch moment_zero.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    
@transform(moment_zero, suffix('moment_zero.done'.format(cgatcore_params['project'])), 'cleanup.done'.format(cgatcore_params['project']))
def cleanup(infile,outfile):
    statement = 'casa -c cleanup.py {} && touch cleanup.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    

def main(argv=None):
    if argv is None:
        argv = sys.argv
    P.main(argv)

if __name__ == "__main__":
    sys.exit(P.main(sys.argv))
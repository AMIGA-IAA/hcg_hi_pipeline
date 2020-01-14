import imp
imp.load_source('common_functions','common_functions.py')
import common_functions as cf

def cleanup(config,logger):
    """
    Deleted non-essential files at the end of the pipeline.
    Uses the 'cleanup_level' parameter. The levels are as follows:
    1) Calibration and flagging tabled deleted as well as CASA .last files.
    2) In addition to 1, the full (not split) MS is deleted along with the dirty images amd non-essential output from tclean.
    3) Everything except the final fits cubes and the summary information is deleted.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    cln_lvl = config['global']['cleanup_level']
    logger.info('Starting level {} cleanup.'.format(cln_lvl))
    if cln_lvl >= 1:
        logger.info('Deleting CASA .last files.')
        del_list = glob.glob('./*.last')
        for file_path in del_list:
            os.remove(file_path)
        logger.info('Deleting calibration tables.')
        shutil.rmtree('./cal_tabs')
        logger.info('Deleting flag tables.')
        shutil.rmtree('./{}.flagversions'.format(msfile))
    if cln_lvl >= 2:
        logger.info('Deleting full measurement set.')
        shutil.rmtree('./{}'.format(msfile))        
        logger.info('Deleting dirty images.')
        del_list = glob.glob(img_dir+'*.dirty.*')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting CLEANing masks.')
        del_list = glob.glob(img_dir+'*.mask')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting CLEAN models.')
        del_list = glob.glob(img_dir+'*.model')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting primary beam and PSF models.')
        del_list = glob.glob(img_dir+'*.pb')
        for file_path in del_list:
            shutil.rmtree(file_path)
        del_list = glob.glob(img_dir+'*.psf')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting weighting.')
        del_list = glob.glob(img_dir+'*.sumwt')
        for file_path in del_list:
            shutil.rmtree(file_path)
    if cln_lvl >= 3:
        logger.info('Deleting split measurement sets.')
        shutil.rmtree(src_dir)
        logger.info('Deleting CLEAN residuals.')
        del_list = glob.glob(img_dir+'*.residual')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting image files (except fits).')
        del_list = glob.glob(img_dir+'*.image*')
        for file_path in del_list:
            shutil.rmtree(file_path)
    logger.info('Cleanup completed.')

# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])

#Cleanup unwanted files
cleanup(config,logger)
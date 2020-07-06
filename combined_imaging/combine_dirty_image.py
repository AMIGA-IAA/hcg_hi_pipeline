import glob, numpy
import imp
imp.load_source('common_functions','common_functions.py')
import common_functions as cf

# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)

HCG = config['combine']['hcg']
proj_IDs = config['combine']['proj_ids']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = 'HCG{}.log'.format(str(HCG)),
                    LOG_FILE_ERROR = 'HCG{}_errors.log'.format(str(HCG)), new_log=True) # Set up your logger

logger.info('Starting joint (dirty) imaging of HCG {0} from the projects: {1}'.format(str(HCG),proj_IDs))

msfiles = []
for proj in proj_IDs:
    msfile = '../{0}/sources/HCG{1}*.*split.contsub'.format(proj,str(HCG))
    new_files = glob.glob(msfile)
    if len(new_files) > 0:
        msfiles.extend(new_files)
        logger.info('MS file(s) added to combine list: {}'.format(new_files))
    else:
        logger.warning('MS not found: {}'.format(msfile))
        
logger.info('Setting relative weights of each MS.')
for msfile in msfiles:
    command = "initweights(vis='{0}', wtmode='nyq')".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)
        
logger.info('Starting to make combined dirty image.')

img_dir = 'HCG'+str(HCG)

img_param = config['image']
img_param['msfiles'] = msfiles
img_param['img_dir'] = img_dir
img_param['HCG'] = HCG
img_param['clean_thresh'] = 2.5*img_param['rms']
command = "tclean(vis={msfiles}, imagename='{img_dir}/HCG{HCG}.dirty', cell='{pix_size}', imsize={im_size}, spw='{im_chns}', specmode='cube', outframe='bary', veltype='radio', restfreq='{rest_freq}', gridder='mosaic', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='multiscale', scales={scales}, weighting='briggs', robust={robust}, pbcor=True, niter=0, gain=0.1, cyclefactor=2.0, interactive=False, threshold='{clean_thresh}mJy', usemask='auto-multithresh', phasecenter='{phasecenter}')".format(**img_param)
logger.info('Executing command: '+command)
exec(command)
cf.check_casalog(config,config_raw,logger,casalog)

logger.info('Completed joint (dirty) imaging of HCG {0}.'.format(str(HCG)))

logger.info('Moving CASA log to source directory.')

os.system('mv {0} HCG{1}/.'.format(casalog.logfile(),str(HCG)))
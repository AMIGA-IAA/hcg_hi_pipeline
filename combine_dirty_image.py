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
    msfile = '../{0}/sources/HCG{1}.split.contsub'.format(proj,str(HCG))
    if os.path.exists(msfile):
        msfiles.append(msfile)
        logger.info('MS file added to combine list: {}'.format(msfile))
    else:
        logger.warning('MS not found: {}'.format(msfile))
        
logger.info('Starting to make combined dirty image.')

img_dir = 'HCG'+str(HCG)

img_param = config['image']
command = "tclean(vis={0}, imagename='{1}/HCG{2}.dirty', cell='{3}', imsize={4}, spw='{5}', specmode='cube', outframe='bary', veltype='radio', restfreq='{6}', gridder='mosaic', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='multiscale', scales={7}, weighting='briggs', robust={8}, restoringbeam='common', pbcor=True, niter=0, gain=0.1, cyclefactor=2.0, interactive=False, threshold='{9}mJy', usemask='auto-multithresh', phasecenter='{10}')".format(msfiles,img_dir,HCG,img_param['pix_size'],img_param['im_size'],img_param['im_chns'],img_param['rest_freq'],img_param['scales'],img_param['robust'],str(2.5*img_param['rms']),img_param['phasecenter'])
logger.info('Executing command: '+command)
exec(command)
cf.check_casalog(config,config_raw,logger,casalog)

logger.info('Completed joint (dirty) imaging of HCG {0}.'.format(str(HCG)))
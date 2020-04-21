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
                    LOG_FILE_ERROR = 'HCG{}_errors.log'.format(str(HCG))) # Set up your logger

logger.info('Starting joint (clean) imaging of HCG {0} from the projects: {1}'.format(str(HCG),proj_IDs))

msfiles = []
for proj in proj_IDs:
    msfile = '../{0}/sources/HCG{1}.split.contsub'.format(proj,str(HCG))
    if os.path.exists(msfile):
        msfiles.append(msfile)
        logger.info('MS file added to combine list: {}'.format(msfile))
    else:
        logger.warning('MS not found: {}'.format(msfile))
        
logger.info('Starting to make combined clean image.')

img_dir = 'HCG'+str(HCG)

img_param = config['image']
command = "tclean(vis={0}, imagename='{1}/HCG{2}', cell='{3}', imsize={4}, spw='{5}', specmode='cube', outframe='bary', veltype='radio', restfreq='{6}', gridder='mosaic', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='multiscale', scales={7}, weighting='briggs', robust={8}, restoringbeam='common', pbcor=True, niter=100000, gain=0.1, cyclefactor=2.0, interactive=False, threshold='{9}mJy', usemask='auto-multithresh', phasecenter='{10}', sidelobethreshold={11}, noisethreshold={12}, lownoisethreshold={13}, minbeamfrac={14}, negativethreshold={15})".format(msfiles,img_dir,HCG,img_param['pix_size'],img_param['im_size'],img_param['im_chns'],img_param['rest_freq'],img_param['scales'],img_param['robust'],str(2.5*img_param['rms']),img_param['phasecenter'],img_param['automask_sl'],img_param['automask_ns'],img_param['automask_lns'],img_param['automask_mbf'],img_param['automask_neg'])
logger.info('Executing command: '+command)
exec(command)
cf.check_casalog(config,config_raw,logger,casalog)

logger.info('Completed joint (clean) imaging of HCG {0}.'.format(str(HCG)))

logger.info('Starting generation of fits files.')

ia.open('{0}/HCG{1}.dirty.image'.format(img_dir,HCG))
coords = ia.coordsys()
coord_chn = False
if 'J2000' not in coords.referencecode()[0]:
    coord_chn = True
    logger.info('Coordinate system not J2000. Image will be regridded.')
    command = "imregrid(imagename='{0}/HCG{1}.image', template='J2000', output='{0}/HCG{1}.image.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,HCG)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)
    command = "imregrid(imagename='{0}/HCG{1}.image.pbcor', template='J2000', output='{0}/HCG{1}.image.pbcor.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,HCG)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)
coords.done()
ia.close()

fitsname = 'HCG{}_HI.fits'.format(str(HCG))
logger.info('Saving image cube as {}'.format(fitsname))
if coord_chn:
    imagename = 'HCG{0}.image.J2000'.format(str(HCG))
else:
    imagename = 'HCG{0}.image'.format(str(HCG))
command = "exportfits(imagename='{0}/{1}', fitsimage='{0}/{2}', velocity=True,optical=False,overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(img_dir,imagename,fitsname)
logger.info('Executing command: '+command)
exec(command)
cf.check_casalog(config,config_raw,logger,casalog)
fitsname = 'HCG{}_HI.pbcor.fits'.format(str(HCG))
logger.info('Saving primary beam corrected image cube as {}'.format(fitsname))
if coord_chn:
    imagename = 'HCG{0}.image.pbcor.J2000'.format(str(HCG))
else:
    imagename = 'HCG{0}.image.pbcor'.format(str(HCG))
command = "exportfits(imagename='{0}/{1}', fitsimage='{0}/{2}', velocity=True,optical=False,overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(img_dir,imagename,fitsname)
logger.info('Executing command: '+command)
exec(command)
cf.check_casalog(config,config_raw,logger,casalog)

logger.info('Completed generating fits files.')

logger.info('Moving logs to source directory.')

os.system('mv casa-*.log HCG{}/.'.format(str(HCG)))
os.system('mv HCG{0}.log HCG{0}/.'.format(str(HCG)))
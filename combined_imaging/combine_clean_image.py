import glob, numpy
import imp
imp.load_source('common_functions','common_functions.py')
import common_functions as cf

# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)

name = str(config['combine']['name'])
proj_IDs = config['combine']['proj_ids']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(str(name)),
                    LOG_FILE_ERROR = '{}_errors.log'.format(str(name))) # Set up your logger

logger.info('Starting joint (clean) imaging of {0} from the projects: {1}'.format(str(name),proj_IDs))

if not bool(config['combine']['mstransform']):
    msfiles = []
    for proj in proj_IDs:
        msfile = '../{0}/sources/{1}*.*split.contsub'.format(proj,str(name))
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
        
    logger.info('Starting to make combined clean image.')

    img_dir = name

    img_param = config['image']
    img_param['msfiles'] = msfiles
    img_param['img_dir'] = img_dir
    img_param['name'] = name
    img_param['clean_thresh'] = 2.5*img_param['rms']
    if not config_raw.has_option('image','restoringbeam'):
        command = "tclean(vis={msfiles}, imagename='{img_dir}/{name}', cell='{pix_size}', imsize={im_size}, spw='{im_chns}', specmode='cube', outframe='bary', veltype='radio', restfreq='{rest_freq}', gridder='mosaic', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='multiscale', scales={scales}, weighting='briggs', robust={robust}, restoringbeam='common', pbcor=True, niter=100000, gain=0.1, cyclefactor=2.0, interactive=False, threshold='{clean_thresh}mJy', usemask='auto-multithresh', phasecenter='{phasecenter}', sidelobethreshold={automask_sl}, noisethreshold={automask_ns}, lownoisethreshold={automask_lns}, minbeamfrac={automask_mbf}, negativethreshold={automask_neg})".format(**img_param)
    else:
        command = "tclean(vis={msfiles}, imagename='{img_dir}/{name}', cell='{pix_size}', imsize={im_size}, spw='{im_chns}', specmode='cube', outframe='bary', veltype='radio', restfreq='{rest_freq}', gridder='mosaic', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='multiscale', scales={scales}, weighting='briggs', robust={robust}, restoringbeam={restoringbeam}, pbcor=True, niter=100000, gain=0.1, cyclefactor=2.0, interactive=False, threshold='{clean_thresh}mJy', usemask='auto-multithresh', phasecenter='{phasecenter}', sidelobethreshold={automask_sl}, noisethreshold={automask_ns}, lownoisethreshold={automask_lns}, minbeamfrac={automask_mbf}, negativethreshold={automask_neg})".format(**img_param)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)

    logger.info('Completed joint (clean) imaging of {0}.'.format(name))
else:
    logger.info('Starting to make combined clean image.')

    img_dir = name

    img_param = config['image']
    img_param['img_dir'] = img_dir
    img_param['name'] = name
    img_param['clean_thresh'] = 2.5*img_param['rms']
    if not config_raw.has_option('image','restoringbeam'):
        command = "tclean(vis='{name}.ms', imagename='{img_dir}/{name}', cell='{pix_size}', imsize={im_size}, spw='{im_chns}', specmode='cube', outframe='bary', veltype='radio', restfreq='{rest_freq}', gridder='mosaic', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='multiscale', scales={scales}, weighting='briggs', robust={robust}, restoringbeam='common', pbcor=True, niter=100000, gain=0.1, cyclefactor=2.0, interactive=False, threshold='{clean_thresh}mJy', usemask='auto-multithresh', phasecenter='{phasecenter}', sidelobethreshold={automask_sl}, noisethreshold={automask_ns}, lownoisethreshold={automask_lns}, minbeamfrac={automask_mbf}, negativethreshold={automask_neg})".format(**img_param)
    else:
        command = "tclean(vis='{name}.ms', imagename='{img_dir}/{name}', cell='{pix_size}', imsize={im_size}, spw='{im_chns}', specmode='cube', outframe='bary', veltype='radio', restfreq='{rest_freq}', gridder='mosaic', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='multiscale', scales={scales}, weighting='briggs', robust={robust}, restoringbeam={restoringbeam}, pbcor=True, niter=100000, gain=0.1, cyclefactor=2.0, interactive=False, threshold='{clean_thresh}mJy', usemask='auto-multithresh', phasecenter='{phasecenter}', sidelobethreshold={automask_sl}, noisethreshold={automask_ns}, lownoisethreshold={automask_lns}, minbeamfrac={automask_mbf}, negativethreshold={automask_neg})".format(**img_param)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)

    logger.info('Completed joint (clean) imaging of {0}.'.format(name))

logger.info('Starting generation of fits files.')

ia.open('{0}/{1}.dirty.image'.format(img_dir,name))
coords = ia.coordsys()
coord_chn = False
if 'J2000' not in coords.referencecode()[0]:
    coord_chn = True
    logger.info('Coordinate system not J2000. Image will be regridded.')
    command = "imregrid(imagename='{0}/{1}.image', template='J2000', output='{0}/{1}.image.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,name)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)
    command = "imregrid(imagename='{0}/{1}.image.pbcor', template='J2000', output='{0}/{1}.image.pbcor.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,name)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)
coords.done()
ia.close()

fitsname = '{}_HI.fits'.format(name)
logger.info('Saving image cube as {}'.format(fitsname))
if coord_chn:
    imagename = '{0}.image.J2000'.format(name)
else:
    imagename = '{0}.image'.format(name)
command = "exportfits(imagename='{0}/{1}', fitsimage='{0}/{2}', velocity=True,optical=False,overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(img_dir,imagename,fitsname)
logger.info('Executing command: '+command)
exec(command)
cf.check_casalog(config,config_raw,logger,casalog)
fitsname = '{}_HI.pbcor.fits'.format(name)
logger.info('Saving primary beam corrected image cube as {}'.format(fitsname))
if coord_chn:
    imagename = '{0}.image.pbcor.J2000'.format(name)
else:
    imagename = '{0}.image.pbcor'.format(name)
command = "exportfits(imagename='{0}/{1}', fitsimage='{0}/{2}', velocity=True,optical=False,overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(img_dir,imagename,fitsname)
logger.info('Executing command: '+command)
exec(command)
cf.check_casalog(config,config_raw,logger,casalog)

logger.info('Completed generating fits files.')

logger.info('Moving logs to source directory.')

if bool(config['combine']['mstransform']):
    os.system('mv {0}.ms {0}/.'.format(name))
os.system('mv {0} {1}/.'.format(casalog.logfile(),name))
os.system('mv {0}.log {0}/.'.format(name))
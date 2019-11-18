import imp
imp.load_source('common_functions','common_functions.py')
from common_functions import *

def contsub(msfile,config,config_raw,config_file,logger):
    """
    Subtracts the continuum from each of the science target MSs.
    If the no line free range is set then the user is queried (in interactive mode) and the configuration file updated.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting continuum subtraction.')
    contsub = config['continuum_subtraction']
    calib = config['calibration']
    src_dir = config['global']['src_dir']+'/'
    logger.info('Checking for line free channel ranges in parameters.')
    reset_ch = False
    if len(contsub['linefree_ch']) == 0 or len(contsub['linefree_ch']) != len(calib['targets']):
        reset_ch = True
        if len(contsub['linefree_ch']) < len(calib['targets']):
            logger.warning('There are more target fields than channel ranges. Appending blank ranges.')
            while len(contsub['linefree_ch']) < len(calib['targets']):
                contsub['linefree_ch'].append('')
        elif len(contsub['linefree_ch']) > len(calib['targets']):
            logger.warning('There are more channel ranges than target fields.')
            logger.info('Current channel ranges: {}'.format(contsub['linefree_ch']))
            logger.warning('The channel range list will now be truncated to match the number of targets.')
            contsub['linefree_ch'] = contsub['linefree_ch'][:len(calib['targets'])]
    elif interactive:
        print('Current line free channels set as:')
        for i in range(len(contsub['linefree_ch'])):
            print('{0}: {1}'.format(calib['targets'][i],contsub['linefree_ch'][i]))
        resp = str(raw_input('Do you want revise the line free channels (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_ch = True
    if reset_ch:
        if not interactive:
            logger.critical('The number of line free channel ranges provided does not match the number of targets.')
            logger.info('Line free change ranges: {}'.format(contsub['linefree_ch']))
            logger.info('Targets: {}'.format(calib['targets']))
            sys.exit(-1)
        else:
            print('For each target enter the line free channels in the following format:\nspwID1:min_ch1~max_ch1;min_ch2~max_ch2,spwID2:min_ch3~max_ch3 etc.')
            for i in range(len(calib['targets'])):
                contsub['linefree_ch'][i] = uinput('Line free channels for {}: '.format(calib['targets'][i]), contsub['linefree_ch'][i])
                logger.info('Setting line free channels for {0} as: {1}.'.format(calib['targets'][i], contsub['linefree_ch'][i]))
            logger.info('Updating config file to set line free channels.')
            config_raw.set('continuum_subtraction','linefree_ch',contsub['linefree_ch'])
            configfile = open(config_file,'w')
            config_raw.write(configfile)
            configfile.close()
    logger.info('Line free channels set as: {}.'.format(contsub['linefree_ch']))
    logger.info('For the targets: {}.'.format(calib['targets']))
    for i in range(len(calib['targets'])):
        target = calib['targets'][i]
        chans = contsub['linefree_ch'][i]
        spws = chans.split(',')
        for i in range(len(spws)):
            spw = spws[i].strip()
            spw = spw[0]
            spws[i] = spw
        logger.info('Subtracting the continuum from field: {}'.format(target))
        command = "uvcontsub(vis='{0}{1}'+'.split', field='{1}', fitspw='{2}', spw='{3}', excludechans=False,combine='',solint='int', fitorder={4}, want_cont={5})".format(src_dir,target,chans,','.join(spws),contsub['fitorder'],contsub['save_cont'])
        logger.info('Executing command: '+command)
        exec(command)
    logger.info('Completed continuum subtraction.')
    


def plot_spec(config,logger):
    """
    For each SPW and each science target amplitude vs channel and amplitude vs velocity are plotted.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting plotting amplitude spectrum.')
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir,logger)
    calib = config['calibration']
    targets = calib['targets']
    src_dir = config['global']['src_dir']+'/'
    for target in targets:
        msmd.open('{0}{1}.split'.format(src_dir,target))
        spws = msmd.spwsforfield('{}'.format(target))
        msmd.close()
        for spw in spws:
            plot_file = plots_obs_dir+'{0}_amp_chn_spw{1}.png'.format(target,spw)
            logger.info('Plotting amplitude vs channel to {}'.format(plot_file))
            plotms(vis=src_dir+target+'.split.contsub', xaxis='chan', yaxis='amp',
                   ydatacolumn='corrected', spw=str(spw), plotfile=plot_file,
                   expformat='png', overwrite=True, showgui=False)
            plot_file = plots_obs_dir+'{0}_amp_vel_spw{1}.png'.format(target,spw)
            logger.info('Plotting amplitude vs velocity to {}'.format(plot_file))
            plotms(vis=src_dir+target+'.split.contsub', xaxis='velocity', yaxis='amp',
                   ydatacolumn='corrected', spw=str(spw), plotfile=plot_file,
                   expformat='png', overwrite=True, showgui=False,
                   freqframe='BARY', restfreq=str(config['global']['rest_freq']), veldef='OPTICAL')
    logger.info('Completed plotting amplitude spectrum.')
            
def dirty_image(config,config_raw,config_file,logger):
    """
    Generates a dirty (continuum subtracted) image of each science target.
    Checks that the pixel size, image size, and line emission channels are set (will prompt user if in interactive mode).
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting making dirty image.')
    calib = config['calibration']
    contsub = config['continuum_subtraction']
    rest_freq = config['global']['rest_freq']
    targets = calib['targets']
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    makedir('./'+img_dir,logger)
    logger.info('Removing any existing dirty images.')
    for target in targets:
        del_list = glob.glob(img_dir+'{}.dirty*'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
    logger.info('Checking clean parameters for dirty image.')
    reset_cln = False
    if len(cln_param['pix_size']) == 0 or len(cln_param['pix_size']) != len(targets):
        if not interactive:
            logger.critical('The number of pixel sizes provided does not match the number of targets.')
            logger.info('Pixel sizes: {}'.format(cln_param['pix_size']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['pix_size']) < len(targets):
            logger.warning('There are more target fields than pixel sizes. Appending blanks.')
            while len(cln_param['pix_size']) < len(targets):
                cln_param['pix_size'].append('')
        elif len(cln_param['pix_size']) > len(targets):
            logger.warning('There are more pixel sizes than target fields.')
            logger.info('Current pixel sizes: {}'.format(cln_param['pix_size']))
            logger.warning('The pixel size list will now be truncated to match the number of targets.')
            cln_param['pix_size'] = cln_param['pix_size'][:len(targets)]
    elif interactive:
        print('Current pixel sizes set as:')
        for i in range(len(cln_param['pix_size'])):
            print('{0}: {1}'.format(targets[i],cln_param['pix_size'][i]))
        resp = str(raw_input('Do you want revise the pixel sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired pixel size:')
        for i in range(len(targets)):
            cln_param['pix_size'][i] = uinput('Pixel size for {}: '.format(targets[i]), cln_param['pix_size'][i])
            logger.info('Setting pixel size for {0} as: {1}.'.format(targets[i], cln_param['pix_size'][i]))
        logger.info('Updating config file to set pixel sizes.')
        config_raw.set('clean','pix_size',cln_param['pix_size'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Pixel sizes set as: {}.'.format(cln_param['pix_size']))
    logger.info('For the targets: {}.'.format(targets))
    reset_cln = False
    if len(cln_param['im_size']) == 0 or len(cln_param['im_size']) != len(targets):
        if not interactive:
            logger.critical('The number of image sizes provided does not match the number of targets.')
            logger.info('Image sizes: {}'.format(cln_param['im_size']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['im_size']) < len(targets):
            logger.warning('There are more target fields than image sizes. Appending blanks.')
            while len(cln_param['im_size']) < len(targets):
                cln_param['im_size'].append('')
        elif len(cln_param['im_size']) > len(targets):
            logger.warning('There are more image sizes than target fields.')
            logger.info('Current image sizes: {} pixels.'.format(cln_param['im_size']))
            logger.warning('The image size list will now be truncated to match the number of targets.')
            cln_param['im_size'] = cln_param['im_size'][:len(targets)]
    elif interactive:
        print('Current images sizes set as:')
        for i in range(len(cln_param['im_size'])):
            print('{0}: {1}'.format(targets[i],cln_param['im_size'][i]))
        resp = str(raw_input('Do you want revise the image sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired image size:')
        for i in range(len(targets)):
            print('Note: The pixel size for this target was set to: {}'.format(cln_param['pix_size'][i]))
            cln_param['im_size'][i] = uinput('Image size for {}: '.format(targets[i]), cln_param['im_size'][i])
            logger.info('Setting image size for {0} as: {1} x {2}.'.format(targets[i], cln_param['im_size'][i],cln_param['pix_size'][i]))
        logger.info('Updating config file to set image sizes.')
        config_raw.set('clean','im_size',cln_param['im_size'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Image sizes set as: {} pixels.'.format(cln_param['im_size']))
    logger.info('For the targets: {}.'.format(targets))
    reset_cln = False
    if len(cln_param['line_ch']) == 0 or len(cln_param['line_ch']) != len(targets):
        if not interactive:
            logger.critical('The number of line channel ranges provided does not match the number of targets.')
            logger.info('Pixel sizes: {}'.format(cln_param['line_ch']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['line_ch']) < len(targets):
            logger.warning('There are more target fields than channel ranges. Appending blank ranges.')
            while len(cln_param['line_ch']) < len(targets):
                cln_param['line_ch'].append('')
        elif len(cln_param['line_ch']) > len(targets):
            logger.warning('There are more channel ranges than target fields.')
            logger.info('Current channel ranges: {}'.format(cln_param['line_ch']))
            logger.warning('The channel range list will now be truncated to match the number of targets.')
            cln_param['line_ch'] = cln_param['line_ch'][:len(targets)]
    elif interactive:
        print('Current image channels set as:')
        for i in range(len(cln_param['line_ch'])):
            print('{0}: {1}'.format(targets[i],cln_param['line_ch'][i]))
        resp = str(raw_input('Do you want revise the channels that will be imaged (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the channels you want to image in the following format:\nspwID:min_ch~max_ch')
        for i in range(len(targets)):
            print('Note: The continuum channels for this target were set to: {}'.format(contsub['linefree_ch'][i]))
            cln_param['line_ch'][i] = uinput('Channels to image for {}: '.format(targets[i]), cln_param['line_ch'][i])
            logger.info('Setting image channels for {0} as: {1}.'.format(targets[i], cln_param['line_ch'][i]))
        logger.info('Updating config file to set channels to be imaged.')
        config_raw.set('clean','line_ch',cln_param['line_ch'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Line emission channels set as: {}.'.format(cln_param['line_ch']))
    logger.info('For the targets: {}.'.format(targets))
    for i in range(len(targets)):
        target = targets[i]
        logger.info('Making dirty image of {} (line only).'.format(target))
        command = "tclean(vis='{0}{1}'+'.split.contsub', field='{1}', imagename='{2}{1}'+'.dirty', cell='{3}', imsize=[{4},{4}], specmode='cube', outframe='bary', veltype='radio', restfreq='{5}', gridder='wproject', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='hogbom', weighting='briggs', robust={6}, restoringbeam='common', niter=0, interactive=False)".format(src_dir,target,img_dir,cln_param['pix_size'][i],cln_param['im_size'][i],rest_freq,cln_param['robust'])
        logger.info('Executing command: '+command)
        exec(command)
    logger.info('Completed making dirty image.')
    
    
# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = get_logger(LOG_FILE_INFO  = '{}_contsub_dirty_image.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])

#Contsub and make dity image
contsub(msfile,config,config_raw,config_file,logger)
plot_spec(config,logger)
del_list = glob.glob(config['global']['img_dir']+'/'+'*.dirty.*')
if len(del_list) > 0:
    logger.info('Deleting existing dirty image(s): {}'.format(del_list))
    for file_path in del_list:
        shutil.rmtree(file_path)
dirty_image(config,config_raw,config_file,logger)
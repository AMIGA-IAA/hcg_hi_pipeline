import imp, glob, shutil, numpy
imp.load_source('common_functions','common_functions.py')
import common_functions as cf

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
    targets = calib['target_names'][:]
    fields = calib['targets'][:]
    for i in range(len(targets)):
        target = targets[i]
        if 'spw' in target:
            inx = target.index('.spw')
            target_name = target[:inx]
            if target_name in calib['target_names'][i-1]:
                fields.insert(i,fields[i-1])
    reset_ch = False
    if len(contsub['linefree_ch']) == 0 or len(contsub['linefree_ch']) != len(targets):
        reset_ch = True
        if len(contsub['linefree_ch']) < len(targets):
            logger.warning('There are more target fields than channel ranges. Appending blank ranges.')
            while len(contsub['linefree_ch']) < len(targets):
                contsub['linefree_ch'].append('')
        elif len(contsub['linefree_ch']) > len(targets):
            logger.warning('There are more channel ranges than target fields.')
            logger.info('Current channel ranges: {}'.format(contsub['linefree_ch']))
            logger.warning('The channel range list will now be truncated to match the number of targets.')
            contsub['linefree_ch'] = contsub['linefree_ch'][:len(targets)]
    elif interactive:
        print('Current line free channels set as:')
        for i in range(len(contsub['linefree_ch'])):
            print('{0}: {1}'.format(targets[i],contsub['linefree_ch'][i]))
        resp = str(raw_input('Do you want revise the line free channels (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_ch = True
    if reset_ch:
        if not interactive:
            logger.critical('The number of line free channel ranges provided does not match the number of targets.')
            logger.info('Line free change ranges: {}'.format(contsub['linefree_ch']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        else:
            print('For each target enter the line free channels in the following format:\nspwID1:min_ch1~max_ch1;min_ch2~max_ch2,spwID2:min_ch3~max_ch3;min_ch4~max_ch4')
            for i in range(len(targets)):
                contsub['linefree_ch'][i] = cf.uinput('Line free channels for {}: '.format(targets[i]), contsub['linefree_ch'][i])
                logger.info('Setting line free channels for {0} as: {1}.'.format(targets[i], contsub['linefree_ch'][i]))
                if type(contsub['fitorder']) == type(1):
                    order_set = False
                    while not order_set:
                        try:
                            order = int(cf.uinput('Set the fit order for {}: '.format(targets[i]), contsub['fitorder']))
                            if order >= 0:
                                order_set = True
                        except ValueError:
                            print 'Fit order must be an integer.'
                    if order != contsub['fitorder'] and len(targets) > 1:
                        order_list = list(numpy.zeros(len(targets),dtype='int')+contsub['fitorder'])
                        order_list[i] = order
                        order = order_list
                    contsub['fitorder'] = order
                else:
                    order_set = False
                    while not order_set:
                        try:
                            order = int(cf.uinput('Set the fit order for {}: '.format(targets[i]), contsub['fitorder'][i]))
                            if order >= 0:
                                order_set = True
                                contsub['fitorder'] = order
                        except ValueError:
                            print 'Fit order must be an integer.'
            logger.info('Updating config file to set line free channels and fit orders.')
            config_raw.set('continuum_subtraction','linefree_ch',contsub['linefree_ch'])
            config_raw.set('continuum_subtraction','fitorder',contsub['fitorder'])
            configfile = open(config_file,'w')
            config_raw.write(configfile)
            configfile.close()
    logger.info('Line free channels set as: {}.'.format(contsub['linefree_ch']))
    logger.info('Fit order(s) set as: {}.'.format(contsub['fitorder']))
    logger.info('For the targets: {}.'.format(targets))
    extra_splits = 0
    for i in range(len(targets)):
        target = targets[i]
        field = fields[i]
        chans = contsub['linefree_ch'][i]
        spws = chans.split(',')
        for i in range(len(spws)):
            spw = spws[i].strip()
            spw = spw[0]
            spws[i] = spw
        logger.info('Subtracting the continuum from field: {}'.format(target))
        if type(contsub['fitorder']) == type(1):
            order = contsub['fitorder']
        else:
            order = contsub['fitorder'][i]
        command = "uvcontsub(vis='{0}{1}'+'.split', field='{2}', fitspw='{3}', spw='{4}', excludechans=False, combine='spw', solint='int', fitorder={5}, want_cont={6})".format(src_dir,target,field,chans,','.join(spws),order,contsub['save_cont'])
        logger.info('Executing command: '+command)
        exec(command)
        cf.check_casalog(config,config_raw,logger)
    logger.info('Completed continuum subtraction.')
    


def plot_spec(config,logger,contsub=False):
    """
    For each SPW and each science target amplitude vs channel and amplitude vs velocity are plotted.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting plotting amplitude spectrum.')
    plots_obs_dir = './plots/'
    cf.makedir(plots_obs_dir,logger)
    calib = config['calibration']
    targets = calib['target_names'][:]
    fields = calib['targets'][:]
    for i in range(len(targets)):
        target = targets[i]
        if 'spw' in target:
            inx = target.index('.spw')
            target_name = target[:inx]
            if target_name in calib['target_names'][i-1]:
                fields.insert(i,fields[i-1])
    src_dir = config['global']['src_dir']+'/'
    for i in range(len(targets)):
        target = targets[i]
        field = fields[i]
        if contsub:
            MS_list = glob.glob('{0}{1}*split.contsub'.format(src_dir,target))
        else:
            MS_list = glob.glob('{0}{1}*split'.format(src_dir,target))
        for MS in MS_list:
            if contsub:
                plot_file = plots_obs_dir+'{0}_contsub_amp_chn.png'.format(target)
            else:
                plot_file = plots_obs_dir+'{0}_amp_chn.png'.format(target)
            logger.info('Plotting amplitude vs channel to {}'.format(plot_file))
            plotms(vis=MS, xaxis='chan', yaxis='amp',
                   ydatacolumn='corrected', plotfile=plot_file,
                   expformat='png', overwrite=True, showgui=False)
            if not contsub:
                plot_file = plots_obs_dir+'{0}_amp_vel.png'.format(target)
                logger.info('Plotting amplitude vs velocity to {}'.format(plot_file))
                plotms(vis=MS, xaxis='velocity', yaxis='amp',
                       ydatacolumn='corrected', plotfile=plot_file,
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
    targets = calib['target_names'][:]
    fields = calib['targets'][:]
    for i in range(len(targets)):
        target = targets[i]
        if 'spw' in target:
            inx = target.index('.spw')
            target_name = target[:inx]
            if target_name in calib['target_names'][i-1]:
                fields.insert(i,fields[i-1])
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    cf.makedir('./'+img_dir,logger)
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
            cln_param['pix_size'][i] = cf.uinput('Pixel size for {}: '.format(targets[i]), cln_param['pix_size'][i])
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
            cln_param['im_size'][i] = cf.uinput('Image size for {}: '.format(targets[i]), cln_param['im_size'][i])
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
            cln_param['line_ch'][i] = cf.uinput('Channels to image for {}: '.format(targets[i]), cln_param['line_ch'][i])
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
        field = fields[i]
        logger.info('Making dirty image of {} (line only).'.format(target))
        command = "tclean(vis='{0}{1}'+'.split.contsub', field='{2}', imagename='{3}{1}'+'.dirty', cell='{4}', imsize=[{5},{5}], specmode='cube', outframe='bary', veltype='radio', restfreq='{6}', gridder='wproject', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='hogbom', weighting='briggs', robust={7}, restoringbeam='common', niter=0, interactive=False)".format(src_dir,target,field,img_dir,cln_param['pix_size'][i],cln_param['im_size'][i],rest_freq,cln_param['robust'])
        logger.info('Executing command: '+command)
        exec(command)
        cf.check_casalog(config,config_raw,logger)
                
    logger.info('Completed making dirty image.')
    
    
# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])

#Contsub
cf.check_casaversion(logger)
plot_spec(config,logger)
contsub(msfile,config,config_raw,config_file,logger)
plot_spec(config,logger,contsub=True)

#Remove previous dirty images
targets = config['calibration']['target_names']
for target in targets:
    del_list = glob.glob(config['global']['img_dir']+'/'+'{}.dirty.*'.format(target))
    if len(del_list) > 0:
        logger.info('Deleting existing dirty image(s): {}'.format(del_list))
        for file_path in del_list:
            shutil.rmtree(file_path)
    
#Make dirty image
dirty_image(config,config_raw,config_file,logger)

#Review and backup parameters file
cf.diff_pipeline_params(config_file,logger)
cf.backup_pipeline_params(config_file,logger)
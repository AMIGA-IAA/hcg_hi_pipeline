import imp, numpy
imp.load_source('common_functions','common_functions.py')
import common_functions as cf


def manual_flags(logger):
    """
    Apply manual flags from the file 'manual_flags.list'.
    """
    logger.info('Starting manual flagging.')
    if interactive:
        print("\nManual flags from 'manual_flags.list' are about to be applied.")
        print("It is strongly recommended that you inspect the data and modify (and save) 'manual_flags.list' appropriately before proceeding.\n")
        resp = str(raw_input('Do you want to proceed (y/n): '))
        while resp.lower() not in ['yes','ye','y']:
            resp = str(raw_input('Do you want to proceed (y/n): '))
    logger.info('Applying flags from manual_flags.list')
    try:
        flag_file = open('manual_flags.list', 'r')
        lines = flag_file.readlines()
        if lines == []:
            logger.warning("The file is empty. Continuing without manual flagging.")
        else:
            command = "flagdata(vis='{}', mode='list', action='apply', inpfile={})".format(msfile,lines)
            logger.info('Executing command: '+command)
            exec(command)
            logger.info('Completed manual flagging.')
        flag_file.close()
    except IOError:
        logger.warning("'manual_flags.list' does not exist. Continuing without manual flagging.")        

def base_flags(msfile, config,logger):
    """ 
    Sets basic initial data flags.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting basic flagging.')
    flag = config['flagging']
    tol = flag['shadow_tol'] 
    quack_int = flag['quack_int']
    logger.info('Flagging antennae with more than {} m of shadowing.'.format(tol))
    command = "flagdata(vis='{0}', mode='shadow', tolerance={1}, flagbackup=False)".format(msfile,tol)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Flagging zero amplitude data.')
    command = "flagdata(vis='{}', mode='clip', clipzeros=True, flagbackup=False)".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Flagging first {} s of every scan.'.format(quack_int))
    command = "flagdata(vis='{0}', mode='quack', quackinterval={1}, quackmode='beg', flagbackup=False)".format(msfile,quack_int)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed basic flagging.')

def tfcrop(msfile,config,logger):
    """
    Runs CASA's TFcrop flagging algorithm.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    flag = config['flagging']
    logger.info('Starting running TFCrop.')
    command = "flagdata(vis='{0}', mode='tfcrop', action='apply', display='', timecutoff={1}, freqcutoff={2}, flagbackup=False)".format(msfile,flag['timecutoff'],flag['freqcutoff'])
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed running TFCrop.')

def rflag(msfile,config,logger):
    """
    Runs CASA's rflag flagging algorithm.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    flag = config['flagging']
    thresh = flag['rthresh']
    logger.info('Starting running rflag with a threshold of {}.'.format(thresh))
    command = "flagdata(vis='{0}', mode='rflag', action='apply', datacolumn='corrected', freqdevscale={1}, timedevscale={1}, display='', flagbackup=False)".format(msfile,thresh)
    logger.info('Executing command: '+command)
    exec(command)
    exec(command)
    logger.info('Completed running rflag.')

def extend_flags(msfile,logger):
    """
    Extends existing flags.
    
    Input:
    msfile = Path to the MS. (String)
    """
    flag_version = 'extended'
    logger.info('Starting extending existing flags.')
    command = "flagdata(vis='{}', mode='extend', spw='', extendpols=True, action='apply', display='', flagbackup=False)".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    command = "flagdata(vis='{}', mode='extend', spw='', growtime=75.0, growfreq=90.0, action='apply', display='', flagbackup=False)".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed extending existing flags.')

def flag_sum(msfile,name,logger):
    """
    Writes a summary of the current flags to file.
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename where flags summary will be saved. (String) 
    """
    sum_dir = './summary/'
    cf.makedir(sum_dir,logger)
    out_file = sum_dir+'{0}.{1}flags.summary'.format(msfile,name)
    logger.info('Starting writing flag summary to: {}.'.format(out_file))
    flag_info = flagdata(vis=msfile, mode='summary')
    out_file = open(out_file, 'w')
    out_file.write('Total flagged data: {:.2%}\n\n'.format(flag_info['flagged']/flag_info['total']))
    logger.info('Total flagged data: {:.2%}'.format(flag_info['flagged']/flag_info['total']))
    out_file.write('Flagging per spectral window\n')
    for spw in flag_info['spw'].keys():
        out_file.write('SPW {0}: {1:.2%}\n'.format(spw,flag_info['spw'][spw]['flagged']/flag_info['spw'][spw]['total']))
    out_file.write('\nFlagging per field\n')
    for field in flag_info['field'].keys():
        out_file.write('{0}: {1:.2%}\n'.format(field,flag_info['field'][field]['flagged']/flag_info['field'][field]['total']))
    out_file.write('\nFlagging per antenna\n')
    for ant in flag_info['antenna'].keys():
        out_file.write('{0}: {1:.2%}\n'.format(ant,flag_info['antenna'][ant]['flagged']/flag_info['antenna'][ant]['total']))
    out_file.close()
    logger.info('Completed writing flag summary.')
    
def restore_flags(msfile,name,logger):
    """
    Restored the flag version corresponding to the named file.
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename for the flag version. (String) 
    """
    logger.info('Restoring flag version from: {}.'.format(name))
    command = "flagmanager(vis='{0}', mode='restore', versionname='{1}')".format(msfile,name)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed restoring flag version.')
    
def save_flags(msfile,name,logger):
    """
    Save the current flag version as "name".
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename for the flag version. (String) 
    """
    logger.info('Saving flag version as: {}.'.format(name))
    command = "flagmanager(vis='{0}', mode='save', versionname='{1}')".format(msfile,name)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed saving flag version.')
    
def rm_flags(msfile,name,logger):
    """
    Delete the flag version "name".
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename for the flag version. (String) 
    """
    logger.info('Removing flag version: {}.'.format(name))
    command = "flagmanager(vis='{0}', mode='delete', versionname='{1}')".format(msfile,name)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed removing flag version.')
    
def plot_flags(msfile,name,logger):
    """
    Make a plot with flagged and unflagged points coloured differently.
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename for the flag version. (String)
    """
    logger.info('Making flags plots for flag version: {}'.format(name))
    plots_obs_dir = './plots/'
    cf.makedir(plots_obs_dir,logger)
    plot_name = plots_obs_dir+'flag_plot_'+name
    
    calib = config['calibration']
    fields = calib['targets'][:]
    fields.extend(calib['bandcal'])
    fields.extend(calib['fluxcal'])
    fields.extend(calib['phasecal'])
    fields = list(set(fields))
    
    msmd.open(msfile)
    spw_IDs = []
    for field in fields:
        spw_IDs.extend(list(msmd.spwsforfield(field)))
    spw_IDs = list(set(list(spw_IDs)))
    nspw = len(spw_IDs)
    msmd.close()
    
    for field in fields:
        logger.info('Making flags plots for {}.'.format(field))
        plot_file = plot_name+'_'+field
        logger.info('Plotting amplitude vs frequency to {}'.format(plot_file+'_freq.png'))
        plotms(vis=msfile, xaxis='freq', yaxis='amp', field=field, plotfile=plot_file+'_freq.png',
               customflaggedsymbol=True, spw=','.join(numpy.array(spw_IDs,dtype='str')),
               averagedata=True, avgtime='60', expformat='png', overwrite=True, showgui=False)
        logger.info('Plotting amplitude vs time to {}'.format(plot_file+'_time.png'))
        plotms(vis=msfile, xaxis='time', yaxis='amp', field=field, plotfile=plot_file+'_time.png',
               customflaggedsymbol=True, spw=','.join(numpy.array(spw_IDs,dtype='str')),
               averagedata=True, avgchannel='5', expformat='png', overwrite=True, showgui=False)
    logger.info('Completed flags plots ')

def select_refant(msfile,config,config_raw,config_file,logger):
    """
    Checks if a reference antenna is set, if it has not been then the user is queried to set it.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting reference antenna selection.')
    calib = config['calibration']
    tb.open(msfile+'/ANTENNA')
    ant_names = tb.getcol('NAME')
    tb.close()
    if calib['refant'] not in ant_names:
        logger.warning('No valid reference antenna set. Requesting user input.')
        first = True
        print('\n\n\n')
        while calib['refant'] not in ant_names:
            if not first:
                print('\n\nString entered is not a valid antenna name.')
            print('Valid antenna names:\n{}\n'.format(ant_names))
            calib['refant'] = str(raw_input('Please select a reference antenna by name: '))
            first = False
        logger.info('Updating config file ({0}) to set reference antenna as {1}.'.format(config_file,calib['refant']))
        config_raw.set('calibration','refant',calib['refant'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
        logger.info('Completed reference antenna selection.')
    else:
        logger.info('Reference antenna already set as: {}.'.format(calib['refant']))

def set_fields(msfile,config,config_raw,config_file,logger):
    """
    Checks if the field intentions have already been set, if not then the user is queried.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting set field purposes.')
    calib = config['calibration']
    tb.open(msfile+'/FIELD')
    field_names = tb.getcol('NAME')
    tb.close()
    tb.open('{}/SPECTRAL_WINDOW'.format(msfile))
    spw_names = tb.getcol('NAME')
    if not config['importdata']['jvla']:
        spw_IDs = tb.getcol('DOPPLER_ID')
    else:
        spw_IDs = tb.getcol('FREQ_GROUP')
    nspw = len(spw_IDs)
    tb.close()
    std_flux_mods = ['3C48_L.im', '3C138_L.im', '3C286_L.im', '3C147_L.im']
    std_flux_names = {'0134+329': '3C48_L.im', '0137+331': '3C48_L.im', '3C48': '3C48_L.im', 'J0137+3309': '3C48_L.im',
                      '0518+165': '3C138_L.im', '0521+166': '3C138_L.im', '3C138': '3C138_L.im', 'J0521+1638': '3C138_L.im',
                      '1328+307': '3C286_L.im', '1331+305': '3C286_L.im', '3C286': '3C286_L.im', 'J1331+3030': '3C286_L.im',
                      '0538+498': '3C147_L.im', '0542+498': '3C147_L.im', '3C147': '3C147_L.im', 'J0542+4951': '3C147_L.im'}
    
    change_made = False
    if len(calib['targets']) == 0:
        if not interactive:
            logger.critical('There are no targets listed in the parameters file.')
            sys.exit(-1)
        else:
            logger.warning('No target field(s) set. Requesting user input.')
            print('\n\n')
            while True:
                target = ''
                print('Valid field names:\n{}\n'.format(field_names))
                target = str(raw_input('Please select a target field by name: '))
                if target not in field_names:
                    print('\n\nString entered is not a valid field name.')
                    continue
                else:
                    calib['targets'].append(target)
                    logger.info('{} set as a target field.'.format(target))
                    resp = ''
                    while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                        resp = str(raw_input('Do you want to add another target (y/n): '))
                    if resp.lower() in ['yes','ye','y']:
                        continue
                    else:
                        break
            change_made = True
    else:
        logger.info('Target field(s) already set as: {}.'.format(calib['targets']))
        if interactive:
            resp = str(raw_input('Do you want to add another target (y/n): '))
            while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                resp = str(raw_input('Do you want to add another target (y/n): '))
            if resp.lower() in ['yes','ye','y']:
                while True:
                    target = ''
                    print('Valid field names:\n{}\n'.format(field_names))
                    target = str(raw_input('Please select a target field by name: '))
                    if target not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        continue
                    else:
                        calib['targets'].append(target)
                        logger.info('{} set as a target field.'.format(target))
                        resp = ''
                        while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                            resp = str(raw_input('Do you want to add another target (y/n): '))
                        if resp.lower() in ['yes','ye','y']:
                            continue
                        else:
                            break
                change_made = True
                
                
    if len(calib['target_names']) == 0 or len(calib['target_names']) != len(calib['targets']):
        if len(calib['target_names']) < len(calib['targets']):
            logger.warning('There are more target fields than simple target names. Appending blanks.')
            while len(calib['target_names']) < len(calib['targets']):
                calib['target_names'].append('')
        elif len(calib['target_names']) > len(calib['targets']):
            logger.warning('There are more simple target names than target fields.')
            logger.info('Current simple target names: {}'.format(calib['target_names']))
            logger.warning('The simple target name list will now be truncated to match the number of targets.')
            calib['target_names'] = calib['target_names'][:len(calib['targets'])]
        change_made = True
    if interactive:
        print('Current simple target names set as:')
        print(calib['target_names'])
        print('For the targets:')
        print(calib['targets'])
        resp = ''
        while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
            resp = str(raw_input('Do you want to revise these names (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            change_made = True
            print('Note: Target names should NOT include spaces.')
            for i in range(len(calib['target_names'])):
                calib['target_names'][i] = cf.uinput('Enter simple name for target {}: '.format(calib['targets'][i]), calib['target_names'][i])
        else:
            pass
    if len(calib['target_names']) != len(calib['targets']):
        logger.warning('The number of targets ({0}) and simple names ({1}) do not match.'.format(len(calib['targets']),len(calib['target_names'])))
        logger.info('The original field names will be used.')
        logger.info('Replacing simple name: {}'.format(calib['target_names']))
        logger.info('With original field names: {}'.format(calib['targets']))
        calib['target_names'] = calib['targets']
        change_made = True
    elif numpy.any(numpy.array(calib['target_names'],dtype='str') == ''):
        inx = numpy.where(numpy.array(calib['target_names'],dtype='str') == '')[0]
        logger.warning('The following target have no simple names set: {}'.format(calib['targets'][inx]))
        logger.info('The original field names will be used.')
        calib['target_names'][inx] = calib['targets'][inx]
        change_made = True 
    
                
    if len(calib['targets']) != nspw:
        msmd.open(msfile)
        spw_IDs = []
        for target in calib['targets']:
            spw_IDs.extend(list(msmd.spwsforfield(target)))
        spw_IDs = list(set(list(spw_IDs)))
        spw_names = msmd.namesforspws(spw_IDs)
        nspw = len(spw_IDs)
        msmd.close()
        
    flux_cal_names_bad = False
    for i in range(len(calib['fluxcal'])):
        if calib['fluxcal'][i] not in field_names:
            flux_cal_names_bad = True
            if not interactive:
                logger.critical('Illegal name for flux calibrator: {}'.format(calib['fluxcal'][i]))
                sys.exit(-1)
    if flux_cal_names_bad or len(calib['fluxcal']) != nspw:
        if nspw == 1:
            if not interactive:
                logger.critical('No valid flux calibrator set.')
                sys.exit(-1)
            else:
                logger.warning('No valid flux calibrator set. Requesting user input.')
                if len(calib['fluxcal']) == 0:
                    calib['fluxcal'].append('')
                first = True
                while calib['fluxcal'][0] not in field_names:
                    if not first:
                        print('\n\nString entered is not a valid field name.')
                    print('Valid field names:\n{}\n'.format(field_names))
                    calib['fluxcal'][0] = str(raw_input('Please select a flux calibrator by name: '))
                    first = False
                change_made = True
        else:
            if not interactive:
                logger.critical('The number of flux calibrators does not match the number of spectral windows ({}).'.format(nspw))
                logger.info('Flux calibrators: {}'.format(calib['fluxcal']))
                sys.exit(-1)
            else:
                if len(calib['fluxcal']) != nspw:
                    logger.warning('Incorrect number of flux calibrators set. Requesting user input.')
                else:
                    logger.warning('At least one flux calibrator is incorrect. Please revise the list.')
                logger.info('Current calibrators list: {}'.format(calib['fluxcal']))
                if len(calib['fluxcal']) > nspw:
                    logger.warning('Too many flux calibrators set.')
                    logger.warning('The following will be truncated: {}'.format(calib['fluxcal'][nspw-1:]))
                    calib['fluxcal'] = calib['fluxcal'][:nspw]
                if len(calib['fluxcal']) < nspw:
                    logger.warning('Too few flux calibrators set.')
                    for i in range(len(calib['fluxcal']),nspw):
                        calib['fluxcal'].append('')
                i = 0
                first = True
                print('Valid field names:\n{}\n'.format(field_names))
                while i in range(len(calib['fluxcal'])):
                    if first:
                        print('SPW {0}: {1}'.format(spw_IDs[i],spw_names[i]))
                    calib['fluxcal'][i] = cf.uinput('Enter flux calibrator for SPW {}: '.format(spw_IDs[i], default=calib['fluxcal'][i]))
                    if calib['fluxcal'][i] not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        print('Valid field names:\n{}\n'.format(field_names))
                        first = False
                    else:
                        i += 1
                        first = True
                change_made = True
        logger.info('Flux calibrators set as: {}.'.format(calib['fluxcal']))
    else:
        logger.info('Flux calibrator already set as: {}.'.format(calib['fluxcal']))
        
    
    
    flux_mod_names_bad = False
    for i in range(len(calib['fluxmod'])):
        if calib['fluxmod'][i] not in std_flux_mods:
            flux_mod_names_bad = True
            if not interactive:
                logger.error('Non-standard name for flux model: {}'.format(calib['fluxmod'][i]))
    if flux_mod_names_bad or len(calib['fluxmod']) != len(calib['fluxcal']):
        logger.warning('Flux calibrator models do not match flux calibrators.')
    else:
        logger.info('Flux models already set as: {}.'.format(calib['fluxmod']))
            
    if len(calib['fluxmod']) == 0:
        if not interactive:
            logger.warning('There is no flux calibrator model listed in the parameters file.')
        flux_mod_names_bad = False
        for i in range(len(calib['fluxcal'])):
            if calib['fluxcal'][i] in std_flux_names.keys():
                calib['fluxmod'].append(std_flux_names[calib['fluxcal'][i]])
            else:
                flux_mod_names_bad = True
                if not interactive:
                    logger.critical('Some flux calibrator models cannot be automatcially assigned.')
                    sys.exit(-1)
        if not flux_mod_names_bad:
            logger.info('Flux models automatically set as: {}.'.format(calib['fluxmod']))
            change_made = True
                
    if flux_mod_names_bad or len(calib['fluxmod']) != len(calib['fluxcal']):
        if not interactive:
            if len(calib['fluxmod']) != len(calib['fluxcal']):
                logger.critical('The number of models does not match the number of flux calibrators.')
                logger.info('Flux calibrators: {}'.format(calib['fluxcal']))
                logger.info('Flux calibrator models: {}'.format(calib['fluxmod']))
                sys.exit(-1)
            elif calib['man_mod']:
                logger.warning('Proceeding with non-standard flux model assumed to be a manual flux scale.')
            else:
                logger.critical('Non-standard flux models in parameters and not indicated as manual flux scales.')
                logger.info('Flux calibrators: {}'.format(calib['fluxcal']))
                logger.info('Flux calibrator models: {}'.format(calib['fluxmod']))
                sys.exit(-1)
        else:
            if len(calib['fluxcal']) == 1:
                if len(calib['fluxmod']) == 0:
                    calib['fluxmod'].append('')
                logger.warning('No valid flux model set. Requesting user input.')
                while calib['fluxmod'][0] not in std_flux_mods:
                    print('Usual flux calibrator models will be 3C48_L.im, 3C138_L.im, 3C286_L.im, or 3C147_L.im.\n')
                    calib['fluxmod'][0] = str(raw_input('Please select a flux model name: '))
                    if calib['fluxmod'][0] not in std_flux_mods:
                        resp = str(raw_input('The model name provided is not one of the 3 expected options.\nDo you want to proceed with the model {} ?'.format(calib['fluxmod'][0])))
                        if resp.lower() in ['yes','ye','y']:
                            resp = ''
                            while resp.lower() not in ['yes','ye','y'] and resp.lower() not in ['no','n']:
                                resp = str(raw_input('Is this a manually defined flux model? '))
                                if resp.lower() in ['yes','ye','y']:
                                    calib['man_mod'] = True
                                else:
                                    calib['man_mod'] = False
                            break
                        else:
                            continue
            else:
                if len(calib['fluxmod']) != len(calib['fluxcal']):
                    logger.warning('Incorrect number of flux models set. Requesting user input.')
                else:
                    logger.warning('At least one flux model is incorrect. Please revise the list.')
                logger.info('Current models list: {}'.format(calib['fluxmod']))
                if len(calib['fluxmod']) > len(calib['fluxcal']):
                    logger.warning('Too many flux models set.')
                    logger.warning('The following will be truncated: {}'.format(calib['fluxmod'][len(calib['fluxcal'])-1:]))
                    calib['fluxmod'] = calib['fluxmod'][:len(calib['fluxcal'])]
                if len(calib['fluxmod']) < len(calib['fluxcal']):
                    logger.warning('Too few flux models set.')
                    for i in range(len(calib['fluxmod']),len(calib['fluxcal'])):
                        calib['fluxmod'].append('')
                i = 0
                while i in range(len(calib['fluxmod'])):
                    print('Usual flux calibrator models will be 3C48_L.im, 3C138_L.im, or 3C286_L.im.\n')
                    calib['fluxmod'][i] = cf.uinput('Enter flux model for calibrator {}: '.format(calib['fluxcal'][i], default=calib['fluxmod'][i]))
                    if calib['fluxmod'][i] not in std_flux_mods:
                        resp = str(raw_input('The model name provided is not one of the 3 expected options.\nDo you want to proceed with the model {} ?'.format(calib['fluxmod'][i])))
                        if resp.lower() in ['yes','ye','y']:
                            resp = ''
                            while resp.lower() not in ['yes','ye','y'] and resp.lower() not in ['no','n']:
                                resp = str(raw_input('Is this a manually defined flux model? '))
                                if resp.lower() in ['yes','ye','y']:
                                    calib['man_mod'] = True
                                else:
                                    calib['man_mod'] = False
                            i += 1
                    else:
                        i += 1
            change_made = True
        logger.info('Flux models set as: {}.'.format(calib['fluxmod']))
        
    
    band_cal_names_bad = False
    for i in range(len(calib['bandcal'])):
        if calib['bandcal'][i] not in field_names:
            band_cal_names_bad = True
            if not interactive:
                logger.critical('Illegal name for bandpass calibrator: {}'.format(calib['bandcal'][i]))
                sys.exit(-1)
    if band_cal_names_bad or len(calib['bandcal']) != nspw:
        if nspw == 1:
            if not interactive:
                logger.critical('No valid bandpass calibrator set.')
                sys.exit(-1)
            else:
                logger.warning('No valid bandpass calibrator set. Requesting user input.')
                if len(calib['bandcal']) == 0:
                    calib['bandcal'].append('')
                first = True
                while calib['bandcal'][0] not in field_names:
                    if not first:
                        print('\n\nString entered is not a valid field name.')
                    print('Valid field names:\n{}\n'.format(field_names))
                    calib['bandcal'][0] = str(raw_input('Please select a bandpass calibrator by name: '))
                    first = False
                change_made = True
        else:
            if not interactive:
                logger.critical('The number of bandpass calibrators does not match the number of spectral windows ({}).'.format(nspw))
                logger.info('Bandpass calibrators: {}'.format(calib['bandcal']))
                sys.exit(-1)
            else:
                if len(calib['bandcal']) != nspw:
                    logger.warning('Incorrect number of bandpass calibrators set. Requesting user input.')
                else:
                    logger.warning('At least one bandpass calibrator is incorrect. Please revise the list.')
                logger.info('Current calibrators list: {}'.format(calib['bandcal']))
                if len(calib['bandcal']) > nspw:
                    logger.warning('Too many bandpass calibrators set.')
                    logger.warning('The following will be truncated: {}'.format(calib['bandcal'][nspw-1:]))
                    calib['bandcal'] = calib['bandcal'][:nspw]
                if len(calib['bandcal']) < nspw:
                    logger.warning('Too few bandpass calibrators set.')
                    for i in range(len(calib['bandcal']),nspw):
                        calib['bandcal'].append('')
                i = 0
                first = True
                print('Valid field names:\n{}\n'.format(field_names))
                while i in range(len(calib['bandcal'])):
                    if first:
                        print('SPW {0}: {1}'.format(spw_IDs[i],spw_names[i]))
                    calib['bandcal'][i] = cf.uinput('Enter bandpass calibrator for SPW {}: '.format(spw_IDs[i], default=calib['bandcal'][i]))
                    if calib['bandcal'][i] not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        print('Valid field names:\n{}\n'.format(field_names))
                        first = False
                    else:
                        i += 1
                        first = True
                change_made = True
        logger.info('Bandpass calibrators set as: {}.'.format(calib['bandcal']))
    else:
        logger.info('Bandpass calibrator already set as: {}.'.format(calib['bandcal']))
        

    phase_cal_names_bad = False
    for i in range(len(calib['phasecal'])):
        if calib['phasecal'][i] not in field_names:
            phase_cal_names_bad = True
            if not interactive:
                logger.critical('Illegal name for phase calibrator: {}'.format(calib['phasecal'][i]))
                sys.exit(-1)
    if phase_cal_names_bad or len(calib['phasecal']) != len(calib['targets']):
        if len(calib['targets']) == 1:
            if not interactive:
                logger.critical('No valid phase calibrator set.')
                sys.exit(-1)
            else:
                logger.warning('No valid phase calibrator set. Requesting user input.')
                if len(calib['phasecal']) == 0:
                    calib['phasecal'].append('')
                first = True
                while calib['phasecal'][0] not in field_names:
                    if not first:
                        print('\n\nString entered is not a valid field name.')
                    print('Valid field names:\n{}\n'.format(field_names))
                    calib['phasecal'][0] = str(raw_input('Please select a phase calibrator by name: '))
                    first = False
                change_made = True
        else:
            if not interactive:
                logger.critical('The number of phase calibrators does not match the number of targets.')
                logger.info('Phase calibrators: {}'.format(calib['phasecal']))
                logger.info('Targets: {}'.format(calib['targets']))
                sys.exit(-1)
            else:
                if len(calib['phasecal']) != len(calib['targets']):
                    logger.warning('Incorrect number of phase calibrators set. Requesting user input.')
                else:
                    logger.warning('At least one phase calibrator is incorrect. Please revise the list.')
                logger.info('Current calibrators list: {}'.format(calib['phasecal']))
                if len(calib['phasecal']) > len(calib['targets']):
                    logger.warning('Too many phase calibrators set.')
                    logger.warning('The following will be truncated: {}'.format(calib['phasecal'][len(calib['targets'])-1:]))
                    calib['phasecal'] = calib['phasecal'][:len(calib['targets'])]
                if len(calib['phasecal']) < len(calib['targets']):
                    logger.warning('Too few phase calibrators set.')
                    for i in range(len(calib['phasecal']),len(calib['targets'])):
                        calib['phasecal'].append('')
                i = 0
                print('Valid field names:\n{}\n'.format(field_names))
                while i in range(len(calib['phasecal'])):
                    calib['phasecal'][i] = cf.uinput('Enter phase calibrator for {}: '.format(calib['targets'][i]), default=calib['phasecal'][i])
                    if calib['phasecal'][i] not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        print('Valid field names:\n{}\n'.format(field_names))
                    else:
                        i += 1
                change_made = True
        logger.info('Phase calibrators set as: {}.'.format(calib['phasecal']))
    else:
        logger.info('Phase calibrator already set as: {}.'.format(calib['phasecal']))
    if change_made:
        logger.info('Updating config file to set target and calibrator fields.')
        config_raw.set('calibration','fluxcal',calib['fluxcal'])
        config_raw.set('calibration','bandcal',calib['bandcal'])
        config_raw.set('calibration','phasecal',calib['phasecal'])
        config_raw.set('calibration','targets',calib['targets'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    else:
        logger.info('No changes made to preset target and calibrator fields.')
    logger.info('Completed setting field purposes.')

   
    
def calibration(msfile,config,logger):
    """
    Runs the basic calibration steps on each SPW based on the intents described in the configuration file.
    Applies the calibration to all science target fields.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting calibration.')
    plots_obs_dir = './plots/'
    cf.makedir(plots_obs_dir,logger)
    sum_dir = './summary/'
    cf.makedir(sum_dir,logger)
    cal_tabs = './cal_tabs/'
    cf.makedir(cal_tabs,logger)
    calib = config['calibration']
    std_flux_mods = ['3C48_L.im', '3C138_L.im', '3C286_L.im', '3C147_L.im']
    
    msmd.open(msfile)
    spw_IDs = []
    for target in calib['targets']:
        spw_IDs.extend(list(msmd.spwsforfield(target)))
    spw_IDs = list(set(list(spw_IDs)))
    spw_names = msmd.namesforspws(spw_IDs)
    nspw = len(spw_IDs)
    msmd.close()
    
    for i in range(nspw):
        msmd.open(msfile)
        spw_fields = msmd.fieldsforspw(spw_IDs[i], asnames=True)
        msmd.close()
        cals_in_spw = list(set(spw_fields).intersection(calib['phasecal']))
        targets_in_spw = list(set(spw_fields).intersection(calib['targets']))
        if len(cals_in_spw) == 0:
            logger.warning('No phase calibrator for SPW {}.'.format(spw_IDs[i]))
        if len(targets_in_spw) == 0:
            logger.warning('No targets in SPW {}.'.format(spw_IDs[i]))
    
    gctab = cal_tabs+'gaincurve.cal'
    logger.info('Calibrating gain vs elevation({}).'.format(gctab))
    command = "gencal(vis='{0}', caltable='{1}', caltype='gceff')".format(msfile,gctab)
    logger.info('Executing command: '+command)
    exec(command)
    
    prev_set = {}
    for i in range(len(calib['fluxcal'])):
        if calib['fluxcal'][i] not in prev_set.keys():
            prev_set[calib['fluxcal'][i]] = i
                
            logger.info('Load model for flux calibrator {0} ({1}).'.format(calib['fluxcal'][i],calib['fluxmod'][i]))
            if calib['fluxmod'][i] not in std_flux_mods and calib['man_mod']:
                #Add loop to go over every SPW the flux calibrator is used for.
                #This way a different flux can be specified in each if necessary.
                #In practice for the HI line this is unlikely to be an issue.
                command = "setjy(vis='{0}', field='{1}', scalebychan=True, fluxdensity=[{2},0,0,0], standard='manual')".format(msfile,calib['fluxcal'][i],calib['fluxmod'][i])
                logger.info('Executing command: '+command)
                exec(command)
            elif calib['fluxmod'][i] in std_flux_mods:
                command = "setjy(vis='{0}', field='{1}', scalebychan=True, model='{2}')".format(msfile,calib['fluxcal'][i],calib['fluxmod'][i])
                logger.info('Executing command: '+command)
                exec(command)
            else:
                logger.warning('The flux model cannot be recognised. The setjy task will not be run. Fluxes will be incorrect.')
        elif calib['fluxmod'][i] != calib['fluxmod'][prev_set[calib['fluxcal'][i]]]:
            logger.warning('The flux model for {0} has already been set as {1}, but it does not match the current model ({2}).'.format(calib['fluxcal'][i],calib['fluxmod'][prev_set[calib['fluxcal'][i]]],calib['fluxmod'][i]))
            logger.warning('The former will not be replaced. Check the flux model assignments in the parameters file.')
            
    plot_file = plots_obs_dir+'{0}_bpphaseint.png'.format(msfile)
    logger.info('Plotting bandpass phase vs. time for reference antenna to: {}'.format(plot_file))
    plotms(vis=msfile, plotfile=plot_file, xaxis='channel', yaxis='phase', field=calib['bandcal'][i], spw = ','.join(numpy.array(spw_IDs,dtype='str')),
           correlation='RR,LL', avgtime='1E10', antenna=calib['refant'], coloraxis='antenna2', expformat='png', 
           overwrite=True, showlegend=False, showgui=False, iteraxis='spw')
    
    dltab = cal_tabs+'delays.cal'
    logger.info('Calibrating delays for bandpass calibrators {0} ({1}).'.format(calib['bandcal'],dltab))
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', gaintype='K', gaintable=['{4}'], spw='{5}')".format(msfile,','.join(calib['bandcal']),dltab,calib['refant'],gctab,','.join(numpy.array(spw_IDs,dtype='str')))
    logger.info('Executing command: '+command)
    exec(command)
    
    bptab = cal_tabs+'bpphase.gcal'
    logger.info('Make bandpass calibrator phase solutions for {0} ({1}).'.format(calib['bandcal'],bptab))
    command = "gaincal(vis='{0}', field='{1}',  caltable='{2}', refant='{3}', calmode='p', solint='int', combine='', minsnr=2.0, gaintable=['{4}','{5}'], spw='{6}')".format(msfile,','.join(calib['bandcal']),bptab,calib['refant'],gctab,dltab,','.join(numpy.array(spw_IDs,dtype='str')))
    logger.info('Executing command: '+command)
    exec(command)
    
    plot_file = plots_obs_dir+'{0}_bpphasesol.png'.format(msfile)
    logger.info('Plotting bandpass phase solutions to: {}'.format(plot_file))
    plotms(vis=bptab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='phase',
           plotrange=[0,0,-180,180], expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna', coloraxis='spw', spw=','.join(numpy.array(spw_IDs,dtype='str')))
    
    bstab = cal_tabs+'bandpass.bcal'
    logger.info('Determining bandpass solution(s) ({}).'.format(bstab))
    command = "bandpass(vis='{0}', caltable='{1}', field='{2}', refant='{3}', solint='inf', solnorm=True, gaintable=['{4}', '{5}', '{6}'], spw='{7}')".format(msfile,bstab,','.join(calib['bandcal']),calib['refant'],gctab, dltab, bptab,','.join(numpy.array(spw_IDs,dtype='str')))
    logger.info('Executing command: '+command)
    exec(command)
    
    plot_file = plots_obs_dir+'{0}_bandpasssol_.png'.format(msfile)
    logger.info('Plotting bandpass amplitude solutions to: {}'.format(plot_file))
    plotms(vis=bstab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='chan', yaxis='amp',
           expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna', coloraxis='spw', spw=','.join(numpy.array(spw_IDs,dtype='str')))
    
    calfields = []
    calfields.extend(calib['fluxcal'])
    calfields.extend(calib['bandcal'])
    calfields.extend(calib['phasecal'])
    calfields = list(set(calfields))
    calfields = ','.join(calfields)
    
    iptab = cal_tabs+'intphase.gcal'
    logger.info('Determining integration phase solutions ({}).'.format(iptab))
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', calmode='p', solint='int', minsnr=2.0, gaintable=['{4}', '{5}', '{6}'],spw='{7}')".format(msfile,calfields,iptab,calib['refant'],gctab, dltab, bstab,','.join(numpy.array(spw_IDs,dtype='str')))
    logger.info('Executing command: '+command)
    exec(command)
    
    sptab = cal_tabs+'scanphase.gcal'
    logger.info('Determining scan phase solutions ({}).'.format(sptab))
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', calmode='p', solint='inf', minsnr=2.0, gaintable=['{4}', '{5}', '{6}'],spw='{7}')".format(msfile,calfields,sptab,calib['refant'],gctab, dltab, bstab,','.join(numpy.array(spw_IDs,dtype='str')))
    logger.info('Executing command: '+command)
    exec(command)
    
    amtab = cal_tabs+'amp.gcal'
    logger.info('Determining amplitude solutions ({}).'.format(amtab))
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', calmode='ap', solint='inf', minsnr=2.0, gaintable=['{4}', '{5}', '{6}', '{7}'],spw='{8}')".format(msfile,calfields,amtab,calib['refant'],gctab, dltab, bstab, iptab,','.join(numpy.array(spw_IDs,dtype='str')))
    logger.info('Executing command: '+command)
    exec(command)
    
    plot_file = plots_obs_dir+'phasesol.png'
    logger.info('Plotting phase solutions to: {}'.format(plot_file))
    plotms(vis=amtab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='phase',
           expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna', coloraxis='spw', plotrange=[-1,-1,-20,20], spw=','.join(numpy.array(spw_IDs,dtype='str')))

    plot_file = plots_obs_dir+'ampsol.png'
    logger.info('Plotting amplitude solutions to: {}'.format(plot_file))
    plotms(vis=amtab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='amp',
           expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna', coloraxis='spw', plotrange=[-1,-1,0,1], spw=','.join(numpy.array(spw_IDs,dtype='str')))
    
    if len(calfields.split(',')) > len(list(set(calib['fluxcal']))):
        fxtab = cal_tabs+'fluxsol.cal'
        logger.info('Applying flux scale to calibrators ({}).'.format(fxtab))
        command = "fluxscale(vis='{0}', caltable='{1}', fluxtable='{2}', reference='{3}', incremental=True)".format(msfile,amtab,fxtab,','.join(calib['fluxcal']))
        logger.info('Executing command: flux_info = '+command)
        exec('flux_info = '+command)

        out_filename = sum_dir+'{0}.flux.summary'.format(msfile)
        logger.info('Writing calibrator fluxes summary to: {}.'.format(out_filename))
        for i in range(nspw):
            out_file = open(out_filename, 'a+')
            out_file.write('Spectral window: {}\n'.format(spw_IDs[i]))
            for k in range(len(flux_info.keys())):
                if 'spw' in flux_info.keys()[k] or 'freq' in flux_info.keys()[k]:
                    continue
                else:
                    fieldID = flux_info.keys()[k]
                    out_file.write('Flux density for {0}: {1} +/- {2} Jy\n'.format(flux_info[fieldID]['fieldName'], flux_info[fieldID][str(spw_IDs[i])]['fluxd'][0], flux_info[fieldID][str(spw_IDs[i])]['fluxdErr'][0]))
                    out_file.write('\n')
            out_file.close()
    
    logger.info('Apply all calibrations to bandpass and flux calibrators.')
    for i in range(len(calib['bandcal'])):
        logger.info('Applying clibration to: {}'.format(calib['bandcal'][i]))
        if calib['bandcal'][i] == calib['fluxcal'][i]:
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}'], gainfield=['', '{1}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['bandcal'][i],gctab, dltab, bstab, iptab, amtab)
            logger.info('Executing command: '+command)
            exec(command)
        else:
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{1}', '{1}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['bandcal'][i],gctab, dltab, bstab, iptab, amtab, fxtab)
            logger.info('Executing command: '+command)
            exec(command)
            
            logger.info('Applying clibration to: {}'.format(calib['fluxcal'][i]))
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['fluxcal'][i],gctab, dltab, bstab, iptab, amtab, fxtab, calib['bandcal'][i])
            logger.info('Executing command: '+command)
            exec(command)
            
    plot_file = plots_obs_dir+'corr_phase.png'
    logger.info('Plotting corrected phases for {0} to: {1}'.format(calib['bandcal'],plot_file))
    plotms(vis=msfile, plotfile=plot_file, field=','.join(calib['bandcal']), xaxis='channel', yaxis='phase', ydatacolumn='corrected', correlation='RR,LL', 
           avgtime='1E10', antenna=calib['refant'], spw=','.join(numpy.array(spw_IDs,dtype='str')), coloraxis='antenna2', iteraxis='spw', expformat='png', 
           overwrite=True, showlegend=False, showgui=False)

    plot_file = plots_obs_dir+'corr_amp.png'
    logger.info('Plotting corrected amplitudes for {0} to: {1}'.format(calib['bandcal'],plot_file))
    plotms(vis=msfile, plotfile=plot_file, field=','.join(calib['bandcal']), xaxis='channel', yaxis='amp', ydatacolumn='corrected', correlation='RR,LL', 
           avgtime='1E10', antenna=calib['refant'], spw=','.join(numpy.array(spw_IDs,dtype='str')), coloraxis='antenna2', iteraxis='spw', expformat='png', 
           overwrite=True, showlegend=False, showgui=False)
    
    logger.info('Apply all calibrations to phase calibrators and targets.')
    for i in range(len(calib['targets'])):
        if not calib['phasecal'][i] in calib['fluxcal']:
            logger.info('Applying clibration to: {}'.format(calib['phasecal'][i]))
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['phasecal'][i],gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'][i])
            logger.info('Executing command: '+command)
            exec(command)
            
            logger.info('Applying clibration to: {}'.format(calib['targets'][i]))
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{9}', '{9}', '{9}'], calwt=False)".format(msfile,calib['targets'][i],gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'][i],calib['phasecal'][i])
            logger.info('Executing command: '+command)
            exec(command)
        else:
            logger.info('Applying clibration to: {}'.format(calib['targets'][i]))
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}'], gainfield=['', '{7}', '{7}', '{8}', '{8}'], calwt=False)".format(msfile,calib['targets'][i],gctab, dltab, bstab, iptab, amtab,calib['bandcal'][i],calib['phasecal'][i])
            logger.info('Executing command: '+command)
            exec(command)
    
    logger.info('Completed calibration.')



def split_fields(msfile,config,logger):
    """
    Splits the MS into separate MS for each science target.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting split fields.')
    calib = config['calibration']
    src_dir = config['global']['src_dir']+'/'
    sum_dir = './summary/'
    cf.makedir(sum_dir,logger)
    cf.makedir('./'+src_dir,logger)
    for i in range(len(calib['targets'])):
        field = calib['targets'][i]
        target_name = calib['target_names'][i]
        msmd.open(msfile)
        spws = msmd.spwsforfield(field)
        if len(spws) > 1:
            logger.info('{0} was observed in multiple SPWs. These will now be combined (if possible) and the field split into a separate MS.'.format(field))
            spws_nchan = numpy.array(numpy.zeros(len(spws)),dtype='int')
            for j in range(len(spws)):
                spws_nchan[j] = msmd.nchan(spws[j])
            if len(set(spws_nchan)) == 1:
                command = "mstransform(vis='{0}', outputvis='{2}{1}.split', field='{3}', spw='{4}', combinespws=True)".format(msfile,target_name,src_dir,field,','.join(numpy.array(spws,dtype='str')))
                logger.info('Executing command: '+command)
                exec(command)
            else:
                logger.info('SPWs {} cannot be combined and will be split into separate MSs.'.format(spws))
                for spw in spws:
                    command = "split(vis='{0}', outputvis='{1}{2}'+'.spw{3}.split', field='{4}', spw='{3}')".format(msfile,src_dir,target_name,spw,field)
                    logger.info('Executing command: '+command)
                    exec(command)
        else:
            logger.info('Splitting {0} into separate file: {1}.'.format(field, target_name+'.split'))
            command = "split(vis='{0}', outputvis='{1}{2}'+'.split', field='{3}')".format(msfile,src_dir,target_name,field)
            logger.info('Executing command: '+command)
            exec(command)
        msmd.close()
        listobs_file = sum_dir+target_name+'.listobs.summary'
        cf.rmfile(listobs_file,logger)
        logger.info('Writing listobs summary for split data set to: {}'.format(listobs_file))
        listobs(vis=src_dir+target_name+'.split', listfile=listobs_file)
    logger.info('Completed split fields.')


# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(config['global']['project_name']),
                       LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])

#Flag, set intents, calibrate, flag more, calibrate again, then split fields
restore_flags(msfile,'Original',logger)
manual_flags(logger)
base_flags(msfile,config,logger)
tfcrop(msfile,config,logger)
flag_version = 'initial'
rm_flags(msfile,flag_version,logger)
save_flags(msfile,flag_version,logger)
flag_sum(msfile,flag_version,logger)
select_refant(msfile,config,config_raw,config_file,logger)
set_fields(msfile,config,config_raw,config_file,logger)
plot_flags(msfile,flag_version,logger)
calibration(msfile,config,logger)
rflag(msfile,config,logger)
flag_version = 'rflag'
rm_flags(msfile,flag_version,logger)
save_flags(msfile,flag_version,logger)
flag_sum(msfile,flag_version,logger)
extend_flags(msfile,logger)
flag_version = 'extended'
rm_flags(msfile,flag_version,logger)
save_flags(msfile,flag_version,logger)
flag_sum(msfile,flag_version,logger)
calibration(msfile,config,logger)
flag_version = 'final'
rm_flags(msfile,flag_version,logger)
save_flags(msfile,flag_version,logger)
flag_sum(msfile,flag_version,logger)
plot_flags(msfile,flag_version,logger)
cf.rmdir(config['global']['src_dir'],logger)
split_fields(msfile,config,logger)

#Review and backup parameters file
cf.diff_pipeline_params(config_file,logger)
cf.backup_pipeline_params(config_file,logger)
import pysubs2
import yaml
import re
import logging

logger = logging.getLogger(__name__)

def ass(config,ass_path):
    sub = pysubs2.load(ass_path)

    # Update Info:
    logger.debug("Setting ass information")
    sub.info.setdefault("PlayResX",'1920')
    sub.info.setdefault("PlayResY",'1080')
    sub.info.update(config['info'])

    # Process general settings
    if config['general']['remove_miscellaneous_events']:
        logger.debug("Removing miscellaneous_events")
        sub.remove_miscellaneous_events()

    for i, line in reversed(list(enumerate(sub.events))):

        if config['general']['remove_comments'] and line.is_comment:
            logger.debug(f"Removing comment line:{i}")
            sub.events.pop(i)
        
        if config['general']['remove_drawings'] and line.is_drawing:
            logger.debug(f"Removing drawing line:{i}")
            sub.events.pop(i)
        
        for r in config["replace"]:
            old = line.text
            line.text = re.sub(r["regex"],r["replacement"],line.text)

            if old != line.text:
                logger.debug(f"Performing regex ({r['regex']}) replacement for line:{i}")

    # Process styles:
    for key in sub.styles.keys():

        for cfg in config['styles']:
            style_settings = cfg.copy()
            
            match_regex = style_settings.pop("regex")
            mode = style_settings.pop("mode")

            if "fontsize" in style_settings:
                style_settings["fontsize"] = style_settings["fontsize"] / 1080 * float(sub.info["PlayResY"])
            
            if "marginv" in style_settings:
                style_settings["marginv"] = style_settings["marginv"] / 1080 * float(sub.info["PlayResY"])

            if "marginl" in style_settings:
                style_settings["marginl"] = style_settings["marginl"] / 1920 * float(sub.info["PlayResX"])
                
            if "marginr" in style_settings: 
                style_settings["marginr"] = style_settings["marginr"] / 1920 * float(sub.info["PlayResX"])

            if re.fullmatch(match_regex,str(key)) != None:

                if mode == 'replace':
                    logger.debug(f"Replacing style: {key}")
                    sub.styles[key] = pysubs2.SSAStyle(**style_settings)
                
                elif mode == 'update':
                    logger.debug(f"Updating style: {key}")
                    sub.styles[key].__dict__.update(style_settings)
                else:
                    logger.critical(f"'{mode}' mode is not Supported")

    sub.save(ass_path)


def srt(config,srt_path):
    sub = pysubs2.load(srt_path)
    
    if config['general']['remove_miscellaneous_events'] == 'yes':
        sub.remove_miscellaneous_events()

    for i, line in reversed(list(enumerate(sub.events))):

        if config['general']['remove_comments'] and line.is_comment:
            logger.debug(f"Removing comment line:{i}")
            sub.events.pop(i)
        
        if config['general']['remove_drawings'] and line.is_drawing:
            logger.debug(f"Removing drawing line:{i}")
            sub.events.pop(i)
        
        for r in config["replace"]:
            old = line.text
            line.text = re.sub(r["regex"],r["replacement"],line.text)

            if old != line.text:
                logger.debug(f"Performing regex ({r['regex']}) replacement for line:{i}")
    
    sub.save(srt_path,**config['save'])

def standardize(config_path,files):

    with open(config_path) as cfg_file:
        config = yaml.full_load(cfg_file.read())

    for path in files:
        
        if str(path).endswith(".ass"):
            logger.info(f"[PostProcessing] Formatting ass subtitle: {path}")
            ass(config['ass'],path)
        
        elif str(path).endswith(".srt") or  str(path).endswith(".vtt"):
            logger.info(f"[PostProcessing] Formatting srt/vtt subtitle: {path}")
            srt(config['srt'],path)
        
        else:
            logger.warning("Unsupported format")

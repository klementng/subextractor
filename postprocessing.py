import pysubs2
import yaml
import re


def ass(config,ass_path):
    sub = pysubs2.load(ass_path)

    # Update Info:
    sub.info.setdefault("PlayResX",'1920')
    sub.info.setdefault("PlayResY",'1080')
    sub.info.update(config['info'])

    # Process general settings
    if config['general']['remove_miscellaneous_events']:
        sub.remove_miscellaneous_events()

    for i, line in reversed(list(enumerate(sub.events))):

        if config['general']['remove_comments'] and line.is_comment:
            sub.events.pop(i)
        
        if config['general']['remove_drawings'] and line.is_drawing:
            sub.events.pop(i)
        
                    
        for r in config["replace"]:
            line.text = re.sub(r["regex"],r["replacement"],line.text)

    # Process styles:
    for key in sub.styles.keys():

        for cfg in config['styles']:
            style_settings = cfg.copy()
            
            match_regex = style_settings.pop("regex")
            mode = style_settings.pop("mode")

            if "fontsize" in style_settings:
                style_settings["fontsize"] = style_settings["fontsize"] / 1080 * float(sub.info["PlayResY"])
            
            if "marginv" in style_settings:
                style_settings["marginv"] = style_settings["fontsize"] / 1080 * float(sub.info["PlayResY"])

            if "marginl" in style_settings:
                style_settings["marginl"] = style_settings["marginl"] / 1920 * float(sub.info["PlayResX"])
                
            if "marginr" in style_settings: 
                style_settings["marginr"] = style_settings["fontsize"] / 1920 * float(sub.info["PlayResX"])

            if re.fullmatch(match_regex,str(key)) != None:

                if mode == 'replace':
                    sub.styles[key] = pysubs2.SSAStyle(**style_settings)
                
                elif mode == 'update':
                    sub.styles[key].__dict__.update(style_settings)

                else:
                    raise RuntimeError(f"{mode} is not supported")
                
    sub.save(ass_path)


def srt(config,srt_path):
    sub = pysubs2.load(srt_path)
    
    if config['general']['remove_miscellaneous_events'] == 'yes':
        sub.remove_miscellaneous_events()

    for i, line in reversed(list(enumerate(sub.events))):

        if config['general']['remove_comments'] and line.is_comment:
            sub.events.pop(i)
        
        if config['general']['remove_drawings'] and line.is_drawing:
            sub.events.pop(i)
        
        for r in config["replace"]:
            sub.events[i].text = re.sub(r["regex"],r["replacement"],line.text)
    
    sub.save(srt_path,**config['save'])

def standardize(config_path,files):

    with open(config_path) as cfg_file:
        config = yaml.full_load(cfg_file.read())

    for path in files:
        
        if str(path).endswith(".ass"):
            ass(config['ass'],path)
        
        elif str(path).endswith(".srt"):
            srt(config['srt'],path)

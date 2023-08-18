import pysubs2
import yaml
import re
import logging
import copy

logger = logging.getLogger(__name__)


class BaseFormatter:

    def __init__(self,config: dict) -> None:

        self.config = config
        self.general = config.get('general',{})
        self.regex_replace = config.get("replace",[])
        
        self.save_kwargs = config.get('save',{})
        
    def format_general(self, ssafile:pysubs2.SSAFile):

        ssafile = copy.deepcopy(ssafile)
        
        if self.general.get('remove_miscellaneous_events',False):
            ssafile.remove_miscellaneous_events()

        rm_drawing = self.general.get('remove_drawings',False)
        rm_dup = self.general.get("remove_duplicate_lines",False)
        rm_comments = self.general.get('remove_comments',False)

        prev_event = pysubs2.SSAEvent()

        for i, event in reversed(list(enumerate(ssafile.events))):

            if rm_comments and event.is_comment:
                logger.debug(f"Removing comment line:{i}")
                ssafile.events.pop(i)
            
            if rm_drawing and event.is_drawing:
                logger.debug(f"Removing drawing line:{i}")
                ssafile.events.pop(i)

            if rm_dup:    
                if event.start == prev_event.start and event.end == prev_event.end and event.plaintext == prev_event.plaintext:
                    logger.debug(f"Removing duplicate line:{i}")
                    ssafile.events.pop(i)
            
            for r in self.regex_replace:
                old = event.text
                event.text = re.sub(r["regex"],r["replacement"],event.text)

                if old != event.text:
                    logger.debug(f"Performing regex ({r['regex']}) replacement for line:{i}")

            prev_event = event
        
        return ssafile

    def format(self,path, save = False):
        ssafile = pysubs2.load(path)
        
        ssafile = self.format_general(ssafile)

        if save == True:
            ssafile.save(path,**self.save_kwargs)
        
        return ssafile


class SSAFormatter(BaseFormatter):
    
    def __init__(self, config: dict) -> None:
        super().__init__(config)

        self.info = config.get("info",{})
        self.styles = config.get("styles",[])
    
    def update_info(self,ssafile:pysubs2.SSAFile):

        ssafile = copy.deepcopy(ssafile)

        remove = self.info.get("remove",[])
        update = self.info.get("update",{})

        for key in remove:
            ssafile.info.pop(key,None)
        
        ssafile.info.update(update)

        return ssafile
    
    def format_ssa_styles(self,ssafile):
        
        ssafile = copy.deepcopy(ssafile)

        ssafile.info.setdefault("PlayResX",'1920')
        ssafile.info.setdefault("PlayResY",'1080')

        for key in ssafile.styles.keys():

            for sty in self.styles:
                sty_copy = sty.copy()
                
                match_regex = sty_copy.pop("regex")
                mode = sty_copy.pop("mode")

                if "fontsize" in sty_copy:
                    sty_copy["fontsize"] = round(sty_copy["fontsize"] / 1080 * float(ssafile.info["PlayResY"]), 1)
                
                if "marginv" in sty_copy:
                    sty_copy["marginv"] = int(round(sty_copy["marginv"] / 1080 * float(ssafile.info["PlayResY"])))

                if "marginl" in sty_copy:
                    sty_copy["marginl"] = int(round(sty_copy["marginl"] / 1920 * float(ssafile.info["PlayResX"])))
                    
                if "marginr" in sty_copy: 
                    sty_copy["marginr"] = int(round(sty_copy["marginr"] / 1920 * float(ssafile.info["PlayResX"])))

                if re.fullmatch(match_regex,str(key)) != None:

                    if mode == 'replace':
                        logger.debug(f"Replacing style: {key}")
                        ssafile.styles[key] = pysubs2.SSAStyle(**sty_copy)
                    
                    elif mode == 'update':
                        logger.debug(f"Updating style: {key}")
                        ssafile.styles[key].__dict__.update(sty_copy)
                    else:
                        logger.critical(f"'{mode}' mode is not Supported")
        
        return ssafile

    def format(self, path, save=False):
        ssafile = pysubs2.load(path)

        ssafile = self.update_info(ssafile)
        ssafile = self.format_general(ssafile)
        ssafile = self.format_ssa_styles(ssafile)

        if save == True:
            ssafile.save(path,**self.save_kwargs)

        return ssafile

class SRTFormatter(BaseFormatter):
        
    def __init__(self, config: dict) -> None:
        super().__init__(config)


def standardize(config_path,files):
    with open(config_path) as cfg_file:
        config = yaml.full_load(cfg_file.read())

    for path in files:
        
        if str(path).endswith(".ass"):
            logger.info(f"[PostProcessing] Formatting ass subtitle: {path}")
            formatter = SSAFormatter(config['ass'])
            formatter.format(path,save=True)
        
        elif str(path).endswith(".srt") or str(path).endswith(".vtt"):
            formatter = SRTFormatter(config['srt'])
            formatter.format(path,save=True)
        
        else:
            logger.warning("Unsupported format")

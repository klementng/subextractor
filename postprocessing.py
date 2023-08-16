import pysubs2
import yaml

def standardize(config_path,files):

    with open(config_path) as cfg_file:
        config = yaml.full_load(cfg_file.read())

    for path in files:
        sub = pysubs2.SSAFile.load(path)

        sub.info.pop("PlayResX",None)
        sub.info.pop("PlayResY",None)

        for key in sub.styles.keys():
            sub.styles[key] = pysubs2.SSAStyle(**config["SSAstyle"])

        sub.save(path, **config["save"])

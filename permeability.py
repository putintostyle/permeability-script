import argparse
from ImageAnalyCmd import *
from ImageAnalyzer import *

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-wd', '--working_dir', help='where images are store')
    args = parser.parse_args()
    return args

def main():
    parse = parse_args()

    shell = ImageAnalyzerShell(parse.working_dir)
    shell.cmdloop()

main()
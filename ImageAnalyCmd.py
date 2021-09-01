import cmd
from ImageAnalyzer import *
import shutil
import pandas as pd
import random
import logging
try:
    from tqdm import tqdm
except:
    subprocess.run(['pip', 'install',  'tdqm'])
    from tqdm import tqdm
import time
''' 
workflow:
if rename:
    rename
select LF
select ref
regions = []
select show
imagecal from ref
image analysis
result show
'''

class ImageAnalyzerShellBase(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "usage > "
        self.intro  = "Type: rename to initial the program \n  If you have references to ROI please make sure the file is .csv file \n please type man for more information "  ## defaults to None

    ## Command definitions ##
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print(self._hist)

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print("Exiting...")

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception as e:
            print(e.__class__, ":", e)

    # shortcuts
    do_quit = do_exit
    do_q = do_quit
    do_history = do_hist

class ImageAnalyzerShell(ImageAnalyzerShellBase):
    def __init__(self, workDir):
        ImageAnalyzerShellBase.__init__(self)
        self.workDir = workDir
        self.preprocessor = ImagePreprocessor(workDir)
        self.fatCut = []
        self.analyzer = ImageAnalyzer(workDir, self.preprocessor, self.fatCut)
        self.region = {}
        self.result = {}
        self.pid = None
    def do_man(self, args):
        print('Please do rename first, this function will generate a new folder which contains all the copies of renamed file\n')
        print('fat : this function is to indicate the references of fats to calibrate image, please type fat 70 80 90')
        print('this means we take three cuts in a image for calibration. It is recommened that three set of cuts for calibration, that is, use fat function three times')
        print('inputfile : If you have other files to indicate ROI please type inputfile filename')
        print('select : select region interactively. usage:select')
    def do_pid(self, args):
        cmds = args.split()
        self.pid = cmds
    def do_rename(self, args):
        # usage rename [folder]
        # TODO: rename rules
        cmds = args.split()
        dataFolder = '__data__'
        if not os.path.isdir(os.path.join(self.workDir, dataFolder)):
            os.mkdir(os.path.join(self.workDir, dataFolder))
        
        for dirPath, dirNames, fileNames in os.walk(os.path.join(self.workDir)):
#     print dirPath
            for f in fileNames:
                if f == 'I11':
                    continue
                old_file = os.path.join(dirPath, f)
                dst = os.path.join(self.workDir, dataFolder)
                new_file = os.path.join(dst, str(f)[1:-1])
                if f[0] == 'I':
                    shutil.copyfile(old_file, new_file)
        self.preprocessor.path = os.path.join(self.workDir, dataFolder)
        self.analyzer.path = os.path.join(self.workDir, dataFolder)
    def do_fat(self, args):
        cmds = args.split()
        if len(cmds) != 3:
            print('please specify three cuts, for example , fat 70 80 90')
        else:
            self.fatCut.append([int(i) for i in cmds])
    def do_print(self, args):
        cmds = args.split()
        if 'fat' in cmds:
            print(self.fatCut)
        if 'region' in cmds:
            print(self.region)
        if 'result' in cmds:
            try:
                print(self.analyzer.result_mean)
            except:
                print('please fo computation first')
    def do_clean(self, args):
        cmds = args.split()
        if '-f' in cmds:
            self.fatCut = []
        if '-reg' in cmds:
            if cmds[cmds.index('-reg')+1] == 'all':
                self.region = {}
            else:
                self.region.pop(cmds[cmds.index('-reg')+1])
        if '-result' in cmds:
            self.result = {}
    def do_inputfile(self, args):
        cmds = args.split()

        file = np.array(pd.read_csv(cmds[0]).values)
        
        for data in file:
            if data[1] != 'VIF':
                tmp_dict = {'slice name' : data[0], 'regions':[[data[2], data[3], 5]]}

                self.region[data[1]] = tmp_dict
        self.region['VIF'] = {'regions':[]}
        for data in file[file[:,1] == 'VIF']:
            self.region['VIF']['slice name'] = data[0]
            self.region['VIF']['regions'].append([data[2], data[3], 3])


    def do_select(self, args):
        # usage select 70 LF [--manual-radius] [--manual-input](center.x, center.y, radius)
        # dict = {'LF':{'slice_name': 'I70', 'region':[center, radius]}, 'CH':{'slice_name': 'I70', 'region':[center, radius]}}
        self.do_rename(args)
        cmds = args.split()
        if '-help' in cmds:
            print('usage: select slice_num label [--manual-radius](default 5) [--manual-input](center.x, center.y, radius)\n')
            print('for example: select 70 RF --manual-radius\n')
            print('or: select 70 RF --manual-input 50 60 7')
        else:
            
            if len(cmds) <= 2:
                print('too less argument, for more information, please type <select -help>')
                
            else:
                slice = cmds[0]
                label = cmds[1]
                
                if '--manual-input' in cmds:
                    input_idx = cmds.index('--manual-input')+1
                    tmp_dict = {'slice name' : slice, 'regions':[[cmds[input_idx], cmds[input_idx+1], cmds[input_idx+2]]]} # center
                elif '--manual-radius' in cmds:
                    tmp_dict = {'slice name' : slice, 'regions':self.preprocessor.select_region(slice,  manRadius=True)}
                else:
                    tmp_dict = {'slice name' : slice, 'regions':self.preprocessor.select_region(slice)}
                self.region[label] = tmp_dict
         # 新增region上去
    def do_regionshow(self, args): 
        
        pass
    def do_computation(self, args):
        # usage concerntration -all 64 -LR 64
        cmds = args.split()

        if '-all' in cmds:
            series = cmds[cmds.index('-all')+1]
        else:
            print('need parameters, for example, -all 64')
        # ToDo : Specify region
        
        self.analyzer.dict = self.region
        if self.fatCut == []:
            self.fatCut = [[70,85,90],
                            [75,80,90],
                            [74,87,95],
                            ]
        
        for label in self.analyzer.dict:
            
            
            if label != 'VIF':
                self.removeNoise = []
                self.positive = []
                self.negative = []
                for fat_arr in  self.fatCut:
                    self.analyzer.label = label
                    ### store initial slice
                    start_ROI = self.region[label]['slice name']
                    start_VIF = self.region['VIF']['slice name']
                    ### store initial data
                    # print(label, start_ROI, (fat_arr))
                    self.initROI = self.analyzer.storeRegion(label, start_ROI, fat_arr)
                    self.initVIF = self.analyzer.storeRegion('VIF',start_VIF, fat_arr)
                    
                    self.c_p = self.analyzer.computeConcerntration(label,
                                                                    self.initVIF,
                                                                    start_VIF,
                                                                    int(start_VIF)+int(series),
                                                                    fat_arr,
                                                                    VIF = True,
                                                                    ROI_size = len(self.initROI),
                                                                    )
                    purturbList = [[random.randint(-1, 1), random.randint(-1, 1)] for i in range(3)]
                    
                    for purturb in purturbList:
                        self.c_t = self.analyzer.computeConcerntration(label,
                                                                    self.initROI, 
                                                                    start_ROI,
                                                                    int(start_ROI)+int(series),
                                                                    fat_arr, 
                                                                    purturb = purturb)

                        
                        self.y = (self.c_t+1e-10)/(self.c_p+1e-10)

                        Ki = self.analyzer.computeKi(len(self.initROI),
                                                        self.c_p,
                                                        self.y)
                
                        removeNoise, bins, positive, negative = self.analyzer.noiseElimation(np.array(Ki))
                        self.bins = bins
                        self.removeNoise.append(removeNoise)
                        self.positive.append(positive)
                        self.negative.append(negative)
                        
                tmp_dict = {'remove': np.mean(self.removeNoise, axis = 0), 'bins': self.bins, 'positive' :np.mean(self.positive, axis = 0), 'negative':np.mean(self.negative, axis = 0)}
                self.result[label] = tmp_dict
        print('done, to read computational result please type:stat -all')
        # pd.DataFrame.from_dict(data=self.result, orient='index').to_csv('result_file.csv', header=True)
    def do_stat(self, args):
        # usage stat -all [-original] [-removenoise]
        cmds = args.split()
        if self.pid != None:
            
            if '-all' in cmds:
                if '-removenoise' in cmds:
                    for label in self.analyzer.dict:
                        if label != 'VIF':
                            self.analyzer.plotStat(self.result, label, target='eliminate')
                else:
                    for label in self.analyzer.dict:
                        if label != 'VIF':
                            self.analyzer.plotStat(self.result, label, target='original')
                
                pd.DataFrame.from_dict(data=self.analyzer.result_mean, orient='index').to_csv(str(self.pid)+'_result_file.csv', header=True)
            else:
                print('not yet finished')
        else:
            print('please enter the pid with using pid [pid]')
        
        


from random import random
from ImagePreprocessor import *
from sklearn import linear_model

class ImageAnalyzer:
    def __init__(self, workDir, preprocessor, fatCut):
        self.fileName = None
        self.init_ROI = None
        self.dict = None
        self.path = workDir
        self.img = None
        self.label = None
        
        self.preprocessor = preprocessor
        print(self.preprocessor.path)
        self.result_mean = {}

    def imageCal(self, slice, fat_arr):
        self.img = self.preprocessor.image_calibration(slice, fat_arr)

    def storeRegion(self, label, slice , fat_arr, purturb=None):
        if label == 'VIF':
            self.imageCal(str(slice), fat_arr) # cal image
        else:
            self.imageCal(str(slice), fat_arr)
        ROI = []
        
        for selectROI in self.dict[label]['regions']:
            for i in range(0,144):
                for j in range(0,144):
                    if (purturb == None):
                        with_purt  = ((i-(selectROI[0]))**2+(j-(selectROI[1]))**2<=selectROI[2]**2)
                        without_purt = False
                    else:
                        with_purt = False
                        without_purt = (purturb != None)&((i-(selectROI[0]+purturb[0]))**2+(j-(selectROI[1]+purturb[1]))**2<=selectROI[2]**2)
                    if (with_purt|without_purt):
                        if self.img[i][j] == 0:
                            tmp = self.img[i-3:i+2,j-3:j+2]
                            ROI.append(np.mean(tmp)+1e-10)
                        else:
                            ROI.append(self.img[i][j])              
        return np.array(ROI)

    def initialRegion(self, label):
        if self.fileName == None:
            print('add a file name')
        else:
            return self.storeRegion(label, self.dict[label]['slice name']) # here to provide label and slice

    def computeConcerntration(self, label, initial, start_slice, end_slice, fat_arr, VIF = False, ROI_size = None, purturb = None):
        c = []
        
        
        for sliceNum in range(start_slice, end_slice):
            
            
            ROI_t = self.storeRegion(label, sliceNum, fat_arr, purturb)
            c_t = np.zeros(len(ROI_t))
            
            for i in range(len(c_t)):
                if (ROI_t[i] == 0) & (initial[i] == 0):
                    c_t[i] = 0
                else:
                    c_t[i] = -np.log(ROI_t[i]/initial[i])
            if VIF:
                
                c.append([np.mean(c_t) for i in range(ROI_size)])
            else:
                c.append(c_t)

        return np.array(c)
    
    def computeKi(self, shape_ROI, c_p, y, drop_list = []):
        Ki = []
        for i in range(shape_ROI):
            c_p_tmp = c_p[:,i]+1e-10
            per_time = 0
            y_t = []
            x_t = []
            for time in range(len(c_p_tmp)):
                if time not in drop_list: 
                    if time <= 16: 
                        per_time += c_p_tmp[time]*(4/60)
                        y_t.append(y[:,i][time])
                        x_t.append(per_time/(c_p_tmp[time]))
                    elif (time>16)&(time<=35):
                        per_time += c_p_tmp[time]*(6/60)
                        y_t.append(y[:,i][time])
                        x_t.append(per_time/(c_p_tmp[time]))
                    elif (time>35)&(time<=41):
                        per_time += c_p_tmp[time]*(8/60)
                        y_t.append(y[:,i][time])
                        x_t.append(per_time/(c_p_tmp[time]))
                    elif (time>41):
                        per_time += c_p_tmp[time]
                        y_t.append(y[:,i][time])
                        x_t.append(per_time/(c_p_tmp[time]))
            x_t = np.array(x_t)
            y_t = np.array(y_t)

            y_t_mean = np.mean(y_t)
            y_t_std = np.std(y_t)

            drop_index = []
            for index in range(len(y_t)):
                if abs(y_t[index]-y_t_mean)>y_t_std:
                    drop_index.append(index)

            y_t = np.delete(y_t, drop_index)
            x_t = np.delete(x_t, drop_index)
    
            regr = linear_model.LinearRegression()
    
            regr.fit(x_t.reshape(-1,1), y_t)
            Ki.append(round(regr.coef_[0],5))
        return np.array(Ki)
    
    def noiseElimation(self, Ki, bin_num = 200):
        
        plot1 = np.histogram(Ki[Ki>=0], bins=bin_num , range = (0, np.max(np.abs(Ki))))
        plot2 = np.histogram(-1*Ki[Ki<0], bins = plot1[1])
        
        self.bins = plot1[1]
        
        bar1 = plot1[0]
        bar2 = plot2[0]
        
        substr_bar = np.zeros(len(bar1))
        for i in range(len(bar1)):
            if (bar1[i]-bar2[i]) < 0:
                substr_bar[i] = 0
            else:
                substr_bar[i] = bar1[i]-bar2[i]
        
        return substr_bar/len(Ki), plot1[1][0:-1], bar1/len(Ki), bar2/len(Ki)
        
    def plotStat(self, result, label, target = 'eliminate', save = False, PATH = None) :
        ''' TO DO: path writable '''
        if (target == 'eliminate') | (target == 'all'):
            plt.clf()
            plt.bar(result[label]['bins'],result[label]['remove'],width = 0.002,color = 'grey')
            plt.xlim(-max(result[label]['bins']), max(result[label]['bins']))
            plt.ylim(0, 0.08)
            plt.suptitle('Total amount of '+label+' = '+str(np.sum(result[label]['bins']*result[label]['remove'])))
            plt.xlabel('Ki (1/min)')
            plt.ylabel('fraction of voxels')
            if save:
                plt.savefig(PATH+'AIF_full_seq\\' +label+' after subtraction.png')
            plt.show()
        elif (target == 'original')|(target == 'all'):
            plt.clf()
            plt.bar(-1*result[label]['bins'],result[label]['negative'],width = 0.002,color = 'r')
            plt.bar(result[label]['bins'], result[label]['positive'],width = 0.002,color = 'b')
            plt.xlim(-max(result[label]['bins']), max(result[label]['bins']))
            plt.ylim(0, 0.08)
            plt.suptitle('Total amount of '+label+' = '+str(np.sum(result[label]['bins']*result[label]['remove'], )))
            plt.xlabel('Ki (1/min)')
            plt.ylabel('fraction of voxels')
            if save:
                plt.savefig(PATH+'AIF_full_seq\\' +label+' before subtraction.png')
            plt.show()
        
        self.result_mean[label] = {'Ki' : np.sum(result[label]['bins']*result[label]['remove'])}
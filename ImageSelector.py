import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets  import RectangleSelector
from matplotlib.patches import Circle
from matplotlib.artist import Artist
# xdata = np.linspace(0,9*np.pi, num=301)
# ydata = np.sin(xdata)

# fig, ax = plt.subplots()
# ax.plot(xdata, ydata)




# tellme('left click to started\n  double click to confirm')

class window_motion:

    def  __init__(self, fig, ax, manRadius = False):
        self.fig = fig
        self.ax = ax
        self.pressed = None
        self.region = []
        self.circ = Circle((0,0), 0, fill=False, color='r')
        self.ax.add_patch(self.circ)
        self.left = None
        self.right = None
        self.manRadius = manRadius
    def tellme(self, s):
        print(s)
        plt.title(s, fontsize = 16)
        plt.draw() 
    def onclick(self, event):
        self.pressed = True
        self.double = event.dblclick
        if event.button == 1:
            self.left = True
            self.right = False
        elif event.button == 3:
            self.left = False
            self.right = True
        self.xcoor = event.xdata
        self.ycoor = event.ydata
        
        # if (not self.double) & (self.left):
            
        if self.right:
            if self.region == []:
                print('please select')
            else:
                for cir in self.region:
                    if ((self.xcoor-cir[0])**2+(self.ycoor-cir[1])**2) < cir[2]**2:
                        self.ax.add_patch(Circle((cir[0], cir[1]), 1/2*cir[2], fill=True, color='grey') )
                        self.region.remove(cir)
                        self.fig.canvas.draw()


        elif self.double:
            self.region.pop()
            plt.close()
            # print(self.region)
        
        elif self.left & (not self.manRadius):
            self.pressed = False
            
            
            self.drawcirc(event)
            self.ax.add_patch(self.circ)
            self.tellme('region center in {:.2f}, {:.2f}, radius {:.2f}\n double click to confrim'.format(self.center[0], self.center[1], self.radius))
            self.plot()
            self.region.append(self.center+[self.radius])

    def onrelease(self, event):
        
        if (self.left) & self.manRadius:
            self.pressed = False
            self.drawcirc(event)
            self.ax.add_patch(self.circ)
            self.tellme('region center in {:.2f}, {:.2f}, radius {:.2f}\n double click to confrim'.format(self.center[0], self.center[1], self.radius))
            self.plot()
            self.region.append(self.center+[self.radius])


    def plot(self):
        for circ in self.region:
            self.ax.add_patch(Circle((circ[0], circ[1]), 1/2*circ[2], fill=False, color='r') )
        self.fig.canvas.draw()
        
    def connect(self):
        cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        rid = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)
        mot = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)

    def onmotion(self, event):
        if self.left:
            if self.pressed:
                self.drawcirc(event)
            
    def drawcirc(self, event):
        if self.manRadius:
            self.tmp_x, self.tmp_y = event.xdata, event.ydata
            x_vec = self.tmp_x - self.xcoor
            y_vec = self.tmp_y - self.ycoor
            self.center = [(self.tmp_x+self.xcoor)/2, (self.tmp_y+self.ycoor)/2]
            self.radius = np.sqrt(x_vec**2+y_vec**2)
            self.circ.set_center((self.center[0], self.center[1]))
            self.circ.set_height(self.radius)
            self.circ.set_width(self.radius)
        else:
            self.tmp_x, self.tmp_y = event.xdata, event.ydata
            self.center = [self.tmp_x, self.tmp_y]
            self.circ.set_center((self.tmp_x, self.tmp_y))
            self.radius = 5
            self.circ.set_height(self.radius)
            self.circ.set_width(self.radius)
        # self.ax.remove()
        # self.ax.plot([self.xcoor, event.xdata], [self.ycoor, self.ycoor])
        # self.ax.plot([self.xcoor, event.xdata], [event.ydata, event.ydata])
        # self.ax.plot([event.xdata, event.xdata], [self.ycoor, event.ydata])
        # self.ax.plot([self.xcoor, self.xcoor], [self.ycoor, event.ydata])
        # print(self.circ.get_height())
        # print(self.circ.get_width())
        # self.ax.add_patch(self.circ)
        
        self.fig.canvas.draw()
        
# plt.axis('equal')
# wm = window_motion(fig, ax)
# wm.connect()

# plt.show()    
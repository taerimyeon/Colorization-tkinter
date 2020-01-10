# -*- coding: utf-8 -*-
"""
Created on Wed Dec 25 16:17:22 2019

@author: Steven Jonathan (github: tttdddstvn)
"""


import numpy as np
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkf
import tkinter.colorchooser as tkc
import tkinter.messagebox as msg
from PIL import Image
from PIL import ImageTk
from PIL import ImageGrab
from colorizationCy import colorize, rgb2ntsc, ntsc2rgb


class Paint:
    gI = '0.bmp'  # For original image, default name
    cI = '0_marked.bmp'  # For marked image, default name
    filename = '0.png'  # Default filename, will be changed when read file
    penSize = 5.0  # Default brush size
    penColor = 'yellow'  # Default brush color
    H = 265  # Canvas height (fixed)
    W = 320  # Canvas width (fixed)
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Colorization using Optimization (Levin et al. 2004)")
        self.root.resizable(False, False)
        self.root.geometry("850x400")  # Define window size
        
        self.brushWidthText = tk.Label(self.root, text="Brush Width")
        self.brushWidthText.grid(row=0, column=0, columnspan=3, pady=10)
        
        self.inputImgText = tk.Label(self.root, text="Input Image")
        self.inputImgText.grid(row=0, column=3, columnspan=4, pady=10)
        
        self.outImgText = tk.Label(self.root, text="Output Image")
        self.outImgText.grid(row=0, column=7, columnspan=4, pady=10)
        
        self.penSizeLab = tk.Label(self.root,
                                   text="{0:.2f}".format(float(self.penSize)))
        self.penSizeLab.grid(row=1, column=1, sticky=tk.E+tk.W, padx=5, pady=5)
        
        self.penColorLab = tk.Canvas(self.root, width=20, height=20)
        self.penColorLab.grid(row=1, column=2)
        self.penColorLab.create_oval(5, 5, 20, 20,
                                     outline=self.penColor, fill=self.penColor)
        
        self.slider = ttk.Scale(self.root, from_= 1, to = 30,
                                command=self.changepenWidth,
                                orient=tk.HORIZONTAL)
        self.slider.set(self.penSize)
        self.slider.grid(row=1, column=0, padx=2, pady=2)
        
        # Define button(s) ====================================================
        self.browseButton = tk.Button(self.root, text='Browse',
                                      command=self.fileOpen,
                                      height=1, width=12)
        self.browseButton.grid(row=2, column=0, columnspan=3, padx=10, pady=5)
        
        self.changeColor = tk.Button(self.root, text='Change Colour',
                                     command=self.changepenColor,
                                     height=1, width=12)
        self.changeColor.grid(row=3, column=0, columnspan=3, padx=10, pady=5)
        
        self.exitButton = tk.Button(self.root, text='Exit',
                                    command=self.quitProgram,
                                    height=1, width=12)
        self.exitButton.grid(row=4, column=0, columnspan=3, padx=10, pady=5)
        
        self.clearCanvas = tk.Button(self.root, text='Clear Canvas',
                                     command=self.clrCanvas,
                                     height=1, width=12)
        self.clearCanvas.grid(row=5, column=3, columnspan=2)
        
        self.saveSketch = tk.Button(self.root, text='Save Sketch',
                                     command=self.saveSketchDia,
                                     height=1, width=12)
        self.saveSketch.grid(row=5, column=5, columnspan=2)
        
        self.colorizeButton = tk.Button(self.root, text='Colorize',
                                        command=self.colorizeImg,
                                        height=1, width=12)
        self.colorizeButton.grid(row=5, column=7, columnspan=2)
        
        self.saveColorized = tk.Button(self.root, text='Save Colorized',
                                       command=self.saveColorizedDia,
                                       height=1, width=12)
        self.saveColorized.grid(row=5, column=9, columnspan=2)
        # Define button(s) ====================================================
        
        # Create drawing canvas
        self.c = tk.Canvas(self.root, bg='white', width=self.W, height=self.H,
                           bd=0, highlightthickness=0)
        self.c.grid(row=1, column=3, rowspan=4, columnspan=4, padx=10, pady=5)
        
        # Create display canvas
        self.c1 = tk.Canvas(self.root, bg='white', width=self.W, height=self.H,
                            bd=0, highlightthickness=0)
        self.c1.grid(row=1, column=7, rowspan=4, columnspan=4, padx=10, pady=5)

        self.setup()
        self.root.mainloop()
    
    def fileOpen(self):
        self.filename = tkf.askopenfilename(initialdir="./images",
                                            title="Select a File",
                                            filetypes=(("bmp files", "*.bmp"),
                                                       ("png files", "*.png"),
                                                       ("jpg files", "*.jpg"),
                                                       ("all files", "*.*")))
        if self.filename:
            size = (self.W, self.H)
            imgFile = Image.open(self.filename)
            resized = imgFile.resize(size, Image.ANTIALIAS)
            self.gI = resized  # gI = original image, resized to fit canvas
            self.gI = np.array(self.gI)/255.0  # normalize to 0-1
            self.img = ImageTk.PhotoImage(resized)
            self.c.delete("all")
            self.c.create_image(0, 0, image=self.img, anchor=tk.NW, tags="IM2")
            self.fromBrowse = True
    
    def saveSketchDia(self):
        x = self.root.winfo_rootx()+self.c.winfo_x()
        y = self.root.winfo_rooty()+self.c.winfo_y()
        x1 = x+self.c.winfo_width()
        y1 = y+self.c.winfo_height()
        filenameSave = tkf.asksaveasfilename(initialdir="./images",
                                             defaultextension=".bmp",
                                             filetypes=(("bmp files", "*.bmp"),
                                                        ("png files", "*.png"),
                                                        ("jpg files", "*.jpg"),
                                                        ("all files", "*.*")))
        if filenameSave:
            # ImageGrab doesn't work well on scaled screen
            img = ImageGrab.grab((x, y, x1, y1))
            filenameSave = filenameSave[:-4]+"_marked.bmp"  # Append _marked
            img.save(filenameSave)
        else:
            return
    
    def colorizeImg(self):
        x = self.root.winfo_rootx()+self.c.winfo_x()
        y = self.root.winfo_rooty()+self.c.winfo_y()
        x1 = x+self.c.winfo_width()
        y1 = y+self.c.winfo_height()
        self.cI = ImageGrab.grab((x, y, x1, y1))
        self.cI = np.array(self.cI)/255.0  # cI is the marked image
        copycI = np.zeros_like(self.cI)
        rows, cols = self.cI.shape[0], self.cI.shape[1]
        for r in range(rows):
            for c in range(cols):
                # If a pixel(m, n) in all channels == 1 use gI otherwise cI
                if all(self.cI[r,c]==1):
                    copycI[r,c] = self.gI[r,c]
                else:
                    copycI[r,c] = self.cI[r,c]
        
        # Compute difference image to find the marked pixels
        colorIm = (np.sum(abs(self.gI-self.cI), axis=2) > 0.01)
        sgI = rgb2ntsc(self.gI)  # ntsc here is YUV color space
        #scI = rgb2ntsc(self.cI)
        scopycI = rgb2ntsc(copycI)
        
        ntscIm = np.zeros_like(sgI)
        ntscIm[:, :, 0] = sgI[:,:,0]
        ntscIm[:, :, 1] = scopycI[:,:,1]
        ntscIm[:, :, 2] = scopycI[:,:,2]
        
        # Function colorize() expects two args and return nI
        nI = colorize(colorIm, ntscIm)
        nI = ntsc2rgb(nI)  # nI is still in YUV so need to convert back to RGB
        nI = np.array(255*nI, dtype=np.uint8)
        
        self.img2 = ImageTk.PhotoImage(Image.fromarray(nI))
        self.c1.delete("all")
        self.c1.create_image(0, 0, image=self.img2, anchor=tk.NW, tags="IM3")
    
    def saveColorizedDia(self):
        x = self.root.winfo_rootx()+self.c1.winfo_x()
        y = self.root.winfo_rooty()+self.c1.winfo_y()
        x1 = x+self.c1.winfo_width()
        y1 = y+self.c1.winfo_height()
        filenameSave = tkf.asksaveasfilename(initialdir="./images",
                                             defaultextension=".bmp",
                                             filetypes=(("bmp files", "*.bmp"),
                                                        ("png files", "*.png"),
                                                        ("jpg files", "*.jpg"),
                                                        ("all files", "*.*")))
        if filenameSave:
            img = ImageGrab.grab((x, y, x1, y1))
            filenameSave = filenameSave[:-4]+"_result.bmp"  # Append _result
            img.save(filenameSave)
        else:
            return
    
    def changepenWidth(self, e):  # Change width of pen through slider
        self.penSize = e
        temp = float(self.penSize)
        if len("{0:.1f}".format(temp)) == 3:
            temp = "{0:.2f}".format(temp)
        else:
            temp = "{0:.1f}".format(temp)
        self.penSizeLab.config(text=temp)  # To update label (brush size)
        self.penSizeLab.update()
    
    def changepenColor(self):  # Changing the pen color
        color = tkc.askcolor(color=self.color)[1]
        if color:  # If not clicking 'Cancel' when choosing color
            self.color = color
            self.penColorLab.create_oval(5, 5, 20, 20,
                                         outline=self.color, fill=self.color)
    
    def setup(self):
        self.old_x = None
        self.old_y = None
        self.line_width = self.penSize
        self.color = self.penColor
        self.eraser_on = False
        self.c.bind('<B1-Motion>', self.paint)
        self.c.bind('<ButtonRelease-1>', self.reset)
    
    def quitProgram(self):
        MsgBox = msg.askquestion("Exit Application",  # Window title
                                 "Are you sure you want to exit?",  # Message
                                 icon="warning")
        if MsgBox == 'yes':
            self.root.destroy()

    def clrCanvas(self):  # To clear drawing canvas
        self.c.delete("all")
        self.c1.delete("all")

    def paint(self, event):
        self.line_width = self.penSize
        paint_color = 'white' if self.eraser_on else self.color
        if self.old_x and self.old_y:
            self.c.create_line(self.old_x, self.old_y, event.x, event.y,
                               width=self.line_width, fill=paint_color,
                               capstyle=tk.ROUND, smooth=False, splinesteps=36)
        self.old_x = event.x
        self.old_y = event.y

    def reset(self, event):
        self.old_x, self.old_y = None, None


if __name__ == "__main__":
    Paint()

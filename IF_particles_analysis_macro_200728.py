# Import required packages

import os, sys, csv, math, datetime
from ij import IJ, ImagePlus, ImageStack, WindowManager
from ij.io import DirectoryChooser
from ij.io import FileSaver
from ij.measure import ResultsTable
from ij.measure import Measurements
from ij.process import ImageProcessor
from ij.process import ImageConverter
from ij.gui import WaitForUserDialog
from ij.gui import GenericDialog
from ij.plugin.frame import RoiManager
from ij.plugin.filter import ParticleAnalyzer
from ij.plugin.filter import Analyzer
from ij.plugin import ChannelSplitter
from ij.plugin import Duplicator
from ij.plugin import ImageCalculator
from ij.plugin import RGBStackMerge
from java.awt import Color

import time

# Set Threshold mode

thresholdMode = False

colors2= ["Red" ,"Green" ,"Blue"]

thresholds = {}

gd = GenericDialog("Set Threshold Mode")
gd.addChoice("Would you like to enable thresholding mode?", ["No, run the normal macro", "Yes, enable thresholding mode"], "No")
gd.showDialog()

if gd.getNextChoice() == "Yes, enable thresholding mode":
    thresholdMode = True
    
if thresholdMode == False:
    gd = GenericDialog("Set Thresholds")
    gd.addStringField("Lower bound for Red", "90")
    gd.addStringField("Lower bound for Green", "100")
    gd.addStringField("Lower bound for Blue", "100")
    gd.showDialog()
    thresholds["Red"] = int(gd.getNextString());
    thresholds["Green"] = int(gd.getNextString());
    thresholds["Blue"] = int(gd.getNextString());
    
gd = GenericDialog("Other Thresholds.")
gd.addMessage("Adjust after you have determined if new thresholds are needed.")
    

# Set default thresholds:
#	minimum_size is the minimum area to be considered an ROI

	
minimum_size=[]
maximum_size=[]

for x,color in enumerate(colors2):
	gd.addStringField("Minimum Size of ROI for Channel "+color,"30")
	gd.addStringField("Maximum Size of ROI for Channel "+color, "2000")

gd.showDialog()



for x in range(len(colors2)):
	minimum_size.append(float(gd.getNextString()))
	maximum_size.append(float(gd.getNextString()))

#set pix_width and pix_height to real dimensions per pixel 



# Get input and output directories with GUI 

dc = DirectoryChooser("Choose an input directory")  
inputDirectory = dc.getDirectory() 

dc = DirectoryChooser("Choose an output directory")
outputDirectory = dc.getDirectory()

output_name =outputDirectory+"output.csv"
open(output_name, "w").close

# set the output column names for the csv sheet

subfolders = []
# Finds subfolders in input directory

for subfolder in os.listdir(inputDirectory):
    if os.path.isdir(inputDirectory + subfolder):
        subfolders.append(subfolder)

# If there are no subfolders, runs on images in input directory instead

if len(subfolders) == 0:
    subfolders = [""]
for subfolder in subfolders:

    #Opens each image

    for filename in os.listdir(inputDirectory + subfolder): 
        imp = IJ.openImage(inputDirectory + subfolder + '/' + filename)	

        if imp:
            #IJ.run(imp, "Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=0.87" "pixel_height=0.87" "voxel_depth=25400.0508001")			


            # Splits channels

           
            #Summary contains the information for a row for the current image

            summary = {}
            summary['Directory'] = inputDirectory + subfolder
            summary['Subfolder']= subfolder
            summary['Filename'] = filename
            summary["Big-area"] = imp.getProcessor().getStatistics().area
            color = ["Red" ,"Green" ,"Blue"]
            summary["Red-Green-Coloc-%"]="NA"
            summary["Green-Red-Coloc-%"]="NA"
       








            # FINDS THE TISSUE AREA
            img2 = imp.duplicate()
            channels2=ChannelSplitter.split(img2);
            blueimg2=channels2[2];
            IJ.run(blueimg2, "8-bit", "");
            IJ.setAutoThreshold(blueimg2, "Default dark");
            IJ.setThreshold(blueimg2,28, 254);
            IJ.run(blueimg2, "Convert to Mask", "");
            blueimg2.show()
            time.sleep(1)
            rt2 = ResultsTable()
            ta=Analyzer(blueimg2,Measurements.AREA|Measurements.LIMIT,rt2)
            ta.measure();
            double=rt2.getColumnAsDoubles(rt2.getColumnIndex("Area"))
            summary["Tissue-area"] =double[0];
            blueimg2.changes = False
            blueimg2.close()
            	

#    PARTICLE ANALYSIS ETC..
                
            channels = ChannelSplitter.split(imp);
            
            
            
            for i, channel in enumerate(channels):
                IJ.run(channel, "8-bit", "");
                IJ.run(channel, "Subtract Background...", "rolling=50 sliding");
                IJ.setAutoThreshold(channel,"Default");
                summary[color[i] + "-intensity"] = "NA"
                summary[color[i] + "-ROI-count"] = "NA"
                
                
                
                    #gets the mean grey intensity of the channel
                    
                    # Measures each channel
                    
                IJ.run("Set Measurements...", "area mean display redirect=None decimal=1");

                summary[color[i] + "-intensity"] = channel.getStatistics(Measurements.MEAN).mean
                


                
                

            
                #Sets the thresholds from the dialog box
                IJ.setAutoThreshold(channel,"Default");
                channel.show()
                
                if thresholdMode == False:
                    IJ.setThreshold(channel, thresholds[color[i]], 255)
                    summary[color[i] + "-threshold-used"] = ImageProcessor.getMinThreshold(channel.getProcessor())
                
                # if thresholdMode:
                #     happy=False
                #     while(happy==False):
                #         IJ.run("Threshold...")
                #         WaitForUserDialog("Title", "Adjust threshold for " + color[i]).show()
                        
                #         gd = GenericDialog("Set Threshold Mode")
                #         gd.addChoice("Do you want to continue with this threshold?", ["No,choose again", "Yes, use this threshold."],"No")
                #         gd.showDialog()
                #         if gd.getNextChoice() == "Yes, use this threshold.":
                #             happy = True


                #     #Get the threshold you've used
                # summary[color[i] + "-threshold-used"] = ImageProcessor.getMinThreshold(channel.getProcessor())

                    #Threshold and watershed

                    IJ.run(channel, "Convert to Mask", "")
                    IJ.run(channel, "Watershed", "")
                    IJ.run("Set Measurements...", "area mean limit display redirect=None decimal=1");
                    
                    table = ResultsTable()
                    roim = RoiManager(True)
                    ParticleAnalyzer.setRoiManager(roim)

                        #Analyses particles: finds all the objects that match criteria
                    
                    pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER | ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES, Measurements.AREA, table, minimum_size[i], maximum_size[i], 0.1, 1.0)
                    pa.setHideOutputImage(True)
                    pa.analyze(channel)
                
                
                if thresholdMode:
                    happy=False
                    while(happy==False):
                        IJ.run("Threshold...")
                        WaitForUserDialog("Title", "Adjust threshold for " + color[i]).show()
                        summary[color[i] + "-threshold-used"] = ImageProcessor.getMinThreshold(channel.getProcessor())
                        channel.show()
                       
                        summary[color[i] + "-threshold-used"] = ImageProcessor.getMinThreshold(channel.getProcessor())
                      
                        copy=channel.duplicate()
                        copy.show()
                        

                        IJ.setThreshold(copy, ImageProcessor.getMinThreshold(channel.getProcessor()), ImageProcessor.getMaxThreshold(channel.getProcessor()))
#                        channel.close()
                        IJ.run(copy, "Convert to Mask", "")
                        IJ.run(copy, "Watershed", "")
                        IJ.run("Set Measurements...", "area mean limit display redirect=None decimal=1");
                        
                        table = ResultsTable()
                        roim = RoiManager(True)
                        ParticleAnalyzer.setRoiManager(roim)

                        #Analyses particles: finds all the objects that match criteria
                    
                        pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER | ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES, Measurements.AREA, table, minimum_size[i], maximum_size[i], 0.1, 1.0)
                        pa.analyze(copy)
                        copy.show()
                        WaitForUserDialog("Title", "Look at threshold for" + color[i]).show()
                        gd = GenericDialog("Set Threshold Mode")
                        gd.addChoice("Do you want to continue with this threshold?", ["No,choose again", "Yes, use this threshold."],"No")
                        gd.showDialog()
                        copy.changes = False
                        copy.close()

                        if gd.getNextChoice() == "Yes, use this threshold.":
                            happy = True
                            

                
                
                    #adds count to summary 
                
                if table.getColumnIndex("Area") != -1:
                    summary[color[i] + "-ROI-count"] = len(table.getColumn(table.getColumnIndex("Area")))
                    doubles=table.getColumnAsDoubles(table.getColumnIndex("Area"))
                    summary[color[i]+ "-Total-area"] =sum(doubles)
                    arr=[]

                    for x, y in enumerate(doubles):
                        if(y>=100) & (y<=3000):
                            arr.append(y)

                    summary[color[i]+"-Cell-Count"]=len(arr)
                    summary[color[i]+"-Cell-Area"]=sum(arr)
                    summary[color[i]+"-Max-ROI"]=maximum_size[i]
                    summary[color[i]+"-Min-ROI"]=minimum_size[i]
                    summary[color[i]+"-ratio-cell count/tissue area"]=len(arr)/summary["Tissue-area"]
                    summary[color[i]+"-ratio-particles/tissue area"]=len(table.getColumn(table.getColumnIndex("Area")))/summary["Tissue-area"]
                    summary[color[i]+"-ratio-totalareaofparticles/tissue area"]=sum(doubles)/summary["Tissue-area"]


                channel.changes = False
                channel.close()

                roim.reset()
                roim.close()


                 # FINDS THE COLOCALIZATION PERCENTAGE BETWEEN GREEN AND RED CHANNEL
            pa_red = ParticleAnalyzer(ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES | ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.IN_SITU_SHOW, Measurements.AREA, table, minimum_size[0], maximum_size[0], 0.1, 1.0)
            pa_green = ParticleAnalyzer(ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES | ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.IN_SITU_SHOW, Measurements.AREA, table, minimum_size[1], maximum_size[1], 0.1, 1.0)

            img3=imp.duplicate()
            channels_coloc=ChannelSplitter.split(img3);
            red_coloc=channels_coloc[0];
            green_coloc=channels_coloc[1];
            IJ.setAutoThreshold(red_coloc, "Default dark");
            IJ.run(red_coloc, "Options...", "BlackBackground=true");
            IJ.setThreshold(red_coloc,summary["Red" + "-threshold-used"], 255);
            IJ.run(red_coloc, "Convert to Mask", "");
            pa_red.analyze(red_coloc)
#            red_coloc.show()
            rt3 = ResultsTable()
            ta_coloc=Analyzer(red_coloc, Measurements.INTEGRATED_DENSITY ,rt3)
            ta_coloc.measure();
            redIntensity=(rt3.getColumnAsDoubles(rt3.getColumnIndex("IntDen")))[0];
            imp.close()

            IJ.setAutoThreshold(green_coloc, "Default dark");
            IJ.run(green_coloc, "Options...", "BlackBackground=true");
            IJ.setThreshold(green_coloc,summary["Green" + "-threshold-used"], 255);
            IJ.run(green_coloc, "Convert to Mask", "");
            pa_green.analyze(green_coloc)
#            green_coloc.show()
            rt4 = ResultsTable()
            ta_coloc2=Analyzer(green_coloc,Measurements.INTEGRATED_DENSITY ,rt4);
            ta_coloc2.measure();
            greenIntensity=(rt4.getColumnAsDoubles(rt4.getColumnIndex("IntDen")))[0];

            ic_coloc =ImageCalculator();
            coloc_img=ic_coloc.run("Multiply create",red_coloc,green_coloc);
            rt5 = ResultsTable()
            ta_coloc3=Analyzer(coloc_img,Measurements.INTEGRATED_DENSITY ,rt5);
            ta_coloc3.measure();
            totalIntensity=(rt5.getColumnAsDoubles(rt5.getColumnIndex("IntDen")))[0];
            rgb=RGBStackMerge();
            composite=rgb.mergeChannels([red_coloc,green_coloc],False); 
            composite.show();
            fs=FileSaver(composite);
            fs.saveAsJpeg(outputDirectory + '/' + "coloc_"+filename);
            composite.close();
            
            summary["Coloc density"]= totalIntensity
            summary["Red integrated density"]= redIntensity
            summary["Green integrated density"]= greenIntensity

            if redIntensity == 0:
                summary["Red-Green-Coloc-%"]= "NaN"
            else:
            	summary["Red-Green-Coloc-%"]= float (totalIntensity*100/redIntensity)
            
            if greenIntensity == 0:
                summary["Green-Red-Coloc-%"]= "NaN"
            else:
            	summary["Green-Red-Coloc-%"]= float (totalIntensity*100/greenIntensity)
            	
  # FINDS THE COLOCALIZATION PERCENTAGE BETWEEN RED AND BLUE CHANNEL
            pa_red2 = ParticleAnalyzer(ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES | ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.IN_SITU_SHOW, Measurements.AREA, table, minimum_size[0], maximum_size[0], 0.1, 1.0)
            pa_blue = ParticleAnalyzer(ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES | ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.IN_SITU_SHOW, Measurements.AREA, table, minimum_size[1], maximum_size[1], 0.1, 1.0)

            img4=imp.duplicate()
            channels_coloc2=ChannelSplitter.split(img4);
            red_coloc=channels_coloc2[0];
            blue_coloc=channels_coloc2[2];
           
            IJ.setAutoThreshold(red_coloc, "Default dark");
            IJ.run(red_coloc, "Options...", "BlackBackground=true");
            IJ.setThreshold(red_coloc,summary["Red" + "-threshold-used"], 255);
            IJ.run(red_coloc, "Convert to Mask", "");
            pa_red2.analyze(red_coloc)

            IJ.setAutoThreshold(blue_coloc, "Default dark");
            IJ.run(blue_coloc, "Options...", "BlackBackground=true");
            IJ.setThreshold(blue_coloc,summary["Blue" + "-threshold-used"], 255);
            IJ.run(blue_coloc, "Convert to Mask", "");
            pa_blue.analyze(blue_coloc)

            rt5 = ResultsTable()
            ta_coloc4=Analyzer(blue_coloc,Measurements.INTEGRATED_DENSITY ,rt5);
            ta_coloc4.measure();
            blueIntensity=(rt5.getColumnAsDoubles(rt5.getColumnIndex("IntDen")))[0];

            ic_coloc2 =ImageCalculator();
            coloc_img2=ic_coloc2.run("Multiply create",red_coloc,blue_coloc);
            rt5 = ResultsTable()
            ta_coloc4=Analyzer(coloc_img2,Measurements.INTEGRATED_DENSITY ,rt5);
            ta_coloc4.measure();
            totalIntensity2=(rt5.getColumnAsDoubles(rt5.getColumnIndex("IntDen")))[0];
            rgb2=RGBStackMerge();
            composite2=rgb2.mergeChannels([red_coloc,blue_coloc],False); 
            composite2.show();
            fs=FileSaver(composite2);
            fs.saveAsJpeg(outputDirectory + '/' + "coloc2_"+filename);
            composite2.close();
            
            summary["Coloc2 density"]= totalIntensity2
            summary["Blue integrated density"]= blueIntensity

            if redIntensity == 0:
                summary["Red-Blue-Coloc-%"]= "NaN"
            else:
            	summary["Red-Blue-Coloc-%"]= float (totalIntensity2*100/redIntensity)
            
            if blueIntensity == 0:
                summary["Blue-Red-Coloc-%"]= "NaN"
            else:
            	summary["Blue-Red-Coloc-%"]= float (totalIntensity2*100/blueIntensity)

                # Writes everything in the output file
            fieldnames=[]
            fieldnames.append("Directory")
            fieldnames.append("Subfolder")
            fieldnames.append("Filename")
            fieldnames.append("Tissue-area")
            fieldnames.append( "Big-area")
                
            

            fieldnames.append("Red"+"-intensity")
            fieldnames.append("Red"+ "-threshold-used")
            fieldnames.append("Red"+ "-ROI-count")
            fieldnames.append("Red"+ "-Max-ROI")
            fieldnames.append("Red"+ "-Min-ROI")
            fieldnames.append("Red"+"-Total-area")
            fieldnames.append("Red"+ "-Cell-Count")
            fieldnames.append("Red"+ "-Cell-Area")
            fieldnames.append("Red"+ "-ratio-particles/tissue area")
            fieldnames.append("Red"+ "-ratio-totalareaofparticles/tissue area")
            fieldnames.append("Red"+"-ratio-cell count/tissue area")
            
            fieldnames.append("Green"+"-intensity")
            fieldnames.append("Green"+ "-threshold-used")
            fieldnames.append("Green"+ "-ROI-count")
            fieldnames.append("Green"+ "-Min-ROI")
            fieldnames.append("Green"+ "-Max-ROI")
            fieldnames.append("Green"+"-Total-area")
            # fieldnames.append("Green"+ "-Cell-Count")
            # fieldnames.append("Green"+ "-Cell-Area")
            fieldnames.append("Green"+ "-ratio-particles/tissue area")
            fieldnames.append("Green"+ "-ratio-totalareaofparticles/tissue area")

            fieldnames.append("Blue"+"-intensity")
            fieldnames.append("Blue"+ "-threshold-used")
            fieldnames.append("Blue"+ "-ROI-count")
            fieldnames.append("Blue"+ "-Min-ROI")
            fieldnames.append("Blue"+ "-Max-ROI")
            fieldnames.append("Blue"+"-Total-area")
            # fieldnames.append("Blue"+ "-Cell-Count")
            # fieldnames.append("Blue"+ "-Cell-Area")
            fieldnames.append("Blue"+ "-ratio-particles/tissue area")
            fieldnames.append("Blue"+ "-ratio-totalareaofparticles/tissue area")
            fieldnames.append("Red-Green-Coloc-%")
            fieldnames.append("Green-Red-Coloc-%")
            fieldnames.append("Red-Blue-Coloc-%")
            fieldnames.append("Blue-Red-Coloc-%")
            fieldnames.append("Coloc density")
            fieldnames.append("Coloc2 density")
            fieldnames.append("Red integrated density")
            fieldnames.append("Green integrated density")
            fieldnames.append("Blue integrated density")



            
            

        #                 for i, channel in enumerate(channels):
        #                     fieldnames.append(color[i]+"-intensity")
        #                     fieldnames.append(color[i]+ "-threshold-used")
        #                     fieldnames.append(color[i]+ "-ROI-count")
        #                     fieldnames.append(color[i]+ "-Total-area")
        #                     fieldnames.append(color[i]+ "-Min-ROI")
        #                     fieldnames.append(color[i]+ "-Max-ROI")
        #                     fieldnames.append(color[i]+ "-big-area")
        #                     fieldnames.append(color[i]+ "-ratio-particles/tissue area")
        #                     fieldnames.append(color[i]+ "-ratio-totalareaofparticles/tissue area")
        # #                    fieldnames.append(color[i]+ "-tissue-area")

                
            with open(output_name, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore', lineterminator = '\n')
                if os.path.getsize(output_name) < 1:
                    writer.writeheader()
                writer.writerow(summary)

        

            

            
            
# End of macro
cat = """

       \    /\           Macro completed!    
        )  ( ')   meow!
       (  /  )
        \(__)|"""

print(cat)

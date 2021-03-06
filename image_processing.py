import os
import time
import imageio
import imgaug as ia
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage
from imgaug import augmenters as iaa 
from imgaug import parameters as iap
from collections import defaultdict
from PIL import Image
import numpy as np
from skimage import io as sk_io
ia.seed(1)


def conversion(txt_file_directory,image_directory,conversion_seq):
	"""
	Takes images and annotations from different folders, applies transformation to both the image
	and annotation, and saves both. 
	"""

	# go one level back.
	img_save_dir=os.path.join(os.path.split(image_directory)[0],"images_transformed") 
	txt_sav_dir=os.path.join(os.path.split(txt_file_directory)[0],"yolo_annotations_transformed")
	
	if not os.path.exists(img_save_dir):
		os.makedirs(img_save_dir)

	if not os.path.exists(txt_sav_dir):
		os.makedirs(txt_sav_dir)

	# sepereted directories is good to make sure we loop simultanouesly.
	iterable= zip(os.listdir(image_directory),os.listdir(txt_file_directory)) 
	
	count=0

	for img,txt in iterable:
		bb_list=[]
		l=[]
		label_list=[]

		"""
		the img and txt have need to match exactly.
		"""
		

		if img.endswith(".jpg") and txt.endswith(".txt") and img.rstrip(".jpg")== txt.rstrip(".txt"):
			

			image = imageio.imread(os.path.join(image_directory,img))

			file=open(os.path.join(txt_file_directory,txt))


			for line in file.readlines():	


				"""
				read from the yolo format, convert to pascal voc, which matches the bounding box requirements of 
				imgaug's BoundingBox class.
				"""
			
				label=int(line.split()[0])

				# create a list, then remove the class label.
				new_line=line.split()[1:] 
			
				xmin = max(float(new_line[0]) - float(new_line[2]) / 2, 0)
				xmax = min(float(new_line[0]) + float(new_line[2]) / 2, 1)
				ymin = max(float(new_line[1]) - float(new_line[3]) / 2, 0)
				ymax = min(float(new_line[1]) + float(new_line[3]) / 2, 1)

				xmin = float(image.shape[1] * xmin)
				xmax = float(image.shape[1] * xmax)
				ymin = float(image.shape[0] * ymin)
				ymax = float(image.shape[0] * ymax)
								
				bb=BoundingBox(x1=xmin, x2=xmax, y1=ymin, y2=ymax)
				bb_list.append(bb)
				label_list.append(label)
	
			bbs = BoundingBoxesOnImage(bb_list,shape=image.shape)

			image_aug, bbs_aug = conversion_seq(image=image, bounding_boxes=bbs)
			for i in range(len(bbs.bounding_boxes)):
				
				"""
				Convert the  voc bounding box format back to yolo format.
				"""
				after=bbs_aug.bounding_boxes[i]
				

				xcen = float((after.x1 + after.x2)) / 2 / image_aug.shape[1] 
				ycen = float((after.y1 + after.y2)) / 2 / image_aug.shape[0]

				w = float((after.x2 - after.x1)) / image_aug.shape[1]
				h = float((after.y2 - after.y1)) / image_aug.shape[0]


				l1=[label,xcen, ycen, w, h] 
				l.append(l1)
				
			label_array=np.array(label_list)
			yolo_array=np.array(l)

	
			yolo_array[:,0]=label_array

			yolo_array=yolo_array[~np.any(yolo_array[:,1:]<0,axis=1)] 
			yolo_array=yolo_array[~np.any(yolo_array[:,1:]>1,axis=1)]

			
			txt=os.path.splitext(txt)[0]+"a"+".txt"
			with open(os.path.join(txt_sav_dir,txt),"wt", encoding='ascii') as stream: 		
				
				# format types for all columns.
				fmt= '%d', '%1.7f', '%1.7f', '%1.7f','%1.7f' 
				np.savetxt(stream, yolo_array, fmt=fmt)
				
			
			#save images.
			img=os.path.splitext(img)[0]+"a"+".jpg" #saves the transformed image with "a" notation at the end.
			file_path = os.path.join(img_save_dir, img)
			sk_io.imsave(file_path, image_aug) # save the transformed image.
			#ia.imshow(image_aug)

			count+=1
			if count%50==0:
				print("{} annotations and images have been transformed!!".format(count))



sometimes=lambda aug: iaa.Sometimes(0.9,aug) 

seq=iaa.SomeOf((1,2),
	[
	sometimes(iaa.BlendAlphaFrequencyNoise(foreground=iaa.EdgeDetect(0.75),upscale_method="nearest")),

	sometimes(iaa.BlendAlphaMask(iaa.InvertMaskGen(0.5, iaa.VerticalLinearGradientMaskGen()),
		iaa.Sequential([iaa.Clouds(),iaa.WithChannels([1, 2])]))),

	sometimes(iaa.BlendAlphaCheckerboard(nb_rows=2, nb_cols=(1, 4),foreground=iaa.AddToHue((-80, 80)))),

	#important augmenter
	sometimes(iaa.BlendAlphaVerticalLinearGradient(iaa.AveragePooling(10),start_at=(0.0, 1.0), end_at=(0.0, 1.0))),

	sometimes(iaa.BlendAlphaSimplexNoise(iaa.EdgeDetect(1.0),upscale_method="linear"))
	
	])


sometimes2=lambda aug: iaa.Sometimes(0.95,aug) # probability is increased

seq2=iaa.SomeOf((1,2),
	[
	
	sometimes2(iaa.AdditiveGaussianNoise(scale=(10, 70))),
	
	#sometimes(iaa.AverageBlur(k=(3, 5))), # varying kernel size. 
	
	sometimes2(iaa.GaussianBlur(sigma=(1.0, 3.0))), # not the same as gaussian noise.

	sometimes2(iaa.MotionBlur(k=10, angle=[-30, 30])),
	
	sometimes2(iaa.MeanShiftBlur(spatial_radius=(5.0, 40.0), color_radius=(5.0, 40.0))), # heavy but important augmenter.

	#These three are from contrast module, the above five from  blur module.
	sometimes2(iaa.HistogramEqualization()),

	sometimes2(iaa.SigmoidContrast(gain=(3, 10), cutoff=(0.4, 0.6))),

	sometimes2(iaa.LinearContrast(alpha=(0.6, 1.4)))

	])


sometimes3=lambda aug: iaa.Sometimes(0.93,aug)

seq3=iaa.SomeOf((1,2),
	[
	
	#sometimes3(iaa.Affine(scale=1.5)), # cuts out part of the objects, resulting in negative coordinates..
 
	sometimes3(iaa.ElasticTransformation(alpha=(20, 30.0), sigma=5.0)),

	sometimes3(iaa.Rot90((1, 3), keep_size=False)), # On 90,270 transformation, the width and height change.

	sometimes3(iaa.Rotate((-30, 30))),

	sometimes3(iaa.WithPolarWarping(iaa.AveragePooling((2, 7)))),
	
	sometimes3(iaa.ShearY((30, 50))), 
	
	sometimes3(iaa.ShearX((30, 70))),

	 
	])



# img_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\(3,4)-geometric"
# txt_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\(3,4)-geometric-labels"
img_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\main\\main\\main experiments\\Not Augmented\\train_images"
txt_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\main\\main\\main experiments\\Not Augmented\\train_annotations_yolo"

if __name__=="__main__":		
	start=time.time()
	conversion(txt_path,img_path,seq3)
	print("Running Time is: %.3f seconds." % (time.time()-start))

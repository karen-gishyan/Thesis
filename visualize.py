
import imgaug as ia
import imgaug.augmenters as iaa
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage
from PIL import Image
import xml.etree.ElementTree as ET
import os
from scipy import misc



def visualize_bounding_box(annot_path,images_path,save=True):

	save_path=os.path.join(os.path.dirname(images_path),"images_with_bounding_boxes")

	if not os.path.exists(save_path):
		os.makedirs(save_path)

	count=0
	for xml in os.listdir(annot_path):

		bounding_box_list=[]

		full_path=os.path.join(annot_path,xml)
		tree=ET.parse(full_path)
		root=tree.getroot()		
		
		for object in root.iter("object"): 
					
			voc_list=[]

			name=str(object.find("name").text)		
			box= object.find("bndbox")

			xmin=int(box.find("xmin").text)
			ymin=int(box.find("ymin").text)
			xmax=int(box.find("xmax").text)
			ymax=int(box.find("ymax").text)

			bb_list=[xmin,ymin,xmax,ymax]
			bounding_box_list.append(BoundingBox(*bb_list))

		image_path=os.path.join(images_path,os.path.splitext(xml)[0]+".jpg")
		image=Image.open(image_path)


		bbs = BoundingBoxesOnImage(bounding_box_list, shape=image.size) 

		with_boxes=bbs.draw_on_image(image,size=2)
		
		count+=1
		if count<3:
			ia.imshow(with_boxes)
		
		if save:
			im=Image.fromarray(with_boxes)
			im.save(os.path.join(save_path,os.path.splitext(xml)[0]+".jpg"))
		

	
if __name__=="__main__":
	annot_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\trials\\grid_horizontal_xmls"
	images_path="C:\\Users\\gishy\\Dropbox\\My PC (LAPTOP-SQRN8N46)\\Desktop\\trials\\grid_horizontal_images"
	visualize_bounding_box(annot_path,images_path)








# -*- coding: utf-8 -*-
"""
Created on Wed Sep  1 19:19:42 2021

@author: Dhanajayan
"""


from pdf2image import convert_from_path
from numpy import asarray
import numpy as np
import cv2
import pytesseract
from pytesseract import Output
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import pandas as pd


def invoice_data_extraction(pdf_path,poppler_path):
    # pdf file location
    pdf_path = pdf_path
    # convert pdf to image
    img = convert_from_path(pdf_path,fmt = 'png',poppler_path = poppler_path)
    # Adjust image pixel for better ocr results
    def adjust_gamma(image,gamma = 1.0):
        
        invGamma = 1.0/gamma
        table = np.array([((i/255)** invGamma)*255
                           for i in np.arange(0,256)]).astype('uint8')
        
        return cv2.LUT(image,table)
        
    img_file =  asarray(img[0])
    gamma = .5
    
    adjusted = adjust_gamma(img_file,gamma = gamma)
    
    custom_config = r'--oem 3 --psm 6'
    text_data = pytesseract.image_to_data(adjusted,config=custom_config,
                                          output_type=Output.DICT)    
    
    df = pd.DataFrame(text_data)
    
    df = df.drop(["level","page_num","par_num","block_num","conf",
                  "width","height"],axis = 1)
    
    Quantity = []
    vat_price =[]
    
    for idx,word in enumerate(df["text"]):
        if word.lower() == "Qty".lower() or word.lower() == "Quantity".lower():
             line_no_1 = df["line_num"][idx]
             new_df = df[idx:]
             new_df.reset_index(drop=True, inplace=True)
             position = df["left"][idx]
             #text = new_df[ new_df["word_num"] == word_no]
             # Extract quantity of each line items
             for t,(txt, j) in enumerate(zip(new_df["text"],new_df["left"])):
                 if (abs(j-position) < 50) :
                     
                     if txt.isnumeric() == True:
                         top_1 = new_df["top"][t]
                         
                         Quantity.append(int(txt))
                         
             # Extract Vat of each quantity  
             for i,(txt, k) in enumerate(zip(new_df["text"],new_df["left"])):
                 if txt.lower() == "VAT".lower():
                     line_no_2 = new_df["line_num"][i]
                     
                     if line_no_1 == line_no_2:
                         vat = []
                         position_1 = new_df["left"][i]
                         for j,(txt, k) in enumerate(zip(new_df["text"],new_df["left"])):
                             if (abs(k-position_1) < 50) :
                                 top = new_df["top"][j]
                                
                                 if top <= (top_1+10):
                                     if (txt.replace('.', '', 1).isdigit()) == True:
                                      vat.append(txt)
                                      
                         vat_price.append(vat)                        
                                         
        # extract total invoce amout and vat amount          
        elif word.lower() == "Total".lower():
            line_no = df["line_num"][idx]
            total_df = df[df["line_num"] == line_no]
            total_amount = ' '.join(total_df["text"])
            vat_line_df = df[df["line_num"] == (line_no-1)]
            total_vat = ' '.join(vat_line_df["text"])

    df_final = pd.DataFrame(Quantity,columns = ["Quantity"])
    try:
        df_final["VAT"] = vat_price
    except ValueError:
        pass
    
    return df_final, total_vat,total_amount
    
    
    
if __name__ == '__main__':
    pdf_path = r"C:\Users\Dhanajayan\Desktop\infognana\CG_0a2898ab-ed08-4029-b860-b8c470af27d7_1777792.pdf"
    poppler_path = r"C:\Users\Dhanajayan\Downloads\Release-21.03.0\poppler-21.03.0\Library\bin"
    df_QTY_VAT,total_vat_price,total_invoce_amount = invoice_data_extraction(pdf_path,poppler_path)
    
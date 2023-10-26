from ftplib import FTP
from datetime import datetime, timedelta
import time
from PIL import Image
import os
import numpy as np

def DownloadFile(fn: str) -> bool:
    try:
        with open(fn,'wb') as fp:
            ftp.retrbinary(f'RETR {fn}', fp.write)
            print(f'Downloaded {fn}')
            return True
    except:
        print(f'File "{fn}" does not exsit')
        return False

def CropAndResize(fn: str, path = ''):
    img = Image.open(path+fn)
    border = 70 + 16
    down = 70
    img = img.crop((border, border+down, img.width - border, img.height - border+down))
    img = img.resize((240,240),Image.Resampling.LANCZOS)
    img.save(fn)

def UpdateImageNames(fn: str, num: int):
    new_img = Image.open(fn)
    img_list = []
    for i in range(num):
        img_name = f'images/{i}.png'
        if not os.path.isfile(img_name):
            new_img.save(img_name)
            return
        img_list.append(Image.open(img_name))
    # remove first element
    img_list.pop(0)
    # add new image
    img_list.append(new_img)
    # save in order
    for i in range(num):
        img_name = f'images/{i}.png'
        img_list[i].save(img_name)

def CombineImages(num: int, cols: int):

    rows = int(np.ceil(num/cols))

    fileFormat = 'images/{name}.png'
    filenames = [fileFormat.format(name = x) for x in range(num)]
    images = [Image.open(x).convert("RGBA") for x in filenames]
    widths, heights = zip(*(i.size for i in images))

    total_width = max(widths)*cols
    total_height = max(heights)*rows

    new_im = Image.new("RGBA", (total_width, total_height))

    x_offset = 0
    y_offset = 0
    for im in images:

        new_im.paste(im, ( x_offset, y_offset ))
        x_offset += im.size[0]
        if x_offset >= total_width:
            x_offset = 0
            y_offset += im.size[1]

    new_im.save('images/radar.png', "PNG")


# while True:
#     image_count = 7
#     with FTP("ftp.bom.gov.au") as ftp:
#         # Create filename based on 2 mins ago
#         filename = (datetime.utcnow() - timedelta(minutes=6) ).strftime('IDR714.T.%Y%m%d%H%M.png')
#         ftp.login()
#         ftp.cwd("anon/gen/radar")
#         if DownloadFile(filename):
#             CropAndResize(filename)
#             UpdateImageNames(filename,image_count)
#             CombineImages(image_count,3)
#         os.remove(filename)
#     time.sleep(60)

# path = '../radar_backgrounds_orginal/'
# filelist=os.listdir(path)
# for f in filelist:
#     if f.endswith(".png"):
#         CropAndResize(f,path)

# back = Image.open('IDR714.background.png').convert("RGBA") 
# back.paste(Image.open('IDR714.topography.png').convert("RGBA"),(0,0),Image.open('IDR714.topography.png').convert("RGBA"))
# back.paste(Image.open('IDR714.roads.png').convert("RGBA"),(0,0),Image.open('IDR714.roads.png').convert("RGBA"))
# back.paste(Image.open('watchFace.png').convert("RGBA"),(0,0),Image.open('watchFace.png').convert("RGBA"))
# back.save('comb.png', "PNG")

# img = Image.open('IDR714.roads.png')
# img = img.convert("RGBA")
# datas = img.getdata()
# newData = []
# for item in datas:
#     if item[0] == 255 and item[1] == 255 and item[2] == 255:
#         newData.append((255, 255, 255, 0))
#     else:
#         newData.append(item)
# img.putdata(newData)
# img.save("IDR714.roads.png", "PNG")

#CropAndResize('watchFace.png','../radar_backgrounds_orginal/')
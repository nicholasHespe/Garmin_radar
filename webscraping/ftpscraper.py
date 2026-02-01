from ftplib import FTP
from datetime import datetime, timedelta
import time
from PIL import Image
import os
import numpy as np
import subprocess
from pathlib import Path

def DownloadFile(fn: str, local_path: str = None, ftp_conn=None) -> bool:
    """Download a file from FTP server"""
    try:
        save_path = local_path if local_path else fn
        # Use provided FTP connection or fall back to global
        ftp_to_use = ftp_conn if ftp_conn is not None else ftp
        with open(save_path, 'wb') as fp:
            ftp_to_use.retrbinary(f'RETR {fn}', fp.write)
            print(f'Downloaded {fn} -> {save_path}')
            return True
    except Exception as e:
        print(f'File "{fn}" does not exist or failed to download: {e}')
        return False

def DownloadTransparencies(radar_id: str, transparency_dir: str = 'radar_transparencies', ftp_conn=None):
    """Download background transparency layers for a radar station"""
    Path(transparency_dir).mkdir(exist_ok=True)

    layers = ['background', 'topography', 'roads']
    downloaded = {}

    # Use provided FTP connection or fall back to global
    ftp_to_use = ftp_conn if ftp_conn is not None else ftp

    print(f'Downloading transparency layers for {radar_id}...')
    ftp_to_use.cwd('/anon/gen/radar_transparencies')

    for layer in layers:
        filename = f'{radar_id}.{layer}.png'
        local_path = os.path.join(transparency_dir, filename)

        # Only download if doesn't exist (transparencies don't change often)
        if not os.path.exists(local_path):
            if DownloadFile(filename, local_path, ftp_to_use):
                downloaded[layer] = local_path
            else:
                print(f'Warning: Could not download {layer} layer')
        else:
            print(f'Using cached {filename}')
            downloaded[layer] = local_path

    ftp_to_use.cwd('/anon/gen/radar')  # Return to radar directory
    return downloaded

def CropAndResize(fn: str, path = ''):
    """Crop and resize an image to 240x240 for watch display"""
    img = Image.open(path+fn)
    border = 70 + 16
    down = 70
    img = img.crop((border, border+down, img.width - border, img.height - border+down))
    img = img.resize((240,240),Image.Resampling.LANCZOS)
    img.save(fn)

def CreateCompositeBackground(transparency_layers: dict, output_path: str = 'composite_background.png') -> str:
    """Composite background, topography, and roads into a single background image"""
    print('Creating composite background...')

    # Start with background layer
    if 'background' not in transparency_layers:
        print('Warning: No background layer, using blank background')
        composite = Image.new('RGBA', (240, 240), (0, 0, 0, 255))
    else:
        composite = Image.open(transparency_layers['background']).convert('RGBA')
        # Crop and resize background
        border = 70 + 16
        down = 70
        composite = composite.crop((border, border+down, composite.width - border, composite.height - border+down))
        composite = composite.resize((240, 240), Image.Resampling.LANCZOS)

    # Overlay topography
    if 'topography' in transparency_layers:
        topo = Image.open(transparency_layers['topography']).convert('RGBA')
        topo = topo.crop((border, border+down, topo.width - border, topo.height - border+down))
        topo = topo.resize((240, 240), Image.Resampling.LANCZOS)
        composite = Image.alpha_composite(composite, topo)

    # Overlay roads
    if 'roads' in transparency_layers:
        roads = Image.open(transparency_layers['roads']).convert('RGBA')
        roads = roads.crop((border, border+down, roads.width - border, roads.height - border+down))
        roads = roads.resize((240, 240), Image.Resampling.LANCZOS)
        composite = Image.alpha_composite(composite, roads)

    composite.save(output_path, 'PNG')
    print(f'Saved composite background to {output_path}')
    return output_path

def CompositeRadarOnBackground(radar_image_path: str, background_path: str, output_path: str):
    """Overlay radar data on top of the composite background"""
    background = Image.open(background_path).convert('RGBA')
    radar = Image.open(radar_image_path).convert('RGBA')

    # Composite radar on top of background
    final = Image.alpha_composite(background, radar)
    final.save(output_path, 'PNG')
    return output_path

def GetRecentRadarFiles(radar_id: str, count: int = 7, ftp_conn=None) -> list:
    """Find the most recent radar files on FTP server"""
    print(f'Scanning for recent {radar_id} radar files...')

    try:
        # Use provided FTP connection or fall back to global
        ftp_to_use = ftp_conn if ftp_conn is not None else ftp

        # List all files in radar directory
        files = []
        ftp_to_use.retrlines('NLST', files.append)

        # Filter for our radar ID and sort by timestamp (filename contains timestamp)
        radar_files = [f for f in files if f.startswith(f'{radar_id}.T.') and f.endswith('.png')]
        radar_files.sort(reverse=True)  # Most recent first

        # Get the requested number of most recent files
        recent_files = radar_files[:count]
        print(f'Found {len(recent_files)} recent files')

        return recent_files
    except Exception as e:
        print(f'Error listing radar files: {e}')
        return []

def InitializeImageBuffer(radar_id: str, num_images: int, composite_bg_path: str, use_radar_naming: bool = False):
    """Download most recent radar images to populate buffer on startup"""
    print(f'Initializing image buffer with {num_images} most recent images...')

    # Get most recent radar files from FTP
    recent_files = GetRecentRadarFiles(radar_id, num_images)

    if not recent_files:
        print('Warning: No radar files found on FTP server')
        return False

    # Download and process each file
    downloaded_count = 0
    for filename in reversed(recent_files):  # Oldest to newest
        if DownloadFile(filename):
            # Crop and resize
            CropAndResize(filename)

            # Composite with background if available
            if os.path.exists(composite_bg_path):
                temp_output = 'temp_radar_composite.png'
                CompositeRadarOnBackground(filename, composite_bg_path, temp_output)
                os.remove(filename)
                os.rename(temp_output, filename)

            # Add to rolling buffer
            UpdateImageNames(filename, num_images, radar_id if use_radar_naming else None)
            downloaded_count += 1
            os.remove(filename)
        else:
            print(f'Failed to download {filename}')

    print(f'Initialized buffer with {downloaded_count} images')

    # Create composite grid (only for non-radar-specific naming)
    if downloaded_count > 0 and not use_radar_naming:
        CombineImages(num_images, 3)

    return downloaded_count > 0

def GetOrCreateBackground(radar_id: str) -> str:
    """Get or create composite background for a specific radar station"""
    composite_bg_path = f'composite_background_{radar_id}.png'

    # Return if already exists
    if os.path.exists(composite_bg_path):
        print(f'Using cached background for {radar_id}')
        return composite_bg_path

    # Download transparency layers and create background
    print(f'Creating new background for {radar_id}...')
    with FTP("ftp.bom.gov.au") as ftp_conn:
        ftp_conn.login()
        transparency_layers = DownloadTransparencies(radar_id, ftp_conn=ftp_conn)
        if transparency_layers:
            CreateCompositeBackground(transparency_layers, composite_bg_path)
            return composite_bg_path
        else:
            print(f'Warning: Could not create background for {radar_id}')
            return None

def GenerateImagesForRadar(radar_id: str, num_images: int = 7) -> bool:
    """Generate radar images for a specific station on-demand"""
    print(f'Generating {num_images} images for {radar_id}...')

    # Get or create background for this radar
    composite_bg_path = GetOrCreateBackground(radar_id)
    if not composite_bg_path:
        print(f'Failed to get background for {radar_id}')
        return False

    # Connect to FTP and generate images
    try:
        with FTP("ftp.bom.gov.au") as ftp_conn:
            ftp_conn.login()
            ftp_conn.cwd("/anon/gen/radar")

            # Get most recent radar files
            recent_files = GetRecentRadarFiles(radar_id, num_images, ftp_conn)
            if not recent_files:
                print(f'No radar files found for {radar_id}')
                return False

            # Download and process each file
            downloaded_count = 0
            for idx, filename in enumerate(reversed(recent_files)):  # Oldest to newest
                if DownloadFile(filename, ftp_conn=ftp_conn):
                    # Crop and resize
                    CropAndResize(filename)

                    # Composite with background - save directly to final location
                    output_name = f'images/{radar_id}-{idx}.png'
                    CompositeRadarOnBackground(filename, composite_bg_path, output_name)
                    os.remove(filename)

                    downloaded_count += 1
                    print(f'Generated {output_name}')
                else:
                    print(f'Failed to download {filename}')

            print(f'Generated {downloaded_count}/{num_images} images for {radar_id}')
            return downloaded_count > 0

    except Exception as e:
        print(f'Error generating images for {radar_id}: {e}')
        return False

def UpdateImageNames(fn: str, num: int, radar_id: str = None):
    """Update rolling buffer of images with optional radar-specific naming"""
    new_img = Image.open(fn)
    img_list = []

    # Use radar-specific naming if provided
    name_pattern = f'images/{radar_id}-{{i}}.png' if radar_id else 'images/{i}.png'

    for i in range(num):
        img_name = name_pattern.format(i=i)
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
        img_name = name_pattern.format(i=i)
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


# Configuration
RADAR_ID = 'IDR133'  # Default radar station (can be changed based on GPS)
SYDNEY_RADAR_ID = 'IDR063'  # Pre-generate Sydney for watch app
image_count = 7
composite_bg_path = 'composite_background.png'

# Ensure images directory exists
Path('images').mkdir(exist_ok=True)

# Initialize: Download transparency layers and create composite background
print(f'Starting BetterWeather radar server for {RADAR_ID}...')
print('='*50)

with FTP("ftp.bom.gov.au") as ftp:
    ftp.login()

    # Download and create background
    print('\n[1/3] Setting up background layers...')
    transparency_layers = DownloadTransparencies(RADAR_ID)
    if transparency_layers:
        CreateCompositeBackground(transparency_layers, composite_bg_path)
    else:
        print('Warning: No transparency layers downloaded, radar will have no background')

    # Populate image buffer with most recent radar data
    print('\n[2/3] Populating image buffer...')
    ftp.cwd("/anon/gen/radar")
    InitializeImageBuffer(RADAR_ID, image_count, composite_bg_path)

# Pre-generate Sydney (IDR063) images for watch app
print('\n[3/3] Pre-generating Sydney (IDR063) images for watch app...')
sydney_images_exist = all(os.path.exists(f'images/{SYDNEY_RADAR_ID}-{i}.png') for i in range(7))
if not sydney_images_exist:
    success = GenerateImagesForRadar(SYDNEY_RADAR_ID, 7)
    if success:
        print(f'Successfully pre-generated {SYDNEY_RADAR_ID} images')
    else:
        print(f'Warning: Failed to pre-generate {SYDNEY_RADAR_ID} images')
else:
    print(f'{SYDNEY_RADAR_ID} images already exist, skipping generation')

print('='*50)
print('Initialization complete! Starting continuous updates...\n')

# Main loop: Download radar images and composite with background
while True:
    with FTP("ftp.bom.gov.au") as ftp:
        # Create filename based on 6 mins ago (BOM updates every 6-10 minutes)
        filename = (datetime.utcnow() - timedelta(minutes=6)).strftime(f'{RADAR_ID}.T.%Y%m%d%H%M.png')
        ftp.login()
        ftp.cwd("/anon/gen/radar")

        if DownloadFile(filename):
            # Crop and resize radar image
            CropAndResize(filename)

            # Composite radar on background if background exists
            if os.path.exists(composite_bg_path):
                temp_output = 'temp_radar_composite.png'
                CompositeRadarOnBackground(filename, composite_bg_path, temp_output)
                os.remove(filename)
                os.rename(temp_output, filename)

            # Update rolling buffer of images (no radar-specific naming for default station)
            UpdateImageNames(filename, image_count, None)

            # Create composite grid image
            CombineImages(image_count, 3)

            os.remove(filename)

        subprocess.call('./updateDNS.sh', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(60)

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
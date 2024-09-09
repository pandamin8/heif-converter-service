import datetime
from flask import Flask, request, jsonify
import os
import tempfile
import pyheif
from PIL import Image, ImageOps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_heif_to_jpeg():
    # Check if the POST request has the file part
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'})
    if 'path' not in request.form:
        return jsonify({'error': 'No path part'})

    file = request.files['image']
    
    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Save the HEIF file to a temporary directory
    with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as temp_heic:
        temp_heic.write(file.read())

    # Decode the HEIF file
    heif_file = pyheif.read(temp_heic.name)
    
    # Convert to JPEG
    image = Image.frombytes(
        heif_file.mode, 
        heif_file.size, 
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    
    # Create required directories if not exist
    base_dir = os.getenv('IMAGES_BASE_DIRECTORY')
    path = request.form.get('path')

    output_dir = base_dir + path

    os.makedirs(output_dir, exist_ok=True)

    imagename = f'{os.path.splitext(file.filename)[0]}'

    currentTime = datetime.datetime.now()
    timestamp = currentTime.timestamp()

    imageFileName = imagename.split('.')
    name = ''.join(imageFileName[0])
    newImageName = name + '_' + str(int(timestamp))

    # Save the JPEG file
    output_path = os.path.join(output_dir, newImageName)

    image.thumbnail((1200, 800))

    thumbnail = request.form.get('thumbnail')

    extension = '.jpeg'

    if thumbnail == 'true':
        image.save(output_path + '.webp', 'webp', optimize=True, quality=20)
        createThumbnail(image, output_dir, newImageName)
        extension = '.webp'
    else:
        image.save(output_path + '.jpeg', 'jpeg', optimize=True, quality=20)

    deleteImage(output_dir, newImageName, name)

    print('----------------------------------------------------\n\n')
    print('image converted => ' + output_path)
    print('\n\n----------------------------------------------------')

    return jsonify({'image_name': newImageName + extension})

@app.route('/compress', methods=['POST'])
def compress_images():
    # Check if the POST request has the file part
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'})
    if 'path' not in request.form:
        return jsonify({'error': 'No path part'})

    file = request.files['image']
    
    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    # Read the image data
    image = Image.open(file)
    
    # Create required directories if not exist
    base_dir = os.getenv('IMAGES_BASE_DIRECTORY')
    path = request.form.get('path')

    output_dir = base_dir + path

    os.makedirs(output_dir, exist_ok=True)

    imagename = file.filename

    currentTime = datetime.datetime.now()
    timestamp = currentTime.timestamp()

    imageFileName = imagename.split('.')
    name = ''.join(imageFileName[:-1])
    newImageName = name + '_' + str(int(timestamp))

    # Save the compressed image file
    output_path = os.path.join(output_dir, newImageName)

    image = ImageOps.exif_transpose(image)
    image.thumbnail((1200, 800))

    image = image.convert('RGB')

    thumbnail = request.form.get('thumbnail')
    
    extension = '.jpeg'

    if thumbnail == 'true':
        image.save(output_path + '.webp', 'webp', optimize=True)
        createThumbnail(image, output_dir, newImageName)
        extension = '.webp'
    else:
        image.save(output_path + '.jpeg', 'jpeg', optimize=True)

    deleteImage(output_dir, newImageName, name)

    print('----------------------------------------------------\n\n')
    print('image compressed => ' + output_path)
    print('\n\n----------------------------------------------------')

    return jsonify({'image_name': newImageName + extension})

def deleteImage(dirPath, currentImage, imagePrefix):
    files = os.listdir(dirPath)

    for file in files:
        name = file.split('.')[0]
        prefix = name.split('_')[0]
        extension = '.' + file.split('.')[-1]
        if prefix == imagePrefix and file != currentImage + extension:
            os.remove(os.path.join(dirPath, file))
            print(f"Deleted file: {file}")

def createThumbnail(image, dir, fileName):
    image100x100 = image.copy()
    image300x200 = image.copy()


    dir100x100 = dir + '/100x100/'
    dir300x200 = dir + '/300x200/'

    os.makedirs(dir100x100, exist_ok=True)
    os.makedirs(dir300x200, exist_ok=True)

    image100x100.thumbnail((150, 150))
    image300x200.thumbnail((300, 200))

    image100x100.save(dir100x100 + fileName + '.jpeg', 'jpeg', optimize=True)
    image300x200.save(dir300x200 + fileName + '.webp', 'webp', optimize=True)

    prefix = fileName.split('_')[0]
    deleteImage(dir100x100, fileName, prefix)
    deleteImage(dir300x200, fileName, prefix)
    

if __name__ == '__main__':
    from waitress import serve
    port = os.getenv('PORT')
    print('server is running on port : ' + port)
    serve(app, host="0.0.0.0", port=port)
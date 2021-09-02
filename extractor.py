import json
import os
import shutil
import tempfile
import zipfile
import pandas as pd
from PIL import Image

from job_manager import write_progress


def run_extractor(job_id, payload):
    payload_root_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(payload, 'r') as zip_ref:
        zip_ref.extractall(payload_root_dir)
    raw_images_zip_path = os.path.join(payload_root_dir, 'raw_images.zip')
    gt_csv_file_path = os.path.join(payload_root_dir, 'gt.csv')
    df = pd.read_csv(gt_csv_file_path)
    df["OCR"] = ""
    raw_images_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(raw_images_zip_path, 'r') as zip_ref:
        zip_ref.extractall(raw_images_dir)
    images = os.listdir(raw_images_dir)
    cropped_image_dir = tempfile.mkdtemp()
    write_progress(job_id, 5)
    num_of_images = len(images)
    for idx, image in enumerate(images):
        percent = round(float(float(idx) * 90.0) / float(num_of_images), 2)
        write_progress(job_id, percent)
        img_path = os.path.join(raw_images_dir, image)
        os.environ["PYTHONPATH"] = "./ultimateALPR/binaries/windows/x86_64;./ultimateALPR/python"
        cmd = 'python ./ultimateALPR/samples/python/recognizer/recognizer.py --image "' + img_path + \
              '" --assets ./ultimateALPR/assets > out.txt'
        os.system(cmd)
        with open('out.txt', 'r') as f:
            lines = f.readlines()
            json_string = lines[1][34:]
            json_obj = json.loads(json_string)
            ocr = json_obj['plates'][0]['text']
            df.at[idx, "OCR"] = ocr
            roi = json_obj['plates'][0]['warpedBox']
            im = Image.open(img_path)
            im = im.crop((roi[0], roi[1], roi[4], roi[5]))
            cropped_image_path = os.path.join(cropped_image_dir, image)
            im.save(cropped_image_path)
        os.remove('out.txt')
    shutil.make_archive(os.path.join(job_id, 'roi'), 'zip', cropped_image_dir)
    df.to_csv(os.path.join(job_id, 'gt_ocr.csv'))
    shutil.make_archive(job_id, 'zip', job_id)
    shutil.rmtree(cropped_image_dir)
    shutil.rmtree(raw_images_dir)
    shutil.rmtree(payload_root_dir)
    write_progress(job_id, 100)

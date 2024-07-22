from pytube import YouTube


from pytube.innertube import _default_clients
from pytube import cipher
import re

_default_clients["ANDROID"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["IOS"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["ANDROID_EMBED"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["IOS_EMBED"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["IOS_MUSIC"]["context"]["client"]["clientVersion"] = "6.41"
_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]



def get_throttling_function_name(js: str) -> str:
    """Extract the name of the function that computes the throttling parameter.

    :param str js:
        The contents of the base.js asset file.
    :rtype: str
    :returns:
        The name of the function used to compute the throttling parameter.
    """
    function_patterns = [
        r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&\s*'
        r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
        r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)',
    ]
    #logger.debug('Finding throttling function name')
    for pattern in function_patterns:
        regex = re.compile(pattern)
        function_match = regex.search(js)
        if function_match:
            #logger.debug("finished regex search, matched: %s", pattern)
            if len(function_match.groups()) == 1:
                return function_match.group(1)
            idx = function_match.group(2)
            if idx:
                idx = idx.strip("[]")
                array = re.search(
                    r'var {nfunc}\s*=\s*(\[.+?\]);'.format(
                        nfunc=re.escape(function_match.group(1))),
                    js
                )
                if array:
                    array = array.group(1).strip("[]").split(",")
                    array = [x.strip() for x in array]
                    return array[int(idx)]

    raise RegexMatchError(
        caller="get_throttling_function_name", pattern="multiple"
    )

cipher.get_throttling_function_name = get_throttling_function_name


import os
import cv2


import requests
import subprocess

# Set default figure size for plots
from pylab import rcParams

rcParams['figure.figsize'] = 8, 16

# Initialize the OCR reader
reader = easyocr.Reader(['en'])

def download_youtube_video(url, download_folder):
    yt = YouTube(url)
    stream = yt.streams.filter(file_extension='mp4').first()
    video_path = os.path.join(download_folder, stream.default_filename)
    stream.download(output_path=download_folder)
    return video_path

def video_to_frames_url_auto(url=None, folder='./frames'):
    if url is None:
        raise ValueError("A URL must be provided.")

    if not os.path.exists(folder):
        os.makedirs(folder)

    if 'youtube.com' in url or 'youtu.be' in url:
        video_path = download_youtube_video(url, folder)
    else:
        video_path = os.path.join(folder, 'temp_video.mp4')
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        else:
            raise ValueError(f"Failed to download video. Status code: {response.status_code}")

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError("Error opening video stream or file")

    frame_index = 0
    while True:
        ret, frame = video.read()
        if not ret:
            break

        frame_filename = os.path.join(folder, f'frame_{frame_index:04d}.jpg')
        cv2.imwrite(frame_filename, frame)
        frame_index += 1

    video.release()
    print(f"Extracted {frame_index} frames to '{folder}'")

    if 'youtube.com' not in url and 'youtu.be' not in url:
        os.remove(video_path)

def extract_text_from_images(folder_path):
    reader = easyocr.Reader(['en'])

    images = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    seen_texts = set()

    for index, image in enumerate(images):
        image_path = os.path.join(folder_path, image)
        output = reader.readtext(image_path)

        for item in output:
            if len(item) == 3:
                bbox, text, confidence = item
                if confidence > 0.9033 and text and text not in seen_texts:
                    seen_texts.add(text)
                    print(f"{text}")

def download_subtitles(video_link):
    try:
        subprocess.run(['yt-dlp', '--write-subs', '--sub-lang', 'en', '--write-auto-subs', '--skip-download', video_link], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error downloading subtitles: {e}")
        return False

def convert_subtitles_to_srt(vtt_file):
    srt_file = vtt_file.replace('.vtt', '.srt')
    try:
        subprocess.run(['ffmpeg', '-i', vtt_file, srt_file], check=True)
        return srt_file
    except subprocess.CalledProcessError as e:
        print(f"Error converting subtitles: {e}")
        return None

def extract_text_from_srt(srt_file):
    text = []
    with open(srt_file, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line and not line.isdigit() and not line.startswith('00:'):
                text.append(line)
    return '\n'.join(text)



def main():
    # YouTube video link
    video_link = 'https://youtu.be/malsYBOkuI0?si=3TiYhCerCN9kF-a4'
    output_folder = '/content/drive/MyDrive/Colab Notebooks/frames'

    # Download YouTube video and extract frames
    video_to_frames_url_auto(video_link, output_folder)

    # Download subtitles
    if not download_subtitles(video_link):
        return

    vtt_files = [f for f in os.listdir('.') if f.endswith('.vtt')]
    srv_files = [f for f in os.listdir('.') if f.endswith('.srv')]

    if not vtt_files and not srv_files:
        print("No VTT or SRV file found.")
        return

    vtt_file = vtt_files[0] if vtt_files else srv_files[0]

    # Convert subtitles to SRT
    srt_file = convert_subtitles_to_srt(vtt_file)
    if not srt_file:
        return

    # Extract text from SRT
    text = extract_text_from_srt(srt_file)
    if text:
        print("The subtitles in the video are:\n")
        print(text)
    else:
        print("Failed to extract text from subtitles.")

    # Clean up
    os.remove(vtt_file)
    os.remove(srt_file)

    # Extract text from frames using OCR
    extract_text_from_images(output_folder)

if __name__ == "__main__":
    main()

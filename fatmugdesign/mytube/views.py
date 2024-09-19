
import os
import subprocess
import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import VideoForm
import re
from .models import Video



# Configure logging
logging.basicConfig(level=logging.INFO)

def upload_video(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save()

            # Path to the uploaded video
            video_path = os.path.join(settings.MEDIA_ROOT, video.file.name)

            # Subtitle directories for different languages
            subtitle_dirs = {
                'en': os.path.join(settings.MEDIA_ROOT, 'subtitles'),
                'fr': os.path.join(settings.MEDIA_ROOT, 'subtitles2'),
                'es': os.path.join(settings.MEDIA_ROOT, 'subtitles1'),
                'hi': os.path.join(settings.MEDIA_ROOT, 'subtitles3'),
            }

            # Create subtitle directories if they do not exist
            for dir_path in subtitle_dirs.values():
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)

            # Extract subtitles for each language (English, French, Spanish)
            languages = ['en', 'fr', 'es','hi']
            for index, lang in enumerate(languages):
                subtitle_file_name = os.path.splitext(os.path.basename(video.file.name))[0] + f"_{lang}.srt"
                subtitle_path = os.path.join(subtitle_dirs[lang], subtitle_file_name)

                # FFmpeg command to extract the subtitles for the respective language
                command = ['ffmpeg', '-y', '-i', video_path, '-map', f'0:s:{index}', subtitle_path]

                try:
                    logging.info(f"Running command: {' '.join(command)}")
                    subprocess.run(command, check=True)

                    # Convert the extracted SRT file to VTT
                    vtt_path = convert_srt_to_vtt(subtitle_path)

                    # Save the VTT file path in the Video model for respective language
                    if lang == 'en':
                        video.subtitle_file = os.path.join('subtitles', os.path.basename(vtt_path))
                    elif lang == 'fr':
                        video.subtitle_file_fr = os.path.join('subtitles2', os.path.basename(vtt_path))
                    elif lang == 'es':
                        video.subtitle_file_es = os.path.join('subtitles1', os.path.basename(vtt_path))
                    elif lang == 'hi':
                        video.subtitle_file_es = os.path.join('subtitles3', os.path.basename(vtt_path))

                    video.save()

                except subprocess.CalledProcessError as e:
                    logging.error(f"Error extracting subtitles for {lang}: {e}")

            return redirect('video_list')
    else:
        form = VideoForm()
    return render(request, 'index.html', {'form': form})

def video_list(request):
    videos = Video.objects.all()
    return render(request, 'index.html', {'videos': videos})


def delete_video(request, pk):
    video = get_object_or_404(Video, pk=pk)

    if request.method == 'POST':
        # Convert FieldFile to a string to get the path for the video file
        video_path = os.path.join(settings.MEDIA_ROOT, str(video.file))

        # Delete the video file
        if os.path.exists(video_path):
            os.remove(video_path)

        # Define all subtitle paths (SRT and VTT) and delete them if they exist
        subtitle_paths = [
            str(video.subtitle_file),     # English subtitles
            str(video.subtitle_file_fr),  # French subtitles
            str(video.subtitle_file_es),  # Spanish subtitles
            str(video.subtitle_file_hi),  # Hindi subtitles (if added)
        ]

        for subtitle_file in subtitle_paths:
            if subtitle_file:
                # Delete both .srt and .vtt formats
                srt_path = os.path.join(settings.MEDIA_ROOT, subtitle_file.replace(".vtt", ".srt"))
                vtt_path = os.path.join(settings.MEDIA_ROOT, subtitle_file)

                if os.path.exists(srt_path):
                    os.remove(srt_path)

                if os.path.exists(vtt_path):
                    os.remove(vtt_path)

        # Delete the video record from the database
        video.delete()

        return redirect('video_list')

    return render(request, 'index.html', {'video': video})


# Helper function to convert SRT to VTT
def convert_srt_to_vtt(srt_path):
    vtt_path = os.path.splitext(srt_path)[0] + ".vtt"
    try:
        with open(srt_path, 'r', encoding='utf-8') as srt_file, open(vtt_path, 'w', encoding='utf-8') as vtt_file:
            vtt_file.write("WEBVTT\n\n")
            for line in srt_file:
                vtt_file.write(line.replace(',', '.'))  # Adjust timecode format
    except UnicodeDecodeError:
        logging.error(f"Encoding error reading file: {srt_path}")
    return vtt_path


def search_subtitles(request):
    query = request.GET.get('q', '').strip().lower()
    if not query:
        return JsonResponse({'results': []})

    results = []
    videos = Video.objects.all()

    for video in videos:
        subtitle_files = [video.subtitle_file, video.subtitle_file_fr, video.subtitle_file_es, video.subtitle_file_hi]

        for subtitle_file in subtitle_files:
            if subtitle_file:
                subtitle_path = os.path.join(settings.MEDIA_ROOT, str(subtitle_file))
                try:
                    with open(subtitle_path, 'r', encoding='utf-8') as file:
                        content = file.read().lower()
                        matches = re.finditer(re.escape(query), content)
                        for match in matches:
                            timestamp = extract_timestamp_from_content(content, match.start())
                            results.append({
                                'video': {
                                    'title': video.title,
                                    'url': video.file.url,
                                },
                                'phrase': query,
                                'timestamp': timestamp,
                                'subtitle_file': subtitle_file.url
                            })
                except FileNotFoundError:
                    continue

    return JsonResponse({'results': results})


def extract_timestamp_from_content(content, start_position):
    # Extract timestamp from content based on position
    lines = content.split('\n')
    for line in lines:
        if '-->' in line:
            timestamp = line.split(' --> ')[0]
            return timestamp
    return '00:00:00.000'



def video_detail(request, pk):
    video = get_object_or_404(Video, pk=pk)
    data = {
        'title': video.title,
        'file': video.file.url,
        'subtitle_files': [
            {'url': video.subtitle_file.url, 'language': 'en', 'label': 'English'} if video.subtitle_file else None,
            {'url': video.subtitle_file_fr.url, 'language': 'fr',
             'label': 'French'} if video.subtitle_file_fr else None,
            {'url': video.subtitle_file_es.url, 'language': 'es',
             'label': 'Spanish'} if video.subtitle_file_es else None,
            {'url': video.subtitle_file_hi.url, 'language': 'hi', 'label': 'Hindi'} if video.subtitle_file_hi else None
        ]
    }
    # Filter out None values
    data['subtitle_files'] = [item for item in data['subtitle_files'] if item]

    return JsonResponse(data)



def list_view(request):
    new= Video.objects.all()
    return render(request, 'listview.html', {'new': new})

def video_player(request, id):
    video = get_object_or_404(Video, pk=id)
    return render(request, 'player.html', {'video': video})


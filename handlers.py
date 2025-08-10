import gradio as gr
import os
import glob
import cv2
import yt_dlp
import shutil
import json
from vector_store import vector_store
from helpers import parse_youtube_link
from keyframe_extractor import extract_keyframes_from_youtube
from configs import MAX_RESULTS

def handle_query(query, k=5):
  metadata = []
  results = vector_store.similarity_search_with_score(query, k=k)
  for rs in results:
    doc, score = rs
    yt_link, start_time, end_time = parse_youtube_link(doc.metadata["video_id"])
    data = {
        "doc": doc,
        "score": score,
        "yt_link": yt_link,
        "start_time": start_time,
        "end_time": end_time
    }
    metadata.append(data)
  return metadata

def handle_query_for_table(query, k=5):
    metadata = handle_query(query, k)
    table_data = []
    for r in metadata:
        table_data.append([
            r["yt_link"],
            r["start_time"],
            r["end_time"],
            round(float(r["score"]), 5)
        ])
    return table_data, metadata

def handle_fetch_keyframes(metadatas, frames, save_to, progress=gr.Progress()):
    all_logs = []
    video_to_files = {}
    total_videos = len(metadatas)
    
    global stop_flag
    stop_flag = False

    for i, m in enumerate(metadatas):
        if stop_flag: break
        video_id = m["doc"].metadata["video_id"]
        # Update progress bar
        progress((i+1) / total_videos, desc=f"Extracting keyframes {video_id} ({i + 1}/{total_videos})")
        
        sub_folder = os.path.join(save_to, video_id)
        success, keyframe_files, output_log = extract_keyframes_from_youtube(
            youtube_url=m["yt_link"],
            start_time=float(m["start_time"]), 
            end_time=float(m["end_time"]), 
            frames=int(frames),
            save_to=sub_folder
        )
        video_to_files[video_id] = keyframe_files
        all_logs.append(f"--- Logs for {m['yt_link']} ({video_id}) ---\n{output_log}")
    return video_to_files, all_logs

def serialize_metadata(metadata, video_to_files):
    serialized = []
    for item in metadata:
        doc = item.get("doc")
        score = item.get("score")
        video_id = doc.metadata.get("video_id") if doc else None
        serialized.append({
            "id": doc.id if doc else None,
            "metadata": doc.metadata if doc else None,
            "page_content": doc.page_content if doc else None,
            "score": float(score) if score is not None else None,
            "keyframes": video_to_files.get(video_id, [])
        })
    return json.dumps(serialized, indent=2)

def extract_and_display(metadata, save_to, frames_per_vid):
    shutil.rmtree(save_to) if os.path.exists(save_to) else None
    if not metadata:
        return ["No metadata available."]
    video_to_files, all_logs = handle_fetch_keyframes(metadata, frames_per_vid, save_to)
    return serialize_metadata(metadata, video_to_files), "\n\n".join(all_logs)

def generate_gallery(directory, frames):
  sub_folders = [f.path for f in os.scandir(directory) if f.is_dir()]
  galleries = []
  for folder in sub_folders:
    images = sorted(glob.glob(os.path.join(folder, "*.jpg")))
    label = f"{len(images)} keyframes: {os.path.basename(folder)}"
    if not images: continue
    gallery = gr.Gallery(images, label=label, columns=frames, height=150, visible=True, allow_preview=False)
    galleries.append(gallery)
  galleries += [gr.Gallery(visible=False) for _ in range(len(galleries), MAX_RESULTS)]
  return galleries

def clear():
  galleries = [gr.Gallery(visible=False)]*MAX_RESULTS
  code = None
  return *galleries, code

def set_stop_flag():
    global stop_flag
    stop_flag = True
    gr.Warning('Canceling....', 1.5)
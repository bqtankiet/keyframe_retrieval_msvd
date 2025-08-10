import yt_dlp
import cv2
import os

def extract_keyframes_from_youtube(youtube_url, start_time, end_time, interval=0.0, frames=None, save_to="keyframes"):
    """
    Extract keyframes from a YouTube video within a specific time range.

    Args:
        youtube_url (str): URL of the YouTube video.
        start_time (float): Start time in seconds.
        end_time (float): End time in seconds.
        interval (float): Time interval between keyframes in seconds (default: 0.0s).
        frames (int): Number of keyframes to extract (default: None).
        save_to (str): Directory to save keyframes (default: 'keyframes').

    Returns:
        tuple: (success_flag, keyframe_files, output_log)
    """
    global stop_flag
    stop_flag = False

    output_log = []
    def log(msg):
        print(msg)
        output_log.append(msg)

    # Validate input
    if start_time < 0 or end_time < 0:
        log("[ERROR] - Timestamps cannot be negative.")
        return False, [], "\n".join(output_log)
    if start_time > end_time:
        log("[ERROR] - Start time must be less than or equal to end time.")
        return False, [], "\n".join(output_log)
    if interval < 0:
        log("[ERROR] - Interval time must be greater than or equals 0.")
        return False, [], "\n".join(output_log)
    if frames is not None and frames <= 0:
        log("[ERROR] - Number of frames must be greater than 0.")
        return False, [], "\n".join(output_log)
    if interval == 0 and frames is None:
        log("[INFO] - interval = 0 and frames not specified. Extract only 1 keyframe.")
        end_time = start_time
        interval = 1
        frames = 1
    elif start_time == end_time:
        log("[INFO] - start_time == end_time. Extract only 1 keyframe.")
        end_time = start_time
        interval = 1
        frames = 1

    # Determine extraction mode: frames or interval
    use_frames = frames is not None
    if use_frames:
        log(f"[INFO] - Extracting {frames} keyframes.")
    else:
        log(f"[INFO] - Extracting keyframes with interval {interval}s.")

    # Create save directory if it doesn't exist
    if save_to:
        # shutil.rmtree(save_to) if os.path.exists(save_to) else None
        os.makedirs(save_to, exist_ok=True)

    ydl_opts = {
        'format': 'best[ext=mp4]',
        'noplaylist': True,
        'quiet': False,
        'simulate': True,
        'forceurl': True,
    }

    try:
        if stop_flag:
          log("[WARNING] - Process stopped by user")
          return False, [], "\n".join(output_log)

        # Get video URL and metadata
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            video_url = info_dict.get('url')
            video_duration = info_dict.get('duration', 0)

        if not video_url:
            log("[ERROR] - Could not get video stream URL.")
            return False, [], "\n".join(output_log)

        if video_duration and end_time > video_duration:
            log(f"[ERROR] - End time {end_time}s exceeds video duration {video_duration}s.")
            return False, [], "\n".join(output_log)

        # Open video stream
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            log("[ERROR] - Could not open video stream.")
            return False, [], "\n".join(output_log)

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        log(f"[INFO] - Video FPS: {fps}, Total Frames: {frame_count}, Duration: {video_duration}s")

        # Calculate frame range
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)

        # Calculate interval or frame positions
        if use_frames:
            if frames == 1:
                time_points = [start_time]
            else:
                interval = (end_time - start_time) / (frames - 1) if frames > 1 else (end_time - start_time)
                time_points = [start_time + i * interval for i in range(frames)]
        else:
            frame_interval = max(1, int(interval * fps))
            time_points = []
            current_time = start_time
            while current_time <= end_time:
                time_points.append(current_time)
                current_time += interval

        # # Attempt 1: Direct seeking
        # log(f"[INFO] - Attempting direct seek for keyframes from {start_time}s to {end_time}s...")
        # keyframe_files = []
        # for current_time in time_points:
        #     if stop_flag:
        #         log("[WARNING] - Process stopped by user")
        #         break
        #     log(f"[INFO] - Seeking to {current_time:.2f} seconds...")
        #     cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        #     ret, frame = cap.read()
        #     if ret:
        #         output_file = os.path.join(save_to, f"keyframe_{current_time:.2f}s.jpg")
        #         cv2.imwrite(output_file, frame)
        #         keyframe_files.append(output_file)
        #         log(f"[INFO] - Saved keyframe at {current_time:.2f} seconds as {output_file}")
        #     else:
        #         log(f"[WARNING] - Failed to extract frame at {current_time:.2f} seconds.")
        #         break

        # if ret:
        #     cap.release()
        #     cv2.destroyAllWindows()
        #     return True, keyframe_files, "\n".join(output_log)

        # log("[INFO] - Direct seek failed. Attempting sequential frame reading...")

        # Attempt 2: Sequential frame reading
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        current_frame = 0
        current_time = 0.0
        saved_frames = set()
        target_frames = [int(t * fps) for t in time_points]
        target_frames_set = set(target_frames)
        keyframe_files = []
        while current_frame <= end_frame:
            if stop_flag:
                log("[WARNING] - Process stopped by user")
                break
            ret, frame = cap.read()
            if not ret:
                log(f"[ERROR] - Could not read frame at position {current_frame}.")
                break
            current_time = current_frame / fps
            if current_frame in target_frames_set and current_time not in saved_frames:
                output_file = os.path.join(save_to, f"keyframe_{current_time:.2f}s.jpg")
                cv2.imwrite(output_file, frame)
                keyframe_files.append(output_file)
                log(f"[INFO] - Saved keyframe at {current_time:.2f} seconds as {output_file}")
                saved_frames.add(current_time)
            current_frame += 1

        if current_frame < start_frame:
            log(f"[ERROR] - Could not reach start frame {start_frame} (stopped at {current_frame}).")

        cap.release()
        cv2.destroyAllWindows()
        return current_frame > start_frame, keyframe_files, "\n".join(output_log)

    except Exception as e:
        log(f"[ERROR] - An unexpected error occurred: {str(e)}")
        return False, [], "\n".join(output_log)

def generate_youtube_link(video_id, start=0):
  return f"https://www.youtube.com/watch?v={video_id}&t={start}s"

def parse_youtube_link(video_id):
  """
  Args:
    video_id: format: id_start_end, eg. WTf5EgVY5uU_98_104
  """
  id_part, start_time, end_time = video_id.rsplit("_", 2)
  return generate_youtube_link(id_part, start_time), start_time, end_time
import gradio as gr
from configs import MAX_RESULTS
from handlers import (
    set_stop_flag,
    generate_gallery,
    extract_and_display,
    handle_query_for_table,
    clear,
)

# Gradio
with gr.Blocks(title="MSVD Keyframe Extractor") as app:
  gr.Markdown("<h1 style='text-align: center;'>MSVD Keyframe Extractor</h1>")
  gr.Markdown("<p style='text-align: center;'>Simple demo Keyframe Extractor with MSVD dataset.</p>")
  gr.Markdown("---")

  metadata_state = gr.State([])

  # Query input --------------------------------------------------------------------
  with gr.Column():
    query = gr.Textbox(
        label="Query",
        placeholder="Enter a query",
        value="A woman is breaking an egg"
    )
    
    # Configuration inputs ----------------------------------------------------------
    with gr.Row():
      k = gr.Slider(label="K (Number of results", minimum=1, maximum=MAX_RESULTS, value=5, step=1)
      frames_per_vid = gr.Slider(label="Frames per video", minimum=1, maximum=100, value=10, step=1)
      save_to = gr.Textbox(label="Save to", placeholder="Folder name", value="keyframes")

  # Query button --------------------------------------------------------------------
  with gr.Row():
    query_button = gr.Button("Query", variant="primary")
    cancel_button = gr.Button("Cancel", variant="stop")

  # Query results -------------------------------------------------------------------
  gr.Markdown("### Query results")
  # Tab 1: Dataframe
  with gr.Tab("Table"):
    query_result = gr.Dataframe(
      headers=["YouTube Link", "Start", "End", "Score"],
      type="array",
      wrap=True,
      show_label=True
    )

  # Tab 2: Keyframe
  with gr.Tab("Keyframes"):
    galleries = []
    for i in range(0, MAX_RESULTS):
      gallery = gr.Gallery(visible=False)
      galleries.append(gallery)

  # Tab 3: JSON
  with gr.Tab("JSON"):
    code = gr.Code(label="Results", language="javascript", interactive=False, max_lines=50)

  # Logs ----------------------------------------------------------------------------
  gr.Markdown("### Logs")
  logs_text = gr.Textbox(label="Extraction Logs", lines=10, interactive=False)

  # Handle button event
  query_button.click(
      fn=clear,
      inputs=[],
      outputs=[*galleries, code]
  ).then(
      fn=handle_query_for_table,
      inputs=[query, k],
      outputs=[query_result, metadata_state]
  ).then(
      fn=extract_and_display,
      inputs=[metadata_state, save_to, frames_per_vid],
      outputs=[code, logs_text]
  ).then(
      fn=generate_gallery,
      inputs=[save_to, frames_per_vid],
      outputs=galleries
  )

  cancel_button.click(
    fn=set_stop_flag,
    inputs=[],
    outputs=[]
  )

# Launch
app.launch(debug=True, share=True)
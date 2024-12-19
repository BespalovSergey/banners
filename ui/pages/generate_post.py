import os
import sys
from threading import Thread
from queue import Queue

from motleycrew.common.logging import logger, configure_logging
from dotenv import load_dotenv

sys.path.append(os.path.abspath("."))

import streamlit as st
import time
from threading import Event

from tools.generate_post_tools.generate_post_mixins import TEXT_GENERATION_REMARKS_WIDGET_KEY
from tools.generate_post_tools.text_generation_tool import PostTextGeneratorTool
from viewers import StreamLitItemQueueViewer, StreamLitItemView, streamlit_queue_render
from ui.ui_utils import navigation_menu, find_remarks, stop_other_generators


configure_logging(verbose=True)
load_dotenv()

# init sidebar width
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"]{
    min-width: 25%;
    max-width: 25%;
    }
    """,
    unsafe_allow_html=True,
)


def run_generate(postTextGenerator: PostTextGeneratorTool, render_queue: Queue, prompt: str):
    try:
        postTextGenerator.text_generator.set_prompt(prompt)
        postTextGenerator.invoke(prompt)
    except Exception as e:
        view_data = {"subheader": ("Error:",), "code": (str(e),)}
        render_queue.put(StreamLitItemView(view_data))

def main():
    navigation_menu()
    
    generator_key = PostTextGeneratorTool.ui_state_name
    stop_other_generators(generator_key)
    
    st.header("Generate post")
    generator = st.session_state.get(generator_key)

    # prompt_label = "Prompt"
    prompt_label = "Промпт для генерации"
    # title_of_post_label = "Title for post"
    title_of_post_label = "Заголовок для поста"
    # tone_of_voice_label = "Tone of voice"
    tone_of_voice_label = "В каком тоне написать пост"
    # max_review_iterations_label = "Output handler iterations"
    max_review_iterations_label = "Максимальное количество попыток на перегенерацию"
    

    with st.sidebar.form("form"):
        tone_of_voice = st.selectbox(
            tone_of_voice_label,
            options=["Нейтральном", "Возвышенном", "Панибратском"],
            index=0
        )
        title_of_post = st.text_area(title_of_post_label, "", height=100)
        prompt = st.text_area(prompt_label, "Введите текст для генерации поста.")
        max_review_iterations = st.number_input(max_review_iterations_label, 1, 100, 5)

        col1, col2 = st.columns((0.4, 0.6))
        with col1:
            submitted = st.form_submit_button("Submit")
        with col2:
            clear_submitted = st.form_submit_button("Clear results")

    if clear_submitted:
        if generator is not None:
            generator.stop()
            generator = None
            st.session_state[generator_key] = generator
        return

    if submitted:
        if generator is not None:
            generator.stop()
            generator = None
            st.session_state[generator_key] = generator
        
        # check fields:
        is_valid_fields = True
        for text, label in (
            (title_of_post, title_of_post_label),
            (prompt, prompt_label),
        ):
            if not text:
                st.text("{} field required".format(label))
                is_valid_fields = False

        if not is_valid_fields:
            return

        prompt_text = f"""Текст для поста ресторана в {tone_of_voice.lower()} тоне 
                                                    с названием '{title_of_post}' 
                                                    согласно поставленной задаче: {prompt}"""

        generator = PostTextGeneratorTool(
            max_remarks_iterations=max_review_iterations
        )
        
        st.session_state[generator_key] = generator
        t = Thread(target=run_generate, args=(generator, generator.render_queue, prompt_text))
        st.session_state['current_thread'] = t
        t.start()
        
    elif generator is not None:
        viewer = StreamLitItemQueueViewer(generator.render_queue)
        history = generator.get_history()
        for view_item in history:
            viewer.view(view_item, to_history=False)

        remarks, widget_key = find_remarks(TEXT_GENERATION_REMARKS_WIDGET_KEY)
        if remarks:
            generator.put_remarks(remarks)
            if widget_key:
                st.session_state[widget_key] = None
        else:
            generator.put_remarks(None)
        
        generator.finish_event.wait()
        
        main_thread = st.session_state.get('current_thread')
        if main_thread is not None:
            while main_thread.is_alive():
                time.sleep(0.5)
            st.session_state['current_thread'] = None
            
        new_prompt = generator.get_new_prompt_with_remarks()  
        
        if new_prompt != "":
            t = Thread(target=run_generate, args=(generator, generator.render_queue, new_prompt))
            st.session_state['current_thread'] = t
            t.start()
        else:
            generator.stop()
            
            
    if generator:        
        streamlit_queue_render(generator.render_queue)

main()

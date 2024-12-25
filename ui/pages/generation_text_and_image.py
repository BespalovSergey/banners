import os
import sys

from motleycrew.common.logging import logger, configure_logging
from dotenv import load_dotenv

sys.path.append(os.path.abspath("."))

import streamlit as st
from threading import Event

from tools.generate_post_tools.generate_post_mixins import TEXT_GENERATION_REMARKS_WIDGET_KEY
from tools.generate_post_tools.text_generation_tool import PostTextGeneratorTool
from viewers import  streamlit_queue_render
from ui.ui_utils import navigation_menu


from ui.worker import Worker

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


def main():
    navigation_menu()
    
    worker_key = Worker.ui_state_name
    
    if 'stop_generate_text' not in st.session_state:
        st.session_state.stop_generate_text = Event()
    
    st.header("Generate post + image correction")
    generator = st.session_state.get(PostTextGeneratorTool.ui_state_name)
    worker = st.session_state.get(worker_key)
    painter = st.session_state.get("painter")

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
        # prompt = st.text_area(prompt_label, "Введите текст для генерации поста.")
        prompt = st.text_area(prompt_label, "")
        max_review_iterations = st.number_input(max_review_iterations_label, 1, 100, 5)

        col1, col2 = st.columns((0.4, 0.6))
        with col1:
            submitted = st.form_submit_button("Submit")
        with col2:
            clear_submitted = st.form_submit_button("Clear results")

    if clear_submitted:
        if worker is not None:
            worker.stop()
            worker = None
            st.session_state[worker_key] = worker
            generator = None
            st.session_state[PostTextGeneratorTool.ui_state_name] = worker
            painter = None
            st.session_state["painter"] = painter
            if 'stop_generate_text' in st.session_state:
                del st.session_state.stop_generate_text
        return

    if submitted:
        if worker is not None:
            worker.stop()
            worker = None
            st.session_state[worker_key] = worker
            generator = None
            st.session_state[PostTextGeneratorTool.ui_state_name] = worker
            painter = None
            st.session_state["painter"] = painter
            if 'stop_generate_text' in st.session_state:
                del st.session_state.stop_generate_text
        
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
        
        worker = Worker(
            max_remarks_iterations=max_review_iterations,
            genetation_text_prompt=prompt_text
        )
        
        st.session_state[worker_key] = worker
        worker.run_post_text_generator()
        
    elif worker is not None:
        worker.reset_view()
        worker.get_previous_history()
        
        if not st.session_state.stop_generate_text.is_set():
            worker.get_remarks()
            worker.continue_generation()
    
    
    if (generator is not None) and (painter is None) and (generator.remarks_completed_event.is_set() or (generator.remarks_iterations == generator.max_remarks_iterations)):
            
        worker._render_queue.put(None)
        streamlit_queue_render(worker.render_queue)
        
        if not st.session_state.stop_generate_text.is_set():
            if not generator.remarks_completed_event.is_set():
                with st.spinner("Generation text ..."): 
                    generator.remarks_completed_event.wait()
            
            worker._render_queue.put(None)
            streamlit_queue_render(worker.render_queue)
            
            st.session_state.stop_generate_text.set()
        
            worker.init_image_genarator()
                
        elif st.session_state.stop_generate_text.is_set():
            worker.init_image_genarator()
            worker.run_image_genarator()
        
    if worker:
        streamlit_queue_render(worker.render_queue)

main()

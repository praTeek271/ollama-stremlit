import ollama
import streamlit as st
from openai import OpenAI
from utilities.icon import page_icon
from PyPDF2 import PdfReader

# Function to extract text from PDF files
def extract_text_from_pdf(file):
    text = ''
    try:
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    except Exception as e:
        text = f"Error reading PDF file: {e}"
    return text

# Function to extract text from TXT files
def extract_text_from_txtpypdf(file, data=""):
    if data:
        return data.replace('\n', " ")
    try:
        with open(file, 'r') as textfile:
            content = textfile.readlines()
        return "".join(content).replace('\n', " ")
    except Exception as e:
        return f"Error reading TXT file: {e}"

# Function to determine the file type and extract content
def extraction(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(uploaded_file)
    elif ext == "txt":
        return extract_text_from_txtpypdf(uploaded_file, data=uploaded_file.read().decode("utf-8"))
    else:
        return "Unsupported file format."

# Streamlit page configuration
st.set_page_config(
    page_title="Chat Playground",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

def extract_model_names(models_info: list) -> tuple:
    return tuple(model["model"] for model in models_info["models"])

def main():
    page_icon("💬")
    st.subheader("Ollama Playground", divider="red", anchor=False)

    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    models_info = ollama.list()
    available_models = extract_model_names(models_info)

    if available_models:
        selected_model = st.selectbox(
            "Pick a model available locally on your system ↓", available_models
        )
    else:
        st.warning("You have not pulled any model from Ollama yet!", icon="⚠️")
        if st.button("Go to settings to download a model"):
            st.page_switch("pages/03_⚙️_Settings.py")

    message_container = st.container()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        avatar = "🤖" if message["role"] == "assistant" else "😎"
        with message_container.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    file_meta_data = {}
    chat_input_container = st.container()
    with chat_input_container:
        row1 = st.container()
        row2 = st.container()
        
        with row1:
            uploaded_file = st.file_uploader("Upload File", type=["txt", "pdf"], label_visibility="collapsed")
        
        with row2:
            prompt = st.chat_input("Enter a prompt here...")

#         uploaded_file = None
    
#         if file_button_pressed:
#             uploaded_file = st.file_uploader("", type=["txt", "pdf"], label_visibility="visible")
# #---------------------------------#
        if uploaded_file:
            file_content = extraction(uploaded_file)
            file_meta_data["filename"] = uploaded_file.name
            file_meta_data["contents"] = file_content
            st.text_area("File Content", file_content, height=100,label_visibility="hidden",max_chars=500)

            if prompt and file_meta_data["filename"]:
                prompt_template = f"""
                here is the contents of the file named {file_meta_data['filename']},
                \n\nAnd here is the text data that you have to analyse:\n
                {file_meta_data['contents']}\n
                now use the file contents and answer the below question:\n{prompt}?
                """


                print("-----------------------> filename", file_meta_data["filename"])
                print("----------------------------> contents", "\n".join(file_meta_data["contents"].split("\n")[:5]))


                try:
                    st.session_state.messages.append(
                        {"role": "user", "content": prompt_template}
                    )

                    with message_container.chat_message("assistant", avatar="🤖"):
                        
                        with st.spinner("Uploading and analyzing the file with the question..."):
                            stream = client.chat.completions.create(
                                model=selected_model,
                                messages=[
                                    {"role": m["role"], "content": m["content"]}
                                    for m in st.session_state.messages
                                ],
                                stream=True,
                            )
                        response = st.write_stream(stream)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )

                except Exception as e:
                    st.error(e, icon="⛔️")

    if prompt:
        if len(file_meta_data)>0:
            prompt_template=f"""
                            answer the below question:\n
                            {prompt}
                            only from the uploaded file from above.
                            """
        else:
            prompt_template = f"""
            {prompt} , answer this question, in a brief and concise manner.
            """
        try:
            st.session_state.messages.append(
                {"role": "user", "content": prompt_template}
            )

            message_container.chat_message("user", avatar="😎").markdown(prompt)

            with message_container.chat_message("assistant", avatar="🤖"):
                with st.spinner("model working..."):
                    stream = client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )
                response = st.write_stream(stream)
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )

        except Exception as e:
            st.error(e, icon="⛔️")

if __name__ == "__main__":
    main()

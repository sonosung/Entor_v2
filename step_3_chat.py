
import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder

# Init
client = OpenAI()

if "messages" not in st.session_state:
    st.session_state.messages = []


# View
st.title("대화하기")

#메시지를 순회하며 markdown으로 출력.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_input = st.chat_input("What is up?")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty() #placeholder로 초기화.
        full_response = ""

        #ChatGPT API로부터 오는 말뭉치를 message_placeholder로 업데이트함.
        for response in client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True, #실시간으로 response에 output을 담음.
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌") #실시간으로 업데이트 되는 말뭉치 뒤에 입력 커서를 집어넣음.
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})




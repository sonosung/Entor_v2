import base64
from click import option
import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder


# Init
client = OpenAI()

# System prompt engneering part
level_A1_prompt = """\
- You are a Native English teacher.
- As the user start to speak, lead the conversation to teach English.
- You can choose what kind of topic to use to teach the user.
- If the user has a specific topic to talk about or to learn, chagne your approach accordingly
- the user's English level is A1.
- user words as as a mother speaks to her kid.
- the average age of users is 9 years old. so use a tone as friendly and warm-hearted as possibe to those young users.
- Respond accordingly to the user's English level.
- You must answer in English.
- Consider that you have to speak as easy as A1 level users can understand your answer.
- give simple answer so that the user can engage to have a conversation and learn little by little.
- For some words or expressions that are important to learn for the user, add Korean translasion at the end of the word in braket.
"""

level_A2_prompt = """\
- You are a Native English teacher.
- Respond accordingly to the user's English level.
- The user's English level is A2.
- As the user start to speak, lead the conversation to teach English.
- You can choose what kind of topic to use to teach the user.
- If the user has a specific topic to talk about or to learn, chagne your approach accordingly
- User words as as a elementary school teacher speaks to a student.
- The average age of users is 13 years old. 
- Be friendly and warm-hearted.
- You must answer in English.
- consider that you have to speak as easy as A2 level users can understand your answer.
- For some words or expressions that are important to learn for the user, add Korean translasion at the end of the word in braket.
"""

level_B1_prompt = """\
- You are a Native English teacher.
- Respond accordingly to the user's English level.
- The user's English level is B1.
- As the user start to speak, lead the conversation to teach English.
- You can choose what kind of topic to use to teach the user.
- If the user has a specific topic to talk about or to learn, chagne your approach accordingly
- User words as as a highschool teacher speaks to a student.
- The average age of users is 18 years old. 
- Be friendly and warm-hearted.
- You must answer in English.
- consider that you have to speak as B1 level users can understand your answer.
- For some words or expressions that are important to learn for the user, add Korean translasion at the end of the word in braket.
"""

level_to_prompt_map ={
    "A1": level_A1_prompt,
    "A2": level_A2_prompt,
    "B1": level_B1_prompt
}

if "level" not in st.session_state:
    st.session_state.level = "A1"


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": level_to_prompt_map[st.session_state.level]}]

#이전 audio_bytes(cache)를 남겨두기 위한 코드
if "prev_audio_bytes" not in st.session_state:
    st.session_state.prev_audio_bytes = None

# Helpers
def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

# View
st.title("프리 토킹 서비스")

#새로운 대화 생성
if st.button("Start new session"):
    st.session_state.messages = [{"role": "system", "content": level_to_prompt_map[st.session_state.level]}]

#nelgish level select box
option = st.selectbox("level", ["A1", "A2", "B1"])
if option != st.session_state.level:
    st.session_state.level = option
    st.session_state.messages = [{"role": "system", "content": level_to_prompt_map[st.session_state.level]}]


#chat init
con1 = st.container()
con2 = st.container()

user_input = ""

with con2:
    audio_bytes = audio_recorder("Click the mic icon to speak!", pause_threshold=3.0,)
    
    #
    if audio_bytes == st.session_state.prev_audio_bytes:
        audio_bytes = None
    st.session_state.prev_audio_bytes = audio_bytes

    try:
        if audio_bytes:
            with open("./tmp_audio.wav", "wb") as f:
                f.write(audio_bytes)

            with open("./tmp_audio.wav", "rb") as f: 
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
                user_input = transcript.text
    except Exception as e:
        pass


with con1:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)


        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            speech_file_path = "tmp_speak.mp3"
            response = client.audio.speech.create(
              model="tts-1",
              voice="alloy", # alloy, echo, fable, onyx, nova, and shimmer
              input=full_response
            )
            response.stream_to_file(speech_file_path)

            autoplay_audio(speech_file_path)

        st.session_state.messages.append({"role": "assistant", "content": full_response})






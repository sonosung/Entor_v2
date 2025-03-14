import streamlit as st

st.title("Echo Bot")

# Initialize chat history
#초기화 영역.
#session_state은 화면이 업데이트 되도, 기존 정보를 기록하여 유지함.
if "messages" not in st.session_state:  #1. session_state에 어떤 값이 존재하는지 확인. 없는경우,
    st.session_state.messages = []      #session_state.messages를 List로 초기화한다.List 말고 다른 함수를 넣을 수도 있음.

# Display chat messages from history on app rerun #화면에 보이게 해주는 영역.
#OpenAI 의 message 형태와 동일하게 만듦.
for message in st.session_state.messages:
    with st.chat_message(message["role"]): #{"role": "assistant", "content": "hello"}
        st.markdown(message["content"])

# React to user input
# prompt = st.chat_input("What is up?"):
# prompt :
#를 하나로 합치면
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = f"Echo: {prompt}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
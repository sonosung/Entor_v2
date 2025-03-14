from typing import List
import random
import io
import base64
import time
import pandas as pd
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import os
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import StrOutputParser, AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from fastapi import FastAPI

#FastAPI호출
app = FastAPI()

# Set page configuration for wide layout
st.set_page_config(layout="wide")

if "curr_page" not in st.session_state:
    st.session_state["curr_page"] = "home"
    st.session_state["curr_topic"] = "home"

if "prev_audio_bytes" not in st.session_state:
    st.session_state.prev_audio_bytes = None

if "exam_context" not in st.session_state:
    st.session_state.exam_context = {}

#개별로 설정한 API키 불러오기.
api_key = os.getenv("OPENAI_API_KEY2")

if api_key is None:
    raise ValueError("OPENAI_KEY 환경 변수가 설정되지 않았습니다.")

# OpenAI 클라이언트 설정
client = OpenAI(api_key=api_key)


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

def recognize_speech():
    user_input = ""
    # 질문에 답하기
    audio_bytes = audio_recorder("talk", pause_threshold=3.0,)
    if audio_bytes == st.session_state.prev_audio_bytes:
        audio_bytes = None
    st.session_state.prev_audio_bytes = audio_bytes

    try:
        if audio_bytes:
            with st.spinner("음성 인식중..."):
                with open("./tmp_audio.wav", "wb") as f:
                    f.write(audio_bytes)

                with open("./tmp_audio.wav", "rb") as f: 
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language="en"
                    )
                    user_input = transcript.text
    except Exception as e:
        print(e)
        pass
    return user_input


# Assuming you have a dictionary that holds your data like below:
speaking_topic_to_topic_info_map = {
    'speaking__listen_and_answer': {'display_name': '듣고 질문에 답하기', 'emoji': '💭'},
    'speaking__express_an_opinion': {'display_name': '의견 말하기', 'emoji': '🗣️'},
    'speaking__debate': {'display_name': '토론하기', 'emoji': '👩‍'},
    'speaking__describe_img': {'display_name': '사진 묘사하기', 'emoji': '🏞️'},
    'speaking__describe_charts': {'display_name': '도표 보고 발표하기', 'emoji': '📊'},
}

writing_topic_to_topic_info_map = {
    'writing__dictation': {'display_name': '받아쓰기 시험 유형 만들기', 'emoji': '✏️'},
    'writing__responding_to_an_email': {'display_name': '이메일 답장하기', 'emoji': '✉️'},
    'writing__summarization': {'display_name': '제시문 내용을 요약하기', 'emoji': '✍️'},
    'writing__writing_opinion': {'display_name': '자신의 의견쓰기', 'emoji': '📝'},
}


def go_to_topic(topic):
    st.session_state["curr_page"] = topic
    st.session_state["curr_topic"] = topic

def go_to_main():
    st.session_state["curr_page"] = "home"
    st.session_state["curr_topic"] = "home"

def go_to_result():
    st.session_state["curr_page"] = "result"

# Create a function to display each topic in the grid
# def display_main_button(main, ):

def display_topic(topic, topic_info, key):
    with st.container(border=True):
        st.write(f"{topic_info['emoji']} **{topic_info['display_name']}**")
        st.button("시작", key=f"start_{topic}_{key}", on_click=go_to_topic, kwargs=dict(topic=topic))


con = st.container()
if st.session_state["curr_page"] == "home":
    with con:
        st.title("Speaking & Writing Korean Tutor!")


        tab1, tab2 = st.tabs(["Speaking 시험", "Writing 시험"])

        with tab1:

            cols = st.columns(2)
            for i, (topic, topic_info) in enumerate(speaking_topic_to_topic_info_map.items()):
                with cols[i % 2]:  # This will alternate between the two columns
                    display_topic(topic, topic_info, i)
        
        with tab2:
            cols = st.columns(2)
            for i, (topic, topic_info) in enumerate(writing_topic_to_topic_info_map.items()):
                with cols[i % 2]:  # This will alternate between the two columns
                    display_topic(topic, topic_info, i)


elif st.session_state["curr_page"] == "speaking__listen_and_answer":
    topic_info = speaking_topic_to_topic_info_map[st.session_state.curr_topic]
    st.title(topic_info['display_name'])
    st.button("메인으로", on_click=go_to_main)

    # random 하게 질문 하나 가져오기
    @st.cache_data
    def load_listen_and_answer_data():
        df = pd.read_csv("./data/speaking__listen_and_answer/question_and_audio.csv")
        return df

    df = load_listen_and_answer_data()

    if "question" not in st.session_state.exam_context:
        sample = df.sample(n=1).iloc[0]

        question = sample["question"]
        audio_file_path = sample["audio_file_path"]

        st.session_state.exam_context["sample"] = sample
        st.session_state.exam_context["question"] = question
        st.session_state.exam_context["audio_file_path"] = audio_file_path


    if st.button("시험 시작"):
        st.session_state.exam_context["exam_start"] = True
        st.session_state.exam_context["do_speech"] = True

    if st.session_state.exam_context.get("exam_start", False):
        if st.session_state.exam_context["do_speech"]:
            autoplay_audio(st.session_state.exam_context["audio_file_path"])
            st.session_state.exam_context["do_speech"] = False

        if not st.session_state.exam_context["do_speech"]:
            recognized_text = recognize_speech()
            st.session_state.exam_context["user_answer"] = recognized_text

        if st.session_state.exam_context.get("user_answer"):

            with st.container(border=True):
                answer_text = f"""
                - Question: {st.session_state.exam_context["question"]}
                - Your Answer: {st.session_state.exam_context.get("user_answer")}
                """

                st.markdown(answer_text)
                

            def get_speaking__listen_and_answer_result(answer_text):
                model = ChatOpenAI(model="gpt-4-1106-preview")
                class Score(BaseModel):
                    reason: str = Field(description="Question에 대해 Your Answer가 적절한지에 대해 추론하라. 한국어로.")
                    score: int = Field(description="Question에 대해 Your Answer가 적절한지에 대해 0~200점 사이의 점수를 부여하라")
                    feedback: str = Field(description="Adjust Your Answer's grammar and expression to provide what would have been a better answer. only provide adjusted sentence in English.")
                parser = JsonOutputParser(pydantic_object=Score)
                format_instruction = parser.get_format_instructions()

                human_msg_prompt_template = HumanMessagePromptTemplate.from_template(
                    "{input}\n---\nQuestion에 대해 Your Answer가 적절한지에 대해 추론해서 0~10점 사이의 점수를 부여해라. 다음의 포맷에 맞춰 응답해라.  : {format_instruction}",
                    partial_variables={"format_instruction": format_instruction})

                prompt_template = ChatPromptTemplate.from_messages(
                    [
                        human_msg_prompt_template
                    ],
                )
                
                chain = prompt_template | model | parser
                return chain.invoke({"input": answer_text})

                
            with st.container(border=True):
                """
                ### 평가 결과
                """

                with st.spinner("채점중..."):
                    result = get_speaking__listen_and_answer_result(answer_text)

                f"""
                {result['reason']}

                #### 총점: {result['score']}

                
                #### 답변에 대한 피드백^^: 
                
                {result['feedback']}

                """

####################################
# 
elif st.session_state["curr_page"] == "speaking__express_an_opinion":
    topic_info = speaking_topic_to_topic_info_map[st.session_state.curr_topic]
    st.title(topic_info['display_name'])
    st.button("메인으로", on_click=go_to_main)

    # random 하게 질문 하나 가져오기
    @st.cache_data
    def load_speaking__express_an_opinion_data():
        df = pd.read_csv("./data/speaking__express_an_opinion/question_and_audio.csv")
        return df

    df = load_speaking__express_an_opinion_data()

    if "question" not in st.session_state.exam_context:
        sample = df.sample(n=1).iloc[0]

        question = sample["question"]
        audio_file_path = sample["audio_file_path"]

        st.session_state.exam_context["sample"] = sample
        st.session_state.exam_context["question"] = question
        st.session_state.exam_context["audio_file_path"] = audio_file_path

    if st.button("시험 시작"):
        st.session_state.exam_context["exam_start"] = True
        st.session_state.exam_context["do_speech"] = True

    if st.session_state.exam_context.get("exam_start", False):
        if st.session_state.exam_context["do_speech"]:
            autoplay_audio(st.session_state.exam_context["audio_file_path"])
            st.session_state.exam_context["do_speech"] = False

        if not st.session_state.exam_context["do_speech"]:
            recognized_text = recognize_speech()
            st.session_state.exam_context["user_answer"] = recognized_text

        if st.session_state.exam_context.get("user_answer"):

            with st.container(border=True):
                answer_text = f"""
                - Question: {st.session_state.exam_context["question"]}
                - Your Answer: {st.session_state.exam_context.get("user_answer")}
                """

                st.markdown(answer_text)
                
            with st.container(border=True):
                def get_speaking__express_opinion_result(answer_text):
                    model = ChatOpenAI(model="gpt-4-1106-preview")
                    class Score(BaseModel):
                        reason: str = Field(description="Question에 대해 의견을 말하는 TOEIC Speaking 시험이다. 의견을 적절히 구조적으로 응답했는지 추론하라. 한국어로.")
                        score: int = Field(description="Question에 대해 Your Answer가 충분히 논리적으로 의견을 표현했는지에 대해 0~10점 사이의 점수를 부여하라.")
                    parser = JsonOutputParser(pydantic_object=Score)
                    format_instruction = parser.get_format_instructions()

                    human_msg_prompt_template = HumanMessagePromptTemplate.from_template(
                        "{input}\n---\nQuestion에 대해 Your Answer가 충분히 논리적으로 의견을 표현했는지에 대해 0~10점 사이의 점수를 부여하라. 그리고 문법, 어조, 억양에 문제가 있다면 한가지씩 개선점을 제안하라. 다음의 포맷에 맞춰 응답해라.  : {format_instruction}",
                        partial_variables={"format_instruction": format_instruction})

                    prompt_template = ChatPromptTemplate.from_messages(
                        [
                            human_msg_prompt_template
                        ],
                    )
                    
                    chain = prompt_template | model | parser
                    return chain.invoke({"input": answer_text})

                """
                ### 평가 결과
                """

                with st.spinner("채점중..."):
                    result = get_speaking__express_opinion_result(answer_text)

                f"""
                {result['reason']}

                #### 총점: {result['score']}

                """


elif st.session_state["curr_page"] == "speaking__debate":

    st.title("토론하기")
    st.button("메인으로", on_click=go_to_main)
#챗봇과 사용자 간의 대화형 진행을 위해 변수 2개 설정.
    con1 = st.container()
    con2 = st.container()

    user_input = ""
#챗봇 모델 설정
    if "model" not in st.session_state.exam_context:
        st.session_state.exam_context["model"] = ChatOpenAI(model="gpt-3.5-turbo")
#exam_context에 들어갈 메시지 설정.
    if "messages" not in st.session_state.exam_context:
        system_prompt = """\
- 너는 AI 시험 감독이다.
- user의 영어 실력을 위해 어떠한 주제에 대해 서로 질문과 답을하며 토론한다."""

        model = st.session_state.exam_context["model"]
        question = model.invoke("Create a controversial question for me.").content #미리 질문을 하나 생성해놓음.

        st.session_state.exam_context["messages"] = [SystemMessage(content=system_prompt),
                                                     AIMessage(content=question),
                                                     ] #대화하며 메시지의 히스토리가 쌓이는 부분.

        #토론하기 시작하면 바로 질문을 오디오 형식으로 전환하기 위해 tts 사용.
        speech_file_path = "tmp_speak.mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy", # alloy, echo, fable, onyx, nova, and shimmer
            input=question
        )
        response.stream_to_file(speech_file_path)
        autoplay_audio(speech_file_path)

    with con1:
        for message in st.session_state.exam_context['messages']:
            if isinstance(message, SystemMessage):
                continue
            role = 'user' if message.type == 'human' else 'assistant' #사람과 챗봇의 메시지를 구분짓기 위해 이모지를 'human' else 'assistant'로 설정.
            with st.chat_message(role):
                st.markdown(message.content)

    #과거 메시지를 채우는 con2
    with con2:
        user_input = recognize_speech() #cognize_speech안에 audio recorder가 들어있어서, 메시지 아래에 음성 입력란이 표시됨.

    #현재 메시지를 채우는 con1
    with con1:
    
        #5번의 대화를 주고받고, 채점을 위해 최대 대화수를 5버느로 설정.
        turn_len = len(st.session_state.exam_context['messages'])
        max_turn_len = 5

        if user_input and turn_len < max_turn_len:
            st.session_state.exam_context['messages'].append(HumanMessage(content=user_input))

            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                model = st.session_state.exam_context["model"]

                for chunk in model.stream(st.session_state.exam_context['messages']):
                    full_response += (chunk.content or "")
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

            st.session_state.exam_context['messages'].append(AIMessage(content=full_response))

        if turn_len >= max_turn_len:

            def get_speaking__debate_result(conversation):
                model = ChatOpenAI(model="gpt-4-1106-preview")
                class Score(BaseModel):
                    reason: str = Field(description="주어진 대화에 대해 User가 얼마나 논리적이고 유창하게 영어로 응답하였는지 추론하라. 한국어로.")
                    score: int = Field(description="주어진 대화에서 User의 응답에 대해 유창성과 논리성을 고려하여, 0~200점 사이의 점수를 부여하라.TOEIC Speaking의 등급 기준에 산정하여 점수를 계산하라.")
                parser = JsonOutputParser(pydantic_object=Score)
                format_instruction = parser.get_format_instructions()

                human_msg_prompt_template = HumanMessagePromptTemplate.from_template(
                    "{input}\n---\n주어진 대화에서 User의 응답에 대해 유창성과 논리성을 고려하여 0~200점 사이의 점수를 부여하라. TOEIC Speaking의 등급 기준에 산정하여 점수를 계산하라. 다음의 포맷에 맞춰 응답해라.  : {format_instruction}",
                    partial_variables={"format_instruction": format_instruction})

                prompt_template = ChatPromptTemplate.from_messages(
                    [
                        human_msg_prompt_template
                    ],
                )
                
                chain = prompt_template | model | parser
                return chain.invoke({"input": conversation})

                
            with st.container(border=True):
                """
                ### 평가 결과
                """

                with st.spinner("채점중..."):

                    conversation = ""
                    for msg in st.session_state.exam_context["messages"]:
                        role = 'User' if msg.type == 'human' else 'AI'
                        conversation += f"{role}: {msg.content}"

                    result = get_speaking__debate_result(conversation)

                grade = ""

                if 190 < result['score'] == 200 :
                    grade = "Advanced high"
                elif 180 <= result['score'] <= 190:
                    grade = "Advanced Mid"    
                elif 160 <= result['score'] <= 170:
                    grade = "Advanced Low"
                elif 140 <= result['score'] <= 150:
                    grade = "Intermediate High"
                elif result['score'] <= 130:
                    grade = "Intermediate Mid 3"
                elif result['score'] <= 120:
                    grade = "Intermediate Mid 2"
                elif result['score'] <= 120:
                    grade = "Intermediate Mid 1"
                elif 90 <= result['score'] <= 100:
                    grade = "Intermediate Low"
                elif 60 <= result['score'] <= 80:
                    grade = "Novice High"
                elif 30 <= result['score'] <= 50:
                    grade = "Novice Mid"
                elif 0 <= result['score'] <= 20:
                    grade = "Novice Low"

                grade = f"{grade}, {result['score']}"

                f"""
                {result['reason']}

                #### 등급: {grade}
                """

#사진 묘사하기 시험.
elif  st.session_state["curr_page"] == "speaking__describe_img":
    topic_info = speaking_topic_to_topic_info_map[st.session_state.curr_topic]
    st.title(topic_info['display_name'])
    st.button("메인으로", on_click=go_to_main)

    # random 하게 질문 하나 가져오기. cache_data를 써서 매번 재실행 되지 않도록 설정.
    @st.cache_data
    def load_speaking__describe_img():
        df = pd.read_csv("./data/speaking__describe_img/desc_img.csv")
        return df

    df = load_speaking__describe_img()

    if "img_path" not in st.session_state.exam_context:
        sample = df.sample(n=1).iloc[0] #시험 초기화

        img_path = sample["img_path"]
        desc = sample["desc"]

        st.session_state.exam_context["img_path"] = img_path
        st.session_state.exam_context["desc"] = desc
        st.session_state.exam_context["recognized_text"] = ""

    st.image(st.session_state.exam_context['img_path'])
    
    with st.container(border=True):
        recognized_text = recognize_speech()
        if recognized_text:
            st.session_state.exam_context["recognized_text"] = recognized_text
        st.write(st.session_state.exam_context["recognized_text"])

    submit = st.button("제출하기")

    if submit:
        def get_speaking__describe_img(user_input, ref):
            #1. 모델 설정.
            model = ChatOpenAI(model="gpt-4-1106-preview", temperature=0.8) # CoT 는 다양한 샘플을 만들어야하기 때문에 temperature를 올려야함
            #2. Object 만들기.
            class Evaluation(BaseModel):
                score: int = Field(description="사진 묘사하기 표현 표현 점수. 0~10점")
                feedback: str = Field(description="사진 묘사하기를 더 잘 할 수 있도록하는 자세한 피드백. Markdown형식, 한국어로.")
            #3. Json 파싱 생성.
            parser = JsonOutputParser(pydantic_object=Evaluation)
            #4. format_instructions 생성.
            format_instructions = parser.get_format_instructions()

            #5. 모델에 프롬프트 생성.
            human_prompt_template = HumanMessagePromptTemplate.from_template(
                            "사진 묘사하기 영어 시험이다. 사용자의 응답을 Reference와 비교하여 평가하라.\n사용자: {input}\Reference: {ref}\n{format_instructions}",
                                        partial_variables={"format_instructions": format_instructions})

            prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        human_prompt_template,
                                                    ])
            #6. chain 생성.
            eval_chain = prompt | model | parser
            
            #7. chain.invoke를 통해 input값 넣기.
            result = eval_chain.invoke({"input": user_input, "ref": ref})
            
            #8. 출력.
            return result


        st.title("결과 & 피드백- 사진 묘사하기")

        with st.spinner("결과 & 피드백 생성중..."):
            #score와 feedback이 dictionary 형태로 담긴 result변수.
            result = get_speaking__describe_img(user_input=recognized_text,
                                                ref=st.session_state.exam_context['desc'])
        
            grade = ""
            if result['score'] >= 8:
                grade = "고급"
            elif 4 < result['score'] < 8:
                grade = "중급"
            elif result['score'] <= 4:
                grade = "초급"

            grade = f"{grade} ({result['score']}/10)"

            f"""
            당신이 제공한 답변은 스피킹 사진 묘사 시험에서 `{grade}` 수준으로 시작하기 좋은 접근입니다.
            
            여기 몇가지 피드백을 드립니다.

            {result['feedback']}
            """

#차트 설명하기.
elif  st.session_state["curr_page"] == "speaking__describe_charts":
    topic_info = speaking_topic_to_topic_info_map[st.session_state.curr_topic]
    st.title(topic_info['display_name'])
    st.button("메인으로", on_click=go_to_main)

    # 1. 미리 만들어둔 도표에 대한 설명을 저장한 csv 파일에서 random 하게 질문 하나 가져오기
    @st.cache_data
    def load_speaking__describe_charts():
        df = pd.read_csv("./data/speaking__describe_charts/desc_charts.csv")
        return df

    df = load_speaking__describe_charts()

    #2. 초기 실행시 데이터를 가져오도록, session_state에 exam_context 초기화
    if "img_path" not in st.session_state.exam_context:
        sample = df.sample(n=1).iloc[0]

        img_path = sample["img_path"]
        desc = sample["desc"]

        st.session_state.exam_context["img_path"] = img_path
        st.session_state.exam_context["desc"] = desc
        st.session_state.exam_context["recognized_text"] = ""

    st.image(st.session_state.exam_context['img_path'])
    
    with st.container(border=True):
        #이전과 동일한 마이크로 음성인식.
        recognized_text = recognize_speech()
        if recognized_text:
            st.session_state.exam_context["recognized_text"] = recognized_text
        st.write(st.session_state.exam_context["recognized_text"])

    submit = st.button("제출하기")

    if submit:
        def get_speaking__describe_img(user_input, ref):
            model = ChatOpenAI(model="gpt-4-1106-preview", temperature=0.8) # CoT 는 다양한 샘플을 만들어야하기 때문에 temperature를 올려야함
            class Evaluation(BaseModel):
                score: int = Field(description="도표 보고 발표하기 점수. 0~10점")
                feedback: str = Field(description="도표 보고 발표하기 점수. Markdown형식, 한국어로.")
            parser = JsonOutputParser(pydantic_object=Evaluation)
            format_instructions = parser.get_format_instructions()

            human_prompt_template = HumanMessagePromptTemplate.from_template(
                            "도표보고 발표하기 영어 시험이다. 사용자의 응답을 Reference와 비교하여 평가하라.\n사용자: {input}\Reference: {ref}\n{format_instructions}",
                                        partial_variables={"format_instructions": format_instructions})

            prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        human_prompt_template,
                                                    ])
            eval_chain = prompt | model | parser

            result = eval_chain.invoke({"input": user_input, "ref": ref})
            return result


        st.title("결과 & 피드백- 도표 보고 발표하기")

        with st.spinner("결과 & 피드백 생성중..."):

            result = get_speaking__describe_img(user_input=recognized_text,
                                                ref=st.session_state.exam_context['desc'])
        
            grade = ""
            if result['score'] >= 8:
                grade = "고급"
            elif 4 < result['score'] < 8:
                grade = "중급"
            elif result['score'] <= 4:
                grade = "초급"

            grade = f"{grade} ({result['score']}/10)"

            f"""
            당신이 제공한 답변은 스피킹 사진 묘사 시험에서 `{grade}` 수준으로 시작하기 좋은 접근입니다.
            
            여기 몇가지 피드백을 드립니다.

            {result['feedback']}
            """

#Listen and Writing test
elif  st.session_state["curr_page"] == "writing__dictation":
    from utils import grade_dictation

    topic_info = writing_topic_to_topic_info_map[st.session_state.curr_topic]
    st.title(topic_info['display_name'])
    st.button("메인으로", on_click=go_to_main)

    # random 하게 질문 하나 가져오기
    @st.cache_data
    def load_writing__dictation():
        df = pd.read_csv("./data/writing__dictation/sent_and_audio.csv")
        return df

    df = load_writing__dictation()

    if "sentence" not in st.session_state.exam_context:
        sample = df.sample(n=1).iloc[0]

        sentence = sample["sentence"]
        audio_file_path = sample["audio_file_path"]

        st.session_state.exam_context["sample"] = sample
        st.session_state.exam_context["sentence"] = sentence
        st.session_state.exam_context["audio_file_path"] = audio_file_path


    if st.button("시험 시작"):
        st.session_state.exam_context["exam_start"] = True
        st.session_state.exam_context["do_speech"] = True

    if st.session_state.exam_context.get("exam_start", False):
        if st.session_state.exam_context["do_speech"]:
            autoplay_audio(st.session_state.exam_context["audio_file_path"])
            st.session_state.exam_context["do_speech"] = False


        user_answer = st.text_input("user answer")
        if user_answer:
            st.session_state.exam_context["user_answer"] = user_answer

        if st.session_state.exam_context.get("user_answer"):

            with st.container(border=True):
                answer_text = f"""
                - Original sentence: {st.session_state.exam_context["sentence"]}
                - Your Answer: {st.session_state.exam_context.get("user_answer")}
                """

                st.markdown(answer_text)
                

            def get_writing__dictation_result(answer_text, ref):
                model = ChatOpenAI(model="gpt-4-1106-preview")
                class Evaluation(BaseModel):
                    reason: str = Field(description="받아쓰기 평가를 위한 추론")
                    score: int = Field(description="받아쓰기 점수. 0~10점")
                parser = JsonOutputParser(pydantic_object=Evaluation)
                format_instruction = parser.get_format_instructions()

                human_prompt_template = HumanMessagePromptTemplate.from_template(
                                            "영어 받아쓰기 시험이다. 사용자의 응답을 Reference와 비교하여 평가하라.\n사용자: {input}\Reference: {ref}\n{format_instructions}",
                                            partial_variables={"format_instructions": format_instruction})

                prompt_template = ChatPromptTemplate.from_messages(
                    [
                        human_prompt_template,
                    ])

                chain = prompt_template | model | parser
                return chain.invoke({"input": answer_text, "ref": ref})
                
            with st.container(border=True):
                """
                ### 평가 결과
                """

                with st.spinner("채점중..."):
                    model_result = get_writing__dictation_result(answer_text, st.session_state.exam_context['sentence'])
                    automatic_result = grade_dictation(correct_script=st.session_state.exam_context['sentence'], student_response=answer_text)

                    model_score = model_result['score']
                    automatic_score = automatic_result['accuracy'] * 10
                    final_score = (model_score + automatic_score)/2

                f"""
                ### Model 평가 결과
                {model_result['reason']}
                점수: {model_score}

                ### Automatic 평가 결과
                점수: {automatic_score}

                #### 총점: {final_score}

                """

##

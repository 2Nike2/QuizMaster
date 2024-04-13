import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

# .envの読み込み(AWSの認証情報を想定)
load_dotenv()

# 認証情報読み込み
yaml_path = "config.yaml"
with open(yaml_path) as file:
    config = yaml.load(file, Loader=SafeLoader)
    
authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days'],
)

authenticator.login()
if st.session_state["authentication_status"]:   

    # 使用する生成AIのモデル
    deployment_name = 'gpt-35-turbo'

    # AzureのOpenAIのモデル
    model = AzureChatOpenAI(deployment_name=deployment_name)

    prompt = PromptTemplate.from_template('''\
### 指示
あなたは有名なクイズ作家兼プログラマーです。与えられたジャンルに関する4択クイズを考えて、指定した形式で出力してください。

### 条件
・大前提として記述については正確であることが求められます、絶対に間違った知識、あいまいな知識による問題、回答、解説の生成はしないでください。
　ユーザの知識に歪めるようなクイズを作ったら減給になります。
・難易度としては一般人向けの難易度にしてください。
・正解は1つのみにしてください。
・ユーザは何度もクイズを解くことになるので、空きが来ないようにジャンルに基づいたうえで様々な問題を生成してください。
・出力内容としては「ジャンル」、「問題」、「1」、「2」、「3」、「4」、「回答番号」、「解説」にしてください。全て文字列です。
・「回答番号」は「1」、「2」、「3」、「4」のいずれかです。文字列で出力してください。
・クイズはWebサイトで出題、回答させることを想定している為、プログラムで扱いやすいJSON形式で返してください。
・「回答番号」については偏りがあると回答者が真剣に考えることなく選択する可能性があるため、均等に分散させるようにしてください。
・「解説」については、問題全体についての簡単な解説をしてください。
・「1解説」、「2解説」、「3解説」、「4解説」については、それぞれの選択肢に対する正解または不正解の理由を解説してください。

### 出力(JSON)例
{{
    "ジャンル": "地理",
    "問題": "世界で最も長い川は何ですか？",
    "1": "アマゾン川",
    "2": "ナイル川",
    "3": "長江",
    "4": "ミシシッピ川",
    "回答番号": "2",
    "解説": "ナイル川はアフリカを流れる川で、全長約6,650キロメートルに及びます。これは世界で最も長い川とされており、その流域は複数の国にまたがっています。ナイル川は古代エジプト文明の発展に大きく寄与し、今日でもその地域の重要な水源となっています。",
    "1解説": "1 アマゾン川 - 不正解。アマゾン川は南アメリカに位置し、流量は世界で最も多いですが、長さではナイル川に次ぐ第二位です。",
    "2解説": "2 ナイル川 - 正解。前述の通り、ナイル川は世界で最も長い川です。",
    "3解説": "3 長江 - 不正解。ヤンツェ川は中国最長の川であり、アジアでも長さで第三位ですが、世界全体ではナイル川やアマゾン川に比べて短いです。",
    "4解説": "4 ミシシッピ川 - 不正解。ミシシッピ川はアメリカ合衆国を流れる主要な川の一つであり、世界で最も長い川のリストで上位に位置していますが、最も長い川はナイル川です。"
}}
    
### ジャンル
{genre}

### 出力(JSON)
''')
    
    parser = JsonOutputParser()
    
    chain = prompt | model | parser

    # 問題と正答をセッション状態で保持
    if 'question' not in st.session_state:
        st.session_state.question = None
    if 'correct' not in st.session_state:
        st.session_state.correct = None
    if 'choice_dict' not in st.session_state:
        st.session_state.choice_dict = dict()

    st.title('クイズマスター')

    st.text('クイズマスターは、クイズを出題するアプリです。まずは好きなジャンルを選んでください。')

    # ジャンル選択のセレクトボックス
    genre = st.selectbox('ジャンルを選択してください', ['一般常識', '日本語表現', '社会',  'サイエンス', '美術', 'スポーツ'])

    # 出題ボタン
    if st.button('出題'):

        result = chain.invoke({'genre': genre})

        st.session_state.question = result['問題']
        st.session_state.correct = result['回答番号']
        st.session_state.explanation = result['解説'] + '  \n' + result['1解説'] + '  \n' + result['2解説'] + '  \n' + result['3解説'] + '  \n' + result['4解説']
        for i in range(1, 5):
            st.session_state.choice_dict[str(i)] = result[str(i)]


    if st.session_state.question is not None:
        
        # 問題の表示
        st.write(st.session_state.question)
        for key in st.session_state.choice_dict.keys():
            st.write(f'{key}: {st.session_state.choice_dict[key]}')

        # 回答の入力(4択問題の回答番号1～4)
        st.session_state.answer = st.selectbox('回答を入力してください(1～4)', ['1', '2', '3', '4'])

        # 回答ボタン
        if st.button('回答'):
            if st.session_state.answer == st.session_state.correct:
                st.write('正解です！')
            else:
                st.write('不正解です！')
                
            st.write(f'正解は{st.session_state.correct}です。')
            st.write('解説')
            st.write(st.session_state.explanation)
            
    
    
    authenticator.logout('ログアウト', 'sidebar')
        
elif st.session_state["authentication_status"] is False:
    st.error('ユーザ名かパスワードが違います。')

elif st.session_state["authentication_status"] is None:
    st.warning('ユーザ名かパスワードを入力してください。')
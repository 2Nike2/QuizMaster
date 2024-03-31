import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
import os
import boto3
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

    # AWSのBedrockに接続する為のクライアントを生成
    client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

    # 使用する生成AIのモデル
    # model_id = 'anthropic.claude-3-haiku-20240307-v1:0'
    model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

    question_generation_prompt_template = '''\
    ### 指示
    あなたは有名なクイズ作家兼プログラマーです。与えられたジャンルに関する4択クイズを考えて、指定した形式で出力してください。

    ### 条件
    ・大前提として記述については正確であることが求められます、間違った知識、あいまいな知識による問題、回答、解説の生成はしないでください。
    ・難易度としては中学生向けから学者向けまで幅広いレベルの問題を出していいです。
    ・正解は1つのみにしてください。
    ・ユーザは何度もクイズを解くことになるので、空きが来ないようにジャンルに基づいたうえで様々な問題を生成してください。
    ・出力内容としては「ジャンル」、「問題」、「1」、「2」、「3」、「4」、「回答番号」、「解説」にしてください。全て文字列です。
    ・「回答番号」は「1」、「2」、「3」、「4」のいずれかです。文字列で出力してください。
    ・クイズはWebサイトで出題、回答させることを想定している為、プログラムで扱いやすいJSON形式で返してください。
    ・「回答番号」については偏りがあると回答者が真剣に考えることなく選択する可能性があるため、適度にランダムに選択してください。

    ### 出力(JSON)例
    {{
        "ジャンル": "ことわざ",
        "問題": "「猿も木から落ちる」の意味は何ですか？",
        "1": "猿は木から降りるのが下手",
        "2": "熟練した人でも失敗することがある",
        "3": "木が高ければ高いほど落ちやすい",
        "4": "猿は木を壊す",
        "回答番号": "2",
        "解説": "このことわざは、普段猿が木登りが上手であるにも関わらず、時には木から落ちることがあるという事実から来ています。\\nそれに喩えて、どんなに技術が高く、経験が豊富な人であっても、時には間違いや失敗を犯すことがあるという意味を込めています。"
    }}
        
    ### ジャンル
    {}

    ### 出力(JSON)
    '''

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

        prompt = question_generation_prompt_template.format(genre)
        # 問題と正答の自動生成
        response = client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(
                            {
                                "anthropic_version": "bedrock-2023-05-31",
                                "max_tokens": 1024,
                                "temperature": 0.8,
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": [{"type": "text", "text": prompt}],
                                    }
                                ],
                            }
                        ),
                    )
        
        result = json.loads(json.loads(response.get('body').read())['content'][0]['text'])
        
        st.session_state.question = result['問題']
        st.session_state.correct = result['回答番号']
        st.session_state.explanation = result['解説']
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
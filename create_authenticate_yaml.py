import csv
import yaml
from streamlit_authenticator.utilities.hasher import Hasher
import os
from dotenv import load_dotenv

# 参考
# https://qiita.com/bassan/items/ed6d821e5ef680a20872

load_dotenv()

config_yaml_path = 'config.yaml'

site_user_list = os.getenv("SITE_USER_LIST").split(',')
site_password_list = os.getenv("SITE_PASSWORD_LIST").split(',')
site_email_list = os.getenv("SITE_EMAIL_LIST").split(',')

## yaml 設定一覧が記述されたデータを読み込み
with open(config_yaml_path,"r") as f:
    yaml_data = yaml.safe_load(f)

## パスワードのハッシュ化
users_dict = {}
for (name, password, email) in zip(site_user_list, site_password_list, site_email_list):
    
    tmp_dict = {
        "name": name,
        "password": Hasher([password]).generate()[0],
        "email":email,
    }
    users_dict[name] = tmp_dict

## yaml 書き込み
yaml_data["credentials"]["usernames"] = users_dict
with open(config_yaml_path, "w") as f:
    yaml.dump(yaml_data, f)
    print("完了")
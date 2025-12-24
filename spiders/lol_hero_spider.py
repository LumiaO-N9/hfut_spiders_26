import requests
import json # 内置
import time
import random
import os
# https 协议
# game.gtimg.cn 域名 ---DNS解析---> 服务器IP绑定
# /images/lol/act/img/js/heroList/hero_list.js 服务器资源路径
# ?之后的都是请求参数，ts=2944117，多个参数通过&分割
hero_url = "https://game.gtimg.cn/images/lol/act/img/js/heroList/hero_list.js?ts=2944117"
hero_info_url_format = "https://game.gtimg.cn/images/lol/act/img/js/hero/{}.js?ts=2944118"
my_headers = {
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}
# get请求方式，表示向服务器获取数据，常见的还有post、delete、put......
response = requests.get(url=hero_url,headers=my_headers)
json_obj = json.loads(response.text)
role_dict = {'assassin':'刺客', 'tank':'坦克', 'support':'辅助', 'fighter':'战士', 'marksman':'射手', 'mage':'法师'}
with open('lol_heros.txt',mode='w',encoding='utf8') as f1:
    for hero in json_obj['hero']:
        # 解析英雄信息
        hero_id = hero['heroId']
        hero_name = hero['name']
        hero_title = hero['title']
        hero_roles = hero['roles']
        cn_hero_roles = []
        for e_role in hero_roles:
            cn_hero_roles.append(role_dict[e_role])
        hero_cn_role = ','.join(cn_hero_roles)
        # 构建英雄详情接口地址
        hero_info_url = hero_info_url_format.format(hero_id)
        hero_detail_response = requests.get(url=hero_info_url, headers=my_headers)
        hero_detail_json_obj = json.loads(hero_detail_response.text)
        # 遍历取每一个皮肤对应的插画链接
        cnt = 0
        for skin in hero_detail_json_obj['skins']:
            chromas = skin['chromas']
            if chromas == '1':
                continue
            # 提取皮肤的名称
            skin_name = skin['name'].replace('/','|')
            skin_pic_url = skin['centerImg']
            print(skin_pic_url, skin_name)
            save_path = f'../pics/heros/{hero_name}'
            full_save_path = f'{save_path}/{cnt:02d}-{skin_name}.jpg'
            # 增加跳过逻辑，如果已经获取了，则跳过
            if not os.path.exists(full_save_path):
                # 依次请求并保存
                pic_response = requests.get(url=skin_pic_url, headers=my_headers)
                # content 将请求得到的响应以二进制的形式返回
                # 将图片保存，wb表示用二进制的方式写入
                # 判断目录是否存在，不存在则创建
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                with open(full_save_path, 'wb') as f:
                    f.write(pic_response.content)
            cnt += 1
        for spell in hero_detail_json_obj['spells']:
            spell_name = spell['name'] # 技能名称
            spell_key = spell['spellKey'] # 技能键位
            spell_desc = spell['description'].replace('\n',' ').strip() # 技能详情
            # 保存到文件中，每个英雄按照每一个技能一行数据进行保存，即：每个英雄5行数据
            hero_info_line = '|'.join([hero_id,hero_name,hero_title,hero_cn_role,spell_key,spell_name,spell_desc])
            f1.write(hero_info_line+'\n')
        # 每处理一个英雄后随机休眠1～3s，避免服务器负载过大以及触发反爬虫机制
        time.sleep(random.randint(1,3))

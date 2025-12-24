import requests
import json

hero_detail_url = 'https://game.gtimg.cn/images/lol/act/img/js/hero/1.js?ts=2944125'
my_headers = {
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}
response = requests.get(url=hero_detail_url,headers=my_headers)
# 遍历取每一个皮肤对应的插画链接
cnt = 0
for skin in json.loads(response.text)['skins']:
    chromas = skin['chromas']
    if chromas == '1':
        continue
    # 提取皮肤的名称
    hero_name = skin['heroName']
    skin_name = skin['name']
    skin_pic_url = skin['centerImg']
    print(skin_pic_url,skin_name)
    # 依次请求并保存
    pic_response = requests.get(url=skin_pic_url,headers=my_headers)
    # content 将请求得到的响应以二进制的形式返回
    # 将图片保存，wb表示用二进制的方式写入
    with open(f'../pics/heros/{hero_name}-{cnt}-{skin_name}.jpg', 'wb') as f:
        f.write(pic_response.content)
    cnt += 1
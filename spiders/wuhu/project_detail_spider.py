"""
create table if not exists project_detail_zzk_01(
    id bigint NOT NULL AUTO_INCREMENT comment '自增id'
    ,project_no varchar(255) comment '项目编号'
    ,project_name varchar(255) comment '项目名称'
    ,project_addr  varchar(500) comment '建设地点'
    ,project_price varchar(20) comment '项目合同金额'
    ,project_require text comment '项目投标人要求'
    ,project_detail_url varchar(255) comment '项目详情URL'
    ,input_time datetime default CURRENT_TIMESTAMP comment '插入时间'
    ,update_time datetime default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP comment '更新时间'
    ,PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4 COMMENT='项目详情表';
"""
import pymysql
import requests
from lxml import etree

host = 'rm-bp1y7dm47j8h060vy4o.mysql.rds.aliyuncs.com'
user = 'hfut22'
password = '123456'
port = 3307
database = 'hfut22'
my_headers = {
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

def extract_text_by_search_str_in_p(x_obj,search_str):
    p_tag = x_obj.xpath(f"//p[contains(string(.),'{search_str}')]")[0]
    return p_tag.xpath('string(.)').split(search_str)[-1]

# 建立链接
with pymysql.connect(host=host, user=user, passwd=password, port=port, db=database) as conn:
    # 创建cursor游标
    with conn.cursor() as cursor:
        # flag为0表示详情未获取，故需要进行提取
        cursor.execute('select id,project_title,project_detail_url from project_list_zzk_01 where flag = 0 limit 1')
        rows = cursor.fetchall()
        # 依次遍历每一个项目
        for row in rows:
            id,project_title,project_detail_url = row[0],row[1],row[2]
            print(f"当前正在处理项目：{project_title}，详情地址：{project_detail_url}")
            # 使用requests模块请求项目详情地址
            response = requests.get(url=project_detail_url,headers=my_headers)
            xpath_obj = etree.HTML(response.text,etree.HTMLParser())
            # 提取项目编号
            project_no = xpath_obj.xpath("//div[@class='text l']/text()")[0].strip()
            # 提取项目名称，由于标签没有特点，所以只能采取字符串搜索来定位标签
            project_name = extract_text_by_search_str_in_p(xpath_obj,'项目名称：')
            # 同理，提取项目地点、合同估算价
            project_addr = extract_text_by_search_str_in_p(xpath_obj,'建设地点：').split('；')[0].replace('。','')
            project_price = extract_text_by_search_str_in_p(xpath_obj,'合同估算价：').replace('。','')
            # 提取投标人资格要求
            # 定位投标人资格要求标题p标签
            require_title_p = xpath_obj.xpath("//p[@style='line-height: 150%;' and contains(string(.),'投标人资格要求')]")[0]
            # 循环提取标题标签p的后续p标签，直到下一个标题p标签出现就停止
            flag = True
            project_require = ''
            while flag:
                next_require_title_p = require_title_p.xpath("./following-sibling::p[1]")[0]
                next_require_title_p_style = next_require_title_p.xpath("./@style")[0]
                print(next_require_title_p_style)
                if next_require_title_p_style == 'line-height: 150%;':
                    flag = False
                else:
                    project_require += next_require_title_p.xpath("string(.)")
                require_title_p = next_require_title_p
            print(project_require)
            # print(next_require_title_p.xpath('string(.)'))
            # print(project_no,project_name,project_addr,project_price)
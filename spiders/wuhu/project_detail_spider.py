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
import json
from lxml import etree
from openai import OpenAI

host = 'rm-bp1y7dm47j8h060vy4o.mysql.rds.aliyuncs.com'
user = 'hfut22'
password = '123456'
port = 3307
database = 'hfut22'
my_headers = {
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

client = OpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key="sk-32c1c98604324aa0a42edca638da3340",
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

extract_rule = """
帮我解析一下上面的内容，需要提取：
项目编号、项目名称、建设地点、合同金额或估算价、投标人资格要求
建设地点需要进行归纳，越简单越好
合同金额或估算价需要统一单位，以元作为单位，最终返回纯数字
投标人资格要求只需要概述一下即可，大约50字～100字左右
以需要提取的字段名作为key，提取到的值作为value，如果Key对应的Value不存在则可以将Value置为空字符串，最终结果以json格式返回
不要罗里吧嗦，只返回json结果即可，除json数据之外任何东西都不需要，最好能把json压缩到一行
"""

def extract_text_by_search_str_in_p(x_obj,search_str):
    p_tag = x_obj.xpath(f"//p[contains(string(.),'{search_str}')]")[0]
    return p_tag.xpath('string(.)').split(search_str)[-1]

# 用于解析网页内容，基于大模型
def extract_content_by_ai(project_content,extract_rule):
    # 初始化OpenAI客户端

    messages = [{"role": "user", "content": f"{project_content}"}, {"role": "system", "content": f"{extract_rule}"}]

    completion = client.chat.completions.create(
        model="deepseek-v3.2",  # 您可以按需更换为其它深度思考模型
        messages=messages,
        extra_body={"enable_thinking": False},
        stream=True,
        stream_options={
            "include_usage": False
        },
    )

    reasoning_content = ""  # 完整思考过程
    answer_content = ""  # 完整回复
    is_answering = False  # 是否进入回复阶段
    print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")

    for chunk in completion:
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
            continue

        delta = chunk.choices[0].delta

        # # 只收集思考内容
        # if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
        #     if not is_answering:
        #         print(delta.reasoning_content, end="", flush=True)
        #     reasoning_content += delta.reasoning_content

        # 收到content，开始进行回复
        if hasattr(delta, "content") and delta.content:
            if not is_answering:
                print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                is_answering = True
            print(delta.content, end="", flush=True)
            answer_content += delta.content
    json_obj = json.loads(answer_content.replace('```','').replace('json','').strip())
    return json_obj['项目编号'],json_obj['项目名称'],json_obj['建设地点'],json_obj['合同金额或估算价'],json_obj['投标人资格要求']


def insert_into_mysql(conn,insert_sql,batch_rows,ids):
     with conn.cursor() as cursor:
         cursor.executemany(insert_sql,batch_rows)
         conn.commit()
         update_id_sql = f"update project_list_zzk_01 set flag = 1 where id in ({','.join(ids)})"
         # print(update_id_sql)
         cursor.execute(update_id_sql)
         conn.commit()


# 建立链接
with pymysql.connect(host=host, user=user, passwd=password, port=port, db=database) as conn:
    # 创建cursor游标
    with conn.cursor() as cursor:
        # flag为0表示详情未获取，故需要进行提取
        cursor.execute('select id,project_title,project_detail_url from project_list_zzk_01 where flag = 0')
        rows = cursor.fetchall()
        # 依次遍历每一个项目
        project_detail_list = []
        insert_sql = """
        insert into project_detail_zzk_01(project_no,project_name,project_addr,project_price,project_require,project_detail_url) values (%s,%s,%s,%s,%s,%s)
        """
        batch_size = 5
        ids = set()
        for row in rows:
            id,project_title,project_detail_url = row[0],row[1],row[2]
            ids.add(str(id))
            print(f"当前正在处理项目：{project_title}，详情地址：{project_detail_url}")
            # 使用requests模块请求项目详情地址
            response = requests.get(url=project_detail_url,headers=my_headers)
            xpath_obj = etree.HTML(response.text,etree.HTMLParser())
            # 借助AI大模型帮助我们解析网页内容
            # 第一步：将项目详情内容全部提取
            div = xpath_obj.xpath("//div[@class='article-main']")[0]
            project_all_content = div.xpath("string(.)").strip()
            # 第二步：构建AI的Prompt提示词，借助AI提取想要的内容
            project_no,project_name,project_addr,project_price,project_require = extract_content_by_ai(project_all_content,extract_rule)
            project_detail_list.append((project_no,project_name,project_addr,project_price,project_require,project_detail_url))
            if len(project_detail_list) == batch_size:
                insert_into_mysql(conn,insert_sql,project_detail_list,ids)
                project_detail_list = []
                ids = set()
        if len(project_detail_list) > 0:
            insert_into_mysql(conn,insert_sql,project_detail_list,ids)
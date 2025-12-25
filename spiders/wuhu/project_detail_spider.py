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
            # # 提取项目编号
            # project_no = xpath_obj.xpath("//div[@class='text l']/text()")[0].strip()
            # # 提取项目名称，由于标签没有特点，所以只能采取字符串搜索来定位标签
            # project_name = extract_text_by_search_str_in_p(xpath_obj,'项目名称：')
            # # 同理，提取项目地点、合同估算价
            # project_addr = extract_text_by_search_str_in_p(xpath_obj,'建设地点：').split('；')[0].replace('。','')
            # project_price = extract_text_by_search_str_in_p(xpath_obj,'合同估算价：').replace('。','')
            # # 提取投标人资格要求
            # # 定位投标人资格要求标题p标签
            # require_title_p = xpath_obj.xpath("//p[@style='line-height: 150%;' and contains(string(.),'投标人资格要求')]")[0]
            # # 循环提取标题标签p的后续p标签，直到下一个标题p标签出现就停止
            # flag = True
            # project_require = ''
            # while flag:
            #     next_require_title_p = require_title_p.xpath("./following-sibling::p[1]")[0]
            #     next_require_title_p_style = next_require_title_p.xpath("./@style")[0]
            #     if next_require_title_p_style == 'line-height: 150%;':
            #         flag = False
            #     else:
            #         project_require += next_require_title_p.xpath("string(.)")
            #     require_title_p = next_require_title_p
            # print(project_require)
            # # print(next_require_title_p.xpath('string(.)'))
            # # print(project_no,project_name,project_addr,project_price)
            # 借助AI大模型帮助我们解析网页内容
            # 第一步：将项目详情内容全部提取
            div = xpath_obj.xpath("//div[@class='article-main']")[-1]
            project_all_content = div.xpath("string(.)")
            # 第二步：构建AI的Prompt提示词，借助AI提取想要的内容
            print(project_all_content)
'''
大模型代码调用示例：
# coding=utf-8
# pip install openai -i https://mirrors.aliyun.com/pypi/simple
from openai import OpenAI
import os

# 初始化OpenAI客户端
client = OpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key="sk-32c1c98604324aa0a42edca638da3340",
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
project_content = "一、项目编号：WH010FJ25SG0853（任务书编号：FS34020120251123号）二、项目名称：首都医科大学附属北京安定医院芜湖医院供电工程项目三、项目概况与招标范围1.建设地点：项目位于芜湖市三山经开区三华山路以北，峨桥路以东，高岗埠路以南，北京天坛医院安徽医院以西；建设规模：设计总建筑面积112905.10平方米，地上建筑面积76852.46平方米，地下建筑面积36052.64平方米，电压10kV，总容量10700kVA；招标范围：包含环网柜到开闭所高压进线柜10kV电源电缆及拖拉管施工，配电房高低压柜及变压器等设备安装调试，柴油发电机组及柴发机房内配电柜安装调试，配电房高压柜出线电缆安装，柜间母线槽安装，10kV高压桥架安装，电力监控系统、配电房备品备件、配电房装修等。具体详见招标文件、图纸及招标工程量清单；计划工期：90个日历天。2.标段划分：共一个标段。3.合同估算价：17093506.56元。4.资金来源：政府性资金。四、投标人资格要求1.投标人资质要求：须具备以下（1）或（2）资质，并具有有效的安全生产许可证。（1）电力工程施工总承包三级及以上资质，并同时取得五级及以上“承装（修、试）电力设施许可证”(许可类别须包括承装类、承修类及承试类)； （2）输变电工程专业承包三级及以上资质，并同时取得五级及以上“承装（修、试）电力设施许可证”(许可类别须包括承装类、承修类及承试类)。2.投标人类似业绩要求：无。3.项目负责人（项目经理，下同）资质要求：投标人拟委任的项目负责人须具备机电工程专业一级注册建造师执业资格，具备有效的安全生产考核合格证书。4.项目负责人类似业绩要求：无。5.本次招标是否接受联合体投标： 否。本项目为非复杂工程，施工内容简单，工期较短，不接受联合体投标。6.不良行为记录投标人须符合下列情形之一（不良行为以芜湖市公共资源交易信用管理平台的不良行为披露专栏公开信息为准）：（1）未被市、县市区公共资源交易监管部门记不良行为记录；（2）曾被市、县市区公共资源交易监管部门记不良行为记录，投标截止日不在披露期内。7.其他要求：（1）落实政府采购政策需满足的资格要求：本项目预留份额专门面向中小企业采购。本项目要求中小企业承担的部分不少于签约合同价的40%（其中小微企业承担的部分不少于中小企业承担部分的70%）。预留份额通过以下措施进行：分包。如果投标人本身提供所有工程均由中小企业承建，视同符合了相关资格条件。无需再向其他中小企业分包。（2）其他要求：无。五、招标文件的获取1.获取时间：2025年12月25日9:00至投标截止时间。2.获取方式：凡有意参加投标者，请于获取时间内登录芜湖市公共资源交易数智共享系统（以下简称“数智共享系统”）下载招标文件。数智共享系统进入方法1：通过网址http://60.167.105.5:20080/tpbidder/；方法2：通过芜湖市公共资源交易中心网（https://whsggzy.wuhu.gov.cn/），选择“市场主体”- “数智共享系统”。3.招标文件售价：0元。六、投标文件的递交1.递交截止时间：2026年01月15日09:15。2.递交方法：投标人应在投标文件递交截止时间前通过数智共享系统递交电子投标文件。七、开标时间及地点1.开标时间：2026年01月15日09:15。2.开标地点：芜湖市公共资源交易中心开标室（详见开标区电子显示屏）。八、其他公告内容1.招标方式：公开招标。2.资格审查方式：资格后审。3.评标办法：综合评估法。4.投标保证金账号：①开户单位：芜湖市公共资源交易中心开户银行及账号：中国建设银行股份有限公司芜湖政务新区支行(6232811650000148944)②开户单位：芜湖市公共资源交易中心开户银行及账号：徽商银行股份有限公司芜湖南湖路支行(1101801021000587877357048)③开户单位：芜湖市公共资源交易中心开户银行及账号：农业银行芜湖分行金桥支行(126301010400377840000003502)④开户单位：芜湖市公共资源交易中心开户银行及账号：中国银行芜湖分行营业部(188748260885)5.对招标文件的异议、投诉：投标人或者其他利害关系人对招标文件有异议的，应在投标截止时间10日前通过数智共享系统在线或以书面形式提出。投标人或者其他利害关系人对异议答复不满意，或者招标人、代理机构未在规定时间内作出异议答复的，可以在规定时间内通过数智共享系统在线或以书面形式向招标监督管理机构提出投诉。受理异议、投诉的联系人和联系方式见招标公告第十条。九、发布公告的媒介本次招标公告同时在中国招标投标公共服务平台、安徽省公共资源交易监管网、芜湖市公共资源交易中心网上发布。十、联系方式1.招标人名称：芜湖市重点工程建设管理处地址：芜湖市政务文化中心B区3楼联系人：高工 电话：0553-38335672.招标代理机构名称：芜湖宜正工程咨询有限公司地址：安徽省芜湖市鸠江区皖江财富广场A3座3层302A室联系人：檀俊芳、胡琴电话：19955350938、157553810993.招标监督管理机构名称：芜湖市公共资源交易监督管理局地址：芜湖市鸠江区瑞祥路88号皖江财富广场 A4 座9楼电话：0553-31216594.芜湖市公共资源交易中心保证金窗口联系电话：0553-5932711，电子保函技术支持电话：0553-3996569；技术咨询电话：0553-3121801，0512-58188516。十一、注册事项1.潜在投标人须登录数智共享系统查阅招标文件。登录前须持有与数智共享系统兼容的数字证书，详情参见 CA 数字证书及电子签章业务办事指南（市中心及分中心)服务指南。（特别提醒：潜在投标人查阅招标文件后，如参与投标，则需在招标文件获取时间内通过数智共享系统完成投标信息的填写。）"

extract_rule = """
帮我解析一下上面的内容，需要提取：
项目编号、项目名称、合同金额或估算价、投标人资格要求
投标人资格要求只需要概述一下即可，大约50字～100字左右
以需要提取的字段名作为key，提取到的值作为value，最终结果以json格式返回
不要罗里吧嗦，只返回json结果即可
"""
messages = [{"role": "user", "content": f"{project_content}"},{"role": "system", "content": f"{extract_rule}"}]

completion = client.chat.completions.create(
    model="deepseek-v3.2",  # 您可以按需更换为其它深度思考模型
    messages=messages,
    extra_body={"enable_thinking": True},
    stream=True,
    stream_options={
        "include_usage": True
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

    # 只收集思考内容
    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
        if not is_answering:
            print(delta.reasoning_content, end="", flush=True)
        reasoning_content += delta.reasoning_content

    # 收到content，开始进行回复
    if hasattr(delta, "content") and delta.content:
        if not is_answering:
            print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
            is_answering = True
        print(delta.content, end="", flush=True)
        answer_content += delta.content
'''

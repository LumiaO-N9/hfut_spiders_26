import requests
import json
import pymysql
"""
create table if not exists project_list_zzk_01(
    id bigint NOT NULL AUTO_INCREMENT comment '自增id'
    ,project_id varchar(255) comment '项目id'
    ,project_title varchar(255) comment '项目名称'
    ,project_hylb  varchar(20) comment '行业类别'
    ,project_xmzl varchar(20) comment '项目字类'
    ,project_date varchar(20) comment '项目时间'
    ,project_detail_url varchar(255) comment '项目详情URL'
    ,input_time datetime default CURRENT_TIMESTAMP comment '插入时间'
    ,update_time datetime default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP comment '更新时间'
    ,PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4 COMMENT='项目列表数据';
"""
# 请求是的表单数据，可以用于过滤
requests_form = {
    'searchText':'',
    'categoryNum':'005001',
    'xmlx':'',
    'hylb':'全部',
    'searchjydd':'340201', # 交易地点为市辖区
    'searchxmxq':'全部',
    'searchjyfs':'全部',
    'searchinfotype':'005001001', # 取招标公告
    'searchdate':'20day', # 取近20天
    'siteGuid':'7eb5f7f1-9041-43ad-8e13-8fcb82ea831a',
    'pageindex':'0', # 取第一页
    'pagesize':'10', # 每次请求返回的大小
    'projectzilei':'全部',
    'YZM':'1',
    'ImgGuid':'1'
}

hylb_dict = {
    'A01':'房建',
    'A02':'市政',
    'A03':'公路',
    'A04':'铁路',
    'A05':'民航',
    'A06':'水运',
    'A07':'水利',
    'A08':'能源',
    'A09':'邮电通信',
    'A10':'桥梁',
    'A11':'城市轨道',
    'A12':'矿产冶金',
    'A13':'信息网络',
    'A14':'工业制造',
    'A99':'高标准农田',
}

xmzl_dict = {
    'SG':'施工',
    'SJ':'设计',
    'JL':'监理',
    'KC':'勘察',
    'JC':'检测',
    'ZX':'全过程咨询',
    'ZN':'智能化',
    'EP':'施工设计一体化',
    'QT':'其他',
}

api_url = 'https://whsggzy.wuhu.gov.cn/EpointWebBuilder1/rest/lightfrontaction/getPageInfoListNewWhJyxxCustom'
my_headers = {
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}
detail_url_format = "https://whsggzy.wuhu.gov.cn/whggzyjy"
# 共四页数据
total_pages = 4
host = 'rm-bp1y7dm47j8h060vy4o.mysql.rds.aliyuncs.com'
user = 'hfut22'
password = '123456'
port = 3307
database = 'hfut22'
# 建立链接
with pymysql.connect(host=host, user=user, passwd=password, port=port, db=database) as conn:
    # 创建cursor游标
    with conn.cursor() as cursor:
        table_name = 'project_list_zzk_01'
        insert_sql = 'insert into project_list_zzk_01(project_id,project_title, project_hylb, project_xmzl, project_date, project_detail_url) values (%s,%s,%s,%s,%s,%s)'
        for page in range(total_pages):
            requests_form['pageindex'] = str(page)
            response = requests.post(url=api_url,data=requests_form,headers=my_headers)
            project_json_obj = json.loads(response.text)
            project_list = []
            for project in project_json_obj['custom']['infodata']:
                # 依次提取每一个项目的信息
                project_id = project['infoid']
                project_title = project['title']
                project_hylb = hylb_dict[project['hylb']]
                project_xmzl = xmzl_dict[project['projectzilei']]
                project_date = project['infodate']
                project_detail_url = detail_url_format + project['infourl']
                # print(project_title, project_hylb, project_xmzl, project_date, project_detail_url)
                # 将解析到的数据写入数据库，没来一个项目写入一次数据库
                # cursor.execute(insert_sql,(project_id,project_title, project_hylb, project_xmzl, project_date, project_detail_url))
                project_list.append((project_id,project_title, project_hylb, project_xmzl, project_date, project_detail_url))
            # 批量写入，性能更高
            cursor.executemany(insert_sql,project_list)
            conn.commit()

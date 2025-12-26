from flask import Flask, render_template, request, jsonify
import pymysql
from config import Config
import json

app = Flask(__name__)
app.config.from_object(Config)


def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**app.config['DB_CONFIG'])


@app.route('/')
def index():
    """首页 - 显示项目列表"""
    page = request.args.get('page', 1, type=int)
    per_page = app.config['PER_PAGE']
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 查询总记录数
    cursor.execute(
        "SELECT COUNT(*) as total FROM project_list_zzk_02 pl JOIN project_detail_zzk_02 pd ON pl.id = pd.id")
    total = cursor.fetchone()['total']

    # 查询项目列表，按金额降序排列
    query = """
    SELECT 
        pl.project_id,
        pl.project_title,
        pl.project_hylb,
        pl.project_xmzl,
        pd.project_no,
        pd.project_addr,
        pd.project_price,
        pd.project_detail_url
    FROM project_list_zzk_02 pl
    JOIN project_detail_zzk_02 pd ON pl.id = pd.id
    ORDER BY CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2)) DESC
    LIMIT %s OFFSET %s
    """

    cursor.execute(query, (per_page, offset))
    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    # 计算分页信息
    total_pages = (total + per_page - 1) // per_page

    return render_template('index.html',
                           projects=projects,
                           page=page,
                           total_pages=total_pages,
                           total=total)


@app.route('/detail/<project_id>')
def detail(project_id):
    """项目详情页"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = """
    SELECT 
        pl.project_id,
        pl.project_title,
        pl.project_hylb,
        pl.project_xmzl,
        pl.project_date,
        pl.project_detail_url,
        pd.project_no,
        pd.project_addr,
        pd.project_price,
        pd.project_require
    FROM project_list_zzk_02 pl
    JOIN project_detail_zzk_02 pd ON pl.id = pd.id
    WHERE pl.project_id = %s
    """

    cursor.execute(query, (project_id,))
    project = cursor.fetchone()

    cursor.close()
    conn.close()

    if not project:
        return "项目不存在", 404

    return render_template('detail.html', project=project)


@app.route('/analysis')
def analysis():
    """数据分析页"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 1. 行业分布分析
    cursor.execute("""
    SELECT 
        CASE 
            WHEN pl.project_hylb IS NULL OR pl.project_hylb = '' THEN '未分类'
            ELSE pl.project_hylb 
        END as category,
        COUNT(*) as count,
        SUM(
            CASE 
                WHEN pd.project_price IS NOT NULL AND pd.project_price != '' 
                THEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2))
                ELSE 0 
            END
        ) as total_amount
    FROM project_list_zzk_02 pl
    JOIN project_detail_zzk_02 pd ON pl.id = pd.id
    GROUP BY 
        CASE 
            WHEN pl.project_hylb IS NULL OR pl.project_hylb = '' THEN '未分类'
            ELSE pl.project_hylb 
        END
    ORDER BY count DESC
    """)
    industry_data = cursor.fetchall()

    # 2. 金额分布分析
    cursor.execute("""
    SELECT 
        CASE 
            WHEN pd.project_price IS NULL OR pd.project_price = '' THEN '未提供金额'
            WHEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2)) < 1000000 THEN '0-100万'
            WHEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2)) < 5000000 THEN '100-500万'
            WHEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2)) < 10000000 THEN '500-1000万'
            ELSE '1000万以上'
        END as price_range,
        COUNT(*) as count,
        SUM(
            CASE 
                WHEN pd.project_price IS NOT NULL AND pd.project_price != '' 
                THEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2))
                ELSE 0 
            END
        ) as total_amount
    FROM project_list_zzk_02 pl
    JOIN project_detail_zzk_02 pd ON pl.id = pd.id
    GROUP BY 
        CASE 
            WHEN pd.project_price IS NULL OR pd.project_price = '' THEN '未提供金额'
            WHEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2)) < 1000000 THEN '0-100万'
            WHEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2)) < 5000000 THEN '100-500万'
            WHEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2)) < 10000000 THEN '500-1000万'
            ELSE '1000万以上'
        END
    ORDER BY 
        CASE 
            WHEN price_range = '未提供金额' THEN 0
            WHEN price_range = '0-100万' THEN 1
            WHEN price_range = '100-500万' THEN 2
            WHEN price_range = '500-1000万' THEN 3
            ELSE 4
        END
    """)
    price_data = cursor.fetchall()

    # 3. 项目类型分析（修复空值问题）
    cursor.execute("""
    SELECT 
        CASE 
            WHEN pl.project_xmzl IS NULL OR pl.project_xmzl = '' THEN '未分类'
            ELSE pl.project_xmzl 
        END as project_type,
        COUNT(*) as count
    FROM project_list_zzk_02 pl
    JOIN project_detail_zzk_02 pd ON pl.id = pd.id
    GROUP BY 
        CASE 
            WHEN pl.project_xmzl IS NULL OR pl.project_xmzl = '' THEN '未分类'
            ELSE pl.project_xmzl 
        END
    ORDER BY count DESC
    LIMIT 10
    """)
    type_data = cursor.fetchall()

    # 4. 每日项目数量（修复日期格式问题）
    cursor.execute("""
    SELECT 
        pl.project_date,
        COUNT(*) as count
    FROM project_list_zzk_02 pl
    JOIN project_detail_zzk_02 pd ON pl.id = pd.id
    GROUP BY 
        pl.project_date
    ORDER BY pl.project_date
    """)
    monthly_data = cursor.fetchall()

    # 5. 统计总数
    cursor.execute("""
    SELECT 
        COUNT(*) as total_projects,
        SUM(
            CASE 
                WHEN pd.project_price IS NOT NULL AND pd.project_price != '' 
                THEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2))
                ELSE 0 
            END
        ) as total_amount,
        AVG(
            CASE 
                WHEN pd.project_price IS NOT NULL AND pd.project_price != '' 
                THEN CAST(REPLACE(pd.project_price, '万元', '') AS DECIMAL(10,2))
                ELSE NULL 
            END
        ) as avg_amount
    FROM project_list_zzk_02 pl
    JOIN project_detail_zzk_02 pd ON pl.id = pd.id
    """)
    stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('analysis.html',
                           industry_data=json.dumps(industry_data, default=str),
                           price_data=json.dumps(price_data, default=str),
                           type_data=json.dumps(type_data, default=str),
                           monthly_data=json.dumps(monthly_data, default=str),
                           stats=stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
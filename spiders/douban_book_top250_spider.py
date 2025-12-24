import requests
from lxml import etree

my_headers = {
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

# w 表示写入模式为：overwrite即覆盖写入，a 表示append即追加写入
with open('douban_top250_books.txt', 'w', encoding='utf-8') as f:
    for start in range(0, 226, 25):
        url = f"https://book.douban.com/top250?start={start}"
        # print(f"当前处理的URL为：{url}")
        response = requests.get(url=url, headers=my_headers)
        html_xpath = etree.HTML(response.text, etree.HTMLParser())
        table_list = html_xpath.xpath("//div[@class='indent']/table")

        for table in table_list:
            td = table.xpath("./tr/td[2]")[0]
            title = td.xpath('./div[1]/a/text()')[0].strip()
            infos = td.xpath("./p[@class='pl']/text()")[0].strip().split("/")
            if len(infos) == 4:
                author = infos[0].strip()
            elif len(infos) == 3:
                author = ''
            elif len(infos) > 4:
                author = "|".join(infos[-4::-1]).strip()
            else:
                raise ValueError("infos长度不对，需要手动处理！")
            # 下标为负数表示从右往左数
            publish = infos[-3].strip()
            year = infos[-2].strip()
            price = infos[-1].strip()
            rating_nums = td.xpath(".//span[@class='rating_nums']/text()")[0]
            comment_nums = td.xpath(".//span[@class='pl']/text()")[0].replace("(", "").replace(")", "").strip()
            quote = ''
            quote_text = td.xpath("./p[@class='quote']/span/text()")
            if len(quote_text) > 0:
                quote = quote_text[0].strip()
            line = f"{title}\t{author}\t{publish}\t{year}\t{price}\t{rating_nums}\t{comment_nums}\t{quote}\n"
            # print(line)
            f.write(line)
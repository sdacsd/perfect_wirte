'''
并行分词处理
'''
import os
import pickle
import logging

import sys
sys.path.append("..")

# 导入自定义解析结构
from python_structured import *
from sql_structured import *

# 导入FastText库，使用gensim 3.4.0版本
from gensim.models import FastText

import numpy as np

# 导入词频统计库
import collections
# 导入词云展示库
import wordcloud
# 导入图像处理库，使用Pillow 5.1.0版本
from PIL import Image

# 导入多进程库
from multiprocessing import Pool as ThreadPool

# Python解析函数
def multipro_python_query(data_list):
    """并行处理Python查询解析"""
    result = [python_all_context_parse(line) for line in data_list]
    return result

def multipro_python_code(data_list):
    """并行处理Python代码解析"""
    result = [python_query_parse(line) for line in data_list]
    return result

def multipro_python_context(data_list):
    """并行处理Python上下文解析"""
    result = []
    for line in data_list:
        if line == '-10000':
            result.append(['-10000'])
        else:
            result.append(python_part_context_parse(line))
    return result

# SQL解析函数
def multipro_sql_query(data_list):
    """并行处理SQL查询解析"""
    result = [sql_all_context_parse(line) for line in data_list]
    return result

def multipro_sql_code(data_list):
    """并行处理SQL代码解析"""
    result = [sql_query_parse(line) for line in data_list]
    return result

def multipro_sql_context(data_list):
    """并行处理SQL上下文解析"""
    result = []
    for line in data_list:
        if line == '-10000':
            result.append(['-10000'])
        else:
            result.append(sql_part_context_parse(line))
    return result

# 最终的Python版解析函数
def python_parse_final(python_list, split_num):
    """处理并行Python解析的最终函数"""

    # 解析acont1数据块
    acont1_data = [i[1][0][0] for i in python_list]
    acont1_split_list = [acont1_data[i:i + split_num] for i in range(0, len(acont1_data), split_num)]
    pool = ThreadPool(10)
    acont1_list = pool.map(multipro_python_context, acont1_split_list)
    pool.close()
    pool.join()
    acont1_cut = [p for sublist in acont1_list for p in sublist]
    print('acont1条数：%d' % len(acont1_cut))

    # 解析acont2数据块
    acont2_data = [i[1][1][0] for i in python_list]
    acont2_split_list = [acont2_data[i:i + split_num] for i in range(0, len(acont2_data), split_num)]
    pool = ThreadPool(10)
    acont2_list = pool.map(multipro_python_context, acont2_split_list)
    pool.close()
    pool.join()
    acont2_cut = [p for sublist in acont2_list for p in sublist]
    print('acont2条数：%d' % len(acont2_cut))

    # 解析查询数据块
    query_data = [i[3][0] for i in python_list]
    query_split_list = [query_data[i:i + split_num] for i in range(0, len(query_data), split_num)]
    pool = ThreadPool(10)
    query_list = pool.map(multipro_python_query, query_split_list)
    pool.close()
    pool.join()
    query_cut = [p for sublist in query_list for p in sublist]
    print('query条数：%d' % len(query_cut))

    # 解析代码数据块
    code_data = [i[2][0][0] for i in python_list]
    code_split_list = [code_data[i:i + split_num] for i in range(0, len(code_data), split_num)]
    pool = ThreadPool(10)
    code_list = pool.map(multipro_python_code, code_split_list)
    pool.close()
    pool.join()
    code_cut = [p for sublist in code_list for p in sublist]
    print('code条数：%d' % len(code_cut))

    # 获取qids
    qids = [i[0] for i in python_list]
    print(qids[0])
    print(len(qids))

    return acont1_cut, acont2_cut, query_cut, code_cut, qids

# 最终的SQL版解析函数
def sql_parse_final(sql_list, split_num):
    """处理并行SQL解析的最终函数"""

    # 解析acont1数据块
    acont1_data = [i[1][0][0] for i in sql_list]
    acont1_split_list = [acont1_data[i:i + split_num] for i in range(0, len(acont1_data), split_num)]
    pool = ThreadPool(10)
    acont1_list = pool.map(multipro_sql_context, acont1_split_list)
    pool.close()
    pool.join()
    acont1_cut = [p for sublist in acont1_list for p in sublist]
    print('acont1条数：%d' % len(acont1_cut))

    # 解析acont2数据块
    acont2_data = [i[1][1][0] for i in sql_list]
    acont2_split_list = [acont2_data[i:i + split_num] for i in range(0, len(acont2_data), split_num)]
    pool = ThreadPool(10)
    acont2_list = pool.map(multipro_sql_context, acont2_split_list)
    pool.close()
    pool.join()
    acont2_cut = [p for sublist in acont2_list for p in sublist]
    print('acont2条数：%d' % len(acont2_cut))

    # 解析查询数据块
    query_data = [i[3][0] for i in sql_list]
    query_split_list = [query_data[i:i + split_num] for i in range(0, len(query_data), split_num)]
    pool = ThreadPool(10)
    query_list = pool.map(multipro_sql_query, query_split_list)
    pool.close()
    pool.join()
    query_cut = [p for sublist in query_list for p in sublist]
    print('query条数：%d' % len(query_cut))

    # 解析代码数据块
    code_data = [i[2][0][0] for i in sql_list]
    code_split_list = [code_data[i:i + split_num] for i in range(0, len(code_data), split_num)]
    pool = ThreadPool(10)
    code_list = pool.map(multipro_sql_code, code_split_list)
    pool.close()
    pool.join()
    code_cut = [p for sublist in code_list for p in sublist]
    print('code条数：%d' % len(code_cut))

    # 获取qids
    qids = [i[0] for i in sql_list]

    return acont1_cut, acont2_cut, query_cut, code_cut, qids

# 主函数，将Python和SQL的解析集合到一个函数中
def main(lang_type, split_num, source_path, save_path):
    """主函数，根据语言类型调用相应的解析函数并保存结果"""
    total_data = []
    with open(source_path, "rb") as f:
        # 存储为字典，有序
        corpus_lis = pickle.load(f)

        # 处理不同语言的解析
        if lang_type == 'python':
            parse_acont1, parse_acont2, parse_query, parse_code, qids = python_parse_final(corpus_lis, split_num)
            for i in range(len(qids)):
                total_data.append([qids[i], [parse_acont1[i], parse_acont2[i]], [parse_code[i]], parse_query[i]])
        elif lang_type == 'sql':
            parse_acont1, parse_acont2, parse_query, parse_code, qids = sql_parse_final(corpus_lis, split_num)
            for i in range(len(qids)):
                total_data.append([qids[i], [parse_acont1[i], parse_acont2[i]], [parse_code[i]], parse_query[i]])

    # 将结果写入文件
    with open(save_path, "w") as f:
        f.write(str(total_data))

# 设置语言类型和分割数量
python_type = 'python'
sql_type = 'sql'
words_top = 100
split_num = 1000

# 测试函数，比较不同路径下的数据是否一致
def test(path1, path2):
    """测试函数，用于比较两个文件路径下的数据"""
    with open(path1, "rb") as f:
        # 存储为字典，有序
        corpus_lis1 = pickle.load(f)
    with open(path2, "rb") as f:
        corpus_lis2 = eval(f.read())

    # 输出比较结果
    print(corpus_lis1[10])
    print(corpus_lis2[10])

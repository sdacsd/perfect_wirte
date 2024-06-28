import pickle
from collections import Counter

#读取pickle二进制文件
def load_pickle(filename):
    return pickle.load(open(filename, 'rb'), encoding='iso-8859-1')

#计算一个列表中指定元素的出现次数
#single_list--> count_listElement
def single_list(arr, target):
    return arr.count(target)

#staqc：把语料中的单候选和多候选分隔开
def data_staqc_prpcessing(filepath,single_path,mutiple_path):
    with open(filepath,'r')as f:
        total_data = eval(f.read())
        f.close()
    qids = []
    for i in range(0, len(total_data)):
        qids.append(total_data[i][0][0])
    result = Counter(qids)

    total_data_single = []
    total_data_multiple = []
    for i in range(0, len(total_data)):
        if(result[total_data[i][0][0]]==1):
            total_data_single.append(total_data[i])
        else:
            total_data_multiple.append(total_data[i])
    f = open(single_path, "w")
    f.write(str(total_data_single))
    f.close()
    f = open(mutiple_path, "w")
    f.write(str(total_data_multiple))
    f.close()
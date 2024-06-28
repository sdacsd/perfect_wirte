import pickle

def load_pickle(filename):
    return pickle.load(open(filename, 'rb'), encoding='iso-8859-1')

# 构建初步词典的具体步骤1
# 查找两个文本语料库中的单词并生成词汇表
def get_vocab(filepath1, filepath2):
    word_vacab = set()
    corpora = [filepath1, filepath2]

    for corpus in corpora:
        for data in corpus:
            for i in range(1, 4):
                for j in range(len(data[i][0])):
                    word_vacab.add(data[i][0][j])
                for j in range(len(data[i][1])):
                    word_vacab.add(data[i][1][j])

    print(len(word_vacab))
    return word_vacab

# 构建初步词典
# 从两个文本数据集中获取全部出现过的单词，并将单词保存到文件中
def vocab_prpcessing(filepath1,filepath2,save_path):
    with open(filepath1, 'r')as f:
        total_data1 = eval(f.read())
        f.close()

    with open(filepath2, 'r')as f:
        total_data2 = eval(f.read())
        f.close()

    x1 = get_vocab(total_data1, total_data2)
    #total_data_sort = sorted(x1, key=lambda x: (x[0], x[1]))
    f = open(save_path, "w")
    f.write(str(x1))
    f.close()

# 获取两个文本数据集中出现的单词的集合，
# 并且仅返回在第二个数据集中出现过而未在第一个数据集中出现过的单词的集合
def final_vocab_prpcessing(filepath1,filepath2,save_path):
    word_set = set()
    with open(filepath1, 'r') as f:
        total_data1 = set(eval(f.read()))
        f.close()
    with open(filepath2, 'r') as f:
        total_data2 = eval(f.read())
        f.close()
    total_data1 = list(total_data1)
    x1 = get_vocab(total_data2, total_data2)
    # total_data_sort = sorted(x1, key=lambda x: (x[0], x[1]))
    for i in x1:
        if i in total_data1:
            continue
        else:
            word_set.add(i)
    print(len(total_data1))
    print(len(word_set))
    f = open(save_path, "w")
    f.write(str(word_set))
    f.close()


from sklearn.manifold import TSNE
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
from gensim.models import KeyedVectors

# 将词向量文件转换为二进制格式以提高加载速度
def trans_bin(word_path, bin_path):
    wv_from_text = KeyedVectors.load_word2vec_format(word_path, binary=False)
    # 初始化相似度矩阵
    wv_from_text.init_sims(replace=True)
    # 保存为二进制文件
    wv_from_text.save(bin_path)
    """
    使用以下代码读取二进制文件:
    model = KeyedVectors.load(embed_path, mmap='r')
    """

# 构建新的词典和词向量矩阵
def get_new_dict(type_vec_path, type_word_path, final_vec_path, final_word_path):
    """
    type_vec_path: 预训练词向量文件路径
    type_word_path: 词汇表文件路径
    final_vec_path: 输出词向量文件路径
    final_word_path: 输出词典文件路径
    """
    # 加载预训练词向量模型
    model = KeyedVectors.load(type_vec_path, mmap='r')

    with open(type_word_path, 'r') as f:
        total_word = eval(f.read())

    # 初始化特殊标记
    word_dict = ['PAD', 'SOS', 'EOS', 'UNK']  # 其中0: PAD_ID, 1: SOS_ID, 2: EOS_ID, 3: UNK_ID
    fail_word = []

    # 创建随机数生成器
    rng = np.random.RandomState(None)
    pad_embedding = np.zeros(shape=(1, 300)).squeeze()
    unk_embedding = rng.uniform(-0.25, 0.25, size=(1, 300)).squeeze()
    sos_embedding = rng.uniform(-0.25, 0.25, size=(1, 300)).squeeze()
    eos_embedding = rng.uniform(-0.25, 0.25, size=(1, 300)).squeeze()
    word_vectors = [pad_embedding, sos_embedding, eos_embedding, unk_embedding]

    # 为每个词汇找到其词向量
    for word in total_word:
        try:
            word_vectors.append(model.wv[word])
            word_dict.append(word)
        except KeyError:
            fail_word.append(word)

    # 打印一些统计信息
    print(f"词汇总数: {len(total_word)}")
    print(f"找到的词汇数: {len(word_dict)}")
    print(f"未找到的词汇数: {len(fail_word)}")

    # 将词向量和词典保存到文件
    word_vectors = np.array(word_vectors)
    word_dict = dict(map(reversed, enumerate(word_dict)))

    with open(final_vec_path, 'wb') as file:
        pickle.dump(word_vectors, file)

    with open(final_word_path, 'wb') as file:
        pickle.dump(word_dict, file)

    print("词典和词向量矩阵构建完成")

# 获取词在词典中的位置索引
def get_index(type, text, word_dict):
    location = []
    if type == 'code':
        location.append(1)  # SOS_ID
        len_c = len(text)
        if len_c + 1 < 350:
            if len_c == 1 and text[0] == '-1000':
                location.append(2)  # EOS_ID
            else:
                for i in range(len_c):
                    index = word_dict.get(text[i], word_dict.get('UNK'))
                    location.append(index)
                location.append(2)  # EOS_ID
        else:
            for i in range(348):
                index = word_dict.get(text[i], word_dict.get('UNK'))
                location.append(index)
            location.append(2)  # EOS_ID
    else:
        if not text or text[0] == '-10000':
            location.append(0)  # PAD_ID
        else:
            for word in text:
                index = word_dict.get(word, word_dict.get('UNK'))
                location.append(index)

    return location

# 将训练、测试、验证语料序列化
def Serialization(word_dict_path, type_path, final_type_path):
    """
    word_dict_path: 词典文件路径
    type_path: 输入语料文件路径
    final_type_path: 输出序列化语料文件路径
    """
    with open(word_dict_path, 'rb') as f:
        word_dict = pickle.load(f)

    with open(type_path, 'r') as f:
        corpus = eval(f.read())

    total_data = []

    for entry in corpus:
        qid = entry[0]
        Si_word_list = get_index('text', entry[1][0], word_dict)
        Si1_word_list = get_index('text', entry[1][1], word_dict)
        tokenized_code = get_index('code', entry[2][0], word_dict)
        query_word_list = get_index('text', entry[3], word_dict)
        block_length = 4
        label = 0

        # Padding or truncating sequences
        Si_word_list = Si_word_list[:100] + [0] * (100 - len(Si_word_list))
        Si1_word_list = Si1_word_list[:100] + [0] * (100 - len(Si1_word_list))
        tokenized_code = tokenized_code[:350] + [0] * (350 - len(tokenized_code))
        query_word_list = query_word_list[:25] + [0] * (25 - len(query_word_list))

        one_data = [qid, [Si_word_list, Si1_word_list], [tokenized_code], query_word_list, block_length, label]
        total_data.append(one_data)

    with open(final_type_path, 'wb') as file:
        pickle.dump(total_data, file)

# 将新词添加到词典中并在词向量矩阵中添加相应的词向量
def get_new_dict_append(type_vec_path, previous_dict, previous_vec, append_word_path, final_vec_path, final_word_path):
    """
    type_vec_path: 预训练词向量文件路径
    previous_dict: 之前的词典文件路径
    previous_vec: 之前的词向量文件路径
    append_word_path: 追加的词汇文件路径
    final_vec_path: 输出词向量文件路径
    final_word_path: 输出词典文件路径
    """
    # 加载预训练词向量模型
    model = KeyedVectors.load(type_vec_path, mmap='r')

    with open(previous_dict, 'rb') as f:
        pre_word_dict = pickle.load(f)

    with open(previous_vec, 'rb') as f:
        pre_word_vec = pickle.load(f)

    with open(append_word_path, 'r') as f:
        append_word = eval(f.read())

    word_dict = list(pre_word_dict.keys())
    word_vectors = pre_word_vec.tolist()
    fail_word = []

    # 创建随机数生成器
    rng = np.random.RandomState(None)
    unk_embedding = rng.uniform(-0.25, 0.25, size=(1, 300)).squeeze()

    for word in append_word:
        try:
            word_vectors.append(model.wv[word])
            word_dict.append(word)
        except KeyError:
            fail_word.append(word)

    # 打印一些统计信息
    print(f"原始词汇总数: {len(pre_word_dict)}")
    print(f"追加词汇总数: {len(append_word)}")
    print(f"找到的词汇总数: {len(word_dict)}")
    print(f"未找到的词汇总数: {len(fail_word)}")

    # 将词向量和词典保存到文件
    word_vectors = np.array(word_vectors)
    word_dict = dict(map(reversed, enumerate(word_dict)))

    with open(final_vec_path, 'wb') as file:
        pickle.dump(word_vectors, file)

    with open(final_word_path, 'wb') as file:
        pickle.dump(word_dict, file)

    print("词典和词向量矩阵更新完成")

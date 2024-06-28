# -*- coding: utf-8 -*-
import sqlparse #0.4.2
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer
wnler = WordNetLemmatizer()
from nltk.corpus import wordnet
import re
import inflection

OTHER = 0
FUNCTION = 1
BLANK = 2
KEYWORD = 3
INTERNAL = 4

TABLE = 5
COLUMN = 6
INTEGER = 7
FLOAT = 8
HEX = 9
STRING = 10
WILDCARD = 11
SUBQUERY = 12
DUD = 13

#ttypes-->types
types = {0: "OTHER", 1: "FUNCTION", 2: "BLANK", 3: "KEYWORD", 4: "INTERNAL", 5: "TABLE", 6: "COLUMN", 7: "INTEGER",
         8: "FLOAT", 9: "HEX", 10: "STRING", 11: "WILDCARD", 12: "SUBQUERY", 13: "DUD", }

scanner = re.Scanner([(r"\[[^\]]*\]", lambda scanner, token: token), (r"\+", lambda scanner, token: "REGPLU"),
                      (r"\*", lambda scanner, token: "REGAST"), (r"%", lambda scanner, token: "REGCOL"),
                      (r"\^", lambda scanner, token: "REGSTA"), (r"\$", lambda scanner, token: "REGEND"),
                      (r"\?", lambda scanner, token: "REGQUE"),
                      (r"[\.~``;_a-zA-Z0-9\s=:\{\}\-\\]+", lambda scanner, token: "REFRE"),
                      (r'.', lambda scanner, token: None), ])

#---------------------子函数1：代码的规则--------------------

def string_scanner(s):
    results = scanner.scan(s)[0]
    return results
#---------------------子函数2：代码的规则--------------------
# SQL语句处理
class SqlParser():
    @staticmethod
    #对输入的SQL语句进行清理和标准化
    def formatSql(sql):
        s = sql.strip().lower()
        if not s[-1] == ";":
            s += ';'
        s = re.sub(r'\(', r' ( ', s)
        s = re.sub(r'\)', r' ) ', s)
        words = ['index', 'table', 'day', 'year', 'user', 'text']
        for word in words:
            s = re.sub(r'([^\w])' + word + '$', r'\1' + word + '1', s)
            s = re.sub(r'([^\w])' + word + r'([^\w])', r'\1' + word + '1' + r'\2', s)
        s = s.replace('#', '')
        return s

    #将输入的SQL解析为一个SQL令牌列表,并对其进行处理
    def parseStringsTokens(self, tok):
        if isinstance(tok, sqlparse.sql.TokenList):
            for c in tok.tokens:
                self.parseStringsTokens(c)
        elif tok.ttype == STRING:
            if self.regex:
                tok.value = ' '.join(string_scanner(tok.value))
            else:
                tok.value = "CODSTR"
    #重命名 SQL 语句中的标识符
    def renameIdentifiers(self, tok):
        if isinstance(tok, sqlparse.sql.TokenList):
            for c in tok.tokens:
                self.renameIdentifiers(c)
        elif tok.ttype == COLUMN:
            if str(tok) not in self.idMap["COLUMN"]:
                colname = "col" + str(self.idCount["COLUMN"])
                self.idMap["COLUMN"][str(tok)] = colname
                self.idMapInv[colname] = str(tok)
                self.idCount["COLUMN"] += 1
            tok.value = self.idMap["COLUMN"][str(tok)]
        elif tok.ttype == TABLE:
            if str(tok) not in self.idMap["TABLE"]:
                tabname = "tab" + str(self.idCount["TABLE"])
                self.idMap["TABLE"][str(tok)] = tabname
                self.idMapInv[tabname] = str(tok)
                self.idCount["TABLE"] += 1
            tok.value = self.idMap["TABLE"][str(tok)]

        elif tok.ttype == FLOAT:
            tok.value = "CODFLO"
        elif tok.ttype == INTEGER:
            tok.value = "CODINT"
        elif tok.ttype == HEX:
            tok.value = "CODHEX"

    #将 SQL 解析器对象哈希化
    def __hash__(self):
        return hash(tuple([str(x) for x in self.tokensWithBlanks]))

    #初始化
    def __init__(self, sql, regex=False, rename=True):

        self.sql = SqlParser.formatSql(sql)

        self.idMap = {"COLUMN": {}, "TABLE": {}}
        self.idMapInv = {}
        self.idCount = {"COLUMN": 0, "TABLE": 0}
        self.regex = regex

        self.parseTreeSentinel = False
        self.tableStack = []

        self.parse = sqlparse.parse(self.sql)
        self.parse = [self.parse[0]]

        self.removeWhitespaces(self.parse[0])
        self.identifyLiterals(self.parse[0])
        self.parse[0].ptype = SUBQUERY
        self.identifySubQueries(self.parse[0])
        self.identifyFunctions(self.parse[0])
        self.identifyTables(self.parse[0])

        self.parseStringsTokens(self.parse[0])

        if rename:
            self.renameIdentifiers(self.parse[0])

        self.tokens = SqlParser.getTokens(self.parse)

    @staticmethod

    def getTokens(parse):
        flatParse = []
        for expr in parse:
            for token in expr.flatten():
                if token.ttype == STRING:
                    flatParse.extend(str(token).split(' '))
                else:
                    flatParse.append(str(token))
        return flatParse

    #删除多余空格
    def removeWhitespaces(self, tok):
        if isinstance(tok, sqlparse.sql.TokenList):
            tmpChildren = []
            for c in tok.tokens:
                if not c.is_whitespace:
                    tmpChildren.append(c)

            tok.tokens = tmpChildren
            for c in tok.tokens:
                self.removeWhitespaces(c)

    #识别 SQL 表达式中的子查询
    def identifySubQueries(self, tokenList):
        isSubQuery = False

        for tok in tokenList.tokens:
            if isinstance(tok, sqlparse.sql.TokenList):
                subQuery = self.identifySubQueries(tok)
                if (subQuery and isinstance(tok, sqlparse.sql.Parenthesis)):
                    tok.ttype = SUBQUERY
            elif str(tok) == "select":
                isSubQuery = True
        return isSubQuery

    #用于标识 SQL 解析器对象中的不同类型的文本字面量
    def identifyLiterals(self, tokenList):
        blankTokens = [sqlparse.tokens.Name, sqlparse.tokens.Name.Placeholder]
        blankTokenTypes = [sqlparse.sql.Identifier]

        for tok in tokenList.tokens:
            if isinstance(tok, sqlparse.sql.TokenList):
                tok.ptype = INTERNAL
                self.identifyLiterals(tok)
            elif (tok.ttype == sqlparse.tokens.Keyword or str(tok) == "select"):
                tok.ttype = KEYWORD
            elif (tok.ttype == sqlparse.tokens.Number.Integer or tok.ttype == sqlparse.tokens.Literal.Number.Integer):
                tok.ttype = INTEGER
            elif (tok.ttype == sqlparse.tokens.Number.Hexadecimal or tok.ttype == sqlparse.tokens.Literal.Number.Hexadecimal):
                tok.ttype = HEX
            elif (tok.ttype == sqlparse.tokens.Number.Float or tok.ttype == sqlparse.tokens.Literal.Number.Float):
                tok.ttype = FLOAT
            elif (tok.ttype == sqlparse.tokens.String.Symbol or tok.ttype == sqlparse.tokens.String.Single or tok.ttype == sqlparse.tokens.Literal.String.Single or tok.ttype == sqlparse.tokens.Literal.String.Symbol):
                tok.ttype = STRING
            elif (tok.ttype == sqlparse.tokens.Wildcard):
                tok.ttype = WILDCARD
            elif (tok.ttype in blankTokens or isinstance(tok, blankTokenTypes[0])):
                tok.ttype = COLUMN

    def identifyFunctions(self, tokenList):
        for tok in tokenList.tokens:
            if (isinstance(tok, sqlparse.sql.Function)):
                self.parseTreeSentinel = True
            elif (isinstance(tok, sqlparse.sql.Parenthesis)):
                self.parseTreeSentinel = False
            if self.parseTreeSentinel:
                tok.ttype = FUNCTION
            if isinstance(tok, sqlparse.sql.TokenList):
                self.identifyFunctions(tok)

    def identifyTables(self, tokenList):
        if tokenList.ptype == SUBQUERY:
            self.tableStack.append(False)

        for i in range(len(tokenList.tokens)):
            prevtok = tokenList.tokens[i - 1]
            tok = tokenList.tokens[i]

            if (str(tok) == "." and tok.ttype == sqlparse.tokens.Punctuation and prevtok.ttype == COLUMN):
                prevtok.ttype = TABLE

            elif (str(tok) == "from" and tok.ttype == sqlparse.tokens.Keyword):
                self.tableStack[-1] = True

            elif ((str(tok) == "where" or str(tok) == "on" or str(tok) == "group" or str(tok) == "order" or str(tok) == "union") and tok.ttype == sqlparse.tokens.Keyword):
                self.tableStack[-1] = False

            if isinstance(tok, sqlparse.sql.TokenList):
                self.identifyTables(tok)

            elif (tok.ttype == COLUMN):
                if self.tableStack[-1]:
                    tok.ttype = TABLE

        if tokenList.ptype == SUBQUERY:
            self.tableStack.pop()

    def __str__(self):
        return ' '.join([str(tok) for tok in self.tokens])

    def parseSql(self):
        return [str(tok) for tok in self.tokens]

# 缩略词处理
def revert_abbrev(line):
    # 对句子中的缩写词进行还原，例如 I'm -> I am
    abbrev_dict = {'I\'m': 'I am', 'you\'re': 'you are', 'he\'s': 'he is', 'she\'s': 'she is', 'it\'s': 'it is',
                   'we\'re': 'we are', 'they\'re': 'they are', 'I\'ve': 'I have', 'you\'ve': 'you have',
                   'we\'ve': 'we have', 'they\'ve': 'they have', 'can\'t': 'cannot',
                   'won\'t': 'would not', 'don\'t': 'do not', 'doesn\'t': 'does not',
                   'didn\'t': 'did not', 'haven\'t': 'have not', 'hasn\'t': 'has not',
                   'hadn\'t': 'had not', 'shouldn\'t': 'should not', 'wouldn\'t': 'would not',
                   'mustn\'t': 'must not', 'mightn\'t': 'might not'}
    abbrev_pattern = re.compile(r'\b(' + '|'.join(abbrev_dict.keys()) + r')\b')

    def replace(match):
        return abbrev_dict[match.group(0)]

    return abbrev_pattern.sub(replace, line)

#获取词性
def get_word_pos(tag):
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

#---------------------子函数1：句子的去冗--------------------
# 句子预处理，包括缩写词还原，去除括号内容，转换为下划线命名，去除末尾空格和句号
def preprocess_sentence(line):
    line = revert_abbrev(line)
    line = re.sub(r'[\t\n]+', ' ', line)
    line = inflection.underscore(line)
    line = re.sub(r'\([^\)]*\)', '', line)
    line = line.strip('. ')
    return line

#---------------------子函数1：句子的分词--------------------
# 对文本单词进行处理和清理
def process_words(line):
    # 找单词
    line = re.findall(r"[\w]+|[^\s\w]", line)
    line = ' '.join(line)

    # 替换数字和其他标记
    tag_patterns = [r"\d+(\.\d+)+", r'\"[^\"]+\"', r"0[xX][A-Fa-f0-9]+", r"\s?\d+\s?", r"(?<![A-Z|a-z|_|])\d+[A-Za-z]+"]
    for pattern in tag_patterns:
        line = re.sub(pattern, 'TAG', line)

    # 小写化并进行词性标注、词性还原、词干提取
    cut_words = line.lower().split()
    tags_dict = dict(pos_tag(cut_words))
    wnl = WordNetLemmatizer()
    word_list = []
    for word in cut_words:
        word_pos = get_word_pos(tags_dict[word])
        if word_pos in ['a', 'v', 'n', 'r']:
            # 词性还原
            word = wnl.lemmatize(word, pos=word_pos)
        # 词干提取
        word = wordnet.morphy(word) if wordnet.morphy(word) else word
        word_list.append(word)

    return word_list

# 去除所有非常用符号；防止解析有误
def filter_all_invachar(line):
    line = re.sub('[^(0-9|a-z|A-Z|\-|_|\'|\"|\-|\(|\)|\n)]+', ' ', line)
    # 包括\r\t也清除了
    # 中横线
    line = re.sub('-+', '-', line)
    # 下划线
    line = re.sub('_+', '_', line)
    # 去除横杠
    line = line.replace('|', ' ').replace('¦', ' ')
    return line

# 去除部分非常用符号；防止解析有误
def filter_part_invachar(line):
    line= re.sub('[^(0-9|a-z|A-Z|\-|#|/|_|,|\'|=|>|<|\"|\-|\\|\(|\)|\?|\.|\*|\+|\[|\]|\^|\{|\}|\n)]+',' ', line)
    #包括\r\t也清除了
    # 中横线
    line = re.sub('-+', '-', line)
    # 下划线
    line = re.sub('_+', '_', line)
    # 去除横杠
    line = line.replace('|', ' ').replace('¦', ' ')
    return line

########################主函数：代码的tokens#################################

# 解析 SQL 查询语句，进行文本预处理
def sql_query_parse(line: object) -> object:
    # 过滤特殊符号并合并多余空白字符
    line = re.sub(r'[^\w.\-\t\n]+', ' ', line)
    line = re.sub(r'\.+', '.', line)
    line = re.sub(r'\t+', '\t', line)
    line = re.sub(r'\n+', '\n', line)
    line = re.sub(r' +', ' ', line)
    # 替换小数为统一名称
    line = re.sub(r"\d+(\.\d+)+",'number',line)#新增加 替换小数

    try:
        query = SqlParser(line, regex=True)
        typedCode = query.parseSql()
        typedCode = typedCode[:-1]
        # 骆驼命名转下划线
        typedCode = inflection.underscore(' '.join(typedCode)).split(' ')
        cut_tokens = [re.sub("\s+", " ", x.strip()) for x in typedCode]
        # 全部小写化
        token_list = [x.lower()  for x in cut_tokens]
        # 列表里包含 '' 和' '
        token_list = [x.strip() for x in token_list if x.strip() != '']
        return token_list
    # 存在为空的情况，词向量要进行判断
    except:
        return '-1000'

# 将提供的文本进行标准化和归一化处理,除去所有特殊字符
def sql_all_context_parse(line):
    line = filter_all_invachar(line)
    line = preprocess_sentence(line)
    word_list = process_words(line)
    # 分完词后,再去掉括号
    for i in range(0, len(word_list)):
        if re.findall('[\(\)]', word_list[i]):
            word_list[i] = ''
    # 列表里包含 '' 或 ' '
    word_list = [x.strip() for x in word_list if x.strip() != '']
    # 解析可能为空
    return word_list
# 将提供的文本进行标准化和归一化处理，除去部分特殊字符
def sql_part_context_parse(line):
    line = filter_part_invachar(line)
    line = preprocess_sentence(line)
    word_list = process_words(line)
    # 列表里包含 '' 或 ' '
    word_list = [x.strip() for x in word_list if x.strip() != '']
    # 解析可能为空
    return word_list
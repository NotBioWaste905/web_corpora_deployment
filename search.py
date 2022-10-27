import spacy
import nltk
from tqdm import tqdm
import pandas as pd
import json
from string import punctuation
punctuation = set(punctuation)
punctuation.add('\n')
punctuation.add(' ')
nlp = spacy.load("en_core_web_sm")


with open("indexes.json", 'r', encoding="utf-8") as f,\
        open("texts.json", 'r', encoding="utf-8") as t:
    indexes = json.load(f)
    texts = json.load(t)
data = pd.read_csv("corpus.csv", sep=",", header=None)

# индексация

def index_df(df: pd.DataFrame):
    indexes = {}
    texts = {}
    count = 0

    for review in tqdm(df["review"]):
        texts[count] = review
        review = nlp(review)
        for word in review:
            if word.lemma_ is not None and word.lemma_ not in punctuation:
                if word.lemma_ not in indexes:
                    indexes[word.lemma_] = [count]
                elif word.lemma_ in indexes and count not in indexes[word.lemma_]:
                    indexes[word.lemma_].append(count)
        count += 1

    with open("indexes.json", 'w', encoding="utf-8") as f,\
            open("texts.json", 'w', encoding="utf-8") as t:
        f.write(json.dumps(indexes, ensure_ascii=False, indent=2))
        t.write(json.dumps(texts, ensure_ascii=False, indent=2))

# функция проверяющая слово на соответствие запросу

def check(word: str, query: str):
    word = word.lower()
    if '+' in query:            # для запросов типа 'знать+NOUN'
        w, p = query.split('+')
        w = w.lower()
        # doc = nlp(sent)
        pos = nlp(word)[0].pos_
        lemma = nlp(word)[0].lemma_
        if lemma == w and pos == p:
            return True
        else:
            return False

    elif '"' in query:          # для точных запросов
        w = query.strip('"').lower()
        if word == w:
            return True
        else:
            return False

    elif query.isupper():       # для запросов типа VERB
        pos = nlp(word)[0].pos_
        if pos == query:
            return True
        else:
            return False

    else:                       # для поиска со всеми словоформами
        lemma = nlp(word)[0].lemma_
        w = nlp(query)[0].lemma_
        if lemma == w:
            return True
        else:
            return False


class Searcher:
    def __init__(self, index=indexes, texts=texts, data=data) -> None:
        self.index = index      # индексы текстов
        self.texts = texts      # эээ не помню че это
        self.data = data

    # принимает на вход слово и выдает кортеж (id текстов в которых встречается; сами тексты)
    def get_texts(self, word: str):
        word = word.lower()
        doc = nlp(word)
        for i in doc:
            lemma = i.lemma_
        if lemma in self.index:
            text_ids = [x for x in self.index[lemma]]
            texts_raw = [self.texts[str(x)] for x in self.index[lemma]]

        return text_ids, texts_raw

    def get_meta(self, id):
        return self.data.iloc[id]

    def search(self, query: str):
        '''
        Делим запрос на несколько подзапросов, каждый со своими правилами(?).
        '''
        query = query.split(' ')
        texts_ids_ = set()       # здесь будут храниться id текстов котoрые подходят по набору слов
        output = []

        for part in query:
            # проверяем есть ли слово(?) в первой части запроса, чтобы ограничить число текстов
            if part.islower() or '"' in part or '+' in part:
                word = part.strip('"').split('+')[0]
                if texts_ids_:
                    texts_ids_ = texts_ids_.intersection(
                        set(self.get_texts(word)[0]))
                else:
                    texts_ids_ = set(self.get_texts(word)[0])

        if not texts_ids_:  # если слов в запросе не было, то и тексты мы берем все
            texts_ids_ = set([x for x in self.texts])

        # находим в каждом тексте интересующий нас паттерн
        for txt, id in tqdm([(self.texts[str(x)], x) for x in texts_ids_]):
            sentences = nltk.sent_tokenize(txt)
            for s in sentences:
                left, center, right, text_id = '', '', '', 0  # поля для вывода
                words = [x for x in nltk.word_tokenize(s) if x not in punctuation]
                count = 0
                for i in range(len(words)-len(query)):  # идем по словам
                    # начиная с каждого слова ищем нужный нам паттерн
                    for j in range(len(query)):
                        if check(words[i+count], query[j]):
                            center += words[i+count] + ' '
                            count += 1
                        else:
                            center = ''
                            count = 0
                            break
                    else:   # попадаем сюда в случае, если нужный паттерн найден
                        left = ' '.join(words[:i])
                        right = ' '.join(words[i+len(query):])
                        text_id = id
                        count = 0
                        output.append((left, center, right, text_id))

        return output


# запуск кода для теста
if __name__ == "__main__":
    # data = pd.read_excel("xlsx_corpus.xlsx")
    data = pd.read_csv("corpus.csv", sep=",", header=None)
    # index_df(data)

    with open("indexes.json", 'r', encoding="utf-8") as f,\
            open("texts.json", 'r', encoding="utf-8") as t:
        indexes = json.load(f)
        texts = json.load(t)


    s = Searcher(indexes, texts, data)
    print(s.get_meta(10)["rate"])
    # print(s.search('"bad"'))

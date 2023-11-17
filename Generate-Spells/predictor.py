import math
from nltk import ngrams
from deep_translator import GoogleTranslator
import tqdm
import json
from jellyfish import levenshtein_distance
import pathlib
import sys
import os

path = str(pathlib.Path(__file__).parent.parent.absolute())
sys.path.append(path)

from src.config.logger import logger


SUPERVISE = True
MIN_ACCEPTABLE_PROBIITY = 0.005
MAXIMUM_DIFFERENT_SPELLS_COUNT = 2000
NGRAM_COUNTS = [2, 3, 4]

WANT_4_GRAM = os.environ.get("want_4gram", False) == "yes"
WANT_4_GRAM = True


PROXIES = {"http": "http://82.115.16.187:18001", "https": "http://82.115.16.187:18001", 
"http": "http://82.115.16.187:18003", "https": "http://82.115.16.187:18003"}

def generate_posibles(text):
    letter_list = ['a','o','u','y','i','e','h','w','v',' ','q','k','g','z','j','x','s','t','c']
    if 'w' not in text and 'v' not in text :
        letter_list.remove('v')
    if 'kh' not in text and ('k' not in text and 'q'  not in text and 'c' not in text):
        letter_list.remove('k')
        if 'gh' not in text and 'q' not in text:
            letter_list.remove('q')
            
    if 'j' not in text and 'zh' not in text:
        letter_list.remove('z')
        letter_list.remove('j')
    
    if 'x' not in text and 's' not in text and 'th' not in text and 'c' not in text:
        letter_list.remove('x')
        letter_list.remove('s')
        if 'k' not in text and 'c' and 'q' not in text:
            letter_list.remove('c')
        # letter_list.remove('t')
    
    if 'gh' not in text and 'q' not in text:
        # letter_list.remove('g')
        if 'k' not in text and 'q' in letter_list:
            letter_list.remove('q')
    
    return letter_list


def generate_different_spells(eng_name, probility_dics, left_side_dics, right_side_dics, n, m):
    """
    :What:
        - generate different spells function
    :Args:
        - new_dic (dict)
        - eng_name (str): a firstname or last name that translated to english
        - n (int) : the number of n in ngram
        - all_f_dic1 (dict) : used for creating name compounds from left side
        - all_f_dic2 (dict) : used for creating name compounds from right side
    :Duties:
        - use name that translated to english and do ngram on it,
         take first and last bunch of letters from it,
         then search for all possible letters that mitght come after or
         before that bunch of letters.

    :Returns:
        - new_pos_parts (dict) : builded from left side
            - keys (str) : possible different spells with *, #
            - values (float) : probility of each key

        - new_neg_parts (dict) :  builded from right side
            - keys (str) : possible different spells with *, #
            - values (float) : probility of each key

        - letters1 (list) : list of letters that is not vowel, in filtering true names can be usefull

    """
    all_f_dic_1_ng = left_side_dics[0]
    all_f_dic_2_ng = right_side_dics[0]
    all_f_dic_1_mg = left_side_dics[1]
    all_f_dic_2_mg = right_side_dics[1]

    new_dic_ng = probility_dics[0]
    new_dic_mg = probility_dics[1]

    letters1=[]
    possible_lets=generate_posibles(eng_name)
    for t in eng_name:
        if t not in letters1 and t not in possible_lets:
            letters1.append(t)
    letters1.sort()

    def change_count(n, text):
        if n == 3:
                if (len(text) - n - 1) <= 6:
                    change_count = 2
                else:
                    change_count = 3

        elif n == 2:
            change_count = 2
        else:
            if (len(text) - n - 1) <= 7:
                change_count = 2
            elif (len(text) - n - 1) <= 13:
                change_count = 3
            else:
                change_count = 4
        return(change_count)
    # change_count = 4
    def delelte(part, letters1):
        possible_lets = generate_posibles(part)
        for let in part:
            # if let not in letters1 and let not in ['a','o','u','y','i','e','h','w','v',' ','q','k','g','z','j','x','s']:
            if let not in letters1 and let not in possible_lets:
                return False
        
        return True

    def check_distance(text, word, type):
        text = text[1:-1]
        word = word.replace('*', '')
        word = word.replace('#', '')
        if type == 'neg':
            if len(text)>len(word):
                distance = levenshtein_distance(text[-len(word):], word) 
            else:
                distance = levenshtein_distance(word[-len(text):], text)
            # print(text, word, distance)
    
        elif type == 'pos':
            if len(text)>len(word):
                distance = levenshtein_distance(text[:len(word)], word) 
            else:
                distance = levenshtein_distance(word[:len(text)], text)

        
        if distance <= len(word)//2 :
            return True
        else :
            return False

    def create_word_from_begin(spart, tup1, f_dic1, dic, n, previosprob=None, itr=0):  

        sparts={}
        word=''
        init_word=''
        for let1 in tup1:
            init_word = init_word + let1
        init_word = spart + init_word

        if tup1 in f_dic1:
            for tup2 in f_dic1[tup1]:
                if abs(tup2[1]) > change_count(n, eng_name):
                    continue
                word = init_word

                for ires in range(-tup2[1],0,1):
                    word = word + tup2[0][ires]

                # print((tup1, tuple(tup2[0]), tup2[1]))
            
                
                if (tup1, tuple(tup2[0]), tup2[1]) in dic:


                    if previosprob != None :
                        prob2=dic[(tup1, tuple(tup2[0]), tup2[1])]+previosprob
                        # prob2=math.sqrt(prob2)
                        prob2 = prob2/2
                        

                        if (prob2 > 0.005 and len(sparts) <= 25 - 4 * itr)  and delelte(word, letters1) == True and check_distance(eng_name, word, 'pos') == True:
                    
                            sparts.update( {word : prob2 } )
                

                        
                    elif previosprob == None :
                        prob2 = dic[(tup1, tuple(tup2[0]), tup2[1])]
                        # prob2=math.sqrt(prob2)
                        if (prob2 > 0.005 and len(sparts)<50) and delelte(word, letters1) == True:
                            sparts.update( {word : prob2 } )

                    else:
                        break
                

        return sparts

    def create_word_from_end(epart, tup1, f_dic2, dic, n, previosprob=None, itr=0):
        eparts={}
        word=''

        if tup1 in f_dic2:
            for tup2 in f_dic2[tup1]:
                if abs(tup2[1]) > change_count(n, eng_name):
                    continue
                word=''

                for let2 in tup2[0]:
                    word = word + let2

                for ires in range(-abs(tup2[1]),0,1):
                    word = word + tup1[ires] 
                
                word += epart

                if (tup1, tuple(tup2[0]), tup2[1]) in dic:


                    if previosprob != None :
                        prob2=dic[(tup1, tuple(tup2[0]), tup2[1])]+previosprob
                        # prob2=math.sqrt(prob2)
                        prob2 = prob2/2
                        if (prob2 > 0.005 and len(eparts) <= 25 - 4 * itr) and delelte(word, letters1) == True and check_distance(eng_name, word, 'neg') == True:
                            eparts.update( {word : prob2 } )


                            
                        
                    elif previosprob == None:
                        prob2 = dic[(tup1, tuple(tup2[0]), tup2[1])]
                        # prob2=math.sqrt(prob2)
                        if (prob2 > 0.005 and len(eparts)<50) and delelte(word, letters1) == True:
                            eparts.update( {word : prob2 } )
                    
                    else:
                        break


        return eparts

    def my_func(parts, m, fdic, bdic, x, itr):

        my_dic={}
        # print(len(parts))

        for part, value in parts.items():
            

            if '*' in part and '#' in part :
                ans={part:value}

            else:
            
                if x=='pos' :
                    last_tup=list(ngrams(part,m))[-1]
                    # print(last_tup)
                    ans=create_word_from_begin(spart=part[:-m],tup1=last_tup,f_dic1=fdic, dic=bdic, n=m, previosprob= value, itr= itr)

                elif x=='neg' :
                    first_tup=list(ngrams(part,m))[0]
                    
                    ans=create_word_from_end(part[m:], first_tup, fdic, bdic, m, value, itr)

            for name, val in ans.items():
                if name not in my_dic:

                    my_dic.update({name:val})
                else :
                    my_dic.update({name : (val + my_dic[name])})
        return my_dic


    if len(probility_dics) == 3:
        all_f_dic_1_og = left_side_dics[2]
        all_f_dic_2_og = right_side_dics[2]
        new_dic_og = probility_dics[2]

        ng = list(ngrams(eng_name,2))

        new_pos_parts=create_word_from_begin('', ng[0], all_f_dic_1_og, new_dic_og, 2)          
        new_neg_parts=create_word_from_end('', ng[-1], all_f_dic_2_og, new_dic_og, 2)

        new_pos_parts = my_func(new_pos_parts, n, all_f_dic_1_ng, new_dic_ng, 'pos',0)
        new_neg_parts = my_func(new_neg_parts, n, all_f_dic_2_ng, new_dic_ng, 'neg',0)

        
    else:
        ng = list(ngrams(eng_name,n))
        new_pos_parts=create_word_from_begin('', ng[0], all_f_dic_1_ng, new_dic_ng, n)          
        new_neg_parts=create_word_from_end('', ng[-1], all_f_dic_2_ng, new_dic_ng, n)

    for inn1 in range(4):
        new_pos_parts={k: v for k, v in sorted(new_pos_parts.items(), key=lambda item: item[1],reverse=True)}
        new_pos_parts = my_func(new_pos_parts, m, all_f_dic_1_mg, new_dic_mg, 'pos', inn1)
        if len(new_pos_parts)>15000:
            break
        # print(len(new_pos_parts))

    for inn2 in range(4):
        new_neg_parts={k: v for k, v in sorted(new_neg_parts.items(), key=lambda item: item[1],reverse=True)}
        new_neg_parts = my_func(new_neg_parts, m, all_f_dic_2_mg, new_dic_mg, 'neg', inn2)
        # print(len(new_neg_parts))
        if len(new_neg_parts)>15000:
            break



    return [new_pos_parts, new_neg_parts, letters1]


def recognize_true_different_spells(
    entext, orginal_persian_name, new_pos_parts, new_neg_parts, letters1
):
    """

    :What:
        - recognize true different spells function
    :Args:
        - entext (str): translated name to english
        - orginal_persian_name (str) : orginal name writen in persian language
        - new_pos_parts (dict) : has explained before
        - new_neg_parts (dict) : has explained before
        - letters1 (list) : has explained before
    :Duties:
        - delete * and # from each word
        - we have orginal_persian_name that gives us a chance to compare it with translate of
         each different spells and if they are the same, the word pass

    :Returns:
        - final_dic_of_word (dict) : contain different spells of a name with their probilities

    """

    max_count_of_distance = len(entext) / 2 - 1
    # max_count_of_different_spells = 8*len(entext) - 6
    dic_of_word = {}
    dic_of_word.update({entext[1:-1]: 0.6})

    for word1, value in new_pos_parts.items():
        possible_lets = generate_posibles(word1)
        letters2 = []

        for tf in word1:
            if tf not in letters2 and tf not in possible_lets:
                letters2.append(tf)
        letters2.sort()
        distance = levenshtein_distance(entext[1:-1], word1[1:-1])
        if letters1 == letters2 and distance <= max_count_of_distance:
            if word1[1:-1] not in dic_of_word:
                dic_of_word.update({word1[1:-1]: value / 2})
            else:
                dic_of_word.update(
                    {word1[1:-1]: (dic_of_word[word1[1:-1]] + value) / 2}
                )

    for word2, value in new_neg_parts.items():
        possible_lets = generate_posibles(word2)
        letters2 = []

        for tf in word2:

            if tf not in letters2 and tf not in possible_lets:
                letters2.append(tf)
        letters2.sort()
        distance = levenshtein_distance(entext[1:-1], word2[1:-1])

        if letters1 == letters2 and distance <= max_count_of_distance:
            if word2[1:-1] not in dic_of_word:
                dic_of_word.update({word2[1:-1]: value / 2})
            else:
                dic_of_word.update(
                    {word2[1:-1]: (dic_of_word[word2[1:-1]] + value) / 2}
                )
    if "fr" in dic_of_word:
        dic_of_word.update({"far": 0.9})
    dic_of_word = {
        k: v
        for k, v in sorted(dic_of_word.items(), key=lambda item: item[1], reverse=True)
        if v > 0.005
    }

    return dic_of_word


def fileter(orginal_persian_name, dic_of_word, entext):
    # max_count_of_different_spells = 10*len(entext)
    equivalent_f = {'م':['m'], 'ر':['r'], 'ن':['n'],'ش':['sh'], 'س':['s'], 'ص':['s'], 'ث':['s','th'], 'پ':['p'], 'ت':['t'], 'ط':['t'], 'ز':['z'], 'ض':['z'], 'ظ':['z'], 'ذ':['z'],'ژ':['zh', 'j'], 'ج':['g','j'],'ف':['f'], 'د':['d'],'ل':['l'],  'ک':['k', 'q','ch','c'],'ب':['b'],'ق':['gh','q','g'],'غ':['gh'],'گ':['g'],'خ':['kh'],'چ':['ch']}

    persian_equivalents = {'س':['ص','ث','س'], 'ث':['ص','ث','س'], 'ص':['ص','ث','س'], 'ت':['ت','ط','ث'], 'ط':['ت','ط'] , 'ز':['ض','ز','ظ','ذ'], 'ض':['ض','ز','ظ','ذ'],'ذ':['ض','ز','ظ','ذ'],'ظ':['ض','ز','ظ','ذ'],'ک':['چ','ک'], 'چ':['چ','ک'], 'گ':['گ','ج'], 'ج':['ج','ژ'],'ژ':['ج','ژ'],'ق':['ق','غ','گ','ج'], 'غ':['ق','غ']}
    
    equivalent_e = {'r':['ر'], 'b':['ب'],'d':['د'], 'f':['ف'],'th':['ث'],'ch':['چ','ک'],'gh':['ق','غ'], 'j':['ج', 'ژ'],'zh':['ژ'], 'z':['ز', 'ظ', 'ض', 'ذ'], 't':['ت', 'ط'], 'kh':['خ'], 'sh':['ش'], 's':['ص','س','ث'], 'm':['م'], 'p':['پ'], 'n':['ن'], 'l':['ل'],'k':['ک'],'g':['گ','ج']}

    engs = {}
    fars_let = []
    containing_list = []

    pre_let = ""
    if 'الدین' in orginal_persian_name or 'الله' in orginal_persian_name:
        orginal_persian_name = orginal_persian_name.replace('ال','')
    for let in orginal_persian_name:

        if let in equivalent_f:
            if let not in fars_let:
                fars_let.append(let)
            
            clist = []
            for eq in equivalent_f[let]:
                clist.append(eq)

                if eq not in engs:
                    engs.update({eq: 1})
                else:
                    engs.update({eq: engs[eq] + 1})
            if clist not in containing_list:
                containing_list.append(clist)

        pre_let = let

    fars_let.sort()

    new_fars_let = fars_let
    for let1 in fars_let:
        if let1 in persian_equivalents:
            for eqs in persian_equivalents[let1]:
                if eqs not in new_fars_let:
                    new_fars_let.append(eqs)
    if "سح" in orginal_persian_name:
        new_fars_let.append("ش")
    new_fars_let.sort()

    final_dic = {}
    min_axeptable_score = len(containing_list)

    for word in dic_of_word:
        score = 0
        for clist in containing_list:
            for letter in clist:
                if letter in word:  
                    score += 1
                    break
        if 'x' in word :
            score += 2
        
        if score >= min_axeptable_score :
            engs2 = {}
            a = 0
            pre_let = ""
            word2 = word
            for i in range(len(word)):
                tup = word[i : i + 2]
                if tup in word2 and tup in equivalent_e and len(tup) == 2:
                    if tup not in engs2:
                        engs2.update({tup: len(word2.split(tup)) - 1})

                    word2 = word2.replace(tup, "")

            for let in word2:
                if let != pre_let:
                    if let not in engs2:
                        engs2.update({let: 1})
                    else:
                        engs2.update({let: engs2[let] + 1})
                pre_let = let

            for let in engs:
                if let in engs2:
                    if  (engs[let] >1 and let in equivalent_e and ((equivalent_e[let][0] + equivalent_e[let][0] in orginal_persian_name) or (equivalent_e[let][0] + ' ' + equivalent_e[let][0]) in orginal_persian_name)) :
                        pass
                        
                    elif engs[let] != engs2[let]:
                        a=1
                        break

            if a == 0:
                final_dic.update({word: dic_of_word[word]})

    final_final_dic = {}

    for word in final_dic:
        fars_eq_let = []
        word2 = word
        for lets in equivalent_e:
            if lets in word2:
                for let in equivalent_e[lets]:
                    if let not in fars_eq_let:
                        fars_eq_let.append(let)
                word2 = word2.replace(lets, "")

        fars_eq_let.sort()
        if len(list(set(fars_eq_let) - set(new_fars_let))) == 0:
            final_final_dic.update({word: final_dic[word]})

    final_final_dic = {
        k: v
        for k, v in sorted(
            final_final_dic.items(), key=lambda item: item[1], reverse=True
        )
        if v > 0.005
    }

    count = 0
    final_dic = {}
    for k, v in final_final_dic.items():
        if count < MAXIMUM_DIFFERENT_SPELLS_COUNT:
            final_dic.update({k: v})

        else:
            break
        count += 1

    return final_dic



def translate_per_to_en(text, source, target):
    try:
        translated = GoogleTranslator(source=source, target=target).translate(text)
    except:
        print("try with proxy ...")
        translated = GoogleTranslator(
            source=source, target=target, proxies=PROXIES
        ).translate(text)

    
    return translated


def read_files(ngram_count):
    """
    :What:
        - read files function
    :Args: -

    :Duties:
        - read 6 json files (3 of them are for generate from right side
         3 other are for generate from left side)

    :Returns:
        - firstname (list) : contain right_side, left_side, probility files for firstname
        - lastname (list) : contain right_side, left_side, probility files for lastname

    """

    print(f"start reading from {ngram_count} grams files ...")
    logger.debug(f"start reading from {ngram_count} grams files ...")
    with open(
        f"src/probility_files/Left_Side_Lastname_{ngram_count}g.json",
        "r",
        encoding="utf8",
    ) as file:
        json_object1 = json.load(file)

    with open(
        f"src/probility_files/Right_Side_Lastname_{ngram_count}g.json",
        "r",
        encoding="utf8",
    ) as file:
        json_object2 = json.load(file)

    with open(
        f"src/probility_files/Probility_Lastname_{ngram_count}g.json",
        "r",
        encoding="utf8",
    ) as file:
        json_object3 = json.load(file)

    with open(
        f"src/probility_files/Left_Side_Firstname_{ngram_count}g.json",
        "r",
        encoding="utf8",
    ) as file:
        json_object4 = json.load(file)

    with open(
        f"src/probility_files/Right_Side_Firstname_{ngram_count}g.json",
        "r",
        encoding="utf8",
    ) as file:
        json_object5 = json.load(file)

    with open(
        f"src/probility_files/Probility_Firstname_{ngram_count}g.json",
        "r",
        encoding="utf8",
    ) as file:
        json_object6 = json.load(file)

    def read_json(json_object1, json_object2, json_object3):
        """
        :What:
            - read json function
        :Args:
            - json_object1 (dict): left side json object
            - json_object2 (dict): right side json object
            - json_object3 (dict): probility json object
        :Duties:
            - python does not recognize that the keys are tuples, because of that, this function
             bring the string keys to tuple

        :Returns:
            - right side (dict)
            - left side (dict)
            - probility (dict)

        """

        right_side = {}
        left_side = {}
        probility = {}

        for k, v in json_object1.items():
            left_side.update(
                {
                    tuple(
                        (
                            k[1:-1].replace("(", "").replace(")", "").replace("'", "")
                        ).split(", ")[0:ngram_count]
                    ): v
                }
            )

        for k, v in json_object2.items():
            right_side.update(
                {
                    tuple(
                        (
                            k[1:-1].replace("(", "").replace(")", "").replace("'", "")
                        ).split(", ")[0:ngram_count]
                    ): v
                }
            )

        for k, v in json_object3.items():
            tupllist = []
            for i in range(3):
                if i == 2:
                    tupllist.append(
                        int(
                            k[1:-1]
                            .replace("(", "")
                            .replace(")", "")
                            .replace("'", "")
                            .split(", ")[ngram_count * 2]
                        )
                    )
                else:
                    tupllist.append(
                        tuple(
                            (k[1:-1].replace("(", "").replace(")", "").replace("'", ""))
                            .replace("-", "")
                            .split(", ")[i * ngram_count : (i + 1) * ngram_count]
                        )
                    )

            probility.update({tuple(tupllist): v})

        return [right_side, left_side, probility]

    lastname_dics = read_json(json_object1, json_object2, json_object3)
    firstname_dics = read_json(json_object4, json_object5, json_object6)

    return [firstname_dics, lastname_dics]


[
    [right_side_firstname3, left_side_firstname3, probility_firstname3],
    [right_side_lastname3, left_side_lastname3, probility_lastname3]] = read_files(NGRAM_COUNTS[1])

[
    [right_side_firstname2, left_side_firstname2, probility_firstname2],
    [right_side_lastname2, left_side_lastname2, probility_lastname2]] = read_files(NGRAM_COUNTS[0]) 

if WANT_4_GRAM:
    [[right_side_firstname4, left_side_firstname4, probility_firstname4],
        [right_side_lastname4, left_side_lastname4, probility_lastname4]]=read_files(NGRAM_COUNTS[2])


print("reading finished ... ")
logger.debug("reading finished ... ")
def find_silents(orginal_fars_name, translated_fars_name):
    persian_silents = ['ب','پ','ت','ث','ج','چ','ح','خ','د','ذ','ر','ز','ژ','س','ش','ص','ض','ط','ظ','غ','ف','ق','ک','گ','ل','م','ن','ه']
    persian_equivalents = {'س':['ص','ث','س'], 'ث':['ص','ث','س'], 'ص':['ص','ث','س'], 'ت':['ت','ط'], 'ط':['ت','ط'] , 'ز':['ض','ز','ظ','ذ','ژ'], 'ض':['ض','ز','ظ','ذ','ژ'],'ذ':['ض','ز','ظ','ذ'],'ظ':['ض','ز','ظ','ذ'],'ک':['چ','ک'], 'چ':['چ','ک'], 'گ':['گ','ج','ق','غ'], 'ج':['ج','ژ','ز'],'ژ':['ج','ژ','ز'],'ق':['ق','غ','گ','ج'], 'غ':['ق','غ','گ','ج']}
    orginal_bunch = []
    translated_bunch = []
    for orginal_let in orginal_fars_name:
        if orginal_let in persian_silents:
            if orginal_let in persian_equivalents:
                orginal_bunch.append(persian_equivalents[orginal_let])
            else:
                orginal_bunch.append([orginal_let])

    for tr_let in translated_fars_name:
        if tr_let in persian_silents:
            if tr_let in persian_equivalents:
               translated_bunch.append(persian_equivalents[tr_let])
            else:
                translated_bunch.append([tr_let])
            
    return orginal_bunch == translated_bunch
    
def compare_with_others(orginal_text, translated):
    forms1 = {'آ':'ا', 'ؤ':'و','ی':'ئ'}
    forms2 = {'ا':'آ', 'و':'ؤ','ئ':'ی'}
    other_forms_of_original_text =[]
    for let in orginal_text:
        if let in forms1.keys():
            other_forms_of_original_text.append(orginal_text.replace(let,forms1[let]))
        elif let in forms2.keys():
            other_forms_of_original_text.append(orginal_text.replace(let,forms2[let]))

    if translated in other_forms_of_original_text:
        return True
    else:
        return False

    

    

def tranlator_filter(fars_name, spells):
    final_dic_of_words={}
    text_to_translate=''
    text_to_translate_list=[]
    fars_name_no_space = ''
    for fars_name_splited in fars_name.split():
        fars_name_no_space += fars_name_splited

    for diffrent_spell in spells.keys():
        if len(text_to_translate)<4900:
            text_to_translate +=  diffrent_spell + ' rezaeifar' + "\n"
        else:
            text_to_translate_list.append(text_to_translate)
            text_to_translate=''

    if len(text_to_translate_list) == 0:
        text_to_translate_list=[text_to_translate]

    for text2tr in text_to_translate_list:
        translated1 = translate_per_to_en(text2tr, source='en', target='fa')

        itr=0
        for trtext1 in (translated1.split("\n")):
            translated_splited_from_rezaeifar = trtext1.split(' رضایی فر')[0]
            no_space_translated = ''
            for splited in translated_splited_from_rezaeifar.split():
                no_space_translated += splited

            if translated_splited_from_rezaeifar== fars_name or translated_splited_from_rezaeifar == fars_name_no_space or  fars_name == no_space_translated or fars_name_no_space == no_space_translated or compare_with_others(fars_name, translated_splited_from_rezaeifar):
            # if find_silents(fars_name, translated_splited_from_rezaeifar) or find_silents(fars_name_no_space, translated_splited_from_rezaeifar) or find_silents(fars_name, no_space_translated) or find_silents(fars_name_no_space, no_space_translated):
                if text2tr.split("\n")[itr].split(' rezaeifar')[0] in spells:
                    final_dic_of_words.update({ text2tr.split("\n")[itr].split(' rezaeifar')[0] : spells[text2tr.split("\n")[itr].split(' rezaeifar')[0]] })
            itr+=1
    return final_dic_of_words


def get_ready_to_generate_different_spelling(fatext, translated, type_name):
    """
    :What:
        - get ready to generate different_spelling function
    :Args:
        - fatext (str) : the firstname or lastname writen in persian language
        - type_name (str) : specify that fatext is lastname or firstname
    :Duties:
        - translate persian name to english after some changes on orginal input
        - call generate different spells function and recognize_true_different_spells function and return the results


    :Returns:
        - annot_names (dict) : contain of different spells with their probilities

    """

    global right_side_firstname3, left_side_firstname3, probility_firstname3, right_side_firstname4, left_side_firstname4, probility_firstname4
    global right_side_lastname3, left_side_lastname3, probility_lastname3, right_side_lastname4, left_side_lastname4, probility_lastname4
    l = fatext
    f = fatext
    result = {}
    if type_name == "Last_name":
        list = []
        if len(l.split()) > 2:
            l = l.split()[0] + " " + l.split()[1]
            fatext = fatext.split()[0] + " " + fatext.split()[1]

        try:

            eng_name = translated.lower().split("mohammad hossein ")[1]
        except:
            try:
                eng_name = translated.lower().split("mohammad hussain ")[1]
            except:
                eng_name = translated.lower().split("mohammad hossein")[1]
        if SUPERVISE:
            var_supervise = input(f"IF translation of {fatext} :--> *{eng_name}#, just press Enter, else Enter the right translation ... \n")
            if len(var_supervise.split()) == 0 :
                pass
            else:
                eng_name = var_supervise

        for ename in eng_name.split():
            if len(ename) <= 3 :
                [new_pos_parts, new_neg_parts, letters] = generate_different_spells(
                    "*" + ename + "#",
                    [probility_lastname2,probility_lastname3],
                    [left_side_lastname2, left_side_lastname3],
                    [right_side_lastname2, right_side_lastname3],
                    NGRAM_COUNTS[0],
                    NGRAM_COUNTS[1],

                )
                annot_names = recognize_true_different_spells(
                    "*" + ename + "#", fatext, new_pos_parts, new_neg_parts, letters
                )

            elif len(ename) <= 20 or WANT_4_GRAM == False:
                [new_pos_parts, new_neg_parts, letters] = generate_different_spells(
                    "*" + ename + "#",
                    [probility_lastname3, probility_lastname4, probility_lastname2],
                    [left_side_lastname3, left_side_lastname4, left_side_lastname2],
                    [right_side_lastname3, right_side_lastname4, right_side_lastname2],
                    NGRAM_COUNTS[1],
                    NGRAM_COUNTS[2],
                )
                annot_names = recognize_true_different_spells(
                    "*" + ename + "#", fatext, new_pos_parts, new_neg_parts, letters
                )
            list.append(annot_names)

        if len(list) == 2:
            names = {}
            for name1, val1 in list[0].items():
                for name2, vla2 in list[1].items():
                    if (
                        levenshtein_distance(name1 + name2, eng_name)
                        <= len(eng_name) / 2 + 1
                    ):
                        names.update({name1 + ' ' + name2: (val1 * vla2) / 2})
                    # if len(names)>1000:
                    #     break
            result = fileter(fatext, names, eng_name)
            # result = names
        elif len(list) == 1:
            names = {}
            for name1, val1 in list[0].items():
                if levenshtein_distance(name1, ename) <= len(ename) / 2:
                    names.update({name1: val1})
                # if len(names)>1000:
                #     break
            result = fileter(fatext, names, eng_name)
            if len(result) == 0:
                result = names
            
            # result = names
            


    elif type_name == "First_name":
        list = []


        eng_name = translated.lower().split(" rezaei")[0]
        if SUPERVISE:
            var_supervise = input(f"IF translation of {fatext} :--> *{eng_name}#, just press Enter, else Enter the right translation ... \n")
            if len(var_supervise.split()) == 0 :
                pass
            else:
                eng_name = var_supervise

        splited_english_name = eng_name.split()

        if len(eng_name.split()) >= 2 and (
            splited_english_name[0] == "seyyed" or splited_english_name[0] == "seyed"
        ):
            eng_name = eng_name.split(splited_english_name[0] + " ")[1]
            fatext = fatext.split("سید")[1]

        for ename in eng_name.split():
            if len(ename) <= 3 :
                [new_pos_parts, new_neg_parts, letters] = generate_different_spells(
                    "*" + ename + "#",
                    [probility_firstname2,probility_firstname3],
                    [left_side_firstname2, left_side_firstname3],
                    [right_side_firstname2, right_side_firstname3],
                    NGRAM_COUNTS[0],
                    NGRAM_COUNTS[1],

                )
                annot_names = recognize_true_different_spells(
                    "*" + ename + "#", fatext, new_pos_parts, new_neg_parts, letters
                )

            elif len(ename) <= 20 or WANT_4_GRAM == False:
                [new_pos_parts, new_neg_parts, letters] = generate_different_spells(
                    "*" + ename + "#",
                    [probility_firstname3, probility_firstname4, probility_firstname2],
                    [left_side_firstname3, left_side_firstname4, left_side_firstname2],
                    [right_side_firstname3, right_side_firstname4, right_side_firstname2],
                    NGRAM_COUNTS[1],
                    NGRAM_COUNTS[2],
                )
                annot_names = recognize_true_different_spells(
                    "*" + ename + "#", fatext, new_pos_parts, new_neg_parts, letters
                )
            list.append(annot_names)

        if len(list) == 2:
            names = {}
            for name1, val1 in list[0].items():
                for name2, val2 in list[1].items():
                    if (
                        levenshtein_distance(name1 + name2, eng_name)
                        <= len(eng_name) / 2 + 1
                    ):
                        names.update({name1 + ' ' + name2: (val1 * val2) / 2})
                    # if len(names)>1000:
                    #     break
            result = fileter(fatext, names, eng_name)
            # result = names
        elif len(list) == 1:
            names = {}
            for name1, val1 in list[0].items():
                if levenshtein_distance(name1, ename) <= len(ename) / 2:
                    names.update({name1: val1})
                # if len(names)>1000:
                #     break
            result = fileter(fatext, names, eng_name)
            if len(result) == 0:
                result = names
            # result = names
    
    tr_result = tranlator_filter(fars_name=fatext, spells=result)
    if len(tr_result) == 0:
        tr_result = result


    return tr_result

def pretify(d):
    return json.dumps(d, sort_keys=False, ensure_ascii=False)


def get_name(persian_fname, persian_lname):
    """
    :What:
        - get name function
    :Args:
        - persian_fname (str) : persian firstname
        - persian_lname (str) : persian lastname

    :Duties:
        - call get_ready_to_generate_different_spelling function by both firstname and lastname entry
        - sort final name based on the probility

    :Returns:
        - different spells (dict) :
            keys (str) : firstname and lastname
            values (float) : probility

    """
    persian_f = persian_fname + " " + "رضایی"
    persian_l = "محمدحسین" + " " + persian_lname
    fullname = persian_f + '\n' + persian_l

    seyed_flag = 'سید' in persian_fname
    
    translated = translate_per_to_en(fullname, source='fa', target='en').split('\n')
    english_fname = translated[0]
    english_lname = translated[1]


    different_spells = {}
    
    fspells = get_ready_to_generate_different_spelling(persian_fname, english_fname, "First_name")

    lspells = get_ready_to_generate_different_spelling(persian_lname, english_lname, "Last_name")


    have_space = len(list(fspells.keys())[0].split()) >= 2
    if have_space:
        max_lenght = 10
    else:
        max_lenght = 5
    
    final_firstname_list = []
    for ifirst, firstname in enumerate(list(fspells.keys())[:10]):
        # final_firstname_list.append(firstname)
        new_firstname = ''
        if have_space :
            for name in firstname.split():
                new_firstname += name

        if new_firstname not in final_firstname_list and new_firstname != '' and  len(final_firstname_list)<max_lenght:
            final_firstname_list.append(new_firstname)

        if firstname not in final_firstname_list and firstname != '' and  len(final_firstname_list)<max_lenght:
            final_firstname_list.append(firstname)
        
    have_space = len(list(lspells.keys())[0].split()) >= 2
    if have_space:
        max_lenght = 10
    else:
        max_lenght = 5

    final_lastname_list = []
    for ilast, lastname in enumerate(list(lspells.keys())[:10]):
        # final_lastname_list.append(lastname)
        new_lastname = ''
        if have_space:
            for name in lastname.split():
                new_lastname += name
        
        if new_lastname not in final_lastname_list and new_lastname != '' and  len(final_lastname_list)<max_lenght:
            final_lastname_list.append(new_lastname)
        if lastname not in final_lastname_list and lastname != '' and  len(final_lastname_list)<max_lenght:
            final_lastname_list.append(lastname)

            

    i = 0
    for firstname in final_firstname_list:
        j = 0

        for lastname in final_lastname_list:

            different_spells.update({firstname + " " + lastname: i + j })
            j += 1
        i += 1

    different_spells = {
        k: v
        for k, v in sorted(
            different_spells.items(), key=lambda item: item[1], reverse=False
        )
    }
    
    # return fspells, lspells, 1
    return final_firstname_list[:10], final_lastname_list[:10], seyed_flag, list(different_spells.keys())[:50]
    # return list(fspells.keys())[:5], list(lspells.keys())[:5], 1

print(get_name('الهام','امیرفیروزکوهی'))


from nltk import ngrams
import tqdm
import json

import pathlib
import sys
import os

path = str(pathlib.Path(__file__).parent.parent.absolute())
sys.path.append(path)


proxies = {"http": "http://82.115.16.187:18001", "https": "http://82.115.16.187:18001"}



def read_names_file(filename):
    """
    :What:
        - read names function
    :Args:
        - filename (str): specify what kind of name we want to read from (firstname or lastname)
    :Duties:
        - read from kind of name that we want to make_probility from that and
        put (*, #) at begining and end of each name and save them to dictionary

    :Returns:
        - all_fl_names (dict) : contain names with *, # and their repetetion

    """

    all_fl_names = {}
    if filename == "Lastname":
        with open("src/lastname.json", encoding="utf8") as file:
            l = file.read()
        with open("src/firstname.json", encoding="utf8") as file:
            f = file.read()

        last_name = json.loads(l)
        first_name = json.loads(f)

        for k1, v1 in last_name.items():
            if '"' not in k1 and "'" not in k1 and "." not in k1 and "-" not in k1:
                all_fl_names.update({"*" + k1 + "#": v1})

        for k2, v2 in first_name.items():
            if '"' not in k2 and "'" not in k2 and "." not in k2 and "-" not in k2:
                if "*" + k2 + "#" not in all_fl_names:
                    all_fl_names.update({"*" + k2 + "#": v2})

    if filename == "Firstname":
        with open("src/firstname.json", encoding="utf8") as file:
            f = file.read()

        first_name = json.loads(f)

        for k2, v in first_name.items():
            if '"' not in k2 and "'" not in k2 and "." not in k2 and "-" not in k2:
                all_fl_names.update({"*" + k2 + "#": v})

    return all_fl_names


class assinging_probilities:
    """
    :What:
        - assign problity class
    :Args:
        - ngram_count (int) : the number of n in ngram
        - name2train (dict) : A dictionary of names with their repetetion

    :Duties:
        - create_ngram from names and save the count of their repetition
        - calculate the probility of occuring each tuple
        - split positive distances from negetive distances
        - The final goal is making 3 dictionary that used in predictor.py to predict

    :Returns:
        - new_dic (dict) :
            - keys (tuple) : ngram results
            - values (float) : value of probility

        - all_f_dic1 (dict) :
            - keys (tuple) : contain bunch of letters
            - values (list) : a list of tuples that contain bunch of letters and the amount of their positive distances from their keys
        - all_f_dic2 (dict) :
            - keys (tuple) : contain bunch of letters
            - values (list) : a list of tuples that contain bunch of letters and the amount of their negetive distances from their keys


    """

    def __init__(self, name2train, ngram_count):
        self.name2train = name2train
        self.ngram_count = ngram_count

    def create_ngrams(self, names, n):
        """
        :What:
            - create ngram function
        :Args:
            - names (dict):
                - keys (str) : person first or lastname
                - values (int) : person first or lastname's reprtition in database
        :Duties:
            - Do ngram
            - make dictionary that show us the repetition of occuring tuple of letters after other tuple of letters
             with their distances

        :Returns:
            - dic_ll (dict) :
                - keys (tuple) : for example : (('a','l'),('l','i'),1)
                - values (int) : show the count of their keys

            - first_dic (dict) :
                - keys (tuple) : for example ('a','l')
                - values (list) : all possible bunch of letters that may happen after or before it's key
                 and their probility is greater than 0.01

        """
        dic_ll = {}
        first_dic = {}
        for name, value in names.items():
            ngram = list(ngrams(name, n))

            for ig1, gr1 in enumerate(ngram):
                for ig2, gr2 in enumerate(ngram):

                    if ig2 == ig1 or abs(ig2 - ig1) > n:
                        continue

                    if (gr1, gr2, (ig2 - ig1)) not in dic_ll:
                        dic_ll.update({(gr1, gr2, (ig2 - ig1)): 1 * value})

                    else:
                        count = dic_ll[(gr1, gr2, (ig2 - ig1))] + 1 * value
                        dic_ll.update({(gr1, gr2, (ig2 - ig1)): count})

                    if (gr1, (ig2 - ig1)) not in first_dic:
                        first_dic.update({(gr1, (ig2 - ig1)): 1 * value})

                    else:
                        count = first_dic[(gr1, (ig2 - ig1))] + 1 * value
                        first_dic.update({(gr1, (ig2 - ig1)): count})

        return [dic_ll, first_dic]

    def calculate_probility(self):
        """
        :What:
            - claculate probility function
        :Args: internal arguments :
            - self.name2train (dict)
            - self.ngram_count (int)

        :Duties:
            - calculating probilty of occuring bunch of letters after or before other bunch of letters

        :Returns:
            - new_dic (dict) :
                - keys (tuple) : tuple of two bunchs of letters and a distance amount
                - values (float) : value of probility

        """

        [dic_ll, first_dic] = self.create_ngrams(self.name2train, self.ngram_count)
        print("create ngram done!")
        new_dic = {}

        for dic in tqdm.tqdm(dic_ll):

            if dic[2] > 0:
                count = first_dic[(dic[0], dic[2])]
                whole = dic_ll[dic]
                prob = whole / count
                if prob > 1:
                    print(dic)
                    print(whole)
                    print(count)
                if prob > 0.005:
                    new_dic.update({dic: round(prob, 3)})

            # for tups in secon_dic:
            elif dic[2] < 0:

                count = first_dic[(dic[0], dic[2])]
                whole = dic_ll[dic]
                prob = whole / count

                if prob > 1:
                    print(dic)
                    print(whole)
                    print(count)

                if prob > 0.005:
                    new_dic.update({dic: round(prob, 3)})

        return new_dic

    def split_pos_distance_from_neg_distance(self, new_dic):
        """
        :What:
            - split positive distances from negetive distances function
        :Args:
            - new_dic (dict)
        :Duties:
            - each bunch of letter has few occurence after or before other bunch of letters, so
            this fuction arranges all occurence after or before a special bunch of letters to a list


        :Returns:
            - all_f_dic1 (dict) :
                - keys (tuple) : contain bunch of letters
                - values (list) : a list of tuples that contain bunch of letters and the amount of their positive distances from their keys
            - all_f_dic2 (dict) :
                - keys (tuple) : contain bunch of letters
                - values (list) : a list of tuples that contain bunch of letters and the amount of their negetive distances from their keys

        """
        all_f_dic1 = {}
        all_f_dic2 = {}

        for tupls1 in tqdm.tqdm(new_dic):
            x = 0
            y = 0
            sames_of_max_prob1 = []
            sames_of_max_prob2 = []

            if tupls1[0] not in all_f_dic1:

                for tupls2 in new_dic:
                    if tupls2[2] > 0:
                        if tupls1[2] > 0:
                            if tupls2[0] == tupls1[0]:
                                if tupls2[1:] not in sames_of_max_prob1:
                                    sames_of_max_prob1.append(tupls2[1:])
                                    x = 1
                if x == 1:
                    all_f_dic1.update({tupls1[0]: sames_of_max_prob1})

            if tupls1[0] not in all_f_dic2:
                for tupls2 in new_dic:
                    if tupls2[2] < 0:
                        if tupls1[2] < 0:
                            if tupls2[0] == tupls1[0]:
                                if tupls2[1:] not in sames_of_max_prob2:
                                    sames_of_max_prob2.append(tupls2[1:])
                                    y = 1
                if y == 1:
                    all_f_dic2.update({tupls1[0]: sames_of_max_prob2})

        return [all_f_dic1, all_f_dic2]


print("start training ... \n")


def start_determine_probs(all_fl_names, filename, ngram_count):
    """
    :What:
        - start to determine probs function
    :Args:
        - all_fl_names (dict): has explained before
        - filename (str) : specify that we want to train from lastname file or firstname file
    :Duties:
        - call assining_probilities class
        - sort the results and pass 2500 of them to  split_pos_distance_from_neg_distance function each time (to decrease runtime)
        - save the results to dictionaries and the save them into 3 file in json format.

    """

    my_class = assinging_probilities(all_fl_names, ngram_count)
    new_dic = my_class.calculate_probility()
    new_dic = {
        k: v for k, v in sorted(new_dic.items(), key=lambda item: item[1], reverse=True)
    }

    all_f_dic1 = {}
    all_f_dic2 = {}
    for i in tqdm.tqdm(range(0, len(new_dic), 3000)):
        newd = dict((k, v) for k, v in list(new_dic.items())[i : i + 3000])

        [f_dic1, f_dic2] = my_class.split_pos_distance_from_neg_distance(newd)

        for dic1 in f_dic1:
            if dic1 in all_f_dic1:
                all_f_dic1.update(
                    {dic1: list(dict.fromkeys(all_f_dic1[dic1] + f_dic1[dic1]))}
                )
            else:
                all_f_dic1.update({dic1: f_dic1[dic1]})

        for dic2 in f_dic2:
            if dic2 in all_f_dic2:
                all_f_dic2.update(
                    {dic2: list(dict.fromkeys(all_f_dic2[dic2] + f_dic2[dic2]))}
                )
            else:
                all_f_dic2.update({dic2: f_dic2[dic2]})

    data1 = dict((str(k), v) for k, v in all_f_dic1.items())
    data2 = dict((str(k), v) for k, v in all_f_dic2.items())
    json_obj1 = json.dumps(data1)
    json_obj2 = json.dumps(data2)
    if os.path.exists("src\\probility_files") :
        pass
    else:
        os.mkdir("src\\probility_files")
    
    with open(
        f"src\\probility_files\\Left_Side_{filename}_{ngram_count}g.json", "w"
    ) as outfile:
        outfile.write(json_obj1)
    with open(
        f"src\\probility_files\\Right_Side_{filename}_{ngram_count}g.json", "w"
    ) as outfile:
        outfile.write(json_obj2)

    my_new_dic = dict((str(k), v) for k, v in new_dic.items())
    json_obj3 = json.dumps(my_new_dic)
    with open(
        f"src\\probility_files\\Probility_{filename}_{ngram_count}g.json", "w"
    ) as outfile:
        outfile.write(json_obj3)

    return True


# all_fl_firstname = read_names_file("Firstname")
# start_determine_probs(all_fl_firstname, "Firstname", 3)

# all_fl_lastname = read_names_file("Lastname")
# start_determine_probs(all_fl_lastname, "Lastname", 3)

# all_fl_firstname = read_names_file("Firstname")
# start_determine_probs(all_fl_firstname, "Firstname", 4)

# all_fl_lastname = read_names_file("Lastname")
# start_determine_probs(all_fl_lastname, "Lastname", 4)

all_fl_firstname = read_names_file("Firstname")
start_determine_probs(all_fl_firstname, "Firstname", 2)

all_fl_lastname = read_names_file("Lastname")
start_determine_probs(all_fl_lastname, "Lastname", 2)

print("finished ...\n ")

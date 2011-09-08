#Retardifies any text.
#Output is converted to lowercase and given various word, letter combination, and suffix replacements.

import re
import random

wordrepl = {
            "love": "luv",
            "love": "luvz",
            "the": "da",
            "there": "dere",
            "are": "r",
            "you": "u",
            "you'll": "u'll",
            "my": "mai",
            "cool": "kewl",
            "now": "meow",
            "please": "pleez",
            "baby": "babeh",
            "kitty": "kitteh",
            "enough": "enuff",
            "lazy": "lazee",
            "yeah": "ya",
            "oh": "o",
            "stupid": "stoopid",
            "done": "dun",
            "cat": "kitteh",
            "you're": "ur",
            "cheese": "cheez",
            "wrote": "rote",
            "like": "liek",
            "from": "frum",
            "really": "rly",
            "june": "joon",
            "hi": "hai",
            "thing": "ting",
            "that": "dat",
            "that's": "dat's",
            "at": "@",
            "with": "wid",
            "they": "dey",
            "here": "hurr",
            "heart": "hart",
            "don't": "dun't",
            "there's": "dere's",
            "there'll": "dere'll",
            "that's": "dat's",
            "that'll": "dat'll",
            "have": "hav",
            "does": "duz",
            "how": "hao",
            "was": "wuz",
            "none": "nun",
            "some": "sum",
            "is": "iz",
            "more": "moar",
            "of": "ov",
            "it's": "it'z",
            "for": "foar",
            "maybe": "mayb",
            "do": "dew",
            "and": "n",
            "can": "kan",
            "guys": "gaiz",
            "hot": "hawt",
            "when": "wen",
            "had": "hadd",
            "because": "cuz",
            "cause": "cuz",
            "just": "jus",
            "look": "luk",
            "what": "wut",
            "come": "kum",
            "came": "kaym",
            "wrong": "rong",
            "have to": "havta",
            "know": "kno",
            "ask": "ax",
            "asked": "axed",
            "be": "b",
            "write": "rite",
            "read": "reed",
            "see": "c",
            "through": "threw",
            "one": "wun",
            "any": "n e",
            "next": "nex",
            "been": "ben",
            "anyone": "n e wun",
            "anybody": "n e body",
            "someone": "sumwun",
            "this": "dis",
            "by": "bai",
            "though": "dow",
            "them": "dem",
            "bye": "bai",
            "day": "dai",
            "favorite": "favoarit",
            "before": "bfoar",
            "easy": "eezy",
            "well": "wel",
            "then": "den",
            "than": "den",
            "to": "2",
            "too": "2",
            "why": "y",
            "computer": "compooper",
            "people": "ppl",
            "every": "evry",
            "these": "deze",
            "those": "doze",
            "thanks": "thx",
           }

innerrepl = {
             "friend": "fwend",
             "ies": "eez",
             "thank": "tank",
             "ould": "ud",
             "ll": "l",
             "iel": "eel",
             "thing": "ting",
             "ain": "ayn",
             "ane": "ayn",
             "ame": "aym",
             "qu": "kw",
             "aim": "aym",
             "doc": "dok",
             "ail": "ayl",
             "alk": "awk",
             "know": "now",
             "ord": "awd",
             "beaut": "byoot",
             "your": "ur",
             "ood": "ud",
             "ake": "ayk",
             "ith": "idd",
             "eed": "eeed",
             "thi": "ti",
             "ight": "ite",
             "uck": "uk",
             "mount": "maont",
             "few": "fyoo",
             "ost": "oast",
             "adj": "aj",
             "iew": "yoo",
             "ss": "zz",
             "tion": "shun",
            }

suffixrepl = {
              "s": "z",
              "er": "a",
              "or": "uh",
              "le": "ull",
              "ed": "d",
              "al": "ull",
              "all": "ull",
              "ule": "yool",
              "ing": "in",
              "low": "lo",
              "ent": "int",
              "ape": "aep",
              "ate": "ayt",
              "ude": "ood",
              "uce": "ooss",
              "rry": "wwy",
              "oop": "ewp",
              "east": "eest",
              "ity": "itee",
              "uch": "utch",
              "icy": "icee",
              "ay": "ai",
              "ect": "ek",
              "ly": "li",
             }

smilies = [":)", "xD", ":P", ":p", "(:", ":D", ":DDD", "=D", ":3", "^_^", "^__^;", "<3", "D:", ";D", "D;"]

class Retardify(object):
    def word_replace(self, text):
        for k, v in wordrepl.iteritems():
            text=re.sub(r"\b%s\b" % k, r"%s" % v, text)
        return text

    def inner_replace(self, text):
        for k, v in innerrepl.iteritems():
            text=re.sub(r"%s" % k, r"%s" % v, text)
        return text

    def suffix_replace(self, text):
        for k, v in suffixrepl.iteritems():
            text=re.sub(r"(\w{2,})(%s)\b" % k, r"\1%s" % v, text)
        return text

    def random_smilie(self):
        return random.choice(smilies)

    def transform(self, text, smilies=False):
        """If smilies is set, a single smilie is added to the end of the text.
        For customization of smilie placement, simply call self.random_smilie() where you want them."""
        newtext=self.word_replace(text.lower())
        newtext=self.inner_replace(newtext)
        newtext=self.suffix_replace(newtext)
        if smilies==True:
            newtext+=" "+self.random_smilie()
        return newtext


if __name__=="__main__":
    text=raw_input("Text:\n")
    print ""
    retard=Retardify()

    print retard.transform(text, smilies=True)

#!/usr/bin/env python

# Original code borrowed from "hrs" at https://github.com/hrs/Markov-Sentence-Generator
# Sentence generator was made OO, to make it easier to call for varying corpora.
# This was originally used for the purpose of making semi-intelligent chatbots.
#
# Some of this is a bit of a mess and works by magic.
# 
# A few additional edits were made to fit my uses, including:
# - An optional fix for frequent periods (which may be caused by the newline swapping)
# - An optional sentence generation argument of a list of starter_words. There is a chance of one of those words being used as a starter word. Not too useful; I do not recommend using this.
# - An option to make sentences a bit more proper, via capitalizations.
# - An option to randomly insert paragraph breaks, to make longer messages look a bit more legitimate.
# - An optional replacement of newlines with periods (for people who chat and make constant newlines)

import re, random, sys, itertools

class MarkovSentences(object):
    def __init__(self, brain, chain_length, newline_fix=False):
        self.chain_length=chain_length
        self.tempMapping = {}
        self.mapping = {}
        self.starts = []
        self.buildMapping(self.wordlist(brain, newline_fix), chain_length)
    
    def fixFrequentPeriods(self, L, repeating=1):
        """This is used due to newline overuse of IRC/Skype chatters. I recommend newlines to be converted to periods for chat logs.
        What this does is strip periods if n or more are detected in a row with one-word lines."""
        ret = []
        for is_trailing, group in itertools.groupby(L, key=lambda x: x.endswith(".")):
            if is_trailing:
                group = list(group)
                if len(group) > repeating:
                    #repeating = maximum repetitions of the period
                    ret.extend(x[:-1] for x in group)
                else:
                    ret.extend(group)
            else:
                ret.extend(group)
        return ret

    def newlineToPeriod(self, word):
        """Replaces all newlines with periods. This may or may not be good for what you want."""
        if "\n" in word:
            word="."
        word=word.lstrip()
        return word

    def toHash(self, lst):
        return tuple(lst)

    def wordlist(self, brain, newline_fix=False):
        f = open(brain, "r")
        if newline_fix == True:
            wordlist = [self.newlineToPeriod(w) for w in re.findall(r"[\w:;'\"<>]+|\n|[_^()~*.,!?]", f.read())]
        else:
            wordlist = [w for w in re.findall(r"[\w:;'\"<>]+|\n|[_^()~*.,!?]", f.read())]
        f.close()
        return wordlist

    def addItemToTempMapping(self, history, word):
        while len(history) > 0:
            first = self.toHash(history)
            if first in self.tempMapping:
                if word in self.tempMapping[first]:
                    self.tempMapping[first][word] += 1.0
                else:
                    self.tempMapping[first][word] = 1.0
            else:
                self.tempMapping[first] = {}
                self.tempMapping[first][word] = 1.0
            history = history[1:]

    # Building and normalizing the mapping.
    def buildMapping(self, wordlist, chain_length):
        """Creates frequently mappings and list of starter words. Generate this only once for your 'brain' text."""
        self.starts.append(wordlist[0])
        for i in range(1, len(wordlist) - 1):
            if i <= chain_length:
                history = wordlist[: i + 1]
            else:
                history = wordlist[i - chain_length + 1 : i + 1]
            follow = wordlist[i + 1]
            if follow not in ".,!?:; " and len(follow) > 3:
                self.starts.append(follow)
            self.addItemToTempMapping(history, follow)
        # Normalize the values in tempMapping, put them into mapping
        for first, followset in self.tempMapping.iteritems ():
            total = sum(followset.values())
            # Normalizing here:
            self.mapping[first] = dict([(k, v / total) for k, v in followset.iteritems()])

    # Returns the next word in the sentence (chosen randomly), given the previous ones.
    def next(self, prevList):
        sum = 0.0
        retval = ""
        index = random.random()
        # Shorten prevList until it's in mapping
        while self.toHash(prevList) not in self.mapping:
            try:
                prevList.pop(0)
            except IndexError:
                return False
        # Get a random word from the mapping, given prevList
        for k, v in self.mapping[self.toHash(prevList)].iteritems():
            sum += v
            if sum >= index and retval == "":
                retval = k
        return retval

    def genMessage(self, message_length=20, line=None, paragraph_chance=None, starter_words=None, proper_sentences=False, input_only=False, fix_periods=False):
        """Generates a message based on a brain, and possibly a random word selected from line input.

        Keyword arguments:

        message_length (int) -- approximate length of the message you want to produce
        line (string) -- an inputted line, of which a single word 4 or more letters long will be randomly selected for use
        paragraph_chance (int) -- there will be a 1/paragraph_chance of inserting "\n\n" at the end of a sentence if this is set, otherwise the message will appear as one paragraph
        starter_words (list) -- a list of strings, which will be used in the event the line input cannot be used to generate a message. you must manually verify that these strings are already valid in the brain. only recommended for use in chatbots.
        proper_sentences (bool) -- set this to True to capitalize the first letter of every sentence and capitalize all 'I' and 'I' contractions
        input_only (bool) -- force only use of the line input; None will be returned if a message cannot be generated. not recommended.
        fix_periods (bool) -- remove periods if they appear in a format similar to "how. are. you." due to conversion of newlines to periods. only recommended for use in chatbots.

        If no line is inputted, or the line is too short, or if the word selected is not in the brain, it will use a random word from the brain to start with, or if given, possibly a random word from a list of starter_words.
        """
        if len(line) < 2:
            #if not using an inputted line as starter text, or if the line is too short, use a random starter
            curr = random.choice(self.starts)
        if line != None:
            #curr = random.choice(self.starts)
            if starter_words:
                if len(curr) < 4:
                    curr = random.choice(starter_words)
                else:
                    try:
                        curr = random.choice(line.split())
                    except IndexError:
                        curr = random.choice(self.starts)
            else:
                try:
                    curr = random.choice(line.split())
                except IndexError:
                    curr = random.choice(self.starts)

            if input_only==True:
                #override using starter_words or starter words
                curr=random.choice(line.split())

        sent = curr
        prevList = [curr]
        words = 0
        finish_sentence = 0
        punctuation = [".", "!", ":", "?", ",", "(", ")", "<", ">", ";", "~", "^", "_", "*"]

        # Add words until sentence max, then continue until we hit a period
        while words <= message_length or finish_sentence==1:
            currword = self.next(prevList)
            if currword==False:
                #self.next() will return False if there are no instances of the selected word in the brain, or no instance of one being followed by any other word
                if input_only==True:
                    #if the selected starter word does not work, and if input_only was selected, stop here
                    return None
                if starter_words and random.randint(1,3)==1:
                    #if specific starter_words were given + a 33% chance, use those. otherwise use something from the brain to start with.
                    #33% chosen for the purpose of creating ample variety. if your list of starter_words is long enough, feel free to change 1/3 to 1/2 or 1/1.
                    curr = random.choice(starter_words)
                else:
                    curr = random.choice(self.starts)
                sentwords=sent.split()
                if ":" not in sentwords[-1] and ";" not in sentwords[-1]:
                    del sentwords[-1]
                sent = " ".join(sentwords)
                sent += " "+curr
                prevList = [curr]
                continue

            prevList.append(currword)
            try:
                if (prevList[-1] == prevList[-2]) and (not any(x in prevList[-1] for x in punctuation)):
                    #remove duplicates, and stop here if one is detected
                    sentwords=sent.split()
                    currword=self.next(prevList)
                    sent=" ".join(sentwords)
                    continue
            except:
                continue

            # if the prevList has gotten too long, trim it
            if len(prevList) > self.chain_length:
                prevList.pop(0)
            if (currword not in ".,!?"):
                sent += " " # Add spaces between words (but not punctuation)
            if currword == ".":
                if any(x in sent[-1] for x in punctuation):
                    continue
            if (":" in currword or ";" in currword) and (len(currword)<4):
                sent+=currword.upper()
            else:
                sent += currword
            words += 1
            if words==message_length:
                finish_sentence=1

            if finish_sentence==1:
                if sent[-1] == ".":
                    break

        sentwords=sent.split()
        if fix_periods == True:
            sentwords=self.fixFrequentPeriods(sentwords, repeating=1)
            sent=" ".join(sentwords)
        message=sent.lstrip()
        message=re.sub(r"[()]", "", message) #parentheses never play well, at least with the current logic
        if proper_sentences == True:
            sentences=re.split(r"([.!?]\s*)", message)[:-1] #for some reason the end element is always empty, hence the [:-1]
            message="".join([sentence[0].upper()+sentence[1:] for sentence in sentences]) #str.capitalize() doesn't work here, since it makes following letters lowercase
            words=message.split()
            i_words=["i", "i'm", "i've", "i'd", "i'll"]
            message=" ".join([word.capitalize() if any(i_word==word.lower() for i_word in i_words) else word for word in words]) #this one's a doozy
        if paragraph_chance:
            #"paragraph" creations; can make longer messages look more legitimate
            sentences=re.split(r"([.!?]+\s*)", message)[:-1]
            message=""
            for item in sentences:
                if ("." in item or "!" in item or "?" in item) and (random.randint(1, paragraph_chance)==1) and (item != sentences[-1]):
                    message+=item+"\n\n"
                else:
                    message+=item
        return message


if __name__ == "__main__":
    message_length=30
    brain = "brain.txt" #brain = the location of the corpus
    chain_length=2 #I recommend a chain length of 2 for more original sentences
    markov=MarkovSentences(brain, chain_length, newline_fix=True)
    text=raw_input("Text: ")
    message=markov.genMessage(message_length, line=text, proper_sentences=True, paragraph_chance=5)
    print message

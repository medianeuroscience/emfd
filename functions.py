# Functions to use for Dictionary Creation 
import pandas as pd
import numpy as np

# Plotting
from matplotlib import pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# NLP
import spacy, re, fnmatch 
nlp = spacy.load('en')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from string import punctuation
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
nltk_stopwords = stopwords.words('english')
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from spacy.lang.en.stop_words import STOP_WORDS

def make_wordclouds(mnl):
    
    fs = [x for x in mnl.foundation.unique()]
    frames = []
    for f in fs:
        frames.append(mnl[mnl.foundation == f])

    def blue_color_func(word, font_size, position,orientation,random_state=None, **kwargs):
        return("hsl(230,100%%, %d%%)" % np.random.randint(49,51))

    def red_color_func(word, font_size, position,orientation,random_state=None, **kwargs):
        return("hsl(350,100%%, %d%%)" % np.random.randint(49,51))

    for frame in frames:

        if frame.foundation.unique()[0].split('.')[1] == 'virtue':
            f = frame.sort_values(frame.foundation.unique()[0],ascending=False).head(50).set_index('word').T.to_dict()
            freq = {}
            for k,v in f.items():
                freq[k] = v[frame.foundation.unique()[0]]

            wc = WordCloud(background_color="white", max_words=1000, colormap="GnBu", font_path='/usr/share/fonts/truetype/ubuntu/Ubuntu-L.ttf')
            wc.generate_from_frequencies(freq)
            wc.recolor(color_func = blue_color_func)

            plt.imshow(wc, interpolation='bilinear')
            plt.axis("off")
            plt.title(frame.foundation.unique()[0])
            plt.show()

        else:

            f = frame.sort_values(frame.foundation.unique()[0],ascending=False).head(50).set_index('word').T.to_dict()
            freq = {}
            for k,v in f.items():
                freq[k] = v[frame.foundation.unique()[0]]

            wc = WordCloud(background_color="white", max_words=1000, colormap="Reds", font_path='/usr/share/fonts/truetype/ubuntu/Ubuntu-L.ttf')
            wc.generate_from_frequencies(freq)
            wc.recolor(color_func = red_color_func)

            plt.imshow(wc, interpolation='bilinear')
            plt.axis("off")
            plt.title(frame.foundation.unique()[0])
            plt.show()
        
    return
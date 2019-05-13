# The Extended Moral Foundations Dictionary (E-MFD):
## Development and Applications of a Crowd-Sourced Moral Foundations Dictionary

This folder is organized in the following manner:

1.) Data:
- raw and preprocessed highlights utilized for the creation of the E-MFD 
- preprocessed, held-out (i.e., not used for content analysis or dictionary creation) news articles utilized for predicting share counts
- preprocessed, movie scripts utilized for predicting share counts

2.) Dictionaries:
- emfd_scoring: The E-MFD for text scoring. 
- emfd_amp: The E-MFD for usage with Affect Misattribution Procedures or Lexical Decision Tasks
- mfd2.0dic: The MFD2.0 (see https://osf.io/xakyw/)
- mft_original: The original Moral Foundations Dictionary (see https://www.moralfoundations.org/othermaterials)


4.) Notebooks:
- dicitonary_construction.ipynb: Code and pipeline for constructing the E-MFD
- dictionary_exploration.ipynb: Code for exploring the E-MFD (wordclouds)
- dictionary_tresholding.ipynb: Code for thresholding the E-MFD 
- dictionary_validation.ipynb: Code for document scoring, sharing, and movie rating predictions 
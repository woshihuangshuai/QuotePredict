# QuotePredict

## Dependency

  gensim
  
  sklearn

## Data
  
  **News date** is crawled from Yahoo! Finance with YahooFianceNewsSpider.
  
  **Quote date** is get from Yahoo! Finance with getYahooQuote.py in YahooFinanceNewsSpider.
  
## Method

  We use **BOW(Bag of Words)** to map news content to sparse vector and use **SVR** and **SVM** to predict quote direction.
  
  We predict quote of certain company **in 20 minutes** after the time when the news about certain company has been posted.
  
## Experiment Result

  accuracy:
    
  1. SVR: 48%(Gaussian kernel)

  2. SVM: 49%(linear kernel)、51%(polynomial kernel)、52%(Gaussian kernel)
    
This is a cursory trial and There have many things can be optimized in terms of data clean, Textual representation(BOW,Noun     Phrases,Named Entities, Proper Nouns), classifier and so on.
  
## An idea

  1. extract main ideas of the news
  2. use word2vec to map words to vector
  3. represent the main ideas as the average of its word-embeddings
  4. use word-embeddings as the input of SVM to predict quote direction.
    
  
  

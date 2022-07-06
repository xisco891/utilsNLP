
import bs4 as bs
import re
from helpers import convert2word, convert2number


####
#### String Matching Algorithms
####
def levehnstein_matching(name, df):
    max_score = 0
    from fuzzywuzzy import fuzz
    if name not in df["fullname"].unique():
        for i, element in enumerate(df["fullname"].unique()):

            if isinstance(element, str) and isinstance(name, str):

                ratio = fuzz.ratio(name, element)
                if ratio > max_score:
                    max_score = ratio
                    team_matched = element

    else:
        team_matched = name
    return team_matched


def sequenceMatcher(string1, string2):
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, string1, string2).ratio()
    return ratio


vorjahr_words = ["Vorjahr", "vorjahr", "VORJAHR"]
### Enriching Keyowrd adding Upper and lower case versions to the base list of keywords -> list of common words.
def enrich_keywords(keywords_list): 
    keywords_upper = [ keyword.upper()  for keyword in keywords_list ]
    keywords_lower = [ keyword.lower()  for keyword in keywords_list ]
    return keywords_list + keywords_upper + keywords_lower


def get_publication_container(bsoup_object):
    publication_container = bsoup_object.find("div", {"class":"publication_container"})
    if publication_container:
        return publication_container
    else:
        return None

def get_bsoup(html_doc):

    bsoup_object = bs.BeautifulSoup(html_doc, "html.parser")
    publication_container = get_publication_container(bsoup_object)
    if publication_container is None:
        publication_container = bsoup_object
    return publication_container


def get_batch_bsoups(html_docs, step=None):
    init = 0
    end = len(html_docs)
    if step is None:
        step = 20
        
    while((init+step)<end):
        bsoup_object = [  get_bsoup(html_doc)  for html_doc in html_docs[init:init+step] ]
        init += step   
        yield bsoup_object
            
    if init < end:
        bsoup_object = [  get_bsoup(html_doc)  for html_doc in html_docs[init:end] ]
        yield bsoup_object 


def is_fiscal_year(word, fiscal_year):
    if len(word) != 4:
        return False
    else:
        if word != fiscal_year:
            return False
        else:
            return True

        
def row_has_words(texts, patterns): 
    ### Check whether all words in a chunk of text is found in patterns
    import re
    for text in texts: 
        
        for pattern in patterns:
            if pattern in text:
                return text
    
    return None
        
#####################################
### Cleaners for matched data in HTML.
#####################################
    
def clean_text(text):
    
    ## cleaning Text of non ASCII characters, excludes umlautes, get rid of \n, etc. 
    cleaned_text = re.sub('[^a-zA-Z0-9 äöüÜ]+', "", text)
    cleaned_text = re.sub('[\n]', "", cleaned_text)
    cleaned_text = " ".join( [ split_word for split_word in cleaned_text.strip().split(" ") if split_word != "" ] )

    
    return cleaned_text



def remove_leading_zeros(text):
    
    #### It removes leading zeros in float numbers to help deal with numbers. 
    for i, ch in enumerate(text): 
        if ch != 0: 
            return text[i:]

      

        
def get_round_number(text, replace_comma_values):
    
    ### Rounding Numbers for all special cases and fit the various ways someone will write a number in a document.
    if text.count(".") == 0:

        text = remove_leading_zeros(text)

    elif text.count(".") > 1: 

        text = text.split(",")[0]
        text = text.replace(".", "")
        
    else: 
        if replace_comma_values:
            text = text.split(",")[0]
            text = text.replace(".", "")
        else:
            text = text.replace(",", ".")
            
                
    number = float(text)
    return number


def convert_data(text, replace_comma_values): 

    #### Converting data for matched texts. Removing and fitting to special cases. 
    
    text = text.replace("EUR", "")
    text = text.replace("EURO", "")
    text = text.replace("Euro", "")
    text = text.replace("VJ.", "")
    text = text.replace("€", "")
    
    text = text.strip()
          
    if "." in text:
        if "," in text:

            if text.replace(",", "").replace(".", "").isdigit():
                number = get_round_number(text, replace_comma_values)
                return number

    elif text.replace(",", ".").isdigit():
        #print("2nd case")
        if replace_comma_values:
            return get_round_number(text.replace(",", "."), replace_comma_values)
        else:
            return float(text.replace(",", "."))

    elif "," in text and "." not in text:
        #print("3rd case")
        try:
            number = text.replace(",", ".")
            return float(number)
        except:
            pass

   
    return clean_text(text)
    
    

def get_index(file_name):
    
    ## Getting for index of a given document. 
    for i, file_dir in enumerate(file_dirs):
        
        if file_name == file_dir:
            return i
    
    return None


### Converts To String objects
def convertToString(data):
    
    convertedArray = []
    
    for value in data: 
        
        if isinstance(value, str):
            convertedArray.append(value)
        
        else: 
            toString = str(value)
            convertedArray.append(toString)
            
    return convertedArray
            
    
    
## For <tr></tr> blocks , looks for td blocks, gets its text, converts the data, makes sure there is no empty value, 
## For those texts appended to the candidate list it then check with row_has_words whether those "str" values are found in patterns. 
## If True then checks whether table row name is either Rohergebnis or Umsatzerlöse, if True, then it does not append any more rows.
## If no Revenue per se is found then adds all these rows



                


def extract_numbers(text, multiple_patterns): 

    matches = []
        
    for i, pattern in enumerate(multiple_patterns): 
        
        pattern = pattern.replace("[^]", "").strip()
        pattern = re.sub(' +', " ", pattern)
                
        if i == 9:
            for match in re.findall(pattern, text):
                pattern_number = "keine (?!gewerblichen|Gewerblichen|gewerblichte)"
                if re.match(pattern_number, text):
                    #print("There is a match!")
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", 0])
                
        if i == 10:
            for match in re.findall(pattern, text):
                pattern_number = "([0-9]+) \(Vorjahr [0-9]+\) Mitarbeiterinnen und Mitarbeiter"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter und MitarbeiterInnen", max_n])
                    
        if i == 14: 
            for match in re.findall(pattern, text):
                pattern_number = 'Arbeitnehmer betrug ([0-9,]+)'
                matched_n_employees = re.findall(pattern_number, text)

                if matched_n_employees != []:
                    #print("matched_n_employees:", matched_n_employees)
                    n_employees = [ float(n.replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])
                    
                    
        if i == 15:            
            #print("Finding matches for : ", pattern)
            for match in re.findall(pattern, text):
                #print("There is a match : ", match)
                pattern_number = "([0-9]+) \(.*[0-9]+\) angestellte Mitarbeiter."
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    #print("matched_n_employees:", matched_n_employees)
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["angestellte Mitarbeiter", max_n])

        if i == 16: 
            for match in re.findall(pattern, text):
                pattern_number = "Mitarbeiter betrug.* ([0-9]+)"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    #print("matched_n_employees:", matched_n_employees)
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])

                    
        if i == 17: 
            for match in re.findall(pattern, text):
                pattern_number = "waren ([0-9]+) Mitarbeiter beschäftigt"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])

        if i == 18: 
            for match in re.findall(pattern, text):
                pattern_number = "([0-9]+) \(Vorjahr: [0-9]+\) Mitarbeiter"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["MitarbeiterDurchschnitt", max_n])
                    
                    
      
        if i == 19: 
            for match in re.findall(pattern, text):
                             
                pattern_number = '([0-9]+) \(.*\) Angestellte.'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Angestellte", max_n])

        
        if i == 20: 
            for match in re.findall(pattern, text):
                
                             
                pattern_number = '([0-9]+) \(.*\) Arbeitnehmer beschäftigt'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)

                    matches.append(["Arbeitnehmer", max_n])
                    
                    
        if i == 21: 
            
            for match in re.findall(pattern, text):
                pattern_number = 'Arbeitnehmer betrug ([0-9,]+)'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])

        if i == 22: 
            
            for match in re.findall(pattern, text):
                
                
                pattern_number = '([0-9]+) \(.*[0-9]+\) Mitarbeiter'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])
        
        if i == 23: 
            
            for match in re.findall(pattern, text):
                
                pattern_number = '([0-9]+) \(.*[0-9]+\) Mitarbeiter beschäftigt.'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])
        if i == 24: 
            
            for match in re.findall(pattern, text):
                pattern_number = 'durchschnittlich ([0-9,]+) Vollkräfte beschäftigt.'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])
                                                
        if i == 25: 
            
            for match in re.findall(pattern, text):
                
                pattern_number = '([0-9]+) \(.*\) gewerbliche Arbeitnehmer'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])
                                           
                        
                        
        if i == 26: 
            for match in re.findall(pattern, text):
                pattern_number = "durchschnittlich ([0-9.]+) Arbeitnehmer"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])
            
            
        if i == 27: 
 
            for match in re.findall(pattern, text):
                pattern_number = "durchschnittlich ([0-9.]+) Mitarbeiter"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])            
        if i == 28: 
 
            for match in re.findall(pattern, text):
                pattern_number = "durchschnittlich ([0-9.]+) Arbeitnehmer"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])     
                    
        if i == 29: 
 
            for match in re.findall(pattern, text):
                pattern_number = "wurden ([0-9.]+) Mitarbeiter .* beschäftigt"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])                                
                    
                    
        if i == 30: 
 
            for match in re.findall(pattern, text):
                pattern_number = "durchschnittlich ([0-9]+)"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])                                
        if i == 31: 
            
            #print("pattern: ", pattern)
            #print("text: ", text)
            
            for match in re.findall(pattern, text):
                pattern_number = "\(.*\) ([0-9,]+) AN beschäftigt.."
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])                                
        if i == 32: 
            for match in re.findall(pattern, text):
                pattern_number = "Arbeitnehmer .* auf ([0-9]+)"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])                                
        if i == 33: 
            for match in re.findall(pattern, text):
                pattern_number = "betrug ([0-9]+) Personen."
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])                                                                                  
                   
        if i == 34: 
            for match in re.findall(pattern, text):
                pattern_number = "([0-9]+) interne Arbeitnehmer"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])                                                                                  
               
        if i == 35: 
            for match in re.findall(pattern, text):
                pattern_number = "([0-9]+) externe Mitarbeiter"
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])
                    
        if i == 36: 
            for match in re.findall(pattern, text):
                pattern_number = "durchschnittlich ([0-9,]+) \(.*[0-9]+\) Arbeitnehmer."
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])             
        
        if i == 37: 
            for match in re.findall(pattern, text):
                pattern_number = "([0-9]+) \(Arbeitnehmer .* bei der Gesellschaft beschäftigt."
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])             
  
        if i == 38: 
            for match in re.findall(pattern, text):
                pattern_number = "([0-9]+) \(.*\) Arbeitnehmer beschäftigt."
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])             
  
        if i == 39: 
            for match in re.findall(pattern, text):
                pattern_number = "keine eigenen Mitarbeiter"
                if re.findall(pattern_number, text):
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", 0])      
                    
                    
        if i == 40: 
            for match in re.findall(pattern, text):
                pattern_number = '.* Arbeitnehmer betrug ([0-9]+)'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Arbeitnehmer", max_n])             

                    
        if i == 41: 
            for match in re.findall(pattern, text):
                pattern_number = '.* durch folgende Personen geführt: ([a-zäöüÄÖÜ A-Z]+)'
                if re.findall(pattern_name, text) != []:
                    matches.append(["Geschäftsführer", 1])             

        
       
        if i == 42: 
            for match in re.findall(pattern, text):
                pattern_number = '[A-Za-z0-9äöü.ß]+ Insgesamt ist die Anzahl der Mitarbeiter in der Gruppe zum Jahresende auf über ([0-9.,]+) Personen angestiegen'
                matched_n_employees = re.findall(pattern_number, text)
                if matched_n_employees != []:
                    n_employees = [ float(n.replace(".", "").replace(",", ".")) for n in matched_n_employees]
                    max_n = max(n_employees)
                    print("There is match for pattern: ", pattern)
                    matches.append(["Mitarbeiter", max_n])             
           
                

    return matches



def get_right_before_after_numbers(words, i, fiscal_year):

    #### Matches of numbers before and after a word and returns a candidate pair - [revenue_word, number]
    
    matches = []
    l_words = len(words)
   
    if i>=1:
        preceeding_word = words[i-1] 
        if preceeding_word.replace(",", "").replace(".", "").isdigit(): 
             if is_fiscal_year(preceeding_word, fiscal_year) is False:
                    #print("word: ", words[i])
                    #print("preceeding_word: ", preceeding_word)
                    matches.append([words[i].replace(".", ""), preceeding_word])

        else:
            if preceeding_word in ["keine", "Keine"]:
                #print("Keine Word found in the preceeding word.")
                matches.append([words[i].replace(".", ""), 0])

            else:
                converted_number = convert2number(preceeding_word)
                if converted_number: 
                    matches.append([words[i].replace(".", ""), converted_number])


    if i < l_words-1:
        
        following_word = words[i+1]
        
        if following_word.replace(",", "").replace(".", "").isdigit():
            following_word = following_word.replace(",", ".")
            if is_fiscal_year(following_word, fiscal_year) is False:
                matches.append([words[i].replace(".", ""), following_word])

        else:
            converted_number = convert2number(following_word)
            if converted_number: 
                matches.append([words[i].replace(".", ""), converted_number])
    
    return matches

    
    
def get_numbers(text, fiscal_year, employee_keywords=None, pattern_employee_tables=None):

    words = text.strip().split(' ')
    #print("text: ", text)
    #print("words: ", words)
    matches = []
    keys_extracted = []
 
    for i, word in enumerate(words): 
        word = word.replace(".", "").replace(",", "")
        if word in employee_keywords and len(word) < 40 and "Pensionszusagen." not in words and "Betriebe" not in words:
            #### Looks for numbers Before or After an employee keyword found in text.
            rba_matches = get_right_before_after_numbers(words, i, fiscal_year)
            #print("rba_matches: ", rba_matches)
            if rba_matches != []:
    
                keys_extracted.extend([ rba_match[0] for rba_match in rba_matches ])
                for rba_match in rba_matches: 
                    matches.append(rba_match)


        #### Looks for numbers Before or After an Vorjahr!.
            
        elif word in vorjahr_words:
            
            for key in keys_extracted: 
                if key in pattern_employee_tables: 
                    rba_matches = get_right_before_after_numbers(words, i, fiscal_year)
                    if rba_matches != []:
                        keys_extracted.extend([ rba_match[0] for rba_match in rba_matches ])
            
                        for rba_match in rba_matches: 
                            matches.append(rba_match)

    
       
    return matches
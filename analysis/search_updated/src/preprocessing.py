import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re

# Download the necessary resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

SECTION_SPLITTER = ' || '

def preprocess_text(text):
    # lowercase the text
    text = text.lower()

    # Remove escape sequences
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\r', ' ', text)
    text = re.sub(r'\t', ' ', text)
    # Remove extra whitespaces
    text = re.sub(' +', ' ', text)

    # Remove 


    # Tokenize the text
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token.lower() not in stop_words]
    
    # Lemmatize the tokens
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Remove punctuation
    tokens = [re.sub(r'[^\w\s]', '', token) for token in tokens]
    # Remove digits
    tokens = [re.sub(r'\d+', '', token) for token in tokens]
    # Remove empty tokens
    tokens = [token for token in tokens if len(token) > 0]

    
    # Return the preprocessed tokens
    return tokens


def parse_hierarchy(titles):
    # parse the hierarchy of section titles, e.g. if 1. A, 1.1 B then A - B
    # This function parses a list of section titles into a hierarchy-indicated format.

    result = []  # Stores the final formatted titles
    current_hierarchy = []  # Stack to maintain the current path of titles

    for title in titles:
        # Split the title into the numeric part and text part
        number, text = title.split(' ', 1)
        if not number.endswith('.'):
            number = number + '.'
        # Calculate the depth based on the number of dots in the number part
        level = number.count('.') 
        
        # Adjust the hierarchy stack to the current level
        current_hierarchy = current_hierarchy[:level-1]
        # Add the current section title
        current_hierarchy.append(text.strip())
        
        # Join all elements in the current_hierarchy with a hyphen
        result.append(SECTION_SPLITTER.join(current_hierarchy))

    return result

def add_whitespace(text):
    # Add whitespace after section numbers if there is none, e.g. 1.B -> 1. B
    text = re.sub(r'(\d\.)([a-zA-Z]+)', r'\1 \2', text)
    text = re.sub(r'(\d(\.\d)+)(\S+)', r'\1 \3', text)
    return text



def parse_section_list(section_list):
    result = [list(v.values())[0] for v in section_list]
    result = [add_whitespace(section) for section in result]
    # only keep names starting with a section number, e.g. 1., 1.1
    remove_non_sec = [section for section in result if re.match(r'^\d+\.\s*', section)]
    if len(remove_non_sec) == 0:
        remove_non_sec = result[:result.index('Bibliography')]
        remove_non_sec = [f'{i}. {section}' for i, section in enumerate(remove_non_sec, 1)]

    return remove_non_sec, parse_hierarchy(remove_non_sec)

def split_by_section(text, section_list, title):
    try:
        section_list, hierarchy = parse_section_list(section_list)
    except ValueError:
        print(section_list)
        print(title)
        raise
    assert len(section_list) != 0, f"No sections found in {title}"
    result = dict()
    for i in range(len(section_list)-1):
        start = section_list[i]
        end = section_list[i+1]
        start_index = text.find(start)
        end_index = text.find(end)
        section_text = text[start_index:end_index]
        if len(section_text) - len(start) > 10:
            result[hierarchy[i]] = {'main_text': hierarchy[i] + '\n' + section_text, 'section_title': start, 
                                    'entry_title': title, 
                                    'hierarchy_title': SECTION_SPLITTER.join([title, hierarchy[i]])}
    # Add the last section
    try:
        start = section_list[-1]
        start_index = text.find(start)
    except IndexError:
        print(section_list)
        print(title)
        print(start)
        raise
    section_text = text[start_index:]
    if len(section_text) - len(start) > 10:
        result[hierarchy[-1]] = {'main_text': hierarchy[i] + '\n' + section_text, 'section_title': start, 
                                    'entry_title': title, 
                                    'hierarchy_title': SECTION_SPLITTER.join([title, hierarchy[i]])}
    return result

# Example usage
if __name__ == "__main__":
    text = "\n1. Life and Works\n\n\nHistory is written by the winners. Most of what we know of William of\nChampeaux's life and work has been refracted down to us through the\nprism of a man who hated him. Peter Abelard lost almost every battle\nwith William, his teacher and political enemy, yet he tells us that\nWilliam was a discredited, defeated, jealous, and resentful man.\nAbelard claims to have humiliated William in debate, driving him from\nthe Paris schools. He alleges that, in defeat, William cast himself in\nthe role of monastic reformer only to advance his political career by\nan unearned reputation for piety. Still, even Abelard recognized that\nWilliam was no fraud, calling him \"first in reputation and in fact,\"\nand relocating to study under his tutelage (HC; trans. Radice\n1974).\n\n\nOn the scholarly front, Abelard presents only half the story. He brags\nof forcing William to abandon a firmly-held realist theory of\nuniversals, but, rather than come over to Abelard's vocalist or\nnominalist cause, William developed a second, more sophisticated,\nrealist view. So what might have appeared as an expression of\nintellectual honesty and academic rigor on William's part, Abelard\npresents as somehow shameful."
    preprocessed_text = preprocess_text(text)
    print(preprocessed_text)
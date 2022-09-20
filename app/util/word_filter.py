from app.core.exceptions import EmptySearchCriteria


STOPWORDS_NL = [
    "de",
    "en",
    "van",
    "ik",
    "te",
    "dat",
    "die",
    "in",
    "een",
    "hij",
    "het",
    "niet",
    "zijn",
    "is",
    "was",
    "op",
    "aan",
    "met",
    "als",
    "voor",
    "had",
    "er",
    "maar",
    "om",
    "hem",
    "dan",
    "zou",
    "of",
    "wat",
    "mijn",
    "men",
    "dit",
    "zo",
    "door",
    "over",
    "ze",
    "zich",
    "bij",
    "ook",
    "tot",
    "je",
    "mij",
    "uit",
    "der",
    "daar",
    "haar",
    "naar",
    "heb",
    "hoe",
    "heeft",
    "hebben",
    "deze",
    "u",
    "want",
    "nog",
    "zal",
    "me",
    "zij",
    "nu",
    "ge",
    "geen",
    "omdat",
    "iets",
    "worden",
    "toch",
    "al",
    "waren",
    "veel",
    "meer",
    "doen",
    "toen",
    "moet",
    "ben",
    "zonder",
    "kan",
    "hun",
    "dus",
    "alles",
    "onder",
    "ja",
    "eens",
    "hier",
    "wie",
    "werd",
    "altijd",
    "doch",
    "wordt",
    "wezen",
    "kunnen",
    "ons",
    "zelf",
    "tegen",
    "na",
    "reeds",
    "wil",
    "kon",
    "niets",
    "uw",
    "iemand",
    "geweest",
    "andere",
]

ADDITIONAL_FILTER_WORDS = [
    "zuid",
    "holland",
    "zuid-holland",
]

STOPWORD_LIST = STOPWORDS_NL + ADDITIONAL_FILTER_WORDS


def get_filtered_search_criteria(search_query: str): 
    """
    Sanitize input string from stopwords or 
    other specified filter words
    """
    case_normalized = search_query.lower()
    query_words = case_normalized.split(" ")
    filtered = filter(lambda v: v not in STOPWORD_LIST, query_words)
    search_criteria = list(filtered)

    if len(search_criteria) is 0:
        raise EmptySearchCriteria("Filtered search query contains 0 criteria")

    return search_criteria


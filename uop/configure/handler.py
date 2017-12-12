import re

def fuzzyfinder(keywords, collection):
    suggestions = []
    pattern = '.*'.join(keywords)
    regex = re.compile(pattern)
    for item in collection:
        match = regex.search(item)
        if match:
            suggestions.append((match.start(), item))
    return [x for _, x in suggestions]
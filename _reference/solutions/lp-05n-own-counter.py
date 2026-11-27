def make_counter():
    seen = {}
    def count(word):
        if word not in seen:
            seen[word] = 0
        seen[word] = seen[word] + 1
        return seen[word]
    return count

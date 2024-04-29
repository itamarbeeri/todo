
class Compressor:
    def __init__(self):
        self.split_depth = 2
        self.version = 1

    def get_metadata(self):
        return '00000000'

    def compress(self, text):
        return self.run_compression([text], dict())

    def decompress(self, compressed_text):
        return compressed_text

    def run_compression(self, text_list, compression_dict):

        patterns = count_patterns(text_list)

        # sort yo find best pattern to replace
        best_patterns = sort_best_patterns(patterns)

        # TODO: replace pattern
        new_text_list = text_list

        # TODO: add pattern to dict
        new_compression_dict = compression_dict

        self.run_compression(new_text_list, new_compression_dict)

def count_patterns(text_list):
    pass

def sort_best_patterns(patterns):
    pass

def codeword_score(code_length, pattern_length, repetitions):
    return code_length + pattern_length + (code_length - pattern_length) * repetitions

"""
c = code_length
p = patterns length
N = repetitions

score = c + p + (c - p) * N
score = c * (N + 1) + p * (1 - N)
score = c * (N + 1) + p - N * p

N > 1
p > c

Np > Nc + c + p
Np - p > Nc + c(
N > (c+p) / (p-c)

c = 2 -> N>5
p max = text_length // 5
"""
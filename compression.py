
class Compressor:
    def __init__(self):
        self.version = 1

    def get_metadata(self):
        return '00000000'

    def compress(self, text):
        return text

    def decompress(self, compressed_text):
        return compressed_text
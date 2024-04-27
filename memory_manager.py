
from encription import Cipher
from compression import Compressor
from error_correction import ErrorCorrector

class MemoryManager:
    def __init__(self):
        self.cipher = Cipher()
        self.compressor = Compressor()
        self.error_corrector = ErrorCorrector()
        self.STX = '01101001'
        self.ETX = '10110100'

    def pack_memory(self, text):
        cipher_text = self.cipher.encrypt_text(text)
        compressed_text = self.compressor.compress(cipher_text)
        error_correction_code = self.error_corrector.builb_error_correction_code(compressed_text)

        packed_memory = self.STX + \
                        self.cipher.get_metadata() + \
                        self.compressor.get_metadata() + \
                        self.error_corrector.get_metadata() + \
                        compressed_text + \
                        error_correction_code + \
                        self.ETX

        return packed_memory

    def unpack_memory(self, packed_memory):
        mock_error_correction_code = self.error_corrector.mock_error_correction_code()

        pre_metadata_length = len(self.STX +
                                  self.cipher.get_metadata() +
                                  self.compressor.get_metadata() +
                                  self.error_corrector.get_metadata())

        post_metadata_length = len(mock_error_correction_code + self.ETX)
        error_correction_code = packed_memory[-len(mock_error_correction_code + self.ETX): -len(self.ETX)]

        compressed_text = packed_memory[pre_metadata_length:-post_metadata_length]
        corrected_text, text_validity = self.error_corrector.correct_text(compressed_text, error_correction_code)

        cipher_text = self.compressor.decompress(corrected_text)
        text = self.cipher.decrypt_text(cipher_text)

        return text


def test_functions(text, memory_manager):
    packed_memory = memory_manager.pack_memory(text)
    unpacked_memory = memory_manager.unpack_memory(packed_memory)

    assert text == unpacked_memory

if __name__ == '__main__':
    text = 'this is the string i want to encrypt. will it be successfull encrypted and decrypted? will it be the same?'
    memory_manager = MemoryManager()
    test_functions(text, memory_manager)


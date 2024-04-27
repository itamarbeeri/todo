import random

def text2bits(text):
    return ''.join(format(ord(char), '08b') for char in text)


def bits2text(bin_str):
    return ''.join(chr(int(bin_str[i:i + 8], 2)) for i in range(0, len(bin_str), 8))


def xor_binary_strings(bin_str1, bin_str2):
    if len(bin_str1) != len(bin_str2):
        raise ValueError("Binary strings must have the same length")

    return ''.join(str(int(bit1) ^ int(bit2)) for bit1, bit2 in zip(bin_str1, bin_str2))


class Cipher:
    def __init__(self, embedding_idx=70, length_bits=8):
        self.embedding_idx = embedding_idx
        self.length_bits = length_bits
        self.version = 1

    def get_metadata(self):
        return '00000000'

    def encrypt_text(self, text):
        bits = text2bits(text)
        embedded_bits = self.embbed_random_key(bits)
        randomness = self.generate_randomness_for_embedded_bits(embedded_bits)
        cipher_bits = xor_binary_strings(embedded_bits, randomness)
        return bits2text(cipher_bits)


    def decrypt_text(self, cipher_text):
        cipher_bits = text2bits(cipher_text)
        randomness = self.generate_randomness_for_embedded_bits(cipher_bits)
        embedded_bits = xor_binary_strings(cipher_bits, randomness)
        bits = self.remove_random_key(embedded_bits)
        return bits2text(bits)

    def embbed_random_key(self, bits):
        randomness_length = random.randint(128, 255)
        randomness_length = randomness_length - randomness_length % 8
        randomness = ''.join(str(random.randint(0, 1)) for _ in range(randomness_length))
        embedded_bits = bits[:self.embedding_idx] + bin(randomness_length)[2:] + randomness + bits[self.embedding_idx:]
        return embedded_bits


    def remove_random_key(self, embedded_bits):
        randomness_length_bits = embedded_bits[self.embedding_idx: self.embedding_idx + self.length_bits]
        randomness_length = int(randomness_length_bits, 2)
        bits = embedded_bits[:self.embedding_idx] + embedded_bits[self.embedding_idx + randomness_length + self.length_bits:]
        return bits


    def generate_randomness_for_embedded_bits(self, embedded_bits):
        randomness_length_bits = embedded_bits[self.embedding_idx: self.embedding_idx + self.length_bits]
        randomness_length = int(randomness_length_bits, 2)
        randomness = embedded_bits[self.embedding_idx + self.length_bits: self.embedding_idx + self.length_bits + randomness_length]

        pseudo_randomness = ''
        while len(pseudo_randomness) < len(embedded_bits):
            pseudo_randomness += randomness
            randomness = randomness[-1] + randomness[:-1]

        pseudo_randomness = pseudo_randomness[0:len(embedded_bits)]
        pseudo_randomness = pseudo_randomness[:self.embedding_idx] + \
                            '0' * (randomness_length + self.length_bits) + \
                            pseudo_randomness[self.embedding_idx + randomness_length + self.length_bits:]

        return pseudo_randomness


def test_functions(text, cipher):
    bits = text2bits(text)
    assert text == bits2text(bits)
    assert bits == cipher.remove_random_key(cipher.embbed_random_key(bits))
    assert text == cipher.decrypt_text(cipher.encrypt_text(text))

if __name__ == '__main__':
    text = 'this is the string i want to encrypt. will it be successfull encrypted and decrypted? will it be the same?'
    cipher = Cipher(embedding_idx=70, length_bits=8)
    test_functions(text, cipher)

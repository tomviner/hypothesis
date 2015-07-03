from hypothesis.internal.bitarray import BitArray
from hypothesis.internal.compat import hrange


class BloomFilter(object):
    def __init__(self, hash_size):
        if hash_size % 2:
            raise ValueError(
                'hash size %d is not divisible by 2' % (hash_size,))
        self.hash_size = hash_size
        self.data = BitArray(2 ** 16)

    def add(self, value):
        for h in self.__value_to_hashes(value):
            self.data[h] = True

    def __contains__(self, value):
        return all(self.data[h] for h in self.__value_to_hashes(value))

    def __value_to_hashes(self, value):
        if len(value) != self.hash_size:
            raise ValueError("Invalid sized hash. Expected %d but got %d" % (
                self.hash_size, len(value)))
        for i in hrange(self.hash_size // 2):
            offset = i * 2
            hi = value[offset]
            lo = value[offset + 1]
            yield hi * 256 + lo

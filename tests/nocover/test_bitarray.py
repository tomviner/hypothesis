from hypothesis.internal.bitarray import BitArray
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule
from hypothesis.strategies import integers, booleans


class MirroredBitArray(object):
    def __init__(self, n):
        self.bitarray = BitArray(n)
        self.mirror = [False] * n

    def __len__(self):
        assert len(self.mirror) == len(self.bitarray)
        return len(self.bitarray)

    def __getitem__(self, i):
        bitv = self.bitarray[i]
        mirrorv = self.mirror[i]
        assert bitv == mirrorv
        return bitv

    def __setitem__(self, i, v):
        v = bool(v)
        self.bitarray[i] = v
        self.mirror[i] = v
        assert self[i] == v


Indices = integers(0, 5000)


class BitArrayModel(RuleBasedStateMachine):
    bitarrays = Bundle('bitarrays')

    @rule(target=bitarrays, n=Indices)
    def build_array(self, n):
        return MirroredBitArray(n)

    @rule(x=bitarrays, i=Indices, v=booleans())
    def set_value(self, x, i, v):
        try:
            x[i] = v
        except IndexError:
            pass

    @rule(x=bitarrays, i=Indices)
    def get_value(self, x, i):
        try:
            x[i]
        except IndexError:
            pass

    @rule(x=bitarrays)
    def check_length(self, x):
        len(x)


TestBitArrays = BitArrayModel.TestCase

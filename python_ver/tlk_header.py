import input_stream
import tlk_file


class TlkHeader:
    def __init__(self, in_stream):
        self.magic = input_stream.read_int_32(in_stream)
        self.ver = input_stream.read_int_32(in_stream)
        self.min_ver = input_stream.read_int_32(in_stream)
        self.entry_1_count = input_stream.read_int_32(in_stream)
        self.entry_2_count = input_stream.read_int_32(in_stream)
        self.tree_nodes_count = input_stream.read_int_32(in_stream)  # count of unique symbols
        self.data_len = input_stream.read_int_32(in_stream)

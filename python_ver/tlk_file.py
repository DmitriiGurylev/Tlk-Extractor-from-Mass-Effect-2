import os

from bit_array import BitArray
import bit_convertor
from huffman_node import HuffmanNode
import tlk_header
from input_stream import InputStream
from tlk_string_ref import TlkStringRef
from wrapper import Wrapper

from xml.etree import ElementTree as ET

'''
Structure of TLK file of Mass Effect 2:
1. Header
    a) magic
    b) ver
    c) min_ver
    d) entry_1_count
    e) entry_2_count
    f) tree_nodes_count
    g) data_len
2. Entries 
    entry_1 and entry_2; 
    8 bytes per entry: 
        4 bytes - string_id, 
        4 bytes - bit_offset
3. Huffman nodes ()
4. Other sequences
'''


class TlkFile:
    def __init__(self):
        self.header = None
        self.string_refs = []
        self.character_tree = []
        self.bits = BitArray()

    def get_string(self, bit_offset: Wrapper) -> str:
        root_node = self.character_tree[0]
        cur_node = root_node
        cur_string = ''

        offset = bit_offset.val
        while offset < self.bits.length:
            if self.bits.get_reversed_bit(offset):
                next_node_id = cur_node.right_node_id
            else:
                next_node_id = cur_node.left_node_id

            if next_node_id >= 0:
                cur_node = self.character_tree[next_node_id]
            else:
                try:
                    char = bit_convertor.to_char_rev(bit_convertor.get_bytes_by_int_32(0xffff - next_node_id), 0)
                except:
                    raise Exception
                if char != '\0':
                    cur_string += char
                    cur_node = root_node
                else:
                    offset += 1
                    bit_offset.val = offset
                    return cur_string
            offset += 1
        offset += 1
        bit_offset.val = offset
        return None

    # Loads a TLK file into memory.
    def load_tlk_data(self, source_path):
        # ****************** STEP ONE ****************
        # -- load TLK file header --
        # reading first 28(4 * 7) bytes to build Header

        # using LittleEndian for PC architecture and BigEndian for Xbox360
        input_s = InputStream(source_path)
        self.header = tlk_header.TlkHeader(input_s)  # read 7 * 4 = 28 bytes

        # read possibly correct ME2 TLK file, but from another platfrom
        if self.header.magic == 1416391424:
            raise Exception('header.magic == 1416391424')
        # read definitely NOT a ME2 TLK ile
        if self.header.magic != 7040084:
            raise Exception('header.magic != 7040084')

        # ****************** STEP TWO ****************
        # -- read and store Huffman Tree nodes --

        # jumping to the beginning of Huffmann Tree stored in TLK file * /
        pos = input_s.pos  # position after reading of header
        # an entry is: 4 bytes - string_id and 4 bytes - bit_offset
        input_s.pos = pos + (self.header.entry_1_count + self.header.entry_2_count) * 8  # TODO ??? WHAT IS ENTRY

        for _ in range(self.header.tree_nodes_count):
            # read 8 bytes: 4 bytes to get left_node_id, 4 bytes to get right_node_id
            h_node = HuffmanNode(stream=input_s)
            self.character_tree.append(h_node)

        # / ****************** STEP THREE ****************
        # -- read all of coded data into memory --
        data_length = self.header.data_len  # number of bytes of encoded sequence
        data = [None] * data_length
        input_s.read_to_array(data, 0, data_length)
        # and store it as raw bits for further processing
        self.bits = BitArray(a=data)

        # ****************** STEP FOUR ****************
        # -- decode (basing on Huffman Tree) raw bits data into actual strings --
        # and store them in a Dictionary <int,string> where:
        # int: bit offset of the beginning of data
        # (offset starting at 0 and counted for Bits array)
        # so offset == 0 means the first bit in Bits array
        # string: actual decoded String
        raw_str = {}
        offset = Wrapper(0)  # wrapper of bits offset

        while offset.val < self.bits.length:
            key = offset.val
            s = self.get_string(offset)
            raw_str[key] = s

        # rewind BinaryReader just after the Header
        # at the beginning of TLK Entries data
        input_s.pos = pos

        # **************** STEP FIVE ****************
        # -- bind data to String IDs --
        # go through Entries in TLK file and read it's String ID and offset
        # then check if offset is a key in rawStrings and if it is, then bind data.
        # Sometimes there's no such key, in that case, our String ID is probably a substring
        # of another String present in rawStrings.
        for i in range(self.header.entry_1_count + self.header.entry_2_count):
            s_ref = TlkStringRef(input_s)  # read 8 bytes
            s_ref.position = i  # position is an entry
            if s_ref.bit_offset >= 0:
                # actually, it should store the fullString and subStringOffset,
                # but as we don't have to use this compression feature,
                # we will store only the part of String we need

                # key = raw_str.keys.Last(c => c < s_ref.bit_offset);
                # String fullString = raw_str[key];
                # int subStringOffset = fullString.LastIndexOf(partString);
                # s_ref.StartOfString = subStringOffset;
                # s_ref.data = fullString;
                if s_ref.bit_offset in raw_str.keys():
                    s_ref.data = raw_str[s_ref.bit_offset]
                else:
                    s_ref.data = self.get_string(Wrapper(s_ref.bit_offset))
            self.string_refs.append(s_ref)

    def store_to_file(self, dest_file: str, file_format: str):
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        if file_format.lower() == 'to_xml':
            print(file_format + ' XML')
            self.save_to_xml_file(dest_file)
        else:
            print(file_format + ' TXT')
            self.save_to_text_file(dest_file)

    # Writing data in an XML format.
    def save_to_xml_file(self, abs_path: str):
        root = ET.Element('tlkFile')  # <tlkFile> tag
        root.set("TLKToolVersion", '1.0.4')  # <tlkFile> attributes
        comment = ET.Comment('Male entries section begin (ends at position {0})'.format(
            (str(self.header.entry_1_count - 1))))
        root.append(comment)

        for i in range(len(self.string_refs)):
            sr = self.string_refs[i]

            if sr.position == self.header.entry_1_count:
                comment1 = ET.Comment('Male entries section end')
                comment2 = ET.Comment('Female entries section begin (ends at position {0})'.format(
                    (str(self.header.entry_1_count + self.header.entry_2_count - 1))))
                root.append(comment1)
                root.append(comment2)

            s = ET.SubElement(root, 'string')  # <string> tag

            s1 = ET.SubElement(s, 'id')  # <id> tag
            s1.text = str(sr.string_id)

            s2 = ET.SubElement(s, 'position')  # <position> tag
            s2.text = str(sr.position)

            s3 = ET.SubElement(s, 'data')  # <data> tag
            s3.text = '-1' if sr.bit_offset < 0 else sr.data
        comment = ET.Comment("Female entries section end")
        root.append(comment)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="\t", level=0)
        tree.write(abs_path, encoding="utf-8")

    def save_to_text_file(self, dest_file: str):
        total_count = len(self.string_refs)

        with open(dest_file, "w+") as f:
            for i in range(total_count):
                s = self.string_refs[i]
                line = str(s.string_id) + ': ' + str(s.data) + '\r\n'
                f.write(line)

import unittest

from jetson_remote.edid import EDID_HEADER, analyze_edid


def valid_base_block(extension_count: int = 0) -> bytes:
    block = bytearray(128)
    block[:8] = EDID_HEADER
    block[18] = 1
    block[19] = 4
    block[20] = 0x80
    block[126] = extension_count
    block[127] = (-sum(block[:-1])) % 256
    return bytes(block)


class EdidTests(unittest.TestCase):
    def test_valid_base_block(self):
        report = analyze_edid(valid_base_block())
        self.assertTrue(report["valid"])
        self.assertEqual(report["size"], 128)
        self.assertEqual(report["block_checksums_valid"], [True])

    def test_checksum_failure_is_invalid(self):
        data = bytearray(valid_base_block())
        data[30] = 1
        self.assertFalse(analyze_edid(bytes(data))["valid"])

    def test_extension_count_must_match_size(self):
        report = analyze_edid(valid_base_block(extension_count=1))
        self.assertFalse(report["valid"])
        self.assertFalse(report["extension_count_matches_size"])


if __name__ == "__main__":
    unittest.main()

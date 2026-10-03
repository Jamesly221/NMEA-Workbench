import json
from pathlib import Path
import tempfile
import unittest
from src.nmea.catalog import load_catalog
from src.nmea.parser import parse, coordinate, sentence

ROOT = Path(__file__).resolve().parents[1]


class ParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, errors = load_catalog(ROOT / 'data/sentences')
        assert not errors, errors

    def test_known_checksum_and_position(self):
        raw = '$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A'
        result = parse(raw, self.catalog)
        self.assertEqual(result.checksum, 'Valid')
        self.assertEqual(result.health, 'OK')
        self.assertAlmostEqual(coordinate('4807.038', 'N', True), 48.1173)
        self.assertAlmostEqual(coordinate('01131.000', 'E', False), 11.5166666667)
        self.assertIn('48.1173000', result.rows[2][3])

    def test_all_bundled_examples(self):
        for code, entry in self.catalog.items():
            with self.subTest(code=code):
                result = parse(entry['example'], self.catalog)
                self.assertEqual(result.kind, code)
                self.assertEqual(result.checksum, 'Valid')
                self.assertEqual(result.issues, [])

    def test_checksum_states(self):
        raw = sentence('HEHDT,90.0,T')
        self.assertEqual(parse(raw[:-2] + 'ZZ', self.catalog).checksum, 'Malformed')
        wrong = '00' if raw[-2:] != '00' else '01'
        self.assertEqual(parse(raw[:-2] + wrong, self.catalog).checksum, 'Mismatch')
        self.assertEqual(parse('$HEHDT,90.0,T', self.catalog).checksum, 'Missing')
        self.assertEqual(parse(raw[:-2] + raw[-2:].lower(), self.catalog).checksum, 'Valid')

    def test_void_status_is_distinct_from_checksum(self):
        result = parse(sentence('GNRMC,123520,V,,,,,,,230394,,,'), self.catalog)
        self.assertEqual(result.checksum, 'Valid')
        self.assertEqual(result.health, 'Review')
        self.assertTrue(any('void' in issue for issue in result.issues))

    def test_bad_coordinates_and_numeric_values(self):
        for value, hemisphere, lat in [('4860.0','N',True), ('9000.1','N',True), ('18100.0','E',False), ('4807.0','E',True), ('NaN','N',True)]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    coordinate(value, hemisphere, lat)
        self.assertEqual(coordinate('9000.0', 'S', True), -90)
        self.assertEqual(coordinate('18000.0', 'W', False), -180)
        for angle in ('400', '-1', 'nan', 'inf', 'oops', ''):
            self.assertEqual(parse(sentence(f'HEHDT,{angle},T'), self.catalog).health, 'Review')

    def test_unsupported_and_malformed_messages_do_not_crash(self):
        for raw in ('', 'junk', '$', '$GPHDT,90,T*', '$GPHDT,90,T*00*00', '$GPHDT,90,\x00T', '$GPHDT,90,é', '$PTEST,1*00'):
            with self.subTest(raw=repr(raw)):
                self.assertNotEqual(parse(raw, self.catalog).health, 'OK')
        result = parse(sentence('GPXYZ,1,,3'), self.catalog)
        self.assertEqual(len(result.rows), 3)
        self.assertEqual(result.rows[1][2], '(empty)')

    def test_truncation_and_extra_fields(self):
        self.assertTrue(parse(sentence('GPRMC,123519,A'), self.catalog).issues)
        result = parse(sentence('HEHDT,90,T,EXTRA'), self.catalog)
        self.assertEqual(result.rows[-1][2], 'EXTRA')

    def test_invalid_time_date_and_units(self):
        for body in ('GPRMC,250000,A,4807.038,N,01131.000,E,1,90,230394,,',
                     'GPRMC,123519,A,4807.038,N,01131.000,E,1,90,310294,,',
                     'GPVTG,90,T,,M,1,N,1.852,X,A'):
            self.assertTrue(parse(sentence(body), self.catalog).issues)

    def test_demo_preserves_bad_lines(self):
        lines = (ROOT / 'examples/logs/demo.txt').read_text().splitlines()
        records = [parse(line, self.catalog) for line in lines]
        self.assertEqual(len(records), 9)
        self.assertEqual(records[5].checksum, 'Mismatch')
        self.assertEqual(records[6].checksum, 'Missing')
        self.assertTrue(records[-1].issues)


class CatalogTests(unittest.TestCase):
    def test_bad_entries_are_reported_without_losing_good_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = (ROOT / 'data/sentences/HDT.json').read_text()
            (root / 'good.json').write_text(good)
            (root / 'broken.json').write_text('{')
            (root / 'wrong.json').write_text(json.dumps({'type': 'BAD'}))
            (root / 'list.json').write_text('[]')
            entries, errors = load_catalog(root)
            self.assertIn('HDT', entries)
            self.assertEqual(len(errors), 3)

    def test_duplicate_types_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('a.json', 'b.json'):
                (root / name).write_text((ROOT / 'data/sentences/HDT.json').read_text())
            entries, errors = load_catalog(root)
            self.assertEqual(len(entries), 1)
            self.assertEqual(len(errors), 1)


if __name__ == '__main__':
    unittest.main()

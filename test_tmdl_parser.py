import unittest
import os
import json
import tempfile
from tmdl_parser import TmdlParser

class TestTmdlParser(unittest.TestCase):
    def setUp(self):
        # Create a temp file, but close it so we can write to it cleanly in tests or let the parser read it
        # We'll re-open in write_tmdl
        fd, self.test_file_path = tempfile.mkstemp(suffix='.tmdl')
        os.close(fd)

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def write_tmdl(self, content):
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip()) # Strip leading/trailing whitespace from the test string convenience

    def test_simple_table(self):
        content = """
table MyTable
	lineageTag: 12345
"""
        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        self.assertEqual(result['name'], 'MyTable')
        self.assertEqual(result['type'], 'table')
        self.assertEqual(result['lineageTag'], '12345')

    def test_columns(self):
        content = """
table MyTable
	column Column1
		dataType: string
		summarizeBy: none

	column Column2
		dataType: int64
"""
        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        self.assertIn('columns', result)
        self.assertEqual(len(result['columns']), 2)
        
        col1 = result['columns'][0]
        self.assertEqual(col1['name'], 'Column1')
        self.assertEqual(col1['dataType'], 'string')
        
        col2 = result['columns'][1]
        self.assertEqual(col2['name'], 'Column2')
        self.assertEqual(col2['dataType'], 'int64')

    def test_multiline_expression(self):
        # Note: In the test string, we need to be careful with indentation.
        # The parser expects tabs.
        content = "table MyTable\n" \
                  "\tpartition MyPartition = m\n" \
                  "\t\tsource = \n" \
                  "\t\t\tlet\n" \
                  "\t\t\t    Source = Sql.Database(\"Server\", \"DB\")\n" \
                  "\t\t\tin\n" \
                  "\t\t\t    Source"
        
        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        self.assertIn('partitions', result)
        partition = result['partitions'][0]
        source = partition['source']
        
        self.assertIn('Sql.Database', source)
        # Verify normalization: common indentation (3 tabs) should be removed
        lines = source.split('\n')
        self.assertTrue(lines[0].startswith('let'))
        self.assertTrue(lines[1].strip().startswith('Source'))

    def test_annotations(self):
        content = """
table MyTable
	annotation PBI_ResultType = Table
	annotation 'Complex Name' = Value
"""
        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        self.assertIn('annotations', result)
        self.assertEqual(len(result['annotations']), 2)
        self.assertEqual(result['annotations'][0]['name'], 'PBI_ResultType')
        self.assertEqual(result['annotations'][0]['value'], 'Table')

    def test_source_details_extraction(self):
        content = """
table MyTable
	partition MyPartition = m
		source = 
			let
			    Source = Sql.Database("Server", "DB"),
			    Data1 = Source{[Schema="dbo",Item="Table1"]}[Data],
			    Data2 = Source{[Schema="sales",Item="FactSales"]}[Data]
			in
			    Data2
"""
        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        partition = result['partitions'][0]
        self.assertIn('sourceDetails', partition)
        
        details = partition['sourceDetails']
        self.assertEqual(len(details), 2)
        
        self.assertEqual(details[0]['schema'], 'dbo')
        self.assertEqual(details[0]['item'], 'Table1')
        
        self.assertEqual(details[1]['schema'], 'sales')
        self.assertEqual(details[1]['item'], 'FactSales')

    def test_base64_extraction(self):
        content = """
table ReportPages
	partition ReportPages = m
		source = 
			let
			    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i45WcqnMS8zNTFZwyy9KTU4sLlGK1YlWcivKr0rNQxULKUrNS1FIqlQIqSxIVYBqwyID0asUGwsA", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [PageName = _t]),
			    #"Changed Type" = Table.TransformColumnTypes(Source,{{"PageName", type text}})
			in
			    #"Changed Type"
"""
        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        partition = result['partitions'][0]
        self.assertIn('sourceDetails', partition)
        
        details = partition['sourceDetails']
        # Should have one entry for the base64 content
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['contentType'], 'decompressed_json')
        # We can check if the content contains expected substrings (I don't know the exact decoded content yet, but I assume it's valid JSON-like structure or text)
        self.assertIsInstance(details[0]['content'], str)
        self.assertTrue(len(details[0]['content']) > 0)

    def test_measures(self):
        # Scenario 1: Measure with ``` block (indented 3 tabs)
        # Scenario 2: Simple inline measure
        # Scenario 3: Indented block without delimiters
        content = "table KeyMeasures\n" \
                  "\tmeasure 'Dynamic Forecast NY' = ```\n" \
                  "\t\t\t\n" \
                  "\t\t\t\n" \
                  "\t\t\tCALCULATE(\n" \
                  "\t\t\t    SUM ( Dynamic_and_Snapshot[VolsPipelineA] )\n" \
                  "\t\t\t)\n" \
                  "\t\t\t\n" \
                  "\t\t\t```\n" \
                  "\t\tformatString: 0\n" \
                  "\t\tdisplayFolder: Dynamic\n" \
                  "\n" \
                  "\tmeasure 'Simple Measure' = SUM(Table[Col])\n" \
                  "\t\tformatString: 0\n" \
                  "\n" \
                  "\tmeasure 'Indented Block' = \n" \
                  "\t\t\t\n" \
                  "\t\t\tVAR x = 1\n" \
                  "\t\t\tRETURN x\n" \
                  "\t\tformatString: #\n"

        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        self.assertIn('measures', result)
        measures = result['measures']
        self.assertEqual(len(measures), 3)
        
        # Check Measure 1
        m1 = measures[0]
        self.assertEqual(m1['name'], 'Dynamic Forecast NY')
        self.assertEqual(m1['formatString'], '0')
        self.assertEqual(m1['displayFolder'], 'Dynamic')
        self.assertIn('CALCULATE', m1['expression'])
        
        # Check Measure 2
        m2 = measures[1]
        self.assertEqual(m2['name'], 'Simple Measure')
        self.assertEqual(m2['expression'], 'SUM(Table[Col])')
        self.assertEqual(m2['formatString'], '0')

        # Check Measure 3
        m3 = measures[2]
        self.assertEqual(m3['name'], 'Indented Block')
        self.assertIn('VAR x = 1', m3['expression'])
        self.assertEqual(m3['formatString'], '#')

    def test_relationships(self):
        content = """
relationship 3e854db7-a13c-4e2c-849d-ccc951acba01
	joinOnDateBehavior: datePartOnly
	fromColumn: DimCountry.loaddate
	toColumn: LocalDateTable_5a13719e-1f5e-4327-aa48-e42d38b532fb.Date

relationship 6a714e8c-01ad-40bf-b082-bc734e0434db
	fromColumn: DimRegion.loaddate
	toColumn: LocalDateTable_9acbb5a2-1056-4af2-897a-95f9dcbd723b.Date
"""
        self.write_tmdl(content)
        parser = TmdlParser(self.test_file_path)
        result = parser.parse()
        
        self.assertIn('relationships', result)
        rels = result['relationships']
        self.assertEqual(len(rels), 2)
        
        rel1 = rels[0]
        self.assertEqual(rel1['name'], '3e854db7-a13c-4e2c-849d-ccc951acba01')
        self.assertEqual(rel1['type'], 'relationship')
        self.assertEqual(rel1['joinOnDateBehavior'], 'datePartOnly')
        self.assertEqual(rel1['fromColumn'], 'DimCountry.loaddate')
        
        rel2 = rels[1]
        self.assertEqual(rel2['name'], '6a714e8c-01ad-40bf-b082-bc734e0434db')
        self.assertEqual(rel2['fromColumn'], 'DimRegion.loaddate')

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import shutil
import tempfile
import json
from pbip_parser import PbipParser

class TestPbipParser(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the PBIP structure
        self.test_dir = tempfile.mkdtemp()
        
        # Create PBIP structure
        self.pbip_folder = os.path.join(self.test_dir, "TestReport.pbip")
        os.makedirs(self.pbip_folder)
        
        self.semantic_model_folder = os.path.join(self.pbip_folder, "TestModel.SemanticModel")
        os.makedirs(self.semantic_model_folder)
        
        self.definition_folder = os.path.join(self.semantic_model_folder, "definition")
        os.makedirs(self.definition_folder)
        
        # Create dummy TMDL files
        with open(os.path.join(self.definition_folder, "database.tmdl"), 'w') as f:
            f.write("database TestDB\n\tcompatibilityLevel: 1567\n")
            
        with open(os.path.join(self.definition_folder, "model.tmdl"), 'w') as f:
            f.write("model Model\n\tculture: en-US\n")
            
        # Create tables folder and a table
        self.tables_folder = os.path.join(self.definition_folder, "tables")
        os.makedirs(self.tables_folder)
        
        with open(os.path.join(self.tables_folder, "DimDate.tmdl"), 'w') as f:
            f.write("table DimDate\n\tcolumn Date\n\t\tdataType: dateTime\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parse_pbip_structure(self):
        # Ensure the config file exists in the current directory (where the test runs)
        # We assume pbip_model_definition.json is in the same folder as this test script
        
        parser = PbipParser(self.pbip_folder)
        result = parser.parse()
        
        self.assertIsNotNone(result)
        
        # Check database
        self.assertIn('database', result)
        self.assertEqual(result['database']['name'], 'TestDB')
        
        # Check model
        self.assertIn('model', result)
        self.assertEqual(result['model']['name'], 'Model')
        
        # Check tables
        self.assertIn('tables', result)
        self.assertEqual(len(result['tables']), 1)
        self.assertEqual(result['tables'][0]['name'], 'DimDate')

if __name__ == '__main__':
    unittest.main()

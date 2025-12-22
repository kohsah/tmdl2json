import json
import argparse
import sys

def generate_mermaid_erd(json_data):
    lines = ["erDiagram"]
    
    # Process Tables
    tables = json_data.get("tables", [])
    processed_tables = set()
    
    for table in tables:
        table_name = table.get("name")
        if not table_name:
            continue
        lower_table_name = table_name.lower()
        if "datetabletemplate" in lower_table_name or "localdatetable" in lower_table_name:
            continue
        
        processed_tables.add(table_name)
        
        # Sanitize table name for Mermaid
        # We use quotes for table names to handle spaces and special chars
        safe_table_name = f'"{table_name}"'
        
        lines.append(f"    {safe_table_name} {{")
        
        columns = table.get("columns", [])
        for col in columns:
            col_name = col.get("name")
            raw_data_type = col.get("dataType", "string")
            
            # Map TMDL data types to standard ERD types
            # int64 -> int
            # double -> float
            # dateTime -> datetime
            # string -> string
            # boolean -> boolean
            # decimal -> decimal
            # binary -> blob
            
            dtype_map = {
                "int64": "int",
                "double": "float",
                "dateTime": "datetime",
                "boolean": "boolean",
                "decimal": "decimal",
                "binary": "blob",
                "string": "string"
            }
            
            data_type = dtype_map.get(raw_data_type, raw_data_type)
            
            # Clean up column name for display
            # Mermaid attributes: type name
            # According to ERD.md, attributes are "type name".
            # The name should NOT be quoted unless it contains spaces or special characters?
            # ERD.md examples: string firstName, string custNumber.
            # But what if the name has spaces?
            # ERD.md doesn't explicitly say names with spaces are supported in attributes without quotes, 
            # but usually for Mermaid entity names they are.
            # However, looking at the user request "do not quote field names in tables".
            # This implies we should just output the name directly.
            # But we must handle spaces. In Mermaid ERD, attribute names with spaces are usually problematic or need underscores.
            # Or maybe the user means "don't wrap the whole thing in quotes".
            # Let's try to replace spaces with underscores to be safe and unquoted, 
            # OR just output it as is if it has no spaces.
            # If it has spaces, maybe we SHOULD quote it?
            # Re-reading user input: "see the documentation, do not quote field names in tables"
            # Documentation example:
            #     CUSTOMER {
            #         string name
            #         string custNumber
            #         string sector
            #     }
            # It seems standard attributes don't use quotes.
            # Let's strip quotes if we were adding them, and sanitize the name.
            # If the name has spaces, Mermaid might fail or truncate.
            # Let's assume we should replace spaces with underscores or keep it as is if Mermaid supports it.
            # Actually, standard Mermaid ERD attribute names shouldn't have spaces usually.
            # But in Power BI, column names OFTEN have spaces (e.g. "Order Date").
            # Let's try replacing spaces with underscores for the attribute name in the diagram
            # to ensure valid syntax without quotes.
            
            display_name = col_name
            if "=" in display_name:
                display_name = display_name.split("=", 1)[0].strip()
            safe_col_name = display_name.replace(" ", "_").replace('"', '').replace("'", "")
            lines.append(f'        {data_type} {safe_col_name}')
            
        lines.append("    }")

    # Process Relationships
    relationships = json_data.get("relationships", [])
    for rel in relationships:
        from_table = rel.get("fromTable")
        to_table = rel.get("toTable")
        
        if not from_table or not to_table:
            continue
        lf = from_table.lower()
        lt = to_table.lower()
        if "datetabletemplate" in lf or "localdatetable" in lf or "datetabletemplate" in lt or "localdatetable" in lt:
            continue
            
        # Ensure tables exist (or at least are referenced safely)
        # If a table in relationship wasn't in "tables" list, we still render the relationship
        # but the table definition might be missing columns.
        
        from_col = rel.get("fromColumnName", "")
        to_col = rel.get("toColumnName", "")
        
        # Determine Cardinality
        # Power BI Default: Many-to-One (from -> to)
        # fromSide: Many
        # toSide: One
        
        # Defaults
        # ERD.md Syntax:
        # }o : Zero or more (no upper limit)
        # || : Exactly one
        # |{ : One or more (no upper limit)
        # |o : Zero or one
        
        # Power BI Relationships:
        # Typically "Many to One" means (*) -> (1)
        # The 'from' side is the Many side.
        # The 'to' side is the One side.
        
        # However, standard Power BI relationships are usually "Zero or More" to "Exactly One" (or "Zero or One" if nullable)
        # For simplicity and typical representation:
        left_card = "}o" # Zero or more
        right_card = "||" # Exactly one
        
        # Check specific cardinality overrides
        if rel.get("toCardinality", "").lower() == "many":
            right_card = "o{" # Zero or more
            
        # Cross filtering behavior could imply other nuances, but structure is primary.
        
        # Relationship Type
        # ERD.md supports identifying (--) and non-identifying (..)
        # Power BI relationships are typically non-identifying in the strict sense (tables exist independently),
        # but often modeled as solid lines in tools.
        # However, to be precise with Mermaid's definition: "non-identifying ... can exist without the other"
        # In PBI, dimensions and facts exist independently.
        # So we should probably use .. (dotted) for non-identifying.
        # But commonly ERDs use solid lines. Let's stick to solid (--) for visual clarity unless requested otherwise,
        # or better, use .. if we want to be semantically strict about "non-identifying".
        # Let's use -- (identifying/solid) as it's the default most users expect for "Foreign Key" style links.
        # But wait, ERD.md says: "non-identifying relationship that we might specify in Mermaid as: ... .. ..."
        # Let's stick to the code's current solid line usage as it matches the previous output which the user saw,
        # unless we want to change to ..
        # The user asked to "use ONLY the prescribed syntax in this document".
        # The document allows both.
        # Let's keep -- as it maps to the standard "relationship" concept in PBI Desktop UI (solid line).
        
        # Wait, PBI uses:
        # Active relationship: Solid line
        # Inactive relationship: Dotted line
        
        # Let's check if relationship is active?
        # The JSON might not have 'isActive' (defaults to true).
        is_active = rel.get("isActive", True)
        
        connector = "--" if is_active else ".."
        
        # Label for the relationship
        # According to ERD.md:
        # <first-entity> [<relationship> <second-entity> : <relationship-label>]
        # The label should be quoted
        label = f"{from_col} to {to_col}"
        
        # Use proper syntax with quotes for entities
        lines.append(f'    "{from_table}" {left_card}{connector}{right_card} "{to_table}" : "{label}"')

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate Mermaid ERD from TMDL JSON output")
    parser.add_argument("input_file", help="Path to the JSON input file")
    parser.add_argument("--output", "-o", help="Path to output Mermaid file (e.g. output.mmd or output.md)")
    
    args = parser.parse_args()
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        mermaid_content = generate_mermaid_erd(data)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                # If it's a markdown file, wrap in code block
                if args.output.endswith('.md'):
                    f.write("```mermaid\n")
                    f.write(mermaid_content)
                    f.write("\n```")
                else:
                    f.write(mermaid_content)
            print(f"ERD generated at: {args.output}")
        else:
            print(mermaid_content)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

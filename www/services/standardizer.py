import pandas as pd
from www.services.format_functions import format_sr_column

class OpenAlexStandardizer:
    """
    Phase 2 & 4: Transform & Calculate Fields (Standardizer).
    
    This class handles the Transformation phase of the ETL pipeline. It maps the 
    proprietary, deeply-nested JSON structure returned by the OpenAlex API into 
    the flat, strict Web of Science (WoS) format required by Bibliometrix-Python.
    
    It implements the 'Lookup Strategy' to map column names and enforce Data Types.
    """
    
    @staticmethod
    def _reconstruct_abstract(inverted_index: dict) -> str:
        """
        OpenAlex abstracts are provided as inverted indices (for copyright reasons).
        This helper parses the inverted index dictionary and reconstructs the full 
        abstract string.
        """
        if not inverted_index:
            return ""
        # The inverted index maps words to list of positions
        # e.g. {"The": [0], "quick": [1], ...}
        # Find the max position
        max_pos = max([pos for positions in inverted_index.values() for pos in positions], default=-1)
        if max_pos == -1:
            return ""
            
        words = [""] * (max_pos + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(words)

    @staticmethod
    def _format_authors(authorships: list) -> tuple:
        """Returns (AU list, AF list)"""
        au = []
        af = []
        for authorship in authorships:
            author = authorship.get("author", {})
            name = author.get("display_name", "")
            if not name:
                continue
            
            af.append(name)
            
            # Convert to "Surname, Initials"
            parts = name.split()
            if len(parts) > 1:
                surname = parts[-1]
                initials = " ".join([p[0].upper() + "." for p in parts[:-1]])
                au.append(f"{surname}, {initials}")
            else:
                au.append(f"{name},")
                
        return au, af

    @staticmethod
    def _format_affiliations(authorships: list) -> list:
        affiliations = []
        for authorship in authorships:
            institutions = authorship.get("institutions", [])
            for inst in institutions:
                inst_name = inst.get("display_name", "")
                if inst_name and inst_name not in affiliations:
                    affiliations.append(inst_name)
        return affiliations

    def standardize(self, raw_data: list) -> pd.DataFrame:
        """
        Maps raw OpenAlex JSON items to WoS Standard Schema.
        """
        records = []
        
        for item in raw_data:
            # Multi-value field processing
            au, af = self._format_authors(item.get("authorships", []))
            c1 = self._format_affiliations(item.get("authorships", []))
            
            cr = []
            for ref in item.get("referenced_works", []):
                cr.append(str(ref))
                
            de = [kw.get("display_name") for kw in item.get("keywords", [])]
            id_kw = [c.get("display_name") for c in item.get("concepts", [])]
            
            # Abstract
            abstract = ""
            if "abstract_inverted_index" in item and item["abstract_inverted_index"]:
                abstract = self._reconstruct_abstract(item["abstract_inverted_index"])
                
            biblio = item.get("biblio", {}) or {}
            
            pmid = ""
            ids = item.get("ids", {})
            if "pmid" in ids:
                pmid = ids["pmid"].split("/")[-1]
                
            source_info = item.get("primary_location", {}).get("source", {}) or {}
            
            record = {
                "DB": "OPENALEX",
                "UT": str(item.get("id", "")),
                "DI": str(item.get("doi", "") or "").replace("https://doi.org/", ""),
                "PMID": pmid,
                "TI": str(item.get("title", "") or ""),
                "SO": str(source_info.get("display_name", "") or ""),
                "JI": str(source_info.get("host_organization_name", "") or ""),
                "PY": str(item.get("publication_year", "") or ""),
                "DT": str(item.get("type", "") or ""),
                "LA": str(item.get("language", "") or ""),
                "TC": int(item.get("cited_by_count", 0) or 0),
                "AU": au,
                "AF": af,
                "C1": c1,
                "RP": "",
                "CR": cr,
                "DE": de,
                "ID": id_kw,
                "AB": abstract,
                "VL": str(biblio.get("volume", "") or ""),
                "IS": str(biblio.get("issue", "") or ""),
                "BP": str(biblio.get("first_page", "") or ""),
                "EP": str(biblio.get("last_page", "") or "")
            }
            records.append(record)
            
        df = pd.DataFrame(records)
        
        # Convert PY to numeric for plotting (Annual Scientific Production expects numbers)
        df['PY'] = pd.to_numeric(df['PY'], errors='coerce')
        
        # Calculate SR using the existing function
        df['SR'] = df.apply(self._calculate_sr, axis=1)
        
        return df
        
    def _calculate_sr(self, row: pd.Series) -> str:
        """
        Invokes the existing format_sr_column function from Bibliometrix-Python
        by mocking the raw Web of Science format.
        """
        # format_sr_column expects a Web_of_Science raw entry format where fields are lists.
        # It reads AU, PY, and SO.
        au_raw = [row['AU'][0]] if row['AU'] else ["Unknown, U."]
        py_raw = [row['PY']] if row['PY'] else [""]
        so_raw = [row['SO']] if row['SO'] else [""]
        
        dummy_entry = {
            'AU': au_raw,
            'PY': py_raw,
            'SO': so_raw
        }
        
        try:
            return format_sr_column(dummy_entry, 'Web_of_Science', '.txt')
        except Exception as e:
            return ""

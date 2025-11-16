# src/schema.py
from typing import List, Dict, Any
import re
from datetime import datetime

class SchemaInferer:
    @staticmethod
    def infer(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Infer a simple schema from a list of dict records.
        Returns a dict with 'fields' and 'primary_key_candidates'.
        Important: the returned 'fields' will contain JSON/BSON-serializable types only.
        """
        if not records:
            return {"fields": {}, "primary_key_candidates": []}

        field_info: Dict[str, Dict[str, Any]] = {}
        for rec in records:
            if not isinstance(rec, dict):
                continue
            for k, v in rec.items():
                if k not in field_info:
                    field_info[k] = {"types": set(), "nulls": 0, "examples": []}
                # record python type name (simple)
                field_info[k]["types"].add(type(v).__name__)
                if v is None:
                    field_info[k]["nulls"] += 1
                if len(field_info[k]["examples"]) < 3:
                    field_info[k]["examples"].append(v)

        # convert sets to lists and add suggested_type / nullable
        for k, info in list(field_info.items()):
            types_set = info.get("types", set())
            types_list = sorted(list(types_set))
            info["types"] = types_list  # lists are BSON-serializable

            # determine suggested_type
            if "int" in types_list and "float" not in types_list:
                info["suggested_type"] = "integer"
            elif "float" in types_list or ("int" in types_list and "float" in types_list):
                info["suggested_type"] = "decimal"
            elif "str" in types_list:
                sample = str(info["examples"][0]) if info["examples"] else ""
                if re.match(r"^\d{4}-\d{2}-\d{2}", sample):
                    info["suggested_type"] = "date"
                else:
                    info["suggested_type"] = "string"
            else:
                # fallback
                info["suggested_type"] = types_list[0] if types_list else "string"

            info["nullable"] = info.get("nulls", 0) > 0

        # primary key candidates (simple heuristic)
        pk_candidates = [k for k in ["id", "key"] if k in field_info and field_info[k].get("nulls", 0) == 0]

        return {"fields": field_info, "primary_key_candidates": pk_candidates}

class SchemaEvolver:
    @staticmethod
    def evolve(current: Dict[str, Any], new_guess: Dict[str, Any], source_id: str) -> tuple[Dict[str, Any], Dict]:
        """
        Compare current schema and new guess, produce evolved schema and a diff.
        """
        old_fields = current.get("fields", {})
        new_fields = new_guess.get("fields", {})
        diff = {"added": [], "removed": [], "type_changed": [], "nullable_changed": []}

        for k, new_info in new_fields.items():
            if k not in old_fields:
                diff["added"].append(k)
            else:
                old_info = old_fields[k]
                # compare suggested_type safely
                if old_info.get("suggested_type") != new_info.get("suggested_type"):
                    diff["type_changed"].append((k, old_info.get("suggested_type"), new_info.get("suggested_type")))
                if old_info.get("nullable") != new_info.get("nullable"):
                    diff["nullable_changed"].append(k)

        for k in old_fields:
            if k not in new_fields:
                diff["removed"].append(k)

        version = current.get("version", 0) + 1
        migration_notes = []
        if diff["added"]:
            migration_notes.append(f"Added: {', '.join(diff['added'])}")
        if diff["type_changed"]:
            for f, o, n in diff["type_changed"]:
                migration_notes.append(f"{f}: {o} to {n}")

        evolved = {
            "schema_id": f"schema_v{version}",
            "source_id": source_id,
            "version": version,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "compatible_dbs": ["mongodb", "postgresql"],
            "fields": new_fields,
            "primary_key_candidates": new_guess.get("primary_key_candidates", []),
            "migration_notes": "; ".join(migration_notes) if migration_notes else None
        }
        return evolved, diff

"""
FleetGuard — Copilot Tools & Entity Resolution Engine
Defines operational read tools, controlled write tools, and entity resolution
strictly scoped to the authenticated user's fleet.
"""

import re
import difflib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Sequence
from sqlalchemy import select, func, desc, or_

from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus, DutyStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation, LocationSource
from models.asset_domain import Asset, AssetType
from models.operational_event import EntityType
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus
from models.ticket import Ticket
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from services.copilot_proposal import TripProposalManager

logger = logging.getLogger("fleetguard.copilot.tools")

# GPS Freshness Thresholds (Standard: 15 minutes fresh, 24-hour historical window)
GPS_FRESH_THRESHOLD_SECONDS = 900.0  # 15 minutes
GPS_STALE_MAX_WINDOW_SECONDS = 86400.0  # 24 hours


# ==============================================================================
# ENTITY RESOLVER
# ==============================================================================

class CopilotEntityResolver:
    """
    Intelligently resolves informal names, partial plates, ordinals,
    and fuzzy search queries into database entities for a specific fleet.
    """

    VEHICLE_STOP_WORDS = {
        "my", "the", "a", "an", "this", "that", "truck", "trucks",
        "lorry", "lorries", "vehicle", "vehicles", "car", "cars", "van", "vans"
    }

    DRIVER_STOP_WORDS = {
        "my", "the", "a", "an", "this", "that", "driver", "drivers",
        "pilot", "pilots", "operator", "operators", "chauffeur"
    }

    ORDINALS = {
        "first": 1, "1st": 1,
        "second": 2, "2nd": 2,
        "third": 3, "3rd": 3,
        "fourth": 4, "4th": 4,
        "fifth": 5, "5th": 5,
        "sixth": 6, "6th": 6,
        "seventh": 7, "7th": 7,
        "eighth": 8, "8th": 8,
        "ninth": 9, "9th": 9,
        "tenth": 10, "10th": 10,
    }

    @staticmethod
    def _normalize(text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r"[^a-zA-Z0-9]", "", text).lower()

    @classmethod
    def _clean_words(cls, text: str, stop_words: set) -> str:
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        filtered = [w for w in words if w not in stop_words]
        return "".join(filtered) if filtered else "".join(words)

    @classmethod
    def resolve_vehicle(
        cls,
        vehicles: Sequence[Vehicle],
        query: str
    ) -> Dict[str, Any]:
        """
        Resolves query to a vehicle:
        Returns:
            {"status": "EXACT", "vehicle": Vehicle}
            {"status": "AMBIGUOUS", "candidates": [Vehicle, ...]}
            {"status": "NOT_FOUND", "available": [Vehicle, ...]}
        """
        if not vehicles:
            return {"status": "NOT_FOUND", "message": "No vehicles found in fleet.", "available": []}

        norm_query = cls._normalize(query)
        cleaned = cls._clean_words(query, cls.VEHICLE_STOP_WORDS)
        if not norm_query:
            return {"status": "AMBIGUOUS", "candidates": list(vehicles)}

        # 1. Exact registration match (e.g. "RJ14UF0089" or "RJ 14 UF 0089")
        for v in vehicles:
            v_norm = cls._normalize(v.registration_number)
            if v_norm == norm_query or (cleaned and v_norm == cleaned):
                return {"status": "EXACT", "vehicle": v}

        # 2. Database ID match
        try:
            val_id = int(query.strip())
            for v in vehicles:
                if v.id == val_id:
                    return {"status": "EXACT", "vehicle": v}
        except ValueError:
            pass

        # 3. Ordinal / Truck index matching (e.g. "Truck 1", "Truck 01", "Truck 2", "Truck 02")
        sorted_by_id = sorted(vehicles, key=lambda x: x.id)

        # Word ordinals: "first truck", "second truck", etc.
        for word in query.lower().split():
            if word in cls.ORDINALS:
                idx = cls.ORDINALS[word] - 1
                if 0 <= idx < len(sorted_by_id):
                    return {"status": "EXACT", "vehicle": sorted_by_id[idx]}

        ordinal_pattern = re.search(r"(?:truck|vehicle|lorry)\s*(?:no\.?|#)?\s*0*([1-9]\d*)", query, re.IGNORECASE)
        if ordinal_pattern:
            idx = int(ordinal_pattern.group(1)) - 1
            if 0 <= idx < len(sorted_by_id):
                return {"status": "EXACT", "vehicle": sorted_by_id[idx]}

        # Check for standalone numbers like "02" or "2" if only a few trucks exist
        if re.match(r"^0*([1-9]\d*)$", query.strip()):
            idx = int(query.strip()) - 1
            if 0 <= idx < len(sorted_by_id):
                return {"status": "EXACT", "vehicle": sorted_by_id[idx]}

        # 4. Suffix or Substring match on registration number (e.g., "0089", "UF0089", "RJ14") or make/model
        sub_matches: List[Vehicle] = []
        for v in vehicles:
            v_norm = cls._normalize(v.registration_number)
            v_make = cls._normalize(v.make)
            v_model = cls._normalize(v.model)
            v_full = f"{v_make}{v_model}"

            matched = False
            # Check registration suffix/substring
            if norm_query in v_norm or (cleaned and cleaned in v_norm):
                matched = True
            elif len(v_norm) >= 4 and (v_norm in norm_query or (cleaned and v_norm in cleaned)):
                matched = True
            # Check make and model
            elif cleaned:
                if cleaned == v_make or (len(cleaned) >= 3 and cleaned in v_make) or (len(v_make) >= 3 and v_make in cleaned):
                    matched = True
                elif cleaned == v_model or (len(cleaned) >= 3 and cleaned in v_model) or (len(v_model) >= 3 and v_model in cleaned):
                    matched = True
                elif cleaned in v_full or (len(v_full) >= 3 and v_full in cleaned):
                    matched = True
            elif norm_query:
                if (len(norm_query) >= 3 and norm_query in v_full) or (len(v_full) >= 3 and v_full in norm_query):
                    matched = True

            if matched and v not in sub_matches:
                sub_matches.append(v)

        if len(sub_matches) == 1:
            return {"status": "EXACT", "vehicle": sub_matches[0]}
        elif len(sub_matches) > 1:
            return {"status": "AMBIGUOUS", "candidates": sub_matches}

        # 5. Fuzzy string matching
        scored: List[Tuple[float, Vehicle]] = []
        for v in vehicles:
            candidates_strings = [
                v.registration_number.lower(),
                cls._normalize(v.registration_number),
                f"{v.make or ''} {v.model or ''}".strip().lower(),
            ]
            best_score = max(
                difflib.SequenceMatcher(None, (cleaned or query).lower(), s).ratio()
                for s in candidates_strings if s
            )
            if best_score >= 0.55:
                scored.append((best_score, v))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            if len(scored) == 1 or (scored[0][0] - scored[1][0] >= 0.2 and scored[0][0] >= 0.7):
                return {"status": "EXACT", "vehicle": scored[0][1]}
            else:
                return {
                    "status": "AMBIGUOUS",
                    "candidates": [item[1] for item in scored[:4]]
                }

        return {
            "status": "NOT_FOUND",
            "message": f"Could not find any vehicle matching '{query}'.",
            "available": list(vehicles)
        }

    @classmethod
    def resolve_driver(
        cls,
        drivers: Sequence[Driver],
        query: str
    ) -> Dict[str, Any]:
        """
        Resolves query to a driver record in the fleet.
        """
        if not drivers:
            return {"status": "NOT_FOUND", "message": "No drivers found in fleet.", "available": []}

        norm_query = cls._normalize(query)
        cleaned = cls._clean_words(query, cls.DRIVER_STOP_WORDS)
        if not norm_query:
            return {"status": "AMBIGUOUS", "candidates": list(drivers)}

        # Exact Name or Phone or Employee ID
        for d in drivers:
            d_norm = cls._normalize(d.name)
            if d_norm == norm_query or (cleaned and d_norm == cleaned):
                return {"status": "EXACT", "driver": d}
            if d.phone_number and (cls._normalize(d.phone_number) == norm_query or (cleaned and cls._normalize(d.phone_number) == cleaned)):
                return {"status": "EXACT", "driver": d}
            if d.employee_id and (cls._normalize(d.employee_id) == norm_query or (cleaned and cls._normalize(d.employee_id) == cleaned)):
                return {"status": "EXACT", "driver": d}

        # Substring in name
        sub_matches: List[Driver] = []
        for d in drivers:
            d_norm = cls._normalize(d.name)
            matched = False
            if cleaned and (cleaned in d_norm or d_norm in cleaned):
                matched = True
            elif norm_query and (norm_query in d_norm or d_norm in norm_query):
                matched = True

            if matched and d not in sub_matches:
                sub_matches.append(d)

        if len(sub_matches) == 1:
            return {"status": "EXACT", "driver": sub_matches[0]}
        elif len(sub_matches) > 1:
            return {"status": "AMBIGUOUS", "candidates": sub_matches}

        # Fuzzy name matching
        scored: List[Tuple[float, Driver]] = []
        for d in drivers:
            score = difflib.SequenceMatcher(None, (cleaned or query).lower(), d.name.lower()).ratio()
            if score >= 0.6:
                scored.append((score, d))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            if len(scored) == 1 or (scored[0][0] - scored[1][0] >= 0.2 and scored[0][0] >= 0.75):
                return {"status": "EXACT", "driver": scored[0][1]}
            else:
                return {"status": "AMBIGUOUS", "candidates": [item[1] for item in scored[:4]]}

        return {
            "status": "NOT_FOUND",
            "message": f"Could not find any driver matching '{query}'.",
            "available": list(drivers)
        }


# ==============================================================================
# TOOL SCHEMAS FOR OPENAI / GEMINI FUNCTION CALLING
# ==============================================================================

COPILOT_TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_fleet_summary",
            "description": "Returns operational statistics for the authenticated user's fleet: counts of active, inactive, and maintenance vehicles, active trips, and active drivers.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_vehicles",
            "description": "Retrieves the user's fleet vehicles with IDs, registration numbers, make/model specs, and current operational status. Supports filtering by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["ACTIVE", "INACTIVE", "MAINTENANCE", "ALL"],
                        "nullable": True,
                        "description": "Optional operational status filter (or null for all)."
                    },
                    "search": {
                        "type": "string",
                        "nullable": True,
                        "description": "Optional text search for registration or make/model (or null)."
                    },
                    "limit": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Maximum number of vehicles to retrieve (default 20, max 100)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_details",
            "description": "Retrieves comprehensive information for a specific vehicle by database ID or informal registration/name query. Includes assigned driver and maintenance status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vehicle_id": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Exact database ID of the vehicle (if known, or null)."
                    },
                    "query": {
                        "type": "string",
                        "nullable": True,
                        "description": "Informal vehicle name, label, or partial registration number (e.g. 'Truck 02', 'RJ14UF0089') (or null)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_location",
            "description": "Retrieves the latest available GPS location coordinates, update timestamp, source (phone/hardware), and staleness status for a vehicle or the entire fleet. Pass query='all' or query='both' to inspect all vehicles' locations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vehicle_id": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Exact database ID of the vehicle (if known, or null)."
                    },
                    "query": {
                        "type": "string",
                        "nullable": True,
                        "description": "Informal vehicle name, label, partial registration (e.g. 'Truck 02', '0089'), or 'all'/'both' for all fleet vehicles (or null)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_drivers",
            "description": "Retrieves the list of drivers registered to the fleet, their duty status, active trip status, and current availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_active": {
                        "type": "boolean",
                        "nullable": True,
                        "description": "Filter by active status in fleet (true for active only, false for inactive, or null for all)."
                    },
                    "available_only": {
                        "type": "boolean",
                        "nullable": True,
                        "description": "Filter to only drivers who are ACTIVE and NOT currently on an in-progress trip (default false)."
                    },
                    "search": {
                        "type": "string",
                        "nullable": True,
                        "description": "Optional name, phone, or employee ID search (or null if not filtering)."
                    },
                    "limit": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Maximum drivers to return (default 20, max 100)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_trips",
            "description": "Retrieves trip records for the fleet with status, origin, destination, vehicle, driver, and dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["CREATED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "ALL"],
                        "nullable": True,
                        "description": "Filter trips by operational status (or null)."
                    },
                    "search": {
                        "type": "string",
                        "nullable": True,
                        "description": "Search by city, trip ID, or location (or null)."
                    },
                    "limit": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Maximum trips to return (default 20, max 100)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trip_details",
            "description": "Retrieves complete details for a specific trip by database ID or business ID (e.g. TRP-101).",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Primary key ID of the trip (or null)."
                    },
                    "trip_business_id": {
                        "type": "string",
                        "nullable": True,
                        "description": "Trip business ID (e.g., 'TRP-101', 'TRP-A1B2C3D4') (or null)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_trip_proposal",
            "description": "Validates and stages a controlled trip scheduling proposal for user review. Checks vehicle availability and constraints. Does NOT create the trip until confirmed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vehicle_query": {
                        "type": "string",
                        "description": "Vehicle registration, ID, or informal name (e.g. 'Truck 02', 'RJ14UF0089')."
                    },
                    "origin": {
                        "type": "string",
                        "description": "Origin city or departure location."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination city or delivery location."
                    },
                    "planned_start_time": {
                        "type": "string",
                        "description": "Planned departure date and time (ISO format or formatted string, e.g. '2026-10-27T08:00:00')."
                    },
                    "driver_query": {
                        "type": "string",
                        "nullable": True,
                        "description": "Optional driver name, phone, or ID to assign (or null for auto-select or unassigned)."
                    },
                    "planned_distance_km": {
                        "type": "number",
                        "nullable": True,
                        "description": "Optional estimated route distance in km (or null)."
                    },
                    "revenue": {
                        "type": "number",
                        "nullable": True,
                        "description": "Optional expected freight revenue in rupees (or null)."
                    }
                },
                "required": ["vehicle_query", "origin", "destination", "planned_start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_trip_execution",
            "description": "Explicitly confirms and executes a previously staged trip proposal. Enforces single-use idempotency, records the trip in the database, and returns the verified trip ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposal_id": {
                        "type": "string",
                        "description": "The exact proposal ID returned by prepare_trip_proposal (e.g. 'PROP-XXXXX')."
                    }
                },
                "required": ["proposal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_trip_proposal",
            "description": "Cancels an unexecuted pending trip proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposal_id": {
                        "type": "string",
                        "description": "The proposal ID to cancel."
                    }
                },
                "required": ["proposal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fleet_health",
            "description": "Retrieves the overall health, domain risks, findings, and signals for the authenticated user's fleet.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trip_intelligence",
            "description": "Retrieves comprehensive deterministic trip intelligence for a given trip ID, including profitability, anomalies, efficiency scores, and cost breakdowns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "The unique ID of the trip to investigate."
                    }
                },
                "required": ["trip_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_summary",
            "description": "Retrieves a controlled summary of a specific vehicle, including its recent trips and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vehicle_id": {
                        "type": "integer",
                        "description": "The unique ID of the vehicle."
                    }
                },
                "required": ["vehicle_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_related_evidence",
            "description": "Retrieves evidence records associated with a specific entity (like a vehicle or trip) to support investigations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["TRIP", "VEHICLE", "DRIVER", "EXPENSE", "FUEL"],
                        "description": "The domain category of the entity."
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "The identifier of the specific entity instance."
                    }
                },
                "required": ["entity_type", "entity_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expiring_documents",
            "description": "Retrieves a list of documents (e.g., driver licenses, vehicle permits) that are expiring within the next 30 days or have already expired.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense_analytics",
            "description": "Retrieves analytics and aggregations of fleet expenses grouped by category and time period.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_expenses",
            "description": "Retrieves the company's real financial expense records (e.g. FUEL, MAINTENANCE, TOLL) with timestamps, amounts, vehicles, and status. Use this to answer queries about recent or latest fuel expenses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["FUEL", "MAINTENANCE", "TYRE", "TOLL", "PARKING", "SALARY", "ALLOWANCE", "PENALTY", "ALL"],
                        "nullable": True,
                        "description": "Optional category filter (e.g. 'FUEL', or null)."
                    },
                    "vehicle_id": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Optional vehicle ID filter (or null)."
                    },
                    "limit": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Maximum number of expense records to retrieve (default 10, max 100)."
                    }
                },
                "required": []
            }
        }
    }
]


# ==============================================================================
# TOOL IMPLEMENTATION HANDLERS
# ==============================================================================

class CopilotToolExecutor:
    """
    Executes operational tools on behalf of CopilotService.
    All operations are strictly bounded to company_id.
    """

    def __init__(self, uow: Any, company_id: int, user_id: str, user_name: str = "Fleet Manager"):
        self.uow = uow
        self.company_id = int(company_id)
        self.user_id = str(user_id)
        self.user_name = user_name
        self.proposal_manager = TripProposalManager.get_instance()

    def _get_session(self):
        """Safely extracts SQLAlchemy AsyncSession across all UoW flavors."""
        if hasattr(self.uow, "session") and self.uow.session is not None:
            return self.uow.session
        if hasattr(self.uow, "_session") and self.uow._session is not None:
            return self.uow._session
        if hasattr(self.uow, "repositories") and hasattr(self.uow.repositories, "vehicle"):
            return self.uow.repositories.vehicle.db
        raise RuntimeError("No database session available in Unit of Work.")

    @staticmethod
    def _parse_bool(val: Any, default: Optional[bool] = None, param_name: str = "parameter") -> Optional[bool]:
        """
        Parses boolean inputs safely, converting string representations ('true', 'false', '1', '0')
        and treating None / empty values as the default.
        Raises ValueError on malformed inputs.
        """
        if val is None or val == "":
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            if val == 1:
                return True
            if val == 0:
                return False
            raise ValueError(f"Invalid boolean value for '{param_name}': expected 0 or 1, got {val}")
        if isinstance(val, str):
            s = val.strip().lower()
            if s in ("true", "1", "yes", "t", "y"):
                return True
            if s in ("false", "0", "no", "f", "n"):
                return False
            if s in ("none", "null"):
                return default
            raise ValueError(f"Invalid boolean value for '{param_name}': expected true/false, got '{val}'")
        raise ValueError(f"Invalid type for boolean parameter '{param_name}': expected boolean, got {type(val).__name__}")

    @staticmethod
    def _parse_int(
        val: Any,
        default: Optional[int] = None,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
        param_name: str = "parameter"
    ) -> Optional[int]:
        """
        Parses integer inputs safely, converting string representations and validating bounds.
        Treats None / empty values as default.
        Raises ValueError on malformed inputs.
        """
        if val is None or val == "":
            return default
        try:
            if isinstance(val, bool):
                raise ValueError("Boolean passed for integer")
            if isinstance(val, float):
                if not val.is_integer():
                    raise ValueError("Float with decimal passed for integer")
                parsed = int(val)
            else:
                parsed = int(str(val).strip())
        except (ValueError, TypeError):
            raise ValueError(f"Invalid integer value for '{param_name}': expected integer, got '{val}'")

        if min_val is not None and parsed < min_val:
            parsed = min_val
        if max_val is not None and parsed > max_val:
            parsed = max_val
        return parsed

    @staticmethod
    def _parse_str(val: Any, default: Optional[str] = None, param_name: str = "parameter") -> Optional[str]:
        """
        Parses string inputs safely, stripping whitespace and converting None / empty to default.
        """
        if val is None:
            return default
        if isinstance(val, str):
            s = val.strip()
            if not s or s.lower() in ("null", "none"):
                return default
            return s
        s = str(val).strip()
        return s if s else default

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Central tool dispatcher with robust input validation and defensive error recovery."""
        if not isinstance(args, dict):
            args = {}
        try:
            if tool_name == "get_fleet_summary":
                return await self._get_fleet_summary()

            elif tool_name == "list_vehicles":
                status = self._parse_str(args.get("status"), default=None, param_name="status")
                search = self._parse_str(args.get("search"), default=None, param_name="search")
                limit = self._parse_int(args.get("limit"), default=20, min_val=1, max_val=100, param_name="limit")
                return await self._list_vehicles(status=status, search=search, limit=limit)

            elif tool_name == "get_vehicle_details":
                vehicle_id = self._parse_int(args.get("vehicle_id"), default=None, min_val=1, param_name="vehicle_id")
                query = self._parse_str(args.get("query"), default=None, param_name="query")
                return await self._get_vehicle_details(vehicle_id=vehicle_id, query=query)

            elif tool_name == "get_vehicle_location":
                vehicle_id = self._parse_int(args.get("vehicle_id"), default=None, min_val=1, param_name="vehicle_id")
                query = self._parse_str(args.get("query"), default=None, param_name="query")
                return await self._get_vehicle_location(vehicle_id=vehicle_id, query=query)

            elif tool_name == "list_drivers":
                is_active = self._parse_bool(args.get("is_active"), default=None, param_name="is_active")
                available_only = self._parse_bool(args.get("available_only"), default=False, param_name="available_only")
                search = self._parse_str(args.get("search"), default=None, param_name="search")
                limit = self._parse_int(args.get("limit"), default=20, min_val=1, max_val=100, param_name="limit")
                return await self._list_drivers(
                    is_active=is_active,
                    available_only=available_only,
                    search=search,
                    limit=limit
                )

            elif tool_name == "list_trips":
                status = self._parse_str(args.get("status"), default=None, param_name="status")
                search = self._parse_str(args.get("search"), default=None, param_name="search")
                limit = self._parse_int(args.get("limit"), default=20, min_val=1, max_val=100, param_name="limit")
                return await self._list_trips(status=status, search=search, limit=limit)

            elif tool_name == "get_trip_details":
                trip_id = self._parse_int(args.get("trip_id"), default=None, min_val=1, param_name="trip_id")
                trip_business_id = self._parse_str(args.get("trip_business_id"), default=None, param_name="trip_business_id")
                return await self._get_trip_details(trip_id=trip_id, trip_business_id=trip_business_id)

            elif tool_name == "prepare_trip_proposal":
                return await self._prepare_trip_proposal(args)

            elif tool_name == "confirm_trip_execution":
                proposal_id = self._parse_str(args.get("proposal_id"), default=None, param_name="proposal_id")
                return await self._confirm_trip_execution(proposal_id=proposal_id)

            elif tool_name == "cancel_trip_proposal":
                proposal_id = self._parse_str(args.get("proposal_id"), default=None, param_name="proposal_id")
                return await self._cancel_trip_proposal(proposal_id=proposal_id)

            elif tool_name == "get_fleet_health":
                from services.fleet_intelligence_service import FleetIntelligenceService
                svc = FleetIntelligenceService(self.uow)
                report = await svc.get_fleet_health(str(self.company_id))
                return report.model_dump_json()

            elif tool_name == "get_trip_intelligence":
                trip_id = self._parse_int(args.get("trip_id"), default=None, min_val=1, param_name="trip_id")
                return await self._get_trip_intelligence(trip_id)

            elif tool_name == "get_vehicle_summary":
                vehicle_id = self._parse_int(args.get("vehicle_id"), default=None, min_val=1, param_name="vehicle_id")
                return await self._get_vehicle_summary(vehicle_id)

            elif tool_name == "get_related_evidence":
                entity_type = self._parse_str(args.get("entity_type"), default=None, param_name="entity_type")
                entity_id = self._parse_str(args.get("entity_id"), default=None, param_name="entity_id")
                return await self._get_related_evidence(entity_type, entity_id)

            elif tool_name == "get_expiring_documents":
                return await self._get_expiring_documents()

            elif tool_name == "get_expense_analytics":
                return await self._get_expense_analytics()

            elif tool_name == "list_expenses":
                category = self._parse_str(args.get("category"), default=None, param_name="category")
                vehicle_id = self._parse_int(args.get("vehicle_id"), default=None, min_val=1, param_name="vehicle_id")
                limit = self._parse_int(args.get("limit"), default=10, min_val=1, max_val=100, param_name="limit")
                return await self._list_expenses(category=category, vehicle_id=vehicle_id, limit=limit)

            else:
                return json.dumps({"error": f"Unknown tool: '{tool_name}'"})

        except ValueError as ve:
            logger.warning(f"Parameter validation error in tool '{tool_name}': {ve}")
            return json.dumps({
                "error": "Validation Error",
                "message": f"Parameters for tool '{tool_name}' were invalid: {str(ve)}. Please provide valid arguments."
            })
        except PermissionError as pe:
            logger.warning(f"Security boundary violation in tool {tool_name}: {pe}")
            return json.dumps({"error": "Permission Denied", "detail": str(pe)})
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return json.dumps({"error": "Tool Execution Error", "detail": str(e)})

    # --------------------------------------------------------------------------
    # READ-ONLY OPERATIONS
    # --------------------------------------------------------------------------

    async def _get_fleet_summary(self) -> str:
        session = self._get_session()

        # Vehicle counts by status
        veh_stmt = (
            select(Vehicle.status, func.count(Vehicle.id))
            .where(Vehicle.company_id == self.company_id)
            .group_by(Vehicle.status)
        )
        veh_res = await session.execute(veh_stmt)
        status_counts = {"ACTIVE": 0, "INACTIVE": 0, "MAINTENANCE": 0}
        total_vehicles = 0
        for st, count in veh_res:
            key = st.value if hasattr(st, "value") else str(st)
            status_counts[key] = count
            total_vehicles += count

        # Active trips
        trip_stmt = (
            select(func.count(Trip.id))
            .where(Trip.company_id == self.company_id, Trip.status == TripStatus.IN_PROGRESS)
        )
        active_trips_res = await session.execute(trip_stmt)
        active_trips = active_trips_res.scalar_one_or_none() or 0

        # Active drivers
        driver_stmt = (
            select(func.count(Driver.id))
            .where(Driver.company_id == self.company_id, Driver.status == DriverStatus.ACTIVE)
        )
        active_drivers_res = await session.execute(driver_stmt)
        active_drivers = active_drivers_res.scalar_one_or_none() or 0

        summary = {
            "company_id": self.company_id,
            "total_vehicles": total_vehicles,
            "active_vehicles": status_counts.get("ACTIVE", 0),
            "inactive_vehicles": status_counts.get("INACTIVE", 0),
            "maintenance_vehicles": status_counts.get("MAINTENANCE", 0),
            "vehicles_by_status": status_counts,
            "active_trips_in_progress": active_trips,
            "active_drivers": active_drivers
        }
        return json.dumps(summary)

    async def _list_vehicles(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20
    ) -> str:
        vehicles = await self.uow.repositories.vehicle.search_vehicles(
            company_id=self.company_id,
            status=status,
            search=search,
            limit=min(limit or 20, 100)
        )

        records = []
        for v in vehicles:
            st = v.status.value if hasattr(v.status, "value") else str(v.status)
            records.append({
                "vehicle_id": v.id,
                "registration_number": v.registration_number,
                "make": v.make,
                "model": v.model,
                "year": v.year,
                "status": st,
                "fuel_type": v.fuel_type,
                "assigned_driver_id": v.assigned_driver_id
            })

        return json.dumps({
            "total_count": len(records),
            "vehicles": records
        })

    async def _get_vehicle_details(
        self,
        vehicle_id: Optional[int] = None,
        query: Optional[str] = None
    ) -> str:
        session = self._get_session()

        vehicle: Optional[Vehicle] = None
        if vehicle_id is not None:
            vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(int(vehicle_id), self.company_id)
            if not vehicle:
                return json.dumps({"error": f"Vehicle ID {vehicle_id} not found in your fleet."})
        elif query:
            all_vehicles = await self.uow.repositories.vehicle.search_vehicles(
                company_id=self.company_id,
                limit=100
            )
            res = CopilotEntityResolver.resolve_vehicle(all_vehicles, query)
            if res["status"] == "EXACT":
                vehicle = res["vehicle"]
            elif res["status"] == "AMBIGUOUS":
                candidates = [
                    {"vehicle_id": c.id, "registration_number": c.registration_number, "label": f"{c.make or ''} {c.model or ''}".strip()}
                    for c in res["candidates"]
                ]
                return json.dumps({
                    "status": "AMBIGUOUS",
                    "message": f"Multiple vehicles matched '{query}'. Please specify which vehicle you mean.",
                    "matching_choices": candidates
                })
            else:
                available = [
                    {"vehicle_id": v.id, "registration_number": v.registration_number, "label": f"{v.make or ''} {v.model or ''}".strip()}
                    for v in res.get("available", [])
                ]
                return json.dumps({
                    "status": "NOT_FOUND",
                    "message": f"Could not find vehicle '{query}' in your fleet.",
                    "available_vehicles": available
                })
        else:
            return json.dumps({"error": "Either vehicle_id or query must be provided."})

        # Fetch assigned driver details
        driver_info = None
        if vehicle.assigned_driver_id:
            driver = await session.get(Driver, vehicle.assigned_driver_id)
            if driver and driver.company_id == self.company_id:
                driver_info = {
                    "driver_id": driver.id,
                    "name": driver.name,
                    "phone_number": driver.phone_number,
                    "duty_status": driver.duty_status.value if driver.duty_status else None
                }

        # Fetch recent trips
        trips = await self.uow.repositories.trip.get_trips_by_vehicle(vehicle.id, limit=3)

        # Query maintenance records and repair tickets for diagnostic assessment
        maint_stmt = (
            select(MaintenanceRecord)
            .where(MaintenanceRecord.vehicle_id == vehicle.id)
            .order_by(desc(MaintenanceRecord.id))
            .limit(3)
        )
        maint_res = await session.execute(maint_stmt)
        maint_records = maint_res.scalars().all()

        ticket_stmt = (
            select(Ticket)
            .where(Ticket.vehicle_id == vehicle.id)
            .order_by(desc(Ticket.id))
            .limit(3)
        )
        ticket_res = await session.execute(ticket_stmt)
        tickets = ticket_res.scalars().all()

        active_issues = []
        for m in maint_records:
            tasks = [t.task_type.value for t in m.tasks] if hasattr(m, 'tasks') and m.tasks else []
            active_issues.append({
                "type": "MAINTENANCE_RECORD",
                "business_id": m.business_id,
                "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
                "category": m.category.value if hasattr(m.category, 'value') else str(m.category),
                "workshop": m.workshop,
                "tasks": tasks
            })
        for tk in tickets:
            active_issues.append({
                "type": "REPAIR_TICKET",
                "issue_type": tk.issue_type,
                "amount": tk.amount,
                "status": tk.status.value if hasattr(tk.status, 'value') else str(tk.status)
            })

        records_sufficient = len(active_issues) > 0
        if vehicle.status == VehicleStatus.MAINTENANCE:
            if not records_sufficient:
                diagnostic_notes = (
                    f"Vehicle {vehicle.registration_number} status is set to MAINTENANCE, "
                    "but there are no specific work orders, diagnostic logs, or repair tickets in the database. "
                    "Available records are insufficient to determine the specific failure or cause."
                )
            else:
                diagnostic_notes = f"Vehicle is in MAINTENANCE with {len(active_issues)} logged maintenance/repair record(s)."
        else:
            diagnostic_notes = "Vehicle is currently in operational status with no critical maintenance flags."

        v_status = vehicle.status.value if hasattr(vehicle.status, "value") else str(vehicle.status)
        details = {
            "vehicle_id": vehicle.id,
            "registration_number": vehicle.registration_number,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "tank_capacity": vehicle.tank_capacity,
            "status": v_status,
            "fuel_type": vehicle.fuel_type,
            "assigned_driver": driver_info,
            "recent_trips": [
                {
                    "trip_id": t.id,
                    "business_id": t.trip_id,
                    "route": f"{t.origin_location} -> {t.destination_location}",
                    "status": t.status.value if hasattr(t.status, "value") else str(t.status)
                }
                for t in trips
            ],
            "diagnostic_assessment": {
                "status": v_status,
                "records_sufficient": records_sufficient,
                "logged_issues": active_issues,
                "diagnostic_notes": diagnostic_notes
            }
        }
        return json.dumps(details)

    async def _resolve_single_vehicle_location(self, vehicle: Vehicle) -> Dict[str, Any]:
        """Resolves GPS telemetry and evaluates freshness for a single vehicle."""
        session = self._get_session()

        driver: Optional[Driver] = None
        if vehicle.assigned_driver_id:
            d = await session.get(Driver, vehicle.assigned_driver_id)
            if d and d.company_id == self.company_id:
                driver = d

        # Check in-progress trip if no assigned driver
        if not driver:
            active_trip_stmt = (
                select(Trip)
                .where(
                    Trip.vehicle_id == vehicle.id,
                    Trip.company_id == self.company_id,
                    Trip.status == TripStatus.IN_PROGRESS
                )
                .order_by(desc(Trip.id))
                .limit(1)
            )
            active_trip_res = await session.execute(active_trip_stmt)
            active_trip = active_trip_res.scalar_one_or_none()
            if active_trip and active_trip.driver_id:
                d = await session.get(Driver, active_trip.driver_id)
                if d and d.company_id == self.company_id:
                    driver = d

        lat: Optional[float] = None
        lng: Optional[float] = None
        loc_time: Optional[datetime] = None
        source: str = "PHONE_GPS"
        speed: Optional[float] = None
        accuracy: Optional[float] = None

        if driver:
            loc_stmt = (
                select(DriverLocation)
                .where(
                    DriverLocation.driver_id == driver.id,
                    DriverLocation.company_id == self.company_id
                )
                .order_by(desc(DriverLocation.timestamp))
                .limit(1)
            )
            loc_res = await session.execute(loc_stmt)
            recent_loc = loc_res.scalar_one_or_none()

            if recent_loc:
                lat = recent_loc.latitude
                lng = recent_loc.longitude
                loc_time = recent_loc.timestamp
                source = recent_loc.source.value if hasattr(recent_loc.source, "value") else str(recent_loc.source)
                speed = recent_loc.speed
                accuracy = recent_loc.accuracy
            elif driver.last_known_lat is not None and driver.last_known_lng is not None:
                lat = driver.last_known_lat
                lng = driver.last_known_lng
                loc_time = driver.last_location_at
                source = "PHONE_GPS"

        # Check hardware asset tracker as fallback
        if lat is None:
            asset_stmt = (
                select(Asset)
                .where(
                    Asset.current_vehicle_id == vehicle.id,
                    Asset.asset_type == AssetType.GPS_DEVICE
                )
                .limit(1)
            )
            asset_res = await session.execute(asset_stmt)
            gps_asset = asset_res.scalar_one_or_none()
            if gps_asset:
                source = "HARDWARE_GPS"

        # Handle Unavailable Location
        if lat is None or lng is None:
            return {
                "vehicle_id": vehicle.id,
                "registration_number": vehicle.registration_number,
                "make_model": f"{vehicle.make or ''} {vehicle.model or ''}".strip(),
                "has_location": False,
                "freshness": "UNAVAILABLE",
                "message": (
                    f"No GPS coordinates available for vehicle {vehicle.registration_number}. "
                    "The vehicle currently has no active GPS telemetry or reporting driver."
                )
            }

        # Evaluate Staleness & Timezone Safety
        now = datetime.now(timezone.utc)
        if loc_time:
            if loc_time.tzinfo is None:
                loc_time = loc_time.replace(tzinfo=timezone.utc)
            raw_age = (now - loc_time).total_seconds()

            if raw_age < -60.0:  # Future timestamp / clock skew (> 60s in future)
                age_seconds = raw_age
                freshness = "FUTURE_TIMESTAMP"
                is_stale = True
                future_min = round(abs(raw_age) / 60.0, 1)
                freshness_label = f"Invalid Future Timestamp ({future_min} minutes in future)"
            elif raw_age < 0.0:  # Minor clock skew within 60s
                age_seconds = 0.0
                freshness = "FRESH"
                is_stale = False
                freshness_label = "Live GPS (Recent update)"
            elif raw_age <= GPS_FRESH_THRESHOLD_SECONDS:  # <= 15 minutes (900s)
                age_seconds = raw_age
                freshness = "FRESH"
                is_stale = False
                freshness_label = "Live GPS (Recent update)"
            elif raw_age <= GPS_STALE_MAX_WINDOW_SECONDS:  # > 15m and <= 24 hours
                age_seconds = raw_age
                freshness = "STALE"
                is_stale = True
                minutes_ago = round(raw_age / 60.0, 1)
                freshness_label = f"Stale GPS (Last-Known Location: {minutes_ago} minutes ago)"
            else:  # > 24 hours
                age_seconds = raw_age
                freshness = "VERY_STALE"
                is_stale = True
                hours_ago = round(raw_age / 3600.0, 1)
                freshness_label = f"Very Stale GPS (Last-Known Location: {hours_ago} hours ago)"
        else:
            age_seconds = None
            freshness = "STALE"
            is_stale = True
            freshness_label = "Stale GPS (Timestamp missing - Last-Known Location)"

        address_str = f"Coordinates: {lat:.5f}, {lng:.5f}"
        location_type = "CURRENT_POSITION" if freshness == "FRESH" else "LAST_KNOWN_LOCATION"

        return {
            "vehicle_id": vehicle.id,
            "registration_number": vehicle.registration_number,
            "make_model": f"{vehicle.make or ''} {vehicle.model or ''}".strip(),
            "has_location": True,
            "latitude": lat,
            "longitude": lng,
            "address": address_str,
            "timestamp": loc_time.isoformat() if loc_time else None,
            "age_seconds": round(age_seconds, 1) if loc_time else None,
            "freshness": freshness,
            "freshness_label": freshness_label,
            "is_stale": is_stale,
            "is_last_known": freshness != "FRESH",
            "location_type": location_type,
            "source": source,
            "speed_kmh": round(speed * 3.6, 1) if speed else None,
            "accuracy_meters": accuracy,
            "assigned_driver": driver.name if driver else None
        }

    async def _get_vehicle_location(
        self,
        vehicle_id: Optional[int] = None,
        query: Optional[str] = None
    ) -> str:
        # Check fleet-wide multi-vehicle queries: "all", "both", "fleet", "*"
        if query and query.lower().strip() in ("all", "both", "fleet", "*"):
            all_vehicles = await self.uow.repositories.vehicle.search_vehicles(
                company_id=self.company_id,
                limit=100
            )
            locations = []
            for v in all_vehicles:
                loc = await self._resolve_single_vehicle_location(v)
                locations.append(loc)
            return json.dumps({
                "total_count": len(locations),
                "locations": locations
            })

        # 1. Resolve vehicle
        vehicle: Optional[Vehicle] = None
        if vehicle_id is not None:
            vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(int(vehicle_id), self.company_id)
            if not vehicle:
                return json.dumps({
                    "error": f"Vehicle ID {vehicle_id} not found in your fleet.",
                    "has_location": False,
                    "freshness": "UNAVAILABLE"
                })
        elif query:
            all_vehicles = await self.uow.repositories.vehicle.search_vehicles(
                company_id=self.company_id,
                limit=100
            )
            res = CopilotEntityResolver.resolve_vehicle(all_vehicles, query)
            if res["status"] == "EXACT":
                vehicle = res["vehicle"]
            elif res["status"] == "AMBIGUOUS":
                candidates = [
                    {"vehicle_id": c.id, "registration_number": c.registration_number, "label": f"{c.make or ''} {c.model or ''}".strip()}
                    for c in res["candidates"]
                ]
                return json.dumps({
                    "status": "AMBIGUOUS",
                    "message": f"Multiple vehicles matched '{query}'. Please select one to view its location.",
                    "choices": candidates
                })
            else:
                return json.dumps({
                    "status": "NOT_FOUND",
                    "message": f"Vehicle '{query}' could not be identified in your fleet.",
                    "has_location": False,
                    "freshness": "UNAVAILABLE"
                })
        else:
            return json.dumps({"error": "Either vehicle_id or query must be provided."})

        # Resolve location for the identified vehicle
        loc_data = await self._resolve_single_vehicle_location(vehicle)
        return json.dumps(loc_data)

    async def _list_drivers(
        self,
        is_active: Optional[bool] = None,
        available_only: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 20
    ) -> str:
        session = self._get_session()
        query = select(Driver).where(Driver.company_id == self.company_id)

        if is_active is not None:
            if is_active:
                query = query.where(Driver.status == DriverStatus.ACTIVE)
            else:
                query = query.where(Driver.status != DriverStatus.ACTIVE)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Driver.name.ilike(term),
                    Driver.phone_number.ilike(term),
                    Driver.employee_id.ilike(term)
                )
            )

        query = query.order_by(Driver.name).limit(min(limit or 20, 100))
        result = await session.execute(query)
        drivers = result.scalars().all()

        # Query in-progress trips to identify busy drivers
        active_trips_stmt = (
            select(Trip)
            .where(
                Trip.company_id == self.company_id,
                Trip.status == TripStatus.IN_PROGRESS,
                Trip.driver_id.isnot(None)
            )
        )
        active_trips_res = await session.execute(active_trips_stmt)
        busy_driver_trips = {t.driver_id: t for t in active_trips_res.scalars().all()}

        records = []
        for d in drivers:
            st = d.status.value if hasattr(d.status, "value") else str(d.status)
            duty = d.duty_status.value if d.duty_status else "UNKNOWN"
            is_busy = d.id in busy_driver_trips
            is_driver_active = (d.status == DriverStatus.ACTIVE)
            is_available = is_driver_active and (not is_busy)

            if available_only and not is_available:
                continue

            active_trip_info = None
            if is_busy:
                bt = busy_driver_trips[d.id]
                active_trip_info = {
                    "trip_id": bt.id,
                    "business_id": bt.trip_id,
                    "route": f"{bt.origin_location} -> {bt.destination_location}"
                }

            rec = {
                "driver_id": d.id,
                "name": d.name,
                "employee_id": d.employee_id,
                "status": st,
                "duty_status": duty,
                "is_available": is_available,
                "availability_status": "AVAILABLE" if is_available else ("BUSY_ON_TRIP" if is_busy else "INACTIVE"),
                "active_trip": active_trip_info
            }
            # Privacy & Data Minimization (Phase 5):
            # Only include phone number if search term explicitly included digits/contact search
            if search and any(c.isdigit() for c in search) and d.phone_number and search.strip() in d.phone_number:
                rec["phone_number"] = d.phone_number

            records.append(rec)

        return json.dumps({
            "total_count": len(records),
            "available_count": sum(1 for r in records if r["is_available"]),
            "busy_count": sum(1 for r in records if r["availability_status"] == "BUSY_ON_TRIP"),
            "drivers": records
        })

    async def _list_trips(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20
    ) -> str:
        parsed_status = None
        if status and status.upper() != "ALL":
            try:
                parsed_status = TripStatus(status.upper())
            except ValueError:
                pass

        trips = await self.uow.repositories.trip.search_trips(
            company_id=self.company_id,
            status=parsed_status,
            search=search,
            limit=min(limit or 20, 100)
        )

        records = []
        for t in trips:
            st = t.status.value if hasattr(t.status, "value") else str(t.status)
            records.append({
                "trip_id": t.id,
                "business_id": t.trip_id,
                "origin": t.origin_location,
                "destination": t.destination_location,
                "status": st,
                "vehicle_id": t.vehicle_id,
                "driver_id": t.driver_id,
                "planned_start_time": t.planned_start_time.isoformat() if t.planned_start_time else None,
                "planned_distance": t.planned_distance
            })

        return json.dumps({
            "total_count": len(records),
            "trips": records
        })

    async def _get_trip_details(
        self,
        trip_id: Optional[int] = None,
        trip_business_id: Optional[str] = None
    ) -> str:
        trip: Optional[Trip] = None
        if trip_id is not None:
            trip = await self.uow.repositories.trip.get_trip_by_id(int(trip_id))
        elif trip_business_id:
            trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id.strip())

        if not trip:
            return json.dumps({"error": "Trip not found."})

        # Multi-tenancy check
        if trip.company_id != self.company_id:
            raise PermissionError("Unauthorized access to trip outside your fleet.")

        st = trip.status.value if hasattr(trip.status, "value") else str(trip.status)
        return json.dumps({
            "trip_id": trip.id,
            "business_id": trip.trip_id,
            "status": st,
            "origin_location": trip.origin_location,
            "destination_location": trip.destination_location,
            "vehicle_id": trip.vehicle_id,
            "driver_id": trip.driver_id,
            "planned_start_time": trip.planned_start_time.isoformat() if trip.planned_start_time else None,
            "actual_start_time": trip.actual_start_time.isoformat() if trip.actual_start_time else None,
            "planned_distance": trip.planned_distance,
            "actual_distance": trip.actual_distance,
            "revenue": trip.revenue
        })

    # --------------------------------------------------------------------------
    # WRITE OPERATIONS: CONTROLLED TRIP SCHEDULING (PROPOSAL -> CONFIRMATION)
    # --------------------------------------------------------------------------

    async def _prepare_trip_proposal(self, args: Dict[str, Any]) -> str:
        session = self._get_session()

        vehicle_query = args.get("vehicle_query")
        origin = args.get("origin")
        destination = args.get("destination")
        planned_start_time = args.get("planned_start_time")
        driver_query = args.get("driver_query")
        planned_distance_km = args.get("planned_distance_km")
        revenue = args.get("revenue")

        if not vehicle_query or not origin or not destination or not planned_start_time:
            return json.dumps({
                "status": "MISSING_INFORMATION",
                "error": "Missing required details. Please specify vehicle, origin, destination, and departure time."
            })

        # 1. Resolve Vehicle
        all_vehicles = await self.uow.repositories.vehicle.search_vehicles(
            company_id=self.company_id,
            limit=100
        )
        v_res = CopilotEntityResolver.resolve_vehicle(all_vehicles, vehicle_query)
        if v_res["status"] == "AMBIGUOUS":
            return json.dumps({
                "status": "AMBIGUOUS_VEHICLE",
                "message": f"Multiple vehicles matched '{vehicle_query}'. Please choose one to proceed.",
                "choices": [
                    {"vehicle_id": v.id, "registration_number": v.registration_number, "make": v.make}
                    for v in v_res["candidates"]
                ]
            })
        elif v_res["status"] == "NOT_FOUND":
            return json.dumps({
                "status": "VEHICLE_NOT_FOUND",
                "message": f"Could not find vehicle '{vehicle_query}' in your authorized fleet.",
                "available": [
                    {"vehicle_id": v.id, "registration_number": v.registration_number}
                    for v in v_res.get("available", [])
                ]
            })

        vehicle: Vehicle = v_res["vehicle"]

        # 2. Check Vehicle Constraints & Availability
        if vehicle.status == VehicleStatus.MAINTENANCE:
            return json.dumps({
                "status": "CONSTRAINT_VIOLATION",
                "error": f"Vehicle {vehicle.registration_number} is currently in MAINTENANCE status and cannot be scheduled."
            })

        # Check for active trip
        active_trip_stmt = (
            select(Trip)
            .where(
                Trip.vehicle_id == vehicle.id,
                Trip.company_id == self.company_id,
                Trip.status == TripStatus.IN_PROGRESS
            )
            .limit(1)
        )
        active_trip_res = await session.execute(active_trip_stmt)
        if active_trip_res.scalar_one_or_none():
            return json.dumps({
                "status": "VEHICLE_BUSY",
                "error": f"Vehicle {vehicle.registration_number} is currently on an active trip (IN_PROGRESS)."
            })

        # 3. Resolve Driver
        driver: Optional[Driver] = None
        if driver_query:
            norm_dq = driver_query.lower().strip()
            if norm_dq in ("available", "any", "first available", "first_available", "auto") or "available" in norm_dq:
                # Find first active driver not currently on an active in-progress trip
                active_trips_stmt = (
                    select(Trip.driver_id)
                    .where(
                        Trip.company_id == self.company_id,
                        Trip.status == TripStatus.IN_PROGRESS,
                        Trip.driver_id.isnot(None)
                    )
                )
                busy_ids_res = await session.execute(active_trips_stmt)
                busy_driver_ids = set(busy_ids_res.scalars().all())

                all_drivers = await self.uow.repositories.driver.search_drivers(
                    company_id=self.company_id,
                    is_active=True,
                    limit=50
                )
                available_candidates = [d for d in all_drivers if d.id not in busy_driver_ids]
                if not available_candidates:
                    return json.dumps({
                        "status": "NO_AVAILABLE_DRIVERS",
                        "error": "No available drivers currently in fleet (all active drivers are currently on trips or none exist)."
                    })
                driver = available_candidates[0]
            else:
                all_drivers = await self.uow.repositories.driver.search_drivers(
                    company_id=self.company_id,
                    limit=100
                )
                d_res = CopilotEntityResolver.resolve_driver(all_drivers, driver_query)
                if d_res["status"] == "AMBIGUOUS":
                    return json.dumps({
                        "status": "AMBIGUOUS_DRIVER",
                        "message": f"Multiple drivers matched '{driver_query}'. Please select one.",
                        "choices": [{"driver_id": d.id, "name": d.name} for d in d_res["candidates"]]
                    })
                elif d_res["status"] == "NOT_FOUND":
                    return json.dumps({
                        "status": "DRIVER_NOT_FOUND",
                        "error": f"Driver '{driver_query}' was not found in your fleet."
                    })
                driver = d_res["driver"]
        elif vehicle.assigned_driver_id:
            driver = await session.get(Driver, vehicle.assigned_driver_id)

        if driver:
            if driver.status != DriverStatus.ACTIVE:
                return json.dumps({
                    "status": "DRIVER_UNAVAILABLE",
                    "error": f"Driver {driver.name} is not in ACTIVE status."
                })
            # Verify driver is not on an active in-progress trip
            active_driver_trip_stmt = (
                select(Trip)
                .where(
                    Trip.company_id == self.company_id,
                    Trip.driver_id == driver.id,
                    Trip.status == TripStatus.IN_PROGRESS
                )
                .limit(1)
            )
            busy_driver_trip_res = await session.execute(active_driver_trip_stmt)
            busy_trip = busy_driver_trip_res.scalar_one_or_none()
            if busy_trip:
                return json.dumps({
                    "status": "DRIVER_BUSY",
                    "error": f"Driver {driver.name} is currently assigned to an active trip ({busy_trip.trip_id}: {busy_trip.origin_location} -> {busy_trip.destination_location})."
                })

        # 4. Create Proposal
        proposal = self.proposal_manager.create_proposal(
            company_id=self.company_id,
            user_id=self.user_id,
            vehicle_id=vehicle.id,
            vehicle_registration=vehicle.registration_number,
            driver_id=driver.id if driver else None,
            driver_name=driver.name if driver else None,
            origin_location=origin.strip(),
            destination_location=destination.strip(),
            planned_start_time=planned_start_time.strip(),
            planned_distance_km=float(planned_distance_km) if planned_distance_km else None,
            revenue=float(revenue) if revenue else None,
        )

        return json.dumps({
            "status": "PROPOSAL_READY",
            "requires_confirmation": True,
            "proposal_id": proposal.proposal_id,
            "summary": {
                "vehicle": f"{vehicle.registration_number} ({vehicle.make or ''} {vehicle.model or ''})".strip(),
                "driver": driver.name if driver else "Unassigned",
                "origin": proposal.origin_location,
                "destination": proposal.destination_location,
                "planned_departure": proposal.planned_start_time,
                "planned_distance_km": proposal.planned_distance_km,
                "revenue": proposal.revenue,
                "expires_at": proposal.expires_at.isoformat()
            },
            "confirmation_prompt": (
                f"Trip proposal created (ID: {proposal.proposal_id}). "
                f"Details: Vehicle {proposal.vehicle_registration}, Route {proposal.origin_location} -> {proposal.destination_location}, Departure {proposal.planned_start_time}. "
                "Explicit confirmation required: Please confirm or cancel this trip."
            )
        })

    async def _confirm_trip_execution(self, proposal_id: Optional[str]) -> str:
        if not proposal_id:
            return json.dumps({"error": "proposal_id is required for trip confirmation."})

        proposal_id_clean = proposal_id.strip()
        lock = self.proposal_manager.get_lock(proposal_id_clean)

        async with lock:
            session = self._get_session()

            # Retrieve and validate proposal existence and company tenant boundary
            try:
                proposal = self.proposal_manager.get_proposal(proposal_id_clean, self.company_id)
            except PermissionError as pe:
                return json.dumps({"error": str(pe)})
            except ValueError as ve:
                return json.dumps({"error": str(ve)})

            # Cross-User Security Check: Proposal can only be confirmed by the initiating user
            if proposal.user_id and str(proposal.user_id) != str(self.user_id):
                logger.warning(
                    f"SECURITY: Unauthorized cross-user execution attempt on proposal {proposal_id_clean} "
                    f"by user '{self.user_id}' (staged by '{proposal.user_id}')"
                )
                return json.dumps({
                    "error": f"Unauthorized: Trip proposal {proposal_id_clean} was staged by user '{proposal.user_id}' and can only be confirmed by that user."
                })

            # In-memory Idempotency Protection: If already executed, return original trip record
            if proposal.status == "EXECUTED":
                return json.dumps({
                    "status": "ALREADY_EXECUTED",
                    "idempotent": True,
                    "message": f"Proposal '{proposal_id_clean}' was already executed.",
                    "trip_id": proposal.created_trip_id,
                    "business_id": proposal.created_trip_business_id
                })

            if proposal.status == "CANCELLED":
                return json.dumps({"error": f"Proposal '{proposal_id_clean}' was cancelled and cannot be executed."})

            if proposal.is_expired():
                proposal.status = "EXPIRED"
                return json.dumps({"error": f"Proposal '{proposal_id_clean}' has expired. Please stage a new trip proposal."})

            # Database-Level Idempotency Check: Verify whether a trip was already committed for this proposal
            existing_trip_stmt = (
                select(Trip)
                .where(
                    Trip.company_id == self.company_id,
                    Trip.origin_type == "copilot_ai",
                    Trip.origin_id == proposal_id_clean
                )
                .limit(1)
            )
            existing_trip_res = await session.execute(existing_trip_stmt)
            existing_trip = existing_trip_res.scalar_one_or_none()
            if existing_trip:
                self.proposal_manager.mark_executed(
                    proposal_id=proposal_id_clean,
                    trip_id=existing_trip.id,
                    trip_business_id=existing_trip.trip_id
                )
                return json.dumps({
                    "status": "ALREADY_EXECUTED",
                    "idempotent": True,
                    "message": f"Proposal '{proposal_id_clean}' was already executed.",
                    "trip_id": existing_trip.id,
                    "business_id": existing_trip.trip_id
                })

            # Transition proposal to in-flight EXECUTING status
            proposal.status = "EXECUTING"

            try:
                # Parse planned departure datetime safely
                try:
                    start_dt = datetime.fromisoformat(proposal.planned_start_time)
                except Exception:
                    start_dt = datetime.now(timezone.utc) + timedelta(days=1)

                # Create Trip record with origin_id set to proposal_id for database idempotency
                import uuid
                trip_business_id = f"TRP-{uuid.uuid4().hex[:8].upper()}"

                trip = Trip(
                    trip_id=trip_business_id,
                    status=TripStatus.CREATED,
                    company_id=self.company_id,
                    vehicle_id=proposal.vehicle_id,
                    driver_id=proposal.driver_id,
                    origin_location=proposal.origin_location,
                    destination_location=proposal.destination_location,
                    planned_start_time=start_dt,
                    planned_distance=proposal.planned_distance_km,
                    revenue=proposal.revenue,
                    origin_type="copilot_ai",
                    origin_id=proposal_id_clean,
                    instructions=f"Created via AI Co-Pilot proposal {proposal.proposal_id} by user {self.user_name}"
                )

                session.add(trip)
                await session.flush()
                await session.refresh(trip)
                if hasattr(session, "commit"):
                    await session.commit()

                # Atomically mark proposal as executed
                self.proposal_manager.mark_executed(
                    proposal_id=proposal.proposal_id,
                    trip_id=trip.id,
                    trip_business_id=trip.trip_id
                )

                logger.info(
                    f"AUDIT: AI Co-Pilot created verified trip {trip.trip_id} (ID={trip.id}) "
                    f"for company={self.company_id} under proposal={proposal.proposal_id}"
                )

                return json.dumps({
                    "status": "SUCCESS",
                    "verified": True,
                    "trip_id": trip.id,
                    "business_id": trip.trip_id,
                    "operational_status": trip.status.value,
                    "vehicle": proposal.vehicle_registration,
                    "driver": proposal.driver_name or "Unassigned",
                    "origin": trip.origin_location,
                    "destination": trip.destination_location,
                    "message": f"Trip {trip.trip_id} has been verified and successfully scheduled in Fleetguard."
                })
            except Exception as e:
                # Rollback in-flight status and database transaction safely
                logger.error(f"Transaction failure during trip confirmation for {proposal_id_clean}: {e}", exc_info=True)
                self.proposal_manager.rollback_executing(proposal_id_clean)
                try:
                    await session.rollback()
                except Exception:
                    pass
                return json.dumps({"error": f"Failed to execute trip confirmation: {str(e)}"})

    async def _cancel_trip_proposal(self, proposal_id: Optional[str]) -> str:
        if not proposal_id:
            return json.dumps({"error": "proposal_id is required."})

        proposal = self.proposal_manager.cancel_proposal(proposal_id.strip(), self.company_id)
        return json.dumps({
            "status": "CANCELLED",
            "proposal_id": proposal.proposal_id,
            "message": f"Proposal '{proposal.proposal_id}' was successfully cancelled."
        })

    # --------------------------------------------------------------------------
    # EXISTING OPERATIONS (PRESERVED & ISOLATED)
    # --------------------------------------------------------------------------

    async def _get_trip_intelligence(self, trip_id: Any) -> str:
        if not trip_id:
            return json.dumps({"error": "trip_id is required."})
        try:
            trip_id = int(trip_id)
        except ValueError:
            return json.dumps({"error": "trip_id must be an integer."})

        trip = await self.uow.repositories.trip.get_trip_by_id(trip_id)
        if not trip or trip.company_id != self.company_id:
            return json.dumps({"error": f"Trip {trip_id} not found in your fleet."})

        from services.trip_intelligence_service import TripIntelligenceService
        svc = TripIntelligenceService(self.uow)
        intel = await svc.compute_intelligence(trip)
        return intel.model_dump_json()

    async def _get_vehicle_summary(self, vehicle_id: Any) -> str:
        if not vehicle_id:
            return json.dumps({"error": "vehicle_id is required."})
        try:
            vehicle_id = int(vehicle_id)
        except ValueError:
            return json.dumps({"error": "vehicle_id must be an integer."})

        vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(vehicle_id, self.company_id)
        if not vehicle:
            return json.dumps({"error": f"Vehicle {vehicle_id} not found in your fleet."})

        trips = await self.uow.repositories.trip.get_trips_by_vehicle(vehicle_id, limit=5)
        summary = {
            "vehicle_id": vehicle.id,
            "registration_number": vehicle.registration_number,
            "status": vehicle.status.value if hasattr(vehicle.status, "value") else str(vehicle.status),
            "recent_trips": [
                {
                    "trip_id": t.id,
                    "business_id": t.trip_id,
                    "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                    "distance": t.actual_distance or t.planned_distance,
                } for t in trips
            ]
        }
        return json.dumps(summary)

    async def _get_related_evidence(self, entity_type_str: Optional[str], entity_id: Optional[str]) -> str:
        if not entity_type_str or not entity_id:
            return json.dumps({"error": "entity_type and entity_id are required."})

        try:
            entity_type = EntityType(entity_type_str)
        except ValueError:
            return json.dumps({"error": f"Invalid entity_type {entity_type_str}."})

        events = await self.uow.repositories.operational_event.list_events_by_entity(
            company_id=self.company_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            limit=10
        )

        all_evidence = []
        for ev in events:
            try:
                evidence_list = await self.uow.repositories.evidence.get_for_event(ev.id)
                for evidence in evidence_list:
                    all_evidence.append({
                        "evidence_id": str(evidence.id),
                        "event_id": str(evidence.event_id),
                        "type": evidence.evidence_type,
                        "summary": evidence.summary,
                        "status": evidence.status.value if hasattr(evidence.status, 'value') else str(evidence.status)
                    })
            except Exception as ex:
                logger.warning(f"Failed to fetch evidence for event {ev.id}: {ex}")

        return json.dumps({"related_evidence": all_evidence})

    async def _get_expiring_documents(self) -> str:
        session = self._get_session()
        today = datetime.now(timezone.utc).date()
        thirty_days = today + timedelta(days=30)

        # Drivers
        drivers_stmt = (
            select(Driver).where(
                Driver.company_id == self.company_id,
                Driver.license_valid_until.isnot(None),
                Driver.license_valid_until <= thirty_days
            )
        )
        drivers_res = await session.execute(drivers_stmt)
        expiring = []
        for d in drivers_res.scalars().all():
            st = "EXPIRED" if d.license_valid_until < today else "EXPIRING_SOON"
            expiring.append({
                "entity_type": "DRIVER",
                "entity_id": d.id,
                "name": d.name,
                "document": "Driver License",
                "valid_until": d.license_valid_until.isoformat(),
                "status": st
            })

        return json.dumps({"expiring_documents": expiring})

    async def _get_expense_analytics(self) -> str:
        session = self._get_session()

        stmt = (
            select(Expense.category, func.sum(Expense.amount).label("total_amount"))
            .where(
                Expense.company_id == self.company_id,
                Expense.status == ExpenseStatus.APPROVED
            )
            .group_by(Expense.category)
        )
        res = await session.execute(stmt)

        analytics = {}
        total = 0.0
        for category, total_amount in res:
            cat_name = category.value if hasattr(category, 'value') else str(category)
            analytics[cat_name] = float(total_amount)
            total += float(total_amount)

        return json.dumps({
            "expense_by_category": analytics,
            "total_approved_expenses": total
        })

    async def _list_expenses(
        self,
        category: Optional[str] = None,
        vehicle_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        limit: int = 10
    ) -> str:
        session = self._get_session()
        stmt = (
            select(Expense)
            .where(Expense.company_id == self.company_id)
        )
        if category and category.upper() != "ALL":
            try:
                cat_enum = ExpenseCategory(category.upper())
                stmt = stmt.where(Expense.category == cat_enum)
            except ValueError:
                stmt = stmt.where(Expense.category == category.upper())

        if vehicle_id is not None:
            stmt = stmt.where(Expense.vehicle_id == int(vehicle_id))
        if driver_id is not None:
            stmt = stmt.where(Expense.driver_id == int(driver_id))

        stmt = stmt.order_by(desc(Expense.expense_date)).limit(min(limit or 10, 50))
        result = await session.execute(stmt)
        expenses = result.scalars().all()

        records = []
        total_amount = 0.0
        for exp in expenses:
            cat_val = exp.category.value if hasattr(exp.category, "value") else str(exp.category)
            st_val = exp.status.value if hasattr(exp.status, "value") else str(exp.status)
            amount = float(exp.amount)
            total_amount += amount
            records.append({
                "expense_id": exp.id,
                "business_id": exp.business_id,
                "category": cat_val,
                "amount": amount,
                "currency": exp.currency,
                "status": st_val,
                "expense_date": exp.expense_date.isoformat() if exp.expense_date else None,
                "description": exp.description,
                "vehicle_id": exp.vehicle_id,
                "driver_id": exp.driver_id
            })

        return json.dumps({
            "total_count": len(records),
            "total_amount": round(total_amount, 2),
            "category_filter": category or "ALL",
            "expenses": records
        })

# models.py
# Data models (classes) for supabase database management.
# Version 1.0, WIP 260720-


# ==============================================================================
# 1. IMPORTS, CONFIGURATION & GLOBAL VARIABLES
# ==============================================================================

from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from typing import Any, Optional

from moduler.dates import get_week_day, month_to_text
from moduler.supabasestuff import constants, lowlevel


# ==============================================================================
# 2. DATABASE OBJECT CLASSES
# ==============================================================================

conn = lowlevel.supabase_connect()

@dataclass(kw_only=True)
class DbObject:
    """
    Base class for database objects. One object is (or will be) one row in a table in the database.
    """
    rowAdded: datetime=None
    rowUpdated: datetime=None

    @classmethod
    def unpack_obj(cls, obj: dict[str, Any]) -> "DbObject":
        """
        Takes an object (dict), identifies the type of object, and returns an instance of the relevant DbObject subclass.
        :param cls: 
        :param obj: object to be unpacked into a class instance
        """
        table_name = lowlevel.get_table_name(obj)

        target_cls = None
        for subcls in cls.__subclasses__():
            if subcls.__name__ == table_name:
                target_cls = subcls
                break

        if not target_cls:
            raise ValueError(f"No subclass of DbObject found matching '{table_name}'")

        if table_name == "WoInst":
            type_id: int = obj.get("woTypeId")
            wo_name: str = lowlevel.get_type_name(conn, type_id)
            obj.update({"woName": wo_name})
            

        return target_cls(**obj)


    def to_dict(self) -> dict:
        """
        Packages the object into a dictionary.
        """
        return vars(self).copy()


    def update_attr(self, updated_vals: dict) -> None:
        """
        Takes a dictionary and updates the object.
        """
        for key, val in updated_vals.items():
            if hasattr(self, key):
                setattr(self, key, val)

        return


    def compare_objs(self, other):
        """
        Compare the DbObject to another one and, depending on the types, see if they "belong together".
        """
        this_obj = type(self).__name__
        other_obj = type(other).__name__

        if this_obj == other_obj:
            raise TypeError(f"Both objects are of type {this_obj}.")

        match this_obj:
            case "WoType":
                match other_obj:
                    case "WoInst":
                        return self.woTypeId == other.woTypeId
                    case _:
                        raise TypeError(f"{this_obj} and {other_obj} can not be compared at this time.")
            case "WoInst":
                match other_obj:
                    case "WoType":
                        return self.woTypeId == other.woTypeId
                    case "BioData" | "PerfData" | "ExerciseInst":
                        return self.instId == other.instId
                    case _:
                        raise TypeError(f"{this_obj} and {other_obj} can not be compared at this time.")
            case "BioData":
                match other_obj:
                    case "WoInst":
                        return self.instId == other.instId
                    case _:
                        raise TypeError(f"{this_obj} and {other_obj} can not be compared at this time.")
            case "ExerciseInst":
                match other_obj:
                    case "WoInst":
                        return self.instId == other.instId
                    case "StrExercise":
                        return self.exerciseId == other.exerciseId
                    case "StrSet":
                        return self.exerciseInstId == other.exerciseInstId
                    case _:
                        raise TypeError(f"{this_obj} and {other_obj} can not be compared at this time.")
            case "StrExercise":
                match other_obj:
                    case "ExerciseInst":
                        return self.exerciseId == other.exerciseId
                    case _:
                        raise TypeError(f"{this_obj} and {other_obj} can not be compared at this time.")
            case "StrSet":
                match other_obj:
                    case "ExerciseInst":
                        return self.exerciseInstId == other.exerciseInstId
                    case _:
                        raise TypeError(f"{this_obj} and {other_obj} can not be compared at this time.")


@dataclass(kw_only=True)
class WoType(DbObject):
    """
    Class for workout types - rows in the table WoType.
    """
    woTypeId: int
    woName: str
    woType: str
    woDescr: str=None


class WoInst(DbObject):
    """
    Class for workout instances - rows in the table WoInst.
    """
    def __init__(self, rowAdded: datetime=None, rowUpdated: datetime=None, *, instId: str, instDatetime: str, instDur: int, woTypeId: int, woName: str, instNotes: str=None, externalDataProvider: dict[str, dict[str, Any]]=None):
        super().__init__(rowAdded=rowAdded, rowUpdated=rowUpdated)
        self.instId = instId
        self.instDatetime = datetime.fromisoformat(instDatetime)
        self.instDur = instDur
        self.woTypeId = woTypeId
        self.woName = woName
        self.instNotes = instNotes
        self.externalDataProvider = externalDataProvider

    def __repr__(self) -> str:
        return f"WoInst(instId={self.instId}, instDatetime={self.instDatetime}, instDur={self.instDur}, woTypeId={self.woTypeId}, woName={self.woName}, instNotes={self.instNotes}, externalMetadata={self.externalDataProvider})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, WoInst):
            return NotImplemented
        
        for k, v in self.to_dict().items():
            if v != other.to_dict().get(k):
                return False

        return True


@dataclass(kw_only=True)
class BioData(DbObject):
    """
    Class for biometric data - rows in the table BioData.
    """
    instId: str
    avgHr: int
    maxHr: int
    avgResp: int
    maxResp: int
    activeMins: dict
    zoneDistr: dict
    primeBenefit: str
    trainingLoad: int
    

@dataclass    
class PerfData(DbObject):
    """
    PLACEHOLDER: to be added in later version.
    """
    pass


@dataclass
class StrExercise(DbObject):
    """
    Class for strength exercise - rows in the table StrExercise.
    :param exerciseId: Unique id for the strength exercise.
    :param exerciseDescr: Description of the exercise, including machine settings, things to think of etc.
    :param primaryMuscles: Primary muscles worked. From a list of set muscles/muscle groups (not freetext). Only one allowed per exercise.
    :param secondaryMuscles: Secondary muscles worked. From a list of set muscles/muscle groups. Several muscles/muscles groups are allowed for this field.
    :param metric: The metric on which the exercise is based on, from a list of set options - "bodyweight reps", "weight and reps", "time". If several different metrics can be used for the same exercise, these should be separate rows in the table.
    """
    exerciseId: int
    exerciseDescr: str
    metric: str # what metric to go by - "bodyweight reps", "time", "weight and reps", something more? OBSOBS, should probably be different rows if the same exercise can be done both time based and weight based...
    primaryMuscles: str
    secondaryMuscles: str=None


@dataclass
class ExerciseInst(DbObject):
    """
    Class for strength exercise instances - rows in the table ExerciseInst.
    :param exerciseInstId: Unique instance id for this particular occurence of a certain exercise.
    :param exerciseId: Id for the strength exercise at hand - primary key for StrExercise row/object.
    :param instId: Id for the workout (WoInst) where the exercise instance occured. Primary key for WoInst table.
    :param setCt: Number of sets of this exercise for this particular instance of the exercise.
    :param exerciseNotes: Any notes on the execution of this exercise at this particular occurrence.
    """
    exerciseInstId: int
    exerciseId: int
    instId: str
    setCt: int
    setType: str
    exerciseNotes: str



@dataclass
class StrSet(DbObject):
    """
    Class for strength exercise sets - rows in the table StrSet.
    :param setId: Unique id for the set.
    :param exerciseInstId: Id for the ExerciseInst id that the set belongs to.
    :param setNbr: The set's order in the ExerciseInst.
    :param setWeight: Weight of the set. This can be None if other metric is used, but it can also be combined with other metrics.
    :param setReps: Number of reps in the set. This can be None if other metric is used.
    :param otherMetric: Other metric that's used for the exercise set. Stored in the database in jsonb format, with keys "Metric" and "Value".
    """
    setId: int
    exerciseInstId: int
    setNbr: int
    setWeight: int=None
    setReps: int=None
    otherMetric: dict=None


# ==============================================================================
# 3. TIME PERIOD CLASSES
# ==============================================================================

@dataclass
class PeriodStats:
    """
    Gathers all the stats across all tables for a given period. This can be used to process and present the data in different forms.
    """
    start_date: datetime
    end_date: datetime
    inst_objs: list[WoInst]
    bio_data_objs: Optional[list[BioData]]=None
    perf_data_objs: Optional[list[PerfData]]=None
    str_exercise_objs: Optional[list[StrExercise]]=None
    exercise_inst_objs: Optional[list[ExerciseInst]]=None
    set_objs: Optional[list[StrSet]]=None


    @classmethod
    def unpack_objs(cls, objs: list[dict[str, Any]], obj_type: Optional[str]=None) -> "PeriodStats":
        """
        Takes a list of DbObject instances, identifies the type of object, and returns an instance of the relevant PeriodStats subclass.
        :param objs: list of objects to be unpacked into a class instance
        :param obj_type: string to specify what kind of PeriodStats object to create
        """
        if len(objs) == 0:
            raise ValueError("\"objs\" list is empty.")
        type_errors: int = 0
        for obj in objs:
            if not issubclass(type(obj), DbObject): # if any object is not of the right class type
                type_errors += 1
        if type_errors > 0:
            print(objs[0])
            raise TypeError(f"List \"objs\"contains {type_errors} objects not subclasses of DbObject.")

        # Organize the objects by type:
        inst_objs: list[WoInst] = [obj for obj in objs if type(obj) == WoInst]
        bio_objs: list[BioData] = [obj for obj in objs if type(obj) == BioData]
        perf_objs: list[PerfData] = [obj for obj in objs if type(obj) == PerfData]
        str_exercise_objs: list[StrExercise] = [obj for obj in objs if type(obj) == StrExercise]
        exercise_inst_objs: list[ExerciseInst] = [obj for obj in objs if type(obj) == ExerciseInst]
        set_objs: list[StrSet] = [obj for obj in objs if type(obj) == StrSet]
        
        inst_objs.sort(key=lambda x: x.instDatetime, reverse=False) # Sort WoInst objects by instDatetime
        start_date: datetime = inst_objs[0].instDatetime
        end_date: datetime = inst_objs[-1].instDatetime

        orphans: dict[str, int] = {
            "BioData": 0,
            "PerfData": 0,
            "StrExercise": 0,
            "ExerciseInst": 0,
            "StrSet": 0
        }

        instIds: set[str] = {obj.instId for obj in inst_objs}
        if len(bio_objs) > 0:
            for obj in bio_objs:
                if obj.instId not in instIds:
                    orphans["BioData"] += 1

        if len(perf_objs) > 0:
            for obj in perf_objs:
                if obj.instId not in instIds:
                    orphans["PerfData"] += 1

        if len(exercise_inst_objs) > 0: # if there are any exerciseInst objects provided
            for obj in exercise_inst_objs:
                if obj.instId not in instIds:
                    orphans["ExerciseInst"] += 1

        exerciseIds: set[int] = {obj.exerciseId for obj in exercise_inst_objs} # set of all exerciseIds occurring in ExerciseInst objects
        if len(str_exercise_objs) > 0:
            for obj in str_exercise_objs:
                if obj.exerciseId not in exerciseIds:
                    orphans["StrExercise"] += 1 # all StrExercise objects that don't have a corresponding ExerciseInst object (with the StrExercise's exerciseId)

        exerciseInstIds: set[int] = {obj.exerciseInstId for obj in exercise_inst_objs} # set of all exerciseInstIds occurring in ExerciseInst objects
        if len(set_objs) > 0:
            for obj in set_objs:
                if obj.exerciseInstId not in exerciseInstIds:
                    orphans["StrSet"] += 1

        # Put orphans in dataframe, raise exception, print:
        if orphans.get("BioData") > 0 or orphans.get("PerfData") > 0 or orphans.get("StrExercise") > 0 or orphans.get("ExerciseInst") > 0 or orphans.get("StrSet") > 0:
            df: pd.DataFrame = pd.DataFrame(orphans)
            raise Exception(f"List \"objs\" contains objects without a corresponding other object:\n{df}")

        possible_types: dict[str, bool] = {
            "DayStats": False,
            "WeekStats": False,
            "MonthStats": False,
            "YearStats": False
        }

        # Figure out which types it could be:
        if start_date.date() == end_date.date(): # If start date and end date are the same -> it can be a DayStats object
            possible_types["DayStats"] = True
        if start_date.isocalendar().week == end_date.isocalendar().week: # If start date and end date are in the same week -> it can be a WeekStats object
            possible_types["WeekStats"] = True
        if start_date.month == end_date.month: # If start date and end date are in the same month -> it can be a MonthStats object
            possible_types["MonthStats"] = True
        if start_date.year == end_date.year: # If start date and end date are in the same year -> it can be a YearStats object
            possible_types["YearStats"] = True

        if obj_type: # If object type is given but not valid
            if possible_types[obj_type] == False:
                raise Exception(f"The provided objects in list \"objs\" are not congruent with given object type {obj_type}.")
        else: # If no object type is given
            valid_types: tuple[bool] = tuple(key for key, val in possible_types.items() if val == True)
            if len(valid_types) == 1: # If there's only one possible object type, set obj_type as that
                obj_type = valid_types[0]
            elif len(valid_types) <= 0:
                raise Exception(f"The provided objects in list \"objs\" are not congruent with any object types.")
            else: # If there's more than one possible object type
                obj_type = valid_types[0] # ...use the first one (they're in order from small to larger time period, so the smallest possible time period will be used(?))

        match obj_type:
            case "DayStats":
                weekday_nbr: int = start_date.isocalendar()[2]
                return DayStats(start_date=start_date, end_date=None, inst_objs=inst_objs, bio_data_objs=bio_objs, perf_data_objs=perf_objs, str_exercise_objs=str_exercise_objs, exercise_inst_objs=exercise_inst_objs, set_objs=set_objs, weekday_nbr=weekday_nbr, weekday_name=get_week_day(weekday_nbr, "en", False))
            case "WeekStats":
                return WeekStats(start_date=start_date, end_date=None, inst_objs=inst_objs, bio_data_objs=bio_objs, perf_data_objs=perf_objs, str_exercise_objs=str_exercise_objs, exercise_inst_objs=exercise_inst_objs, set_objs=set_objs, week_nbr=start_date.isocalendar().week)
            case "MonthStats":
                return DayStats(start_date=start_date, end_date=None, inst_objs=inst_objs, bio_data_objs=bio_objs, perf_data_objs=perf_objs, str_exercise_objs=str_exercise_objs, exercise_inst_objs=exercise_inst_objs, set_objs=set_objs, month_nbr=start_date.month, month_name=month_to_text(month_nbr, "en", False))
            case "YearStats":
                return DayStats(start_date=start_date, end_date=None, inst_objs=inst_objs, bio_data_objs=bio_objs, perf_data_objs=perf_objs, str_exercise_objs=str_exercise_objs, exercise_inst_objs=exercise_inst_objs, set_objs=set_objs)
            case _:
                raise ValueError(f"\"{obj_type}\" is not a valid object type.")




    def get_missing_data(self) -> list[DbObject]:
        pass


    def to_dataframe(self, data_fields: Optional[list[str]]=None):
        """
        Takes the instances and puts them into a dataframe for easy presentation.
        :param data_fields: list of what data fields to include. Will include all data fields if nothing else is specified.
        """

        if not data_fields: # if no data fields are provided, include all data fields in inst_objs and bio_data_insts
            data_fields: list[str] = list(self.inst_objs[0].to_dict().keys())
            
        if self.bio_data_objs:
            if len(self.inst_objs) != len(self.bio_data_objs):
                raise Exception("Number of WoInst objects is different from number of BioData objects.")
            data_fields += list(self.bio_data_objs[0].to_dict().keys())
        
        output: dict = {f : [] for f in data_fields}

        for i in range(len(self.inst_objs)): # goes through all the indices of the inst_objs and bio_data_insts lists
            cur_inst = self.inst_objs[i].to_dict()
            for ikey, ival in cur_inst.items():
                output[ikey].append(ival)

            if self.bio_data_objs:
                cur_bio = self.bio_data_objs[i].to_dict()
                for bkey, bval in cur_bio.items():
                    if bkey == "instId":
                        continue # skip instId on the BioData object
                    else:
                        output[bkey].append(bval)
        
        return pd.DataFrame(output)


    def get_summary(self): # vague - figure out what kind of summaries I want. Maybe graphs and charts and stuff too??
        return NotImplementedError("Code missing in this function.")


    def get_time(self, return_type: str, mode: str="total") -> tuple[int] | int:
        """
        Gets total time for the period at hand.
        :param return_type: how the time should be returned - either as "hrmin" (a tuple of (hour, mins)) or "mins".
        :param mode: what time is to be returned - "strength", "cardio" or "total". If nothing is specified, returns "total".
        :return: returns either a tuple of integers - (hour, minute) - or integer - minutes.
        """
        pass
    

    def get_count(self) -> tuple[int, int, int]:
        """
        Gets the number of workouts for the period at hand. Returns a tuple of (strength, cardio, total).
        """
        pass


    def get_type_distr(self):
        """
        Get distribution between different workout types (strength and cardio).
        """
        pass


    def get_wotype_distr(self):
        """
        Get distribution between different workout types (WoTypeIds). 
        """
        pass

    def get_avg(self, obj_filters: list[tuple[str, str, Any]], vars: list[str | int]) -> Any:
        """
        For getting averages of the values for all or a subset of the DbObjects in the PeriodStats object.
        """
        pass


@dataclass
class DayStats(PeriodStats):
    """
    Gathers WoInst and BioData objects for a given date.
    """
    weekday_nbr: int=None
    weekday_name: str=None


@dataclass
class WeekStats(PeriodStats):
    """
    Gathers WoInst and BioData objects for a given week.
    """
    week_nbr: int=None


@dataclass
class MonthStats(PeriodStats):
    """
    Gathers WoInst and BioData objects for a given month.
    """
    month_nbr: int=None
    month_name: str=None
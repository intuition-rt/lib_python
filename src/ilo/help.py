from __future__ import annotations

from typing import Any
from prettytable import PrettyTable

from .robot import Robot


def info():
    """
    Print info about ilorobot
    """
    print("ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command line")


def list_function():
    '''
    Print the list of all the functions available in the library
    '''
    # add the name info <93>
    ilo_table = PrettyTable()
    ilo_table.field_names = ["Methods", "Description"]
    ilo_table.align["Methods"] = "l"
    ilo_table.align["Description"] = "l"
    ilo_table.add_row(
        ["ilo.info()", "Print info about ilorobot"], divider=True)
    ilo_table.add_row(
        ["ilo.list_function", "Print the list of all the functions available in the library"], divider=True)
    print(ilo_table)
    print("")

    my_ilo_table = PrettyTable()
    my_ilo_table.field_names = [
        "Object methods (example: my_ilo.game())", "Description"]
    my_ilo_table.align["Object methods (example: my_ilo.game())"] = "l"
    my_ilo_table.align["Description"] = "l"

    for entry_name in dir(Robot):
        entry: Any = getattr(Robot, entry_name)
        if not callable(entry) or entry_name.startswith("_"):
            continue

        if entry.__doc__ is None:
            continue

        desc = entry.__doc__.lstrip("\n").splitlines()[0]
        my_ilo_table.add_row([entry.__name__, desc], divider=False)

    print(my_ilo_table)
    print("If the table does not display correctly, expand your terminal.")

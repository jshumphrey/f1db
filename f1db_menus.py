#! /usr/bin/env/python3
'''This file implements functionality for some simple command-line menus
to allow users to access the program's functionality without needing to
call codebase objects and functions directly.

Users will still need to modify the config file, SQL scripts, and YAML files
to set up queries, visualizations, etc., but at least they don't have to
modify the actual Python code... right...? Definitely an improvement. Probably.
'''
import os, pdb, platform, sys, textwrap

# Set up a global TextWrapper (seriously, do you really want to pass this around to everyone?)
# and configure it to wrap text nicely for all of the displayed console menus.
wrapper = textwrap.TextWrapper()

def no_op():
    '''This function does nothing. It can be used to have a menu item do nothing when executed.'''
    pass # pylint: disable = unnecessary-pass

def wait_for_input():
    '''This function simply waits for the user to press Enter to continue execution.'''
    input("Press Enter to continue...")

def clear_console():
    '''This function makes the requisite system call, depending on the platform
    the program is running on, to clear all text from the command-line window.'''
    if platform.system().lower() == 'windows':
        os.system("cls")
    else:
        os.system("reset")

class InputError(Exception):
    '''This is a custom exception raised when a user's input is unacceptable.'''
    pass # pylint: disable = unnecessary-pass

class MenuSeparator:
    '''A MenuSeparator is a dummy object that allows you to insert "separator" lines
    within a Menu's list of MenuItems. You may optionally provide some text to display;
    otherwise, the separator is simply represented by a blank line.'''
    def __init__(self, text = ""):
        self.text = text

class Menu:
    '''A Menu represents a single screen from which the user can select from a list of options.
    These options are represented as MenuItems in menu.menu_items.

    The main function that makes a Menu "do things" is menu.run(). Menus loop forever until
    something causes them to exit; this would normally be the user entering the "go back" menu option
    or the "exit the program" menu option, but could also be any kind of uncaught exception.
    If neither of these things happen, the default behavior is to re-display the current menu
    after the user's selection has been received and executed.

    Menus can have submenus underneath them; a submenu is also a Menu and has its own MenuItems.
    To have a MenuItem display a submenu, set its "function" argument to [submenu].run .
    '''
    def __init__(self, connection, parent_menu = None, text = None, allows_multi_select = False):
        self.connection = connection
        self.parent_menu = parent_menu
        self.text = text
        self.allows_multi_select = allows_multi_select

        self.menu_items = []
        self.default_menu_items = self.generate_default_menu_items()

    def generate_default_menu_items(self):
        '''This wraps the process of generating the default menu items for this menu.'''
        default_items = [MenuSeparator()]
        if self.parent_menu:
            default_items.append(MenuItem(
                self,
                "Return to the previous menu.",
                no_op,
                exit_action = "BREAK"
            ))
        default_items += [
            MenuItem(self, "Drop to the PDB debug console.", pdb.set_trace),
            MenuItem(self, "Exit the program.", sys.exit, function_args = [0])
        ]

        return default_items

    def get_enumerated_items(self):
        '''This returns a dict of index: item for all DISPLAYED MenuItems for this Menu.
        "Displayed", here, means that enumerated_items DOES include the default menu items,
        but does NOT include menu separators; those do not receive an index since they're
        not selectable by the user.'''
        return {i: x for i, x in enumerate([x for x in self.menu_items + self.default_menu_items if not isinstance(x, MenuSeparator)], 1)}

    def get_user_selections(self):
        '''This wraps the process of requesting the input string of menu selections
        from the user, validating that input, and passing the input back to the main loop.'''
        print(wrapper.fill("Please make a selection from the menu by entering its item number."))

        if self.allows_multi_select:
            print(wrapper.fill("Multiple selections can be queued by entering multiple item numbers, separated by a space - for example, \"1 3 5\"."))
            user_input = input("Enter your selection(s): ")
        else:
            user_input = input("Enter your selection: ")

        self.validate_user_input(user_input)
        return user_input.split()

    def validate_user_input(self, user_input):
        '''This looks at input provided by the user at the selections menu and
        checks for various issues. InputError is raised if any issues are found.'''
        if not self.allows_multi_select and len(user_input.split()) > 1:
            raise InputError("This menu only allows you to select one item!")

        non_integer_inputs = [x for x in user_input.split() if not x.isdigit()]
        if non_integer_inputs:
            raise InputError("The following selections are not numbers: " + ", ".join(non_integer_inputs) + "!")

        out_of_bounds_inputs = [x for x in user_input.split() if int(x) not in self.get_enumerated_items()]
        if out_of_bounds_inputs:
            raise InputError("The following selections are not in this menu's selections: " + ", ".join(out_of_bounds_inputs) + "!")

    def draw(self):
        '''This wraps the process of drawing all of this menu's text and menu items.
        Note that the menu items here will include additional menu items from extended_menu_items,
        typically a "go back", an "exit" and a "drop to debug" option.'''
        # Clear the console, and print the menu's header.
        clear_console()
        print(wrapper.fill(self.text))
        print() # Prints a blank line.

        index = 1
        for menu_item in self.menu_items + self.default_menu_items:
            if isinstance(menu_item, MenuSeparator):
                print(wrapper.fill(menu_item.text))
            else:
                print(wrapper.fill(f"{index!s}. {menu_item.text}"))
                index += 1

        print() # Prints a blank line.

    def run(self):
        '''This is the main loop that actually displays the menu and handles the user's input.'''
        while True:
            self.draw() # Display all of this menu's text and menu items.

            # Take the user's input and handle their selections.
            try:
                selections = self.get_user_selections()
            except InputError as e: # If the user provides bad input, display its message and have them try again.
                print(str(e))
                wait_for_input()
                continue

            # Execute the functionality of each selected menu item.
            for item in [self.get_enumerated_items()[int(selection)] for selection in selections]:
                item.execute_function()
                if item.exit_action == "WAIT":
                    wait_for_input()
                elif item.exit_action == "BREAK":
                    return
                elif item.exit_action == "EXIT":
                    sys.exit(0)

class MenuItem:
    '''A MenuItem is a single selectable option of a Menu. Each MenuItem carries out some kind of
    function, which is the "function" argument in the constructor. This should be a Python function;
    when the MenuItem is selected, the function will get called with the list of args and the dict of
    kwargs provided in the constructor; if neither of these are provided, the function will be run
    with no arguments.

    If the function you want to call requires custom input from the user, you can set requires_input
    to True; this will prompt the user for input (the text of the prompt comes from prompt_text),
    and passes the user's input as the first argument to the function. (Yes, this is a bit of a kludge.)

    The default behavior for a Menu, after executing a MenuItem, is to simply immediately re-display the menu.
    If you want to change this behavior, set the exit_action argument.
    - A value of "WAIT" will prompt the user to press Enter before the screen is cleared and
      the Menu is re-displayed; this is useful if this MenuItem is printing anything out to the screen
      that the user wants to see.
    - A value of "BREAK" will break out of the Menu's infinite loop, returning you to the Menu's parent.
    - A value of "EXIT" will exit the entire program immediately.
    Each Menu comes with options to do these last two things automatically, so you don't need to define your own.
    '''
    def __init__(self, menu, text, function, function_args = None, function_kwargs = None, exit_action = None, requires_input = False, prompt_text = ""):
        self.menu = menu
        self.text = text
        self.function = function
        self.function_args = function_args if function_args else []
        self.function_kwargs = function_kwargs if function_kwargs else {}
        self.exit_action = exit_action
        self.requires_input = requires_input
        self.prompt_text = prompt_text

    def execute_function(self):
        '''This executes the menu item's function, with any configured arguments.'''
        user_input = [input(self.prompt_text)] if self.requires_input else []
        self.function(*(user_input + self.function_args), **self.function_kwargs)
        return self.exit_action
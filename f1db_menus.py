#! /usr/bin/env/python3
import os, platform, sys, textwrap

# Set up a global TextWrapper (seriously, do you really want to pass this around to everyone?)
# and configure it to wrap text nicely for all of the displayed console menus.
wrapper = textwrap.TextWrapper()

def no_op():
    '''This function does nothing. It can be used to have a menu item do nothing when executed.'''
    pass # pylint: disable = unnecessary-pass

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

class Menu:
    def __init__(self, connection, parent_menu = None, text = None, allows_multi_select = False):
        self.connection = connection
        self.parent_menu = parent_menu
        self.text = text
        self.allows_multi_select = allows_multi_select
        self.menu_items = []

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

    def run(self):
        while True: # Main body of the display loop.
            # Clear the console, and print the menu's header.
            clear_console()
            print(wrapper.fill(self.text))

            # Print each of the menu items.
            enumerated_items = dict(enumerate(self.menu_items, 1))
            for index, menu_item in enumerated_items.values():
                print(wrapper.fill(f"{index!s}. {menu_item.text}"))

            # Take the user's input and handle their selections.
            try:
                selections = self.get_user_selections()
            except InputError as e: # If the user provides bad input, display its message and have them try again.
                print(str(e))
                input("Press Enter to continue...")
                continue

            # Execute the functionality of each selected menu item.
            for item in [enumerated_items[int(selection)] for selection in selections]:
                item.execute_function()
                if item.exit_action == "WAIT":
                    input("Press Enter to continue...")
                elif item.exit_action == "BREAK":
                    break
                elif item.exit_action == "EXIT":
                    sys.exit(0)


class MenuItem:
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
        if self.requires_input:
            user_input = input(self.prompt_text)
            self.function_args.insert(0, user_input)

        self.function(*self.function_args, **self.function_kwargs)
        return self.exit_action
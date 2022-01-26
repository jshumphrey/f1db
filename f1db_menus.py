#! /usr/bin/env/python3
import os, platform, textwrap

# Set up a global TextWrapper (seriously, do you really want to pass this around to everyone?)
# and configure it to wrap text nicely for all of the displayed console menus.
wrapper = textwrap.TextWrapper()

class InputError(Exception):
    '''This is a custom exception raised when a user's input is unacceptable.'''
    pass

class Menu:
    def __init__(self, connection, parent_menu = None, text = None, allows_multi_select = False):
        self.connection = connection
        self.parent_menu = parent_menu
        self.text = text
        self.allows_multi_select = allows_multi_select
        self.menu_items = []

    def get_user_selections(self):
        print(wrapper.fill("Please select any desired actions from the menu below."))

        if self.allows_multi_select:
            print(wrapper.fill("Multiple selections can be queued by entering multiple item numbers, separated by a space - for example, \"1 3 5\"."))
            user_input = input("Enter your selection(s): ")
        else:
            user_input = input("Enter your selection: ")

        self.validate_user_input(user_input)
        return user_input

    def validate_user_input(self, user_input):
        if not self.allows_multi_select and len(user_input.split()) > 1:
            raise InputError("This menu only allows you to select one item!")

        non_integer_inputs = [x for x in user_input.split() if not x.isdigit()]
        if non_integer_inputs:
            raise InputError("The following selections are not numbers: " + ", ".join(non_integer_inputs) + "!")

    def display(self):
        def clear_console():
            if platform.system().lower() == 'windows':
                os.system("cls")
            else:
                os.system("reset")

        status_message = ""
        while True: # Main body of the display loop.
            # Clear the console, and print the menu's header.
            clear_console()
            print(wrapper.fill(self.text))

            # Print each of the menu items.
            enumerated_items = dict(enumerate(self.menu_items, 1))
            for index, menu_item in enumerated_items.values():
                print(wrapper.fill(f"{index!s}. {menu_item.text}"))

            self.display_all_text()
            # Take the user's input and handle their selections.

            try:
                selections = self.get_user_selections()
            except InputError as e:
                status_message = str(e)
                continue # If the user provides bad input, display its message and have them try again.

            for item in [enumerated_items[int(selection)] for selection in selections]:
                item.execute_function()
                if item.exit_action == "WAIT":
                    input("Press Enter to continue...")
                elif item.exit_action == "BREAK":
                    break



class MenuItem:
    def __init__(self, menu, text, function, function_args = None, function_kwargs = None, exit_action = None, requires_input = False, prompt_text = ""):
        self.menu = menu
        self.text = text
        self.function = function
        self.function_args = function_args if function_args else []
        self.function_kwargs = function_kwargs if function_kwargs else {}
        self.return_code = 0
        self.requires_input = requires_input
        self.prompt_text = prompt_text

    def execute_function(self):
        if self.requires_input:
            user_input = input(self.prompt_text)
            self.function_args.insert(0, user_input)

        self.function(*self.function_args, **self.function_kwargs)
        return self.return_code
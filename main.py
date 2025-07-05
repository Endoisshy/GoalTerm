import urwid
import json
import os

FILENAME = "goals.json"

def load_goals():
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {"short": data, "long": []}
            return data
    return {"short": [], "long": []}

def save_goals(goals):
    with open(FILENAME, "w") as f:
        json.dump(goals, f, indent=2)

class GoalTracker:
    def __init__(self):
        self.goals = load_goals()
        self.active_list = "short"
        self.in_popup = False

        self.short_walker = urwid.SimpleFocusListWalker([])
        self.long_walker = urwid.SimpleFocusListWalker([])
        self.short_listbox = urwid.ListBox(self.short_walker)
        self.long_listbox = urwid.ListBox(self.long_walker)

        self.short_box = urwid.LineBox(self.short_listbox, title="Short-Term")
        self.long_box = urwid.LineBox(self.long_listbox, title="Long-Term")

        self.short_container = urwid.AttrMap(self.short_box, None)
        self.long_container = urwid.AttrMap(self.long_box, None)

        self.columns = urwid.Columns(
            [self.short_container, self.long_container],
            focus_column=None
        )

        self.header = urwid.Text(("banner", " GOALS "), align="center")
        self.footer = urwid.Text([
            ('highlight', 'a'), " Add  ",
            ('highlight', 'c'), " Complete  ",
            ('highlight', 'r'), " Remove  ",
            ('highlight', 'n'), " Note  ",
            ('highlight', 'Enter'), " View Note  ",
            ('highlight', 'Tab'), " Switch  ",
            ('highlight', 'q'), " Quit"
        ], align="center")

        self.frame = urwid.Frame(
            header=urwid.AttrMap(self.header, "header"),
            body=self.columns,
            footer=urwid.AttrMap(self.footer, "footer")
        )

        self.main_loop = urwid.MainLoop(
            self.frame,
            palette=[
                ("banner", "black,bold", "light red"),
                ("header", "black", "light red"),
                ("footer", "", ""),
                ("highlight", "light red,bold", ""),
            ],
            unhandled_input=self.handle_input
        )
        self.update_lists()
        self.update_highlight()

    def update_lists(self):
        self.short_walker.clear()
        self.long_walker.clear()
        for goal in self.goals["short"]:
            self.short_walker.append(self.make_goal_widget(goal))
        for goal in self.goals["long"]:
            self.long_walker.append(self.make_goal_widget(goal))

    def make_goal_widget(self, goal):
        mark = "[x]" if goal["done"] else "[ ]"
        note_marker = ">" if goal.get("note") else " "
        text = f"{mark} {note_marker} {goal['text']}"
        return urwid.AttrMap(urwid.SelectableIcon(text, 0), None, 'highlight')

    def update_highlight(self):
        if self.active_list == "short":
            self.short_container.set_attr_map({None: "highlight"})
            self.long_container.set_attr_map({None: None})
        else:
            self.short_container.set_attr_map({None: None})
            self.long_container.set_attr_map({None: "highlight"})

    def handle_input(self, key):
        if self.in_popup:
            return  # Disable keys during popups

        active_box = self.short_listbox if self.active_list == "short" else self.long_listbox
        active_goals = self.goals[self.active_list]

        if key in ('j', 'down'):
            if len(active_goals) > 0:
                try:
                    active_box.focus_position = min(active_box.focus_position + 1, len(active_goals) - 1)
                except IndexError:
                    pass
        elif key in ('k', 'up'):
            if len(active_goals) > 0:
                try:
                    active_box.focus_position = max(active_box.focus_position - 1, 0)
                except IndexError:
                    pass
        elif key == 'tab':
            self.active_list = "long" if self.active_list == "short" else "short"
            self.update_highlight()
        elif key == 'q':
            save_goals(self.goals)
            raise urwid.ExitMainLoop()
        elif key == 'a':
            self.add_goal()
        elif key == 'c':
            self.toggle_done()
        elif key == 'r':
            self.remove_goal()
        elif key == 'n':
            self.edit_note()
        elif key == 'enter':
            self.show_note()

    def add_goal(self):
        self.in_popup = True
        def on_done(edit, text):
            if text:
                self.goals[self.active_list].append({"text": text, "done": False, "note": ""})
                self.update_lists()
            self.in_popup = False
            self.main_loop.widget = self.frame

        edit = urwid.Edit("New goal: ")
        pile = urwid.Pile([
            edit,
            urwid.Divider("─"),
            urwid.Button("Save", on_press=lambda btn: on_done(edit, edit.edit_text)),
            urwid.Button("Cancel", on_press=lambda btn: self.restore_main())
        ])
        self.main_loop.widget = urwid.Filler(pile)

    def toggle_done(self):
        active_box = self.short_listbox if self.active_list == "short" else self.long_listbox
        active_goals = self.goals[self.active_list]
        if len(active_goals) > 0:
            idx = active_box.focus_position
            active_goals[idx]["done"] = not active_goals[idx]["done"]
            self.update_lists()

    def remove_goal(self):
        active_box = self.short_listbox if self.active_list == "short" else self.long_listbox
        active_goals = self.goals[self.active_list]
        if len(active_goals) > 0:
            idx = active_box.focus_position
            del active_goals[idx]
            self.update_lists()

    def edit_note(self):
        active_box = self.short_listbox if self.active_list == "short" else self.long_listbox
        active_goals = self.goals[self.active_list]
        if len(active_goals) > 0:
            idx = active_box.focus_position
            current_note = active_goals[idx].get("note", "")

            self.in_popup = True
            def on_done(edit, text):
                active_goals[idx]["note"] = text
                self.update_lists()
                self.in_popup = False
                self.main_loop.widget = self.frame

            edit = urwid.Edit("Note: ", current_note)
            pile = urwid.Pile([
                edit,
                urwid.Divider("─"),
                urwid.Button("Save", on_press=lambda btn: on_done(edit, edit.edit_text)),
                urwid.Button("Cancel", on_press=lambda btn: self.restore_main())
            ])
            self.main_loop.widget = urwid.Filler(pile)

    def show_note(self):
        active_box = self.short_listbox if self.active_list == "short" else self.long_listbox
        active_goals = self.goals[self.active_list]
        if len(active_goals) > 0:
            idx = active_box.focus_position
            note = active_goals[idx].get("note", "(No note)")
            note_text = urwid.Text(f"Note for {active_goals[idx]['text']} :\n\n{note}\n")
            button = urwid.Button("Close", on_press=lambda btn: self.restore_main())
            pile = urwid.Pile([note_text, urwid.Divider("─"), button])
            overlay = urwid.Overlay(
                urwid.LineBox(pile),
                self.frame,
                'center', ('relative', 60),
                'middle', ('relative', 60)
            )
            self.main_loop.widget = overlay

    def restore_main(self):
        self.in_popup = False
        self.main_loop.widget = self.frame

    def run(self):
        self.main_loop.run()

if __name__ == "__main__":
    GoalTracker().run()
